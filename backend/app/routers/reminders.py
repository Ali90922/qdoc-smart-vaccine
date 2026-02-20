# ===========================================
# File: backend/app/routers/reminders.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.dependencies import get_current_user
from app.pandas_store import (
    get_patient_by_user,
    get_vaccine_by_key,
    add_reminder,
    get_reminders as get_reminders_for_patient,
    ensure_vaccines_seeded,
)

router = APIRouter()


class ReminderRequest(BaseModel):
    vaccine_key: str
    reminder_type: str   # 'email' | 'sms' | 'in_app'


class ReminderOut(BaseModel):
    id: int
    vaccine_name: str
    reminder_type: str
    sent_at: datetime

    class Config:
        from_attributes = True


@router.post("/send")
def send_reminder(
    body: ReminderRequest,
    current_user = Depends(get_current_user)
):
    ensure_vaccines_seeded()
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")

    vaccine = get_vaccine_by_key(body.vaccine_key)
    if not vaccine:
        raise HTTPException(status_code=400, detail=f"Unknown vaccine: {body.vaccine_key}")

    if body.reminder_type not in ("email", "sms", "in_app"):
        raise HTTPException(status_code=400, detail="reminder_type must be 'email', 'sms', or 'in_app'")

    add_reminder(
        patient_id=int(patient["id"]),
        vaccine_key=body.vaccine_key,
        reminder_type=body.reminder_type,
    )

    return {
        "success": True,
        "message": f"Reminder sent via {body.reminder_type} for {vaccine['name']}"
    }


@router.get("/me", response_model=List[ReminderOut])
def get_reminders(
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")

    reminders = get_reminders_for_patient(int(patient["id"]))

    return [
        ReminderOut(
            id=int(r["id"]),
            vaccine_name=str(r.get("name") or r["vaccine_key"]),
            reminder_type=str(r["reminder_type"]),
            sent_at=datetime.fromisoformat(str(r["sent_at"]))
        )
        for r in reminders
    ]
