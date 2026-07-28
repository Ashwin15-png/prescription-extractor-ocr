from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import shutil, os, uuid, io, csv
from datetime import datetime

from .database import get_db
from . import models, schemas
from .config import settings
from .logger import logger
from .ocr import perform_ocr, get_ocr_confidence
from .extractor import extract_fields, clean_ocr_text

router = APIRouter(tags=["Prescription Management"])

# ── 1. Health Check ────────────────────────────────────────────────────────
@router.get("/health", response_model=schemas.HealthCheckResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(func.now())
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")
        db_status = f"unhealthy: {str(e)}"
        
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "environment": settings.ENV,
        "database": db_status,
        "version": settings.VERSION
    }

# ── 2. OCR Image Upload Endpoint ──────────────────────────────────────────
@router.post("/upload", tags=["OCR Engine"])
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    # File type validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a valid image file (JPG, PNG, WEBP).")

    # Save temporary file
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext if ext else '.jpg'}"
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # File size validation (10MB limit)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            os.remove(filepath)
            raise HTTPException(status_code=400, detail=f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file on server.")

    # Execute OCR processing pipeline
    raw_text = perform_ocr(filepath)
    if not raw_text or "OCR Error" in raw_text or raw_text.strip() == "":
        logger.warning(f"OCR returned empty or error for file {file.filename}")
        raise HTTPException(status_code=422, detail="OCR engine could not extract readable text from the uploaded image.")

    # Extract structured fields
    extracted_data = extract_fields(raw_text)
    ocr_confidence = get_ocr_confidence(filepath)

    # Check for existing duplicate prescription
    is_duplicate = False
    dup_id = None
    if extracted_data.get("patient_name") != "Unknown" and extracted_data.get("medicine") != "Not Found":
        existing = db.query(models.Prescription).filter(
            models.Prescription.patient_name.ilike(extracted_data["patient_name"]),
            models.Prescription.medicine.ilike(extracted_data["medicine"])
        ).first()
        if existing:
            is_duplicate = True
            dup_id = existing.id

    return {
        "raw_text": raw_text,
        "extracted_fields": extracted_data,
        "ocr_confidence": ocr_confidence,
        "is_duplicate": is_duplicate,
        "duplicate_record_id": dup_id
    }

# ── 3. Save Prescription Endpoint ──────────────────────────────────────────
@router.post("/save", tags=["Prescription Management"])
def save_prescription(prescription: schemas.PrescriptionCreate, db: Session = Depends(get_db)):
    logger.info(f"Received save request for patient: {prescription.patient_name}")

    if not prescription.patient_name or prescription.patient_name.strip() in ["", "Unknown", "Not Found"]:
        return JSONResponse(status_code=400, content={"error": "Invalid patient name"})

    if not prescription.medicine or prescription.medicine.strip() in ["", "Not Found"]:
        return JSONResponse(status_code=400, content={"error": "Medicine is required."})

    try:
        db_prescription = models.Prescription(
            patient_name=prescription.patient_name.strip(),
            medicine=prescription.medicine.strip(),
            dosage=prescription.dosage.strip() if prescription.dosage else "Not Specified",
            date=prescription.date.strip() if prescription.date else datetime.now().strftime("%d/%m/%Y"),
            doctor_name=prescription.doctor_name or "Unknown",
            hospital_name=prescription.hospital_name or "Unknown",
            raw_text=prescription.raw_text,
            confidence_score=prescription.confidence_score or 85
        )
        db.add(db_prescription)
        db.commit()
        db.refresh(db_prescription)
        logger.info(f"Saved prescription ID {db_prescription.id} for {db_prescription.patient_name}")
        return {"message": "Saved successfully", "id": db_prescription.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Database save error: {e}")
        return JSONResponse(status_code=500, content={"error": "Database save failed."})

# ── 4. Get All Prescriptions (with Search, Filter & Sort) ──────────────────
@router.get("/prescriptions", tags=["Prescription Management"])
def get_prescriptions(
    db: Session = Depends(get_db),
    patient: Optional[str] = Query(None, description="Search by patient name"),
    medicine: Optional[str] = Query(None, description="Filter by medicine"),
    date: Optional[str] = Query(None, description="Filter by date"),
    sort_by: Optional[str] = Query(None, description="Sort order: name_asc, name_desc, medicine_asc, id_desc, id_asc")
):
    query = db.query(models.Prescription)
    if patient:
        query = query.filter(models.Prescription.patient_name.ilike(f"%{patient}%"))
    if medicine:
        query = query.filter(models.Prescription.medicine.ilike(f"%{medicine}%"))
    if date:
        query = query.filter(models.Prescription.date.ilike(f"%{date}%"))

    # Sorting
    if sort_by == "name_asc":
        query = query.order_by(models.Prescription.patient_name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(models.Prescription.patient_name.desc())
    elif sort_by == "medicine_asc":
        query = query.order_by(models.Prescription.medicine.asc())
    elif sort_by == "id_asc":
        query = query.order_by(models.Prescription.id.asc())
    else:
        query = query.order_by(models.Prescription.id.desc())

    return query.all()

# ── 5. Get Single Prescription Details ────────────────────────────────────
@router.get("/prescriptions/{prescription_id}", tags=["Prescription Management"])
def get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    record = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prescription record not found")
    return record

# ── 6. Update Prescription Details ────────────────────────────────────────
@router.put("/prescriptions/{prescription_id}", tags=["Prescription Management"])
def update_prescription(prescription_id: int, update_data: schemas.PrescriptionUpdate, db: Session = Depends(get_db)):
    record = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prescription record not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(record, key, value)

    db.commit()
    db.refresh(record)
    logger.info(f"Updated prescription record ID {prescription_id}")
    return {"message": "Prescription record updated successfully", "record": record}

# ── 7. Delete Prescription Endpoint ───────────────────────────────────────
@router.delete("/prescriptions/{prescription_id}", tags=["Prescription Management"])
def delete_prescription(prescription_id: int, db: Session = Depends(get_db)):
    record = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prescription not found")
    db.delete(record)
    db.commit()
    logger.info(f"Deleted prescription ID {prescription_id}")
    return {"message": "Deleted successfully", "id": prescription_id}

# ── 8. Analytics Overview Endpoint ────────────────────────────────────────
@router.get("/analytics", tags=["Analytics & Reporting"])
def get_analytics(db: Session = Depends(get_db)):
    records = db.query(models.Prescription).all()
    total = len(records)

    med_counts: dict = {}
    dos_counts: dict = {}
    conf_scores = []
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    todays_uploads = 0

    for r in records:
        if r.medicine:
            med_counts[r.medicine] = med_counts.get(r.medicine, 0) + 1
        if r.dosage:
            dos_counts[r.dosage] = dos_counts.get(r.dosage, 0) + 1
        if hasattr(r, 'confidence_score') and r.confidence_score:
            conf_scores.append(r.confidence_score)
        if r.date and today_str in r.date:
            todays_uploads += 1

    most_common_medicine = max(med_counts, key=med_counts.get) if med_counts else "N/A"
    most_common_dosage = max(dos_counts, key=dos_counts.get) if dos_counts else "N/A"
    recent_uploads = min(total, 10)
    avg_confidence = round(sum(conf_scores) / len(conf_scores), 1) if conf_scores else 91.5

    return {
        "total_prescriptions": total,
        "todays_uploads": todays_uploads,
        "most_common_medicine": most_common_medicine,
        "most_common_dosage": most_common_dosage,
        "recent_uploads": recent_uploads,
        "avg_confidence": avg_confidence
    }

# ── 9. Search & Medicine Suggestions Endpoint ─────────────────────────────
@router.get("/api/v1/suggestions", tags=["Smart Features"])
def get_suggestions(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    patients = db.query(models.Prescription.patient_name).filter(
        models.Prescription.patient_name.ilike(f"%{q}%")
    ).distinct().limit(5).all()

    medicines = db.query(models.Prescription.medicine).filter(
        models.Prescription.medicine.ilike(f"%{q}%")
    ).distinct().limit(5).all()

    return {
        "patients": [p[0] for p in patients if p[0]],
        "medicines": [m[0] for m in medicines if m[0]]
    }

# ── 10. CSV Export Endpoint ────────────────────────────────────────────────
@router.get("/export-csv", tags=["Exports"])
@router.get("/api/v1/export/csv", tags=["Exports"])
def export_csv(
    db: Session = Depends(get_db),
    patient: Optional[str] = Query(None),
    medicine: Optional[str] = Query(None),
):
    query = db.query(models.Prescription)
    if patient:
        query = query.filter(models.Prescription.patient_name.ilike(f"%{patient}%"))
    if medicine:
        query = query.filter(models.Prescription.medicine.ilike(f"%{medicine}%"))
    records = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Patient Name", "Medicine", "Dosage", "Date", "Doctor", "Hospital"])
    for r in records:
        writer.writerow([
            r.id, 
            r.patient_name, 
            r.medicine, 
            r.dosage, 
            r.date, 
            getattr(r, 'doctor_name', 'Unknown'), 
            getattr(r, 'hospital_name', 'Unknown')
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescriptions_{timestamp}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

# ── 11. Excel Export Endpoint ──────────────────────────────────────────────
@router.get("/api/v1/export/excel", tags=["Exports"])
def export_excel(
    db: Session = Depends(get_db),
    patient: Optional[str] = Query(None),
    medicine: Optional[str] = Query(None),
):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl is not installed on the server.")

    query = db.query(models.Prescription)
    if patient:
        query = query.filter(models.Prescription.patient_name.ilike(f"%{patient}%"))
    if medicine:
        query = query.filter(models.Prescription.medicine.ilike(f"%{medicine}%"))
    records = query.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prescriptions"

    # Header styling
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center")

    headers = ["Record ID", "Patient Name", "Medicine", "Dosage", "Prescription Date", "Doctor Name", "Hospital Name"]
    ws.append(headers)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    # Add rows
    for r in records:
        ws.append([
            r.id, 
            r.patient_name, 
            r.medicine, 
            r.dosage, 
            r.date,
            getattr(r, 'doctor_name', 'Unknown'),
            getattr(r, 'hospital_name', 'Unknown')
        ])

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescriptions_report_{timestamp}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ── 12. PDF Export Endpoint ────────────────────────────────────────────────
@router.get("/api/v1/export/pdf", tags=["Exports"])
def export_pdf(
    db: Session = Depends(get_db),
    patient: Optional[str] = Query(None),
    medicine: Optional[str] = Query(None),
):
    try:
        from fpdf import FPDF
    except ImportError:
        raise HTTPException(status_code=500, detail="fpdf2 library is not installed on the server.")

    query = db.query(models.Prescription)
    if patient:
        query = query.filter(models.Prescription.patient_name.ilike(f"%{patient}%"))
    if medicine:
        query = query.filter(models.Prescription.medicine.ilike(f"%{medicine}%"))
    records = query.all()

    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(79, 70, 229)
            self.cell(0, 10, 'PrescriptionX - Medical Records Report', 0, 1, 'C')
            self.set_font('Helvetica', 'I', 9)
            self.set_text_color(100, 116, 139)
            self.cell(0, 5, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            self.ln(8)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 10, f'Page {self.page_no()} | Healthcare Digital OCR System', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 10)

    # Table Header
    pdf.set_fill_color(79, 70, 229)
    pdf.set_text_color(255, 255, 255)
    cols = [("ID", 15), ("Patient Name", 50), ("Medicine", 50), ("Dosage", 35), ("Date", 35)]
    for name, width in cols:
        pdf.cell(width, 9, name, 1, 0, 'C', True)
    pdf.ln()

    # Table Rows
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(30, 41, 59)
    fill = False
    for r in records:
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(15, 8, f"#{r.id}", 1, 0, 'C', fill)
        pdf.cell(50, 8, str(r.patient_name)[:24], 1, 0, 'L', fill)
        pdf.cell(50, 8, str(r.medicine)[:24], 1, 0, 'L', fill)
        pdf.cell(35, 8, str(r.dosage)[:18], 1, 0, 'L', fill)
        pdf.cell(35, 8, str(r.date)[:18], 1, 1, 'C', fill)
        fill = not fill

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescription_report_{timestamp}.pdf"
    return StreamingResponse(
        pdf_output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

