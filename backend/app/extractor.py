import re
from typing import Dict

def extract_fields(text: str) -> Dict[str, str]:
    fields = {
        "patient_name": "Not Found",
        "medicine": "Not Found",
        "dosage": "Not Found",
        "date": "Not Found"
    }
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Robust rule: Regex for Patient Name / Name
    name_match = re.search(r'(?i)(?:Patient Name|Name)[?:]\s*([a-zA-Z\s\,\.]+)', text)
    if name_match:
        raw_name = name_match.group(1).strip()
        # Clean extracted name: remove Mr, Mrs, commas, stop at Age/Sex
        raw_name = re.sub(r'(?i)\b(?:Mr|Mrs|Ms|Dr)\b\.?,?\s*', '', raw_name)
        raw_name = raw_name.replace(',', '').strip()
        if re.search(r'(?i)\b(?:Age|Sex)\b', raw_name):
            raw_name = re.split(r'(?i)\b(?:Age|Sex)\b', raw_name)[0].strip()
        
        # Remove trailing non-alphabetic chars
        raw_name = re.sub(r'[^a-zA-Z\s]+$', '', raw_name).strip()
        
        fields["patient_name"] = raw_name if raw_name else "Unknown"
    else:
        fields["patient_name"] = "Unknown"
        
    # Date Regex DD/MM/YYYY, DD.MM.YYYY, with optional time
    date_match = re.search(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}(?:[/\s]\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?\b', text)
    if date_match:
        fields["date"] = date_match.group()
        
    # Dosage Regex e.g., 1-0-1, 1-1-1, 1x2, once daily
    dosage_match = re.search(r'(?i)\b\d-\d-\d\b|\b\d\s?[xX]\s?\d\b|\bonce daily\b', text)
    if dosage_match:
        fields["dosage"] = dosage_match.group()
        
    # Medicine extraction (Robust Heuristic)
    address_keywords = ["road", "street", "colony", "nagar", "clinic", "hospital", "ph:", "phone", "dr.", "dr "]
    
    rx_index = -1
    for i, line in enumerate(lines):
        if re.search(r'(?i)\brx\b', line):
            rx_index = i
            break
            
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        # Avoid address/contact lines
        if any(kw in lower_line for kw in address_keywords) or sum(c.isdigit() for c in line) > 6:
            continue
            
        # Avoid date/dosage lines
        if re.search(r'\b\d{1,2}[/\-\.]\d{1,2}', line) or re.search(r'\d-\d-\d', line):
            continue
            
        # Avoid patient name match
        if fields["patient_name"] != "Unknown" and fields["patient_name"].lower() in lower_line:
            continue
            
        # Pick line if it has medicine keywords or is immediately after Rx
        has_med_keyword = re.search(r'(?i)\b(?:tab|tablet|cap|capsule|syr|syrup|inj|injection)\b', line)
        if has_med_keyword or (rx_index != -1 and i == rx_index + 1):
            if fields["medicine"] == "Not Found" and len(line) > 3:
                fields["medicine"] = line
                
    # 🔍 MANDAOTRY DEBUG LOGGING
    print("--- EXTRACTION DEBUG ---")
    print("RAW TEXT:\n", text)
    print("MATCHED NAME:", fields["patient_name"])
    print("MATCHED DATE:", fields["date"])
    print("MATCHED DOSAGE:", fields["dosage"])
    print("MATCHED MEDICINE:", fields["medicine"])
    print("------------------------")
                
    return fields
