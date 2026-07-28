import pytest
from backend.app.extractor import extract_fields

def test_extract_patient_name():
    raw_text = "City Clinic\nDr. John Smith\nPatient Name: Alice Walker\nRx:\nAmoxicillin 500mg"
    fields = extract_fields(raw_text)
    assert fields["patient_name"] == "Alice Walker"

def test_extract_doctor_name():
    raw_text = "Dr. Robert Johnson MD\nPatient Name: Bob Marley\nDate: 12/05/2026"
    fields = extract_fields(raw_text)
    assert "Robert Johnson" in fields["doctor_name"]

def test_extract_medicine_and_dosage():
    raw_text = "City Hospital\nPatient: John\nRx:\nParacetamol 650mg 1-0-1"
    fields = extract_fields(raw_text)
    assert fields["medicine"] == "Paracetamol"
    assert "650mg" in fields["dosage"]

def test_extract_date():
    raw_text = "Date: 15/08/2026\nPatient: Carol"
    fields = extract_fields(raw_text)
    assert fields["date"] == "15/08/2026"
