from sentence_transformers import SentenceTransformer

from app.config import settings


class LocalEmbeddingService:
    def __init__(self):
        # Local model inference only.
        # First run may download model once if not already available.
        self.model = SentenceTransformer(
            settings.embedding_model,
            trust_remote_code=True,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=8,
        )

        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        vector = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return vector[0].tolist()