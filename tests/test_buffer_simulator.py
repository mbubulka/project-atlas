"""
Test suite for Project Atlas buffer_simulator module.

Tests the main simulation engine and cash flow projections.
"""

import pytest

from src.data_models import create_empty_profile
from src.model_layer.buffer_simulator import (
    _calculate_financial_verdict,
    _identify_risk_factors,
    _simulate_monthly_cash_flow,
    run_buffer_simulation,
)


class TestBufferSimulator:
    """Test suite for financial buffer simulation."""

    def test_run_buffer_simulation_complete_profile(self):
        """Test: Full simulation runs successfully with complete profile."""

        profile = create_empty_profile("Test User")
        profile.user_name = "Test User"
        profile.rank = "E-7"
        profile.years_of_service = 20
        profile.current_savings = 50000
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.monthly_expenses_optional = 500
        profile.current_va_disability_rating = 30
        profile.target_city = "Denver, CO"
        profile.target_state = "CO"
        profile.job_search_timeline_months = 6
        profile.estimated_annual_salary = 100000
        profile.healthcare_plan_choice = "tricare_select"
        profile.job_offer_certainty = 0.8

        result = run_buffer_simulation(profile)

        # Should have all outputs filled
        assert result.annual_take_home_pay > 0
        assert result.monthly_take_home_pay > 0
        assert len(result.monthly_cash_flow) == 6
        assert result.final_cash_buffer is not None
        assert result.financial_verdict in [
            "STRONG_SURPLUS",
            "SURPLUS",
            "BREAK_EVEN",
            "DEFICIT",
            "SEVERE_DEFICIT",
        ]

    def test_simulate_monthly_cash_flow_positive_buffer(self):
        """Test: Positive income > expenses results in accumulating savings."""

        profile = create_empty_profile("Test User")
        profile.rank = "E-7"
        profile.years_of_service = 20
        profile.current_savings = 50000
        profile.monthly_expenses_mandatory = 3000
        profile.current_va_disability_rating = 30
        profile.target_city = "Denver, CO"
        profile.target_state = "CO"
        profile.job_search_timeline_months = 6
        profile.estimated_annual_salary = 100000
        profile.healthcare_plan_choice = "tricare_select"
        profile.job_offer_certainty = 0.8
        profile.monthly_take_home_pay = 6000  # Exceeds expenses
        profile.monthly_healthcare_cost = 500

        result = _simulate_monthly_cash_flow(profile)

        # Cumulative savings should increase over time
        first_month = result.monthly_cash_flow[0]
        last_month = result.monthly_cash_flow[-1]

        assert last_month["cumulative_savings"] > first_month["cumulative_savings"]
        assert result.final_cash_buffer > profile.current_savings

    def test_calculate_financial_verdict_strong_surplus(self):
        """Test: Strong surplus verdict when buffer > 3 months expenses."""

        profile = create_empty_profile("Test User")
        profile.final_cash_buffer = 150000  # Large buffer
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.job_offer_certainty = 0.9

        result = _calculate_financial_verdict(profile)

        assert result.financial_verdict == "STRONG_SURPLUS"
        assert result.financial_verdict_confidence > 0.8

    def test_calculate_financial_verdict_surplus(self):
        """Test: Surplus verdict when buffer > 0 but < 3 months."""

        profile = create_empty_profile("Test User")
        profile.final_cash_buffer = 5000  # Positive but modest
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.job_offer_certainty = 0.8

        result = _calculate_financial_verdict(profile)

        assert result.financial_verdict == "SURPLUS"

    def test_calculate_financial_verdict_deficit(self):
        """Test: Deficit verdict when buffer < -5000."""

        profile = create_empty_profile("Test User")
        profile.final_cash_buffer = -10000  # Significant deficit
        profile.monthly_expenses_mandatory = 3000
        profile.job_offer_certainty = 0.7

        result = _calculate_financial_verdict(profile)

        assert result.financial_verdict in ["DEFICIT", "SEVERE_DEFICIT"]

    def test_identify_risk_factors_negative_buffer(self):
        """Test: Risk identified when buffer is negative."""

        profile = create_empty_profile("Test User")
        profile.final_cash_buffer = -10000
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.monthly_take_home_pay = 4000
        profile.monthly_healthcare_cost = 300
        profile.job_offer_certainty = 0.8
        profile.job_search_timeline_months = 6
        profile.monthly_cash_flow = [{"net_flow": 200}]

        result = _identify_risk_factors(profile)

        # Should identify negative buffer risk
        assert any("Negative cash buffer" in risk for risk in result.risk_factors)

    def test_identify_risk_factors_low_job_certainty(self):
        """Test: Risk identified when job offer certainty is low."""

        profile = create_empty_profile("Test User")
        profile.final_cash_buffer = 20000
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.monthly_take_home_pay = 4000
        profile.monthly_healthcare_cost = 300
        profile.job_offer_certainty = 0.6
        profile.job_search_timeline_months = 6
        profile.monthly_cash_flow = [{"net_flow": 200}]

        result = _identify_risk_factors(profile)

        # Should identify low certainty risk
        assert any("uncertainty" in risk.lower() for risk in result.risk_factors)

    def test_buffer_simulator_monthly_breakdown(self):
        """Test: Each month's data is recorded correctly."""

        profile = create_empty_profile("Test User")
        profile.user_name = "Test User"
        profile.rank = "E-7"
        profile.years_of_service = 20
        profile.current_savings = 50000
        profile.monthly_expenses_mandatory = 3000
        profile.monthly_expenses_negotiable = 500
        profile.monthly_expenses_optional = 500
        profile.current_va_disability_rating = 30
        profile.target_city = "Denver, CO"
        profile.target_state = "CO"
        profile.job_search_timeline_months = 6
        profile.estimated_annual_salary = 100000
        profile.healthcare_plan_choice = "tricare_select"
        profile.job_offer_certainty = 0.9

        result = run_buffer_simulation(profile)

        # Check that monthly records have required fields
        for month_record in result.monthly_cash_flow:
            assert "month" in month_record
            assert "date" in month_record
            assert "income" in month_record
            assert "expenses" in month_record
            assert "net_flow" in month_record
            assert "cumulative_savings" in month_record


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
