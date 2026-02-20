# ===========================================
# File: backend/app/routers/dashboard.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import DashboardOut, VaccineStatusOut
from app.dependencies import get_current_user
from app.engine.rule_engine import evaluate_patient, summarize
from app.pandas_store import get_patient_by_user, get_vaccination_history, to_engine_patient, to_engine_records

router = APIRouter()


@router.get("/me", response_model=DashboardOut)
def get_dashboard(
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete profile setup.")

    history = get_vaccination_history(int(patient["id"]))
    patient_obj = to_engine_patient(patient)
    records_obj = to_engine_records(history)

    results = evaluate_patient(patient_obj, records_obj)
    summary = summarize(results)

    # Sort: OVERDUE first, then DUE_SOON, UP_TO_DATE, NOT_ELIGIBLE
    status_order = {"OVERDUE": 0, "DUE_SOON": 1, "UP_TO_DATE": 2, "NOT_ELIGIBLE": 3}
    results.sort(key=lambda r: status_order.get(r["status"], 99))

    vaccines_out = [VaccineStatusOut(**r) for r in results]

    return DashboardOut(
        patient_name=str(patient["name"]),
        summary=summary,
        vaccines=vaccines_out
    )
