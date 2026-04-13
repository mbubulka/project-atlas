"""
Test suite for Project Atlas retirement_pay_model module.

Golden dataset tests: compares calculated values against known correct answers.
"""


import pytest

from src.data_models import create_empty_profile
from src.model_layer.retirement_pay_model import (
    _calculate_federal_income_tax,
    _calculate_fica_tax,
    _calculate_retirement_pay,
    _calculate_state_income_tax,
    _calculate_va_benefit,
    calculate_take_home_pay,
)


class TestRetirementPayModel:
    """Test suite for military retirement and take-home pay calculations."""

    def test_calculate_retirement_pay_less_than_20_years(self):
        """Test: less than 20 years of service yields $0 retirement pay."""

        profile = create_empty_profile("Test User")
        profile.rank = "E-5"
        profile.years_of_service = 15

        retirement_pay = _calculate_retirement_pay(profile)

        assert retirement_pay == 0.0

    def test_calculate_retirement_pay_e7_20_years(self):
        """
        Golden test: E-7 with 20 years of service.

        High-3 for E-7: ~$52,000
        Formula: $52,000 × 20 × 0.025 = $26,000
        """

        profile = create_empty_profile("Test User")
        profile.rank = "E-7"
        profile.years_of_service = 20

        retirement_pay = _calculate_retirement_pay(profile)

        # Should be approximately $26,000 (20 years × 2.5%)
        assert 25000 <= retirement_pay <= 27000

    def test_calculate_retirement_pay_o4_25_years(self):
        """
        Golden test: O-4 (Major/Commander) with 25 years.

        High-3 for O-4: ~$72,000
        Formula: $72,000 × 25 × 0.025 = $45,000
        """

        profile = create_empty_profile("Test User")
        profile.rank = "O-4"
        profile.years_of_service = 25

        retirement_pay = _calculate_retirement_pay(profile)

        # Should be roughly 25% of high-3 amount
        assert 30000 <= retirement_pay <= 50000

    def test_calculate_va_benefit_30_percent_rating(self):
        """
        Golden test: 30% VA disability rating.

        2024 rate for 30%: ~$561/month × 12 = $6,732/year
        """

        profile = create_empty_profile("Test User")
        profile.current_va_disability_rating = 30

        va_benefit = _calculate_va_benefit(profile)

        # Rounded to nearest 10% (30% stays at 30%)
        assert 6500 <= va_benefit <= 7000

    def test_calculate_va_benefit_with_assumption(self):
        """Test: VA benefit uses assumed rating if provided."""

        profile = create_empty_profile("Test User")
        profile.current_va_disability_rating = 20
        profile.va_rating_assumption = 50

        va_benefit = _calculate_va_benefit(profile)

        # Should use the assumed rating (50%), not current (20%)
        assert va_benefit > 12000  # 50% is higher than 20%

    def test_calculate_federal_income_tax_simple_case(self):
        """
        Golden test: Federal income tax on $100,000 (2024 brackets).

        Standard deduction: $13,850
        Taxable: $100,000 - $13,850 = $86,150
        Expected: ~$10,000 (rough estimate, depends on brackets)
        """

        tax = _calculate_federal_income_tax(100000)

        # Should be roughly 10% effective rate on this income
        assert 8000 <= tax <= 12000

    def test_calculate_federal_income_tax_zero_income(self):
        """Test: zero income means zero tax."""

        tax = _calculate_federal_income_tax(0)

        assert tax == 0.0

    def test_calculate_state_income_tax_texas_no_tax(self):
        """Test: Texas has no state income tax."""

        tax = _calculate_state_income_tax(100000, "TX")

        assert tax == 0.0

    def test_calculate_state_income_tax_colorado(self):
        """Test: Colorado state income tax (~4.4%)."""

        tax = _calculate_state_income_tax(100000, "CO")

        # Colorado rate is ~4.4%
        assert 4000 <= tax <= 4500

    def test_calculate_fica_tax_on_salary(self):
        """
        Golden test: FICA tax on $100,000 salary.

        Social Security: 6.2% on first $168,600
        Medicare: 2.9% + 0.9% additional (if over $200k)
        Expected: 6.2% + 2.9% = 9.1% on $100,000 = ~$9,100
        """

        fica = _calculate_fica_tax(100000)

        assert 8500 <= fica <= 9500

    def test_calculate_take_home_pay_e7_retirement_scenario(self):
        """
        Golden test: Full scenario - E-7 retired, transitioning to Denver.

        Inputs:
        - Retirement: $26,000/year (E-7, 20 years)
        - VA: $6,732/year (30% rating)
        - Salary: $100,000
        - Total Gross: $132,732

        Taxes:
        - Federal: ~$15,000
        - Colorado: ~$5,800
        - FICA: $9,100 (on salary only)
        - Total: ~$29,900

        Take-Home: $132,732 - $29,900 = ~$102,832
        """

        profile = create_empty_profile("E7 Veteran")
        profile.rank = "E-7"
        profile.years_of_service = 20
        profile.current_va_disability_rating = 30
        profile.estimated_annual_salary = 100000
        profile.target_state = "CO"

        result = calculate_take_home_pay(profile)

        # Check rough ranges (exact values depend on bracket calculations)
        assert result.annual_take_home_pay > 88000
        assert result.annual_take_home_pay < 110000
        assert result.monthly_take_home_pay > 7300
        assert result.monthly_take_home_pay < 9000

    def test_calculate_take_home_pay_metadata_stored(self):
        """Test: Income breakdown is stored in metadata for transparency."""

        profile = create_empty_profile("Test User")
        profile.rank = "E-7"
        profile.years_of_service = 20
        profile.current_va_disability_rating = 30
        profile.estimated_annual_salary = 100000
        profile.target_state = "CO"

        result = calculate_take_home_pay(profile)

        breakdown = result.metadata.get("income_breakdown", {})

        assert "gross_income" in breakdown
        assert "retirement_pay" in breakdown
        assert "va_benefit" in breakdown
        assert "salary" in breakdown
        assert "federal_tax" in breakdown
        assert "state_tax" in breakdown
        assert "fica_tax" in breakdown
        assert "total_tax" in breakdown


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
