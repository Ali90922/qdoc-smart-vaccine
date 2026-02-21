# Edge Cases and Policy Gap Analysis

## Scope
This document compares:
- PDF reference: `/Users/Ali_Nawaz/Downloads/vaccine_rules_reference.pdf`
- Extracted text snapshot: `vaccine_rules_reference_extracted.txt`
- Current rules: `backend/app/data/vaccine_rules.json`
- Current engine: `backend/app/engine/rule_engine.py`

No rule or engine changes are made in this analysis.

## Executive Summary
- Overall alignment is strong for core age gates, intervals, dynamic dose handling, and many vaccine constraints.
- Several policy nuances documented in the reference are not currently implemented in the engine/rules.
- Most notable gaps are in MMR exceptions and RSV policy details.

## High-Confidence Matches
- Dynamic HPV dosing by age at first dose:
  - PDF: `vaccine_rules_reference_extracted.txt:324-329`
  - Engine: `backend/app/engine/rule_engine.py:130-137`
- Dynamic Hepatitis B dosing (2 vs 3 for high-risk):
  - PDF: `vaccine_rules_reference_extracted.txt:274-278`
  - Engine: `backend/app/engine/rule_engine.py:139-143`
- Pneu-C-15 catch-up behavior (24-59 months => 1 dose):
  - PDF: `vaccine_rules_reference_extracted.txt:109-112`
  - Engine: `backend/app/engine/rule_engine.py:126-128`
- Pneu-C-20 age/risk gating pattern:
  - PDF: `vaccine_rules_reference_extracted.txt:132-138`
  - Rules+Engine: `backend/app/data/vaccine_rules.json:74-97`, `backend/app/engine/rule_engine.py:200-215`
- Rotavirus "too old to start" guard:
  - PDF: `vaccine_rules_reference_extracted.txt:157-163`
  - Engine: `backend/app/engine/rule_engine.py:268-271`
- Men-C-ACYW long interval (3285 days) and high-risk 2-month override:
  - PDF: `vaccine_rules_reference_extracted.txt:239-253`
  - Rules: `backend/app/data/vaccine_rules.json:156-171`

## Gaps and Edge Cases Not Fully Implemented

### 1) MMR healthcare-worker exception
- PDF states: healthcare workers should always require 2 doses regardless of birth year.
  - Reference: `vaccine_rules_reference_extracted.txt:206`
- Current engine behavior:
  - MMR dose logic is cohort-only (born <1970 => 0, 1970-1984 => 1, 1985+ => 2).
  - No healthcare-worker override exists.
  - Code: `backend/app/engine/rule_engine.py:145-154`
- Status: **Not implemented**

### 2) MMR infant travel dose (6-11 months)
- PDF states: infant travel dose may be given at 6-11 months and does not count toward routine schedule.
  - Reference: `vaccine_rules_reference_extracted.txt:207-208`
- Current engine/rules:
  - MMR minimum age is 12 months.
  - No travel/outbreak risk flags are read by `_get_patient_flags`.
  - Rules: `backend/app/data/vaccine_rules.json:127-138`
  - Engine flags list: `backend/app/engine/rule_engine.py:88-98`
- Status: **Not implemented**

### 3) RSV care-setting qualifiers
- PDF notes Manitoba policy is tied to care-setting qualifiers (PCH/panel flags), and age-only behavior is a known gap.
  - Reference: `vaccine_rules_reference_extracted.txt:337-354`
- Current rules/engine:
  - RSV rule has no required risk factors and triggers by age >= 60.
  - Rules: `backend/app/data/vaccine_rules.json:229-240`
  - Engine age/eligibility flow: `backend/app/engine/rule_engine.py:172-226`
- Status: **Not implemented** (policy nuance not enforced)

### 4) RSV repeat interval policy intent
- PDF notes JSON has annual repeat interval, while policy intent is one-time dose.
  - Reference: `vaccine_rules_reference_extracted.txt:355-356`
- Current rule:
  - `repeat_interval_days = 365`
  - Rules: `backend/app/data/vaccine_rules.json:236`
- Status: **Potential policy mismatch**

### 5) Hepatitis A expanded risk factors
- PDF notes additional qualifiers (homelessness, illicit drug use, MSM) and asks for field mapping verification.
  - Reference: `vaccine_rules_reference_extracted.txt:303-304`
- Current rules/modeled factors:
  - `has_chronic_liver`, `has_chronic_kidney`, `has_hiv`, `is_immunocompromised`
  - Rules: `backend/app/data/vaccine_rules.json:204-209`
  - Engine only reads limited flags list: `backend/app/engine/rule_engine.py:88-98`
- Status: **Partially implemented**

### 6) Influenza first-season under-9 two-dose nuance
- PDF explicitly states engine currently uses 1-dose logic for all ages.
  - Reference: `vaccine_rules_reference_extracted.txt:23-24`
- Current rules/engine:
  - Flu uses single dose with annual repeat.
  - Rules: `backend/app/data/vaccine_rules.json:9-11`
  - Engine repeating-dose logic: `backend/app/engine/rule_engine.py:302-331`
- Status: **Known simplification**

### 7) Tdap pregnancy timing nuance
- PDF includes recommendation timing (27-32 weeks) and pregnancy-specific nuance.
  - Reference: `vaccine_rules_reference_extracted.txt:91-92`
- Current rules/engine:
  - Tdap modeled as age + repeat interval; no trimester/timing-specific branch.
  - Rules: `backend/app/data/vaccine_rules.json:46-57`
- Status: **Not explicitly modeled**

### 8) Tdap catch-up wording for specific birth cohort
- PDF mentions additional catch-up statement for adults born on/after Jan 1, 1989.
  - Reference: `vaccine_rules_reference_extracted.txt:90`
- Current rules/engine:
  - Uses generic age threshold (`min_age_months = 156`) with no cohort-specific catch-up branch.
  - Rules: `backend/app/data/vaccine_rules.json:49`
- Status: **Not explicitly modeled**

## Notes on Deterministic Behavior
- The core engine behavior remains deterministic and internally consistent.
- Most gaps are policy-detail coverage gaps, not code defects in current implemented logic.

## Suggested Use of This Document
- Use this as a judge-facing "known edge cases and policy deltas" appendix.
- Keep it versioned alongside future updates to `vaccine_rules.json` and `rule_engine.py`.
