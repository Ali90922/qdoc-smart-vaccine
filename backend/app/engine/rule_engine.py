# ===========================================
# File: backend/app/engine/rule_engine.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

"""
QDoc Vaccine Rule Engine
========================
Based on Manitoba Health Immunization Program:
- https://www.gov.mb.ca/health/publichealth/cdc/vaccineeligibility.html
- https://www.gov.mb.ca/health/publichealth/cdc/div/schedules.html

Status definitions:
  NOT_ELIGIBLE  — patient does not qualify (age, condition, contraindication)
  OVERDUE       — eligible but missed dose(s) or past due date
  DUE_SOON      — next dose due within DUE_SOON_DAYS (default 30)
  UP_TO_DATE    — all required doses complete and not yet due again
"""

import json
import os
from datetime import date, timedelta
from typing import List, Optional

# ── Config ────────────────────────────────────────────────────────────────────

DUE_SOON_DAYS = 30

_rules_path = os.path.join(os.path.dirname(__file__), "../data/vaccine_rules.json")
with open(_rules_path) as f:
    VACCINE_RULES: List[dict] = json.load(f)["vaccines"]

# Build lookup dict: vaccine_key → rule
RULES_BY_KEY = {v["id"]: v for v in VACCINE_RULES}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _age_in_months(dob: date) -> int:
    """Calculate exact age in months from date of birth."""
    today = date.today()
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    # Adjust if day hasn't been reached yet this month
    if today.day < dob.day:
        months -= 1
    return max(months, 0)


def _birth_year(dob: date) -> int:
    return dob.year


def _classify_by_date(next_due: date) -> str:
    """Given a next due date, return OVERDUE / DUE_SOON / UP_TO_DATE."""
    today = date.today()
    days_left = (next_due - today).days
    if days_left < 0:
        return "OVERDUE"
    elif days_left <= DUE_SOON_DAYS:
        return "DUE_SOON"
    else:
        return "UP_TO_DATE"


def _days_until(next_due: date) -> Optional[int]:
    days = (next_due - date.today()).days
    return days if days >= 0 else None


def _get_patient_flags(patient) -> dict:
    """
    Safely extract all boolean risk factor flags from patient object.
    Returns False for any missing attribute (handles edge cases).
    """
    flags = [
        "is_pregnant", "is_immunocompromised", "has_diabetes",
        "has_chronic_lung", "has_heart_disease", "has_chronic_kidney",
        "has_chronic_liver", "has_asplenia", "has_hiv",
        "resides_in_pch", "is_pch_respite",
        "is_panelled_for_pch_in_transitional_care", "is_panelled_for_pch_in_chronic_care",
        "has_homelessness", "uses_illicit_drugs", "has_cochlear_implant",
        "has_hemoglobinopathy", "on_immunosuppressive_therapy", "is_on_dialysis",
        "is_incarcerated", "is_msm", "is_healthcare_worker", "is_student",
        "is_traveling_to_measles_endemic_country", "is_measles_outbreak_exposed"
    ]
    return {f: bool(getattr(patient, f, False)) for f in flags}


def _get_records_for_vaccine(records: list, vaccine_key: str) -> list:
    """Filter and sort vaccination records for a specific vaccine."""
    matching = []
    for r in records:
        try:
            key = r.vaccine.vaccine_key if hasattr(r, "vaccine") and r.vaccine else None
            if key == vaccine_key:
                matching.append(r)
        except Exception:
            continue
    return sorted(matching, key=lambda r: r.date_given)


# ── Core Eligibility Check ────────────────────────────────────────────────────

def _is_eligible(rule: dict, age_months: int, birth_year: int, flags: dict) -> tuple[bool, str]:
    """
    Check whether a patient is eligible for a vaccine at all.
    Returns (eligible: bool, reason: str)
    """

    # 1. Age — minimum
    min_age = rule.get("min_age_months")
    if min_age is not None and age_months < min_age:
        years = round(min_age / 12, 1)
        return False, f"Patient is too young (minimum age: {years} years)"

    # 2. Age — maximum
    max_age = rule.get("max_age_months")
    if max_age is not None and age_months > max_age:
        years = round(max_age / 12, 1)
        return False, f"Patient is too old for this vaccine (maximum age: {years} years)"

    # 3. Birth year restriction (e.g. Varicella: born 2008 or later)
    birth_year_min = rule.get("birth_year_min")
    if birth_year_min is not None and birth_year < birth_year_min:
        return False, f"Routine eligibility is for individuals born {birth_year_min} or later"

    # 4. Contraindications — certain conditions block the vaccine
    contraindications = rule.get("contraindicated_if", [])
    for condition in contraindications:
        if flags.get(condition, False):
            label = condition.replace("_", " ").replace("is ", "").replace("has ", "")
            return False, f"Contraindicated due to: {label}"

    # 5. MMR special cohort logic (Manitoba)
    if rule.get("id") == "mmr":
        if age_months < 6:
            return False, "Patient is too young (minimum age: 0.5 years)"
        if age_months < 12:
            if flags.get("is_traveling_to_measles_endemic_country") or flags.get("is_measles_outbreak_exposed"):
                return True, "Eligible due to infant travel/outbreak criteria"
            return False, "Infants 6-11 months are only eligible for travel/outbreak criteria"
        if birth_year < 1970 and not (flags.get("is_healthcare_worker") or flags.get("is_student")):
            return False, "Adults born before 1970 are generally considered immune"

    # 6. Pneu-C-20 special rule: age 65+ pathway regardless of listed risk factors
    if rule.get("id") == "pneu_c_20" and rule.get("eligible_at_65_plus") and age_months >= 780:
        return True, "Eligible at age 65+"

    # 7. Risk factor requirement — vaccine ONLY for patients with these conditions
    required_factors = rule.get("risk_factors_required", [])
    if required_factors:
        has_any = any(flags.get(f, False) for f in required_factors)
        if not has_any:
            labels = [f.replace("has_", "").replace("is_", "").replace("_", " ") for f in required_factors]
            return False, f"Only eligible with: {', '.join(labels)}"

    # 8. Risk factor override — makes patient eligible regardless of age restriction
    overrides = rule.get("risk_factor_overrides", [])
    override_min_age = rule.get("risk_override_min_age_months", 0)
    if overrides:
        has_override = any(flags.get(f, False) for f in overrides)
        if has_override and age_months >= override_min_age:
            return True, "Eligible due to high-risk medical condition"

    return True, "Eligible"


def _age_in_months_on(dob: date, on_date: date) -> int:
    months = (on_date.year - dob.year) * 12 + (on_date.month - dob.month)
    if on_date.day < dob.day:
        months -= 1
    return max(months, 0)


def _required_doses_for_rule(rule: dict, age_months: int, birth_year: int, flags: dict, patient, records_for_vaccine: list) -> int:
    vaccine_key = rule.get("id")
    doses_req = rule.get("doses_required", 1)

    if vaccine_key == "pneu_c_15":
        if age_months >= 24:
            return 1
        return 3

    if vaccine_key == "pneu_c_20":
        if age_months < 24:
            return 4
        if age_months < 216:
            return 1
        return 1

    if vaccine_key == "hpv":
        # Manitoba schedule: 2 doses when initiated before 15; otherwise 3 doses.
        if age_months < 180:
            return 2
        if records_for_vaccine:
            first_dose_age = _age_in_months_on(patient.dob, records_for_vaccine[0].date_given)
            if first_dose_age < 180:
                return 2
        return 3

    if vaccine_key == "hepatitis_b":
        high_risk = any(
            flags.get(flag, False)
            for flag in rule.get("risk_factor_overrides", [])
        )
        return 3 if high_risk else 2

    if vaccine_key == "mmr":
        if age_months < 12:
            return 1
        if flags.get("is_healthcare_worker"):
            return 2
        if flags.get("is_student"):
            return 1 if birth_year < 1970 else 2
        if birth_year >= 1985:
            return 2
        if birth_year >= 1970:
            return 1
        return 0

    return doses_req


# ── Main Evaluation Function ──────────────────────────────────────────────────

def evaluate_patient(patient, records: list) -> list:
    """
    Run the full rule engine for a patient against all vaccines.

    Parameters:
        patient: SQLAlchemy Patient ORM object
        records: list of VaccinationRecord ORM objects with .vaccine loaded

    Returns:
        List of dicts with vaccine status for each vaccine
    """

    # Edge case: no patient object
    if patient is None:
        return []

    # Edge case: missing or invalid DOB
    try:
        age_months = _age_in_months(patient.dob)
        birth_year = _birth_year(patient.dob)
    except Exception:
        return [{"error": "Invalid or missing date of birth"}]

    flags = _get_patient_flags(patient)
    results = []

    for rule in VACCINE_RULES:
        vaccine_key  = rule["id"]
        vaccine_name = rule["name"]

        # Get this patient's records for this vaccine (handles missing records gracefully)
        vax_records     = _get_records_for_vaccine(records or [], vaccine_key)
        doses_received  = len(vax_records)
        last_dose_date  = vax_records[-1].date_given if vax_records else None
        doses_req = _required_doses_for_rule(rule, age_months, birth_year, flags, patient, vax_records)

        # ── Step 1: Eligibility check ─────────────────────────────────────────
        eligible, reason = _is_eligible(rule, age_months, birth_year, flags)

        # Rotavirus Manitoba nuance: do not start series after 15 weeks.
        if vaccine_key == "rotavirus" and doses_received == 0 and age_months >= 4:
            eligible = False
            reason = "Too old to start Rotavirus series (must begin before 15 weeks)"

        if not eligible:
            results.append({
                "vaccine_key":     vaccine_key,
                "vaccine_name":    vaccine_name,
                "status":          "NOT_ELIGIBLE",
                "reason":          reason,
                "last_dose":       last_dose_date,
                "next_due":        None,
                "doses_received":  doses_received,
                "doses_required":  doses_req,
                "days_until":      None,
            })
            continue

        # ── Step 2: Repeating vaccines (e.g. annual flu, Tdap every 10 yrs) ──
        repeat_interval = rule.get("repeat_interval_days")
        if repeat_interval:
            if last_dose_date is None:
                # Eligible but never received — overdue immediately
                results.append({
                    "vaccine_key":    vaccine_key,
                    "vaccine_name":   vaccine_name,
                    "status":         "OVERDUE",
                    "reason":         "No doses on record",
                    "last_dose":      None,
                    "next_due":       date.today(),
                    "doses_received": 0,
                    "doses_required": doses_req,
                    "days_until":     None,
                })
            else:
                next_due = last_dose_date + timedelta(days=repeat_interval)
                status   = _classify_by_date(next_due)
                results.append({
                    "vaccine_key":    vaccine_key,
                    "vaccine_name":   vaccine_name,
                    "status":         status,
                    "reason":         None,
                    "last_dose":      last_dose_date,
                    "next_due":       next_due,
                    "doses_received": doses_received,
                    "doses_required": doses_req,
                    "days_until":     _days_until(next_due) if status in ("DUE_SOON", "UP_TO_DATE") else None,
                })
            continue

        # ── Step 3: Non-repeating multi-dose vaccines ──────────────────────────
        dose_interval = rule.get("dose_interval_days")

        if doses_received >= doses_req:
            # All doses complete
            results.append({
                "vaccine_key":    vaccine_key,
                "vaccine_name":   vaccine_name,
                "status":         "UP_TO_DATE",
                "reason":         "All required doses completed",
                "last_dose":      last_dose_date,
                "next_due":       None,
                "doses_received": doses_received,
                "doses_required": doses_req,
                "days_until":     None,
            })
        elif doses_received == 0:
            # Eligible but never started
            results.append({
                "vaccine_key":    vaccine_key,
                "vaccine_name":   vaccine_name,
                "status":         "OVERDUE",
                "reason":         "No doses received yet",
                "last_dose":      None,
                "next_due":       date.today(),
                "doses_received": 0,
                "doses_required": doses_req,
                "days_until":     None,
            })
        else:
            # Partially vaccinated — calculate when next dose is due
            if dose_interval and last_dose_date:
                next_due = last_dose_date + timedelta(days=dose_interval)
                status   = _classify_by_date(next_due)
                results.append({
                    "vaccine_key":    vaccine_key,
                    "vaccine_name":   vaccine_name,
                    "status":         status,
                    "reason":         f"Dose {doses_received + 1} of {doses_req} due",
                    "last_dose":      last_dose_date,
                    "next_due":       next_due,
                    "doses_received": doses_received,
                    "doses_required": doses_req,
                    "days_until":     _days_until(next_due) if status in ("DUE_SOON", "UP_TO_DATE") else None,
                })
            else:
                # No interval defined and partial doses — flag as overdue
                results.append({
                    "vaccine_key":    vaccine_key,
                    "vaccine_name":   vaccine_name,
                    "status":         "OVERDUE",
                    "reason":         f"Dose {doses_received + 1} of {doses_req} overdue",
                    "last_dose":      last_dose_date,
                    "next_due":       date.today(),
                    "doses_received": doses_received,
                    "doses_required": doses_req,
                    "days_until":     None,
                })

    return results


# ── Summary Helper ─────────────────────────────────────────────────────────────

def summarize(results: list) -> dict:
    """Count vaccines in each status category."""
    summary = {"overdue": 0, "due_soon": 0, "up_to_date": 0, "not_eligible": 0}
    for r in results:
        status = r.get("status", "")
        if status == "OVERDUE":
            summary["overdue"] += 1
        elif status == "DUE_SOON":
            summary["due_soon"] += 1
        elif status == "UP_TO_DATE":
            summary["up_to_date"] += 1
        elif status == "NOT_ELIGIBLE":
            summary["not_eligible"] += 1
    return summary


# ── Upcoming Schedule Filter ───────────────────────────────────────────────────

def get_upcoming_schedule(results: list) -> list:
    """
    Filter and sort results for the upcoming schedule page.
    Returns only DUE_SOON and UP_TO_DATE vaccines that have a next_due date,
    sorted by due date ascending.
    """
    upcoming = [
        r for r in results
        if r.get("status") in ("DUE_SOON", "UP_TO_DATE") and r.get("next_due") is not None
    ]
    return sorted(upcoming, key=lambda r: r["next_due"])
