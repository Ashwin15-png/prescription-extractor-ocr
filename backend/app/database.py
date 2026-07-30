import os
import time
from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
from .logger import logger

DATABASE_URL = settings.DATABASE_URL

# Normalize postgres:// to postgresql:// for SQLAlchemy compatibility (e.g. Render/Neon)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Database target: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'Local/SQLite'}")

# Engine creation parameters
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800  # Recycle connections every 30 mins
    engine_kwargs["pool_pre_ping"] = True # Test connections before issuing queries

def create_db_engine():
    try:
        eng = create_engine(DATABASE_URL, **engine_kwargs)
        # Test connection ping
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("SQLAlchemy Engine created and connected successfully.")
        return eng
    except Exception as e:
        logger.error(f"Error connecting to primary database: {e}")
        fallback_url = "sqlite:///./prescription_extractor.db"
        logger.warning(f"Falling back to local SQLite database: {fallback_url}")
        eng = create_engine(fallback_url, connect_args={"check_same_thread": False})
        return eng

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def auto_migrate():
    """Ensure database tables and columns are created and updated automatically."""
    try:
        from .models import Prescription, User # Explicit model imports to populate Base.metadata
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)


        if "prescriptions" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("prescriptions")]
            with engine.connect() as conn:
                if "doctor_name" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN doctor_name VARCHAR DEFAULT 'Unknown'"))
                if "hospital_name" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN hospital_name VARCHAR DEFAULT 'Unknown'"))
                if "confidence_score" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN confidence_score INTEGER DEFAULT 0"))
                if "age" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN age VARCHAR DEFAULT 'N/A'"))
                if "gender" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN gender VARCHAR DEFAULT 'N/A'"))
                if "document_type" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN document_type VARCHAR DEFAULT 'Prescription'"))
                if "created_at" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                if "updated_at" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                
                # Enterprise Document Intelligence Fields
                for field, t in [("hospital_address", "TEXT"), ("registration_num", "VARCHAR"), 
                                 ("generic_name", "VARCHAR"), ("strength", "VARCHAR"),
                                 ("frequency", "VARCHAR"), ("duration", "VARCHAR"),
                                 ("diagnosis", "TEXT"), ("symptoms", "TEXT"), 
                                 ("department", "VARCHAR"), ("follow_up_date", "VARCHAR"),
                                 ("report_num", "VARCHAR"), ("lab_tests", "TEXT"), 
                                 ("qr_code_data", "TEXT")]:
                    if field not in columns:
                        conn.execute(text(f"ALTER TABLE prescriptions ADD COLUMN {field} {t} DEFAULT NULL"))

                # OCR Engine Audit & Location Columns
                for field, t in [("ocr_clean_text", "TEXT"), ("blur_score", "INTEGER"),
                                 ("qr_code", "TEXT"), ("latitude", "VARCHAR"),
                                 ("longitude", "VARCHAR"), ("country", "VARCHAR"),
                                 ("state", "VARCHAR"), ("city", "VARCHAR")]:
                    if field not in columns:
                        conn.execute(text(f"ALTER TABLE prescriptions ADD COLUMN {field} {t} DEFAULT NULL"))

                if "image_quality_score" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN image_quality_score INTEGER DEFAULT 100"))
                if "blur_detected" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN blur_detected BOOLEAN DEFAULT FALSE"))
                    
                # Phase 6 Enterprise Filter Engine Additions
                for field, t in [("noise_level", "INTEGER DEFAULT 0"), 
                                 ("skew_angle", "REAL DEFAULT 0.0"),
                                 ("rotation", "INTEGER DEFAULT 0"), 
                                 ("contrast_score", "INTEGER DEFAULT 100"),
                                 ("brightness_score", "INTEGER DEFAULT 100"),
                                 ("readability_score", "INTEGER DEFAULT 100"),
                                 ("language", "VARCHAR DEFAULT 'English'"),
                                 ("barcode", "VARCHAR DEFAULT NULL"),
                                 ("is_handwritten", "BOOLEAN DEFAULT FALSE"),
                                 ("medicine_category", "VARCHAR DEFAULT NULL"),
                                 ("doctor_specialty", "VARCHAR DEFAULT NULL"),
                                 ("hospital_type", "VARCHAR DEFAULT NULL"),
                                 ("is_emergency", "BOOLEAN DEFAULT FALSE"),
                                 ("is_inpatient", "BOOLEAN DEFAULT FALSE"),
                                 ("is_outpatient", "BOOLEAN DEFAULT FALSE")]:
                    if field not in columns:
                        conn.execute(text(f"ALTER TABLE prescriptions ADD COLUMN {field} {t}"))
                    
                conn.commit()
                logger.info("Database schema auto-migration check complete.")
    except Exception as e:
        logger.warning(f"Auto-migration notice: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()
