"""
Eligibility Engine for Citizen-Scheme-AI (CitizenSchemeAI)
Performs deterministic, rule-based auditing of citizen profiles against government scheme criteria.
Produces transparent, explainable decisions with met, unmet, and conditional criteria.
"""

from typing import List, Tuple
from core.models import CitizenProfile, Scheme, EligibilityResult


class EligibilityEngine:
    """Evaluates citizen profiles against scheme rules deterministically."""

    @classmethod
    def evaluate_scheme(
        cls,
        citizen: CitizenProfile,
        scheme: Scheme,
        lang: str = "en"
    ) -> EligibilityResult:
        """
        Evaluates a citizen's profile against a single scheme.
        Returns a detailed EligibilityResult with scores and audit trails.
        """
        rule = scheme.rules
        met: List[str] = []
        unmet: List[str] = []
        conditional: List[str] = []

        total_rules_checked = 0
        passed_rules = 0

        # 1. Age Check
        total_rules_checked += 1
        if rule.min_age is not None and citizen.age < rule.min_age:
            unmet.append(f"Age {citizen.age} is below minimum required age of {rule.min_age} years.")
        elif rule.max_age is not None and citizen.age > rule.max_age:
            unmet.append(f"Age {citizen.age} exceeds maximum allowable age of {rule.max_age} years.")
        else:
            passed_rules += 1
            if rule.min_age is not None or rule.max_age is not None:
                min_str = f"{rule.min_age}" if rule.min_age is not None else "0"
                max_str = f"{rule.max_age}" if rule.max_age is not None else "any"
                met.append(f"Age ({citizen.age} yrs) satisfies age bracket ({min_str} to {max_str} yrs).")
            else:
                met.append(f"Age ({citizen.age} yrs) has no specific scheme restriction.")

        # 2. Gender Check
        if rule.allowed_genders:
            total_rules_checked += 1
            if citizen.gender.lower() in [g.lower() for g in rule.allowed_genders]:
                passed_rules += 1
                met.append(f"Gender '{citizen.gender}' matches target demographic ({', '.join(rule.allowed_genders)}).")
            elif citizen.gender.lower() == "any":
                conditional.append(f"Scheme is targeted for {', '.join(rule.allowed_genders)}. Gender verification required.")
            else:
                unmet.append(f"Gender '{citizen.gender}' does not match required gender ({', '.join(rule.allowed_genders)}).")
        else:
            met.append("Open to all genders.")

        # 3. State Check
        if rule.allowed_states and "all india" not in [s.lower() for s in rule.allowed_states]:
            total_rules_checked += 1
            if citizen.state.lower() in [s.lower() for s in rule.allowed_states]:
                passed_rules += 1
                met.append(f"State '{citizen.state}' is eligible for this regional scheme.")
            elif citizen.state.lower() == "all india":
                conditional.append(f"Scheme is designated for {', '.join(rule.allowed_states)}. State domicile verification required.")
            else:
                unmet.append(f"State '{citizen.state}' is outside the designated operational states ({', '.join(rule.allowed_states)}).")
        else:
            met.append(f"Applicable across all States & UTs (Pan-India).")

        # 4. Income Ceiling Check
        if rule.max_annual_income is not None:
            total_rules_checked += 1
            if citizen.annual_income <= rule.max_annual_income:
                passed_rules += 1
                met.append(f"Annual income (₹{citizen.annual_income:,.0f}) is within limit (max ₹{rule.max_annual_income:,.0f}).")
            else:
                unmet.append(f"Annual income (₹{citizen.annual_income:,.0f}) exceeds the limit of ₹{rule.max_annual_income:,.0f}.")
        else:
            met.append("No upper income ceiling imposed.")

        # 5. Occupation Check
        if rule.allowed_occupations:
            total_rules_checked += 1
            if citizen.occupation.lower() in [o.lower() for o in rule.allowed_occupations]:
                passed_rules += 1
                met.append(f"Occupation '{citizen.occupation}' is in approved list ({', '.join(rule.allowed_occupations)}).")
            else:
                unmet.append(f"Occupation '{citizen.occupation}' is not among targeted vocations ({', '.join(rule.allowed_occupations)}).")

        # 6. Social Category Check
        if rule.allowed_categories:
            total_rules_checked += 1
            if citizen.category.upper() in [c.upper() for c in rule.allowed_categories]:
                passed_rules += 1
                met.append(f"Category '{citizen.category}' is eligible ({', '.join(rule.allowed_categories)}).")
            else:
                unmet.append(f"Category '{citizen.category}' is not eligible for this targeted scheme ({', '.join(rule.allowed_categories)}).")

        # 7. Student Status
        if rule.requires_student is not None:
            total_rules_checked += 1
            if rule.requires_student == citizen.is_student:
                passed_rules += 1
                if rule.requires_student:
                    met.append("Enrolled student requirement satisfied.")
                else:
                    met.append("Non-student livelihood requirement satisfied.")
            else:
                if rule.requires_student:
                    unmet.append("Scheme exclusively requires active student enrollment.")
                else:
                    unmet.append("Scheme is reserved for non-students / active workforce.")

        # 8. Disability Status Check
        if rule.requires_differently_abled is True:
            total_rules_checked += 1
            if citizen.is_differently_abled:
                passed_rules += 1
                met.append("Person with Disability (PwD) criterion satisfied.")
            else:
                unmet.append("Scheme is specifically earmarked for Differently-Abled (PwD) citizens.")

        # 9. Landholding Checks
        if rule.min_landholding_hectares is not None:
            total_rules_checked += 1
            if citizen.landholding_hectares >= rule.min_landholding_hectares:
                passed_rules += 1
                met.append(f"Landholding ({citizen.landholding_hectares:.2f} ha) meets minimum required ({rule.min_landholding_hectares:.2f} ha).")
            else:
                unmet.append(f"Requires cultivable land ownership (minimum {rule.min_landholding_hectares:.2f} ha; currently {citizen.landholding_hectares:.2f} ha).")

        if rule.max_landholding_hectares is not None:
            total_rules_checked += 1
            if citizen.landholding_hectares <= rule.max_landholding_hectares:
                passed_rules += 1
                met.append(f"Landholding ({citizen.landholding_hectares:.2f} ha) within allowable limit ({rule.max_landholding_hectares:.2f} ha).")
            else:
                unmet.append(f"Landholding ({citizen.landholding_hectares:.2f} ha) exceeds ceiling ({rule.max_landholding_hectares:.2f} ha).")

        # 10. BPL Card Check
        if rule.requires_bpl_card is True:
            total_rules_checked += 1
            if citizen.has_bpl_card:
                passed_rules += 1
                met.append("Holds valid BPL / Ration Card as required.")
            else:
                unmet.append("Requires Below Poverty Line (BPL) or priority ration card.")

        # 11. Compound Women or SC/ST Check (e.g., Stand-Up India)
        if rule.requires_women_or_sc_st is True:
            total_rules_checked += 1
            is_woman = citizen.gender.lower() == "female"
            is_sc_st = citizen.category.upper() in ["SC", "ST"]
            if is_woman or is_sc_st:
                passed_rules += 1
                qualifiers = []
                if is_woman:
                    qualifiers.append("Woman Entrepreneur")
                if is_sc_st:
                    qualifiers.append(f"{citizen.category} Beneficiary")
                met.append(f"Meets priority demographic requirement ({' / '.join(qualifiers)}).")
            else:
                unmet.append("Scheme exclusively supports Women entrepreneurs or SC/ST category borrowers.")

        # Compute Score and Status
        if total_rules_checked == 0:
            confidence = 100.0
            status = "Eligible"
            is_eligible = True
        else:
            confidence = round((passed_rules / total_rules_checked) * 100, 1)

            if len(unmet) == 0 and len(conditional) == 0:
                status = "Eligible"
                is_eligible = True
                confidence = 100.0
            elif len(unmet) == 0 and len(conditional) > 0:
                status = "Potentially Eligible"
                is_eligible = True
                confidence = max(confidence, 80.0)
            elif len(unmet) == 1 and confidence >= 70.0:
                status = "Potentially Eligible"
                is_eligible = False
            else:
                status = "Ineligible"
                is_eligible = False

        # Generate localized explanation
        explanation = cls._generate_explanation(
            scheme_name=scheme.name,
            status=status,
            met=met,
            unmet=unmet,
            conditional=conditional,
            lang=lang
        )

        estimated_benefit = scheme.benefits
        if scheme.financial_benefit_amount > 0:
            estimated_benefit = f"₹{scheme.financial_benefit_amount:,.0f} / year — {scheme.benefits}"

        return EligibilityResult(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            is_eligible=is_eligible,
            status=status,
            confidence_score=confidence,
            met_criteria=met,
            unmet_criteria=unmet,
            conditional_criteria=conditional,
            estimated_benefit=estimated_benefit,
            explanation=explanation,
            required_documents=scheme.required_documents,
            official_portal_url=scheme.official_portal_url
        )

    @classmethod
    def evaluate_all(
        cls,
        citizen: CitizenProfile,
        schemes: List[Scheme],
        lang: str = "en"
    ) -> List[EligibilityResult]:
        """
        Evaluates a citizen against an entire list of schemes,
        sorting by status (Eligible first) and confidence score descending.
        """
        results = [cls.evaluate_scheme(citizen, s, lang=lang) for s in schemes]

        status_order = {"Eligible": 0, "Potentially Eligible": 1, "Ineligible": 2}
        results.sort(key=lambda r: (status_order.get(r.status, 3), -r.confidence_score))
        return results

    @classmethod
    def _generate_explanation(
        cls,
        scheme_name: str,
        status: str,
        met: List[str],
        unmet: List[str],
        conditional: List[str],
        lang: str
    ) -> str:
        """Synthesizes human-friendly explanation in chosen language."""
        if lang == "hi":
            if status == "Eligible":
                base = f"आप **{scheme_name}** के लिए **पूर्णतः पात्र** हैं। आपकी सभी प्रमुख जनसांख्यिकीय शर्तें संतुष्ट हैं।"
            elif status == "Potentially Eligible":
                base = f"आप **{scheme_name}** के लिए **संभावित पात्र** हैं। कुछ दस्तावेजों या शर्तों के अतिरिक्त सत्यापन की आवश्यकता है।"
            else:
                base = f"वर्तमान विवरण के अनुसार आप **{scheme_name}** के लिए पात्र नहीं हैं।"
                if unmet:
                    base += f" मुख्य कारण: {unmet[0]}"
            return base

        elif lang == "mr":
            if status == "Eligible":
                base = f"तुम्ही **{scheme_name}** योजनेसाठी **पूर्ण पात्र** आहात. तुमच्या सर्व प्रमुख अटी पूर्ण झाल्या आहेत."
            elif status == "Potentially Eligible":
                base = f"तुम्ही **{scheme_name}** योजनेसाठी **संभाव्य पात्र** आहात. काही कागदपत्रांची पडताळणी आवश्यक आहे."
            else:
                base = f"सध्याच्या माहितीनुसार तुम्ही **{scheme_name}** योजनेसाठी पात्र नाही."
                if unmet:
                    base += f" मुख्य कारण: {unmet[0]}"
            return base

        else:
            if status == "Eligible":
                base = f"You are **Fully Eligible** for **{scheme_name}**. All primary qualification criteria are fulfilled."
            elif status == "Potentially Eligible":
                base = f"You are **Potentially Eligible** for **{scheme_name}**, pending document or conditional verification."
            else:
                base = f"You do not currently meet the eligibility criteria for **{scheme_name}**."
                if unmet:
                    base += f" Primary roadblock: {unmet[0]}"
            return base
