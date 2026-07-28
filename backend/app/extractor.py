import re
from typing import Dict
from .logger import logger

def clean_ocr_text(text: str) -> str:
    """Auto-clean raw OCR text: strip invalid control chars, normalize spaces."""
    if not text:
        return ""
    # Remove control characters except newlines/tabs
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Remove excessive repeated blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def extract_fields(text: str) -> Dict[str, str]:
    text = clean_ocr_text(text)
    fields = {
        "patient_name": "Unknown",
        "medicine": "Not Found",
        "dosage": "Not Found",
        "date": "Not Found",
        "doctor_name": "Unknown",
        "hospital_name": "Unknown"
    }
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # ── 1. Doctor Name Extraction ─────────────────────────────────────────
    doc_match = re.search(
        r'(?i)(?:Dr\.?|Doctor|Consultant|Physician|Dr)\s*[:\-\.]?\s*([A-Za-z\s\.]{2,40})',
        text
    )
    if doc_match:
        doc_raw = doc_match.group(1).strip()
        doc_raw = re.split(r'(?i)\b(?:MBBS|MD|MS|BAMS|BHMS|DNB|Reg|Phone|Date)\b', doc_raw)[0].strip()
        doc_raw = re.sub(r'[^a-zA-Z\s\.]', '', doc_raw).strip()
        if doc_raw and len(doc_raw) > 2:
            fields["doctor_name"] = f"Dr. {doc_raw.replace('Dr.', '').strip()}"

    # ── 2. Hospital / Clinic Name Extraction ──────────────────────────────
    hosp_keywords = ["hospital", "clinic", "medical center", "healthcare", "nursing home", "care center", "speciality center"]
    for line in lines[:5]:  # Usually in top header lines
        if any(kw in line.lower() for kw in hosp_keywords):
            fields["hospital_name"] = line.strip()
            break

    # ── 3. Patient Name Extraction ────────────────────────────────────────
    name_match = re.search(
        r'(?i)(?:Patient\s*Name|Patient|Name|Pt\.?\s*Name)\s*[:\-\?=]?\s*([^\n]{1,60})',
        text
    )
    if name_match:
        raw_name = name_match.group(1).strip()
        raw_name = re.sub(
            r'(?i)^\s*(?:Mrs\.?|Miss\.?|Mr\.?|Ms\.?|Prof\.?|Dr\.?)\s*[,.]?\s*',
            '', raw_name
        ).strip()
        raw_name = re.split(
            r'(?i)\b(?:Age|Sex|D\.?O\.?B|Male|Female|Yrs|Years|Year)\b|'
            r'\bAge\s*/\s*Sex\b|'
            r'\s*[+\-]?\s*\d+\s*\.?\d*\s*(?:Yrs?|Years?)?\s*(?:\((?:Male|Female|M|F)\))?',
            raw_name
        )[0].strip()
        raw_name = re.sub(r'^[^a-zA-Z]+', '', raw_name)
        raw_name = re.sub(r'[^a-zA-Z\s]+$', '', raw_name)
        raw_name = re.sub(r'\s{2,}', ' ', raw_name).strip()
        if raw_name:
            fields["patient_name"] = raw_name

    # ── 4. Date Extraction ────────────────────────────────────────────────
    date_match = re.search(
        r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?\b|'
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
        text, re.IGNORECASE
    )
    if date_match:
        fields["date"] = date_match.group()

    # ── 5. Dosage & Frequency Extraction ──────────────────────────────────
    freq_match = re.search(r'(?i)\b\d-\d-\d\b|\b\d\s?[xX]\s?\d\b|\bonce\s+daily\b|\btwice\s+daily\b|\b(?:OD|BD|TDS|QID|STAT|HS|PRN)\b', text)
    strength_match = re.search(r'(?i)\b\d+\s*(?:mg|g|ml|mcg|puff|puffs)\b', text)

    if freq_match and strength_match and freq_match.group() != strength_match.group():
        fields["dosage"] = f"{strength_match.group()}, {freq_match.group()}"
    elif freq_match:
        fields["dosage"] = freq_match.group()
    elif strength_match:
        fields["dosage"] = strength_match.group()


    # ── 6. Medicine Extraction (Expanded Heuristics & Common Drugs) ───────
    common_medicines = [
        "Paracetamol", "Amoxicillin", "Ibuprofen", "Lisinopril", "Metformin",
        "Atorvastatin", "Omeprazole", "Azithromycin", "Ciprofloxacin", "Cetirizine",
        "Pantoprazole", "Dolo 650", "Dolo", "Augmentin", "Dispirin", "Combiflam"
    ]
    
    # Check if text directly contains a known medicine
    for med in common_medicines:
        if re.search(r'(?i)\b' + re.escape(med) + r'\b', text):
            fields["medicine"] = med
            break

    # If not found via exact match, check lines with keywords or Rx line
    if fields["medicine"] == "Not Found":
        address_keywords = ["road", "street", "colony", "nagar", "clinic", "hospital",
                            "ph:", "phone", "dr.", "dr ", "mob:", "mobile", "tel:"]
        
        rx_index = -1
        for i, line in enumerate(lines):
            if re.search(r'(?i)\brx\b', line):
                rx_index = i
                break

        for i, line in enumerate(lines):
            lower_line = line.lower()
            if any(kw in lower_line for kw in address_keywords) or sum(c.isdigit() for c in line) > 6:
                continue
            if re.search(r'\b\d{1,2}[/\-\.]\d{1,2}', line) or re.search(r'\d-\d-\d', line):
                continue
            if fields["patient_name"] != "Unknown" and fields["patient_name"].lower() in lower_line:
                continue

            has_med_keyword = re.search(r'(?i)\b(?:tab|tablet|cap|capsule|syr|syrup|inj|injection)\b', line)
            if has_med_keyword or (rx_index != -1 and i == rx_index + 1):
                if len(line) > 3:
                    fields["medicine"] = line.strip()
                    break

    logger.info(f"Extracted fields: {fields}")
    return fields

