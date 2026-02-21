# QDoc Smart Vaccine System - Judge Cheat Sheet

## 1) 30-Second Pitch
We built a deterministic vaccine eligibility and reminder platform. It takes patient profile + vaccine history, applies Manitoba-aligned rule logic, and classifies each vaccine as:
- `OVERDUE`
- `DUE_SOON`
- `UP_TO_DATE`
- `NOT_ELIGIBLE`

Every result is explainable and test-backed.

## 2) Why This Scores Well
- Deterministic rule engine (no black box).
- Explainable reasons per status.
- Handles age, risk, contraindications, cohort logic, and timing.
- Frontend uses normalized status output for dashboard and schedule views.
- Good automated coverage (`74 passed` backend tests).

## 3) Decision Pipeline (Per Vaccine)
Source: `backend/app/engine/rule_engine.py`

1. Compute age in months + birth year.
2. Load vaccine rule from `backend/app/data/vaccine_rules.json`.
3. Compute dynamic required doses for specific vaccines.
4. Run eligibility checks in sequence:
   - age gates
   - cohort gates
   - contraindications
   - age-65+ shortcut where defined
   - risk override / required-risk checks
5. Apply timing logic:
   - repeating vaccines via `repeat_interval_days`
   - non-repeating vaccines via dose progress and `dose_interval_days`
6. Return status + reason + timing fields.

## 4) Current Rule Highlights
- `pneu_c_15`: infant 3-dose path vs catch-up 1-dose path.
- `hpv`: 2 doses if started before 15, otherwise 3.
- `hepatitis_b`: 2 baseline doses, 3 for high-risk profiles.
- `mmr`: birth-year cohorts, including immune cohort handling (born before 1970).
- `pneu_c_20`: age 65+ pathway and high-risk pathway.
- `rotavirus`: explicit start-window guard for unstarted series.
- `men_c_acyw`: long interval supports grade-6 style second-dose timing.
- `rsv`: current rule base supports age-based 60+ annual pathway.

## 5) Status Semantics
- `NOT_ELIGIBLE`: fails policy gates.
- `OVERDUE`: eligible but missed/not started.
- `DUE_SOON`: due in <= 30 days.
- `UP_TO_DATE`: currently covered or completed.

## 6) Demo Flow (2 Minutes)
1. Show baseline profile and status mix (`NOT_ELIGIBLE` vs `OVERDUE`).
2. Toggle risk factors and show deterministic status changes.
3. Show cohort behavior (MMR birth-year effect).
4. Show dynamic dose behavior (HPV or Hep B).
5. Trigger reminder simulation for actionable vaccines.
6. Close with test evidence (`cd backend && pytest -q`).

## 7) Judge Q&A One-Liners
- Why rules over AI?
  - Clinical eligibility needs transparent, auditable logic.
- How do policy changes get updated?
  - Mostly JSON rule updates; code changes only for truly vaccine-specific logic.
- How do you handle edge cases?
  - Boundary, invalid-input, cohort, and risk-based scenarios are covered in tests.

## 8) Core Files
- `backend/app/data/vaccine_rules.json`
- `backend/app/engine/rule_engine.py`
- `backend/tests/engine/test_rule_engine.py`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/Schedule.jsx`
