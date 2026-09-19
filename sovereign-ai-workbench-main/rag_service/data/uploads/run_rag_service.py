from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    service_name: str = "Local Document Intelligence and RAG Service"

    # Local folders only
    uploads_dir: Path = BASE_DIR / "data" / "uploads"
    qdrant_path: Path = BASE_DIR / "data" / "qdrant_db"
    registry_dir: Path = BASE_DIR / "data" / "registry"
    logs_dir: Path = BASE_DIR / "data" / "logs"

    # BGE-M3 model:
    # First run downloads it once from Hugging Face.
    # Later replace this with a local folder path:
    # BASE_DIR / "models" / "bge-m3"
    embedding_model: str = "BAAI/bge-m3"

    embedding_dimension: int = 1024
    collection_name: str = "mrpl_local_documents"

    chunk_size: int = 900
    chunk_overlap: int = 150
    minimum_chunk_length: int = 30

    # OCR
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ocr_language: str = "eng"

    # Access labels in your demo
    default_access_classification: str = "INTERNAL"
    allowed_access_levels: tuple[str, ...] = (
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL",
        "RESTRICTED",
    )


settings = Settings()

for folder in [
    settings.uploads_dir,
    settings.qdrant_path,
    settings.registry_dir,
    settings.logs_dir,
]:
    folder.mkdir(parents=True, exist_ok=True)