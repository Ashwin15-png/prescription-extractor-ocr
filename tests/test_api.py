import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]

def test_get_prescriptions_list():
    response = client.get("/prescriptions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_analytics():
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_prescriptions" in data

def test_save_prescription():
    payload = {
        "patient_name": "Test Patient",
        "medicine": "Test Med",
        "dosage": "500mg",
        "date": "28/07/2026",
        "doctor_name": "Dr. Test",
        "hospital_name": "Test Hospital"
    }
    response = client.post("/save", json=payload)
    assert response.status_code == 200
    assert "id" in response.json()

def test_export_csv():
    response = client.get("/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

def test_export_excel():
    response = client.get("/api/v1/export/excel")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]

def test_export_pdf():
    response = client.get("/api/v1/export/pdf")
    assert response.status_code == 200
    assert "pdf" in response.headers["content-type"]

def test_suggestions():
    response = client.get("/api/v1/suggestions?q=Test")
    assert response.status_code == 200
    data = response.json()
    assert "patients" in data

def test_user_registration_and_login():
    email = "doctor_test@hospital.org"
    register_payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Dr. Test User",
        "role": "Doctor"
    }
    # Register
    res = client.post("/auth/register", json=register_payload)
    assert res.status_code in [200, 400] # 400 if already registered from previous run

    # Login
    login_payload = {
        "email": email,
        "password": "Password123!"
    }
    res_login = client.post("/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
