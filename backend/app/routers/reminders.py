# ===========================================
# File: backend/app/routers/reminders.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import User, Patient, Vaccine, Reminder
from app.dependencies import get_current_user

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")

    vaccine = db.query(Vaccine).filter(Vaccine.vaccine_key == body.vaccine_key).first()
    if not vaccine:
        raise HTTPException(status_code=400, detail=f"Unknown vaccine: {body.vaccine_key}")

    if body.reminder_type not in ("email", "sms", "in_app"):
        raise HTTPException(status_code=400, detail="reminder_type must be 'email', 'sms', or 'in_app'")

    reminder = Reminder(
        patient_id=patient.id,
        vaccine_id=vaccine.id,
        reminder_type=body.reminder_type,
    )
    db.add(reminder)
    db.commit()

    return {
        "success": True,
        "message": f"Reminder sent via {body.reminder_type} for {vaccine.name}"
    }


@router.get("/me", response_model=List[ReminderOut])
def get_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")

    reminders = (
        db.query(Reminder)
        .filter(Reminder.patient_id == patient.id)
        .order_by(Reminder.sent_at.desc())
        .all()
    )

    return [
        ReminderOut(
            id=r.id,
            vaccine_name=r.vaccine.name,
            reminder_type=r.reminder_type,
            sent_at=r.sent_at
        )
        for r in reminders
    ]
