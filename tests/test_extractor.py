import pytest
from backend.app.extractor import extract_fields, clean_ocr_text

def test_clean_ocr_text():
    raw = "Header Line\x00\x07\n\n\n\nPrescription Details"
    cleaned = clean_ocr_text(raw)
    assert "\x00" not in cleaned
    assert "\n\n\n\n" not in cleaned
    assert "Header Line" in cleaned

def test_extract_patient_name():
    sample = """
    CITY CARE CLINIC
    Dr. John Smith, MD
    Date: 12/05/2026
    Patient Name: Alice Johnson
    Rx:
    Paracetamol 500mg
    1-0-1
    """
    fields = extract_fields(sample)
    assert fields["patient_name"] == "Alice Johnson"
    assert fields["doctor_name"] == "Dr. John Smith"
    assert fields["date"] == "12/05/2026"
    assert fields["medicine"] == "Paracetamol"
    assert fields["dosage"] in ["500mg, 1-0-1", "1-0-1", "500mg"]



def test_extract_doctor_and_hospital():
    sample = """
    APEX SPECIALTY HOSPITAL
    Dr. Robert Vance, MBBS, DNB
    Name: Bob Marley
    Rx:
    Amoxicillin 500mg
    1-1-1
    """
    fields = extract_fields(sample)
    assert "Apex Specialty Hospital" in fields["hospital_name"] or "APEX" in fields["hospital_name"]
    assert "Dr. Robert Vance" in fields["doctor_name"]
    assert fields["patient_name"] == "Bob Marley"
    assert fields["medicine"] == "Amoxicillin"
