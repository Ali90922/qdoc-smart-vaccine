# ===========================================
# File: backend/tests/schemas/test_profile_schemas.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas import ProfileCreateRequest, VaccinationRecordInput


def test_vaccination_record_accepts_valid_input():
    row = VaccinationRecordInput(
        vaccine_key=" MMR ",
        dose_number=1,
        date_given=date.today() - timedelta(days=1),
    )
    assert row.vaccine_key == "mmr"


def test_vaccination_record_rejects_empty_vaccine_key():
    with pytest.raises(ValidationError):
        VaccinationRecordInput(
            vaccine_key="   ",
            dose_number=1,
            date_given=date.today() - timedelta(days=1),
        )


def test_vaccination_record_rejects_future_date():
    with pytest.raises(ValidationError):
        VaccinationRecordInput(
            vaccine_key="mmr",
            dose_number=1,
            date_given=date.today() + timedelta(days=1),
        )


def test_vaccination_record_rejects_non_positive_dose():
    with pytest.raises(ValidationError):
        VaccinationRecordInput(
            vaccine_key="mmr",
            dose_number=0,
            date_given=date.today(),
        )


def test_profile_create_rejects_future_dob():
    with pytest.raises(ValidationError):
        ProfileCreateRequest(
            name="John",
            dob=date.today() + timedelta(days=1),
            vaccination_history=[],
        )


def test_profile_create_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProfileCreateRequest(
            name="   ",
            dob=date.today() - timedelta(days=365 * 20),
            vaccination_history=[],
        )


def test_profile_create_allows_empty_history():
    profile = ProfileCreateRequest(
        name="John",
        dob=date.today() - timedelta(days=365 * 20),
        vaccination_history=[],
    )
    assert profile.name == "John"
    assert profile.vaccination_history == []


def test_profile_create_allows_none_history():
    profile = ProfileCreateRequest(
        name="Jane",
        dob=date.today() - timedelta(days=365 * 20),
        vaccination_history=None,
    )
    assert profile.vaccination_history is None


def test_profile_create_rejects_duplicate_vaccine_dose_combination():
    with pytest.raises(ValidationError):
        ProfileCreateRequest(
            name="Alice",
            dob=date.today() - timedelta(days=365 * 25),
            vaccination_history=[
                {"vaccine_key": "mmr", "dose_number": 1, "date_given": date.today() - timedelta(days=100)},
                {"vaccine_key": "mmr", "dose_number": 1, "date_given": date.today() - timedelta(days=90)},
            ],
        )


def test_profile_create_rejects_inconsistent_dose_chronology():
    with pytest.raises(ValidationError):
        ProfileCreateRequest(
            name="Alice",
            dob=date.today() - timedelta(days=365 * 25),
            vaccination_history=[
                {"vaccine_key": "mmr", "dose_number": 1, "date_given": date.today() - timedelta(days=30)},
                {"vaccine_key": "mmr", "dose_number": 2, "date_given": date.today() - timedelta(days=60)},
            ],
        )


def test_profile_create_accepts_valid_multi_dose_chronology():
    profile = ProfileCreateRequest(
        name="Alice",
        dob=date.today() - timedelta(days=365 * 25),
        vaccination_history=[
            {"vaccine_key": "mmr", "dose_number": 1, "date_given": date.today() - timedelta(days=90)},
            {"vaccine_key": "mmr", "dose_number": 2, "date_given": date.today() - timedelta(days=20)},
        ],
    )
    assert len(profile.vaccination_history) == 2
    assert profile.vaccination_history[0].vaccine_key == "mmr"
