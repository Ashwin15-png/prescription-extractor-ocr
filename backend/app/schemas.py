from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PrescriptionCreate(BaseModel):
    patient_name: str = Field(..., description="Name of the patient", example="John Doe")
    medicine: str = Field(..., description="Prescribed medicine/drug name", example="Amoxicillin 500mg")
    dosage: str = Field(..., description="Dosage and frequency instructions", example="1-0-1")
    date: str = Field(..., description="Prescription issue date", example="12/05/2024")
    doctor_name: Optional[str] = Field("Unknown", description="Attending doctor name", example="Dr. Smith")
    hospital_name: Optional[str] = Field("Unknown", description="Hospital or clinic name", example="City Care Hospital")
    raw_text: str = Field(..., description="Raw text extracted by OCR engine", example="Raw OCR output text...")
    confidence_score: Optional[int] = Field(0, description="OCR confidence percentage (0-100)", example=92)

class PrescriptionUpdate(BaseModel):
    patient_name: Optional[str] = None
    medicine: Optional[str] = None
    dosage: Optional[str] = None
    date: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None

class PrescriptionResponse(BaseModel):
    id: int
    patient_name: str
    medicine: str
    dosage: str
    date: str
    doctor_name: Optional[str] = "Unknown"
    hospital_name: Optional[str] = "Unknown"
    raw_text: Optional[str] = ""
    confidence_score: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ExtractedFields(BaseModel):
    patient_name: str = "Unknown"
    medicine: str = "Not Found"
    dosage: str = "Not Found"
    date: str = "Not Found"
    doctor_name: str = "Unknown"
    hospital_name: str = "Unknown"

class UploadResponse(BaseModel):
    raw_text: str
    extracted_fields: ExtractedFields
    ocr_confidence: int
    is_duplicate: bool = False
    duplicate_record_id: Optional[int] = None

class AnalyticsResponse(BaseModel):
    total_prescriptions: int
    todays_uploads: int
    most_common_medicine: str
    most_common_dosage: str
    recent_uploads: int
    avg_confidence: float

class HealthCheckResponse(BaseModel):
    status: str
    environment: str
    database: str
    version: str
