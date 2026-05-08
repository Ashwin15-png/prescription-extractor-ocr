# 🏥 Prescription Extractor

A premium full-stack healthcare web application to upload prescription images, extract text using AI-powered OCR, and manage medical records with a structured database.

> [!TIP]
> **[Check the Verification Guide](./Verification_Guide.md)** to learn how to test the database and live website.

## 🏗️ Tech Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, pytesseract, OpenCV, python-dotenv
- **Frontend:** Premium Vanilla CSS (Glassmorphism), Vanilla JavaScript, Google Fonts (Outfit, Inter)
- **Database:** PostgreSQL (for production-ready data persistence)
- **Environment Management:** python-dotenv

## ⚙️ Prerequisites

1. **Python 3.8+**
2. **PostgreSQL:** Ensure you have a running PostgreSQL instance.
3. **Tesseract-OCR:** You must install Tesseract OCR on your machine.
   - Install to: `C:\Program Files\Tesseract-OCR\tesseract.exe` (Windows)
4. **Environment Variables:** Create a `.env` file in the `backend/` directory with your `DATABASE_URL`.

## 🚀 Setup & Run Instructions

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Database Seeding (Optional)
Run the seeding script to populate the database with sample data:
```bash
python seed_data.py
```

### 3. Run the Backend
```bash
cd backend
python run.py
```
The application will be available at **`http://localhost:8000`**. The backend now serves the frontend automatically.

## ✨ Features

- **Premium UI/UX:** A modern, glassmorphic design system for a high-end feel.
- **AI Extraction:** Automatic field extraction for Patient Name, Date, Medicine, and Dosage.
- **Smart Upload:** Drag-and-drop or click to upload; processing starts automatically.
- **Data Dashboard:** View and refresh stored medical records in a sleek data grid.

## 📂 Project Structure

- `backend/`: FastAPI core, PostgreSQL models, and OCR logic.
- `frontend/`: 
  - `web/`: Premium HTML/CSS/JS frontend files.
  - `streamlit/`: Test environment for OCR validation.
- `uploads/`: Temporary image storage for processing.
- `seed_data.py`: Utility script for database initialization.
