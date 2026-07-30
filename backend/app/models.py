from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean, Float
from sqlalchemy.sql import func
from .database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(150), nullable=False, index=True)
    medicine = Column(String(200), nullable=False, index=True)
    dosage = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False, index=True)
    
    # Enhanced Document Intelligence Fields
    doctor_name = Column(String(150), nullable=True, default="Unknown", index=True)
    hospital_name = Column(String(200), nullable=True, default="Unknown", index=True)
    hospital_address = Column(Text, nullable=True)
    registration_num = Column(String(100), nullable=True)
    
    age = Column(String(20), nullable=True, default="N/A")
    gender = Column(String(20), nullable=True, default="N/A")
    document_type = Column(String(50), nullable=True, default="Prescription", index=True)
    
    # Advanced Medication Fields
    generic_name = Column(String(200), nullable=True)
    strength = Column(String(50), nullable=True)
    frequency = Column(String(50), nullable=True)
    duration = Column(String(50), nullable=True)
    
    # Complete Diagnostics Fields
    diagnosis = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    department = Column(String(150), nullable=True)
    follow_up_date = Column(String(50), nullable=True)
    report_num = Column(String(100), nullable=True)
    lab_tests = Column(Text, nullable=True) # JSON or CSV string
    qr_code_data = Column(Text, nullable=True)
    
    # OCR Engine Audit Metrics
    raw_text = Column(Text, nullable=True)
    ocr_clean_text = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True, default=0)
    image_quality_score = Column(Integer, nullable=True, default=100)
    blur_score = Column(Integer, nullable=True, default=0)
    blur_detected = Column(Boolean, nullable=True, default=False)
    qr_code = Column(Text, nullable=True)
    
    # Location Metadata
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True, default="India")
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Phase 6 Enterprise Filter Engine Additions
    noise_level = Column(Integer, nullable=True, default=0)
    skew_angle = Column(Float, nullable=True, default=0.0)
    rotation = Column(Integer, nullable=True, default=0)
    contrast_score = Column(Integer, nullable=True, default=100)
    brightness_score = Column(Integer, nullable=True, default=100)
    readability_score = Column(Integer, nullable=True, default=100)
    language = Column(String(50), nullable=True, default="English")
    barcode = Column(String(100), nullable=True)
    is_handwritten = Column(Boolean, nullable=True, default=False)
    medicine_category = Column(String(100), nullable=True)
    doctor_specialty = Column(String(150), nullable=True)
    hospital_type = Column(String(100), nullable=True)
    is_emergency = Column(Boolean, nullable=True, default=False)
    is_inpatient = Column(Boolean, nullable=True, default=False)
    is_outpatient = Column(Boolean, nullable=True, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_patient_medicine', 'patient_name', 'medicine'),
        Index('idx_created_date', 'created_at', 'date'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "medicine": self.medicine,
            "dosage": self.dosage,
            "date": self.date,
            "doctor_name": self.doctor_name or "Unknown",
            "hospital_name": self.hospital_name or "Unknown",
            "age": self.age or "N/A",
            "gender": self.gender or "N/A",
            "document_type": self.document_type or "Prescription",
            
            "hospital_address": self.hospital_address or "",
            "registration_num": self.registration_num or "",
            "generic_name": self.generic_name or "",
            "strength": self.strength or "",
            "frequency": self.frequency or "",
            "duration": self.duration or "",
            "diagnosis": self.diagnosis or "",
            "symptoms": self.symptoms or "",
            "department": self.department or "",
            "follow_up_date": self.follow_up_date or "",
            "report_num": self.report_num or "",
            "lab_tests": self.lab_tests or "",
            "qr_code_data": self.qr_code_data or "",
            
            "raw_text": self.raw_text or "",
            "ocr_clean_text": self.ocr_clean_text or "",
            "confidence_score": self.confidence_score or 0,
            "image_quality_score": self.image_quality_score or 100,
            "blur_score": self.blur_score or 0,
            "blur_detected": self.blur_detected or False,
            "qr_code": self.qr_code or "",
            "latitude": self.latitude or "",
            "longitude": self.longitude or "",
            "country": self.country or "India",
            "state": self.state or "",
            "city": self.city or "",
            
            # Phase 6 Enterprise Filter Engine Additions
            "noise_level": self.noise_level or 0,
            "skew_angle": self.skew_angle or 0.0,
            "rotation": self.rotation or 0,
            "contrast_score": self.contrast_score or 100,
            "brightness_score": self.brightness_score or 100,
            "readability_score": self.readability_score or 100,
            "language": self.language or "English",
            "barcode": self.barcode or "",
            "is_handwritten": self.is_handwritten or False,
            "medicine_category": self.medicine_category or "",
            "doctor_specialty": self.doctor_specialty or "",
            "hospital_type": self.hospital_type or "",
            "is_emergency": self.is_emergency or False,
            "is_inpatient": self.is_inpatient or False,
            "is_outpatient": self.is_outpatient or False,
            
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(String(50), default="Staff") # Admin, Doctor, Staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
