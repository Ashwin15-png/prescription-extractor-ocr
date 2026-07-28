from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, index=True, nullable=False)
    medicine = Column(String, index=True, nullable=False)
    dosage = Column(String, nullable=True)
    date = Column(String, index=True, nullable=True)
    doctor_name = Column(String, default="Unknown", nullable=True)
    hospital_name = Column(String, default="Unknown", nullable=True)
    raw_text = Column(Text, nullable=True)
    confidence_score = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=True)

