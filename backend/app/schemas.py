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

    hospital_address: Optional[str] = ""
    registration_num: Optional[str] = ""
    generic_name: Optional[str] = ""
    strength: Optional[str] = ""
    frequency: Optional[str] = ""
    duration: Optional[str] = ""
    diagnosis: Optional[str] = ""
    symptoms: Optional[str] = ""
    department: Optional[str] = ""
    follow_up_date: Optional[str] = ""
    report_num: Optional[str] = ""
    lab_tests: Optional[str] = ""
    qr_code_data: Optional[str] = ""

class OCRUploadResponse(BaseModel):
    raw_text: str
    extracted_fields: ExtractedFields
    ocr_confidence: int = Field(..., description="Average OCR confidence score 0-100")
    image_quality_score: int = Field(100, description="Evaluated Image Clarity 0-100")
    blur_detected: bool = Field(False, description="Flag indicating potential blur limit")
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
    
    hospital_address: Optional[str] = ""
    registration_num: Optional[str] = ""
    generic_name: Optional[str] = ""
    strength: Optional[str] = ""
    frequency: Optional[str] = ""
    duration: Optional[str] = ""
    diagnosis: Optional[str] = ""
    symptoms: Optional[str] = ""
    department: Optional[str] = ""
    follow_up_date: Optional[str] = ""
    report_num: Optional[str] = ""
    lab_tests: Optional[str] = ""
    qr_code_data: Optional[str] = ""

    raw_text: Optional[str] = ""
    ocr_clean_text: Optional[str] = ""
    confidence_score: Optional[int] = 0
    image_quality_score: Optional[int] = 100
    blur_score: Optional[int] = 0
    blur_detected: Optional[bool] = False
    qr_code: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    country: Optional[str] = "India"
    state: Optional[str] = ""
    city: Optional[str] = ""

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
    
    hospital_address: Optional[str] = ""
    registration_num: Optional[str] = ""
    generic_name: Optional[str] = ""
    strength: Optional[str] = ""
    frequency: Optional[str] = ""
    duration: Optional[str] = ""
    diagnosis: Optional[str] = ""
    symptoms: Optional[str] = ""
    department: Optional[str] = ""
    follow_up_date: Optional[str] = ""
    report_num: Optional[str] = ""
    lab_tests: Optional[str] = ""
    qr_code_data: Optional[str] = ""

    raw_text: Optional[str] = ""
    ocr_clean_text: Optional[str] = ""
    confidence_score: Optional[int] = 0
    image_quality_score: Optional[int] = 100
    blur_score: Optional[int] = 0
    blur_detected: Optional[bool] = False
    qr_code: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    country: Optional[str] = "India"
    state: Optional[str] = ""
    city: Optional[str] = ""
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
