"""
Test suite for Project Atlas healthcare_model module.

Tests healthcare cost calculations and plan comparisons.
"""

import pytest

from src.data_models import create_empty_profile
from src.model_layer.healthcare_model import (
    _calculate_aca_cost,
    _calculate_tricare_cost,
    _calculate_va_health_cost,
    compare_healthcare_costs,
    estimate_healthcare_cost_scenarios,
)


class TestHealthcareModel:
    """Test suite for healthcare cost calculations."""

    def test_calculate_tricare_select_cost(self):
        """Test: Tricare Select annual cost calculation."""

        profile = create_empty_profile("Test User")
        profile.target_city = "Denver, CO"

        cost = _calculate_tricare_cost(profile, "tricare_select")

        # Should include copays but no enrollment fee
        assert cost > 0
        assert cost < 3000  # Reasonable upper bound for Tricare Select

    def test_calculate_tricare_prime_vs_select_costs(self):
        """Test: Tricare Prime and Select have meaningfully different costs.
        
        NOTE: Prime typically costs more for low utilization due to higher
        enrollment fee ($372 vs $181.92). For high utilization, Prime may be
        cheaper due to lower copays ($25-$38 vs $37-$51).
        """

        profile = create_empty_profile("Test User")
        profile.target_city = "Denver, CO"

        select_cost = _calculate_tricare_cost(profile, "tricare_select")
        prime_cost = _calculate_tricare_cost(profile, "tricare_prime")

        # Both costs should be positive and reasonable
        assert select_cost > 0, "Select cost should be positive"
        assert prime_cost > 0, "Prime cost should be positive"
        assert select_cost < 10000, "Select cost should be under $10,000 annually"
        assert prime_cost < 10000, "Prime cost should be under $10,000 annually"
        
        # Most important: Costs must be different (not the same)
        assert select_cost != prime_cost, "Prime and Select must have different costs"
        
        # For baseline utilization, Prime should be more expensive due to 
        # higher enrollment fee with limited utilization to offset it
        cost_difference = prime_cost - select_cost
        assert cost_difference > 0, (
            f"Prime (${prime_cost:.2f}) should be more expensive than "
            f"Select (${select_cost:.2f}) for baseline utilization"
        )

    def test_calculate_va_health_cost_high_rating(self):
        """Test: 50%+ VA rating gets free VA healthcare."""

        profile = create_empty_profile("Test User")
        profile.current_va_disability_rating = 50

        cost = _calculate_va_health_cost(profile)

        # Should be minimal (mostly free)
        assert cost < 100

    def test_calculate_va_health_cost_low_rating(self):
        """Test: 0-10% rating pays more for VA healthcare."""

        profile = create_empty_profile("Test User")
        profile.current_va_disability_rating = 0

        cost = _calculate_va_health_cost(profile)

        # Should be higher than high rating
        assert cost > 200

    def test_calculate_aca_cost_estimate(self):
        """Test: ACA cost estimate is reasonable."""

        profile = create_empty_profile("Test User")
        profile.target_city = "Austin, TX"

        cost = _calculate_aca_cost(profile)

        # Rough range for individual ACA coverage
        assert 8000 <= cost <= 15000

    def test_compare_healthcare_costs_returns_all_options(self):
        """Test: Comparison includes all available plan options."""

        profile = create_empty_profile("Test User")
        profile.current_va_disability_rating = 30
        profile.healthcare_plan_choice = "tricare_select"
        profile.target_city = "Denver, CO"

        result = compare_healthcare_costs(profile)

        comparison = result.metadata.get("healthcare_cost_comparison", {})

        # Should have at least Tricare options and ACA
        assert "tricare_select" in comparison
        assert "tricare_prime" in comparison
        assert "aca" in comparison

        # 30% rating qualifies for VA Health
        assert "va_health" in comparison

    def test_healthcare_cost_scenarios_healthy_patient(self):
        """Test: Healthy patient scenario has lower costs."""

        profile = create_empty_profile("Test User")
        profile.annual_healthcare_cost = 5000

        scenarios = estimate_healthcare_cost_scenarios(profile, healthy=True)

        # Healthy scenario should be optimistic
        assert scenarios["low"] < scenarios["mid"]
        assert scenarios["mid"] <= scenarios["high"]

    def test_healthcare_cost_scenarios_sick_patient(self):
        """Test: Sick patient scenario has higher costs."""

        profile = create_empty_profile("Test User")
        profile.annual_healthcare_cost = 5000

        scenarios = estimate_healthcare_cost_scenarios(profile, healthy=False)

        # Pessimistic scenario: costs increase
        assert scenarios["low"] <= scenarios["mid"]
        assert scenarios["mid"] <= scenarios["high"]

    def test_tricare_rates_validate_against_2025_official(self):
        """Test: TRICARE enrollment fees match official 2025 TRICARE.mil Group A rates.
        
        Official 2025 TRICARE rates (CY 2025, Group A - initial enlistment before Jan 1, 2018):
        - TRICARE Prime Individual: $372/year
        - TRICARE Prime Family: $744/year
        - TRICARE Select Individual: $181.92/year
        - TRICARE Select Family: $364.92/year
        
        Source: https://newsroom.tricare.mil/News/TRICARE-News/Article/3959222
        """
        from src.model_layer.config import TRICARE_PLANS

        # Validate individual enrollment fees
        assert TRICARE_PLANS["tricare_prime"].annual_enrollment_fee == 372, (
            "TRICARE Prime individual enrollment fee should be $372/year (2025)"
        )
        assert TRICARE_PLANS["tricare_select"].annual_enrollment_fee == 181.92, (
            "TRICARE Select individual enrollment fee should be $181.92/year (2025)"
        )

        # Validate copays match Table 4 from official source
        # Each plan should have distinct copay structures
        prime_primary = TRICARE_PLANS["tricare_prime"].primary_care_copay
        select_primary = TRICARE_PLANS["tricare_select"].primary_care_copay

        assert prime_primary == 25, "TRICARE Prime primary care should be $25"
        assert select_primary == 37, "TRICARE Select primary care should be $37"

        # Specialist copays
        assert TRICARE_PLANS["tricare_prime"].specialist_copay == 38
        assert TRICARE_PLANS["tricare_select"].specialist_copay == 51

        # Prime has NO deductible, Select does
        assert TRICARE_PLANS["tricare_prime"].annual_deductible == 0
        assert TRICARE_PLANS["tricare_select"].annual_deductible == 150


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
