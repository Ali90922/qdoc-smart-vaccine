# ===========================================
# File: backend/app/schemas.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    user_id: int
    is_new_user: bool   # True = no profile yet → frontend sends to /profile


# ─── Vaccination Record (nested inside profile creation) ─────────────────────

class VaccinationRecordInput(BaseModel):
    vaccine_key: str
    dose_number: int
    date_given: date

    @field_validator("vaccine_key")
    @classmethod
    def vaccine_key_normalized(cls, v):
        key = v.strip().lower()
        if not key:
            raise ValueError("vaccine_key cannot be empty.")
        return key

    @field_validator("date_given")
    @classmethod
    def date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Vaccination date cannot be in the future.")
        return v

    @field_validator("dose_number")
    @classmethod
    def dose_positive(cls, v):
        if v < 1:
            raise ValueError("Dose number must be at least 1.")
        return v


class VaccinationRecordAddRequest(BaseModel):
    vaccine_key: str
    date_given: date

    @field_validator("vaccine_key")
    @classmethod
    def vaccine_key_normalized(cls, v):
        key = v.strip().lower()
        if not key:
            raise ValueError("vaccine_key cannot be empty.")
        return key

    @field_validator("date_given")
    @classmethod
    def date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Vaccination date cannot be in the future.")
        return v


class VaccinationRecordDateUpdateRequest(BaseModel):
    date_given: date

    @field_validator("date_given")
    @classmethod
    def date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Vaccination date cannot be in the future.")
        return v


class VaccinationRecordOut(BaseModel):
    id: int
    vaccine_key: str
    vaccine_name: str
    dose_number: int
    date_given: date

    class Config:
        from_attributes = True


# ─── Patient Profile ─────────────────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    name: str
    dob: date
    gender: Optional[str] = None

    # Risk factors — all optional, default False
    is_pregnant:          Optional[bool] = False
    is_immunocompromised: Optional[bool] = False
    has_diabetes:         Optional[bool] = False
    has_chronic_lung:     Optional[bool] = False
    has_heart_disease:    Optional[bool] = False
    has_chronic_kidney:   Optional[bool] = False
    has_chronic_liver:    Optional[bool] = False
    has_asplenia:         Optional[bool] = False
    has_hiv:              Optional[bool] = False

    # Vaccination history — can be empty for new patients
    vaccination_history: Optional[List[VaccinationRecordInput]] = []

    @field_validator("dob")
    @classmethod
    def dob_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip()

    @model_validator(mode="after")
    def vaccination_history_consistency(self):
        history = self.vaccination_history or []
        if not history:
            return self

        seen = set()
        by_vaccine = {}
        for record in history:
            key = (record.vaccine_key, record.dose_number)
            if key in seen:
                raise ValueError(
                    f"Duplicate vaccination history entry for '{record.vaccine_key}' dose {record.dose_number}."
                )
            seen.add(key)
            by_vaccine.setdefault(record.vaccine_key, []).append(record)

        # Higher dose numbers cannot have older dates than lower doses for same vaccine
        for vaccine_key, records in by_vaccine.items():
            ordered = sorted(records, key=lambda r: r.dose_number)
            for idx in range(1, len(ordered)):
                prev = ordered[idx - 1]
                curr = ordered[idx]
                if curr.date_given < prev.date_given:
                    raise ValueError(
                        f"Inconsistent dose chronology for '{vaccine_key}': "
                        f"dose {curr.dose_number} date is earlier than dose {prev.dose_number}."
                    )

        return self


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    is_pregnant:          Optional[bool] = None
    is_immunocompromised: Optional[bool] = None
    has_diabetes:         Optional[bool] = None
    has_chronic_lung:     Optional[bool] = None
    has_heart_disease:    Optional[bool] = None
    has_chronic_kidney:   Optional[bool] = None
    has_chronic_liver:    Optional[bool] = None
    has_asplenia:         Optional[bool] = None
    has_hiv:              Optional[bool] = None


class ProfileOut(BaseModel):
    id: int
    name: str
    dob: date
    gender: Optional[str]
    is_pregnant: bool
    is_immunocompromised: bool
    has_diabetes: bool
    has_chronic_lung: bool
    has_heart_disease: bool
    has_chronic_kidney: bool
    has_chronic_liver: bool
    has_asplenia: bool
    has_hiv: bool
    vaccination_history: List[VaccinationRecordOut] = []

    class Config:
        from_attributes = True


# ─── Rule Engine Output ───────────────────────────────────────────────────────

class VaccineStatusOut(BaseModel):
    vaccine_key: str
    vaccine_name: str
    status: str             # ELIGIBLE | DUE_SOON | OVERDUE | NOT_ELIGIBLE | UP_TO_DATE
    reason: Optional[str] = None
    last_dose: Optional[date] = None
    next_due: Optional[date] = None
    doses_received: int = 0
    doses_required: int
    days_until: Optional[int] = None  # only for DUE_SOON


class DashboardOut(BaseModel):
    patient_name: str
    summary: dict           # { overdue, due_soon, up_to_date, not_eligible }
    vaccines: List[VaccineStatusOut]


class ScheduleItemOut(BaseModel):
    vaccine_key: str
    vaccine_name: str
    due_date: date
    status: str
    days_until: Optional[int] = None


class ScheduleOut(BaseModel):
    upcoming: List[ScheduleItemOut]
