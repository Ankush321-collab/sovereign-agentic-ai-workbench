import logging
from pathlib import Path
from typing import Dict, Any, List

from multimodal.schemas import ExtractionResult, TableData
from multimodal.file_loader import FileLoader
from multimodal.converter import DocumentConverter
from multimodal.ocr_engine import OCREngine

logger = logging.getLogger("multimodal.document_pipeline")


class DocumentPipeline:
    """End-to-end extraction pipeline for scanned documents, reports, and office files."""

    def __init__(self):
        self.converter = DocumentConverter()
        self.ocr_engine = OCREngine()

    def process(self, file_path: str) -> ExtractionResult:
        """Process a document or image file and produce an ExtractionResult."""
        doc_meta = FileLoader.inspect(file_path)
        path = Path(doc_meta.file_path)
        category = FileLoader.get_category(path.name)

        extracted_text = ""
        tables: List[TableData] = []
        confidence = 0.90
        doc_type = "standard_document"
        findings = []

        if category == "image":
            # For direct images, perform OCR extraction
            text, conf = self.ocr_engine.extract_text(path)
            extracted_text = text
            confidence = conf
            tables = self.ocr_engine.extract_tables_from_text(text)
            doc_type = "scanned_inspection_report" if ("inspection" in path.stem.lower() or "report" in path.stem.lower()) else "image_inspection"

        elif category == "pdf":
            # 1. Try digital markdown extraction first
            md_text = self.converter.convert_to_markdown(str(path))
            extracted_text = md_text

            # Check if PDF appears to be a scanned image with minimal/no digital text
            is_scanned = len(md_text.strip()) < 100 or "[Scanned document" in md_text

            if is_scanned:
                doc_type = "scanned_inspection_report"
                # Render pages to images and run OCR
                page_images = FileLoader.extract_pdf_pages_as_images(str(path), max_pages=5)
                ocr_texts = []
                confs = []
                for i, img in enumerate(page_images):
                    p_text, p_conf = self.ocr_engine.extract_text(img)
                    ocr_texts.append(f"## Page {i + 1}\n\n{p_text}")
                    confs.append(p_conf)
                    p_tables = self.ocr_engine.extract_tables_from_text(p_text, page_num=i + 1)
                    tables.extend(p_tables)

                if ocr_texts:
                    extracted_text = "\n\n---\n\n".join(ocr_texts)
                    confidence = sum(confs) / len(confs) if confs else 0.85
            else:
                tables = self.ocr_engine.extract_tables_from_text(extracted_text)
                if "inspection" in path.stem.lower() or "report" in path.stem.lower():
                    doc_type = "scanned_inspection_report"

        elif category in ["office", "text"]:
            extracted_text = self.converter.convert_to_markdown(str(path))
            tables = self.ocr_engine.extract_tables_from_text(extracted_text)
            confidence = 0.98

        # Extract high-level diagnostic findings from text if present
        findings = self._extract_findings_from_text(extracted_text)

        return ExtractionResult(
            type=doc_type,
            text=extracted_text,
            pages=doc_meta.page_count,
            confidence=round(confidence, 2),
            tables=tables,
            findings=findings,
            metadata={
                "filename": doc_meta.filename,
                "file_size_bytes": doc_meta.file_size_bytes,
                "mime_type": doc_meta.mime_type,
                "pipeline": "DocumentPipeline",
            }
        )

    @staticmethod
    def _extract_findings_from_text(text: str) -> List[str]:
        findings = []
        lines = text.splitlines()
        capture = False
        for line in lines:
            stripped = line.strip()
            if "findings:" in stripped.lower() or "summary of observations:" in stripped.lower():
                capture = True
                continue
            if capture:
                if stripped.startswith(("-", "*", "•", "1.", "2.", "3.")):
                    findings.append(stripped.lstrip("-*• 0123456789.").strip())
                elif stripped.startswith("#") or not stripped:
                    if len(findings) > 0 and not stripped:
                        continue
                    capture = False
        return findings
