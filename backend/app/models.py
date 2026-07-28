from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean
from sqlalchemy.sql import func
from .database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(150), nullable=False, index=True)
    medicine = Column(String(200), nullable=False, index=True)
    dosage = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False, index=True)
    
    # Enhanced Healthcare SaaS Metadata Fields
    doctor_name = Column(String(150), nullable=True, default="Unknown", index=True)
    hospital_name = Column(String(200), nullable=True, default="Unknown", index=True)
    age = Column(String(20), nullable=True, default="N/A")
    gender = Column(String(20), nullable=True, default="N/A")
    document_type = Column(String(50), nullable=True, default="Prescription", index=True)
    
    raw_text = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True, default=0)
    
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
            "raw_text": self.raw_text or "",
            "confidence_score": self.confidence_score or 0,
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
