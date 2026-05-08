from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import shutil
import os
import uuid

from .database import get_db
from . import models
from .ocr import perform_ocr
from .extractor import extract_fields

router = APIRouter()

class PrescriptionCreate(BaseModel):
    patient_name: str = Field(..., example="John Doe")
    medicine: str = Field(..., example="Paracetamol")
    dosage: str = Field(..., example="1-0-1")
    date: str = Field(..., example="12/03/2023")
    raw_text: str = Field(..., example="Raw OCR text here...")

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file or not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file uploaded"})
        
    if not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Please upload an image."})
        
    # Save file
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{ext}"
    
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to save uploaded file."})
        
    # Run OCR
    raw_text = perform_ocr(filepath)
    if not raw_text or "OCR Error" in raw_text or raw_text.strip() == "":
        return JSONResponse(status_code=500, content={"error": "OCR failed or returned empty text."})
    
    # Extract fields
    extracted_data = extract_fields(raw_text)
    
    # Basic check if extraction mostly failed
    if all(v == "Not Found" for v in extracted_data.values()):
        return JSONResponse(status_code=422, content={"error": "Could not extract any structured fields from image.", "raw_text": raw_text})
    
    return {
        "raw_text": raw_text,
        "extracted_fields": extracted_data
    }

@router.post("/save")
def save_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    print("DATA RECEIVED:", prescription.model_dump())
    print("PATIENT NAME:", prescription.patient_name)

    if not prescription.patient_name or prescription.patient_name.strip() in ["", "Unknown", "Not Found"]:
        return JSONResponse(status_code=400, content={"error": "Invalid patient name"})
        
    if not prescription.medicine:
        return JSONResponse(status_code=400, content={"error": "Medicine is required."})
        
    try:
        db_prescription = models.Prescription(**prescription.model_dump())
        db.add(db_prescription)
        db.commit()
        db.refresh(db_prescription)
        return {"message": "Saved successfully", "id": db_prescription.id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Database save failed."})

@router.get("/prescriptions")
def get_prescriptions(db: Session = Depends(get_db)):
    return db.query(models.Prescription).all()
