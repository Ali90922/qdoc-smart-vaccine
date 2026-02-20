# ===========================================
# File: backend/app/routers/schedule.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import ScheduleOut, ScheduleItemOut
from app.dependencies import get_current_user
from app.engine.rule_engine import evaluate_patient, get_upcoming_schedule
from app.pandas_store import get_patient_by_user, get_vaccination_history, to_engine_patient, to_engine_records

router = APIRouter()


@router.get("/me", response_model=ScheduleOut)
def get_schedule(
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete profile setup.")

    history = get_vaccination_history(int(patient["id"]))
    patient_obj = to_engine_patient(patient)
    records_obj = to_engine_records(history)
    results = evaluate_patient(patient_obj, records_obj)
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
