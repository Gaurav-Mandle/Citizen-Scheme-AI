"""Tests for core data models."""

import pytest
from pydantic import ValidationError
from core.models import CitizenProfile, Scheme, SchemeRule, EligibilityResult


def test_valid_citizen_profile():
    profile = CitizenProfile(
        age=32,
        gender="Female",
        state="Maharashtra",
        annual_income=250000.0,
        occupation="Farmer",
        category="OBC",
        is_student=False,
        is_differently_abled=False,
        landholding_hectares=1.5,
        has_bpl_card=True
    )
    assert profile.age == 32
    assert profile.occupation == "Farmer"
    assert profile.has_bpl_card is True


def test_invalid_citizen_age():
    with pytest.raises(ValidationError):
        CitizenProfile(age=-5)  # Negative age should fail

    with pytest.raises(ValidationError):
        CitizenProfile(age=150)  # Beyond limit


def test_invalid_citizen_income():
    with pytest.raises(ValidationError):
        CitizenProfile(age=25, annual_income=-1000.0)


def test_scheme_model_creation():
    scheme = Scheme(
        id="test-scheme",
        name="Test Welfare Scheme",
        ministry="Ministry of Testing",
        level="Central",
        category="Agriculture",
        description="A test scheme description",
        benefits="Direct financial assistance",
        financial_benefit_amount=5000.0,
        rules=SchemeRule(min_age=18, max_age=60),
        required_documents=["Aadhaar Card"],
        application_process=["Visit portal"],
        official_portal_url="https://example.gov.in"
    )
    assert scheme.id == "test-scheme"
    assert scheme.rules.min_age == 18
    assert len(scheme.required_documents) == 1
