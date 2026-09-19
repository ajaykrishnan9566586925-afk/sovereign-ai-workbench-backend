import hashlib
import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.config import settings


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
    }

    def __init__(self):
        tesseract_path = Path(settings.tesseract_cmd)

        if tesseract_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)

    def validate_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise FileNotFoundError("Uploaded file does not exist.")

        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported file. Allowed: PDF, TXT, PNG, JPG, JPEG, TIF, TIFF."
            )

        if file_path.stat().st_size == 0:
            raise ValueError("The uploaded file is empty.")

    def sha256(self, file_path: Path) -> str:
        digest = hashlib.sha256()

        with file_path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)

        return digest.hexdigest()

    def clean_text(self, text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _ocr_pil_image(self, image: Image.Image) -> tuple[str, Optional[float]]:
        data = pytesseract.image_to_data(
            image,
            lang=settings.ocr_language,
            output_type=pytesseract.Output.DICT,
        )

        words = []
        confidences = []

        for word, confidence in zip(data["text"], data["conf"]):
            word = word.strip()

            try:
                confidence_value = float(confidence)
            except (ValueError, TypeError):
                confidence_value = -1

            if word:
                words.append(word)

                if confidence_value >= 0:
                    confidences.append(confidence_value)

        average_confidence = None

        if confidences:
            average_confidence = round(sum(confidences) / len(confidences), 2)

        return self.clean_text(" ".join(words)), average_confidence

    def extract_pdf(self, file_path: Path) -> tuple[list[dict], bool, Optional[float]]:
        document = fitz.open(file_path)

        pages = []
        any_ocr_used = False
        ocr_confidences = []

        for index, page in enumerate(document):
            native_text = self.clean_text(page.get_text("text"))

            # If digital PDF has enough extracted text, use it.
            if len(native_text) >= 30:
                pages.append({
                    "page": index + 1,
                    "text": native_text,
                    "ocr_used": False,
                    "ocr_confidence": None,
                })
                continue

            # Scanned PDF fallback: render page image, OCR locally.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes(
                "RGB",
                [pixmap.width, pixmap.height],
                pixmap.samples,
            )

            ocr_text, confidence = self._ocr_pil_image(image)
            any_ocr_used = True

            if confidence is not None:
                ocr_confidences.append(confidence)

            pages.append({
                "page": index + 1,
                "text": ocr_text,
                "ocr_used": True,
                "ocr_confidence": confidence,
            })

        document.close()

        average_ocr_confidence = None

        if ocr_confidences:
            average_ocr_confidence = round(
                sum(ocr_confidences) / len(ocr_confidences),
                2,
            )

        return pages, any_ocr_used, average_ocr_confidence

    def extract_text_file(self, file_path: Path) -> tuple[list[dict], bool, Optional[float]]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        return [{
            "page": None,
            "text": self.clean_text(text),
            "ocr_used": False,
            "ocr_confidence": None,
        }], False, None

    def extract_image(self, file_path: Path) -> tuple[list[dict], bool, Optional[float]]:
        image = Image.open(file_path).convert("RGB")
        text, confidence = self._ocr_pil_image(image)

        return [{
            "page": 1,
            "text": text,
            "ocr_used": True,
            "ocr_confidence": confidence,
        }], True, confidence

    def extract(self, file_path: Path) -> tuple[list[dict], bool, Optional[float]]:
        self.validate_file(file_path)

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.extract_pdf(file_path)

        if suffix == ".txt":
            return self.extract_text_file(file_path)

        return self.extract_image(file_path)

    def chunk_pages(self, pages: list[dict]) -> list[dict]:
        chunks = []

        for page_data in pages:
            text = page_data["text"]

            if len(text) < settings.minimum_chunk_length:
                continue

            start = 0
            chunk_number = 0

            while start < len(text):
                end = min(start + settings.chunk_size, len(text))

                if end < len(text):
                    boundary = text.rfind(" ", start, end)

                    if boundary > start + 200:
                        end = boundary

                chunk_text = self.clean_text(text[start:end])

                if len(chunk_text) >= settings.minimum_chunk_length:
                    chunks.append({
                        "page": page_data["page"],
                        "chunk_number": chunk_number,
                        "content": chunk_text,
                        "ocr_used": page_data["ocr_used"],
                        "ocr_confidence": page_data["ocr_confidence"],
                    })
                    chunk_number += 1

                if end >= len(text):
                    break

                start = max(end - settings.chunk_overlap, start + 1)

        return chunks