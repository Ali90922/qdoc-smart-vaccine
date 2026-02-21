# QDoc Vaccine Portal - Rule Engine & Rule Base Technical Document

## 1. Purpose of This Document
This document explains the two core technical components that drive the project:
1. **Rule Base**: vaccine policy definitions in data form.
2. **Inference Engine**: deterministic logic that evaluates a patient and classifies each vaccine.

These two components are the heart of the solution and the main basis for rubric scoring.

## 2. Core Files (Source of Truth)
- Rule definitions: `backend/app/data/vaccine_rules.json`
- Inference engine: `backend/app/engine/rule_engine.py`
- Engine test coverage: `backend/tests/engine/test_rule_engine.py`

## 3. Design Principles
- **Deterministic**: same input always produces same output.
- **Explainable**: each classification includes reason text.
- **Policy-driven**: most vaccine policy can be changed in JSON rules without rewriting engine internals.
- **Safety-first defaults**: missing flags resolve to `False`; invalid DOB returns explicit error payload.

## 4. Rule Base Structure
Each vaccine object in `vaccine_rules.json` can define:
- Identity/metadata:
  - `id`, `name`, `description`
- Age gates:
  - `min_age_months`, `max_age_months`
- Dose/timing model:
  - `doses_required`
  - `dose_interval_days` (next dose timing for series)
  - `repeat_interval_days` (recurring vaccines like flu/boosters)
- Eligibility conditioning:
  - `risk_factors_required` (must have at least one)
  - `risk_factor_overrides` + `risk_override_min_age_months`
  - `eligible_at_65_plus` (specific shortcut path for Pneu-C-20)
  - `birth_year_min` (cohort constraints)
- Safety constraints:
  - `contraindicated_if`
  - `is_pregnancy_safe`

## 5. Engine Input/Output Contract
### 5.1 Input
`evaluate_patient(patient, records)` expects:
- `patient` object with:
  - `dob`
  - risk flags (`is_pregnant`, `has_diabetes`, etc.)
- `records` list where each record has:
  - `record.vaccine.vaccine_key`
  - `record.date_given`

### 5.2 Output per vaccine
Engine returns a row with:
- `vaccine_key`, `vaccine_name`
- `status`: one of `NOT_ELIGIBLE`, `OVERDUE`, `DUE_SOON`, `UP_TO_DATE`
- `reason`
- `last_dose`, `next_due`
- `doses_received`, `doses_required`
- `days_until`

## 6. Inference Pipeline (Step-by-Step)
For each vaccine rule:
1. Compute patient age (months) + birth year.
2. Extract all known risk flags safely (`missing => False`).
3. Pull patient records for that vaccine and sort by dose date.
4. Compute dynamic required dose count via `_required_doses_for_rule(...)`.
5. Run eligibility checks `_is_eligible(...)`:
   - min/max age
   - birth-year gate
   - contraindications
   - MMR special cohort logic
   - Pneu-C-20 age 65+ special path
   - required risk-factor gate
   - risk override path
6. Apply vaccine-specific nuance:
   - Rotavirus unstarted after threshold -> not eligible
7. If not eligible -> `NOT_ELIGIBLE` with reason.
8. If eligible and repeating vaccine (`repeat_interval_days`):
   - no prior dose -> `OVERDUE`
   - else classify by due date
9. If eligible and non-repeating:
   - enough doses -> `UP_TO_DATE`
   - zero doses -> `OVERDUE`
   - partial doses + interval -> classify `OVERDUE`/`DUE_SOON`/`UP_TO_DATE` by next due date
   - partial doses + no interval -> `OVERDUE`

## 7. Status Semantics
- `NOT_ELIGIBLE`: failed rule gates (age, cohort, contraindication, missing required risk criteria)
- `OVERDUE`: currently eligible but not started, or due date passed
- `DUE_SOON`: eligible and due in <= `DUE_SOON_DAYS` (30)
- `UP_TO_DATE`: coverage/series currently not due

## 8. Dynamic Dose Logic (Important for Judges)
The engine is not static for all vaccines; required dose count is adjusted contextually.

### 8.1 `pneu_c_15`
- `<24 months` -> 3 doses
- `24-59 months` catch-up path -> 1 dose

### 8.2 `pneu_c_20`
- modeled as 4 doses for `<24 months` path
- single-dose pathway in older age bands

### 8.3 `hpv`
- initiated before age 15 -> 2 doses
- initiated at/after age 15 -> 3 doses

### 8.4 `hepatitis_b`
- baseline -> 2 doses
- high-risk flags present -> 3 doses

### 8.5 `mmr`
- infant travel/outbreak path -> 1 dose
- healthcare/student/birth cohort logic alters required doses

## 9. Special Policy Nuances Implemented
### 9.1 MMR cohort policy
- Infants 6-11 months: only eligible under travel/outbreak conditions
- Adults born before 1970: generally treated as immune unless specific exceptions

### 9.2 Pneumococcal (Pneu-C-20)
- explicit 65+ eligibility path
- separate risk-conditioned pathway from younger ages

### 9.3 RSV
- age + care-setting criteria modeled in rule flags

### 9.4 Rotavirus start-window guard
- unstarted past threshold blocked from initiation

## 10. Rule Coverage Snapshot (Current)
Current rules include:
- Influenza
- DTaP-IPV-Hib
- Tdap-IPV
- Tdap
- Pneu-C-15
- Pneu-C-20
- Rotavirus
- MMRV
- MMR
- Varicella
- Men-C-ACYW
- Hepatitis B
- Hepatitis A
- HPV
- RSV

## 11. Explainability Features
The engine emits reason text for key decisions, including:
- too young / too old thresholds
- contraindication reasons
- required risk-factor failures
- dose-progress messages (e.g., `Dose 2 of 3 due`)

This supports a judge-friendly narrative: every output state can be traced to deterministic logic.

## 12. Test Coverage for Engine Reliability
File: `backend/tests/engine/test_rule_engine.py`

Coverage includes:
- normal cases (eligible and expected status)
- boundary cases (min-age thresholds, due-soon thresholds)
- edge cases (invalid patient DOB, malformed records)
- contraindication cases
- risk-gated cases
- cohort-specific paths (MMR, Pneu-C-20)
- schedule sort/filter and summary aggregation

Recent run result: **51 tests passing**.

## 13. Known Simplifications (Explicitly Declared)
The system intentionally uses simplified/structured abstractions for hackathon scope:
- Some Manitoba policies are represented by grouped risk flags rather than full clinical granularity.
- Product-history sequencing details (for some products) are simplified.
- Reminder delivery is simulated at API/app level rather than integrated with external SMS/email providers.

These are controlled simplifications, not random omissions.

## 14. Why This Architecture Scores Well on Rubric
### Vaccine Rule Engine
- clean separation of policy data and execution logic
- scalable pattern for adding new vaccines

### Classification Accuracy
- deterministic date math and consistent status taxonomy
- strong boundary and edge handling

### Timeline & Visualization
- backend emits normalized due/coverage fields for clear chronology

### Smart Reminder System
- due-soon window is explicit and reusable for reminders

### Input & Technical Quality
- validation + tests + maintainable file structure

## 15. How to Extend the Rule Base Safely
When adding/updating a vaccine:
1. Add/edit rule in `vaccine_rules.json`.
2. If needed, add vaccine-specific branch in `_required_doses_for_rule` or `_is_eligible`.
3. Add tests in `backend/tests/engine/test_rule_engine.py`:
   - at least one normal case
   - one boundary case
   - one invalid/edge case
4. Verify status explanations remain clear in API payload.

## 16. Judge Demo Talking Points (Technical)
- "Rules are data-driven and auditable in JSON."
- "Inference is deterministic and explainable, not black-box."
- "We model age, risk factors, contraindications, cohort logic, and date math."
- "Dynamic dose requirements are computed per vaccine context, not hardcoded globally."
- "Coverage is validated by automated tests over normal/boundary/edge scenarios."

## 17. References
- Manitoba Vaccine Eligibility:
  - https://www.gov.mb.ca/health/publichealth/cdc/vaccineeligibility.html
- Manitoba Immunization Schedules:
  - https://www.gov.mb.ca/health/publichealth/cdc/div/schedules.html
