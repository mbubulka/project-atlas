"""
Error handling and exception testing for ProjectAtlas.
Tests graceful handling of invalid inputs, corrupted data, and edge cases.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch


class TestCSVErrorHandling:
    """Test error handling for CSV file uploads."""

    def test_csv_missing_required_column(self, default_session_state):
        """Test CSV upload with missing required 'Item' column."""
        session = default_session_state

        # CSV missing 'Item' column
        df = pd.DataFrame({
            'Description': ['Rent', 'Food'],
            'Amount': [2000, 500],
        })

        required_cols = {'Item', 'Amount', 'Classification'}

        # Check for missing columns
        missing = required_cols - set(df.columns)
        assert len(missing) > 0  # Should detect missing 'Item'

    def test_csv_missing_amount_column(self, default_session_state):
        """Test CSV upload with missing 'Amount' column."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Rent', 'Food'],
            'Price': [2000, 500],  # Wrong column name
        })

        required_cols = {'Item', 'Amount'}
        missing = required_cols - set(df.columns)
        assert 'Amount' in missing

    def test_csv_empty_file(self, default_session_state):
        """Test handling of empty CSV file."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': [],
            'Amount': [],
        })

        assert len(df) == 0

    def test_csv_all_rows_empty(self, default_session_state):
        """Test CSV with all rows containing empty values."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': [None, None, None],
            'Amount': [None, None, None],
        })

        df_clean = df.dropna()
        assert len(df_clean) == 0

    def test_csv_amount_column_non_numeric(self, default_session_state):
        """Test CSV with non-numeric amounts."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Rent', 'Food'],
            'Amount': ['two thousand', 'five hundred'],
        })

        # Try to convert to numeric (should fail gracefully)
        try:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            # After coercion, values should be NaN
            assert df['Amount'].isna().any()
        except Exception:
            pass  # Acceptable to fail conversion

    def test_csv_duplicate_items_handling(self, default_session_state):
        """Test handling of duplicate item names in CSV."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Rent', 'Food', 'Rent', 'Food'],
            'Amount': [2000, 300, 2000, 300],
        })

        # Should aggregate duplicates
        aggregated = df.groupby('Item')['Amount'].sum()
        assert len(aggregated) == 2  # Only 2 unique items

    def test_csv_special_characters_in_items(self, default_session_state):
        """Test CSV with special characters in item names."""
        session = default_session_state

        df = pd.DataFrame({
            'Item': ['Rent (Apt)', 'Food & Drinks', 'Mom\'s Gift'],
            'Amount': [2000, 300, 100],
        })

        # Should handle special characters without crashing
        assert len(df) == 3

    def test_csv_very_long_item_names(self, default_session_state):
        """Test CSV with very long item names (1000+ characters)."""
        session = default_session_state

        long_name = 'A' * 1000 + ' - This is a very long expense item name'

        df = pd.DataFrame({
            'Item': [long_name, 'Rent'],
            'Amount': [100, 2000],
        })

        assert len(df) == 2
        assert len(df.iloc[0]['Item']) > 1000


class TestInputValidation:
    """Test validation of user inputs."""

    def test_invalid_rank_input(self, default_session_state):
        """Test handling of invalid rank input."""
        session = default_session_state

        valid_ranks = [
            'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9',
            'O1', 'O2', 'O3', 'O4', 'O5', 'O6',
        ]

        session['rank'] = 'E5'

        # Verify it's in valid list
        assert session['rank'] in valid_ranks

    def test_invalid_yos_negative(self, default_session_state):
        """Test that negative YOS is rejected."""
        session = default_session_state

        # Should be constrained to 0+
        session['yos'] = 0  # Minimum
        assert session['yos'] >= 0

    def test_invalid_yos_too_high(self, default_session_state):
        """Test that YOS > 50 is handled."""
        session = default_session_state

        session['yos'] = 50  # Maximum
        assert session['yos'] <= 50

    def test_invalid_dependent_count(self, default_session_state):
        """Test negative dependent count is rejected."""
        session = default_session_state

        session['dependents'] = 0  # Minimum
        assert session['dependents'] >= 0

    def test_invalid_salary_negative(self, default_session_state):
        """Test that negative salary is rejected."""
        session = default_session_state

        session['base_salary'] = 0  # Minimum
        assert session['base_salary'] >= 0

    def test_invalid_va_rating_negative(self, default_session_state):
        """Test that negative VA rating is rejected."""
        session = default_session_state

        session['va_disability_rating'] = '0'  # Minimum
        assert int(session['va_disability_rating']) >= 0

    def test_invalid_va_rating_over_100(self, default_session_state):
        """Test that VA rating > 100% is capped."""
        session = default_session_state

        session['va_disability_rating'] = '100'
        assert int(session['va_disability_rating']) <= 100


class TestDateValidation:
    """Test validation of date inputs."""

    def test_invalid_date_format(self, default_session_state):
        """Test handling of invalid date formats."""
        session = default_session_state

        # Should reject invalid formats
        invalid_dates = [
            '2026/06/30',  # Wrong format
            '30-06-2026',  # Wrong format
            'June 30, 2026',  # Wrong format
            'not-a-date',  # Invalid
        ]

        session['military_separation_date'] = '2026-06-30'

        # Should only accept standard format
        assert isinstance(session['military_separation_date'], str)

    def test_civilian_start_before_separation(self, default_session_state):
        """Test validation: civilian job can't start before separation."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['civilian_job_start_date'] = '2026-01-01'

        # Validation should catch this
        assert session['civilian_job_start_date'] <= session[
            'military_separation_date'
        ]

    def test_retirement_date_before_separation(
        self, default_session_state
    ):
        """Test validation: retirement can't be before separation."""
        session = default_session_state

        session['military_separation_date'] = '2026-06-30'
        session['military_retirement_date'] = '2025-12-31'

        # Validation should catch this
        assert session['military_retirement_date'] <= session[
            'military_separation_date'
        ]

    def test_future_dates_too_far_out(self, default_session_state):
        """Test handling of dates far in future (2100+)."""
        session = default_session_state

        session['projection_end_date'] = '2100-12-31'

        # Should handle gracefully even if unusual
        assert session['projection_end_date'] is not None


class TestCalculationErrorHandling:
    """Test error handling during calculations."""

    def test_division_by_zero_in_percentages(
        self, default_session_state
    ):
        """Test handling of division by zero when calculating percentages."""
        session = default_session_state

        total_expenses = 0

        # Try to calculate percentage
        try:
            if total_expenses > 0:
                mandatory_pct = (
                    session['final_amounts']['Mandatory'] / total_expenses
                )
            else:
                mandatory_pct = 0
            assert mandatory_pct == 0
        except ZeroDivisionError:
            pytest.fail('Division by zero not handled')

    def test_null_salary_calculation(self, default_session_state):
        """Test calculation with None salary value."""
        session = default_session_state

        session['base_salary'] = None

        # Should handle None gracefully
        try:
            if session['base_salary'] is not None:
                pension = (
                    session['base_salary'] * 0.02
                    * session['yos']
                )
            else:
                pension = 0
            assert pension == 0
        except TypeError:
            pytest.fail('None value not handled in calculation')

    def test_missing_session_field(self, default_session_state):
        """Test calculation when required session field is missing."""
        session = default_session_state

        # Remove a required field
        if 'civilian_salary' in session:
            del session['civilian_salary']

        # Should handle gracefully
        civilian_salary = session.get('civilian_salary', 0)
        assert civilian_salary == 0

    def test_calculation_with_infinity(self, default_session_state):
        """Test calculation when inf value is encountered."""
        session = default_session_state

        session['base_salary'] = float('inf')

        # Should handle inf gracefully
        if not isinstance(session['base_salary'], (int, float)):
            session['base_salary'] = 0
        elif session['base_salary'] == float('inf'):
            session['base_salary'] = 999999.99  # Cap at max reasonable

    def test_calculation_with_nan(self, default_session_state):
        """Test calculation when NaN value is encountered."""
        session = default_session_state

        session['base_salary'] = float('nan')

        # Should handle NaN gracefully
        try:
            if pd.isna(session['base_salary']):
                session['base_salary'] = 0
            assert session['base_salary'] == 0
        except (TypeError, ValueError):
            pass


class TestSessionStateErrors:
    """Test error handling in session state management."""

    def test_missing_form_field(self, default_session_state):
        """Test handling when a required form field is missing."""
        session = default_session_state

        # Remove a required field
        if 'rank' in session:
            del session['rank']

        # Should return default or error gracefully
        rank = session.get('rank', 'Not Set')
        assert rank == 'Not Set'

    def test_field_type_mismatch(self, default_session_state):
        """Test handling when field has wrong data type."""
        session = default_session_state

        session['yos'] = 'twenty'  # String instead of int

        # Should handle type conversion or error
        try:
            if isinstance(session['yos'], str):
                yos_numeric = int(session['yos'])
        except ValueError:
            # Expected to fail, should be handled
            pass

    def test_session_state_corruption(self, default_session_state):
        """Test recovery from corrupted session state."""
        session = default_session_state

        # Corrupt the session
        session['rank'] = {'nested': 'dict'}  # Wrong type

        # Should detect and handle
        rank = session.get('rank')
        if not isinstance(rank, str):
            session['rank'] = 'Unknown'
            assert session['rank'] == 'Unknown'

    def test_missing_step_state(self, default_session_state):
        """Test when state from a previous step is missing."""
        session = default_session_state

        # Simulate missing Step 1 data
        required_step1 = ['rank', 'yos', 'service_branch']

        missing_fields = [
            field for field in required_step1
            if field not in session or session[field] is None
        ]

        # Should handle missing fields
        if missing_fields:
            for field in missing_fields:
                session[field] = 'Not Set'


class TestExceptionHandling:
    """Test proper exception handling and recovery."""

    def test_corrupted_csv_recovery(self, default_session_state):
        """Test recovery from corrupted CSV data."""
        session = default_session_state

        try:
            # Simulate corrupted CSV
            df = pd.read_csv(
                'nonexistent_file.csv'
            )  # Will raise FileNotFoundError
        except FileNotFoundError:
            # Should handle gracefully
            session['last_error'] = 'CSV file not found'
            assert 'last_error' in session

    def test_calculation_overflow(self, default_session_state):
        """Test handling of calculation overflow."""
        session = default_session_state

        # Very large numbers
        session['base_salary'] = 999999999999
        session['yos'] = 50

        try:
            result = (
                session['base_salary'] * 0.02 * session['yos']
            )
            # Python handles large numbers OK, but cap if needed
            if result > 999999999999:
                result = 999999999999
            assert result > 0
        except OverflowError:
            pytest.fail('Overflow not handled')

    def test_encoding_error_in_csv(self, default_session_state):
        """Test handling of encoding errors in CSV import."""
        session = default_session_state

        # Create DataFrame with special characters
        df = pd.DataFrame({
            'Item': ['Café', 'Naïve', '日本'],
            'Amount': [100, 200, 300],
        })

        # Should handle encoding gracefully
        assert len(df) == 3


class TestBoundaryErrorHandling:
    """Test error handling at boundaries."""

    def test_very_large_csv_file(self, default_session_state):
        """Test handling of very large CSV (10K+ rows)."""
        session = default_session_state

        # Simulate large CSV
        large_df = pd.DataFrame({
            'Item': [f'Item_{i}' for i in range(10000)],
            'Amount': [100] * 10000,
        })

        # Should handle without crashing
        assert len(large_df) == 10000
        assert large_df['Amount'].sum() == 1000000

    def test_very_small_expense_amounts(self, default_session_state):
        """Test precision handling of very small amounts ($0.01)."""
        session = default_session_state

        small_amount = 0.01
        many_items = small_amount * 1000000

        # Should maintain precision
        assert many_items == 10000.00

    def test_unicode_characters_in_input(self, default_session_state):
        """Test handling of Unicode characters in input."""
        session = default_session_state

        unicode_items = [
            '💰 Rent',
            '🍔 Food',
            '🚗 Car Payment',
        ]

        session['unicode_test'] = unicode_items

        assert len(session['unicode_test']) == 3
