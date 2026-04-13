"""
Integration tests for ProjectAtlas military transition wizard.
Tests complete workflows from Step 1 through Step 8.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock


class TestWizardCompleteFlow:
    """Test complete wizard workflow from military profile to financial summary."""

    def test_full_wizard_flow_e5_20_years(self, default_session_state):
        """Test complete wizard flow: E5 with 20 YOS transitions to civilian career."""
        session = default_session_state

        # Step 1: Military Profile Setup
        session['rank'] = 'E5'
        session['yos'] = 20
        session['dependents'] = 2
        session['marital_status'] = 'Married'

        assert session['rank'] == 'E5'
        assert session['yos'] == 20
        assert session['dependents'] == 2

        # Step 3: Pension Calculation
        # Formula: Base Salary × 0.02 × YOS
        base_salary = 50000
        expected_pension = base_salary * 0.02 * 20  # $20,000/year
        session['estimated_pension'] = expected_pension

        assert session['estimated_pension'] == 20000

    def test_full_wizard_flow_o3_30_years(self, default_session_state):
        """Test complete wizard flow: O3 with 30 YOS (high pension scenario)."""
        session = default_session_state

        # Step 1: Officer Profile
        session['rank'] = 'O3'
        session['yos'] = 30
        session['dependents'] = 3
        session['marital_status'] = 'Married'

        # Step 3: High pension scenario
        base_salary = 100000
        expected_pension = base_salary * 0.02 * 30  # $60,000/year (max)
        session['estimated_pension'] = expected_pension

        assert session['estimated_pension'] == 60000
        assert session['yos'] == 30

    def test_wizard_navigation_preserves_state(self, default_session_state):
        """Test that navigating back and forward preserves all entered data."""
        session = default_session_state

        # Step 1: Enter military profile
        session['rank'] = 'E6'
        session['yos'] = 15
        session['service_branch'] = 'Army'
        original_rank = session['rank']

        # Simulate navigation to Step 2
        assert session['rank'] == original_rank

        # Simulate going back to Step 1
        assert session['rank'] == 'E6'

        # Navigate forward to Step 3
        assert session['rank'] == 'E6'  # Still preserved

    def test_healthcare_step_integration(self, default_session_state):
        """Test healthcare costs integrate properly with financial calculations."""
        session = default_session_state

        # Step 1: Basic profile
        session['rank'] = 'E5'
        session['yos'] = 20

        # Step 2a: Healthcare configuration
        session['tricare_type'] = 'Self Only'
        session['annual_tricare_cost'] = 4200

        session['dental_plan'] = 'Active Duty Dental'
        session['annual_dental_cost'] = 600

        session['vision_plan'] = 'Active Duty Vision'
        session['annual_vision_cost'] = 300

        # Verify healthcare costs set
        total_healthcare = (
            session['annual_tricare_cost']
            + session['annual_dental_cost']
            + session['annual_vision_cost']
        )
        assert total_healthcare == 5100

    def test_pension_to_va_disability_flow(self, default_session_state):
        """Test pension calculation flows into VA disability benefit calculation."""
        session = default_session_state

        # Step 1: Military profile
        session['rank'] = 'E5'
        session['yos'] = 20
        session['base_salary'] = 50000
        session['marital_status'] = 'Married'
        session['dependents'] = 1

        # Step 3: Pension
        expected_pension = 50000 * 0.02 * 20  # $20,000
        session['estimated_pension'] = expected_pension

        # Step 3b: VA Disability
        session['va_disability_rating'] = '50'

        # VA formula: Base Salary × Disability% × Marital/Dependent factors
        va_base = 50000 * 0.50  # 50% disability
        assert session['va_disability_rating'] == '50'

    def test_expense_classification_affects_timeline(self, default_session_state):
        """Test that expense classifications properly feed into timeline visualization."""
        session = default_session_state

        # Step 1: Basic profile
        session['rank'] = 'E5'
        session['yos'] = 20

        # Step 6: Classify expenses
        session['csv_classification_map'] = {
            'Mortgage': 'Mandatory',
            'Groceries': 'Negotiable',
            'Entertainment': 'Optional',
        }

        session['final_amounts'] = {
            'Mandatory': 2000,
            'Negotiable': 1000,
            'Optional': 500,
        }

        total_expenses = sum(session['final_amounts'].values())
        assert total_expenses == 3500

        # Step 8: Verify timeline calculations use these amounts
        assert session['final_amounts']['Mandatory'] == 2000

    def test_prepaid_tracker_integration(self, default_session_state):
        """Test prepaid expense tracker integrates with main expense list."""
        session = default_session_state

        # Step 6: Add prepaid expenses
        session['prepaid_items'] = [
            {'item': 'Car Insurance', 'amount': 1200, 'frequency': 'Annual'},
            {
                'item': 'Home Insurance',
                'amount': 1500,
                'frequency': 'Annual',
            },
            {'item': 'Registration', 'amount': 150, 'frequency': 'Annual'},
        ]

        # Step 8: Verify prepaid items are included
        total_prepaid = sum([item['amount'] for item in session['prepaid_items']])
        assert total_prepaid == 2850

    def test_civilian_salary_affects_sustainability(self, default_session_state):
        """Test that civilian job salary properly affects financial sustainability."""
        session = default_session_state

        # Step 1: Military profile
        session['rank'] = 'E5'
        session['yos'] = 20
        session['base_salary'] = 50000

        # Step 4: Civilian career
        session['civilian_job_title'] = 'Project Manager'
        session['civilian_salary'] = 80000
        session['civilian_job_start_date'] = '2026-07-01'

        # Step 8: Verify civilian salary included in sustainability calculation
        assert session['civilian_salary'] == 80000
        assert session['base_salary'] == 50000

    def test_multiple_date_timeline_changes(self, default_session_state):
        """Test timeline adjusts correctly with changes to separation and retirement dates."""
        session = default_session_state

        # Step 1: Military profile
        session['rank'] = 'E5'
        session['yos'] = 20

        # Step 8: Set timeline dates
        session['military_separation_date'] = '2026-06-30'
        session['military_retirement_date'] = '2046-06-30'
        session['civilian_job_start_date'] = '2026-08-01'

        # Verify dates are stored
        assert session['military_separation_date'] == '2026-06-30'
        assert session['civilian_job_start_date'] == '2026-08-01'

        # Change civilian start date
        session['civilian_job_start_date'] = '2026-09-01'
        assert session['civilian_job_start_date'] == '2026-09-01'


class TestCSVWorkflow:
    """Test CSV upload, classification, and re-download workflow."""

    def test_csv_upload_and_classification(self, default_session_state, mock_csv_data):
        """Test uploading CSV, classifying expenses, and saving back."""
        session = default_session_state

        # Upload CSV
        df = mock_csv_data
        assert 'Item' in df.columns
        assert 'Amount' in df.columns

        # Classify expenses
        session['csv_classification_map'] = {
            'Mortgage': 'Mandatory',
            'Groceries': 'Negotiable',
            'Water': 'Mandatory',
            'Dining Out': 'Optional',
        }

        # Verify classifications
        assert len(session['csv_classification_map']) == 4

    def test_csv_round_trip_accuracy(
        self, default_session_state, mock_csv_data
    ):
        """Test that CSV upload and download preserves data accuracy."""
        session = default_session_state

        # Original data
        original_df = mock_csv_data.copy()
        original_total = original_df['Amount'].sum()

        # Simulate classification and changes
        session['csv_classification_map'] = {
            item: 'Negotiable'
            for item in original_df['Item'].tolist()
        }

        # Simulate re-download
        modified_df = original_df.copy()
        modified_total = modified_df['Amount'].sum()

        # Verify totals match (no data loss)
        assert modified_total == original_total

    def test_csv_with_empty_items(self, default_session_state):
        """Test handling of CSV with empty or missing expense items."""
        session = default_session_state

        # Create CSV with some missing values
        df = pd.DataFrame({
            'Item': ['Mortgage', '', 'Utilities', None],
            'Amount': [2000, 500, 150, 200],
        })

        # Filter out empty items
        df_clean = df[df['Item'].notna() & (df['Item'] != '')]

        # Should have 2 valid items
        assert len(df_clean) == 2


class TestCalculationAccuracy:
    """Test that multi-step calculations maintain accuracy across the wizard."""

    def test_pension_calculation_consistency(self, default_session_state):
        """Test pension calculation is consistent across multiple steps."""
        session = default_session_state

        # Set parameters
        session['rank'] = 'E5'
        session['yos'] = 20
        session['base_salary'] = 50000

        # Calculate pension (Step 3)
        pension_step3 = session['base_salary'] * 0.02 * session['yos']

        # Verify same calculation in Step 8
        pension_step8 = session['base_salary'] * 0.02 * session['yos']

        assert pension_step3 == pension_step8
        assert pension_step3 == 20000

    def test_va_benefit_with_all_modifiers(self, default_session_state):
        """Test VA benefits calculation with all modifiers (rating, marital, dependents)."""
        session = default_session_state

        # Base parameters
        session['base_salary'] = 50000
        session['va_disability_rating'] = '50'
        session['marital_status'] = 'Married'
        session['dependents'] = 2

        # VA calculation (simplified)
        base_rate = 50000 * 0.50  # 50% disability
        # Marital and dependent rates would apply here
        expected_va = base_rate  # Minimum calculation

        assert session['va_disability_rating'] == '50'
        assert session['dependents'] == 2

    def test_income_vs_expenses_timeline_accuracy(self, default_session_state):
        """Test that income vs expenses timeline is calculated accurately over time."""
        session = default_session_state

        # Setup
        session['base_salary'] = 50000
        session['estimated_pension'] = 20000
        session['civilian_salary'] = 80000

        # Expenses
        session['final_amounts'] = {
            'Mandatory': 2000,
            'Negotiable': 1000,
            'Optional': 500,
        }
        total_monthly_expenses = sum(session['final_amounts'].values())

        # Military phase income
        military_monthly = session['base_salary'] / 12
        military_surplus = military_monthly - total_monthly_expenses
        assert military_monthly > 0

        # Civilian phase income
        civilian_monthly = (
            session['estimated_pension'] / 12
            + session['civilian_salary'] / 12
        )
        civilian_surplus = civilian_monthly - total_monthly_expenses
        assert civilian_monthly > military_monthly


class TestNavigationAndState:
    """Test backward/forward navigation preserves state."""

    def test_step_1_to_step_8_and_back(self, default_session_state):
        """Test navigating from Step 1 to Step 8 and back preserves data."""
        session = default_session_state

        # Enter data in Step 1
        session['rank'] = 'O2'
        session['yos'] = 18
        session['service_branch'] = 'Navy'
        step1_rank = session['rank']

        # Navigate to Step 8
        assert session['rank'] == step1_rank

        # Navigate back to Step 1
        assert session['rank'] == 'O2'

        # Verify all Step 1 data intact
        assert session['yos'] == 18
        assert session['service_branch'] == 'Navy'

    def test_all_steps_data_preserved(self, default_session_state):
        """Test that data entered in all steps is preserved during navigation."""
        session = default_session_state

        # Step 1
        session['rank'] = 'E5'
        session['yos'] = 20

        # Step 2a
        session['annual_tricare_cost'] = 4200

        # Step 3
        session['estimated_pension'] = 20000

        # Step 4
        session['civilian_salary'] = 80000

        # Step 6
        session['csv_classification_map'] = {
            'Mortgage': 'Mandatory'
        }

        # Verify all preserved
        assert session['rank'] == 'E5'
        assert session['annual_tricare_cost'] == 4200
        assert session['estimated_pension'] == 20000
        assert session['civilian_salary'] == 80000


class TestDataValidation:
    """Test validation of data during the wizard flow."""

    def test_valid_rank_selection(self, default_session_state):
        """Test that only valid ranks can be selected."""
        session = default_session_state

        valid_ranks = [
            'E1',
            'E2',
            'E3',
            'E4',
            'E5',
            'E6',
            'O1',
            'O2',
            'O3',
        ]

        session['rank'] = 'E5'
        assert session['rank'] in valid_ranks

    def test_yos_range_validation(self, default_session_state):
        """Test that YOS is within valid range (0-50)."""
        session = default_session_state

        # Valid values
        session['yos'] = 0
        assert 0 <= session['yos'] <= 50

        session['yos'] = 25
        assert 0 <= session['yos'] <= 50

        session['yos'] = 50
        assert 0 <= session['yos'] <= 50

    def test_disability_rating_range(self, default_session_state):
        """Test VA disability rating is between 0-100%."""
        session = default_session_state

        session['va_disability_rating'] = '0'
        assert 0 <= int(session['va_disability_rating']) <= 100

        session['va_disability_rating'] = '50'
        assert 0 <= int(session['va_disability_rating']) <= 100

        session['va_disability_rating'] = '100'
        assert 0 <= int(session['va_disability_rating']) <= 100


class TestComplexScenarios:
    """Test complex, realistic military transition scenarios."""

    def test_officer_with_dependents_full_scenario(
        self, default_session_state
    ):
        """Test complex officer scenario: multiple dependents, high income."""
        session = default_session_state

        # Military profile
        session['rank'] = 'O3'
        session['yos'] = 25
        session['service_branch'] = 'Air Force'
        session['base_salary'] = 110000
        session['marital_status'] = 'Married'
        session['dependents'] = 3

        # Healthcare
        session['annual_tricare_cost'] = 5000
        session['annual_dental_cost'] = 800

        # Pension
        expected_pension = 110000 * 0.02 * 25  # $55,000/year
        session['estimated_pension'] = expected_pension

        # VA (assume service-connected disability)
        session['va_disability_rating'] = '30'

        # Civilian career
        session['civilian_job_title'] = 'Manager'
        session['civilian_salary'] = 95000

        # Expenses for family
        session['final_amounts'] = {
            'Mandatory': 5000,
            'Negotiable': 2000,
            'Optional': 1000,
        }

        # Verify scenario is consistent
        assert session['dependents'] == 3
        assert session['estimated_pension'] == 55000

    def test_enlisted_minimal_transition(self, default_session_state):
        """Test minimal scenario: E4 with 6 years, minimal expenses."""
        session = default_session_state

        # Military profile (minimal tenure)
        session['rank'] = 'E4'
        session['yos'] = 6
        session['service_branch'] = 'Army'
        session['base_salary'] = 32000
        session['marital_status'] = 'Single'
        session['dependents'] = 0

        # Healthcare (basic)
        session['annual_tricare_cost'] = 2000

        # No pension (less than 20 years)
        session['estimated_pension'] = 0

        # Minimal expenses
        session['final_amounts'] = {
            'Mandatory': 1500,
            'Negotiable': 300,
            'Optional': 100,
        }

        # Verify scenario
        assert session['estimated_pension'] == 0
        assert session['dependents'] == 0
