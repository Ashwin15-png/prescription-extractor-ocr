import pytesseract
import cv2
import numpy as np
import os

# Set tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def perform_ocr(image_path: str) -> str:
    try:
        # Read image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return "Error: Could not read image."
        
        # Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Perform OCR
        text = pytesseract.image_to_string(thresh)
        return text
    except Exception as e:
        return f"OCR Error: {str(e)}"
