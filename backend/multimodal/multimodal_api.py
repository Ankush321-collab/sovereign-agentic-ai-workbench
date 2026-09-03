"""
backend/multimodal/multimodal_api.py
Pankaj's Multimodal AI, OCR & P&ID Module — FastAPI Router

Exposes:
  POST /multimodal/process — Process document/image (OCR, Vision, P&ID tag extraction)
  POST /multimodal/ocr     — Dedicated OCR endpoint
  POST /multimodal/pid     — Dedicated P&ID extraction endpoint

Follows the shared API contract from team README (Section 9).
"""

import logging
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.multimodal.ocr_engine import ocr_document, _detect_file_type
from backend.multimodal.pid_parser import parse_pid_tags, detect_is_pid
from backend.multimodal.vision_engine import analyze_image

logger = logging.getLogger("multimodal.api")
router = APIRouter(prefix="/multimodal", tags=["Multimodal — Pankaj"])


# ─── Request / Response Schemas ──────────────────────────────────────────────

class ProcessRequest(BaseModel):
    file_path: str
    context_hint: Optional[str] = ""


class OCRRequest(BaseModel):
    file_path: str


class PIDRequest(BaseModel):
    text: Optional[str] = ""
    file_path: Optional[str] = ""


class ProcessResponse(BaseModel):
    success: bool
    type: str
    text: str
    pages: int
    tables: list
    findings: list
    equipment: Optional[list] = []
    instruments: Optional[list] = []
    confidence: float
    model_used: Optional[str] = "local_pipeline"
    error: Optional[str] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/process", response_model=ProcessResponse)
async def process_file(request: ProcessRequest):
    """
    Main multimodal pipeline for all uploaded files (PDFs, Images, P&IDs, Text).
    Extracts OCR text, layout tables, P&ID equipment/instrument tags, and visual findings.
    """
    path = Path(request.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    suffix = path.suffix.lower()
    is_image = suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]

    # Step 1: Run OCR / text extraction
    ocr_res = ocr_document(request.file_path)
    extracted_text = ocr_res.get("text", "")
    tables = ocr_res.get("tables", [])
    pages = ocr_res.get("pages", 1)

    findings = []
    equipment = []
    instruments = []
    model_used = "ocr_extractor"
    confidence = ocr_res.get("confidence", 0.9)

    # Step 2: If image, invoke vision model
    if is_image:
        vision_res = await analyze_image(request.file_path, request.context_hint or "")
        findings.extend(vision_res.get("findings", []))
        model_used = vision_res.get("model_used", "vision_engine")
        if vision_res.get("type"):
            ocr_res["file_type"] = vision_res["type"]

    # Step 3: Run P&ID extraction if applicable
    if detect_is_pid(extracted_text, path.name):
        pid_res = parse_pid_tags(extracted_text)
        equipment = pid_res.get("equipment", [])
        instruments = pid_res.get("instruments", [])
        if equipment or instruments:
            findings.append(f"Identified {len(equipment)} equipment and {len(instruments)} instruments in P&ID diagram")

    # Step 4: Extract generic findings if text is present
    if not findings and extracted_text:
        lines = [l.strip() for l in extracted_text.split("\n") if l.strip()]
        for line in lines:
            if any(k in line.lower() for k in ["corrosion", "warning", "danger", "alert", "defect", "fail", "action"]):
                findings.append(line)

    doc_type = ocr_res.get("file_type", _detect_file_type(suffix, path.name))

    return ProcessResponse(
        success=ocr_res.get("success", True),
        type=doc_type,
        text=extracted_text,
        pages=pages,
        tables=tables,
        findings=findings[:10],
        equipment=equipment,
        instruments=instruments,
        confidence=confidence,
        model_used=model_used,
        error=ocr_res.get("error")
    )


@router.post("/ocr")
async def extract_ocr(request: OCRRequest):
    """Run OCR and layout extraction on a file."""
    res = ocr_document(request.file_path)
    if not res.get("success") and res.get("error"):
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/pid")
async def extract_pid(request: PIDRequest):
    """Extract P&ID tags (Equipment & Instruments) from text or file."""
    text = request.text
    if request.file_path and Path(request.file_path).exists():
        ocr_res = ocr_document(request.file_path)
        text = (text or "") + "\n" + ocr_res.get("text", "")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Provide text or a valid file_path to extract P&ID tags")

    return parse_pid_tags(text)
