# QDoc Vaccine Portal - Rule Engine Technical Notes

## 1) Purpose
This document describes the current rule base and deterministic inference engine used to classify vaccine status.

## 2) Source of Truth
- Rules: `backend/app/data/vaccine_rules.json`
- Engine: `backend/app/engine/rule_engine.py`
- Tests: `backend/tests/engine/test_rule_engine.py`

## 3) Design Goals
- Deterministic output for the same input.
- Explainable status and reason per vaccine.
- Policy-first configuration via JSON, with minimal code branches only where needed.
- Safe defaults: missing flags are treated as `False`; invalid DOB returns explicit error payload.

## 4) Rule Model
Each vaccine rule can define:
- Identity: `id`, `name`, `description`
- Age gates: `min_age_months`, `max_age_months`
- Dose model: `doses_required`, `dose_interval_days`, `repeat_interval_days`
- Eligibility gates:
  - `risk_factors_required`
  - `risk_factor_overrides`
  - `risk_override_min_age_months`
  - `eligible_at_65_plus`
  - `birth_year_min`
- Contraindications: `contraindicated_if`

## 5) Engine Input and Output
### Input
`evaluate_patient(patient, records)` expects:
- `patient.dob`
- known boolean risk fields on patient
- vaccination records with `record.vaccine.vaccine_key` and `record.date_given`

### Output per vaccine
- `vaccine_key`, `vaccine_name`
- `status` in `{NOT_ELIGIBLE, OVERDUE, DUE_SOON, UP_TO_DATE}`
- `reason`
- `last_dose`, `next_due`
- `doses_received`, `doses_required`
- `days_until`

## 6) Inference Pipeline
For each vaccine:
1. Compute age in months and birth year.
2. Read only known risk flags from patient (`_get_patient_flags`).
3. Collect and sort records for that vaccine.
4. Compute required doses with `_required_doses(...)`.
5. Run `_is_eligible(...)` checks:
   - min/max age
   - birth-year cutoff (if present)
   - contraindications
   - MMR immune cohort gate
   - `eligible_at_65_plus` shortcut
   - risk override path
   - required-risk path
6. Apply vaccine-specific guard:
   - Rotavirus cannot be started at or after 4 months if no dose exists.
7. Apply status logic:
   - repeating vaccines classify by next due date
   - non-repeating vaccines classify by dose progress and interval timing

## 7) Dynamic Required Dose Logic
The engine calculates dose count dynamically for:
- `pneu_c_15`
  - `<24 months`: 3 doses
  - `24-59 months`: 1 catch-up dose
- `hpv`
  - if first dose started before age 15: 2 doses
  - otherwise: 3 doses
- `hepatitis_b`
  - baseline: 2 doses
  - high-risk profile: 3 doses
- `mmr`
  - born before 1970: 0 doses (immune cohort)
  - born 1970-1984: 1 dose
  - born 1985 or later: 2 doses

## 8) Current Policy Nuances
- Pneu-C-20:
  - eligible at age 65+ regardless of risk flags
  - high-risk pathway also supported (with configured age floor)
  - otherwise not eligible
- MMR:
  - immune cohort is returned as `UP_TO_DATE` with `doses_required = 0`
- Rotavirus:
  - explicit start-window guard for unstarted series
- Men-C-ACYW:
  - long inter-dose timing (`dose_interval_days = 3285`) to avoid false overdue status for grade-6 spacing
- RSV:
  - current rule base models age-based pathway (60+) with annual repeat interval

## 9) Status Semantics
- `NOT_ELIGIBLE`: blocked by gates (age, cohort, contraindication, missing required risk criteria)
- `OVERDUE`: eligible but due date passed, or eligible with no started doses
- `DUE_SOON`: due in 30 days or less
- `UP_TO_DATE`: currently covered or series complete

## 10) Reliability and Validation
- Engine and rule tests: `backend/tests/engine/test_rule_engine.py`
- Schema tests: `backend/tests/schemas/test_profile_schemas.py`
- Current run: `74 passed` (`cd backend && pytest -q`)

## 11) Extension Workflow
When adding/changing a vaccine rule:
1. Update `backend/app/data/vaccine_rules.json`.
2. Add/adjust logic in `_required_doses(...)` only if policy cannot be represented by data fields.
3. Add focused tests (normal, boundary, edge).
4. Verify reason text is still clear and status behavior is deterministic.

## 12) References
- Manitoba Vaccine Eligibility:
  - https://www.gov.mb.ca/health/publichealth/cdc/vaccineeligibility.html
- Manitoba Immunization Schedules:
  - https://www.gov.mb.ca/health/publichealth/cdc/div/schedules.html
