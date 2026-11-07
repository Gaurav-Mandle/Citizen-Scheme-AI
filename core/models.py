"""
Data models for Citizen-Scheme-AI (CitizenSchemeAI)
Defines schemes, citizen profiles, eligibility criteria, and assessment results.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class CitizenProfile(BaseModel):
    """Represents an individual citizen seeking scheme benefits."""
    age: int = Field(ge=0, le=125, description="Age in years")
    gender: str = Field(default="Any", description="Gender: Male, Female, Transgender, Other, Any")
    state: str = Field(default="All India", description="State or Union Territory of residence")
    annual_income: float = Field(default=0.0, ge=0.0, description="Annual household income in INR")
    occupation: str = Field(default="Other", description="Primary occupation or occupational status")
    category: str = Field(default="General", description="Social category: General, OBC, SC, ST, EWS")
    is_student: bool = Field(default=False, description="Whether currently enrolled as a student")
    is_differently_abled: bool = Field(default=False, description="Person with disability (PwD) status")
    landholding_hectares: float = Field(default=0.0, ge=0.0, description="Agricultural land ownership in hectares")
    marital_status: str = Field(default="Single", description="Single, Married, Widowed, Divorced")
    has_bpl_card: bool = Field(default=False, description="Holds Below Poverty Line (BPL) / Ration card")


class SchemeRule(BaseModel):
    """Rules and constraints that dictate eligibility for a specific scheme."""
    min_age: Optional[int] = Field(default=None, description="Minimum age requirement")
    max_age: Optional[int] = Field(default=None, description="Maximum age requirement")
    allowed_genders: List[str] = Field(default_factory=list, description="Allowed genders; empty means all")
    allowed_states: List[str] = Field(default_factory=list, description="Eligible states; empty means All India")
    max_annual_income: Optional[float] = Field(default=None, description="Upper ceiling for annual income in INR")
    allowed_occupations: List[str] = Field(default_factory=list, description="Target occupations; empty means all")
    allowed_categories: List[str] = Field(default_factory=list, description="Target categories; empty means all")
    requires_student: Optional[bool] = Field(default=None, description="Must be a student if True")
    requires_differently_abled: Optional[bool] = Field(default=None, description="Must be differently-abled if True")
    min_landholding_hectares: Optional[float] = Field(default=None, description="Minimum agricultural land required")
    max_landholding_hectares: Optional[float] = Field(default=None, description="Max agricultural land allowed")
    requires_bpl_card: Optional[bool] = Field(default=None, description="Must possess BPL card if True")
    requires_women_or_sc_st: Optional[bool] = Field(default=None, description="Must be Woman or SC/ST (e.g. Stand-Up India)")
    target_beneficiaries: str = Field(default="", description="Summary of target demographic group")


class SchemeFAQ(BaseModel):
    """Frequently asked question and official answer for a scheme."""
    question: str
    answer: str


class Scheme(BaseModel):
    """Comprehensive representation of a government welfare scheme."""
    id: str
    name: str
    native_names: Dict[str, str] = Field(default_factory=dict, description="Translations in Hindi, Marathi, etc.")
    ministry: str
    level: str = Field(default="Central", description="Central or State level")
    category: str = Field(description="Agriculture, Healthcare, Education, Social Welfare, Housing, etc.")
    description: str
    benefits: str
    financial_benefit_amount: float = Field(default=0.0, description="Approximate annual direct benefit in INR")
    rules: SchemeRule
    required_documents: List[str] = Field(default_factory=list)
    application_process: List[str] = Field(default_factory=list)
    official_portal_url: str
    helpline: str = Field(default="")
    faqs: List[SchemeFAQ] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class EligibilityResult(BaseModel):
    """Structured assessment result produced by the eligibility engine."""
    scheme_id: str
    scheme_name: str
    is_eligible: bool
    status: str = Field(description="Eligible, Potentially Eligible, or Ineligible")
    confidence_score: float = Field(ge=0.0, le=100.0, description="Match score in percentage")
    met_criteria: List[str] = Field(default_factory=list)
    unmet_criteria: List[str] = Field(default_factory=list)
    conditional_criteria: List[str] = Field(default_factory=list)
    estimated_benefit: str
    explanation: str
    required_documents: List[str] = Field(default_factory=list)
    official_portal_url: str = Field(default="")
