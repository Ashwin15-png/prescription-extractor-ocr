import re
from datetime import datetime
from typing import Optional, List, Dict, Any
import cv2
import numpy as np

def clean_ocr_raw_text(text: str) -> str:
    """Normalize raw OCR text by stripping unprintable control characters and extra linebreaks."""
    if not text:
        return ""
    # Strip non-printable ASCII control characters except newlines/tabs
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Collapse 3+ consecutive newlines to 2
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def parse_flexible_date(date_str: str) -> Optional[str]:
    """Parse various medical date formats (DD/MM/YYYY, YYYY-MM-DD, Month DD YYYY) into normalized DD/MM/YYYY."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Common date regex formats
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%Y-%m-%d", "%Y/%m/%d",
        "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
            
    # Regex fallback for embedded dates
    match = re.search(r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b', date_str)
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = "20" + year
        return f"{int(day):02d}/{int(month):02d}/{year}"
        
    return None

def normalize_medicine_name(raw_name: str) -> str:
    """Clean and normalize medicine strings by stripping dosage forms and suffixes."""
    if not raw_name:
        return "Unknown"
        
    cleaned = re.sub(r'(?i)\b(?:tab|tablet|cap|capsule|syr|syrup|inj|injection|oint|ointment|sol|solution)\b\.?', '', raw_name)
    cleaned = re.sub(r'(?i)\b\d+\s*(?:mg|g|ml|mcg|unit|units|puff|puffs)\b', '', cleaned)
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', '', cleaned)
    return cleaned.strip().title() or raw_name.strip().title()

def string_similarity(s1: str, s2: str) -> float:
    """Calculate normalized similarity ratio (0.0 to 1.0) between two strings using Levenshtein distance."""
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
        
    len1, len2 = len(s1), len(s2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
        
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Deletion
                dp[i][j - 1] + 1,       # Insertion
                dp[i - 1][j - 1] + cost # Substitution
            )
            
    max_len = max(len1, len2)
    return 1.0 - (dp[len1][len2] / max_len)

def calculate_blur_score(image: np.ndarray) -> float:
    """Calculate variance of Laplacian as an image sharpness blur metric (higher = sharper)."""
    if image is None:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())
