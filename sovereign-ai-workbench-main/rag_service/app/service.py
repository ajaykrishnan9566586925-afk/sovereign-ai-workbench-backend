import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.document_processor import DocumentProcessor
from app.embedding_service import LocalEmbeddingService
from app.qdrant_store import LocalQdrantStore


class LocalRAGService:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.embeddings = LocalEmbeddingService()
        self.store = LocalQdrantStore()
        self.registry_file = settings.registry_dir / "documents.json"

    def _load_registry(self) -> dict:
        if not self.registry_file.exists():
            return {}

        try:
            return json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_registry(self, registry: dict) -> None:
        self.registry_file.write_text(
            json.dumps(registry, indent=2),
            encoding="utf-8",
        )

    def ingest(
        self,
        temp_file_path: Path,
        original_filename: str,
        access_classification: str,
        metadata: dict,
    ) -> dict:
        self.processor.validate_file(temp_file_path)

        access = access_classification.upper()

        if access not in settings.allowed_access_levels:
            raise ValueError(
                f"Invalid access_classification. Use one of: "
                f"{', '.join(settings.allowed_access_levels)}"
            )

        document_hash = self.processor.sha256(temp_file_path)
        registry = self._load_registry()

        if document_hash in registry:
            existing = registry[document_hash]

            return {
                "success": True,
                "document_id": existing["document_id"],
                "document_name": existing["document_name"],
                "duplicate": True,
                "duplicate_of": existing["document_id"],
                "total_pages": existing.get("total_pages", 0),
                "chunks_indexed": existing.get("chunks_indexed", 0),
                "ocr_used": existing.get("ocr_used", False),
                "ocr_confidence": existing.get("ocr_confidence"),
                "access_classification": existing["access_classification"],
                "message": "Duplicate document detected. Existing document reused.",
                "error": None,
            }

        safe_name = Path(original_filename).name
        document_id = str(uuid4())
        saved_path = settings.uploads_dir / f"{document_id}_{safe_name}"

        shutil.copy2(temp_file_path, saved_path)

        pages, ocr_used, ocr_confidence = self.processor.extract(saved_path)
        chunks = self.processor.chunk_pages(pages)

        if not chunks:
            raise ValueError(
                "No usable text found. For scans, verify Tesseract OCR setup."
            )

        vectors = self.embeddings.embed_documents(
            [chunk["content"] for chunk in chunks]
        )

        document_type = saved_path.suffix.lower().replace(".", "")

        indexed_count = self.store.index_chunks(
            document_id=document_id,
            document_name=safe_name,
            document_hash=document_hash,
            document_type=document_type,
            access_classification=access,
            chunks=chunks,
            vectors=vectors,
            extra_metadata=metadata,
        )

        registry[document_hash] = {
            "document_id": document_id,
            "document_name": safe_name,
            "stored_path": str(saved_path),
            "access_classification": access,
            "total_pages": len(pages),
            "chunks_indexed": indexed_count,
            "ocr_used": ocr_used,
            "ocr_confidence": ocr_confidence,
            "ingested_at": datetime.now().isoformat(timespec="seconds"),
        }

        self._save_registry(registry)

        return {
            "success": True,
            "document_id": document_id,
            "document_name": safe_name,
            "duplicate": False,
            "duplicate_of": None,
            "total_pages": len(pages),
            "chunks_indexed": indexed_count,
            "ocr_used": ocr_used,
            "ocr_confidence": ocr_confidence,
            "access_classification": access,
            "message": "Document processed and indexed locally in Qdrant.",
            "error": None,
        }

    def search(
        self,
        query: str,
        top_k: int,
        user_access_level: str,
        document_name: str | None,
        document_type: str | None,
        metadata_filters: dict,
    ) -> dict:
        # metadata_filters is returned and kept ready for extension.
        # For MVP, direct document name/type filtering works.
        query_vector = self.embeddings.embed_query(query)

        points = self.store.search(
            query_vector=query_vector,
            top_k=top_k,
            user_access_level=user_access_level,
            document_name=document_name,
            document_type=document_type,
        )

        results = []

        for point in points:
            payload = point.payload or {}

            score = round(float(point.score), 4)
            retrieval_confidence = round(
                max(0.0, min(1.0, (score + 1) / 2)),
                4,
            )

            results.append({
                "document": payload.get("document_name"),
                "document_id": payload.get("document_id"),
                "page": payload.get("page"),
                "chunk_id": payload.get("chunk_id"),
                "content": payload.get("content"),
                "score": score,
                "retrieval_confidence": retrieval_confidence,
                "metadata": {
                    **payload.get("metadata", {}),
                    "document_type": payload.get("document_type"),
                    "ocr_used": payload.get("ocr_used"),
                    "requested_metadata_filters": metadata_filters,
                },
                "access_classification": payload.get(
                    "access_classification",
                    "INTERNAL",
                ),
                "ocr_confidence": payload.get("ocr_confidence"),
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "result_count": len(results),
            "message": "Local semantic retrieval completed.",
            "error": None,
        }