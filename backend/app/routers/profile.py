# ===========================================
# File: backend/app/routers/profile.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException
from datetime import date

from app.schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileOut,
    VaccinationRecordOut,
    VaccinationRecordInput,
    VaccinationRecordAddRequest,
    VaccinationRecordDateUpdateRequest,
)
from app.dependencies import get_current_user
from app.pandas_store import (
    ensure_vaccines_seeded,
    get_vaccine_by_key,
    create_patient,
    get_patient_by_user,
    update_patient_by_user,
    add_vaccination_record,
    delete_vaccination_record,
    update_vaccination_record_date,
    get_vaccination_history,
)

router = APIRouter()


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes"}


def _as_optional_str(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return None
    return s


def _get_vaccine_by_key(key: str) -> dict:
    vaccine = get_vaccine_by_key(key)
    if not vaccine:
        raise HTTPException(status_code=400, detail=f"Unknown vaccine key: '{key}'")
    return vaccine


def _build_profile_out(patient: dict) -> ProfileOut:
    records = get_vaccination_history(int(patient["id"]))
    records_out = []
    for r in records:
        records_out.append(VaccinationRecordOut(
            id=int(r["id"]),
            vaccine_key=str(r["vaccine_key"]),
            vaccine_name=str(r.get("name") or r["vaccine_key"]),
            dose_number=int(r["dose_number"]),
            date_given=date.fromisoformat(str(r["date_given"]))
        ))
    return ProfileOut(
        id=int(patient["id"]),
        name=str(patient["name"]),
        dob=date.fromisoformat(str(patient["dob"])),
        gender=_as_optional_str(patient.get("gender")),
        is_pregnant=_as_bool(patient.get("is_pregnant", False)),
        is_immunocompromised=_as_bool(patient.get("is_immunocompromised", False)),
        has_diabetes=_as_bool(patient.get("has_diabetes", False)),
        has_chronic_lung=_as_bool(patient.get("has_chronic_lung", False)),
        has_heart_disease=_as_bool(patient.get("has_heart_disease", False)),
        has_chronic_kidney=_as_bool(patient.get("has_chronic_kidney", False)),
        has_chronic_liver=_as_bool(patient.get("has_chronic_liver", False)),
        has_asplenia=_as_bool(patient.get("has_asplenia", False)),
        has_hiv=_as_bool(patient.get("has_hiv", False)),
        vaccination_history=records_out
    )


def _infer_next_dose(patient_id: int, vaccine_key: str, date_given: date) -> int:
    history = get_vaccination_history(patient_id)
    same_vaccine = [r for r in history if str(r["vaccine_key"]) == vaccine_key]
    if not same_vaccine:
        return 1

    latest_date = max(date.fromisoformat(str(r["date_given"])) for r in same_vaccine)
    if date_given < latest_date:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Date is earlier than the latest '{vaccine_key}' dose ({latest_date.isoformat()}). "
                "Delete newer entries first if you need to backfill older doses."
            ),
        )

    max_dose = max(int(r["dose_number"]) for r in same_vaccine)
    next_dose = max_dose + 1
    for r in same_vaccine:
        existing_dose = int(r["dose_number"])
        existing_date = date.fromisoformat(str(r["date_given"]))
        if existing_date == date_given and existing_dose == next_dose:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Duplicate record detected for '{vaccine_key}' "
                    f"(dose #{existing_dose} on {existing_date.isoformat()})."
                ),
            )
    return next_dose


def _validate_record_date_update(patient_id: int, record_id: int, new_date: date) -> None:
    history = get_vaccination_history(patient_id)
    target = next((r for r in history if int(r["id"]) == int(record_id)), None)
    if not target:
        raise HTTPException(status_code=404, detail="Vaccination record not found.")

    vaccine_key = str(target["vaccine_key"])
    target_dose = int(target["dose_number"])

    same_vaccine = [r for r in history if str(r["vaccine_key"]) == vaccine_key and int(r["id"]) != int(record_id)]
    for r in same_vaccine:
        other_dose = int(r["dose_number"])
        other_date = date.fromisoformat(str(r["date_given"]))

        if other_dose < target_dose and new_date < other_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Updated date cannot be earlier than dose #{other_dose} "
                    f"({other_date.isoformat()}) for '{vaccine_key}'."
                ),
            )
        if other_dose > target_dose and new_date > other_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Updated date cannot be later than dose #{other_dose} "
                    f"({other_date.isoformat()}) for '{vaccine_key}'."
                ),
            )


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(
    body: ProfileCreateRequest,
    current_user = Depends(get_current_user)
):
    ensure_vaccines_seeded()
    try:
        patient = create_patient(int(current_user["id"]), body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if body.vaccination_history:
        for record_input in body.vaccination_history:
            _get_vaccine_by_key(record_input.vaccine_key)
            add_vaccination_record(
                patient_id=int(patient["id"]),
                vaccine_key=record_input.vaccine_key,
                dose_number=record_input.dose_number,
                date_given=record_input.date_given,
            )

    return _build_profile_out(patient)


@router.post("/me/records", response_model=ProfileOut, status_code=201)
def add_profile_record(
    body: VaccinationRecordAddRequest,
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    _get_vaccine_by_key(body.vaccine_key)
    next_dose = _infer_next_dose(int(patient["id"]), body.vaccine_key, body.date_given)

    add_vaccination_record(
        patient_id=int(patient["id"]),
        vaccine_key=body.vaccine_key,
        dose_number=next_dose,
        date_given=body.date_given,
    )

    refreshed = get_patient_by_user(int(current_user["id"]))
    return _build_profile_out(refreshed)


@router.delete("/me/records/{record_id}", response_model=ProfileOut)
def remove_profile_record(
    record_id: int,
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    deleted = delete_vaccination_record(int(patient["id"]), int(record_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Vaccination record not found.")

    refreshed = get_patient_by_user(int(current_user["id"]))
    return _build_profile_out(refreshed)


@router.put("/me/records/{record_id}", response_model=ProfileOut)
def update_profile_record_date(
    record_id: int,
    body: VaccinationRecordDateUpdateRequest,
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    _validate_record_date_update(int(patient["id"]), int(record_id), body.date_given)
    updated = update_vaccination_record_date(int(patient["id"]), int(record_id), body.date_given)
    if not updated:
        raise HTTPException(status_code=404, detail="Vaccination record not found.")

    refreshed = get_patient_by_user(int(current_user["id"]))
    return _build_profile_out(refreshed)


@router.get("/me", response_model=ProfileOut)
def get_profile(
    current_user = Depends(get_current_user)
):
    patient = get_patient_by_user(int(current_user["id"]))
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    return _build_profile_out(patient)


@router.put("/me", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdateRequest,
    current_user = Depends(get_current_user)
):
    update_data = body.model_dump(exclude_none=True)
    try:
        patient = update_patient_by_user(int(current_user["id"]), update_data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return _build_profile_out(patient)
