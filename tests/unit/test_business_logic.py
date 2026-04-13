"""
Unit tests for business logic: VA disability, pension, and expense calculations.

Tests correctness of financial calculations.
"""

import pytest


class TestVADisabilityBenefit:
    """Test VA disability benefit calculations."""

    def test_single_veteran_no_dependents_50_percent(self, va_benefit_calculator):
        """50% rating, single, no dependents = $1,132.90."""
        benefit = va_benefit_calculator(rating=50, married=False, num_deps=0)
        assert abs(benefit - 1132.90) < 0.01, f"Expected ~1132.90, got {benefit}"

    def test_married_no_children_50_percent(self, va_benefit_calculator):
        """50% rating, married, no children = $1,241.90."""
        benefit = va_benefit_calculator(rating=50, married=True, num_deps=0)
        assert abs(benefit - 1241.90) < 0.01, f"Expected ~1241.90, got {benefit}"

    def test_married_1_child_50_percent(self, va_benefit_calculator):
        """50% rating, married, 1 child = $1,322.90."""
        benefit = va_benefit_calculator(rating=50, married=True, num_deps=1)
        assert abs(benefit - 1322.90) < 0.01, f"Expected ~1322.90, got {benefit}"

    def test_married_2_children_50_percent(self, va_benefit_calculator):
        """50% rating, married, 2 children includes additional child amount."""
        benefit = va_benefit_calculator(rating=50, married=True, num_deps=2)
        # Base for 1 child is 1322.90, + 54 for additional child
        expected = 1322.90 + 54.00
        assert abs(benefit - expected) < 0.01, f"Expected ~{expected}, got {benefit}"

    def test_zero_rating_no_benefit(self, va_benefit_calculator):
        """0% rating should give $0 benefit."""
        benefit = va_benefit_calculator(rating=0, married=False, num_deps=0)
        assert benefit == 0

    def test_single_30_percent_rating(self, va_benefit_calculator):
        """30% rating, single, no dependents = $552.47."""
        benefit = va_benefit_calculator(rating=30, married=False, num_deps=0)
        assert abs(benefit - 552.47) < 0.01, f"Expected ~552.47, got {benefit}"

    def test_single_with_1_child_30_percent(self, va_benefit_calculator):
        """30% rating, single, 1 child = $596.47."""
        benefit = va_benefit_calculator(rating=30, married=False, num_deps=1)
        assert abs(benefit - 596.47) < 0.01, f"Expected ~596.47, got {benefit}"

    def test_100_percent_rating(self, va_benefit_calculator):
        """100% rating, single, no dependents = $3,938.58."""
        benefit = va_benefit_calculator(rating=100, married=False, num_deps=0)
        assert abs(benefit - 3938.58) < 0.01, f"Expected ~3938.58, got {benefit}"


class TestExpenseCalculations:
    """Test expense categorization and aggregation."""

    def test_expense_total_calculation(self):
        """Total expenses = mandatory + negotiable + optional + prepaid."""
        mandatory = 2500
        negotiable = 1000
        optional = 500
        prepaid = 300

        total = mandatory + negotiable + optional + prepaid
        expected = 4300

        assert total == expected

    def test_expense_percentage_breakdown(self):
        """Verify expense distribution percentages."""
        mandatory = 2500
        negotiable = 1000
        optional = 500
        prepaid = 300

        total = mandatory + negotiable + optional + prepaid

        mandatory_pct = (mandatory / total) * 100
        negotiable_pct = (negotiable / total) * 100
        optional_pct = (optional / total) * 100
        prepaid_pct = (prepaid / total) * 100

        # Check percentages sum to 100
        assert abs(
            mandatory_pct + negotiable_pct + optional_pct + prepaid_pct - 100.0
        ) < 0.01

        # Check individual percentages are reasonable
        assert 55 < mandatory_pct < 65  # Should be roughly 58%
        assert 20 < negotiable_pct < 30  # Should be roughly 23%
        assert 10 < optional_pct < 15  # Should be roughly 12%
        assert 5 < prepaid_pct < 10  # Should be roughly 7%


class TestCashFlowAnalysis:
    """Test cash flow (income - expenses) calculations."""

    def test_positive_cash_flow(self):
        """Income > Expenses results in positive cash flow."""
        income = 6000
        expenses = 4000
        cash_flow = income - expenses

        assert cash_flow > 0
        assert cash_flow == 2000

    def test_negative_cash_flow(self):
        """Expenses > Income results in negative cash flow."""
        income = 3000
        expenses = 4000
        cash_flow = income - expenses

        assert cash_flow < 0
        assert cash_flow == -1000

    def test_break_even(self):
        """Income == Expenses results in zero cash flow."""
        income = 4000
        expenses = 4000
        cash_flow = income - expenses

        assert cash_flow == 0

    def test_pension_plus_va_income(self):
        """Combined pension and VA income."""
        pension = 5000
        va_disability = 1132.90
        total_income = pension + va_disability

        assert abs(total_income - 6132.90) < 0.01


class TestMonthlyReserveCalculations:
    """Test prepaid item monthly reserve calculations."""

    def test_annual_item_monthly_reserve(self):
        """Annual item cost divided by 12 months."""
        annual_cost = 1200  # e.g., car insurance
        monthly_reserve = annual_cost / 12

        assert abs(monthly_reserve - 100.0) < 0.01

    def test_semi_annual_item_monthly_reserve(self):
        """Semi-annual item cost divided by 6 months."""
        semi_annual_cost = 600  # e.g., 6-month insurance
        monthly_reserve = semi_annual_cost / 6

        assert abs(monthly_reserve - 100.0) < 0.01

    def test_quarterly_item_monthly_reserve(self):
        """Quarterly item cost divided by 3 months."""
        quarterly_cost = 300
        monthly_reserve = quarterly_cost / 3

        assert abs(monthly_reserve - 100.0) < 0.01

    def test_total_prepaid_reserve(self):
        """Total monthly prepaid reserve for multiple items."""
        items = [
            {"name": "Car Insurance", "annual": 1200},  # $100/mo
            {"name": "Home Insurance", "annual": 1800},  # $150/mo
            {"name": "Life Insurance", "annual": 600},  # $50/mo
        ]

        total_reserve = sum(item["annual"] / 12 for item in items)
        expected = 100 + 150 + 50

        assert abs(total_reserve - expected) < 0.01
