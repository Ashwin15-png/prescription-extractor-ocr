import pytesseract
import cv2
import numpy as np
import os
from typing import Tuple, Dict, Any
from .config import settings
from .logger import logger


# Configure tesseract executable path if specified and exists
if os.path.exists(settings.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def deskew_image(img: np.ndarray) -> np.ndarray:
    """Detect text orientation angle and rotate image to deskew scanned documents."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Dilate to join text characters into continuous blocks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours and minimum area rectangle
        contours, _ = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return img
            
        largest_contour = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Rotate image if skew angle is significant (> 0.5 degrees and < 45 degrees)
        if abs(angle) > 0.5 and abs(angle) < 45.0:
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
    except Exception as e:
        logger.warning(f"Deskewing notice: {e}")
        
    return img

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Advanced Multi-Stage Image Preprocessing Pipeline:
       1. Deskewing
       2. Grayscale conversion
       3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
       4. Rescaling low-res images
       5. Non-local Means Denoising
       6. Gaussian Adaptive Thresholding
    """
    if img is None:
        return img

    # 1. Deskew
    img = deskew_image(img)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # 3. Rescale low-resolution images
    h, w = gray.shape[:2]
    if w < 1200:
        scale = 1200 / w
        gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # 4. CLAHE for contrast enhancement on faint handwriting/faded ink
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 5. Denoising
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)

    # 6. Adaptive Thresholding for non-uniform lighting
    adaptive_thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 11
    )

    return adaptive_thresh

def detect_document_type(text: str) -> str:
    """Categorize document into Prescription, Lab Report, Medical Bill, or Doctor Note."""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ["hemoglobin", "wbc", "rbc", "platelet", "cholesterol", "triglycerides", "glucose", "lab report", "test result"]):
        return "Lab Report"
    elif any(k in text_lower for k in ["total amount", "invoice", "bill no", "payment", "receipt", "charge", "tax"]):
        return "Medical Bill"
    elif any(k in text_lower for k in ["clinical note", "diagnosis", "chief complaint", "history of present illness", "advice"]):
        return "Doctor Note"
    else:
        return "Prescription"

def perform_ocr(image_path: str) -> str:
    """Run full OCR pipeline returning cleaned raw text."""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found at: {image_path}")
            return "Error: Image file not found."

        img = cv2.imread(image_path)
        if img is None:
            return "Error: Could not read image file."

        # Process image
        processed = preprocess_image(img)

        # Execute Tesseract OCR with Page Segmentation Mode 6 (uniform block of text)
        text = pytesseract.image_to_string(processed, config='--oem 3 --psm 6')

        # Fallback to PSM 3 (Fully automatic page segmentation) if output is short
        if not text or len(text.strip()) < 15:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 3')

        return text.strip() if text else "No legible text extracted."
    except Exception as e:
        err_msg = f"OCR Error: {e}"
        logger.error(f"OCR Error processing {image_path}: {e}")
        # Return the actual error message so the user can see what failed in the cloud
        return f"EXTRACTION_FAILED:\n{err_msg}\nPlease ensure Tesseract is installed in the deployment environment."

def analyze_image_quality(image_path: str) -> Dict[str, Any]:
    """Calculate average OCR confidence score, blur metrics, and detect QR codes."""
    metrics = {
        "confidence": 85,
        "image_quality": 100,
        "blur_detected": False,
        "qr_code_data": ""
    }
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return metrics
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Blur Detection using Laplacian Variance
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        metrics["image_quality"] = min(100, int(variance / 10))
        metrics["blur_detected"] = variance < 100
        
        # QR Code Detection
        qr_decoder = cv2.QRCodeDetector()
        data, bbox, _ = qr_decoder.detectAndDecode(img)
        if data:
            metrics["qr_code_data"] = data

        processed = preprocess_image(img)
        tess_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        scores = [int(c) for c in tess_data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
        if scores:
            metrics["confidence"] = int(sum(scores) / len(scores))
            
    except Exception as e:
        logger.warning(f"Image analysis error: {e}")
        
    return metrics
