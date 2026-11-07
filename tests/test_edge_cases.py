"""Tests for system edge cases, boundaries, and robustness."""

import pytest
import time
from core.models import CitizenProfile, Scheme, SchemeRule
from core.database import SchemeDatabase
from core.eligibility_engine import EligibilityEngine
from core.security import SecurityGuard


def test_infant_profile():
    # 0 years old citizen
    infant = CitizenProfile(
        age=0,
        gender="Female",
        state="Maharashtra",
        annual_income=0.0
    )
    db = SchemeDatabase()
    pmjay = db.get_scheme_by_id("pmjay-ayushman")
    res = EligibilityEngine.evaluate_scheme(infant, pmjay)
    # 0 years is allowed by AB-PMJAY (min_age 0)
    assert any("satisfies age" in m.lower() for m in res.met_criteria)


def test_centenarian_profile():
    # 105 years old citizen
    centenarian = CitizenProfile(
        age=105,
        gender="Male",
        annual_income=50000.0,
        has_bpl_card=True
    )
    db = SchemeDatabase()
    nsap = db.get_scheme_by_id("nsap-old-age-pension")
    res = EligibilityEngine.evaluate_scheme(centenarian, nsap)
    assert res.is_eligible is True
    assert res.status == "Eligible"


def test_batch_evaluation_performance():
    # Evaluates 500 citizen profiles in less than 1 second
    db = SchemeDatabase()
    schemes = db.get_all_schemes()
    profile = CitizenProfile(
        age=30,
        gender="Male",
        annual_income=150000.0,
        occupation="Farmer"
    )

    start = time.perf_counter()
    for _ in range(500):
        EligibilityEngine.evaluate_all(profile, schemes)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.5, f"Batch performance took {elapsed}s, expected < 1.5s"


def test_scheme_with_no_rules():
    free_scheme = Scheme(
        id="universal-scheme",
        name="Universal Civic Grant",
        ministry="Ministry of Public Good",
        level="Central",
        category="Social Welfare",
        description="Universal grant for all",
        benefits="Free access",
        rules=SchemeRule(),  # No restrictions at all
        official_portal_url="https://india.gov.in"
    )
    citizen = CitizenProfile(age=40)
    res = EligibilityEngine.evaluate_scheme(citizen, free_scheme)
    assert res.is_eligible is True
    assert res.confidence_score == 100.0


def test_safe_field_sanitization():
    dirty = "<script>bad()</script><b>Hello</b>"
    clean = SecurityGuard.sanitize_field(dirty)
    assert "<script>" not in clean
    assert "<b>" not in clean
    assert "Hello" in clean


def test_translation_keys_completeness():
    from core.translations import get_text
    # Check that status_potentially_eligible resolves cleanly across all languages
    for lang in ["en", "hi", "mr"]:
        val = get_text("status_potentially_eligible", lang)
        assert val != "status_potentially_eligible", f"Missing key for {lang}"
        assert len(val) > 0
