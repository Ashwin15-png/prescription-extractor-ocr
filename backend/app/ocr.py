import pytesseract
import cv2
import numpy as np
import os
from .config import settings
from .logger import logger

# Configure tesseract executable path if specified and exists
if os.path.exists(settings.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Multi-stage preprocessing pipeline for prescription images:
       1. Grayscale conversion
       2. Resize if small
       3. Denoising
       4. Adaptive Thresholding
    """
    if img is None:
        return img
        
    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # 2. Scale up low-resolution images
    height, width = gray.shape[:2]
    if width < 1000:
        scale = 1000 / width
        gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
    # 3. Denoising
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 4. Adaptive Thresholding for varying illumination
    adaptive_thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 21, 11
    )
    
    return adaptive_thresh

def perform_ocr(image_path: str) -> str:
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found at: {image_path}")
            return "Error: Image file not found."

        img = cv2.imread(image_path)
        if img is None:
            return "Error: Could not read image."
        
        # Primary preprocessing: Adaptive Thresholding
        processed_img = preprocess_image(img)
        text = pytesseract.image_to_string(processed_img, config='--oem 3 --psm 6')
        
        # Fallback: Standard Otsu Thresholding if primary output is empty
        if not text or not text.strip():
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 3')

        return text.strip()
    except Exception as e:
        logger.error(f"OCR Error processing {image_path}: {e}")
        return f"OCR Error: {str(e)}"

def get_ocr_confidence(image_path: str) -> int:
    """Return average OCR confidence (0-100) using pytesseract image_to_data."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0
        processed_img = preprocess_image(img)
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        scores = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
        return round(sum(scores) / len(scores)) if scores else 75
    except Exception as e:
        logger.warning(f"Confidence score calculation fallback: {e}")
        return 75

