# ===========================================
# File: backend/app/routers/profile.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User, Patient, Vaccine, VaccinationRecord
from app.schemas import ProfileCreateRequest, ProfileUpdateRequest, ProfileOut, VaccinationRecordOut
from app.dependencies import get_current_user

router = APIRouter()


def _get_vaccine_by_key(db: Session, key: str) -> Vaccine:
    """Lookup vaccine by key. Raises 400 if not found."""
    vaccine = db.query(Vaccine).filter(Vaccine.vaccine_key == key).first()
    if not vaccine:
        raise HTTPException(status_code=400, detail=f"Unknown vaccine key: '{key}'")
    return vaccine


def _build_profile_out(patient: Patient) -> ProfileOut:
    """Convert ORM patient + records into ProfileOut schema."""
    records_out = []
    for r in patient.records:
        records_out.append(VaccinationRecordOut(
            id=r.id,
            vaccine_key=r.vaccine.vaccine_key,
            vaccine_name=r.vaccine.name,
            dose_number=r.dose_number,
            date_given=r.date_given
        ))
    return ProfileOut(
        id=patient.id,
        name=patient.name,
        dob=patient.dob,
        gender=patient.gender,
        is_pregnant=patient.is_pregnant,
        is_immunocompromised=patient.is_immunocompromised,
        has_diabetes=patient.has_diabetes,
        has_chronic_lung=patient.has_chronic_lung,
        has_heart_disease=patient.has_heart_disease,
        has_chronic_kidney=patient.has_chronic_kidney,
        has_chronic_liver=patient.has_chronic_liver,
        has_asplenia=patient.has_asplenia,
        has_hiv=patient.has_hiv,
        vaccination_history=records_out
    )


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(
    body: ProfileCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Prevent duplicate profile creation
    existing = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    # Create patient record
    patient = Patient(
        user_id=current_user.id,
        name=body.name,
        dob=body.dob,
        gender=body.gender,
        birth_year=body.dob.year,
        is_pregnant=body.is_pregnant or False,
        is_immunocompromised=body.is_immunocompromised or False,
        has_diabetes=body.has_diabetes or False,
        has_chronic_lung=body.has_chronic_lung or False,
        has_heart_disease=body.has_heart_disease or False,
        has_chronic_kidney=body.has_chronic_kidney or False,
        has_chronic_liver=body.has_chronic_liver or False,
        has_asplenia=body.has_asplenia or False,
        has_hiv=body.has_hiv or False,
    )
    db.add(patient)
    db.flush()  # get patient.id before committing

    # Save vaccination history if provided
    if body.vaccination_history:
        for record_input in body.vaccination_history:
            vaccine = _get_vaccine_by_key(db, record_input.vaccine_key)

            # Check for duplicate dose (same vaccine + dose number)
            duplicate = db.query(VaccinationRecord).filter(
                VaccinationRecord.patient_id == patient.id,
                VaccinationRecord.vaccine_id == vaccine.id,
                VaccinationRecord.dose_number == record_input.dose_number
            ).first()
            if duplicate:
                continue  # silently skip duplicate doses

            vax_record = VaccinationRecord(
                patient_id=patient.id,
                vaccine_id=vaccine.id,
                dose_number=record_input.dose_number,
                date_given=record_input.date_given,
            )
            db.add(vax_record)

    db.commit()
    db.refresh(patient)

    # Reload with relationships
    patient = (
        db.query(Patient)
        .options(joinedload(Patient.records).joinedload(VaccinationRecord.vaccine))
        .filter(Patient.id == patient.id)
        .first()
    )

    return _build_profile_out(patient)


@router.get("/me", response_model=ProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = (
        db.query(Patient)
        .options(joinedload(Patient.records).joinedload(VaccinationRecord.vaccine))
        .filter(Patient.user_id == current_user.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    return _build_profile_out(patient)


@router.put("/me", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Only update fields that were actually sent
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    patient = (
        db.query(Patient)
        .options(joinedload(Patient.records).joinedload(VaccinationRecord.vaccine))
        .filter(Patient.id == patient.id)
        .first()
    )

    return _build_profile_out(patient)
