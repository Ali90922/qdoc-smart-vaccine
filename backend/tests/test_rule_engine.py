# ===========================================
# File: backend/tests/test_rule_engine.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.engine.rule_engine import evaluate_patient, get_upcoming_schedule, summarize


@dataclass
class StubVaccine:
    vaccine_key: str


@dataclass
class StubRecord:
    vaccine: StubVaccine
    dose_number: int
    date_given: date


@dataclass
class StubPatient:
    dob: date
    is_pregnant: bool = False
    is_immunocompromised: bool = False
    has_diabetes: bool = False
    has_chronic_lung: bool = False
    has_heart_disease: bool = False
    has_chronic_kidney: bool = False
    has_chronic_liver: bool = False
    has_asplenia: bool = False
    has_hiv: bool = False


def _status(results, vaccine_key):
    return next(r for r in results if r["vaccine_key"] == vaccine_key)


def test_influenza_not_eligible_when_too_young():
    # 5 months old should be under influenza minimum age (6 months)
    patient = StubPatient(dob=date.today() - timedelta(days=150))
    results = evaluate_patient(patient, [])

    flu = _status(results, "influenza")
    assert flu["status"] == "NOT_ELIGIBLE"
    assert "too young" in (flu["reason"] or "").lower()


def test_influenza_overdue_when_eligible_without_history():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    results = evaluate_patient(patient, [])

    flu = _status(results, "influenza")
    assert flu["status"] == "OVERDUE"
    assert flu["next_due"] == date.today()


def test_influenza_due_soon_when_next_dose_within_30_days():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 40))
    # Flu repeats every 365 days; last dose 340 days ago => due in 25 days
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="influenza"),
            dose_number=1,
            date_given=date.today() - timedelta(days=340),
        )
    ]
    results = evaluate_patient(patient, records)

    flu = _status(results, "influenza")
    assert flu["status"] == "DUE_SOON"
    assert flu["days_until"] is not None
    assert 0 <= flu["days_until"] <= 30


def test_mmr_not_eligible_for_pregnant_patient():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 25), is_pregnant=True)
    results = evaluate_patient(patient, [])

    mmr = _status(results, "mmr")
    assert mmr["status"] == "NOT_ELIGIBLE"
    assert "contraindicated" in (mmr["reason"] or "").lower()


def test_schedule_filters_and_orders_upcoming_entries():
    results = [
        {
            "vaccine_key": "a",
            "vaccine_name": "A",
            "status": "DUE_SOON",
            "next_due": date.today() + timedelta(days=5),
        },
        {
            "vaccine_key": "b",
            "vaccine_name": "B",
            "status": "UP_TO_DATE",
            "next_due": date.today() + timedelta(days=50),
        },
        {
            "vaccine_key": "c",
            "vaccine_name": "C",
            "status": "OVERDUE",
            "next_due": date.today() - timedelta(days=1),
        },
    ]
    upcoming = get_upcoming_schedule(results)
    assert [item["vaccine_key"] for item in upcoming] == ["a", "b"]


def test_summary_counts_statuses():
    data = [
        {"status": "OVERDUE"},
        {"status": "DUE_SOON"},
        {"status": "DUE_SOON"},
        {"status": "UP_TO_DATE"},
        {"status": "NOT_ELIGIBLE"},
    ]
    summary = summarize(data)
    assert summary == {
        "overdue": 1,
        "due_soon": 2,
        "up_to_date": 1,
        "not_eligible": 1,
    }

