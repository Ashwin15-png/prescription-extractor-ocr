import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Debugging connection info
print(f"--- DATABASE DEBUG ---")
print(f"Connecting to: {DATABASE_URL.split('@')[-1] if DATABASE_URL else 'None'}") 

if not DATABASE_URL:
    print("CRITICAL ERROR: DATABASE_URL is not set in environment!")

try:
    engine = create_engine(DATABASE_URL)
    print("SQLAlchemy Engine created successfully.")
except Exception as e:
    print(f"Error creating engine: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
