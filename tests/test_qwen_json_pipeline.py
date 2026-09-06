"""
tests/test_qwen_json_pipeline.py

Tests for the Qwen → structured JSON → PDFApprovalData → generate_pdf_note pipeline.
Covers: valid JSON, malformed JSON, missing fields, invalid findings, Pydantic validation,
handoff to generate_pdf_note, calculation value preservation, and end-to-end PDF generation.
"""

import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from backend.documents.schemas import PDFApprovalData, InspectionFinding, ArtifactResult
from backend.documents.pdf_renderer import generate_approval_note_pdf
from backend.config import OUTPUTS_DIR


# ── Fixtures ─────────────────────────────────────────────────────────────────

VALID_JSON = {
    "file_reference_no": "IOCL/RHQ/PL-MAINT/2026/FL-402",
    "date": "2026-09-06",
    "subject": "REPLACEMENT & SHUTDOWN APPROVAL FOR FLANGE FL-402",
    "background_summary": (
        "During routine NDT inspection on CDU-1, critical wall thinning was identified "
        "on Component FL-402. All observations processed on-premises."
    ),
    "statutory_standard": "ASME B31.3 Section 304.1.2 & OISD-105",
    "operational_risk_assessment": (
        "Severe risk of volatile hydrocarbon containment loss at 142.5 PSI."
    ),
    "financial_sanction_inr": "INR 14,50,000 (Fourteen Lakhs Fifty Thousand Only)",
    "recommendation_for_approval": (
        "Derate operating pressure to 60 PSI and sanction emergency replacement."
    ),
    "inspection_findings_table": [
        {"Component": "FL-402", "Nominal": "6.4 mm", "Measured": "3.8 mm", "Status": "CRITICAL DEFICIT"},
        {"Component": "Retirement Threshold", "Nominal": "4.2 mm", "Measured": "Margin: -0.40 mm", "Status": "VIOLATION"},
    ],
}

# Deterministic calc output preserved verbatim from run_code stdout
CALC_STDOUT = (
    "ASME_B31_3_DESIGN_T=3.80mm\n"
    "RETIREMENT_T=5.80mm\n"
    "REMAINING_LIFE_YEARS=-0.9\n"
    "SAFETY_STATUS=CRITICAL_DEFICIT\n"
)


# ── 1. InspectionFinding model validation ─────────────────────────────────────

def test_inspection_finding_valid():
    f = InspectionFinding(Component="FL-402", Nominal="6.4 mm", Measured="3.8 mm", Status="CRITICAL DEFICIT")
    assert f.Component == "FL-402"
    assert f.Status == "CRITICAL DEFICIT"

def test_inspection_finding_missing_field():
    with pytest.raises(Exception):
        InspectionFinding(Component="FL-402", Nominal="6.4 mm", Measured="3.8 mm")  # missing Status


# ── 2. PDFApprovalData Pydantic validation ────────────────────────────────────

def test_pdfapprovaldata_valid():
    data = PDFApprovalData.model_validate(VALID_JSON)
    assert data.file_reference_no == "IOCL/RHQ/PL-MAINT/2026/FL-402"
    assert len(data.inspection_findings_table) == 2
    assert isinstance(data.inspection_findings_table[0], InspectionFinding)

def test_pdfapprovaldata_missing_required_field():
    bad = {k: v for k, v in VALID_JSON.items() if k != "subject"}
    with pytest.raises(Exception):
        PDFApprovalData.model_validate(bad)

def test_pdfapprovaldata_invalid_finding_structure():
    bad = dict(VALID_JSON)
    bad["inspection_findings_table"] = [{"Component": "FL-402"}]  # missing Nominal, Measured, Status
    with pytest.raises(Exception):
        PDFApprovalData.model_validate(bad)

def test_pdfapprovaldata_empty_findings_list():
    """Empty list is structurally valid — PDF renderer must tolerate it."""
    data_dict = dict(VALID_JSON)
    data_dict["inspection_findings_table"] = []
    data = PDFApprovalData.model_validate(data_dict)
    assert data.inspection_findings_table == []


# ── 3. JSON parsing robustness ────────────────────────────────────────────────

def test_json_loads_valid():
    parsed = json.loads(json.dumps(VALID_JSON))
    data = PDFApprovalData.model_validate(parsed)
    assert data.date == "2026-09-06"

def test_json_loads_malformed_raises():
    malformed = '{"file_reference_no": "X", "date": "Y"'  # truncated
    with pytest.raises(json.JSONDecodeError):
        json.loads(malformed)

def test_json_loads_valid_but_pydantic_fails():
    """Valid JSON but missing Pydantic-required fields → ValidationError."""
    from pydantic import ValidationError
    partial = {"file_reference_no": "X"}
    with pytest.raises(ValidationError):
        PDFApprovalData.model_validate(partial)


# ── 4. model_dump() → generate_pdf_note handoff ──────────────────────────────

def test_model_dump_produces_serialisable_dict():
    data = PDFApprovalData.model_validate(VALID_JSON)
    dumped = data.model_dump()
    assert isinstance(dumped, dict)
    assert isinstance(dumped["inspection_findings_table"], list)
    assert isinstance(dumped["inspection_findings_table"][0], dict)
    # Ensure keys are correct for pdf_renderer.py consumption
    assert "Component" in dumped["inspection_findings_table"][0]

def test_generate_pdf_note_with_validated_payload():
    """End-to-end: validated Pydantic model_dump() → generate_pdf_note → ArtifactResult."""
    data = PDFApprovalData.model_validate(VALID_JSON)
    dumped = data.model_dump()
    result = generate_approval_note_pdf(dumped, output_filename="test_pipeline_note.pdf")

    assert result["validation_status"] == "success"
    assert result["file_type"] == "pdf"
    assert len(result["sha256"]) == 64
    assert result["warnings"] == []

    path = Path(result["path"])
    assert path.exists()
    assert path.stat().st_size > 0

    path.unlink()  # cleanup


# ── 5. Deterministic calculation value preservation ───────────────────────────

def test_calc_values_present_in_pdf():
    """Calculation results injected into PDF background_summary must survive round-trip."""
    data_dict = dict(VALID_JSON)
    data_dict["background_summary"] = (
        "Calculation results: ASME_B31_3_DESIGN_T=3.80mm, RETIREMENT_T=5.80mm, "
        "REMAINING_LIFE_YEARS=-0.9, SAFETY_STATUS=CRITICAL_DEFICIT. "
        "These values are authoritative and must not be altered."
    )
    data = PDFApprovalData.model_validate(data_dict)
    dumped = data.model_dump()
    result = generate_approval_note_pdf(dumped, output_filename="test_calc_preservation.pdf")
    assert result["validation_status"] == "success"

    # Re-open PDF and verify calculation string survives in raw text
    from pypdf import PdfReader
    reader = PdfReader(result["path"])
    full_text = " ".join(page.extract_text() or "" for page in reader.pages)
    assert "3.80mm" in full_text or "CRITICAL_DEFICIT" in full_text

    Path(result["path"]).unlink()


# ── 6. SHA-256 correctness ────────────────────────────────────────────────────

def test_sha256_matches_file():
    data = PDFApprovalData.model_validate(VALID_JSON)
    result = generate_approval_note_pdf(data.model_dump(), output_filename="test_sha256.pdf")
    assert result["validation_status"] == "success"

    with open(result["path"], "rb") as f:
        expected_hash = hashlib.sha256(f.read()).hexdigest()

    assert result["sha256"] == expected_hash
    Path(result["path"]).unlink()


# ── 7. Multi-page / long content ─────────────────────────────────────────────

def test_long_content_multi_page():
    data_dict = dict(VALID_JSON)
    long_text = "This is a very long sentence that repeats to force pagination. " * 200
    data_dict["background_summary"] = long_text
    data_dict["operational_risk_assessment"] = long_text
    data_dict["recommendation_for_approval"] = long_text

    data = PDFApprovalData.model_validate(data_dict)
    result = generate_approval_note_pdf(data.model_dump(), output_filename="test_multipage.pdf")
    assert result["validation_status"] in ("success", "degraded")

    from pypdf import PdfReader
    reader = PdfReader(result["path"])
    assert len(reader.pages) >= 2

    Path(result["path"]).unlink()


# ── 8. PDF can be reopened and parsed ────────────────────────────────────────

def test_pdf_reopenable():
    data = PDFApprovalData.model_validate(VALID_JSON)
    result = generate_approval_note_pdf(data.model_dump(), output_filename="test_reopen.pdf")

    from pypdf import PdfReader
    reader = PdfReader(result["path"])
    assert len(reader.pages) > 0
    text = reader.pages[0].extract_text()
    assert "INDIAN OIL" in text or "NOTE SHEET" in text

    Path(result["path"]).unlink()


# ── 9. _generate_structured_pdf_data unit test (mocked Ollama) ───────────────

import asyncio

def test_generate_structured_pdf_data_valid_response():
    """Mock Ollama returning valid JSON → assert Pydantic validation passes."""
    from backend.agent.nodes import _generate_structured_pdf_data

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": json.dumps(VALID_JSON)}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = asyncio.run(_generate_structured_pdf_data(
            user_query="generate approval note for FL-402",
            context=[],
            tool_results=[{"tool": "run_code", "result": {"stdout": CALC_STDOUT}}],
        ))

    assert result is not None
    assert result["file_reference_no"] == "IOCL/RHQ/PL-MAINT/2026/FL-402"
    assert isinstance(result["inspection_findings_table"], list)
    assert isinstance(result["inspection_findings_table"][0], dict)


def test_generate_structured_pdf_data_malformed_json():
    """Mock Ollama returning malformed JSON → returns None, does not crash."""
    from backend.agent.nodes import _generate_structured_pdf_data

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "{ this is not valid json "}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = asyncio.run(_generate_structured_pdf_data(
            user_query="generate approval note",
            context=[],
            tool_results=[],
        ))

    assert result is None


def test_generate_structured_pdf_data_missing_fields():
    """Mock Ollama returning JSON with missing required fields → returns None."""
    from backend.agent.nodes import _generate_structured_pdf_data

    partial_json = {"file_reference_no": "X", "date": "2026-09-06"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": json.dumps(partial_json)}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = asyncio.run(_generate_structured_pdf_data(
            user_query="generate approval note",
            context=[],
            tool_results=[],
        ))

    assert result is None


# ── 10. End-to-end: Qwen → PDFApprovalData → model_dump → generate_pdf_note ─

def test_e2e_qwen_to_pdf(tmp_path):
    """
    Full pipeline test (Ollama mocked):
    Qwen response → json.loads → PDFApprovalData.model_validate → model_dump
    → generate_pdf_note → Approval_Note.pdf verified.
    """
    from backend.agent.nodes import _generate_structured_pdf_data

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": json.dumps(VALID_JSON)}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        pdf_payload = asyncio.run(_generate_structured_pdf_data(
            user_query="generate approval note for FL-402 inspection",
            context=[],
            tool_results=[
                {"tool": "run_code", "result": {"stdout": CALC_STDOUT}},
                {"tool": "ocr_document", "result": {"text": "FL-402 wall thickness measured at 3.8mm."}},
            ],
        ))

    assert pdf_payload is not None, "Qwen must return a valid structured payload"

    # Handoff to pdf renderer
    result = generate_approval_note_pdf(pdf_payload, output_filename="test_e2e_approval.pdf")

    assert result["validation_status"] == "success", f"PDF validation failed: {result}"
    assert result["file_type"] == "pdf"
    assert len(result["sha256"]) == 64

    path = Path(result["path"])
    assert path.exists()
    assert path.stat().st_size > 0

    from pypdf import PdfReader
    reader = PdfReader(str(path))
    assert len(reader.pages) > 0

    path.unlink()
