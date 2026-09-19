from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings


class LocalQdrantStore:
    def __init__(self):
        # Persistent local Qdrant on disk. No Qdrant cloud.
        self.client = QdrantClient(path=str(settings.qdrant_path))
        self.collection_name = settings.collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [
            item.name
            for item in self.client.get_collections().collections
        ]

        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )

    def index_chunks(
        self,
        document_id: str,
        document_name: str,
        document_hash: str,
        document_type: str,
        access_classification: str,
        chunks: list[dict],
        vectors: list[list[float]],
        extra_metadata: dict,
    ) -> int:
        points = []

        for chunk, vector in zip(chunks, vectors):
            chunk_id = str(uuid4())

            payload = {
                "document_id": document_id,
                "document_name": document_name,
                "document_hash": document_hash,
                "document_type": document_type,
                "page": chunk["page"],
                "chunk_id": chunk_id,
                "chunk_number": chunk["chunk_number"],
                "content": chunk["content"],
                "ocr_used": chunk["ocr_used"],
                "ocr_confidence": chunk["ocr_confidence"],
                "access_classification": access_classification,
                "metadata": extra_metadata,
            }

            points.append(PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload=payload,
            ))

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

        return len(points)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        user_access_level: str,
        document_name: str | None = None,
        document_type: str | None = None,
    ) -> list:
        allowed_levels = self._allowed_levels(user_access_level)

        must_conditions = [
            FieldCondition(
                key="access_classification",
                match=MatchValue(value=level),
            )
            for level in allowed_levels
        ]

        # Qdrant filter cannot express OR using must.
        # Use should to allow any permitted classification.
        access_filter = Filter(should=must_conditions)

        if document_name:
            access_filter.must = [
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name),
                )
            ]

        if document_type:
            current_must = access_filter.must or []
            current_must.append(
                FieldCondition(
                    key="document_type",
                    match=MatchValue(value=document_type),
                )
            )
            access_filter.must = current_must

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=access_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        return response.points

    def _allowed_levels(self, user_level: str) -> list[str]:
        hierarchy = {
            "PUBLIC": 1,
            "INTERNAL": 2,
            "CONFIDENTIAL": 3,
            "RESTRICTED": 4,
        }

        normalized = user_level.upper()

        if normalized not in hierarchy:
            normalized = "INTERNAL"

        maximum = hierarchy[normalized]

        return [
            level
            for level, value in hierarchy.items()
            if value <= maximum
        ]