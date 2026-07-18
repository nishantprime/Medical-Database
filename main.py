from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, String, Integer, Float, or_
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import shutil
import os
import uuid

# --- 1. DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./medical_db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    # Core Details
    id = Column(String, primary_key=True, index=True)
    reg_number = Column(String, index=True, nullable=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    gender = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    blood_group = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    
    # Contact Data
    mobile_number = Column(String, index=True)
    alt_mobile_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    
    # Medical History
    chief_complaint = Column(String, nullable=True)
    present_illness = Column(String, nullable=True)
    prev_skin_diseases = Column(String, nullable=True)
    other_medical_conditions = Column(String, nullable=True)
    prev_surgeries = Column(String, nullable=True)
    drug_allergies = Column(String, nullable=True)
    food_allergies = Column(String, nullable=True)
    current_medications = Column(String, nullable=True)
    family_hx_skin = Column(String, nullable=True)
    family_hx_cancer = Column(String, nullable=True)
    smoking_status = Column(String, nullable=True)
    alcohol_consumption = Column(String, nullable=True)
    pregnancy_status = Column(String, nullable=True)
    
    # Skin Condition Specifics
    primary_condition = Column(String, index=True, nullable=True)
    date_of_onset = Column(String, nullable=True)
    duration_disease = Column(String, nullable=True)
    body_part_affected = Column(String, nullable=True)
    symptoms = Column(String, nullable=True)
    previous_treatment = Column(String, nullable=True)
    sun_exposure_history = Column(String, nullable=True)
    cosmetic_product_usage = Column(String, nullable=True)
    occupational_exposure = Column(String, nullable=True)
    fitzpatrick_skin_type = Column(String, nullable=True)
    
    # Images & AI Metrics
    clinical_image_path = Column(String, nullable=True)
    dermoscopic_image_path = Column(String, nullable=True)
    ai_status = Column(String, nullable=True)
    latest_ai_prediction = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    severity = Column(String, nullable=True)
    disease_progress_status = Column(String, nullable=True)
    
    # Visit Metadata
    last_visit_date = Column(String, nullable=True)
    next_followup_date = Column(String, nullable=True)
    total_visits = Column(Integer, default=1)
    assigned_doctor = Column(String, nullable=True)
    current_treatment_plan = Column(String, nullable=True)
    prescription_available = Column(String, nullable=True)
    report_generated = Column(String, nullable=True)
    status = Column(String, default="Active")

Base.metadata.create_all(bind=engine)

# --- 2. FASTAPI SETUP ---
app = FastAPI()
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to process image saving cleanly
def save_uploaded_file(uploaded_file: UploadFile, patient_id: str, prefix: str) -> str:
    if uploaded_file and uploaded_file.filename:
        ext = uploaded_file.filename.split(".")[-1]
        filename = f"{prefix}_{patient_id}.{ext}"
        path = f"uploads/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)
        return f"/uploads/{filename}"
    return None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, search: str = None, db: Session = Depends(get_db)):
    search_query = request.query_params.get("search", "").strip()
    
    if search_query:
        # The AST compiler will construct: WHERE first_name LIKE ? OR last_name LIKE ? OR mobile_number LIKE ? OR reg_number LIKE ?
        patients = db.query(Patient).filter(
            or_(
                Patient.first_name.contains(search_query),
                Patient.last_name.contains(search_query),
                Patient.mobile_number.contains(search_query),
                Patient.reg_number.contains(search_query) # Registration Number added here
            )
        ).all()
    else:
        patients = db.query(Patient).all()
        
    return templates.TemplateResponse(request, "index.html", {"patients": patients, "search_query": search_query})

# New endpoint for the detailed view
@app.get("/patient/{patient_id}", response_class=HTMLResponse)
async def patient_detail(request: Request, patient_id: str, db: Session = Depends(get_db)):
    # We use .first() to execute a scalar fetch against the Primary Key B-Tree index (O(log N) time complexity)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        return HTMLResponse(content="<h1>404 - Patient Not Found</h1>", status_code=404)
        
    return templates.TemplateResponse(request, "patient_detail.html", {"patient": patient})
    
@app.post("/add_patient/")
async def add_patient(
    reg_number: str = Form(None), first_name: str = Form(...), last_name: str = Form(...),
    gender: str = Form(None), dob: str = Form(None), age: int = Form(None),
    blood_group: str = Form(None), marital_status: str = Form(None), occupation: str = Form(None),
    nationality: str = Form(None), mobile_number: str = Form(...), alt_mobile_number: str = Form(None),
    email: str = Form(None), address: str = Form(None), city: str = Form(None),
    state: str = Form(None), country: str = Form(None), pin_code: str = Form(None),
    chief_complaint: str = Form(None), present_illness: str = Form(None), prev_skin_diseases: str = Form(None),
    other_medical_conditions: str = Form(None), prev_surgeries: str = Form(None), drug_allergies: str = Form(None),
    food_allergies: str = Form(None), current_medications: str = Form(None), family_hx_skin: str = Form(None),
    family_hx_cancer: str = Form(None), smoking_status: str = Form(None), alcohol_consumption: str = Form(None),
    pregnancy_status: str = Form(None), primary_condition: str = Form(None), date_of_onset: str = Form(None),
    duration_disease: str = Form(None), body_part_affected: str = Form(None), symptoms: str = Form(None),
    previous_treatment: str = Form(None), sun_exposure_history: str = Form(None), cosmetic_product_usage: str = Form(None),
    occupational_exposure: str = Form(None), fitzpatrick_skin_type: str = Form(None), ai_status: str = Form(None),
    latest_ai_prediction: str = Form(None), confidence_score: float = Form(None), severity: str = Form(None),
    disease_progress_status: str = Form(None), last_visit_date: str = Form(None), next_followup_date: str = Form(None),
    total_visits: int = Form(1), assigned_doctor: str = Form(None), current_treatment_plan: str = Form(None),
    prescription_available: str = Form(None), report_generated: str = Form(None), status: str = Form("Active"),
    clinical_image: UploadFile = File(None), dermoscopic_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    patient_id = str(uuid.uuid4())
    
    c_img_path = save_uploaded_file(clinical_image, patient_id, "clinical")
    d_img_path = save_uploaded_file(dermoscopic_image, patient_id, "dermoscopic")

    new_patient = Patient(
        id=patient_id, reg_number=reg_number, first_name=first_name, last_name=last_name,
        gender=gender, dob=dob, age=age, blood_group=blood_group, marital_status=marital_status,
        occupation=occupation, nationality=nationality, mobile_number=mobile_number,
        alt_mobile_number=alt_mobile_number, email=email, address=address, city=city,
        state=state, country=country, pin_code=pin_code, chief_complaint=chief_complaint,
        present_illness=present_illness, prev_skin_diseases=prev_skin_diseases,
        other_medical_conditions=other_medical_conditions, prev_surgeries=prev_surgeries,
        drug_allergies=drug_allergies, food_allergies=food_allergies, current_medications=current_medications,
        family_hx_skin=family_hx_skin, family_hx_cancer=family_hx_cancer, smoking_status=smoking_status,
        alcohol_consumption=alcohol_consumption, pregnancy_status=pregnancy_status,
        primary_condition=primary_condition, date_of_onset=date_of_onset, duration_disease=duration_disease,
        body_part_affected=body_part_affected, symptoms=symptoms, previous_treatment=previous_treatment,
        sun_exposure_history=sun_exposure_history, cosmetic_product_usage=cosmetic_product_usage,
        occupational_exposure=occupational_exposure, fitzpatrick_skin_type=fitzpatrick_skin_type,
        clinical_image_path=c_img_path, dermoscopic_image_path=d_img_path, ai_status=ai_status,
        latest_ai_prediction=latest_ai_prediction, confidence_score=confidence_score, severity=severity,
        disease_progress_status=disease_progress_status, last_visit_date=last_visit_date,
        next_followup_date=next_followup_date, total_visits=total_visits, assigned_doctor=assigned_doctor,
        current_treatment_plan=current_treatment_plan, prescription_available=prescription_available,
        report_generated=report_generated, status=status
    )
    
    db.add(new_patient)
    db.commit()
    return RedirectResponse(url="/", status_code=303)