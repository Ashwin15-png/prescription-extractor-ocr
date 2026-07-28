import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.database import SessionLocal, engine, auto_migrate
from backend.app.models import Base, Prescription

def seed_database():
    # Ensure tables and new columns exist
    Base.metadata.create_all(bind=engine)
    auto_migrate()
    
    db = SessionLocal()

    
    # Check if data already exists
    if db.query(Prescription).count() > 0:
        print("Database already contains data. Skipping seeding.")
        db.close()
        return

    sample_prescriptions = [
        Prescription(
            patient_name="Alice Smith",
            medicine="Amoxicillin 500mg",
            dosage="1-1-1",
            date="10/05/2026",
            doctor_name="Dr. John Doe",
            hospital_name="City Care Hospital",
            confidence_score=96,
            raw_text="CITY CARE HOSPITAL\nDr. John Doe, MD\nDate: 10/05/2026\nPatient Name: Alice Smith\nRx:\nAmoxicillin 500mg\n1-1-1 for 5 days"
        ),
        Prescription(
            patient_name="Bob Jones",
            medicine="Ibuprofen 400mg",
            dosage="1-0-1",
            date="12/05/2026",
            doctor_name="Dr. Sarah Jenkins",
            hospital_name="Clinic Plus Specialty Center",
            confidence_score=94,
            raw_text="CLINIC PLUS SPECIALTY CENTER\nDr. Sarah Jenkins\nDate: 12/05/2026\nName: Bob Jones\nRx:\nIbuprofen 400mg\n1-0-1 as needed for pain"
        ),
        Prescription(
            patient_name="Charlie Davis",
            medicine="Lisinopril 10mg",
            dosage="1-0-0",
            date="15/05/2026",
            doctor_name="Dr. Robert Vance",
            hospital_name="Heart Care Center",
            confidence_score=91,
            raw_text="HEART CARE CENTER\nDr. Robert Vance\nDate: 15/05/2026\nCharlie Davis\nRx: Lisinopril 10mg\n1-0-0 daily morning"
        ),
        Prescription(
            patient_name="Diana Prince",
            medicine="Metformin 500mg",
            dosage="1-0-1",
            date="18/05/2026",
            doctor_name="Dr. Marcus Brody",
            hospital_name="Apex Healthcare Center",
            confidence_score=98,
            raw_text="APEX HEALTHCARE CENTER\nDr. Marcus Brody\nDate: 18/05/2026\nPatient Name: Diana Prince\nRx: Metformin 500mg\n1-0-1 after meals"
        ),
        Prescription(
            patient_name="Edward Elric",
            medicine="Pantoprazole 40mg",
            dosage="1-0-0",
            date="20/05/2026",
            doctor_name="Dr. Roy Mustang",
            hospital_name="Central General Hospital",
            confidence_score=89,
            raw_text="CENTRAL GENERAL HOSPITAL\nDr. Roy Mustang\nDate: 20/05/2026\nName: Edward Elric\nRx: Pantoprazole 40mg\n1-0-0 before breakfast"
        )
    ]

    try:
        db.add_all(sample_prescriptions)
        db.commit()
        print(f"Successfully inserted {len(sample_prescriptions)} sample records into the database.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

