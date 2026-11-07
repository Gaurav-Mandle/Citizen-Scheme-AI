"""Tests for deterministic eligibility engine."""

import pytest
from core.models import CitizenProfile
from core.database import SchemeDatabase
from core.eligibility_engine import EligibilityEngine


@pytest.fixture
def db():
    return SchemeDatabase()


def test_farmer_eligible_for_pm_kisan(db):
    farmer = CitizenProfile(
        age=35,
        gender="Male",
        state="Maharashtra",
        annual_income=120000.0,
        occupation="Farmer",
        category="General",
        is_student=False,
        landholding_hectares=2.0,
        has_bpl_card=False
    )
    pm_kisan = db.get_scheme_by_id("pm-kisan")
    result = EligibilityEngine.evaluate_scheme(farmer, pm_kisan)

    assert result.is_eligible is True
    assert result.status == "Eligible"
    assert result.confidence_score == 100.0
    assert len(result.met_criteria) > 0
    assert len(result.unmet_criteria) == 0


def test_student_eligible_for_scholarship(db):
    student = CitizenProfile(
        age=20,
        gender="Female",
        state="Karnataka",
        annual_income=150000.0,
        occupation="Student",
        category="OBC",
        is_student=True,
        has_bpl_card=False
    )
    scholarship = db.get_scheme_by_id("post-matric-scholarship")
    result = EligibilityEngine.evaluate_scheme(student, scholarship)

    assert result.is_eligible is True
    assert result.status == "Eligible"
    assert any("student" in m.lower() for m in result.met_criteria)


def test_non_student_ineligible_for_scholarship(db):
    worker = CitizenProfile(
        age=28,
        gender="Male",
        annual_income=200000.0,
        occupation="Daily Wage Worker",
        is_student=False
    )
    scholarship = db.get_scheme_by_id("post-matric-scholarship")
    result = EligibilityEngine.evaluate_scheme(worker, scholarship)

    assert result.is_eligible is False
    assert result.status == "Ineligible"
    assert any("student" in u.lower() for u in result.unmet_criteria)


def test_high_income_ineligible_for_pmjay(db):
    rich_citizen = CitizenProfile(
        age=45,
        annual_income=1200000.0,  # 12 Lakhs
        has_bpl_card=False
    )
    pmjay = db.get_scheme_by_id("pmjay-ayushman")
    result = EligibilityEngine.evaluate_scheme(rich_citizen, pmjay)

    assert result.is_eligible is False
    assert any("income" in u.lower() for u in result.unmet_criteria)
    assert any("bpl" in u.lower() for u in result.unmet_criteria)


def test_age_boundary_for_sukanya(db):
    teen_girl = CitizenProfile(
        age=16,  # Sukanya requires max age 10
        gender="Female",
        occupation="Student"
    )
    ssy = db.get_scheme_by_id("sukanya-samriddhi")
    result = EligibilityEngine.evaluate_scheme(teen_girl, ssy)

    assert result.is_eligible is False
    assert any("age" in u.lower() for u in result.unmet_criteria)


def test_evaluate_all_sorting(db):
    farmer = CitizenProfile(
        age=30,
        occupation="Farmer",
        annual_income=100000.0,
        has_bpl_card=True
    )
    all_schemes = db.get_all_schemes()
    results = EligibilityEngine.evaluate_all(farmer, all_schemes)

    # First result should be Eligible or have highest score
    assert len(results) == len(all_schemes)
    assert results[0].confidence_score >= results[-1].confidence_score


def test_landless_ineligible_for_pm_kisan(db):
    """Citizens with zero landholding must not qualify for PM-KISAN."""
    landless = CitizenProfile(
        age=30,
        gender="Male",
        occupation="Daily Wage Worker",
        landholding_hectares=0.0
    )
    pm_kisan = db.get_scheme_by_id("pm-kisan")
    result = EligibilityEngine.evaluate_scheme(landless, pm_kisan)

    assert result.is_eligible is False
    assert any("land" in u.lower() for u in result.unmet_criteria)


def test_stand_up_india_compound_criteria(db):
    """General category male must be ineligible for Stand-Up India."""
    general_male = CitizenProfile(
        age=32,
        gender="Male",
        category="General",
        occupation="Self-Employed"
    )
    scheme = db.get_scheme_by_id("stand-up-india")
    result = EligibilityEngine.evaluate_scheme(general_male, scheme)

    assert result.is_eligible is False
    assert any("women" in u.lower() or "sc/st" in u.lower() for u in result.unmet_criteria)

    # But female General entrepreneur MUST qualify
    female_general = CitizenProfile(
        age=32,
        gender="Female",
        category="General",
        occupation="Self-Employed"
    )
    result_f = EligibilityEngine.evaluate_scheme(female_general, scheme)
    assert result_f.is_eligible is True

    # And SC male entrepreneur MUST qualify
    sc_male = CitizenProfile(
        age=32,
        gender="Male",
        category="SC",
        occupation="Self-Employed"
    )
    result_sc = EligibilityEngine.evaluate_scheme(sc_male, scheme)
    assert result_sc.is_eligible is True


def test_regional_scheme_conditional_for_unspecified_state(db):
    """Regional state-restricted scheme must yield conditional status if state is 'All India'."""
    from core.models import Scheme, SchemeRule
    regional_scheme = Scheme(
        id="test-state-scheme",
        name="Maharashtra Krishi Subsidy",
        ministry="Govt of Maharashtra",
        category="Agriculture",
        description="State specific scheme",
        benefits="State subsidy",
        rules=SchemeRule(allowed_states=["Maharashtra"]),
        official_portal_url="https://mahadbt.maharashtra.gov.in"
    )

    unspecified_citizen = CitizenProfile(age=30, state="All India")
    result = EligibilityEngine.evaluate_scheme(unspecified_citizen, regional_scheme)
    assert any("restricted" in c.lower() or "domicile" in c.lower() for c in result.conditional_criteria)
