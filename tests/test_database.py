"""Tests for scheme database and repository operations."""

import pytest
from core.database import SchemeDatabase


def test_database_loads_schemes():
    db = SchemeDatabase()
    schemes = db.get_all_schemes()
    assert len(schemes) >= 10
    assert any(s.id == "pm-kisan" for s in schemes)
    assert any(s.id == "pmjay-ayushman" for s in schemes)


def test_database_filtering_by_category():
    db = SchemeDatabase()
    agri_schemes = db.filter_schemes(category="Agriculture")
    assert len(agri_schemes) >= 1
    for s in agri_schemes:
        assert s.category.lower() == "agriculture"


def test_database_search():
    db = SchemeDatabase()
    results = db.filter_schemes(search_term="hospital")
    assert len(results) >= 1
    assert any("pmjay" in s.id for s in results)


def test_get_scheme_by_id():
    db = SchemeDatabase()
    scheme = db.get_scheme_by_id("pm-kisan")
    assert scheme is not None
    assert "PM-KISAN" in scheme.name
    assert db.get_scheme_by_id("non-existent-xyz") is None


def test_database_atomic_scheme_addition(tmp_path):
    """Test that adding a scheme writes atomically and sanitizes unsafe portal URLs."""
    import json
    test_file = tmp_path / "schemes.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump([], f)

    db = SchemeDatabase(data_path=str(test_file))
    new_scheme_dict = {
        "id": "state-kisan-bonus",
        "name": "State Kisan Bonus Scheme",
        "native_names": {"hi": "राज्य किसान बोनस योजना"},
        "ministry": "Agriculture Dept",
        "level": "State",
        "category": "Agriculture",
        "description": "Additional bonus for paddy growers",
        "benefits": "₹2,500 per acre bonus",
        "financial_benefit_amount": 5000.0,
        "rules": {
            "min_age": 18,
            "max_age": 90,
            "allowed_genders": [],
            "allowed_states": ["Chhattisgarh"],
            "max_annual_income": None,
            "allowed_occupations": ["Farmer"],
            "allowed_categories": [],
            "requires_student": False,
            "requires_differently_abled": None,
            "max_landholding_hectares": None,
            "requires_bpl_card": None,
            "target_beneficiaries": "Paddy farmers"
        },
        "required_documents": ["Kisan Credit Card", "Land Record / Khasra"],
        "application_process": ["Register on state portal"],
        "official_portal_url": "javascript:alert('xss')",  # Malicious URL must be sanitized
        "helpline": "1800-000-000",
        "faqs": [],
        "tags": ["agriculture", "bonus"]
    }

    ok, msg = db.add_scheme(new_scheme_dict)
    assert ok is True
    assert "Successfully registered" in msg

    # Re-read from disk to ensure persistence and URL sanitization
    saved_scheme = db.get_scheme_by_id("state-kisan-bonus")
    assert saved_scheme is not None
    assert saved_scheme.official_portal_url == "https://india.gov.in"
