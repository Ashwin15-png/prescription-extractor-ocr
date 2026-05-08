# ✅ Verification Guide: Prescription Extractor

This guide explains how to verify that the PostgreSQL database and the Web application are working correctly.

---

## 🗄️ 1. Database Verification (CLI)

Use your PostgreSQL terminal (`psql`) to verify the data storage.

### Step 1: Connect to the database
```bash
psql -U ashwin -d ashwin_db
```
*(Enter password `ashwin12345` when prompted)*

### Step 2: List tables
```sql
\dt
```
**Expected Output:** You should see a table named `prescriptions`.

### Step 3: Check table structure
```sql
\d prescriptions
```
**Expected Output:** Columns `id`, `patient_name`, `medicine`, `dosage`, `date`, and `raw_text` should be present.

### Step 4: View records
```sql
SELECT id, patient_name, medicine FROM prescriptions;
```

---

## 🌐 2. Website Verification (End-to-End)

Follow these steps to test the full live pipeline.

### Step 1: Open the Application
Navigate to: **`http://localhost:8000/`**

### Step 2: Extract a Prescription
1.  Go to **"New Extraction"**.
2.  Click the **"Select Image"** button and pick a prescription image.
3.  Wait for the AI loader to finish.
4.  Verify that the "Structured Fields" are auto-populated.

### Step 3: Save to Database
1.  Click the **"Save to Database"** button.
2.  You should see an alert: `"Prescription saved successfully!"`.

### Step 4: Verify in Dashboard
1.  You will be redirected to the **Dashboard**.
2.  The new record should appear at the top of the table.

---

## 🚀 3. API Verification (Swagger UI)

FastAPI provides an interactive documentation page to test APIs directly.

1.  Visit: **`http://localhost:8000/docs`**
2.  Expand the **`GET /prescriptions`** endpoint.
3.  Click **"Try it out"** -> **"Execute"**.
4.  **Expected Output:** A 200 OK response with a list of all prescriptions in JSON format.

---

## 🛠️ Troubleshooting
- **404 Not Found at `/`**: Ensure the backend is running (`python run.py`) and that `main.py` is configured to serve static files.
- **Connection Error**: Check your `.env` file and ensure PostgreSQL service is running.
- **OCR Failed**: Ensure Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
