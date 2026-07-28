import re
from typing import Dict, Any
from .logger import logger
from .utils import clean_ocr_raw_text, parse_flexible_date, normalize_medicine_name

def clean_ocr_text(text: str) -> str:
    """Clean raw OCR text."""
    return clean_ocr_raw_text(text)

def extract_fields(raw_text: str) -> Dict[str, Any]:
    """Multi-stage heuristic parsing engine for extracting structured healthcare fields."""
    text = clean_ocr_text(raw_text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    fields = {
        "patient_name": "Unknown",
        "medicine": "Not Found",
        "dosage": "Not Found",
        "date": "Not Found",
        "doctor_name": "Unknown",
        "hospital_name": "Unknown",
        "age": "N/A",
        "gender": "N/A",
        "document_type": "Prescription",
        "hospital_address": "",
        "registration_num": "",
        "generic_name": "",
        "strength": "",
        "frequency": "",
        "duration": "",
        "diagnosis": "",
        "symptoms": "",
        "department": "",
        "follow_up_date": "",
        "report_num": "",
        "lab_tests": ""
    }

    if not lines:
        return fields

    # ── 1. Doctor Name Extraction
    doc_patterns = [
        r'(?i)(?:Dr\.?|Doctor|Consultant|Physician|Prof\.?)\s*[:\-\.]?\s*([A-Za-z\s\.]{2,30})',
        r'(?i)\bDr\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'(?i)Prepared\s+By\s*:\s*([A-Za-z\s\.]{2,30})'
    ]
    for pattern in doc_patterns:
        match = re.search(pattern, text)
        if match:
            doc_name = match.group(1).split('\n')[0].strip()
            doc_name = re.sub(r'(?i)\b(?:MD|MBBS|MS|DNB|PhD|BAMS|BHMS|Patient|Name)\b.*', '', doc_name).strip()
            if len(doc_name) > 2 and not doc_name.lower().startswith('name'):
                fields["doctor_name"] = f"Dr. {doc_name}" if not doc_name.lower().startswith('dr') else doc_name
                break

    # ── 2. Hospital / Clinic Extraction
    hosp_keywords = ["hospital", "clinic", "medical center", "healthcare", "nursing home", "specialty center", "lab", "diagnostics"]
    for i, line in enumerate(lines[:8]):
        if any(k in line.lower() for k in hosp_keywords) and not any(k in line.lower() for k in ["patient", "doctor", "dr.", "rx"]):
            fields["hospital_name"] = line.strip().title()
            if i + 1 < len(lines):
                 fields["hospital_address"] = lines[i+1].strip()
            break
            
    if fields["hospital_name"] == "Unknown" and lines:
        first_line = lines[0]
        if len(first_line) > 3 and not any(k in first_line.lower() for k in ["patient", "name", "dr", "date"]):
             fields["hospital_name"] = first_line.strip().title()

    # ── 3. Patient Name Extraction
    patient_patterns = [
        r'(?i)(?:Patient\s*Name|Patient|Pt\.?\s*Name)\s*[:\-\.]?\s*([A-Za-z\s\.]{2,30})',
        r'(?i)(?:Mr\.?|Mrs\.?|Ms\.?)\s*([A-Za-z\s\.]{2,30})',
        r'(?i)For\s*:\s*([A-Za-z\s\.]{2,30})'
    ]
    for pattern in patient_patterns:
        match = re.search(pattern, text)
        if match:
            raw_name = match.group(1).split('\n')[0].strip()
            raw_name = re.split(r'(?i)\b(?:Age|Sex|DOB|Male|Female|Yrs|Years|Year|Rx|\d+)\b|\(', raw_name)[0].strip()
            raw_name = re.sub(r'[^a-zA-Z\s]+$', '', raw_name).strip()
            if len(raw_name) >= 2 and raw_name.lower() not in ["name", "patient", "details"]:
                fields["patient_name"] = raw_name.title()
                break

    if fields["patient_name"] == "Unknown":
        for line in lines:
            if re.search(r'(?i)\b(?:Mr|Mrs|Ms|Master)\.?\s+[A-Z][a-z]+', line):
                match = re.search(r'(?i)\b(Mr|Mrs|Ms|Master\.?\s+[A-Za-z\s]+)', line)
                if match:
                    fields["patient_name"] = match.group(1).strip().title()
                    break

    # ── 4. Age & Gender Extraction
    age_match = re.search(r'(?i)\b(?:Age|Aged)\s*[:\-\.]?\s*(\d{1,3})\s*(?:Yrs?|Years?)?\b|\b(\d{1,3})\s*(?:Yrs?|Years?)\b', text)
    if age_match:
        fields["age"] = age_match.group(1) or age_match.group(2)

    gender_match = re.search(r'(?i)\b(?:Gender|Sex)\s*[:\-\.]?\s*(Male|Female|M|F)\b|\b(Male|Female)\b', text)
    if gender_match:
        g = (gender_match.group(1) or gender_match.group(2)).upper()
        fields["gender"] = "Male" if g.startswith("M") else "Female"

    # ── 5. Date Extraction
    date_match = re.search(
        r'\b(?:\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
        text, re.IGNORECASE
    )
    if date_match:
        norm_date = parse_flexible_date(date_match.group())
        fields["date"] = norm_date if norm_date else date_match.group()

    # ── Enterprise Diagnostics Sub-fields 
    rt_match = re.search(r'(?i)(?:Reg|MRN|Registration)\s*(?:No|Number|\#)?\s*[:\-\.]?\s*([A-Z0-9\-]+)', text)
    if rt_match: fields["registration_num"] = rt_match.group(1)

    diag_match = re.search(r'(?i)(?:Diagnosis|Impression|Condition)\s*[:\-\.]\s*([^\n]+)', text)
    if diag_match: fields["diagnosis"] = diag_match.group(1).strip()
    
    symp_match = re.search(r'(?i)(?:Symptoms|Complaints|C/O)\s*[:\-\.]\s*([^\n]+)', text)
    if symp_match: fields["symptoms"] = symp_match.group(1).strip()
    
    dept_match = re.search(r'(?i)(?:Department|Dept)\s*[:\-\.]\s*([A-Za-z\s]+)', text)
    if dept_match: fields["department"] = dept_match.group(1).strip()
    
    fu_match = re.search(r'(?i)(?:Follow\s*up|Review)\s*[:\-\.]\s*([^\n]+)', text)
    if fu_match: fields["follow_up_date"] = fu_match.group(1).strip()
    
    lab_match = re.search(r'(?i)(?:Tests|Investigations|Advised)\s*[:\-\.]\s*([^\n]+)', text)
    if lab_match: fields["lab_tests"] = lab_match.group(1).strip()

    # ── 6. Advanced Dosage & Frequency Extraction
    freq_match = re.search(r'(?i)\b\d-\d-\d(?:-\d)?\b|\b\d\s?[xX]\s?\d\b|\bonce\s+daily\b|\btwice\s+daily\b|\b(?:OD|BD|BID|TDS|QID|STAT|HS|PRN|SOS)\b', text)
    if freq_match:
        fields["frequency"] = freq_match.group()

    strength_match = re.search(r'(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|puff|puffs|IU)\b', text)
    if strength_match:
        fields["strength"] = strength_match.group()

    duration_match = re.search(r'(?i)\b(?:for)\s+(\d+\s+(?:days?|weeks?|months?))\b', text)
    if duration_match:
        fields["duration"] = duration_match.group(1)

    if fields["strength"] and fields["frequency"]:
        fields["dosage"] = f'{fields["strength"]}, {fields["frequency"]}'
    elif fields["frequency"]:
        fields["dosage"] = fields["frequency"]
    elif fields["strength"]:
        fields["dosage"] = fields["strength"]

    # ── 7. Advanced Medicine Name Parsing
    common_medicines = [
        "Amoxicillin", "Paracetamol", "Ibuprofen", "Metformin", "Lisinopril",
        "Aspirin", "Azithromycin", "Ciprofloxacin", "Doxycycline", "Omeprazole",
        "Pantoprazole", "Atorvastatin", "Amlodipine", "Losartan", "Cetirizine",
        "Levothyroxine", "Augmentin", "Albuterol", "Gabapentin", "Hydrochlorothiazide"
    ]
    for med in common_medicines:
        if re.search(r'\b' + re.escape(med) + r'\b', text, re.IGNORECASE):
            fields["medicine"] = med
            fields["generic_name"] = med # Default generic mapping for basic list
            break

    if fields["medicine"] == "Not Found":
        rx_found = False
        for i, line in enumerate(lines):
            if "rx" in line.lower() or "tab" in line.lower() or "cap" in line.lower():
                rx_found = True
                continue
            if rx_found or re.search(r'\d+\s*(?:mg|g|ml|mcg)\b', line, re.IGNORECASE):
                cleaned_med = re.sub(r'(?i)\b(?:tab|tablet|cap|capsule|syr|syrup|inj)\b\.?', '', line)
                cleaned_med = re.sub(r'(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg)\b.*', '', cleaned_med)
                cleaned_med = re.sub(r'(?i)\b(?:OD|BD|TDS|QID|STAT|HS|PRN|1-1-1)\b.*', '', cleaned_med)
                cleaned_med = re.sub(r'[^a-zA-Z\s\-]', '', cleaned_med).strip()
                if len(cleaned_med) >= 3 and cleaned_med.lower() not in ["doctor", "patient", "date", "hospital"]:
                    fields["medicine"] = cleaned_med.title()
                    break

    logger.info(f"Enterprise Fields Extracted Successfully")
    return fields
