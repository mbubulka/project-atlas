"""
Session state management for wizard flow.

Bridges st.session_state (UI input layer) ↔ TransitionProfile (calculation layer)
Everything stays in RAM. Privacy-first: nothing persists without explicit user action.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from src.data_models import TransitionProfile


def initialize_wizard_session():
    """Initialize session state for wizard mode."""
    if "wizard_mode_enabled" not in st.session_state:
        st.session_state.wizard_mode_enabled = False

    if "wizard_current_step" not in st.session_state:
        st.session_state.wizard_current_step = 1  # Steps: 1, 2, 3, 4, then summary

    if "wizard_profile" not in st.session_state:
        st.session_state.wizard_profile = None

    if "wizard_results" not in st.session_state:
        st.session_state.wizard_results = {}

    # Step 6 what-if analysis state
    if "show_what_if_analysis" not in st.session_state:
        st.session_state.show_what_if_analysis = False

    if "selected_coaching_question" not in st.session_state:
        st.session_state.selected_coaching_question = None


def build_profile_from_session() -> TransitionProfile:
    """
    Convert st.session_state inputs → TransitionProfile dataclass.

    This is the bridge between UI (scattered session_state) and calculations (clean Profile).
    Called at start of any calculation in wizard.

    Returns:
        TransitionProfile with all fields populated from session state
    """
    profile = TransitionProfile()

    # ========== USER IDENTITY (Step 1) ==========
    profile.rank = st.session_state.get("user_rank", "")
    profile.years_of_service = st.session_state.get("user_years_of_service", 0)
    profile.service_branch = st.session_state.get("user_service_branch", "")
    profile.separation_date = st.session_state.get("user_separation_date", None)
    profile.marital_status = st.session_state.get("user_marital_status", "Single")
    profile.dependents = st.session_state.get("user_dependents", 0)

    # Retirement location (Step 1) - maps to target_city/state for calculations
    profile.target_city = st.session_state.get("retirement_location", "")
    profile.target_state = st.session_state.get("retirement_state", "")

    # ========== FINANCES (Step 2) ==========
    # Income
    profile.current_annual_retirement_pay = st.session_state.get("military_pension", 0.0)
    profile.current_va_annual_benefit = st.session_state.get("va_annual_benefit", 0.0)
    profile.spouse_annual_income = st.session_state.get("spouse_income_annual", 0.0)
    profile.other_annual_income = st.session_state.get("other_income_annual", 0.0)

    # Expenses
    profile.monthly_expenses_mandatory = st.session_state.get("monthly_expenses_mandatory", 0.0)
    profile.monthly_expenses_negotiable = st.session_state.get("monthly_expenses_negotiable", 0.0)
    profile.monthly_expenses_optional = st.session_state.get("monthly_expenses_optional", 0.0)

    # Savings & Debt
    profile.current_savings = st.session_state.get("current_savings", 0.0)
    profile.current_debt = st.session_state.get("current_debt", 0.0)
    profile.debt_payoff_priority = st.session_state.get("debt_payoff_priority", "minimum")

    # ========== BENEFITS (Step 3) ==========
    # VA Disability
    profile.current_va_disability_rating = st.session_state.get("unified_va_disability_rating", 30)
    profile.va_rating_assumption = st.session_state.get("va_rating_assumption", None)

    # Education Benefits
    profile.plan_to_use_gi_bill = st.session_state.get("plan_to_use_gi_bill", False)
    profile.gi_bill_transfer_eligible = st.session_state.get("gi_bill_transfer_eligible", False)
    profile.education_level = st.session_state.get("education_level", "bachelor")

    # SBP
    profile.elect_sbp = st.session_state.get("elect_sbp", False)
    profile.sbp_beneficiary = st.session_state.get("sbp_beneficiary", "spouse")

    # Healthcare
    profile.healthcare_plan_choice = st.session_state.get("healthcare_plan_choice", "tricare_select")

    # ========== TRANSITION PLAN (Step 4) ==========
    profile.job_search_timeline_months = st.session_state.get("job_search_months", 6)
    profile.estimated_annual_salary = st.session_state.get("estimated_annual_salary", 0.0)
    profile.cost_of_living_adjustment_factor = st.session_state.get("cost_of_living_factor", 1.0)

    # Career field (for context in salary estimates)
    if hasattr(profile, "metadata"):
        profile.metadata["target_career_field"] = st.session_state.get("target_career_field", "technology")

    # Tax Info
    profile.filing_status = st.session_state.get("filing_status", "single")

    return profile


def save_profile_to_file(profile: TransitionProfile, filename: str = None) -> tuple[bool, str]:
    """
    User-initiated export: save profile to JSON file in Downloads.

    This is EXPLICIT user action - nothing automatic.

    Args:
        profile: TransitionProfile to save
        filename: optional filename (default: transition_plan_[date].json)

    Returns:
        (success: bool, message: str)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transition_plan_{timestamp}.json"

    try:
        # Convert profile to dict for JSON serialization
        profile_dict = {
            # Identity
            "rank": profile.rank,
            "years_of_service": profile.years_of_service,
            "service_branch": profile.service_branch,
            "separation_date": (profile.separation_date.isoformat() if profile.separation_date else None),
            "marital_status": profile.marital_status,
            "dependents": profile.dependents,
            # Finances
            "current_savings": profile.current_savings,
            "monthly_expenses_mandatory": profile.monthly_expenses_mandatory,
            "monthly_expenses_negotiable": profile.monthly_expenses_negotiable,
            "monthly_expenses_optional": profile.monthly_expenses_optional,
            "current_debt": profile.current_debt,
            "current_annual_retirement_pay": profile.current_annual_retirement_pay,
            "current_va_annual_benefit": profile.current_va_annual_benefit,
            "spouse_annual_income": profile.spouse_annual_income,
            # Benefits
            "current_va_disability_rating": profile.current_va_disability_rating,
            "healthcare_plan_choice": profile.healthcare_plan_choice,
            "elect_sbp": profile.elect_sbp,
            "plan_to_use_gi_bill": profile.plan_to_use_gi_bill,
            # Transition
            "job_search_timeline_months": profile.job_search_timeline_months,
            "estimated_annual_salary": profile.estimated_annual_salary,
            "target_city": profile.target_city,
            "target_state": profile.target_state,
            "filing_status": profile.filing_status,
        }

        # Try to save to Desktop/ProjectAtlas_Data folder
        save_path = Path.home() / "Desktop" / "ProjectAtlas_Data"
        save_path.mkdir(parents=True, exist_ok=True)
        filepath = save_path / filename

        with open(filepath, "w") as f:
            json.dump(profile_dict, f, indent=2)

        return True, f"[OK] Saved to {filepath}"

    except Exception as e:
        return False, f"[ERROR] Error saving: {str(e)}"


def get_wizard_state(key: str) -> Any:
    """Get wizard-specific state value."""
    return st.session_state.get(f"wizard_{key}", None)


def set_wizard_state(key: str, value: Any) -> None:
    """Set wizard-specific state value."""
    st.session_state[f"wizard_{key}"] = value


def get_step_summary(step: int) -> str:
    """Get mini-summary text for a step."""
    if step == 1:
        rank = st.session_state.get("user_rank", "TBD")
        yos = st.session_state.get("user_years_of_service", 0)
        branch = st.session_state.get("user_service_branch", "TBD")
        sep_date = st.session_state.get("user_separation_date", None)
        date_str = sep_date.strftime("%b %d, %Y") if sep_date else "TBD"
        return f"**{rank}** with {yos} YOS in {branch} | Separating {date_str}"

    elif step == 2:
        # Calculate income and expenses from session state
        current_paycheck = st.session_state.get("current_paycheck_monthly", 0)
        spouse_income = st.session_state.get("spouse_income_annual", 0) / 12
        other_income = st.session_state.get("other_income_annual", 0) / 12
        monthly_income = current_paycheck + spouse_income + other_income

        mandatory = st.session_state.get("monthly_expenses_mandatory", 0)
        negotiable = st.session_state.get("monthly_expenses_negotiable", 0)
        optional = st.session_state.get("monthly_expenses_optional", 0)
        monthly_expenses = mandatory + negotiable + optional

        gap = monthly_income - monthly_expenses
        gap_str = f"${gap:+,.0f}" if gap != 0 else "$0"
        return f"Income: ${monthly_income:,.0f}/mo | Expenses: ${monthly_expenses:,.0f}/mo | Gap: {gap_str}"

    elif step == 3:
        va_rating = st.session_state.get("unified_va_disability_rating", 0)
        gi_bill = "Yes" if st.session_state.get("plan_to_use_gi_bill", False) else "No"
        sbp = "Yes" if st.session_state.get("elect_sbp", False) else "No"
        return f"VA Rating: {va_rating}% | GI Bill: {gi_bill} | SBP: {sbp}"

    elif step == 4:
        job_months = st.session_state.get("job_search_months", 6)
        salary = st.session_state.get("estimated_annual_salary", 0)
        city = st.session_state.get("target_city", "TBD")
        return f"Job search: {job_months}mo | Salary: ${salary:,.0f} | Location: {city}"

    return "Complete"


def clear_wizard_session():
    """Clear all wizard session state (for reset/restart)."""
    wizard_keys = [k for k in st.session_state.keys() if k.startswith("wizard_")]
    for key in wizard_keys:
        del st.session_state[key]
    st.session_state.wizard_current_step = 1
    st.session_state.wizard_profile = None
    st.session_state.wizard_results = {}
