import os
import pytest
from pathlib import Path
from backend.documents.pdf_renderer import generate_approval_note_pdf
from backend.config import OUTPUTS_DIR

@pytest.fixture
def sample_data():
    return {
        "file_reference_no": "TEST/2026/001",
        "date": "2026-09-06",
        "subject": "TEST APPROVAL NOTE",
        "background_summary": "This is a test summary that is very long. " * 20,
        "inspection_findings_table": [
            {"Component": "TEST-1", "Nominal": "10.0 mm", "Measured": "8.5 mm", "Status": "PASS"},
            {"Component": "TEST-2", "Nominal": "12.0 mm", "Measured": "9.0 mm", "Status": "WARNING"}
        ],
        "statutory_standard": "TEST Standard 101",
        "operational_risk_assessment": "Low risk.",
        "financial_sanction_inr": "INR 50,000",
        "recommendation_for_approval": "Approve test."
    }

def test_generate_pdf_success(sample_data):
    filename = "test_approval_note.pdf"
    result = generate_approval_note_pdf(sample_data, output_filename=filename)
    
    assert result["validation_status"] == "success"
    assert result["file_type"] == "pdf"
    assert result["filename"] == filename
    assert len(result["sha256"]) == 64
    assert len(result["warnings"]) == 0
    
    file_path = OUTPUTS_DIR / filename
    assert file_path.exists()
    assert file_path.stat().st_size > 0
    
    # Cleanup
    file_path.unlink()

def test_generate_pdf_empty_data():
    filename = "test_empty_note.pdf"
    result = generate_approval_note_pdf({}, output_filename=filename)
    
    assert result["validation_status"] in ["success", "degraded"]
    assert result["file_type"] == "pdf"
    assert result["filename"] == filename
    
    file_path = OUTPUTS_DIR / filename
    assert file_path.exists()
    
    # Cleanup
    file_path.unlink()
