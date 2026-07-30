import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Prescription
from .logger import logger

def seed_data_logic(db: Session) -> int:
    """Generate and insert 150+ realistic production healthcare database records."""
    # Clear existing data to ensure we have exactly 160 fresh records
    existing_count = db.query(Prescription).count()
    if existing_count > 0:
        logger.info(f"Database already contains {existing_count} records. Clearing table to ensure clean seeding.")
        db.query(Prescription).delete()
        db.commit()

    logger.info("Starting database seeding for 160 healthcare records...")

    # Data lists for randomization
    first_names_m = [
        "Rahul", "Rohit", "Abhishek", "Varun", "Aditya", "Aarav", "Vivaan", "Sai", 
        "Karthik", "Murali", "Rajesh", "Arjun", "Yash", "Karan", "Rakesh", "Vijay", 
        "Sanjay", "Manoj", "Deepak", "Sandeep", "Anil", "Sunil", "Vinay", "Ravi", 
        "Kiran", "Amit", "Suresh", "Vikram", "Ajay", "Harish", "Pranav", "Nikhil"
    ]
    first_names_f = [
        "Sneha", "Priya", "Ananya", "Divya", "Pooja", "Neha", "Swati", "Ritu", 
        "Meera", "Geetha", "Sunita", "Kavita", "Lata", "Preeti", "Riddhi", "Siddhie",
        "Aishwarya", "Shruti", "Deepika", "Kajal", "Rhea", "Priyanka", "Kiran", "Shalini"
    ]
    last_names = [
        "Sharma", "Patel", "Verma", "Gupta", "Iyer", "Rao", "Reddy", "Nair", "Mehta", 
        "Singh", "Joshi", "Deshmukh", "Kulkarni", "Patil", "Kapoor", "Sen", "Bannerjee", 
        "Bose", "Choudhury", "Das", "Menon", "Pillai", "Bhat", "Shenoy", "Narayana"
    ]

    hospitals = [
        ("Apollo Hospitals", "Greams Road, Thousand Lights"),
        ("Fortis Hospital", "Bannerghatta Road, Phase 3"),
        ("Max Super Speciality Hospital", "Saket Institutional Area"),
        ("Manipal Hospital", "HAL Old Airport Road"),
        ("Medanta - The Medicity", "Sector 38, Gurugram"),
        ("Narayana Health City", "Bommasandra Industrial Area"),
        ("Sir Ganga Ram Hospital", "Rajinder Nagar"),
        ("Lilavati Hospital & Research Centre", "A.K. Marg, Bandra West"),
        ("Christian Medical College & Hospital", "Ida Scudder Road, Vellore"),
        ("Tata Memorial Hospital", "Dr. E. Borges Road, Parel"),
        ("Kokilaben Dhirubhai Ambani Hospital", "Rao Saheb Achutrao Patwardhan Marg"),
        ("Jaslok Hospital & Research Centre", "Pedder Road"),
        ("KIMS Hospitals", "Secunderabad"),
        ("Aster CMI Hospital", "New Airport Road, Hebbal"),
        ("Columbia Asia Hospital", "Yeshwanthpur")
    ]

    doctors = [
        ("Dr. Rajesh Sharma", "Cardiology"),
        ("Dr. Amit Patel", "General Medicine"),
        ("Dr. Suresh Kumar", "Pediatrics"),
        ("Dr. Vikram Singh", "Orthopedics"),
        ("Dr. Priyanka Reddy", "Gastroenterology"),
        ("Dr. Sneha Rao", "Endocrinology"),
        ("Dr. Sanjay Gupta", "Neurology"),
        ("Dr. Anil Mehta", "Pulmonology"),
        ("Dr. Rahul Verma", "General Medicine"),
        ("Dr. Sandeep Joshi", "Nephrology"),
        ("Dr. Kavita Nair", "Dermatology"),
        ("Dr. Sunil Dutt", "Oncology"),
        ("Dr. Divya Iyer", "ENT"),
        ("Dr. Manoj Kulkarni", "Allergy & Immunology"),
        ("Dr. Swati Sen", "Gastroenterology")
    ]

    locations = [
        ("Mumbai", "Maharashtra", "19.0760", "72.8777"),
        ("Delhi", "Delhi", "28.7041", "77.1025"),
        ("Bangalore", "Karnataka", "12.9716", "77.5946"),
        ("Chennai", "Tamil Nadu", "13.0827", "80.2707"),
        ("Hyderabad", "Telangana", "17.3850", "78.4867"),
        ("Kolkata", "West Bengal", "22.5726", "88.3639"),
        ("Pune", "Maharashtra", "18.5204", "73.8567"),
        ("Ahmedabad", "Gujarat", "23.0225", "72.5714"),
        ("Jaipur", "Rajasthan", "26.9124", "75.7873"),
        ("Kochi", "Kerala", "9.9312", "76.2673"),
        ("Lucknow", "Uttar Pradesh", "26.8467", "80.9462"),
        ("Chandigarh", "Punjab", "30.7333", "76.7794"),
        ("Indore", "Madhya Pradesh", "22.7196", "75.8577"),
        ("Guwahati", "Assam", "26.1445", "91.7362"),
        ("Patna", "Bihar", "25.5941", "85.1376")
    ]

    medicines = [
        ("Paracetamol", "Acetaminophen", "650mg", "1-0-1", "5 days", "General Medicine", "Fever, Body ache", "Rest, take after meals"),
        ("Amoxicillin", "Amoxicillin Trihydrate", "500mg", "1-1-1", "7 days", "Internal Medicine", "Bacterial Infection", "Complete the course"),
        ("Pantoprazole", "Pantoprazole Sodium", "40mg", "1-0-0", "14 days", "Gastroenterology", "Acidity, GERD", "Take before breakfast"),
        ("Metformin", "Metformin Hydrochloride", "500mg", "0-1-1", "3 months", "Endocrinology", "Type 2 Diabetes", "Monitor blood sugar levels"),
        ("Amlodipine", "Amlodipine Besylate", "5mg", "1-0-0", "1 month", "Cardiology", "Hypertension", "Take daily at same time"),
        ("Atorvastatin", "Atorvastatin Calcium", "10mg", "0-0-1", "1 month", "Cardiology", "High Cholesterol", "Take at bed time"),
        ("Cetirizine", "Cetirizine Hydrochloride", "10mg", "0-0-1", "10 days", "Allergy & Immunology", "Allergic Rhinitis", "May cause drowsiness"),
        ("Azithromycin", "Azithromycin Dihydrate", "500mg", "1-0-0", "3 days", "ENT", "Throat Infection", "Take on empty stomach"),
        ("Ibuprofen", "Ibuprofen", "400mg", "1-0-1", "3 days", "Orthopedics", "Joint Pain", "Take with food"),
        ("Montelukast", "Montelukast Sodium", "10mg", "0-0-1", "15 days", "Pulmonology", "Asthma, Allergies", "Take in evening"),
        ("Telmisartan", "Telmisartan", "40mg", "1-0-0", "1 month", "Cardiology", "Hypertension", "Check BP weekly"),
        ("Levothyroxine", "Sodium Levothyroxine", "50mcg", "1-0-0", "6 months", "Endocrinology", "Hypothyroidism", "Take on empty stomach"),
        ("Clopidogrel", "Clopidogrel Bisulfate", "75mg", "0-1-0", "1 month", "Cardiology", "Antiplatelet therapy", "Notify doctor if bleeding occurs"),
        ("Limcee", "Vitamin C", "500mg", "1-0-0", "30 days", "Nutrition", "Vitamin C Deficiency", "Chewable tablet"),
        ("Zincovit", "Multivitamins with Zinc", "1 tab", "0-1-0", "30 days", "General Medicine", "Nutritional Supplement", "Take after lunch")
    ]

    records = []
    start_date = datetime.now() - timedelta(days=90)

    for i in range(160):
        # Determine gender and name
        gender = random.choice(["Male", "Female"])
        first_name = random.choice(first_names_m) if gender == "Male" else random.choice(first_names_f)
        last_name = random.choice(last_names)
        patient_name = f"{first_name} {last_name}"
        
        age = str(random.randint(18, 85))
        
        # Pick hospital and doctor
        hosp_name, hosp_addr = random.choice(hospitals)
        doc_name, doc_dept = random.choice(doctors)
        city_name, state_name, lat, lon = random.choice(locations)
        
        # Pick medicine
        med_name, gen_name, strength, freq, dur, dept, diag, symp = random.choice(medicines)
        
        # Generate random dates
        rec_date_dt = start_date + timedelta(days=random.randint(1, 85), hours=random.randint(0, 23))
        prescription_date_str = rec_date_dt.strftime("%d/%m/%Y")
        
        follow_up_days = random.choice([7, 10, 14, 30])
        follow_up_dt = rec_date_dt + timedelta(days=follow_up_days)
        follow_up_date_str = follow_up_dt.strftime("%d/%m/%Y")
        
        # Generate random quality & OCR scores
        conf_score = random.randint(81, 99)
        quality_score = random.randint(85, 100)
        blur_score = random.randint(150, 480)
        blur_det = blur_score < 100
        
        reg_num = f"REG-{random.randint(100000, 999999)}"
        report_no = f"REP-{random.randint(100000, 999999)}"
        qr_data = f"PATIENT:{patient_name}|REG:{reg_num}|HOSPITAL:{hosp_name}|CITY:{city_name}"
        
        # Generate OCR Texts
        raw_ocr = (
            f"=== {hosp_name.upper()} ===\n"
            f"{hosp_addr}, {city_name}, {state_name}\n"
            f"REGISTRATION NO: {reg_num}\n"
            f"DEPARTMENT: {doc_dept}\n"
            f"CONSULTANT: {doc_name}\n"
            f"DATE: {prescription_date_str}\n\n"
            f"PATIENT: {patient_name}   AGE: {age}   GENDER: {gender}\n"
            f"SYMPTOMS: {symp}\n"
            f"DIAGNOSIS: {diag}\n\n"
            f"Rx:\n"
            f"Tab. {med_name} {strength}\n"
            f"Frequency: {freq}   Duration: {dur}\n\n"
            f"Follow-up: {follow_up_date_str}\n"
            f"=== HEALTHCARE NETWORK ==="
        )
        
        clean_ocr = (
            f"{hosp_name} - {doc_name}\n"
            f"Patient: {patient_name} ({age}/{gender})\n"
            f"Rx: {med_name} {strength} | {freq} for {dur}\n"
            f"Prescribed Date: {prescription_date_str}"
        )

        # Phase 6 Enterprise Filter Engine randomized stats
        noise_val = random.randint(5, 25)
        skew_val = round(random.uniform(-5.0, 5.0), 2)
        rot_val = random.choice([0, 0, 0, 0, 90, 180, 270])
        contrast_val = random.randint(70, 98)
        brightness_val = random.randint(65, 96)
        readability_val = random.randint(75, 99)
        lang_val = random.choice(["English", "English", "English", "Hindi", "Tamil", "Spanish"])
        barcode_val = random.choice(["None", f"BC-{random.randint(100000,999999)}", "None"])
        handwritten_val = random.choice([True, False, False, False])
        med_cat_val = random.choice(["Antibiotics", "Analgesics", "Antacids", "Antihistamine", "Cardiovascular", "Diabetic", "Vitamins"])
        hosp_type_val = random.choice(["Private", "Government", "Trust", "Corporate"])
        emergency_val = random.choice([True, False, False, False, False])
        inpatient_val = random.choice([True, False, False, False])
        outpatient_val = not inpatient_val

        p = Prescription(
            patient_name=patient_name,
            medicine=med_name,
            dosage=f"{strength}, {freq}",
            date=prescription_date_str,
            doctor_name=doc_name,
            hospital_name=hosp_name,
            hospital_address=f"{hosp_addr}, {city_name}, {state_name}",
            registration_num=reg_num,
            age=age,
            gender=gender,
            document_type="Prescription",
            generic_name=gen_name,
            strength=strength,
            frequency=freq,
            duration=dur,
            diagnosis=diag,
            symptoms=symp,
            department=doc_dept,
            follow_up_date=follow_up_date_str,
            report_num=report_no,
            lab_tests="Routine Blood Counts, Lipid Profile" if doc_dept == "Cardiology" else "None",
            qr_code_data=qr_data,
            raw_text=raw_ocr,
            ocr_clean_text=clean_ocr,
            confidence_score=conf_score,
            image_quality_score=quality_score,
            blur_score=blur_score,
            blur_detected=blur_det,
            qr_code=qr_data,
            latitude=lat,
            longitude=lon,
            country="India",
            state=state_name,
            city=city_name,
            
            # Phase 6 Enterprise Filter Engine Additions
            noise_level=noise_val,
            skew_angle=skew_val,
            rotation=rot_val,
            contrast_score=contrast_val,
            brightness_score=brightness_val,
            readability_score=readability_val,
            language=lang_val,
            barcode=barcode_val,
            is_handwritten=handwritten_val,
            medicine_category=med_cat_val,
            doctor_specialty=doc_dept,
            hospital_type=hosp_type_val,
            is_emergency=emergency_val,
            is_inpatient=inpatient_val,
            is_outpatient=outpatient_val,
            
            created_at=rec_date_dt,
            updated_at=rec_date_dt
        )
        
        records.append(p)

    try:
        db.bulk_save_objects(records)
        db.commit()
        logger.info(f"Successfully seeded {len(records)} prescriptions into the database.")
        return len(records)
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
