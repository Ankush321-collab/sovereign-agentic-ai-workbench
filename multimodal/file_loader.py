import os
import mimetypes
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

from multimodal.schemas import MultimodalDocument

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class FileLoader:
    """Handles file validation, MIME type detection, and PDF/image page extractions."""

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
    PDF_EXTENSIONS = {".pdf"}
    OFFICE_EXTENSIONS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}
    TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}

    @classmethod
    def inspect(cls, file_path: str) -> MultimodalDocument:
        """Inspect a file path and return structured metadata."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = cls._infer_mime(path.suffix.lower())

        page_count = 1
        if path.suffix.lower() == ".pdf":
            page_count = cls._get_pdf_page_count(path)

        return MultimodalDocument(
            file_path=str(path),
            filename=path.name,
            mime_type=mime_type,
            file_size_bytes=file_size,
            page_count=page_count,
        )

    @classmethod
    def get_category(cls, path_or_ext: str) -> str:
        """Categorize file type based on extension."""
        suffix = Path(path_or_ext).suffix.lower()
        if suffix in cls.PDF_EXTENSIONS:
            return "pdf"
        if suffix in cls.IMAGE_EXTENSIONS:
            return "image"
        if suffix in cls.OFFICE_EXTENSIONS:
            return "office"
        if suffix in cls.TEXT_EXTENSIONS:
            return "text"
        return "unknown"

    @classmethod
    def extract_pdf_pages_as_images(cls, pdf_path: str, max_pages: int = 10, dpi: int = 200) -> List[Image.Image]:
        """Convert PDF pages to PIL Images for OCR or visual analysis."""
        images: List[Image.Image] = []
        path = Path(pdf_path)

        if HAS_PYMUPDF:
            doc = fitz.open(str(path))
            pages_to_extract = min(len(doc), max_pages)
            for i in range(pages_to_extract):
                page = doc[i]
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
        else:
            # Fallback if PyMuPDF is not installed
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(str(path), dpi=dpi, first_page=1, last_page=max_pages)
            except Exception:
                pass

        return images

    @staticmethod
    def _get_pdf_page_count(path: Path) -> int:
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(str(path))
                count = len(doc)
                doc.close()
                return count
            except Exception:
                return 1
        return 1

    @staticmethod
    def _infer_mime(suffix: str) -> str:
        mapping = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        return mapping.get(suffix, "application/octet-stream")
