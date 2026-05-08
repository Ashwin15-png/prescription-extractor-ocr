import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.database import SessionLocal, engine
from backend.app.models import Base, Prescription

def seed_database():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
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
            date="10/05/2023",
            raw_text="DR. JOHN DOE\nDate: 10/05/2023\nPatient: Alice Smith\nRx:\nAmoxicillin 500mg\n1-1-1 for 5 days"
        ),
        Prescription(
            patient_name="Bob Jones",
            medicine="Ibuprofen 400mg",
            dosage="1-0-1",
            date="12/05/2023",
            raw_text="CLINIC PLUS\nDate: 12/05/2023\nName: Bob Jones\nRx:\nIbuprofen 400mg\n1-0-1 as needed for pain"
        ),
        Prescription(
            patient_name="Charlie Davis",
            medicine="Lisinopril 10mg",
            dosage="1-0-0",
            date="15/05/2023",
            raw_text="HEART CARE CENTER\n15/05/2023\nCharlie Davis\nRx: Lisinopril 10mg\n1-0-0 daily"
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
