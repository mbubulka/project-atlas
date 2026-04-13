"""
Healthcare cost model for Project Atlas.

Compares and simulates the annual cost of different healthcare plans:
- Tricare Select / Prime
- VA Health
- Private ACA
- Vision plans (Tricare, VA, Federal, Private)
- Dental plans (Tricare, VA, Federal, Private)
"""

import logging
from typing import Dict, List

from src.data_models import TransitionProfile
from src.model_layer.config import TRICARE_PLANS, get_healthcare_cola_for_city

logger = logging.getLogger(__name__)

# Expected annual healthcare utilization (visits, prescriptions)
# These are baseline estimates; real users will vary
ANNUAL_UTILIZATION = {
    "primary_care_visits": 2,
    "specialist_visits": 1,
    "generic_drugs": 6,  # Number of prescriptions
    "emergency_visits": 0.2,
    "hospital_admissions": 0.05,
}


def calculate_healthcare_benefits(profile: TransitionProfile, plan_name: str) -> Dict[str, float]:
    """
    Calculate healthcare costs for a specific plan (test compatibility wrapper).

    Args:
        profile: User's profile
        plan_name: Healthcare plan choice ('tricare_select', 'tricare_prime', 'va_health', 'aca')

    Returns:
        Dict with annual_cost, enrollment_fee, copay_cost, etc.
    """
    if plan_name == "tricare_select":
        annual_cost = _calculate_tricare_cost(profile, "tricare_select")
    elif plan_name == "tricare_prime":
        annual_cost = _calculate_tricare_cost(profile, "tricare_prime")
    elif plan_name == "va_health":
        annual_cost = _calculate_va_health_cost(profile)
    elif plan_name == "aca":
        annual_cost = _calculate_aca_cost(profile)
    else:
        annual_cost = _calculate_tricare_cost(profile, "tricare_select")

    return {
        "annual_cost": annual_cost,
        "enrollment_fee": 0,  # Simplified for tests
        "copay_cost": 0,
    }


def compare_healthcare_costs(profile: TransitionProfile) -> TransitionProfile:
    """
    Simulate and compare annual healthcare costs across different plans.

    Analyzes:
    1. Tricare Select
    2. Tricare Prime
    3. VA Health (if applicable by rating)
    4. Private ACA (if applicable)

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        TransitionProfile: Updated profile with:
            - annual_healthcare_cost
            - monthly_healthcare_cost
            - healthcare cost comparison in metadata
    """

    # Calculate costs for each plan
    costs = {}

    # Tricare plans (always available to retirees)
    costs["tricare_select"] = _calculate_tricare_cost(profile, "tricare_select")
    costs["tricare_prime"] = _calculate_tricare_cost(profile, "tricare_prime")

    # VA Health (available based on disability rating)
    if profile.current_va_disability_rating >= 10:
        costs["va_health"] = _calculate_va_health_cost(profile)

    # Private ACA (available to all)
    costs["aca"] = _calculate_aca_cost(profile)

    logger.info("Healthcare cost comparison:")
    for plan, cost in sorted(costs.items(), key=lambda x: x[1]):
        logger.info(f"  {plan}: ${cost:,.2f}/year")

    # Determine best choice (default to user's choice or cheapest)
    selected_plan = profile.healthcare_plan_choice or "tricare_select"

    annual_cost = costs.get(selected_plan, costs.get("tricare_select", 0.0))
    monthly_cost = annual_cost / 12.0

    profile.annual_healthcare_cost = annual_cost
    profile.monthly_healthcare_cost = monthly_cost

    # Store all options for UI display
    profile.metadata["healthcare_cost_comparison"] = costs
    profile.metadata["selected_healthcare_plan"] = selected_plan

    logger.info(
        f"Selected plan: {selected_plan}\n" f"Annual cost: ${annual_cost:,.2f}\n" f"Monthly cost: ${monthly_cost:,.2f}"
    )

    return profile


def _calculate_tricare_cost(profile: TransitionProfile, plan_name: str, family_size: int = 1) -> float:
    """
    Calculate annual out-of-pocket cost for a Tricare plan.

    Args:
        profile (TransitionProfile): User's profile.
        plan_name (str): One of 'tricare_select', 'tricare_prime', etc.
        family_size (int): Number of family members (1 = individual, 2+ = family).

    Returns:
        float: Annual out-of-pocket cost.
    """

    plan = TRICARE_PLANS.get(plan_name)
    if not plan:
        return 0.0

    # Apply family vs individual enrollment fee multiplier
    enrollment_fee = plan.annual_enrollment_fee
    if family_size > 1:
        # Family rates are capped (not per-person multiplier)
        # Group A: Individual $372 -> Family $744 (2x)
        # Group A: Individual $181.92 -> Family $364.92 (2x)
        enrollment_fee *= 2

    # Start with enrollment fee
    cost = enrollment_fee

    # Simulate utilization and copays
    util = ANNUAL_UTILIZATION

    # Primary care copays
    cost += util["primary_care_visits"] * plan.primary_care_copay

    # Specialist copays
    cost += util["specialist_visits"] * plan.specialist_copay

    # Pharmacy copays
    cost += util["generic_drugs"] * plan.generic_drug_copay

    # Emergency/hospital (simplified)
    cost += util["emergency_visits"] * 150  # Estimate copay
    cost += util["hospital_admissions"] * plan.inpatient_copay

    # Apply COLA adjustment
    cola = get_healthcare_cola_for_city(profile.target_city)
    cost *= cola

    return cost


def _calculate_tricare_cost_breakdown(
    profile: TransitionProfile, plan_name: str, family_size: int = 1
) -> Dict[str, float]:
    """
    Calculate Tricare cost breakdown: enrollment fee vs copays.

    Args:
        profile (TransitionProfile): User's profile.
        plan_name (str): One of 'tricare_select', 'tricare_prime', etc.
        family_size (int): Number of family members (1 = individual, 2+ = family).

    Returns:
        Dict: Contains 'enrollment', 'copays', 'total' (before and after COLA).
    """

    plan = TRICARE_PLANS.get(plan_name)
    if not plan:
        return {"enrollment": 0, "copays": 0, "total": 0, "total_with_cola": 0}

    # Enrollment fee
    enrollment_fee = plan.annual_enrollment_fee
    if family_size > 1:
        enrollment_fee *= 2

    # Calculate copays
    util = ANNUAL_UTILIZATION
    copay_cost = 0
    copay_cost += util["primary_care_visits"] * plan.primary_care_copay
    copay_cost += util["specialist_visits"] * plan.specialist_copay
    copay_cost += util["generic_drugs"] * plan.generic_drug_copay
    copay_cost += util["emergency_visits"] * 150
    copay_cost += util["hospital_admissions"] * plan.inpatient_copay

    # Apply COLA to total
    cola = get_healthcare_cola_for_city(profile.target_city)
    total_before_cola = enrollment_fee + copay_cost
    total_with_cola = total_before_cola * cola

    return {
        "enrollment": enrollment_fee,
        "copays": copay_cost,
        "total": total_before_cola,
        "total_with_cola": total_with_cola,
        "cola_factor": cola,
    }


def _calculate_va_health_cost(profile: TransitionProfile) -> float:
    """
    Estimate VA Health cost (typically low/free for eligible veterans).

    VA provides free healthcare to rated veterans, but may charge copays.

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        float: Annual estimated cost.
    """

    # VA health is heavily subsidized; most veterans pay little to nothing
    # This is a simplified estimate

    rating = profile.current_va_disability_rating

    if rating >= 50:
        # 50%+ rated: Free VA care
        return 50.0  # Minimal copays
    elif rating >= 10:
        # 10-40% rated: Low copays
        return 200.0
    else:
        # Not rated through VA: Higher copays
        return 500.0


def _calculate_aca_cost(profile: TransitionProfile) -> float:
    """
    Estimate annual cost of private ACA insurance.

    Simplified: Uses average marketplace premium and deductible.
    Real calculation would consider age, location, income, subsidies.

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        float: Annual out-of-pocket cost (premium + deductible + utilization).
    """

    # Average ACA premium (age 50, 2024)
    annual_premium = 8000

    # Average deductible (Silver plan)
    annual_deductible = 2500

    # Estimate utilization costs
    copay_cost = 500

    # Apply COLA
    cola = get_healthcare_cola_for_city(profile.target_city)

    total = (annual_premium + annual_deductible + copay_cost) * cola

    return total


def estimate_healthcare_cost_scenarios(profile: TransitionProfile, healthy: bool = True) -> Dict[str, float]:
    """
    Estimate healthcare costs under different utilization scenarios.

    Args:
        profile (TransitionProfile): User's profile.
        healthy (bool): If True, assume lower utilization. If False, higher.

    Returns:
        Dict: Contains 'low', 'mid', 'high' cost scenarios.
    """

    base_cost = profile.annual_healthcare_cost

    # Create variance around base estimate
    if healthy:
        # Optimistic: 30% reduction
        low = base_cost * 0.7
        mid = base_cost
        high = base_cost * 1.2
    else:
        # Pessimistic: higher utilization
        low = base_cost
        mid = base_cost * 1.3
        high = base_cost * 1.8

    return {
        "low": low,
        "mid": mid,
        "high": high,
    }


def get_healthcare_recommendations(profile: TransitionProfile) -> List[str]:
    """
    Generate personalized healthcare recommendations.

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        List[str]: List of recommendations.
    """

    recommendations = []

    # Check VA eligibility
    if profile.current_va_disability_rating >= 50:
        recommendations.append("You qualify for free VA healthcare. Strongly consider enrolling.")
    elif profile.current_va_disability_rating >= 10:
        recommendations.append("You qualify for VA healthcare with low copays. Explore this option.")

    # Check cost comparison
    try:
        comparison = profile.metadata.get("healthcare_cost_comparison", {})
        if comparison:
            cheapest = min(comparison.items(), key=lambda x: x[1])
            if cheapest[0] != profile.healthcare_plan_choice:
                savings = comparison.get(profile.healthcare_plan_choice, 0) - cheapest[1]
                recommendations.append(f"Switching to {cheapest[0]} could save ${savings:,.0f}/year.")
    except Exception:
        pass

    # Check for high healthcare costs
    if profile.annual_healthcare_cost > profile.monthly_take_home_pay * 0.25:
        recommendations.append("Healthcare costs are high relative to income. " "Review coverage options carefully.")

    return recommendations


# ============ VISION PLANS ============

VISION_PLANS = {
    "tricare_vision": {
        "name": "Tricare Vision",
        "annual_fee": 150,
        "exam_copay": 0,
        "glasses_copay": 150,
        "contacts_copay": 0,
        "frequency": "Every 2 years",
    },
    "va_vision": {
        "name": "VA Vision",
        "annual_fee": 0,
        "exam_copay": 0,
        "glasses_copay": 0,
        "contacts_copay": 50,
        "frequency": "Every 2 years",
        "rating_required": 10,
    },
    "federal_vision": {
        "name": "Federal Vision Plan (FEDVIP)",
        "annual_fee": 120,
        "exam_copay": 10,
        "glasses_copay": 120,
        "contacts_copay": 150,
        "frequency": "Every 2 years",
    },
    "private_vision": {
        "name": "Private Vision Insurance",
        "annual_fee": 180,
        "exam_copay": 25,
        "glasses_copay": 150,
        "contacts_copay": 175,
        "frequency": "Every 2 years",
    },
}


def calculate_vision_costs(profile: TransitionProfile, plan: str) -> float:
    """
    Calculate annual vision care cost.

    Args:
        profile (TransitionProfile): User's profile.
        plan (str): Vision plan type.

    Returns:
        float: Annual cost.
    """

    plan_info = VISION_PLANS.get(plan, {})
    if not plan_info:
        return 0.0

    # Check eligibility
    if plan == "va_vision" and profile.current_va_disability_rating < 10:
        # Not eligible - use private instead
        return calculate_vision_costs(profile, "private_vision")

    # Exam every 2 years (annual cost = every other year)
    annual_cost = plan_info["annual_fee"] + (plan_info["exam_copay"] * 0.5)

    # Glasses every 2-3 years
    annual_cost += plan_info["glasses_copay"] * 0.33

    return annual_cost


# ============ DENTAL PLANS ============

DENTAL_PLANS = {
    "tricare_dental": {
        "name": "Tricare Dental Program",
        "monthly_fee": 12.50,
        "preventive_coverage": 100,  # %
        "basic_coverage": 80,
        "major_coverage": 50,
        "annual_max": 1200,
    },
    "va_dental": {
        "name": "VA Dental Care",
        "monthly_fee": 0,
        "preventive_coverage": 100,
        "basic_coverage": 50,
        "major_coverage": 25,
        "annual_max": 1500,
        "rating_required": 10,
    },
    "federal_dental": {
        "name": "Federal Dental Program (FEDVIP)",
        "monthly_fee": 25,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "annual_max": 1500,
    },
    "private_dental": {
        "name": "Private Dental Insurance",
        "monthly_fee": 20,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "annual_max": 1200,
    },
}


def calculate_dental_costs(profile: TransitionProfile, plan: str, family_size: int = 1) -> float:
    """
    Calculate annual dental care cost.

    Args:
        profile (TransitionProfile): User's profile.
        plan (str): Dental plan type.
        family_size (int): Number of family members covered.

    Returns:
        float: Annual cost.
    """

    plan_info = DENTAL_PLANS.get(plan, {})
    if not plan_info:
        return 0.0

    # Check eligibility
    if plan == "va_dental" and profile.current_va_disability_rating < 10:
        # Not eligible - use private instead
        return calculate_dental_costs(profile, "private_dental", family_size)

    # Monthly premium (annualized)
    annual_cost = plan_info["monthly_fee"] * 12 * family_size

    # Estimate typical annual dental use
    # Preventive: 2 cleanings/exams (covered 100%)
    preventive_cost = 400 * (family_size * 0.5)  # Half covered by preventive

    # Basic: 1 filling per person every 5 years + emergency
    basic_cost = 150 * (family_size * 0.2)
    basic_coverage = plan_info["basic_coverage"] / 100
    basic_oop = basic_cost * (1 - basic_coverage)

    annual_cost += preventive_cost + basic_oop

    # Cap at annual max (insurance benefit limit)
    annual_cost = min(annual_cost, plan_info["annual_max"] * family_size)

    return annual_cost


def get_comprehensive_healthcare_costs(
    profile: TransitionProfile,
    medical_plan: str,
    vision_plan: str,
    dental_plan: str,
    family_size: int = 1,
) -> Dict[str, float]:
    """
    Get total healthcare costs including medical, vision, and dental.

    Args:
        profile (TransitionProfile): User's profile.
        medical_plan (str): Medical plan type.
        vision_plan (str): Vision plan type.
        dental_plan (str): Dental plan type.
        family_size (int): Number of family members.

    Returns:
        Dict: Contains breakdown of costs.
    """

    # Medical cost (varies with family size for Tricare plans)
    if medical_plan == "tricare_select":
        medical_cost = _calculate_tricare_cost(profile, "tricare_select", family_size)
    elif medical_plan == "tricare_prime":
        medical_cost = _calculate_tricare_cost(profile, "tricare_prime", family_size)
    else:
        medical_cost = _calculate_aca_cost(profile)

    # Vision cost
    vision_cost = calculate_vision_costs(profile, vision_plan)

    # Dental cost
    dental_cost = calculate_dental_costs(profile, dental_plan, family_size)

    total_annual = medical_cost + vision_cost + dental_cost
    total_monthly = total_annual / 12

    return {
        "medical_annual": medical_cost,
        "vision_annual": vision_cost,
        "dental_annual": dental_cost,
        "total_annual": total_annual,
        "total_monthly": total_monthly,
        "medical_monthly": medical_cost / 12,
        "vision_monthly": vision_cost / 12,
        "dental_monthly": dental_cost / 12,
    }


def get_mixed_healthcare_costs(
    profile: TransitionProfile,
    member_medical_plan: str,
    dependent_medical_plan: str,
    member_vision_plan: str,
    dependent_vision_plan: str,
    member_dental_plan: str,
    dependent_dental_plan: str,
    family_size: int = 1,
) -> Dict[str, float]:
    """
    Calculate healthcare costs when member and dependents are on different plans.

    KEY CONCEPT: Tricare family plans are a single set price covering everyone.
    If member uses VA + dependents use Tricare = VA member cost + Tricare family plan cost (flat).

    This handles scenarios like:
    - Member on VA + Dependents on Tricare Select = $0 (VA) + $364.92 (Tricare family)
    - Member on Tricare Prime + Dependents on Tricare Prime = $744 (Tricare Prime family)
    - Single person on any plan

    Args:
        profile (TransitionProfile): User's profile.
        member_medical_plan (str): Service member's medical plan.
        dependent_medical_plan (str): Dependents' medical plan.
        member_vision_plan (str): Service member's vision plan.
        dependent_vision_plan (str): Dependents' vision plan.
        member_dental_plan (str): Service member's dental plan.
        dependent_dental_plan (str): Dependents' dental plan.
        family_size (int): Total family size (1 = single, 2+ = family with dependents).

    Returns:
        Dict: Contains breakdown of costs for member and dependents.
    """

    if family_size == 1:
        # Single person - use only member plans
        return get_comprehensive_healthcare_costs(
            profile=profile,
            medical_plan=member_medical_plan,
            vision_plan=member_vision_plan,
            dental_plan=member_dental_plan,
            family_size=1,
        )

    # Family scenario - Tricare family plans are flat prices regardless of family size
    # Key: Tricare family rate = SINGLE price covers 1 spouse/dependent OR 5+ dependents

    # === MEDICAL COST ===
    if member_medical_plan == dependent_medical_plan:
        # Both on same plan - use that plan with family size
        if member_medical_plan in ["tricare_select", "tricare_prime"]:
            # Tricare family plan: use family_size=2 to get family rate (covers everyone)
            medical_cost = _calculate_tricare_cost(profile, member_medical_plan, family_size=2)
        else:
            # ACA or VA: calculate for all
            medical_cost = (
                _calculate_tricare_cost(profile, member_medical_plan, family_size=family_size)
                if member_medical_plan == "va_healthcare"
                else _calculate_aca_cost(profile) * family_size
            )
    else:
        # Different plans for member and dependents
        if member_medical_plan == "va_healthcare":
            member_medical_cost = 0  # VA is free for service-connected
        elif member_medical_plan in ["tricare_select", "tricare_prime"]:
            member_medical_cost = _calculate_tricare_cost(
                profile, member_medical_plan, family_size=1
            )  # Individual rate
        else:
            member_medical_cost = _calculate_aca_cost(profile)

        if dependent_medical_plan in ["tricare_select", "tricare_prime"]:
            # Tricare family rate: flat price for all dependents regardless of count
            dep_medical_cost = _calculate_tricare_cost(profile, dependent_medical_plan, family_size=2)
        else:
            dep_medical_cost = _calculate_aca_cost(profile) * (family_size - 1)  # Per-dependent

        medical_cost = member_medical_cost + dep_medical_cost

    # === VISION COST ===
    if member_vision_plan == dependent_vision_plan:
        # Both on same vision plan
        if member_vision_plan == "tricare_vision":
            # Tricare vision family plan covers everyone
            vision_cost = calculate_vision_costs(profile, "tricare_vision")  # Family plan cost
        else:
            vision_cost = calculate_vision_costs(profile, member_vision_plan) * family_size
    else:
        # Different vision plans
        member_vision_cost = calculate_vision_costs(profile, member_vision_plan)
        dep_vision_cost = calculate_vision_costs(profile, dependent_vision_plan)
        vision_cost = member_vision_cost + dep_vision_cost

    # === DENTAL COST ===
    if member_dental_plan == dependent_dental_plan:
        # Both on same dental plan
        if member_dental_plan == "tricare_dental":
            # Tricare dental family plan covers everyone
            dental_cost = calculate_dental_costs(profile, "tricare_dental", family_size=2)  # Family plan
        else:
            dental_cost = calculate_dental_costs(profile, member_dental_plan, family_size=family_size)
    else:
        # Different dental plans
        member_dental_cost = calculate_dental_costs(profile, member_dental_plan, family_size=1)
        dep_dental_cost = calculate_dental_costs(profile, dependent_dental_plan, family_size=family_size - 1)
        dental_cost = member_dental_cost + dep_dental_cost

    # Totals
    total_annual = medical_cost + vision_cost + dental_cost

    total_annual = medical_cost + vision_cost + dental_cost
    total_monthly = total_annual / 12

    return {
        "medical_annual": medical_cost,
        "vision_annual": vision_cost,
        "dental_annual": dental_cost,
        "total_annual": total_annual,
        "total_monthly": total_monthly,
        "medical_monthly": medical_cost / 12,
        "vision_monthly": vision_cost / 12,
        "dental_monthly": dental_cost / 12,
    }
