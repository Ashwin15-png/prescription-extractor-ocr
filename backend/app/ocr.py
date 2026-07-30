import pytesseract
import cv2
import numpy as np
import os
import time
from typing import Dict, Any
from .config import settings
from .logger import logger

# ── Tesseract configuration ───────────────────────────────────────────────────
if os.path.exists(settings.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Maximum dimension to cap any image before processing (performance + memory)
MAX_DIMENSION = 2400   # px — larger images are downscaled to this width
DENOISE_H     = 8      # fastNlMeansDenoising strength (lower = faster + sufficient)


def _load_and_cap_image(image_path: str) -> np.ndarray | None:
    """
    Load image from disk and ensure it is within MAX_DIMENSION on the longest
    side.  This prevents huge TIFF / scan images from exhausting worker memory.
    Returns None if the file cannot be decoded.
    """
    t0 = time.perf_counter()
    img = cv2.imread(image_path)
    if img is None:
        logger.warning(f"cv2.imread returned None for: {image_path}")
        return None

    h, w = img.shape[:2]
    if max(h, w) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug(f"Image resized from {w}x{h} → {new_w}x{new_h}")

    logger.debug(f"Image load+cap: {time.perf_counter()-t0:.3f}s")
    return img


def _compute_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()


def deskew_image(img: np.ndarray) -> np.ndarray:
    """Detect skew and straighten the image in-place (best-effort)."""
    try:
        gray = _compute_gray(img)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return img
        largest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if 0.5 < abs(angle) < 45.0:
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(img, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
    except Exception as exc:
        logger.debug(f"Deskew skipped: {exc}")
    return img


def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Single-pass preprocessing pipeline (shared by both perform_ocr and
    analyze_image_quality to avoid duplicate OpenCV work):
      1. Deskew
      2. Grayscale
      3. Upscale only if below 1200 px wide
      4. CLAHE
      5. Fast denoise
      6. Adaptive threshold
    """
    if img is None:
        return img
    t0 = time.perf_counter()

    img = deskew_image(img)
    gray = _compute_gray(img)

    h, w = gray.shape[:2]
    if w < 1200:
        scale = 1200 / w
        gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    denoised = cv2.fastNlMeansDenoising(enhanced, h=DENOISE_H,
                                         templateWindowSize=7,
                                         searchWindowSize=21)

    result = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 11
    )
    logger.debug(f"Preprocess pipeline: {time.perf_counter()-t0:.3f}s")
    return result


def detect_document_type(text: str) -> str:
    """Classify the document from its raw OCR text."""
    tl = text.lower()
    if any(k in tl for k in ["hemoglobin","wbc","rbc","platelet","cholesterol",
                              "triglycerides","glucose","lab report","test result"]):
        return "Lab Report"
    elif any(k in tl for k in ["total amount","invoice","bill no","payment",
                                "receipt","charge","tax"]):
        return "Medical Bill"
    elif any(k in tl for k in ["clinical note","chief complaint",
                                "history of present illness","advice"]):
        return "Doctor Note"
    return "Prescription"


def perform_ocr(image_path: str) -> str:
    """
    Full OCR pipeline.  Never raises — always returns a string
    (may be an error message if Tesseract fails).
    """
    t_start = time.perf_counter()
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return "Error: Image file not found."

        t0 = time.perf_counter()
        img = _load_and_cap_image(image_path)
        if img is None:
            return "Error: Could not decode image file."
        logger.debug(f"Load image: {time.perf_counter()-t0:.3f}s")

        t0 = time.perf_counter()
        processed = preprocess_image(img)
        logger.debug(f"Preprocess: {time.perf_counter()-t0:.3f}s")

        t0 = time.perf_counter()
        text = pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
        logger.debug(f"Tesseract PSM6: {time.perf_counter()-t0:.3f}s")

        # Fallback to PSM 3 if output is suspiciously short
        if not text or len(text.strip()) < 15:
            t0 = time.perf_counter()
            gray = _compute_gray(img)
            _, thresh = cv2.threshold(gray, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh, config="--oem 3 --psm 3")
            logger.debug(f"Tesseract PSM3 fallback: {time.perf_counter()-t0:.3f}s")

        logger.info(f"perform_ocr total: {time.perf_counter()-t_start:.3f}s")
        return text.strip() if text else "No legible text extracted."

    except pytesseract.TesseractNotFoundError:
        msg = "Tesseract not installed or not found. Set TESSERACT_CMD in config."
        logger.error(msg)
        return f"EXTRACTION_FAILED: {msg}"
    except Exception as exc:
        logger.error(f"OCR pipeline error [{image_path}]: {exc}", exc_info=True)
        return f"EXTRACTION_FAILED: {exc}"


def analyze_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Compute OCR confidence + image quality metrics in a single image read.
    All expensive OpenCV work is done once.
    Returns a safe dictionary — never raises.
    """
    defaults: Dict[str, Any] = {
        "confidence": 85,
        "image_quality": 100,
        "blur_detected": False,
        "qr_code_data": "",
        "noise_level": 12,
        "skew_angle": 0.0,
        "rotation": 0,
        "contrast_score": 85,
        "brightness_score": 80,
        "readability_score": 85,
        "language": "English",
        "barcode": "None",
        "is_handwritten": False,
    }

    t_start = time.perf_counter()
    try:
        img = _load_and_cap_image(image_path)
        if img is None:
            return defaults

        gray = _compute_gray(img)

        # ── Blur / sharpness ──────────────────────────────────────────────────
        t0 = time.perf_counter()
        variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        defaults["image_quality"] = min(100, int(variance / 10))
        defaults["blur_detected"] = variance < 100
        logger.debug(f"Blur: {time.perf_counter()-t0:.3f}s")

        # ── Noise level ───────────────────────────────────────────────────────
        blur_diff = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = int(np.std(gray.astype(np.int16) - blur_diff.astype(np.int16)))
        defaults["noise_level"] = min(100, noise * 4)

        # ── Contrast & Brightness ─────────────────────────────────────────────
        defaults["brightness_score"] = min(100, int(np.mean(gray) / 255.0 * 100))
        defaults["contrast_score"]   = min(100, max(10, int(np.std(gray) * 2)))

        # ── Skew estimation (reuse blur from noise step) ──────────────────────
        t0 = time.perf_counter()
        blur9 = cv2.GaussianBlur(gray, (9, 9), 0)
        _, thresh_sk = cv2.threshold(blur9, 0, 255,
                                     cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel_sk = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate_sk = cv2.dilate(thresh_sk, kernel_sk, iterations=2)
        contours_sk, _ = cv2.findContours(dilate_sk,
                                           cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if contours_sk:
            largest = max(contours_sk, key=cv2.contourArea)
            rect = cv2.minAreaRect(largest)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if 0.1 < abs(angle) < 45.0:
                defaults["skew_angle"] = round(float(angle), 2)
        logger.debug(f"Skew: {time.perf_counter()-t0:.3f}s")

        # ── QR code ───────────────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            qr_decoder = cv2.QRCodeDetector()
            qr_data, _, _ = qr_decoder.detectAndDecode(img)
            if qr_data:
                defaults["qr_code_data"] = qr_data
                defaults["barcode"] = "QR Detected"
        except Exception as qr_exc:
            logger.debug(f"QR detection skipped: {qr_exc}")
        logger.debug(f"QR: {time.perf_counter()-t0:.3f}s")

        # ── OCR confidence (reuse preprocess_image) ───────────────────────────
        t0 = time.perf_counter()
        processed = preprocess_image(img)
        tess_data = pytesseract.image_to_data(
            processed, output_type=pytesseract.Output.DICT
        )
        scores = [
            int(c) for c in tess_data.get("conf", [])
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        if scores:
            avg_conf = int(sum(scores) / len(scores))
            defaults["confidence"]        = avg_conf
            defaults["readability_score"] = avg_conf
            defaults["is_handwritten"]    = avg_conf < 75
        logger.debug(f"OCR conf: {time.perf_counter()-t0:.3f}s")

    except Exception as exc:
        logger.warning(f"analyze_image_quality error: {exc}", exc_info=True)

    logger.info(f"analyze_image_quality total: {time.perf_counter()-t_start:.3f}s")
    return defaults


def process_and_analyze_image(image_path: str) -> tuple[str, Dict[str, Any]]:
    """
    Unified pipeline to load image once, preprocess once, extract text via OCR,
    and compute all image quality/analysis metrics in a single pass.
    """
    t_start = time.perf_counter()
    raw_text = "No legible text extracted."
    defaults: Dict[str, Any] = {
        "confidence": 85,
        "image_quality": 100,
        "blur_detected": False,
        "qr_code_data": "",
        "noise_level": 12,
        "skew_angle": 0.0,
        "rotation": 0,
        "contrast_score": 85,
        "brightness_score": 80,
        "readability_score": 85,
        "language": "English",
        "barcode": "None",
        "is_handwritten": False,
    }

    try:
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return "Error: Image file not found.", defaults

        t0 = time.perf_counter()
        img = _load_and_cap_image(image_path)
        if img is None:
            return "Error: Could not decode image file.", defaults
        logger.debug(f"[Unified] Load image: {time.perf_counter()-t0:.3f}s")

        gray = _compute_gray(img)

        # Blur/Sharpness
        t0 = time.perf_counter()
        variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        defaults["image_quality"] = min(100, int(variance / 10))
        defaults["blur_detected"] = variance < 100

        # Noise level
        blur_diff = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = int(np.std(gray.astype(np.int16) - blur_diff.astype(np.int16)))
        defaults["noise_level"] = min(100, noise * 4)

        # Contrast & Brightness
        defaults["brightness_score"] = min(100, int(np.mean(gray) / 255.0 * 100))
        defaults["contrast_score"]   = min(100, max(10, int(np.std(gray) * 2)))

        # Skew estimation
        blur9 = cv2.GaussianBlur(gray, (9, 9), 0)
        _, thresh_sk = cv2.threshold(blur9, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel_sk = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilate_sk = cv2.dilate(thresh_sk, kernel_sk, iterations=2)
        contours_sk, _ = cv2.findContours(dilate_sk, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if contours_sk:
            largest = max(contours_sk, key=cv2.contourArea)
            rect = cv2.minAreaRect(largest)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if 0.1 < abs(angle) < 45.0:
                defaults["skew_angle"] = round(float(angle), 2)

        # QR code
        try:
            qr_decoder = cv2.QRCodeDetector()
            qr_data, _, _ = qr_decoder.detectAndDecode(img)
            if qr_data:
                defaults["qr_code_data"] = qr_data
                defaults["barcode"] = "QR Detected"
        except Exception as qr_exc:
            logger.debug(f"[Unified] QR detection skipped: {qr_exc}")

        # Preprocess once for OCR and Confidence
        t0 = time.perf_counter()
        processed = preprocess_image(img)
        logger.debug(f"[Unified] Preprocess: {time.perf_counter()-t0:.3f}s")
        
        # OCR Output Text
        t0 = time.perf_counter()
        raw_text = pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
        
        # Fallback to PSM 3 if output is short
        if not raw_text or len(raw_text.strip()) < 15:
            _, thresh_fallback = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            raw_text = pytesseract.image_to_string(thresh_fallback, config="--oem 3 --psm 3")
        raw_text = raw_text.strip() if raw_text else "No legible text extracted."

        # OCR Confidence
        tess_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        scores = [
            int(c) for c in tess_data.get("conf", [])
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        if scores:
            avg_conf = int(sum(scores) / len(scores))
            defaults["confidence"]        = avg_conf
            defaults["readability_score"] = avg_conf
            defaults["is_handwritten"]    = avg_conf < 75

        logger.debug(f"[Unified] Tesseract & Conf: {time.perf_counter()-t0:.3f}s")

    except pytesseract.TesseractNotFoundError:
        msg = "Tesseract not installed or not found. Set TESSERACT_CMD in config."
        logger.error(msg)
        raw_text = f"EXTRACTION_FAILED: {msg}"
    except Exception as exc:
        logger.error(f"[Unified] OCR pipeline error [{image_path}]: {exc}", exc_info=True)
        raw_text = f"EXTRACTION_FAILED: {exc}"

    logger.info(f"[Unified] total: {time.perf_counter()-t_start:.3f}s")
    return raw_text, defaults

