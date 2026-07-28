import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
from .logger import logger

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Connecting to database target: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'Local/SQLite'}")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
        pool_pre_ping=True if DATABASE_URL.startswith("postgresql") else False
    )
    logger.info("SQLAlchemy Engine created successfully.")
except Exception as e:
    logger.error(f"Error creating SQLAlchemy Engine: {e}")
    fallback_url = "sqlite:///./prescription_extractor.db"
    logger.warning(f"Falling back to local database: {fallback_url}")
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def auto_migrate():
    """Ensure existing DB tables have new columns added automatically."""
    try:
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
                if "created_at" not in columns:
                    conn.execute(text("ALTER TABLE prescriptions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()
                logger.info("Database schema auto-migration check complete.")
    except Exception as e:
        logger.warning(f"Auto-migration check notice: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


