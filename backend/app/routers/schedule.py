from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User, Patient, VaccinationRecord
from app.schemas import ScheduleOut, ScheduleItemOut
from app.dependencies import get_current_user
from app.engine.rule_engine import evaluate_patient, get_upcoming_schedule

router = APIRouter()


@router.get("/me", response_model=ScheduleOut)
def get_schedule(
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
    results = evaluate_patient(patient, records)
    upcoming = get_upcoming_schedule(results)

    items = [
        ScheduleItemOut(
            vaccine_key=r["vaccine_key"],
            vaccine_name=r["vaccine_name"],
            due_date=r["next_due"],
            status=r["status"],
            days_until=r.get("days_until"),
        )
        for r in upcoming
    ]

    return ScheduleOut(upcoming=items)
