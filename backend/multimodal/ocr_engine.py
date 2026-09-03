"""
backend/multimodal/ocr_engine.py
Pankaj's Multimodal Module — OCR & Text Extraction Engine

Per README Section 7.2:
  ocr_document(file) → {text, pages, tables, confidence}

Pipeline:
  PDF / Image → markitdown / raw text → structured output

Uses markitdown for PDF/DOCX text extraction (already in requirements).
Falls back to raw file reading for plain text files.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("multimodal.ocr")


def ocr_document(file_path: str) -> dict[str, Any]:
    """
    Extracts text, tables, and metadata from a document file.

    Supports: .pdf, .docx, .txt, .png, .jpg, .jpeg
    Returns per README spec:
      {text, pages, tables, confidence, source, file_type}
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "text": "",
            "pages": 0,
            "tables": [],
            "confidence": 0.0,
            "file_type": "unknown"
        }

    suffix = path.suffix.lower()
    file_type = _detect_file_type(suffix, path.name)

    # ── Text files ─────────────────────────────────────────────────
    if suffix == ".txt":
        return _process_text_file(path)

    # ── PDF / DOCX via markitdown ───────────────────────────────────
    if suffix in [".pdf", ".docx", ".pptx", ".xlsx"]:
        return _process_with_markitdown(path, file_type)

    # ── Images — pass to vision engine ─────────────────────────────
    if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        return _process_image_ocr(path)

    return {
        "success": False,
        "error": f"Unsupported file type: {suffix}",
        "text": "",
        "pages": 0,
        "tables": [],
        "confidence": 0.0,
        "file_type": suffix
    }


def _detect_file_type(suffix: str, filename: str) -> str:
    name_lower = filename.lower()
    if "pid" in name_lower or "p&id" in name_lower or "drawing" in name_lower:
        return "p_and_id_drawing"
    if "inspection" in name_lower or "report" in name_lower:
        return "inspection_report"
    if "sop" in name_lower or "safety" in name_lower or "procedure" in name_lower:
        return "safety_sop"
    if "manual" in name_lower:
        return "technical_manual"
    if suffix in [".png", ".jpg", ".jpeg"]:
        return "image"
    return "document"


def _process_text_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tables = _extract_tables_from_text(text)
        return {
            "success": True,
            "text": text,
            "pages": max(1, len(text) // 2000),
            "tables": tables,
            "confidence": 0.99,
            "source": path.name,
            "file_type": _detect_file_type(path.suffix, path.name),
            "char_count": len(text)
        }
    except Exception as e:
        logger.error(f"Text file read error: {e}")
        return {"success": False, "error": str(e), "text": "", "pages": 0, "tables": [], "confidence": 0.0}


def _process_with_markitdown(path: Path, file_type: str) -> dict:
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(str(path))
        text = result.text_content if hasattr(result, "text_content") else str(result)
        tables = _extract_tables_from_text(text)
        return {
            "success": True,
            "text": text,
            "pages": max(1, len(text) // 2000),
            "tables": tables,
            "confidence": 0.92,
            "source": path.name,
            "file_type": file_type,
            "char_count": len(text)
        }
    except ImportError:
        logger.warning("markitdown not available — falling back to raw text read")
        return _process_text_file(path)
    except Exception as e:
        logger.error(f"markitdown extraction error for {path.name}: {e}")
        return {
            "success": False, "error": str(e),
            "text": "", "pages": 0, "tables": [], "confidence": 0.0, "file_type": file_type
        }


def _process_image_ocr(path: Path) -> dict:
    """For images, return basic file info — vision engine handles the actual interpretation."""
    return {
        "success": True,
        "text": f"[Image file: {path.name} — requires vision model for content extraction]",
        "pages": 1,
        "tables": [],
        "confidence": 0.5,
        "source": path.name,
        "file_type": _detect_file_type(path.suffix, path.name),
        "requires_vision": True
    }


def _extract_tables_from_text(text: str) -> list[dict]:
    """
    Extracts simple tabular data from text using pattern matching.
    Looks for pipe-delimited tables and key: value measurement rows.
    """
    tables = []

    # Detect pipe-delimited markdown tables
    lines = text.split("\n")
    table_rows = []
    for line in lines:
        if "|" in line and len(line.strip()) > 3:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                table_rows.append(cells)
        elif table_rows:
            if len(table_rows) >= 2:
                tables.append({"type": "tabular", "rows": table_rows})
            table_rows = []

    # Detect measurement patterns like "Tag: P-101, Reading: 4.2mm"
    measurement_pattern = re.findall(
        r"(\b[A-Z]{1,3}-\d{2,4}\b)[^\n]*?([\d.]+\s*(?:mm|PSI|GPM|°C|bar|kPa))",
        text
    )
    if measurement_pattern:
        tables.append({
            "type": "measurements",
            "rows": [{"tag": t, "value": v} for t, v in measurement_pattern[:10]]
        })

    return tables
