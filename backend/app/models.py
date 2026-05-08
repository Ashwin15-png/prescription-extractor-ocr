from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, index=True)
    medicine = Column(String)
    dosage = Column(String)
    date = Column(String)
    raw_text = Column(Text)
