# 🎯 Week 1 Documentation: Prescription Extractor
**Project Review & Demo Explanation**

## 📘 1. Database Design

The system utilizes a **PostgreSQL** database to store both structured extracted fields and raw OCR text for reference and future model tuning. The migration from SQLite ensures better concurrency and production-readiness.

### Table: `prescriptions`

**Fields:**
- `id` (Integer, Primary Key)+
- `patient_name` (String)
- `medicine` (String)
- `dosage` (String)
- `date` (String)
- `raw_text` (Text)

**Entity Representation:**
```text
[ prescriptions ]
   |
   |-- id (PK)
   |-- patient_name
   |-- medicine
   |-- dosage
   |-- date
   |-- raw_text
```
*Brief Explanation:* The database stores both the raw output from the OCR engine and the parsed structured fields. This ensures that even if extraction rules fail, the raw data is preserved for manual correction.

---

## 📡 2. Backend API Design

The backend is powered by **FastAPI** and **PostgreSQL**, exposing RESTful endpoints for the frontend. It now also serves static frontend files and manages environment variables via `.env`.

### `POST /upload`
**Purpose:** Accepts a prescription image, runs OCR, and extracts structured fields.
- **Request:** `FormData` containing the image file.
- **Sample Response:**
```json
{
  "text": "Raw OCR output...",
  "fields": {
    "patient_name": "John Doe",
    "medicine": "Paracetamol",
    "dosage": "1-0-1",
    "date": "12/03/2023"
  }
}
```

### `POST /save`
**Purpose:** Stores the extracted and potentially user-edited data into the database.
- **Sample Request:**
```json
{
  "patient_name": "John Doe",
  "medicine": "Paracetamol",
  "dosage": "1-0-1",
  "date": "12/03/2023",
  "raw_text": "..."
}
```
- **Sample Response:**
```json
{
  "message": "Saved successfully",
  "id": 1
}
```

### `GET /prescriptions`
**Purpose:** Retrieves all stored prescription records for the dashboard.
- **Sample Response:**
```json
[
  {
    "id": 1,
    "patient_name": "John Doe",
    "medicine": "Paracetamol",
    "dosage": "1-0-1",
    "date": "12/03/2023"
  }
]
```

---

## 🔍 3. OCR + Extraction Logic

**OCR (Optical Character Recognition):**
- Implemented using **pytesseract** and OpenCV.
- Converts the uploaded prescription image into raw text through grayscale conversion and thresholding.

**Field Extraction:**
- **Date:** Extracted using regular expressions matching standard date formats (e.g., DD/MM/YYYY).
- **Dosage:** Detected using a specific pattern matching like `1-0-1` or `1-1-1`.
- **Patient Name:** Taken heuristically as the first valid line of the extracted text.
- **Medicine:** Improved heuristic that filters out address lines, contact details, and dates, picking up potential medicine names based on RX positioning and keywords (tab, cap, etc).

---

The UI has been upgraded from a basic functional layout to a **Premium Modern Aesthetic**.

**Features:**
- **Premium Design System:** Glassmorphism, electric indigo gradients, and Outfit/Inter typography.
- **Smart Upload Zone:** Drag-and-drop support with automatic processing upon file selection (no manual "Upload" click required).
- **Interactive Result Cards:** Structured fields and raw text displayed in sleek, responsive cards.
- **Micro-animations:** Smooth transitions and a custom AI processing loader.
- **Data Dashboard:** A polished, responsive data grid showing saved records with hover effects.

**Purpose:** To provide a seamless, high-end user experience that mimics a production-grade medical platform.

---

## 🎥 5. Week 1 Demo Flow

During the demo presentation, the following pipeline will be executed live:
1. **Open Upload Page:** Navigate to `http://localhost:8000/`.
2. **Select Image:** Upload a sample printed prescription image.
3. **Display Raw Text:** Show the raw OCR output returned from the backend.
4. **Display Structured Fields:** Show how the regex/heuristics mapped the text to structured form fields.
5. **Save Data:** Click the Save button to insert the record into **PostgreSQL**.
6. **View Dashboard:** Navigate to the dashboard to show the newly stored record via the `GET /prescriptions` API.
7. **Database Verification:** Open `psql` to show the record physically stored in the database.

---

| Component           | Status       | Notes                     |
| ------------------- | ------------ | ------------------------- |
| PostgreSQL Setup    | ✅ Completed | Migrated from SQLite      |
| FastAPI APIs        | ✅ Completed | Serving static files now  |
| OCR Integration     | ✅ Completed | Tesseract + OpenCV        |
| Field Extraction    | ✅ Completed | Regex + Heuristics        |
| Premium UI          | ✅ Completed | Fully redesigned          |
| Database Seeding    | ✅ Completed | Using `seed_data.py`      |
| Verification Guide  | ✅ Completed | Added `Verification_Guide.md` |
| System Debugging    | ✅ Completed | Resolved table auto-creation |
| CSV Export          | ✅ Completed | Integrated into Dashboard |

---

## 🧪 7. Week 1 Testing Summary

The following test scenarios have been added and validated to ensure a robust pipeline:

**Validation & Error Handling Cases:**
- **Valid Prescription Upload:** Returns 200 OK with extracted fields and raw OCR text.
- **Invalid File Upload:** Uploading non-image files (e.g., PDF, TXT) returns 400 Bad Request with `"error": "Invalid file type. Please upload an image."`
- **Missing Data / Empty Upload:** Attempting to upload without selecting a file returns 400 Bad Request with `"error": "No file uploaded"`
- **OCR Failure / Blank Image:** Images where no text can be extracted return 500 Internal Server Error with `"error": "OCR failed or returned empty text."`
- **Missing Required Fields (Save):** Attempting to save a record without patient name or medicine returns 400 Bad Request.

**Functional Cases:**
- **OCR Output:** Verified that text is reliably extracted from clear, printed prescription images.
- **Field Extraction:** Tested regex for dates and dosages, successfully isolating target strings.
- **Database Insertion:** Confirmed that **PostgreSQL** correctly stores both the raw text and the structured fields.
- **Fetch Records:** Confirmed `GET /prescriptions` successfully retrieves all records from the PostgreSQL instance.
- **Static File Serving:** Verified that visiting `http://localhost:8000/` correctly redirects to the index page.
- **Auto-Creation Debug:** Successfully resolved an issue where SQLAlchemy was not detecting models for table creation by implementing explicit model imports in `main.py`.
- **Comprehensive Verification:** Created a dedicated `Verification_Guide.md` for end-to-end system testing.
- **API Responses:** Verified all schema examples and error responses using Swagger UI (`/docs`) and the frontend network tab.

---

## 🎯 8. Final Summary

The system successfully demonstrates a complete working pipeline from image upload to structured data storage, fulfilling all Week 1 requirements. The focus has been on core functionality, modular design, and establishing a baseline for extensibility.

---

## 🚧 9. Future Enhancements (Next Steps)

While the base pipeline works, the following improvements can be implemented in future iterations:
1. **Advanced NLP for Extraction:** Move from basic regex to an NLP engine (like spaCy) or an LLM integration to handle variable structures and unstructured text.
2. **Handwriting Support:** Integrate advanced HTR (Handwritten Text Recognition) models as standard Tesseract struggles heavily with handwritten doctor prescriptions.
3. **Authentication & Security:** Add login portals for medical professionals and secure APIs with JWT tokens.
4. **PDF Generation:** Add the ability to generate a PDF report of the extracted data for patients.
5. **Batch Processing:** Allow users to upload multiple prescriptions at once for bulk extraction.
