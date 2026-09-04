"""
tests/test_multimodal.py
Pankaj's Multimodal AI, OCR & P&ID Module — Unit & Integration Test Suite

Tests:
  1. OCR extracts text from standard text file
  2. OCR handles nonexistent file gracefully
  3. P&ID parser detects equipment tags (P-101, V-204, etc.)
  4. P&ID parser detects instrument tags (PT-201, XV-101, etc.)
  5. P&ID detection heuristic correctly identifies drawing text
  6. Vision engine handles missing image or fallback
  7. API endpoint POST /multimodal/ocr extracts content
  8. API endpoint POST /multimodal/pid extracts tags
  9. API endpoint POST /multimodal/process runs full pipeline on sample report
  10. API endpoint POST /multimodal/process returns 404 on missing file
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.multimodal.ocr_engine import ocr_document, _detect_file_type
from backend.multimodal.pid_parser import parse_pid_tags, detect_is_pid
from backend.multimodal.vision_engine import analyze_image_sync

client = TestClient(app)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"


def test_ocr_extracts_text():
    """OCR engine extracts text and calculates character count from text SOP file."""
    sop_file = SAMPLE_DIR / "Safety_SOP.txt"
    assert sop_file.exists(), "Safety_SOP.txt must exist"
    
    result = ocr_document(str(sop_file))
    assert result["success"] is True
    assert "SAFETY STANDARD OPERATING PROCEDURE" in result["text"]
    assert result["pages"] >= 1
    assert result["confidence"] > 0.8


def test_ocr_missing_file():
    """OCR engine should gracefully return success=False for missing files."""
    result = ocr_document("nonexistent_document_12345.pdf")
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_pid_parser_equipment():
    """P&ID parser extracts standard equipment tags (Pumps, Vessels, Compressors)."""
    schematic_text = (
        "Process Stream Flow: Feed enters Slurry Pump P-101A and Standby Pump P-101B. "
        "Discharges into High Pressure Separator Vessel V-204. Gas stream routes to Compressor K-301."
    )
    result = parse_pid_tags(schematic_text)
    tags = [eq["tag"] for eq in result["equipment"]]
    types = {eq["tag"]: eq["type"] for eq in result["equipment"]}
    
    assert "P-101A" in tags
    assert "P-101B" in tags
    assert "V-204" in tags
    assert "K-301" in tags
    assert types["P-101A"] == "Pump"
    assert types["V-204"] == "Vessel"
    assert types["K-301"] == "Compressor"


def test_pid_parser_instruments():
    """P&ID parser extracts standard ISA instrument tags (PT, FT, TT, XV, BV)."""
    loop_text = (
        "Safety Loop 100: Pressure Transmitter PT-201 signals Emergency Control Valve XV-101. "
        "Manual override via Block Valve BV-102. Flow monitored by FT-102 and Temperature by TT-301."
    )
    result = parse_pid_tags(loop_text)
    tags = [inst["tag"] for inst in result["instruments"]]
    types = {inst["tag"]: inst["type"] for inst in result["instruments"]}
    
    assert "PT-201" in tags
    assert "XV-101" in tags
    assert "BV-102" in tags
    assert "FT-102" in tags
    assert "TT-301" in tags
    assert types["PT-201"] == "Pressure Transmitter"
    assert types["XV-101"] == "Control Valve"


def test_pid_heuristic_detection():
    """detect_is_pid returns True for drawing filenames or tag-dense text."""
    assert detect_is_pid("Simple text", "Unit100_PID_Drawing.pdf") is True
    assert detect_is_pid("Contains P-101, PT-201, XV-102, V-204", "document.txt") is True
    assert detect_is_pid("Regular memo without industrial tags", "meeting_notes.txt") is False


def test_vision_engine_fallback():
    """Vision engine gracefully returns heuristic analysis if vision model is offline or invalid."""
    result = analyze_image_sync("dummy_inspection.jpg")
    assert result["success"] is False or result.get("model_used") in ["heuristic", "none", "qwen2.5vl:latest", "llava:latest"]


def test_api_multimodal_ocr():
    """API endpoint POST /multimodal/ocr extracts text successfully."""
    sop_file = SAMPLE_DIR / "Safety_SOP.txt"
    response = client.post("/multimodal/ocr", json={"file_path": str(sop_file)})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "SAFETY STANDARD OPERATING PROCEDURE" in data["text"]


def test_api_multimodal_pid():
    """API endpoint POST /multimodal/pid extracts tags from provided text."""
    payload = {"text": "Loop: Pump P-101 discharges through valve XV-101 monitored by PT-201."}
    response = client.post("/multimodal/pid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_tags"] >= 3
    eq_tags = [e["tag"] for e in data["equipment"]]
    inst_tags = [i["tag"] for i in data["instruments"]]
    assert "P-101" in eq_tags
    assert "XV-101" in inst_tags
    assert "PT-201" in inst_tags


def test_api_multimodal_process_pipeline():
    """API endpoint POST /multimodal/process executes full multimodal pipeline."""
    sop_file = SAMPLE_DIR / "Valve_Maintenance_Manual.txt"
    response = client.post("/multimodal/process", json={"file_path": str(sop_file)})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "VALVE MAINTENANCE MANUAL" in data["text"]
    assert len(data["equipment"]) > 0 or len(data["instruments"]) > 0 or len(data["findings"]) > 0


def test_api_multimodal_process_404():
    """API endpoint POST /multimodal/process returns 404 for missing file."""
    response = client.post("/multimodal/process", json={"file_path": "does_not_exist_file.pdf"})
    assert response.status_code == 404
