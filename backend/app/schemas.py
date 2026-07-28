from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExtractedFields(BaseModel):
    patient_name: str = Field(..., json_schema_extra={"example": "Alice Smith"})
    medicine: str = Field(..., json_schema_extra={"example": "Amoxicillin"})
    dosage: str = Field(..., json_schema_extra={"example": "500mg, 1-0-1"})
    date: str = Field(..., json_schema_extra={"example": "12/05/2026"})
    doctor_name: Optional[str] = Field("Unknown", json_schema_extra={"example": "Dr. John Doe"})
    hospital_name: Optional[str] = Field("Unknown", json_schema_extra={"example": "City Care Hospital"})
    age: Optional[str] = Field("N/A", json_schema_extra={"example": "34"})
    gender: Optional[str] = Field("N/A", json_schema_extra={"example": "Female"})
    document_type: Optional[str] = Field("Prescription", json_schema_extra={"example": "Prescription"})

class OCRUploadResponse(BaseModel):
    raw_text: str
    extracted_fields: ExtractedFields
    ocr_confidence: int = Field(..., description="Average OCR confidence score 0-100")
    is_duplicate: bool = Field(False, description="Flag indicating if a similar record exists")

class PrescriptionCreate(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=150)
    medicine: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., min_length=1, max_length=50)
    doctor_name: Optional[str] = "Unknown"
    hospital_name: Optional[str] = "Unknown"
    age: Optional[str] = "N/A"
    gender: Optional[str] = "N/A"
    document_type: Optional[str] = "Prescription"
    raw_text: Optional[str] = ""
    confidence_score: Optional[int] = 0

class PrescriptionResponse(BaseModel):
    id: int
    patient_name: str
    medicine: str
    dosage: str
    date: str
    doctor_name: Optional[str] = "Unknown"
    hospital_name: Optional[str] = "Unknown"
    age: Optional[str] = "N/A"
    gender: Optional[str] = "N/A"
    document_type: Optional[str] = "Prescription"
    raw_text: Optional[str] = ""
    confidence_score: Optional[int] = 0
    created_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "Staff"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class SuggestionsResponse(BaseModel):
    patients: List[str]
    medicines: List[str]
    doctors: List[str]
