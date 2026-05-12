# 🏥 Prescription Extractor - AI Powered Healthcare OCR

A premium, production-grade healthcare platform designed to digitize handwritten prescriptions using advanced AI-powered OCR. This project transforms messy medical paperwork into structured, searchable digital records with a stunning, modern UI.

> [!TIP]
> **[Check the Verification Guide](./Verification_Guide.md)** to learn how to test the database and live website.

## ✨ Premium Features

- **🎨 Modern SaaS Aesthetic:** A high-end interface featuring glassmorphism, electric indigo gradients, and smooth micro-animations.
- **🧠 AI-Powered OCR:** Real-time text extraction using Tesseract OCR, with automatic identification of patient names, dates, medicines, and dosages.
- **📂 Interactive Dashboard:** A comprehensive analytics-style dashboard to manage medical records, complete with search, filtering, and CSV export.
- **⚡ Smart Workflow:** Drag-and-drop upload functionality with real-time processing animations and instant validation badges.
- **📱 Responsive Design:** Fully optimized for desktop, tablet, and mobile devices.

## 🏗️ Tech Stack

- **Backend:** FastAPI (Python), PostgreSQL, SQLAlchemy
- **OCR Engine:** Tesseract OCR, OpenCV
- **Frontend:** Premium Vanilla HTML/CSS/JS (No frameworks, lightweight)
- **Design System:** Glassmorphism, Google Fonts (Outfit, Inter, Poppins)
- **Database:** PostgreSQL (Hosted on Neon or Local)

## ⚙️ Prerequisites

1. **Python 3.8+**
2. **PostgreSQL:** A running instance (Local or Neon.tech).
3. **Tesseract-OCR:** Required for text extraction.
   - Install to: `C:\Program Files\Tesseract-OCR\tesseract.exe` (Windows default)
4. **Environment Variables:** Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

## 🚀 Setup & Run Instructions

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Database Initialization
Populate the database with sample records to see the dashboard in action:
```bash
python seed_data.py
```

### 3. Run the Application
```bash
cd backend
python run.py
```
The application will be live at **`http://localhost:8000`**.

## 📂 Project Structure

- `backend/`: FastAPI core, PostgreSQL models, and OCR logic.
- `frontend/web/`: Premium UI assets (HTML, CSS, JS).
- `uploads/`: Temporary storage for processed images.
- `seed_data.py`: Database initialization script.

---

*Developed with ❤️ for the Healthcare Community.*
