# ===========================================
# File: backend/app/routers/dashboard.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User, Patient, VaccinationRecord
from app.schemas import DashboardOut, VaccineStatusOut
from app.dependencies import get_current_user
from app.engine.rule_engine import evaluate_patient, summarize

router = APIRouter()


@router.get("/me", response_model=DashboardOut)
def get_dashboard(
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
        raise HTTPException(status_code=404, detail="Profile not found. Please complete profile setup.")

    records = patient.records or []

    # Run the rule engine
    results = evaluate_patient(patient, records)
    summary = summarize(results)

    # Sort: OVERDUE first, then DUE_SOON, UP_TO_DATE, NOT_ELIGIBLE
    status_order = {"OVERDUE": 0, "DUE_SOON": 1, "UP_TO_DATE": 2, "NOT_ELIGIBLE": 3}
    results.sort(key=lambda r: status_order.get(r["status"], 99))

    vaccines_out = [VaccineStatusOut(**r) for r in results]

    return DashboardOut(
        patient_name=patient.name,
        summary=summary,
        vaccines=vaccines_out
    )
