from dataclasses import dataclass
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
@dataclass
class Settings:
    service_name: str = "Local AI Tool Engine"
    host: str = "127.0.0.1"
    port: int = 8003
    data_dir: Path = BASE_DIR / "data"
    samples_dir: Path = data_dir / "samples"
    sandbox_dir: Path = data_dir / "sandbox"
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    code_timeout: int = 5  # seconds
settings = Settings()
for folder in [settings.data_dir, settings.samples_dir, settings.sandbox_dir]:
    folder.mkdir(parents=True, exist_ok=True)
