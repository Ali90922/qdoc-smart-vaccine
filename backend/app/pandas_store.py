# ===========================================
# File: backend/app/pandas_store.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from typing import Optional

import pandas as pd


STORE_DIR = Path(__file__).resolve().parents[1] / "data_store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

_LOCK = Lock()

USERS_COLS = ["id", "email", "password_hash", "created_at"]
PATIENT_COLS = [
    "id",
    "user_id",
    "name",
    "dob",
    "gender",
    "birth_year",
    "is_pregnant",
    "is_immunocompromised",
    "has_diabetes",
    "has_chronic_lung",
    "has_heart_disease",
    "has_chronic_kidney",
    "has_chronic_liver",
    "has_asplenia",
    "has_hiv",
]
RECORD_COLS = ["id", "patient_id", "vaccine_key", "dose_number", "date_given", "notes"]
REMINDER_COLS = ["id", "patient_id", "vaccine_key", "reminder_type", "sent_at"]
VACCINE_COLS = [
    "id",
    "vaccine_key",
    "name",
    "description",
    "min_age_months",
    "max_age_months",
    "doses_required",
    "dose_interval_days",
    "repeat_interval_days",
]


def _file(name: str) -> Path:
    return STORE_DIR / f"{name}.csv"


def _read(name: str, cols: list[str]) -> pd.DataFrame:
    p = _file(name)
    if not p.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(p)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


def _write(name: str, df: pd.DataFrame) -> None:
    _file(name).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(_file(name), index=False)


def _next_id(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").fillna(0).max()) + 1


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if pd.isna(v):
        return False
    return str(v).strip().lower() in {"1", "true", "yes"}


def ensure_vaccines_seeded() -> tuple[int, int]:
    with _LOCK:
        vaccines_df = _read("vaccines", VACCINE_COLS)
        existing = set(vaccines_df["vaccine_key"].astype(str)) if not vaccines_df.empty else set()

        rules_path = Path(__file__).resolve().parent / "data" / "vaccine_rules.json"
        with open(rules_path) as f:
            rules = json.load(f)["vaccines"]

        inserted = 0
        skipped = 0
        for rule in rules:
            key = rule["id"]
            if key in existing:
                skipped += 1
                continue
            row = {
                "id": _next_id(vaccines_df),
                "vaccine_key": key,
                "name": rule["name"],
                "description": rule.get("description"),
                "min_age_months": rule.get("min_age_months"),
                "max_age_months": rule.get("max_age_months"),
                "doses_required": rule.get("doses_required"),
                "dose_interval_days": rule.get("dose_interval_days"),
                "repeat_interval_days": rule.get("repeat_interval_days"),
            }
            vaccines_df = pd.concat([vaccines_df, pd.DataFrame([row])], ignore_index=True)
            existing.add(key)
            inserted += 1

        _write("vaccines", vaccines_df)
        return inserted, skipped


def get_user_by_email(email: str) -> Optional[dict]:
    with _LOCK:
        users = _read("users", USERS_COLS)
        row = users[users["email"] == email]
        if row.empty:
            return None
        return row.iloc[0].to_dict()


def get_user_by_id(user_id: int) -> Optional[dict]:
    with _LOCK:
        users = _read("users", USERS_COLS)
        row = users[pd.to_numeric(users["id"], errors="coerce") == int(user_id)]
        if row.empty:
            return None
        return row.iloc[0].to_dict()


def create_user(email: str, password_hash: str) -> dict:
    with _LOCK:
        users = _read("users", USERS_COLS)
        if not users[users["email"] == email].empty:
            raise ValueError("Email already registered.")
        row = {
            "id": _next_id(users),
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
        }
        users = pd.concat([users, pd.DataFrame([row])], ignore_index=True)
        _write("users", users)
        return row


def get_vaccine_by_key(vaccine_key: str) -> Optional[dict]:
    with _LOCK:
        vaccines = _read("vaccines", VACCINE_COLS)
        row = vaccines[vaccines["vaccine_key"] == vaccine_key]
        if row.empty:
            return None
        return row.iloc[0].to_dict()


def has_patient_for_user(user_id: int) -> bool:
    with _LOCK:
        patients = _read("patients", PATIENT_COLS)
        return not patients[pd.to_numeric(patients["user_id"], errors="coerce") == int(user_id)].empty


def create_patient(user_id: int, data: dict) -> dict:
    with _LOCK:
        patients = _read("patients", PATIENT_COLS)
        if not patients[pd.to_numeric(patients["user_id"], errors="coerce") == int(user_id)].empty:
            raise ValueError("Profile already exists. Use PUT to update.")

        dob_val = data["dob"]
        dob_iso = dob_val.isoformat() if isinstance(dob_val, date) else str(dob_val)
        row = {
            "id": _next_id(patients),
            "user_id": int(user_id),
            "name": data["name"],
            "dob": dob_iso,
            "gender": data.get("gender"),
            "birth_year": date.fromisoformat(dob_iso).year,
            "is_pregnant": bool(data.get("is_pregnant", False)),
            "is_immunocompromised": bool(data.get("is_immunocompromised", False)),
            "has_diabetes": bool(data.get("has_diabetes", False)),
            "has_chronic_lung": bool(data.get("has_chronic_lung", False)),
            "has_heart_disease": bool(data.get("has_heart_disease", False)),
            "has_chronic_kidney": bool(data.get("has_chronic_kidney", False)),
            "has_chronic_liver": bool(data.get("has_chronic_liver", False)),
            "has_asplenia": bool(data.get("has_asplenia", False)),
            "has_hiv": bool(data.get("has_hiv", False)),
        }
        patients = pd.concat([patients, pd.DataFrame([row])], ignore_index=True)
        _write("patients", patients)
        return row


def get_patient_by_user(user_id: int) -> Optional[dict]:
    with _LOCK:
        patients = _read("patients", PATIENT_COLS)
        row = patients[pd.to_numeric(patients["user_id"], errors="coerce") == int(user_id)]
        if row.empty:
            return None
        return row.iloc[0].to_dict()


def update_patient_by_user(user_id: int, update_data: dict) -> dict:
    with _LOCK:
        patients = _read("patients", PATIENT_COLS)
        mask = pd.to_numeric(patients["user_id"], errors="coerce") == int(user_id)
        if patients[mask].empty:
            raise ValueError("Profile not found.")

        idx = patients[mask].index[0]
        for field, value in update_data.items():
            patients.at[idx, field] = value
        _write("patients", patients)
        return patients.loc[idx].to_dict()


def add_vaccination_record(patient_id: int, vaccine_key: str, dose_number: int, date_given: date, notes: Optional[str] = None) -> dict:
    with _LOCK:
        records = _read("vaccination_records", RECORD_COLS)
        dup = records[
            (pd.to_numeric(records["patient_id"], errors="coerce") == int(patient_id))
            & (records["vaccine_key"] == vaccine_key)
            & (pd.to_numeric(records["dose_number"], errors="coerce") == int(dose_number))
        ]
        if not dup.empty:
            return dup.iloc[0].to_dict()

        row = {
            "id": _next_id(records),
            "patient_id": int(patient_id),
            "vaccine_key": vaccine_key,
            "dose_number": int(dose_number),
            "date_given": date_given.isoformat() if isinstance(date_given, date) else str(date_given),
            "notes": notes,
        }
        records = pd.concat([records, pd.DataFrame([row])], ignore_index=True)
        _write("vaccination_records", records)
        return row


def get_vaccination_history(patient_id: int) -> list[dict]:
    with _LOCK:
        records = _read("vaccination_records", RECORD_COLS)
        vaccines = _read("vaccines", VACCINE_COLS)
        subset = records[pd.to_numeric(records["patient_id"], errors="coerce") == int(patient_id)]
        if subset.empty:
            return []

        merged = subset.merge(vaccines[["vaccine_key", "name"]], on="vaccine_key", how="left")
        merged = merged.sort_values(["vaccine_key", "dose_number"])
        return merged.to_dict(orient="records")


def delete_vaccination_record(patient_id: int, record_id: int) -> bool:
    with _LOCK:
        records = _read("vaccination_records", RECORD_COLS)
        if records.empty:
            return False

        id_mask = pd.to_numeric(records["id"], errors="coerce") == int(record_id)
        patient_mask = pd.to_numeric(records["patient_id"], errors="coerce") == int(patient_id)
        match = records[id_mask & patient_mask]
        if match.empty:
            return False

        kept = records[~(id_mask & patient_mask)]
        _write("vaccination_records", kept)
        return True


def update_vaccination_record_date(patient_id: int, record_id: int, date_given: date) -> bool:
    with _LOCK:
        records = _read("vaccination_records", RECORD_COLS)
        if records.empty:
            return False

        id_mask = pd.to_numeric(records["id"], errors="coerce") == int(record_id)
        patient_mask = pd.to_numeric(records["patient_id"], errors="coerce") == int(patient_id)
        match = records[id_mask & patient_mask]
        if match.empty:
            return False

        idx = match.index[0]
        records.at[idx, "date_given"] = date_given.isoformat() if isinstance(date_given, date) else str(date_given)
        _write("vaccination_records", records)
        return True


def add_reminder(patient_id: int, vaccine_key: str, reminder_type: str) -> dict:
    with _LOCK:
        reminders = _read("reminders", REMINDER_COLS)
        row = {
            "id": _next_id(reminders),
            "patient_id": int(patient_id),
            "vaccine_key": vaccine_key,
            "reminder_type": reminder_type,
            "sent_at": datetime.utcnow().isoformat(),
        }
        reminders = pd.concat([reminders, pd.DataFrame([row])], ignore_index=True)
        _write("reminders", reminders)
        return row


def get_reminders(patient_id: int) -> list[dict]:
    with _LOCK:
        reminders = _read("reminders", REMINDER_COLS)
        vaccines = _read("vaccines", VACCINE_COLS)
        subset = reminders[pd.to_numeric(reminders["patient_id"], errors="coerce") == int(patient_id)]
        if subset.empty:
            return []
        merged = subset.merge(vaccines[["vaccine_key", "name"]], on="vaccine_key", how="left")
        merged = merged.sort_values("sent_at", ascending=False)
        return merged.to_dict(orient="records")


def to_engine_patient(patient_row: dict):
    return SimpleNamespace(
        dob=date.fromisoformat(str(patient_row["dob"])),
        is_pregnant=_as_bool(patient_row.get("is_pregnant")),
        is_immunocompromised=_as_bool(patient_row.get("is_immunocompromised")),
        has_diabetes=_as_bool(patient_row.get("has_diabetes")),
        has_chronic_lung=_as_bool(patient_row.get("has_chronic_lung")),
        has_heart_disease=_as_bool(patient_row.get("has_heart_disease")),
        has_chronic_kidney=_as_bool(patient_row.get("has_chronic_kidney")),
        has_chronic_liver=_as_bool(patient_row.get("has_chronic_liver")),
        has_asplenia=_as_bool(patient_row.get("has_asplenia")),
        has_hiv=_as_bool(patient_row.get("has_hiv")),
        resides_in_pch=False,
        is_pch_respite=False,
        is_panelled_for_pch_in_transitional_care=False,
        is_panelled_for_pch_in_chronic_care=False,
        has_homelessness=False,
        uses_illicit_drugs=False,
        has_cochlear_implant=False,
        has_hemoglobinopathy=False,
        on_immunosuppressive_therapy=False,
        is_on_dialysis=False,
        is_incarcerated=False,
        is_msm=False,
        is_healthcare_worker=False,
        is_student=False,
        is_traveling_to_measles_endemic_country=False,
        is_measles_outbreak_exposed=False,
    )


def to_engine_records(history_rows: list[dict]):
    records = []
    for r in history_rows:
        records.append(
            SimpleNamespace(
                vaccine=SimpleNamespace(vaccine_key=r["vaccine_key"]),
                date_given=date.fromisoformat(str(r["date_given"])),
                dose_number=int(r["dose_number"]),
            )
        )
    return records
