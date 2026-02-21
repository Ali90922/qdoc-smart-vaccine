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

Bugs fixed:
  1. _get_patient_flags: now only reads flags that actually exist on the model
  2. eligible_at_65_plus: checked BEFORE risk_factors_required so 65+ patients
     are not incorrectly blocked
  3. Dynamic dose calculation via _required_doses_for_rule for HPV, Hep B, MMR,
     Pneu-C-15
  4. MMR cohort logic: doses required depend on birth year (Manitoba rules)
  5. Men-C-ACYW: dose_interval_days now set in JSON (3285 days ≈ 9 years),
     preventing incorrect OVERDUE for partial series
  6. Rotavirus: series cannot start after 15 weeks (~3.5 months); added explicit
     age check when doses_received == 0
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

RULES_BY_KEY = {v["id"]: v for v in VACCINE_RULES}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _age_in_months(dob: date) -> int:
    """Calculate exact age in months from date of birth."""
    today = date.today()
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months -= 1
    return max(months, 0)


def _age_in_months_on(dob: date, on_date: date) -> int:
    """Calculate age in months on a specific past date (for dose-age logic)."""
    months = (on_date.year - dob.year) * 12 + (on_date.month - dob.month)
    if on_date.day < dob.day:
        months -= 1
    return max(months, 0)


def _birth_year(dob: date) -> int:
    return dob.year


def _classify_by_date(next_due: date) -> str:
    """Return OVERDUE / DUE_SOON / UP_TO_DATE based on next due date."""
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
    FIX 1: Only read flags that actually exist on the Patient model.
    Uses getattr with False default to safely handle any missing attributes.
    """
    flags = [
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
    return {f: bool(getattr(patient, f, False)) for f in flags}


def _get_records_for_vaccine(records: list, vaccine_key: str) -> list:
    """Filter and sort vaccination records for a specific vaccine key."""
    matching = []
    for r in records:
        try:
            key = r.vaccine.vaccine_key if hasattr(r, "vaccine") and r.vaccine else None
            if key == vaccine_key:
                matching.append(r)
        except Exception:
            continue
    return sorted(matching, key=lambda r: r.date_given)


# ── Dynamic Dose Calculation ──────────────────────────────────────────────────

def _required_doses(rule: dict, age_months: int, birth_year: int,
                    flags: dict, patient, vax_records: list) -> int:
    """
    FIX 3 & 4: Calculate the correct number of required doses dynamically
    for vaccines where the dose count depends on age, birth year, or risk factors.
    Falls back to the JSON doses_required for simple cases.
    """
    vaccine_key = rule.get("id")

    # ── Pneu-C-15: 3 doses for infants; 1 catch-up dose for 24-59 months ──────
    if vaccine_key == "pneu_c_15":
        return 1 if age_months >= 24 else 3

    # ── HPV: 2 doses if series started before age 15; otherwise 3 ─────────────
    if vaccine_key == "hpv":
        if vax_records:
            # Check the age at which the first dose was given
            age_at_first_dose = _age_in_months_on(patient.dob, vax_records[0].date_given)
            return 2 if age_at_first_dose < 180 else 3
        # No doses yet — base on current age
        return 2 if age_months < 180 else 3

    # ── Hepatitis B: 2 doses routine; 3 doses for high-risk patients ──────────
    if vaccine_key == "hepatitis_b":
        high_risk_flags = rule.get("risk_factor_overrides", [])
        is_high_risk = any(flags.get(f, False) for f in high_risk_flags)
        return 3 if is_high_risk else 2

    # ── MMR: FIX 4 — doses depend on Manitoba birth-year cohort rules ──────────
    if vaccine_key == "mmr":
        # Adults born before 1970 are generally considered immune — 0 doses needed
        if birth_year < 1970:
            return 0
        # Born 1970–1984: 1 dose recommended
        if birth_year < 1985:
            return 1
        # Born 1985 or later: 2 doses
        return 2

    return rule.get("doses_required", 1)


# ── Core Eligibility Check ────────────────────────────────────────────────────

def _is_eligible(rule: dict, age_months: int, birth_year: int,
                 flags: dict) -> tuple[bool, str]:
    """
    Check whether a patient qualifies for a vaccine at all.
    Returns (eligible: bool, reason: str).

    FIX 2: eligible_at_65_plus is now checked BEFORE risk_factors_required
    so that 65+ patients are not wrongly blocked.
    """
    vaccine_key = rule.get("id")

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

    # 3. Birth-year restriction (e.g. Varicella: born 2008 or later)
    birth_year_min = rule.get("birth_year_min")
    if birth_year_min is not None and birth_year < birth_year_min:
        return False, f"Routine eligibility is for individuals born {birth_year_min} or later"

    # 4. Contraindications — certain conditions block the vaccine entirely
    for condition in rule.get("contraindicated_if", []):
        if flags.get(condition, False):
            label = condition.replace("_", " ").replace("is ", "").replace("has ", "")
            return False, f"Contraindicated due to: {label}"

    # 5. MMR special cohort logic — adults born before 1970 are immune
    if vaccine_key == "mmr":
        if birth_year < 1970:
            return False, "Adults born before 1970 are generally considered immune (not eligible)"

    # 6. FIX 2: eligible_at_65_plus — checked BEFORE risk_factors_required
    #    so 65+ patients are not wrongly blocked by the requirement check below
    if rule.get("eligible_at_65_plus") and age_months >= 780:
        return True, "Eligible at age 65+"

    # 7. Risk factor override — makes patient eligible even if under the default age
    overrides = rule.get("risk_factor_overrides", [])
    override_min_age = rule.get("risk_override_min_age_months", 0)
    if overrides:
        has_override = any(flags.get(f, False) for f in overrides)
        if has_override and age_months >= override_min_age:
            return True, "Eligible due to high-risk medical condition"
        # Vaccine has overrides defined but patient has none — and eligibility
        # depends on either 65+ OR a risk factor (e.g. Pneu-C-20) → block it
        if rule.get("eligible_at_65_plus"):
            return False, "Only eligible at age 65+ or with a qualifying medical condition"

    # 8. Risk factor requirement — vaccine is ONLY for patients with these conditions
    required_factors = rule.get("risk_factors_required", [])
    if required_factors:
        has_any = any(flags.get(f, False) for f in required_factors)
        if not has_any:
            labels = [f.replace("has_", "").replace("is_", "").replace("_", " ")
                      for f in required_factors]
            return False, f"Only eligible with: {', '.join(labels)}"

    return True, "Eligible"


# ── Main Evaluation Function ──────────────────────────────────────────────────

def evaluate_patient(patient, records: list) -> list:
    """
    Run the full rule engine for a patient against all vaccines.

    Parameters:
        patient : Patient ORM object
        records : list of VaccinationRecord ORM objects with .vaccine loaded

    Returns:
        List of result dicts, one per vaccine
    """
    if patient is None:
        return []

    try:
        age_months = _age_in_months(patient.dob)
        birth_year = _birth_year(patient.dob)
    except Exception:
        return [{"error": "Invalid or missing date of birth"}]

    flags   = _get_patient_flags(patient)
    results = []

    for rule in VACCINE_RULES:
        vaccine_key  = rule["id"]
        vaccine_name = rule["name"]

        vax_records    = _get_records_for_vaccine(records or [], vaccine_key)
        doses_received = len(vax_records)
        last_dose_date = vax_records[-1].date_given if vax_records else None

        # Dynamic dose count (FIX 3 & 4)
        doses_req = _required_doses(rule, age_months, birth_year, flags, patient, vax_records)

        # ── Step 1: Eligibility ───────────────────────────────────────────────
        eligible, reason = _is_eligible(rule, age_months, birth_year, flags)

        # FIX 6 — Rotavirus: cannot START series after 15 weeks (~3.5 months)
        if vaccine_key == "rotavirus" and doses_received == 0 and age_months >= 4:
            eligible = False
            reason   = "Too old to start Rotavirus series (first dose must be given before 15 weeks)"

        # MMR special: if 0 doses required (born < 1970), mark as UP_TO_DATE
        if vaccine_key == "mmr" and doses_req == 0:
            results.append({
                "vaccine_key":    vaccine_key,
                "vaccine_name":   vaccine_name,
                "status":         "UP_TO_DATE",
                "reason":         "Adults born before 1970 are considered immune",
                "last_dose":      last_dose_date,
                "next_due":       None,
                "doses_received": doses_received,
                "doses_required": doses_req,
                "days_until":     None,
            })
            continue

        if not eligible:
            results.append({
                "vaccine_key":    vaccine_key,
                "vaccine_name":   vaccine_name,
                "status":         "NOT_ELIGIBLE",
                "reason":         reason,
                "last_dose":      last_dose_date,
                "next_due":       None,
                "doses_received": doses_received,
                "doses_required": doses_req,
                "days_until":     None,
            })
            continue

        # ── Step 2: Repeating vaccines (annual flu, Tdap every 10 yrs, etc.) ──
        repeat_interval = rule.get("repeat_interval_days")
        if repeat_interval:
            if last_dose_date is None:
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

        # ── Step 3: Non-repeating vaccines ───────────────────────────────────
        dose_interval = rule.get("dose_interval_days")

        if doses_received >= doses_req:
            # All required doses complete
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
            # Eligible but no doses at all
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
            # Partial doses — calculate when next dose is due
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
                # No interval defined — mark overdue conservatively
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


# ── Summary Helper ────────────────────────────────────────────────────────────

def summarize(results: list) -> dict:
    """Count vaccines in each status bucket."""
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


# ── Upcoming Schedule Filter ──────────────────────────────────────────────────

def get_upcoming_schedule(results: list) -> list:
    """
    Return DUE_SOON and UP_TO_DATE vaccines that have a next_due date,
    sorted ascending by due date.
    """
    upcoming = [
        r for r in results
        if r.get("status") in ("DUE_SOON", "UP_TO_DATE") and r.get("next_due") is not None
    ]
    return sorted(upcoming, key=lambda r: r["next_due"])
