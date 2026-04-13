"""
Session State Manager for ProjectAtlas Wizard

Handles persistent form state across wizard steps.
All form inputs are tracked in Streamlit session_state.
"""

from datetime import date
from typing import Any, Dict, List

import streamlit as st


class SessionStateManager:
    """Manages Streamlit session state for the wizard."""

    # Define all form fields that should persist
    FORM_FIELDS = {
        # User Profile - Step 1
        "user_rank": "O-5",
        "user_years_of_service": 28,
        "user_career_field": "Operations Research",
        "user_locality": "Arlington",
        "user_separation_date": date(2026, 6, 1),
        "user_marital_status": "Married",
        "user_dependents": 0,
        "user_service_branch": "Navy",
        "user_state": "VA",
        # Career Estimator Tab (editable context fields)
        "career_education": "Master's",
        "career_clearance": "Secret",
        # SBP & Life Insurance (Step 2b)
        "sbp_election": "off",  # 'off', 'spouse_only', 'family', 'custom'
        "sbp_monthly_cost": 0,
        "sbp_monthly_benefit": 0,
        "life_insurance_monthly_cost": 0,
        "life_insurance_monthly_benefit": 0,
        # Healthcare - Step 2
        "medical_plan": "Tricare Prime",
        "medical_coverage_type": "Family",
        "medical_dependents": 2,
        "medical_custom_cost": 0,
        "tricare_monthly_cost": 0,
        "vision_plan": "Tricare Vision",
        "vision_custom_cost": 0,
        "dental_plan": "Tricare Dental",
        "dental_custom_cost": 0,
        # Income - Step 3 (Pension & Disability)
        "military_pension_gross": 0,  # Changed from 3500 - user must enter their actual amount
        "tricare_deduction_pension": 90,
        "ltc_deduction_pension": 0,
        "other_pretax_deduction": 0,
        "va_rating_slider": 0,
        "va_monthly_amount": 0,
        "pension_take_home": 0,
        # GI Bill - Step 2c
        "gi_bill_choice": "None",
        "gi_bill_months_remaining": 36,
        "gi_bill_bah_monthly": 0,
        "gi_bill_bah_override": 0,
        "gi_bill_include_in_summary": False,
        # Assets & Debts - Step 4
        "asset_checking": 10000,
        "asset_savings": 40000,
        "asset_investments": 100000,
        "asset_home_value": 500000,
        "debt_mortgage": 250000,
        "debt_cc": 0,
        "debt_auto": 0,
        "debt_other": 0,
        "debt_cc_limit": 5000,
        # Financial Resources - Step 4 (Civilian Career)
        "current_savings": 0,  # Available liquid savings for transition
        "available_credit": 0,  # Available credit (credit cards, HELOC, etc.)
        "job_search_timeline_months": 6,  # Expected months to find civilian job
        "estimated_civilian_salary": 0,  # Estimated annual civilian salary
        "current_military_takehome_monthly": 0,  # Monthly take-home from current military job
        "spousal_income_gross_monthly": 0,  # Spouse/partner gross monthly income
        "other_income_gross_monthly": 0,  # Other household income (rental, dividends, etc.)
        # Expenses
        "expenses_data": [],
        "custom_expenses": {},
        "deleted_expenses": [],
        # Wizard navigation
        "current_step": 1,
        "total_steps": 11,
        # Tab routing
        "current_tab": "wizard",
        "show_prediction": False,
        "show_prediction_details": False,
    }

    @staticmethod
    def initialize():
        """Initialize all session state fields if not present."""
        # If a demo profile was just loaded, don't reset any fields - preserve demo data
        if st.session_state.get("_demo_profile_loaded", False):
            # Only initialize fields that are truly missing
            for key, default_value in SessionStateManager.FORM_FIELDS.items():
                if key not in st.session_state:
                    st.session_state[key] = default_value
        else:
            # Normal initialization - set all missing fields to defaults
            for key, default_value in SessionStateManager.FORM_FIELDS.items():
                if key not in st.session_state:
                    st.session_state[key] = default_value

        # Initialize step-specific dictionary state (preserve across navigation)
        dict_fields = {
            "adjusted_classifications": {},
            "adjusted_amounts": {},
            "adjusted_cc_eligibility": {},
            "custom_expenses": {},
            "deleted_expenses": [],
            "csv_classification_map": {},
            "final_amounts": {},
            "prepaid_tracker": [],
        }

        for key, default_value in dict_fields.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

        # Ensure step navigation values are always integers (fix for legacy string values)
        if "current_step" in st.session_state and not isinstance(st.session_state["current_step"], int):
            st.session_state["current_step"] = 1
        if "total_steps" in st.session_state and not isinstance(st.session_state["total_steps"], int):
            st.session_state["total_steps"] = 11

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Safely retrieve a session state value."""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a session state value."""
        st.session_state[key] = value

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all form data as a dictionary for export."""
        return {k: st.session_state.get(k) for k in SessionStateManager.FORM_FIELDS}

    @staticmethod
    def reset():
        """Reset all session state to defaults."""
        for key, default_value in SessionStateManager.FORM_FIELDS.items():
            st.session_state[key] = default_value

    @staticmethod
    def next_step():
        """Advance to next wizard step."""
        current = st.session_state.get("current_step", 1)
        total = st.session_state.get("total_steps", 11)
        if current < total:
            st.session_state["current_step"] = current + 1

    @staticmethod
    def prev_step():
        """Go back to previous wizard step."""
        current = st.session_state.get("current_step", 1)
        if current > 1:
            st.session_state["current_step"] = current - 1

    @staticmethod
    def is_first_step() -> bool:
        """Check if on first step."""
        return st.session_state.get("current_step", 1) == 1

    @staticmethod
    def is_last_step() -> bool:
        """Check if on last step."""
        current = st.session_state.get("current_step", 1)
        total = st.session_state.get("total_steps", 11)
        return current == total

    @staticmethod
    def get_step_progress() -> tuple:
        """Return (current_step, total_steps) for progress display."""
        return (st.session_state.get("current_step", 1), st.session_state.get("total_steps", 11))
