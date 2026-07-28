import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data

def test_get_prescriptions():
    response = client.get("/prescriptions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_analytics():
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_prescriptions" in data
    assert "most_common_medicine" in data

def test_save_prescription_validation():
    # Missing required patient name should fail with 400
    invalid_payload = {
        "patient_name": "",
        "medicine": "Paracetamol",
        "dosage": "1-0-1",
        "date": "12/05/2026",
        "raw_text": "Sample text"
    }
    response = client.post("/save", json=invalid_payload)
    assert response.status_code == 400

def test_export_csv():
    response = client.get("/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

def test_suggestions_endpoint():
    response = client.get("/api/v1/suggestions?q=a")
    assert response.status_code == 200
    data = response.json()
    assert "patients" in data
    assert "medicines" in data
