# ✅ Verification Guide: Prescription Extractor

This guide explains how to verify that the AI OCR pipeline, PostgreSQL database, and the Premium Web UI are functioning correctly.

---

## 🌐 1. Website Verification (End-to-End)

Follow these steps to test the full live pipeline from the browser.

### Step 1: Open the Application
Navigate to: **`http://localhost:8000/`**
- **Expected Result:** You should see the premium landing page with animated backgrounds and the "PrescriptionX" logo.

### Step 2: Upload & Extract
1. Click **"Start Extracting"** or **"Upload Now"**.
2. **Drag and Drop** a prescription image onto the blue upload zone, or click to select a file.
3. Observe the **AI Loader**: You should see a pulse animation and a progress bar.
4. **Verify Extraction:** 
   - The "Raw OCR Output" should appear on the left.
   - The "Extracted Data" fields (Name, Medicine, etc.) should be auto-populated on the right.

### Step 3: Save to Database
1. Click the **"Confirm & Save"** button.
2. Watch for the **Toast Notification**: A green success message should appear at the bottom right.
3. You will be automatically redirected to the **Dashboard**.

### Step 4: Dashboard Analytics
1. Verify the **Stat Cards**: "Total Records" and "Recent Uploads" should have updated.
2. Search: Use the **Search Box** to find your newly added record by patient name.
3. Export: Click **"Export CSV"** to verify data portability.

---

## 🗄️ 2. Database Verification (CLI)

Use your PostgreSQL terminal (`psql`) to verify the data storage on the backend.

### Step 1: Connect to the database
```bash
psql -U your_user -d your_db
```

### Step 2: Query the Records
```sql
-- Check total count
SELECT count(*) FROM prescriptions;

-- View the most recent entry
SELECT patient_name, medicine, date FROM prescriptions ORDER BY id DESC LIMIT 1;
```

---

## 🚀 3. API Verification (Swagger UI)

FastAPI provides an interactive documentation page to test the raw JSON output.

1. Visit: **`http://localhost:8000/docs`**
2. Expand **`GET /prescriptions`** and click **"Try it out"** -> **"Execute"**.
3. **Expected Output:** A 200 OK response with a JSON array containing all prescription records.

---

## 🛠️ Troubleshooting

- **No Data in Dashboard?** Run `python seed_data.py` to populate the DB with sample entries.
- **OCR Not Extracting?** 
  - Ensure Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  - Check the terminal for any `TesseractNotFoundError` or `PermissionDenied` errors.
- **UI Not Loading?** Ensure you are running the backend from the root directory or the `backend/` folder using `python run.py`.
