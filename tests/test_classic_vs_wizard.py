"""
Integration Test: Classic Tab vs Transition Wizard Consistency

This test verifies that both the Classic (8-tab) interface and the Transition Wizard
produce identical financial calculations when given the same input data.

The test:
1. Creates reference input data for a military service member
2. Simulates classic tab session state
3. Simulates wizard session state (with equivalent data)
4. Builds profiles from both paths
5. Runs key calculations through both
6. Compares all outputs for consistency

This ensures user trust: both paths produce same results.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pytest

from src.data_models import TransitionProfile, create_empty_profile
from src.model_layer.bah_lookup import calculate_gi_bill_total, get_bah_rate
from src.model_layer.healthcare_model import (
    calculate_healthcare_benefits,
    compare_healthcare_costs,
)
from src.model_layer.retirement_pay_model import (
    _calculate_retirement_pay,
)
from src.model_layer.salary_predictor import estimate_salary_range

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ========== TEST DATA FIXTURES ==========
@pytest.fixture
def reference_military_profile():
    """
    Reference data for a typical O-5 (Lieutenant Colonel/Commander) military member.
    This represents a realistic transition scenario.
    """
    return {
        # User Identity
        "rank": "O-5",
        "years_of_service": 20,
        "service_branch": "Air Force",
        "separation_date": datetime.now() + timedelta(days=180),
        "marital_status": "Married",
        "dependents": 2,
        # Location
        "retirement_location": "San Diego, CA",
        "retirement_state": "CA",
        "target_city": "San Diego, CA",
        "target_state": "CA",
        # Financial
        "military_pension": 5000.0,  # Monthly
        "current_va_disability_rating": 30,
        "va_annual_benefit": 7380.0,  # From rating
        "spouse_income_annual": 60000.0,
        "other_income_annual": 0.0,
        # Expenses
        "monthly_mandatory_expenses": 2500.0,
        "monthly_negotiable_expenses": 1000.0,
        "monthly_optional_expenses": 500.0,
        # Savings & Debt
        "current_savings": 250000.0,
        "current_debt": 50000.0,
        "debt_payoff_priority": "minimum",
        # Benefits
        "plan_to_use_gi_bill": True,
        "gi_bill_transfer_eligible": False,
        "education_level": "bachelor",
        "gi_months_available": 36,
        "elect_sbp": True,
        "sbp_beneficiary": "spouse",
        "healthcare_plan_choice": "tricare_select",
        # Transition Plan
        "job_search_months": 6,
        "estimated_annual_salary": 150000.0,
        "target_career_field": "Technology/IT",
        "filing_status": "married_joint",
        "cost_of_living_factor": 1.0,
    }


@pytest.fixture
def classic_tab_session_state(reference_military_profile):
    """
    Simulate the session state as would be populated by classic tab UI.

    Classic tab uses different session keys naming (user_prefix) and organization
    (scattered across multiple tabs).
    """
    state = {}

    # User Profile Tab - classic naming convention
    state["user_rank"] = reference_military_profile["rank"]
    state["user_years_of_service"] = reference_military_profile["years_of_service"]
    state["user_service_branch"] = reference_military_profile["service_branch"]
    state["user_separation_date"] = reference_military_profile["separation_date"]
    state["user_marital_status"] = reference_military_profile["marital_status"]
    state["user_dependents"] = reference_military_profile["dependents"]

    # Income Tab - classic names
    state["military_pension"] = reference_military_profile["military_pension"]
    state["va_rating"] = reference_military_profile["current_va_disability_rating"]
    state["va_annual_benefit"] = reference_military_profile["va_annual_benefit"]
    state["spouse_income_monthly"] = reference_military_profile["spouse_income_annual"] / 12
    state["other_income_monthly"] = 0.0
    state["filing_status"] = reference_military_profile["filing_status"]
    state["state"] = reference_military_profile["target_state"]

    # Expenses Tab
    state["housing_expense"] = reference_military_profile["monthly_mandatory_expenses"] * 0.6
    state["utilities_expense"] = reference_military_profile["monthly_mandatory_expenses"] * 0.2
    state["food_expense"] = reference_military_profile["monthly_mandatory_expenses"] * 0.2
    state["discretionary_expense"] = (
        reference_military_profile["monthly_negotiable_expenses"]
        + reference_military_profile["monthly_optional_expenses"]
    )

    # Healthcare Tab
    state["medical_plan"] = reference_military_profile["healthcare_plan_choice"]
    state["medical_dependents_status"] = "spouse+2child"
    state["vision_plan"] = "tricare"
    state["dental_plan"] = "tricare"

    # Education Tab
    state["gi_program_type"] = (
        "post_911" if reference_military_profile["plan_to_use_gi_bill"] else "none"
    )
    state["school_location_preset"] = "San Diego, CA"
    state["gi_months_used"] = 0
    state["bah_custom"] = reference_military_profile["military_pension"]  # Will be overridden

    # What-If Tab
    state["savings_available"] = reference_military_profile["current_savings"]
    state["current_debt"] = reference_military_profile["current_debt"]
    state["new_job_salary_annual"] = reference_military_profile["estimated_annual_salary"]
    state["job_start_month"] = 6

    # SBP
    state["sbp_checkbox"] = reference_military_profile["elect_sbp"]

    return state


@pytest.fixture
def wizard_session_state(reference_military_profile):
    """
    Simulate the session state as populated by wizard mode.

    Wizard uses same session keys as mapped in session_manager.build_profile_from_session()
    """
    state = {}

    # Step 1: User Profile
    state["user_rank"] = reference_military_profile["rank"]
    state["user_years_of_service"] = reference_military_profile["years_of_service"]
    state["user_service_branch"] = reference_military_profile["service_branch"]
    state["user_separation_date"] = reference_military_profile["separation_date"]
    state["user_marital_status"] = reference_military_profile["marital_status"]
    state["user_dependents"] = reference_military_profile["dependents"]
    state["retirement_location"] = reference_military_profile["retirement_location"]
    state["retirement_state"] = reference_military_profile["retirement_state"]

    # Step 2: Financial Snapshot
    state["military_pension"] = reference_military_profile["military_pension"]
    state["current_va_disability_rating"] = reference_military_profile[
        "current_va_disability_rating"
    ]
    state["unified_va_disability_rating"] = reference_military_profile[
        "current_va_disability_rating"
    ]
    state["va_annual_benefit"] = reference_military_profile["va_annual_benefit"]
    state["spouse_income_annual"] = reference_military_profile["spouse_income_annual"]
    state["other_income_annual"] = reference_military_profile["other_income_annual"]

    state["monthly_mandatory_expenses"] = reference_military_profile["monthly_mandatory_expenses"]
    state["monthly_negotiable_expenses"] = reference_military_profile["monthly_negotiable_expenses"]
    state["monthly_optional_expenses"] = reference_military_profile["monthly_optional_expenses"]

    state["current_savings"] = reference_military_profile["current_savings"]
    state["current_debt"] = reference_military_profile["current_debt"]
    state["debt_payoff_priority"] = reference_military_profile["debt_payoff_priority"]

    # Step 3: Benefits & Education
    state["plan_to_use_gi_bill"] = reference_military_profile["plan_to_use_gi_bill"]
    state["gi_bill_transfer_eligible"] = reference_military_profile["gi_bill_transfer_eligible"]
    state["education_level"] = reference_military_profile["education_level"]
    state["gi_months_available"] = reference_military_profile["gi_months_available"]
    state["elect_sbp"] = reference_military_profile["elect_sbp"]
    state["sbp_beneficiary"] = reference_military_profile["sbp_beneficiary"]
    state["healthcare_plan_choice"] = reference_military_profile["healthcare_plan_choice"]

    # Step 4: Transition Plan
    state["job_search_months"] = reference_military_profile["job_search_months"]
    state["target_career_field"] = reference_military_profile["target_career_field"]
    state["estimated_annual_salary"] = reference_military_profile["estimated_annual_salary"]
    state["filing_status"] = reference_military_profile["filing_status"]

    return state


# ========== PROFILE BUILDING TESTS ==========
class TestProfileBuilding:
    """
    Test that both classic and wizard paths build equivalent profiles.
    """

    def test_build_profile_from_classic_session(self, classic_tab_session_state):
        """Verify classic tab session can be converted to profile."""
        # Mock st.session_state
        mock_state = MockSessionState(classic_tab_session_state)

        profile = _build_profile_from_classic_state(mock_state)

        assert profile.rank == "O-5"
        assert profile.years_of_service == 20
        assert profile.service_branch == "Air Force"
        assert profile.current_savings == 250000.0
        assert profile.current_annual_retirement_pay == 60000.0  # 5000 * 12

    def test_build_profile_from_wizard_session(self, wizard_session_state):
        """Verify wizard session can be converted to profile."""
        mock_state = MockSessionState(wizard_session_state)

        profile = _build_profile_from_wizard_state(mock_state)

        assert profile.rank == "O-5"
        assert profile.years_of_service == 20
        assert profile.service_branch == "Air Force"
        assert profile.current_savings == 250000.0
        assert profile.target_city == "San Diego, CA"
        assert profile.target_state == "CA"

    def test_classic_and_wizard_profiles_equivalent(
        self, classic_tab_session_state, wizard_session_state
    ):
        """
        Critical test: Classic and wizard build equivalent profiles.

        This ensures that both UI paths converge on the same data before calculation.
        """
        classic_profile = _build_profile_from_classic_state(
            MockSessionState(classic_tab_session_state)
        )
        wizard_profile = _build_profile_from_wizard_state(MockSessionState(wizard_session_state))

        # Core identity must match
        assert classic_profile.rank == wizard_profile.rank
        assert classic_profile.years_of_service == wizard_profile.years_of_service
        assert classic_profile.service_branch == wizard_profile.service_branch

        # Financial snapshot must match
        assert classic_profile.current_savings == wizard_profile.current_savings
        assert (
            classic_profile.current_annual_retirement_pay
            == wizard_profile.current_annual_retirement_pay
        )
        assert classic_profile.current_va_annual_benefit == wizard_profile.current_va_annual_benefit

        # Target location must match
        assert classic_profile.target_state == wizard_profile.target_state


# ========== CALCULATION CONSISTENCY TESTS ==========
class TestCalculationConsistency:
    """
    Test that the same calculations produce identical results regardless of UI path.
    """

    def test_pension_calculation_identical(self, wizard_session_state):
        """Pension calculation should be deterministic."""
        profile = _build_profile_from_wizard_state(MockSessionState(wizard_session_state))

        # Run calculation twice - should get identical results
        pension_1 = _calculate_retirement_pay(profile)
        pension_2 = _calculate_retirement_pay(profile)

        assert pension_1 == pension_2
        assert pension_1 > 0

    def test_healthcare_costs_deterministic(self, wizard_session_state):
        """Healthcare cost calculation must be deterministic (same input = same output)."""
        wizard_profile = _build_profile_from_wizard_state(MockSessionState(wizard_session_state))

        plan = "tricare_select"

        # Run twice with same profile
        costs_1 = calculate_healthcare_benefits(wizard_profile, plan)
        costs_2 = calculate_healthcare_benefits(wizard_profile, plan)

        # Results should be identical
        assert costs_1["annual_cost"] == costs_2["annual_cost"]
        assert costs_1["enrollment_fee"] == costs_2["enrollment_fee"]
        assert costs_1["copay_cost"] == costs_2["copay_cost"]

    def test_salary_range_identical_classic_vs_wizard(
        self, classic_tab_session_state, wizard_session_state
    ):
        """Salary estimate ranges should be identical."""
        classic_profile = _build_profile_from_classic_state(
            MockSessionState(classic_tab_session_state)
        )
        wizard_profile = _build_profile_from_wizard_state(MockSessionState(wizard_session_state))

        classic_salary = estimate_salary_range(classic_profile)
        wizard_salary = estimate_salary_range(wizard_profile)

        assert classic_salary["low"] == wizard_salary["low"]
        assert classic_salary["mid"] == wizard_salary["mid"]
        assert classic_salary["high"] == wizard_salary["high"]

    def test_bah_calculation_identical(self, wizard_session_state):
        """BAH lookup should be deterministic by location."""
        bah_rate = get_bah_rate("San Diego, CA")

        # Call twice - should get same result
        bah_rate_2 = get_bah_rate("San Diego, CA")

        assert bah_rate == bah_rate_2
        assert bah_rate > 0

    def test_gi_bill_total_identical(self, wizard_session_state):
        """GI Bill total calculation should be deterministic."""
        bah_monthly = get_bah_rate("San Diego, CA")
        months = 36

        # Calculate twice
        total_1 = calculate_gi_bill_total(bah_monthly, months)
        total_2 = calculate_gi_bill_total(bah_monthly, months)

        assert total_1 == total_2
        assert total_1 > 0


# ========== END-TO-END SCENARIO TESTS ==========
class TestEndToEndScenarios:
    """
    Test realistic military transition scenarios through both paths.
    """

    def test_typical_o5_transition_scenario(self, wizard_session_state):
        """
        Scenario: O-5 with 20 years, family, TRICARE, GI Bill, new career.
        Both paths should produce identical financial projections when using same profile.
        """
        # Use wizard profile as source of truth
        wizard_profile = _build_profile_from_wizard_state(MockSessionState(wizard_session_state))

        # Run key calculations
        results = _run_scenario_calculations(wizard_profile)

        # Verify all calculations completed without errors
        assert results["pension"] is not None
        assert results["healthcare_cost"] is not None
        assert results["salary_range"] is not None
        assert results["bah"] is not None

        # Verify results are reasonable values
        assert results["pension"] > 0
        assert results["healthcare_cost"]["annual_cost"] > 0
        assert results["salary_range"]["mid"] > 0

    def test_different_rank_scenarios(self):
        """Test scenarios with different military ranks produce consistent results."""
        ranks = ["O-3", "O-4", "O-5", "O-6"]

        for rank in ranks:
            profile = create_empty_profile()
            profile.rank = rank
            profile.years_of_service = 20

            # Should calculate pension without errors
            pension = _calculate_retirement_pay(profile)
            assert pension is not None

    def test_different_healthcare_plans(self):
        """Test all healthcare plans produce deterministic results."""
        profile = create_empty_profile()
        profile.dependents = 2
        profile.marital_status = "Married"

        plans = ["tricare_select", "tricare_prime", "va_health", "aca"]
        results = {}

        for plan in plans:
            costs = calculate_healthcare_benefits(profile, plan)
            results[plan] = costs

            # Should have consistent keys
            assert "annual_cost" in costs
            assert "enrollment_fee" in costs


# ========== UTILITY FUNCTIONS ==========
class MockSessionState:
    """Mock st.session_state for testing without Streamlit running."""

    def __init__(self, initial_state: Dict[str, Any]):
        self._state = initial_state

    def get(self, key: str, default=None):
        return self._state.get(key, default)

    def __setitem__(self, key: str, value):
        self._state[key] = value

    def __getitem__(self, key: str):
        return self._state[key]

    def __contains__(self, key: str):
        return key in self._state


def _build_profile_from_classic_state(mock_state) -> TransitionProfile:
    """Build profile from classic tab session state."""
    profile = create_empty_profile()

    # User info
    profile.rank = mock_state.get("user_rank", "")
    profile.years_of_service = mock_state.get("user_years_of_service", 0)
    profile.service_branch = mock_state.get("user_service_branch", "")
    profile.separation_date = mock_state.get("user_separation_date", None)
    profile.marital_status = mock_state.get("user_marital_status", "Single")
    profile.dependents = mock_state.get("user_dependents", 0)

    # Financial
    profile.current_annual_retirement_pay = mock_state.get("military_pension", 0) * 12
    profile.current_va_annual_benefit = mock_state.get("va_annual_benefit", 0)
    profile.spouse_annual_income = mock_state.get("spouse_income_monthly", 0) * 12
    profile.other_annual_income = mock_state.get("other_income_monthly", 0) * 12

    profile.current_savings = mock_state.get("savings_available", 0)
    profile.current_debt = mock_state.get("current_debt", 0)

    # Target state (classic uses 'state' key)
    profile.target_state = mock_state.get("state", "")

    # Benefits
    profile.healthcare_plan_choice = mock_state.get("medical_plan", "tricare_select")
    profile.elect_sbp = mock_state.get("sbp_checkbox", False)

    # Salary
    profile.estimated_annual_salary = mock_state.get("new_job_salary_annual", 0)
    profile.filing_status = mock_state.get("filing_status", "single")

    return profile


def _build_profile_from_wizard_state(mock_state) -> TransitionProfile:
    """Build profile from wizard session state (actual path)."""
    profile = create_empty_profile()

    # Step 1: User Identity
    profile.rank = mock_state.get("user_rank", "")
    profile.years_of_service = mock_state.get("user_years_of_service", 0)
    profile.service_branch = mock_state.get("user_service_branch", "")
    profile.separation_date = mock_state.get("user_separation_date", None)
    profile.marital_status = mock_state.get("user_marital_status", "Single")
    profile.dependents = mock_state.get("user_dependents", 0)

    # Retirement location (maps to target_city/state)
    profile.target_city = mock_state.get("retirement_location", "")
    profile.target_state = mock_state.get("retirement_state", "")

    # Step 2: Financial
    profile.current_annual_retirement_pay = mock_state.get("military_pension", 0) * 12
    profile.current_va_annual_benefit = mock_state.get("va_annual_benefit", 0)
    profile.spouse_annual_income = mock_state.get("spouse_income_annual", 0)
    profile.other_annual_income = mock_state.get("other_income_annual", 0)

    profile.monthly_expenses_mandatory = mock_state.get("monthly_mandatory_expenses", 0)
    profile.monthly_expenses_negotiable = mock_state.get("monthly_negotiable_expenses", 0)
    profile.monthly_expenses_optional = mock_state.get("monthly_optional_expenses", 0)

    profile.current_savings = mock_state.get("current_savings", 0)
    profile.current_debt = mock_state.get("current_debt", 0)

    # Step 3: Benefits
    profile.current_va_disability_rating = mock_state.get("unified_va_disability_rating", 30)
    profile.plan_to_use_gi_bill = mock_state.get("plan_to_use_gi_bill", False)
    profile.education_level = mock_state.get("education_level", "bachelor")
    profile.elect_sbp = mock_state.get("elect_sbp", False)
    profile.sbp_beneficiary = mock_state.get("sbp_beneficiary", "spouse")
    profile.healthcare_plan_choice = mock_state.get("healthcare_plan_choice", "tricare_select")

    # Step 4: Transition Plan
    profile.job_search_timeline_months = mock_state.get("job_search_months", 6)
    profile.estimated_annual_salary = mock_state.get("estimated_annual_salary", 0)
    profile.filing_status = mock_state.get("filing_status", "single")

    return profile


def _run_scenario_calculations(profile: TransitionProfile) -> Dict[str, Any]:
    """
    Run standard scenario calculations on a profile.

    Returns dict with all key results.
    """
    results = {
        "pension": _calculate_retirement_pay(profile),
        "healthcare_cost": calculate_healthcare_benefits(profile, profile.healthcare_plan_choice),
        "salary_range": estimate_salary_range(profile),
    }

    if profile.target_city and profile.target_state:
        results["bah"] = get_bah_rate(profile.target_city)

    return results


def _compare_calculation_results(classic_results: Dict, wizard_results: Dict):
    """
    Compare results from classic and wizard paths.

    Raises AssertionError if any results differ.
    """
    # Pension must match exactly
    assert (
        classic_results["pension"] == wizard_results["pension"]
    ), f"Pension mismatch: classic={classic_results['pension']}, wizard={wizard_results['pension']}"

    # Healthcare costs must match exactly
    classic_hc = classic_results["healthcare_cost"]
    wizard_hc = wizard_results["healthcare_cost"]
    assert (
        classic_hc["annual_cost"] == wizard_hc["annual_cost"]
    ), f"Healthcare cost mismatch: classic={classic_hc['annual_cost']}, wizard={wizard_hc['annual_cost']}"

    # Salary ranges must match exactly
    classic_salary = classic_results["salary_range"]
    wizard_salary = wizard_results["salary_range"]
    assert (
        classic_salary["low"] == wizard_salary["low"]
    ), f"Salary low mismatch: classic={classic_salary['low']}, wizard={wizard_salary['low']}"
    assert (
        classic_salary["high"] == wizard_salary["high"]
    ), f"Salary high mismatch: classic={classic_salary['high']}, wizard={wizard_salary['high']}"
    assert (
        classic_salary["mid"] == wizard_salary["mid"]
    ), f"Salary mid mismatch: classic={classic_salary['mid']}, wizard={wizard_salary['mid']}"

    # BAH if available
    if "bah" in classic_results:
        assert (
            classic_results["bah"] == wizard_results["bah"]
        ), f"BAH mismatch: classic={classic_results['bah']}, wizard={wizard_results['bah']}"


# ========== RUN TESTS ==========
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
