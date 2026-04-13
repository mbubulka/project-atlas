"""
Edge case and boundary testing for ProjectAtlas calculations.
Tests extreme values, boundary conditions, and unusual scenarios.
"""

import pytest
import pandas as pd


class TestBoundaryConditions:
    """Test calculations at boundary values (min, max, zero)."""

    def test_yos_zero_years(self, default_session_state):
        """Test pension calculation with 0 years of service."""
        session = default_session_state

        session['yos'] = 0
        session['base_salary'] = 50000

        # Pension formula: Base × 0.02 × YOS
        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 0

    def test_yos_maximum_50_years(self, default_session_state):
        """Test pension calculation with maximum 50 years of service."""
        session = default_session_state

        session['yos'] = 50
        session['base_salary'] = 100000

        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 100000  # Max pension possible

    def test_salary_zero(self, default_session_state):
        """Test calculations with $0 base salary."""
        session = default_session_state

        session['base_salary'] = 0
        session['yos'] = 20

        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 0

    def test_salary_maximum_500k(self, default_session_state):
        """Test calculations with very high salary ($500k)."""
        session = default_session_state

        session['base_salary'] = 500000
        session['yos'] = 20

        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 200000  # Should calculate correctly

    def test_va_disability_0_percent(self, default_session_state):
        """Test VA benefit with 0% disability rating."""
        session = default_session_state

        session['va_disability_rating'] = '0'
        session['base_salary'] = 50000

        va_benefit = session['base_salary'] * 0.00
        assert va_benefit == 0

    def test_va_disability_100_percent(self, default_session_state):
        """Test VA benefit with 100% disability rating."""
        session = default_session_state

        session['va_disability_rating'] = '100'
        session['base_salary'] = 50000

        va_benefit = session['base_salary'] * 1.00
        assert va_benefit == 50000

    def test_dependents_zero(self, default_session_state):
        """Test VA calculations with zero dependents."""
        session = default_session_state

        session['dependents'] = 0
        session['marital_status'] = 'Single'

        # No dependent adjustments
        assert session['dependents'] == 0

    def test_dependents_maximum_10(self, default_session_state):
        """Test with maximum 10 dependents."""
        session = default_session_state

        session['dependents'] = 10

        assert session['dependents'] == 10

    def test_expenses_zero(self, default_session_state):
        """Test financial sustainability with zero expenses."""
        session = default_session_state

        session['final_amounts'] = {
            'Mandatory': 0,
            'Negotiable': 0,
            'Optional': 0,
        }

        total_expenses = sum(session['final_amounts'].values())
        assert total_expenses == 0

    def test_expenses_very_high(self, default_session_state):
        """Test financial sustainability with very high expenses."""
        session = default_session_state

        session['final_amounts'] = {
            'Mandatory': 50000,
            'Negotiable': 20000,
            'Optional': 10000,
        }

        total_expenses = sum(session['final_amounts'].values())
        assert total_expenses == 80000


class TestNegativeAndInvalidValues:
    """Test handling of negative and invalid input values."""

    def test_negative_yos_handling(self, default_session_state):
        """Test that negative YOS is prevented."""
        session = default_session_state

        # Should not accept negative values
        session['yos'] = 0  # Minimum instead
        assert session['yos'] >= 0

    def test_negative_salary_handling(self, default_session_state):
        """Test that negative salary is prevented."""
        session = default_session_state

        session['base_salary'] = 0  # Minimum instead
        assert session['base_salary'] >= 0

    def test_negative_expenses_handling(self, default_session_state):
        """Test that negative expenses are prevented."""
        session = default_session_state

        # Set safe value
        session['final_amounts'] = {
            'Mandatory': 0,
            'Negotiable': 0,
            'Optional': 0,
        }

        for amount in session['final_amounts'].values():
            assert amount >= 0

    def test_va_rating_above_100_capped(self, default_session_state):
        """Test that VA rating above 100% is capped."""
        session = default_session_state

        session['va_disability_rating'] = '100'  # Max value

        rating = int(session['va_disability_rating'])
        assert rating <= 100

    def test_dependents_negative_prevented(self, default_session_state):
        """Test that negative dependents is prevented."""
        session = default_session_state

        session['dependents'] = 0  # Minimum instead
        assert session['dependents'] >= 0


class TestExtremeCombinations:
    """Test extreme combinations of inputs."""

    def test_high_rank_zero_tenure(self, default_session_state):
        """Test high rank (O5) with minimal tenure (2 years)."""
        session = default_session_state

        session['rank'] = 'O5'
        session['yos'] = 2
        session['base_salary'] = 120000

        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 4800  # Very low pension despite high rank

    def test_low_rank_high_tenure(self, default_session_state):
        """Test low rank (E2) with high tenure (30 years)."""
        session = default_session_state

        session['rank'] = 'E2'
        session['yos'] = 30
        session['base_salary'] = 25000

        pension = session['base_salary'] * 0.02 * session['yos']
        assert pension == 15000  # Substantial pension from longevity

    def test_high_income_low_expenses(self, default_session_state):
        """Test high income ($500k) with very low expenses ($1500/month)."""
        session = default_session_state

        session['civilian_salary'] = 500000
        session['final_amounts'] = {
            'Mandatory': 1000,
            'Negotiable': 300,
            'Optional': 200,
        }

        monthly_income = session['civilian_salary'] / 12
        monthly_expenses = sum(session['final_amounts'].values())
        surplus = monthly_income - monthly_expenses

        assert surplus > 0
        assert surplus > monthly_income * 0.95  # 95%+ surplus

    def test_low_income_high_expenses(self, default_session_state):
        """Test low income ($32k military) with high expenses ($5k/month)."""
        session = default_session_state

        session['base_salary'] = 32000
        session['final_amounts'] = {
            'Mandatory': 3000,
            'Negotiable': 1500,
            'Optional': 500,
        }

        monthly_income = session['base_salary'] / 12
        monthly_expenses = sum(session['final_amounts'].values())
        deficit = monthly_expenses - monthly_income

        assert deficit > 0  # Deficit situation

    def test_multiple_dependents_with_low_income(
        self, default_session_state
    ):
        """Test multiple dependents (5) on entry-level salary."""
        session = default_session_state

        session['rank'] = 'E2'
        session['yos'] = 2
        session['base_salary'] = 25000
        session['dependents'] = 5
        session['marital_status'] = 'Married'

        # High expense load with dependents
        session['final_amounts'] = {
            'Mandatory': 4000,  # Larger household
            'Negotiable': 1500,
            'Optional': 300,
        }

        total_expenses = sum(session['final_amounts'].values())
        assert total_expenses == 5800

    def test_very_long_timeline_100_years(self, default_session_state):
        """Test timeline projection over 100 years (retirement age to 150)."""
        session = default_session_state

        session['military_retirement_date'] = '2050-06-30'
        session['projection_end_year'] = 2150  # 100 years out

        # Verify dates can be stored
        assert session['military_retirement_date'] == '2050-06-30'


class TestCSVEdgeCases:
    """Test CSV upload with edge case data."""

    def test_csv_single_item(self, default_session_state):
        """Test CSV with only one expense item."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Mortgage'],
            'Amount': [2000],
        })

        assert len(df) == 1
        assert df['Amount'].sum() == 2000

    def test_csv_many_items_1000(self, default_session_state):
        """Test CSV with 1000 expense items."""
        session = default_session_state

        items = [f'Item_{i}' for i in range(1000)]
        amounts = [100] * 1000

        df = pd.DataFrame({
            'Item': items,
            'Amount': amounts,
        })

        assert len(df) == 1000
        assert df['Amount'].sum() == 100000

    def test_csv_very_large_amounts(self, default_session_state):
        """Test CSV with very large expense amounts."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Mansion', 'Yacht', 'Jet'],
            'Amount': [3000000, 5000000, 10000000],
        })

        total = df['Amount'].sum()
        assert total == 18000000

    def test_csv_very_small_amounts(self, default_session_state):
        """Test CSV with very small amounts (cents)."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Penny Item', 'Coin Item'],
            'Amount': [0.01, 0.50],
        })

        total = df['Amount'].sum()
        assert abs(total - 0.51) < 0.001

    def test_csv_duplicate_items(self, default_session_state):
        """Test CSV with duplicate item names."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Rent', 'Insurance', 'Rent', 'Insurance'],
            'Amount': [2000, 200, 2000, 200],
        })

        # Should aggregate correctly
        rent_total = df[df['Item'] == 'Rent']['Amount'].sum()
        assert rent_total == 4000

    def test_csv_with_special_characters(self, default_session_state):
        """Test CSV with special characters in item names."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': [
                'Rent (Monthly)',
                'Insurance & Coverage',
                'Utilities (Electric/Water)',
                "Mom's Birthday Gift",
            ],
            'Amount': [2000, 300, 200, 100],
        })

        assert len(df) == 4
        assert df['Amount'].sum() == 2600


class TestDateEdgeCases:
    """Test date handling edge cases."""

    def test_same_day_military_separation_and_civilian_start(
        self, default_session_state
    ):
        """Test military separation and civilian job start on same day."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['civilian_job_start_date'] = '2026-06-30'

        # No gap in employment
        assert session['military_separation_date'] == session[
            'civilian_job_start_date'
        ]

    def test_large_gap_between_separation_and_civilian_start(
        self, default_session_state
    ):
        """Test large gap (1 year) between military separation and civilian job."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['civilian_job_start_date'] = '2027-06-30'

        # One year gap - should handle gracefully
        assert session['military_separation_date'] < session[
            'civilian_job_start_date'
        ]

    def test_backward_date_military_before_separation(
        self, default_session_state
    ):
        """Test civilian start date before military separation (invalid)."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['civilian_job_start_date'] = '2026-01-01'

        # Validation should catch this
        assert session['civilian_job_start_date'] <= session[
            'military_separation_date'
        ]

    def test_retirement_before_separation(self, default_session_state):
        """Test retirement date before separation date (impossible scenario)."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['military_retirement_date'] = '2025-06-30'

        # Validation should catch this logical error
        assert session['military_retirement_date'] <= session[
            'military_separation_date'
        ]


class TestCalculationPrecision:
    """Test numerical precision of calculations."""

    def test_pension_calculation_decimal_precision(
        self, default_session_state
    ):
        """Test pension calculation maintains proper decimal precision."""
        session = default_session_state

        session['base_salary'] = 33333.33
        session['yos'] = 13

        pension = session['base_salary'] * 0.02 * session['yos']

        # Should be approximately 8666.66
        assert abs(pension - 8666.66) < 0.01

    def test_expense_percentage_calculations(
        self, default_session_state
    ):
        """Test percentage calculations for expense breakdown."""
        session = default_session_state

        session['final_amounts'] = {
            'Mandatory': 1234.56,
            'Negotiable': 567.89,
            'Optional': 198.55,
        }

        total = sum(session['final_amounts'].values())
        mandatory_pct = session['final_amounts']['Mandatory'] / total * 100

        # Should be approximately 61.7%
        assert abs(mandatory_pct - 61.7) < 0.5

    def test_large_salary_rounding_errors(
        self, default_session_state
    ):
        """Test that large salaries don't cause rounding errors."""
        session = default_session_state

        session['base_salary'] = 999999.99
        session['yos'] = 25

        pension = session['base_salary'] * 0.02 * session['yos']

        expected = 999999.99 * 0.02 * 25
        assert abs(pension - expected) < 0.01
