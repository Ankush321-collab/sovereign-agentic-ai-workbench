import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["external_connections"] == 0

def test_network_status_endpoint():
    response = client.get("/network/status")
    assert response.status_code == 200
    data = response.json()
    assert data["external_connections"] == 0
    assert data["internet_blocked"] is True

def test_routing_endpoint():
    response = client.get("/routing")
    assert response.status_code == 200
    data = response.json()
    assert "active_models" in data

def test_files_list_endpoint():
    response = client.get("/files")
    assert response.status_code == 200
    data = response.json()
    assert "generated_deliverables" in data
    assert "uploaded_documents" in data

def test_chat_endpoint_integration():
    payload = {"message": "Summarize safety SOP and generate word report"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "model" in data
    assert "trace" in data
    assert len(data["trace"]) > 0
