import pytest
from fastapi.testclient import TestClient
from PIL import Image

from multimodal.main import app
from backend.services.multimodal_service import MultimodalService

client = TestClient(app)

@pytest.fixture
def sample_report_file(tmp_path):
    f = tmp_path / "inspection_report.txt"
    f.write_text("CONFIDENTIAL INSPECTION REPORT\nStatus: Action Required\nCorrosion on flange FL-402.")
    return str(f)

@pytest.fixture
def sample_pid_file(tmp_path):
    f = tmp_path / "pid_unit100.png"
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    img.save(str(f))
    return str(f)

def test_health_endpoint():
    res = client.get("/multimodal/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "multimodal"

def test_process_document_endpoint(sample_report_file):
    payload = {"file_path": sample_report_file}
    res = client.post("/multimodal/process", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert "confidence" in data
    assert data["confidence"] > 0.0

def test_process_pid_endpoint(sample_pid_file):
    payload = {"file_path": sample_pid_file}
    res = client.post("/multimodal/process", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "p_and_id_drawing"
    assert "equipment" in data
    assert "instruments" in data

def test_process_missing_file():
    payload = {"file_path": "non_existent_file_xyz_123.pdf"}
    res = client.post("/multimodal/process", json=payload)
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_backend_multimodal_service_client_contract(sample_report_file):
    # Test that MultimodalService contract returns valid dict matching AgentState
    result = await MultimodalService.process_document(sample_report_file)
    assert isinstance(result, dict)
    assert "type" in result
    assert "text" in result
    assert "findings" in result
