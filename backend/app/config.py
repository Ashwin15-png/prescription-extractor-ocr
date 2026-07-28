import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Explicitly load .env file from project root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(dotenv_path=env_path, override=True)


class Settings(BaseModel):
    PROJECT_NAME: str = "Prescription Extractor"
    VERSION: str = "2.0.0"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./prescription_extractor.db"
    )
    
    # Uploads
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    
    # OCR
    TESSERACT_CMD: str = os.getenv(
        "TESSERACT_CMD", 
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    
    # CORS
    CORS_ORIGINS: list = ["*"]

settings = Settings()
