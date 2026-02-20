# ===========================================
# File: backend/tests/engine/test_rule_engine.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from dataclasses import dataclass
from datetime import date, timedelta
import calendar

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
    resides_in_pch: bool = False
    is_pch_respite: bool = False
    is_panelled_for_pch_in_transitional_care: bool = False
    is_panelled_for_pch_in_chronic_care: bool = False
    has_homelessness: bool = False
    uses_illicit_drugs: bool = False
    has_cochlear_implant: bool = False
    has_hemoglobinopathy: bool = False
    on_immunosuppressive_therapy: bool = False
    is_on_dialysis: bool = False
    is_incarcerated: bool = False
    is_msm: bool = False
    is_healthcare_worker: bool = False
    is_student: bool = False
    is_traveling_to_measles_endemic_country: bool = False
    is_measles_outbreak_exposed: bool = False


def _status(results, vaccine_key):
    return next(r for r in results if r["vaccine_key"] == vaccine_key)


def _months_ago(months: int) -> date:
    today = date.today()
    y = today.year
    m = today.month - months
    while m <= 0:
        m += 12
        y -= 1
    day = min(today.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def test_influenza_not_eligible_when_too_young():
    # 5 months old should be under influenza minimum age (6 months)
    patient = StubPatient(dob=date.today() - timedelta(days=150))
    results = evaluate_patient(patient, [])

    flu = _status(results, "influenza")
    assert flu["status"] == "NOT_ELIGIBLE"
    assert "too young" in (flu["reason"] or "").lower()


def test_influenza_boundary_exactly_min_age_is_eligible():
    # Exactly 6 calendar months should pass minimum-age check and become overdue if no record exists.
    patient = StubPatient(dob=_months_ago(6))
    results = evaluate_patient(patient, [])
    flu = _status(results, "influenza")
    assert flu["status"] in ("OVERDUE", "DUE_SOON", "UP_TO_DATE")


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


def test_influenza_due_soon_boundary_at_30_days():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 35))
    # Due in exactly 30 days for yearly repeat.
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="influenza"),
            dose_number=1,
            date_given=date.today() - timedelta(days=335),
        )
    ]
    results = evaluate_patient(patient, records)
    flu = _status(results, "influenza")
    assert flu["status"] == "DUE_SOON"
    assert flu["days_until"] == 30


def test_influenza_overdue_boundary_when_due_yesterday():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 35))
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="influenza"),
            dose_number=1,
            date_given=date.today() - timedelta(days=366),
        )
    ]
    results = evaluate_patient(patient, records)
    flu = _status(results, "influenza")
    assert flu["status"] == "OVERDUE"


def test_mmr_not_eligible_for_pregnant_patient():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 25), is_pregnant=True)
    results = evaluate_patient(patient, [])

    mmr = _status(results, "mmr")
    assert mmr["status"] == "NOT_ELIGIBLE"
    assert "contraindicated" in (mmr["reason"] or "").lower()


def test_mmr_not_eligible_for_immunocompromised_patient():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 25), is_immunocompromised=True)
    results = evaluate_patient(patient, [])
    mmr = _status(results, "mmr")
    assert mmr["status"] == "NOT_ELIGIBLE"
    assert "contraindicated" in (mmr["reason"] or "").lower()


def test_hepatitis_a_requires_risk_factors():
    # Hepatitis A is configured as risk-factor required in rules JSON
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 22))
    results = evaluate_patient(patient, [])
    hep_a = _status(results, "hepatitis_a")
    assert hep_a["status"] == "NOT_ELIGIBLE"
    assert "only eligible with" in (hep_a["reason"] or "").lower()


def test_hepatitis_a_becomes_eligible_with_risk_factor():
    patient = StubPatient(
        dob=date.today() - timedelta(days=365 * 22),
        has_chronic_liver=True,
    )
    results = evaluate_patient(patient, [])
    hep_a = _status(results, "hepatitis_a")
    # Eligible but no doses started should show as overdue
    assert hep_a["status"] == "OVERDUE"
    assert hep_a["doses_required"] == 2


def test_varicella_not_eligible_for_birth_year_before_cutoff():
    # Varicella rule uses birth_year_min=2008
    patient = StubPatient(dob=date(2000, 6, 1))
    results = evaluate_patient(patient, [])
    varicella = _status(results, "varicella")
    assert varicella["status"] == "NOT_ELIGIBLE"
    assert "born 2008 or later" in (varicella["reason"] or "").lower()


def test_dtap_ipv_hib_boundary_at_max_age_months_is_eligible():
    # 83 months is max age per rules.
    patient = StubPatient(dob=date.today() - timedelta(days=83 * 30))
    results = evaluate_patient(patient, [])
    dtap = _status(results, "dtap_ipv_hib")
    assert dtap["status"] != "NOT_ELIGIBLE"


def test_dtap_ipv_hib_past_max_age_is_not_eligible():
    patient = StubPatient(dob=date.today() - timedelta(days=84 * 31))
    results = evaluate_patient(patient, [])
    dtap = _status(results, "dtap_ipv_hib")
    assert dtap["status"] == "NOT_ELIGIBLE"
    assert "too old" in (dtap["reason"] or "").lower()


def test_tdap_repeat_vaccine_up_to_date_when_not_due_soon():
    # Tdap repeat interval is 3650 days. Dose 100 days ago should be UP_TO_DATE.
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="tdap"),
            dose_number=1,
            date_given=date.today() - timedelta(days=100),
        )
    ]
    results = evaluate_patient(patient, records)
    tdap = _status(results, "tdap")
    assert tdap["status"] == "UP_TO_DATE"
    assert tdap["next_due"] is not None
    assert tdap["days_until"] is not None and tdap["days_until"] > 30


def test_pneu_c_20_eligible_at_65_plus_even_without_risk_factors():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 66))
    results = evaluate_patient(patient, [])
    pneu = _status(results, "pneu_c_20")
    assert pneu["status"] == "OVERDUE"


def test_pneu_c_20_eligible_with_risk_override_at_adult_age():
    patient = StubPatient(
        dob=date.today() - timedelta(days=365 * 30),
        has_diabetes=True,
    )
    results = evaluate_patient(patient, [])
    pneu = _status(results, "pneu_c_20")
    assert pneu["status"] == "OVERDUE"


def test_pneu_c_20_not_eligible_when_under_min_age_even_with_risk():
    # Under 2 years old should fail minimum age gate even with risk.
    patient = StubPatient(
        dob=date.today() - timedelta(days=365 * 1),
        has_diabetes=True,
    )
    results = evaluate_patient(patient, [])
    pneu = _status(results, "pneu_c_20")
    assert pneu["status"] == "NOT_ELIGIBLE"
    assert "too young" in (pneu["reason"] or "").lower()


def test_pneu_c_20_not_eligible_for_healthy_age_30():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    results = evaluate_patient(patient, [])
    pneu = _status(results, "pneu_c_20")
    assert pneu["status"] == "NOT_ELIGIBLE"
    assert "only eligible with" in (pneu["reason"] or "").lower()


def test_multi_dose_series_becomes_up_to_date_after_required_doses():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 25))
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="mmr"),
            dose_number=1,
            date_given=date.today() - timedelta(days=180),
        ),
        StubRecord(
            vaccine=StubVaccine(vaccine_key="mmr"),
            dose_number=2,
            date_given=date.today() - timedelta(days=120),
        ),
    ]
    results = evaluate_patient(patient, records)
    mmr = _status(results, "mmr")
    assert mmr["status"] == "UP_TO_DATE"
    assert mmr["doses_received"] == 2
    assert mmr["doses_required"] == 2


def test_partial_multi_dose_series_overdue_after_interval_passes():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    # MMR dose interval is 28 days; first dose long ago => next dose overdue.
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="mmr"),
            dose_number=1,
            date_given=date.today() - timedelta(days=80),
        )
    ]
    results = evaluate_patient(patient, records)
    mmr = _status(results, "mmr")
    assert mmr["status"] == "OVERDUE"
    assert mmr["next_due"] is not None
    assert mmr["reason"] and "dose 2 of 2 due" in mmr["reason"].lower()


def test_partial_multi_dose_series_due_soon_before_interval():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    # MMR interval 28 days; given 10 days ago => due in 18 days (DUE_SOON)
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="mmr"),
            dose_number=1,
            date_given=date.today() - timedelta(days=10),
        )
    ]
    results = evaluate_patient(patient, records)
    mmr = _status(results, "mmr")
    assert mmr["status"] == "DUE_SOON"
    assert mmr["days_until"] == 18


def test_mmr_not_eligible_for_adult_born_before_1970_without_exception():
    patient = StubPatient(dob=date(1960, 5, 1))
    results = evaluate_patient(patient, [])
    mmr = _status(results, "mmr")
    assert mmr["status"] == "NOT_ELIGIBLE"
    assert "considered immune" in (mmr["reason"] or "").lower()


def test_mmr_eligible_for_adult_born_before_1970_if_healthcare_worker():
    patient = StubPatient(dob=date(1960, 5, 1), is_healthcare_worker=True)
    results = evaluate_patient(patient, [])
    mmr = _status(results, "mmr")
    assert mmr["status"] == "OVERDUE"
    assert mmr["doses_required"] == 2


def test_mmr_eligible_for_infant_6_to_11_months_only_with_travel_or_outbreak():
    patient = StubPatient(
        dob=_months_ago(8),
        is_traveling_to_measles_endemic_country=True,
    )
    results = evaluate_patient(patient, [])
    mmr = _status(results, "mmr")
    assert mmr["status"] == "OVERDUE"
    assert mmr["doses_required"] == 1


def test_mmr_not_eligible_for_infant_6_to_11_months_without_travel_or_outbreak():
    patient = StubPatient(dob=_months_ago(8))
    results = evaluate_patient(patient, [])
    mmr = _status(results, "mmr")
    assert mmr["status"] == "NOT_ELIGIBLE"
    assert "travel/outbreak" in (mmr["reason"] or "").lower()


def test_hpv_requires_3_doses_when_starting_at_15_or_older():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 20))
    results = evaluate_patient(patient, [])
    hpv = _status(results, "hpv")
    assert hpv["doses_required"] == 3


def test_hpv_requires_2_doses_when_patient_under_15():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 13))
    results = evaluate_patient(patient, [])
    hpv = _status(results, "hpv")
    assert hpv["doses_required"] == 2


def test_hpv_stays_2_doses_if_initiated_before_15():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 16))
    first_dose = date.today() - timedelta(days=365 * 2)
    records = [StubRecord(vaccine=StubVaccine(vaccine_key="hpv"), dose_number=1, date_given=first_dose)]
    results = evaluate_patient(patient, records)
    hpv = _status(results, "hpv")
    assert hpv["doses_required"] == 2


def test_rotavirus_not_eligible_if_unstarted_after_start_window():
    patient = StubPatient(dob=_months_ago(5))
    results = evaluate_patient(patient, [])
    rota = _status(results, "rotavirus")
    assert rota["status"] == "NOT_ELIGIBLE"
    assert "too old to start" in (rota["reason"] or "").lower()


def test_rsv_not_eligible_for_age_60_without_care_setting():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 65))
    results = evaluate_patient(patient, [])
    rsv = _status(results, "rsv")
    assert rsv["status"] == "NOT_ELIGIBLE"
    assert "only eligible with" in (rsv["reason"] or "").lower()


def test_rsv_eligible_for_age_60_with_pch_residence():
    patient = StubPatient(
        dob=date.today() - timedelta(days=365 * 65),
        resides_in_pch=True,
    )
    results = evaluate_patient(patient, [])
    rsv = _status(results, "rsv")
    assert rsv["status"] == "OVERDUE"


def test_partial_multi_dose_without_interval_defaults_to_overdue():
    patient = StubPatient(dob=date.today() - timedelta(days=365 * 16))
    # men_c_acyw has doses_required=2 and no interval; partial should become overdue.
    records = [
        StubRecord(
            vaccine=StubVaccine(vaccine_key="men_c_acyw"),
            dose_number=1,
            date_given=date.today() - timedelta(days=20),
        )
    ]
    results = evaluate_patient(patient, records)
    men = _status(results, "men_c_acyw")
    assert men["status"] == "OVERDUE"
    assert "overdue" in (men["reason"] or "").lower()


def test_evaluate_patient_returns_empty_for_none_patient():
    assert evaluate_patient(None, []) == []


def test_evaluate_patient_returns_error_for_invalid_dob():
    patient = StubPatient(dob=None)  # noqa: intentional invalid type for edge case
    results = evaluate_patient(patient, [])
    assert results and "error" in results[0]


def test_malformed_record_entries_are_ignored_safely():
    class BadRecord:
        pass

    patient = StubPatient(dob=date.today() - timedelta(days=365 * 30))
    results = evaluate_patient(patient, [BadRecord()])
    # Should still evaluate normally and include known vaccine statuses.
    flu = _status(results, "influenza")
    assert flu["status"] in ("OVERDUE", "DUE_SOON", "UP_TO_DATE", "NOT_ELIGIBLE")


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


def test_schedule_empty_input_returns_empty_output():
    assert get_upcoming_schedule([]) == []


def test_schedule_ignores_rows_without_next_due():
    upcoming = get_upcoming_schedule(
        [
            {"vaccine_key": "x", "status": "DUE_SOON", "next_due": None},
            {"vaccine_key": "y", "status": "UP_TO_DATE", "next_due": date.today() + timedelta(days=1)},
        ]
    )
    assert [r["vaccine_key"] for r in upcoming] == ["y"]


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


def test_summary_empty_input_returns_all_zeroes():
    assert summarize([]) == {
        "overdue": 0,
        "due_soon": 0,
        "up_to_date": 0,
        "not_eligible": 0,
    }
