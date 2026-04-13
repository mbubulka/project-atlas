"""
Project Atlas: Personal Transition Simulator

Main entry point for the Streamlit application.

This is the UI orchestrator that manages:
- File uploads
- User inputs
- Session state management
- Model execution
- Result display
"""

import streamlit as st
import pandas as pd
import logging
import json
import os
from typing import Optional
from datetime import datetime

from src.data_models import TransitionProfile, create_empty_profile
from src.data_layer.loader import clean_transaction_csv, DataCleaningError
from src.model_layer.buffer_simulator import run_buffer_simulation
from src.model_layer.state_taxes import calculate_state_tax, get_all_states_list
from src.ui_layer.dashboard import (
    display_dashboard,
    display_empty_state,
    display_scenario_comparison,
)
from src.ui_layer.ai_chat_interface import render_ai_chat_interface
from src.ui_layer.classification_adjuster import display_classification_adjuster


# Configure Streamlit page
st.set_page_config(
    page_title="Project Atlas",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# ========== SCENARIO SAVE/LOAD FUNCTIONS ==========
def get_scenarios_directory():
    """Create and return the scenarios directory path."""
    scenarios_dir = os.path.join(os.path.dirname(__file__), 'scenarios')
    os.makedirs(scenarios_dir, exist_ok=True)
    return scenarios_dir


def get_all_scenarios():
    """Get list of all saved scenario filenames."""
    scenarios_dir = get_scenarios_directory()
    try:
        files = [f.replace('.json', '') for f in os.listdir(scenarios_dir) if f.endswith('.json')]
        return sorted(files)
    except:
        return []


def get_saveable_session_keys():
    """Return list of session state keys that should be saved in scenarios."""
    return [
        # User Profile
        'user_rank', 'user_years_of_service', 'user_career_field', 
        'user_separation_date', 'user_marital_status', 'user_dependents', 
        'user_service_branch',
        # Income Tab
        'military_pension', 'va_rating', 'va_dependent_status_key', 'va_monthly_custom',
        'use_calculated_va', 'sbp_checkbox', 'new_job_salary_annual', 'job_start_month',
        'rental_income_monthly', 'spouse_income_monthly', 'other_income_monthly',
        'current_income_method', 'current_takehome', 'current_annual_pretax',
        'other_deductions', 'filing_status', 'state', 'savings_available',
        # Healthcare Tab
        'medical_plan', 'medical_dependents_status', 'vision_plan', 'dental_plan',
        # Education Tab
        'gi_program_type', 'school_location_preset', 'school_custom_bah', 'gi_months_used',
        'ruskin_approved', 'ruskin_additional_months', 'bah_custom',
        'salary_education', 'salary_expectation',
        # What-If Tab
        'salary_prediction',
        # VA Disability
        'va_disability_scenario',
    ]


def save_scenario(scenario_name: str):
    """Save current scenario to JSON file."""
    scenario_data = {}
    for key in get_saveable_session_keys():
        if key in st.session_state:
            value = st.session_state[key]
            # Convert date objects to strings for JSON serialization
            if hasattr(value, 'isoformat'):
                scenario_data[key] = value.isoformat()
            else:
                scenario_data[key] = value
    
    scenarios_dir = get_scenarios_directory()
    filepath = os.path.join(scenarios_dir, f'{scenario_name}.json')
    
    try:
        with open(filepath, 'w') as f:
            json.dump(scenario_data, f, indent=2)
        return True, f"Scenario '{scenario_name}' saved successfully!"
    except Exception as e:
        return False, f"Error saving scenario: {str(e)}"


def load_scenario(scenario_name: str):
    """Load scenario from JSON file into session state."""
    scenarios_dir = get_scenarios_directory()
    filepath = os.path.join(scenarios_dir, f'{scenario_name}.json')
    
    try:
        with open(filepath, 'r') as f:
            scenario_data = json.load(f)
        
        # Load data into session state
        for key, value in scenario_data.items():
            # Try to convert ISO date strings back to date objects
            if isinstance(value, str) and key.endswith('_date'):
                try:
                    from datetime import datetime as dt
                    st.session_state[key] = dt.fromisoformat(value).date()
                except:
                    st.session_state[key] = value
            else:
                st.session_state[key] = value
        
        return True, f"Scenario '{scenario_name}' loaded successfully!"
    except Exception as e:
        return False, f"Error loading scenario: {str(e)}"


def delete_scenario(scenario_name: str):
    """Delete a saved scenario."""
    scenarios_dir = get_scenarios_directory()
    filepath = os.path.join(scenarios_dir, f'{scenario_name}.json')
    
    try:
        os.remove(filepath)
        return True, f"Scenario '{scenario_name}' deleted successfully!"
    except Exception as e:
        return False, f"Error deleting scenario: {str(e)}"


# ========== VA DISABILITY BENEFIT CALCULATOR ==========
def get_va_disability_rates():
    """
    Return 2025 VA disability compensation rates from VA.gov.
    Source: Official VA disability rates (effective 2025)
    https://www.va.gov/disability/rates/
    
    Rates are monthly amounts for different disability ratings and dependent statuses.
    Includes rates for spouse and children (rates increase per additional child).
    """
    va_rates = {
        10: {"single": 180.42},
        20: {"single": 356.66},
        30: {
            "single": 552.47,
            "spouse": 617.47,
            "spouse+1child": 673.47,
            "spouse+2child": 729.47,
            "spouse+3child": 785.47,
        },
        40: {
            "single": 795.84,
            "spouse": 882.84,
            "spouse+1child": 969.84,
            "spouse+2child": 1056.84,
            "spouse+3child": 1143.84,
        },
        50: {
            "single": 1132.90,
            "spouse": 1241.90,
            "spouse+1child": 1350.90,
            "spouse+2child": 1459.90,
            "spouse+3child": 1568.90,
        },
        60: {
            "single": 1435.02,
            "spouse": 1566.02,
            "spouse+1child": 1697.02,
            "spouse+2child": 1828.02,
            "spouse+3child": 1959.02,
        },
        70: {
            "single": 1808.45,
            "spouse": 1961.45,
            "spouse+1child": 2114.45,
            "spouse+2child": 2267.45,
            "spouse+3child": 2420.45,
        },
        80: {
            "single": 2102.15,
            "spouse": 2277.15,
            "spouse+1child": 2452.15,
            "spouse+2child": 2627.15,
            "spouse+3child": 2802.15,
        },
        90: {
            "single": 2362.30,
            "spouse": 2559.30,
            "spouse+1child": 2756.30,
            "spouse+2child": 2953.30,
            "spouse+3child": 3150.30,
        },
        100: {
            "single": 3938.58,
            "spouse": 4158.17,
            "spouse+1child": 4377.76,
            "spouse+2child": 4597.35,
            "spouse+3child": 4816.94,
        },
    }
    return va_rates


def calculate_va_benefit(rating: int, dependent_status: str) -> float:
    """
    Calculate monthly VA disability benefit based on rating and dependent status.
    
    Args:
        rating: Disability rating (10-100)
        dependent_status: 'single', 'spouse', 'spouse_1child', 'spouse_2child', 'spouse_3child'
    
    Returns:
        Monthly VA benefit amount
    """
    rates = get_va_disability_rates()
    
    # Round rating to nearest valid rating
    valid_ratings = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    closest_rating = min(valid_ratings, key=lambda x: abs(x - rating))
    
    return rates.get(closest_rating, {}).get(dependent_status, 0)


def calculate_disability_scenario(
    monthly_pension: float,
    va_rating: int,
    years_of_service: int,
    retirement_type: str,  # 'regular' or 'medical'
    combat_related: bool = False,
) -> dict:
    """
    Calculate VA disability compensation scenarios: offset, CRDP, or CRSC.
    
    Rules:
    1. BASIC OFFSET (all cases): VA disability reduces pension unless CRDP/CRSC applies
    2. CRDP (Concurrent Retirement & Disability Pay): 
       - Requires: 20+ YOS AND 50%+ VA rating
       - Result: Full pension + full VA disability (both tax treatment)
    3. CRSC (Combat-Related Special Compensation):
       - Requires: Combat-related disability (any rating)
       - Must apply (not automatic)
       - Result: Pension offset replaced with tax-free CRSC payment
    
    Args:
        monthly_pension: Monthly military pension amount
        va_rating: VA disability rating (0-100%)
        years_of_service: Total years of service
        retirement_type: 'regular' or 'medical'
        combat_related: Is disability combat-related?
    
    Returns:
        Dict with scenarios:
        - basic_offset: pension reduced, VA added (tax shift scenario)
        - crdp: full pension + full VA (if eligible)
        - crsc: pension offset replaced with tax-free CRSC (if eligible)
        - recommended: which scenario applies to this veteran
    """
    
    va_monthly = calculate_va_benefit(va_rating, 'single')  # Use single rate as base
    
    # === SCENARIO 1: BASIC OFFSET (applies to all) ===
    # VA reduces pension unless CRDP/CRSC overrides it
    offset_amount = min(va_monthly, monthly_pension)  # VA can't exceed pension
    pension_after_offset = monthly_pension - offset_amount
    
    offset_scenario = {
        'name': 'Basic Offset (VA reduces pension)',
        'gross_pension': monthly_pension,
        'va_disability': va_monthly,
        'pension_after_offset': pension_after_offset,
        'total_monthly': pension_after_offset + va_monthly,  # Same total but tax-free portion higher
        'pension_taxable': pension_after_offset,
        'va_taxable': 0,  # VA is tax-free
        'eligible': True,  # Everyone gets this if no CRDP/CRSC
        'notes': 'VA disability is tax-free; pension reduced by offset amount',
    }
    
    # === SCENARIO 2: CRDP (Concurrent Retirement & Disability Pay) ===
    # You get FULL pension AND FULL VA disability (no offset)
    crdp_eligible = (years_of_service >= 20) and (va_rating >= 50) and (retirement_type == 'regular')
    
    crdp_scenario = {
        'name': 'CRDP (Full Pension + Full VA)',
        'gross_pension': monthly_pension,
        'va_disability': va_monthly,
        'pension_after_offset': monthly_pension,  # NO OFFSET
        'total_monthly': monthly_pension + va_monthly,  # Both in full
        'pension_taxable': monthly_pension,  # Pension is taxable
        'va_taxable': 0,  # VA is tax-free
        'eligible': crdp_eligible,
        'notes': f"{'✓ ELIGIBLE' if crdp_eligible else '✗ Not eligible'} | Requires 20+ YOS AND 50%+ rating AND regular retirement",
    }
    
    # === SCENARIO 3: CRSC (Combat-Related Special Compensation) ===
    # For combat-related injuries: pension offset replaced with tax-free CRSC
    # You must APPLY (not automatic)
    crsc_eligible = combat_related and (retirement_type == 'regular')
    
    crsc_scenario = {
        'name': 'CRSC (Combat-Related, Tax-Free)',
        'gross_pension': monthly_pension,
        'va_disability': va_monthly,
        'pension_after_offset': pension_after_offset,
        'crsc_tax_free_amount': offset_amount,  # The offset becomes tax-free CRSC
        'total_monthly': pension_after_offset + offset_amount,  # Same as offset, but more is tax-free
        'pension_taxable': pension_after_offset,
        'crsc_taxable': 0,  # CRSC portion is tax-free
        'eligible': crsc_eligible,
        'notes': f"{'✓ ELIGIBLE (must apply)' if crsc_eligible else '✗ Not eligible'} | Requires combat-related disability AND regular retirement",
    }
    
    # === DETERMINE RECOMMENDED SCENARIO ===
    if crdp_eligible:
        recommended = 'crdp'
        recommended_label = 'CRDP'
    elif crsc_eligible:
        recommended = 'crsc'
        recommended_label = 'CRSC (Combat-Related)'
    else:
        recommended = 'basic_offset'
        recommended_label = 'Basic Offset'
    
    return {
        'basic_offset': offset_scenario,
        'crdp': crdp_scenario,
        'crsc': crsc_scenario,
        'recommended': recommended,
        'recommended_label': recommended_label,
        'va_rating': va_rating,
        'years_of_service': years_of_service,
        'retirement_type': retirement_type,
        'combat_related': combat_related,
    }


def calculate_gi_bill_benefits(gi_bill_type, bah_rate, months_used=0, education_level='bachelor'):
    """
    Calculate GI Bill education benefits based on type and usage.
    
    Two Types of GI Bill:
    1. MONTGOMERY GI BILL: Fixed monthly stipend
       - Up to 36 months of coverage
       - Monthly benefit (base, E-5): ~$1,959 (as of 2024)
    
    2. POST-9/11 GI BILL: Flexible tuition coverage + BAH
       - Up to 36 months of benefits (100% rate if 36+ months of service)
       - Monthly housing allowance (BAH) while in school
       - $1,000/year book stipend
       - Can transfer to spouse/children (Ruskin Ruling amendments)
    
    Args:
        gi_bill_type: 'montgomery' or 'post_9_11'
        bah_rate: Monthly BAH for education location (student gets this while in school)
        months_used: Months of benefits used (0-36)
        education_level: 'high_school', 'associate', 'bachelor', 'graduate'
    
    Returns:
        Dict with benefit calculations and monthly income impact
    """
    
    # Base benefit rates (2024 rates, adjust based on actual policy)
    MONTGOMERY_MONTHLY = 1959  # E-5 rate
    POST_9_11_TUITION_CAP = 30803  # 100% rate tuition cap
    BOOK_STIPEND = 1000 / 12  # ~$83/month annualized
    
    months_remaining = 36 - months_used
    
    if gi_bill_type == 'montgomery':
        # Montgomery: Simple fixed monthly benefit
        # Can be used for school or vocational training
        monthly_benefit = MONTGOMERY_MONTHLY
        annual_benefit = monthly_benefit * 12
        total_remaining_benefit = monthly_benefit * months_remaining
        
        return {
            'type': 'Montgomery GI Bill',
            'monthly_payment': monthly_benefit,
            'annual_benefit': annual_benefit,
            'total_remaining': total_remaining_benefit,
            'months_remaining': months_remaining,
            'bah_included': False,
            'bah_monthly': 0,
            'tuition_covered': 'Partial (use stipend to offset)',
            'transferable': False,
            'notes': 'Fixed monthly payment; can use for school tuition, books, living expenses',
            'annual_income_impact': annual_benefit,
        }
    
    else:  # post_9_11
        # Post-9/11: More flexible - tuition coverage + BAH
        # BAH paid directly to student while enrolled
        # Tuition paid to school
        monthly_bah = bah_rate
        annual_bah = monthly_bah * 12
        annual_book_stipend = BOOK_STIPEND * 12
        
        # Tuition coverage depends on months used
        tuition_coverage_pct = max(0, (months_remaining / 36) * 100)
        
        return {
            'type': 'Post-9/11 GI Bill',
            'monthly_bah': monthly_bah,
            'annual_bah': annual_bah,
            'monthly_book_stipend': BOOK_STIPEND,
            'annual_book_stipend': annual_book_stipend,
            'total_monthly_aid': monthly_bah + BOOK_STIPEND,
            'total_annual_aid': annual_bah + annual_book_stipend,
            'tuition_coverage_pct': tuition_coverage_pct,
            'tuition_cap': POST_9_11_TUITION_CAP,
            'months_remaining': months_remaining,
            'bah_included': True,
            'transferable': True,
            'transfer_note': 'Can transfer remaining benefits to spouse/children (Ruskin Ruling allows spouse to use while you work)',
            'notes': 'TAX-FREE: BAH and book stipend are tax-free (tuition paid directly to institution)',
            'annual_income_impact': annual_bah + annual_book_stipend,  # This is what hits your income
        }


# ========== TAX CALCULATION FUNCTIONS ==========
def calculate_federal_tax(annual_income: float, filing_status: str, dependents: int = 0) -> float:
    """
    Calculate federal income tax (simplified 2025 brackets).
    
    Args:
        annual_income: Pre-tax annual income
        filing_status: 'single', 'married_joint', or 'married_separate'
        dependents: Number of dependents
    
    Returns:
        Federal tax amount
    """
    # 2025 Federal tax brackets (simplified)
    if filing_status == 'single':
        brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37),
        ]
        standard_deduction = 14600
    elif filing_status == 'married_joint':
        brackets = [
            (23200, 0.10),
            (94300, 0.12),
            (201050, 0.22),
            (383900, 0.24),
            (487450, 0.32),
            (731200, 0.35),
            (float('inf'), 0.37),
        ]
        standard_deduction = 29200
    else:  # married_separate
        brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (365600, 0.35),
            (float('inf'), 0.37),
        ]
        standard_deduction = 14600
    
    # Apply dependent deductions
    dependent_deduction = dependents * 2000
    
    # Taxable income
    taxable_income = max(0, annual_income - standard_deduction - dependent_deduction)
    
    # Calculate tax using brackets
    tax = 0
    previous_limit = 0
    for limit, rate in brackets:
        if taxable_income <= previous_limit:
            break
        taxable_in_bracket = min(taxable_income, limit) - previous_limit
        tax += taxable_in_bracket * rate
        previous_limit = limit
    
    return tax


def calculate_fica_tax(annual_income: float) -> float:
    """
    Calculate FICA taxes (Social Security + Medicare).
    
    Args:
        annual_income: Pre-tax annual income
    
    Returns:
        Total FICA tax
    """
    # 2025 FICA rates
    ss_rate = 0.062
    ss_wage_base = 168600
    medicare_rate = 0.0145
    medicare_additional = 0.009  # Additional Medicare on income over threshold
    medicare_threshold = 200000
    
    # Social Security tax
    ss_tax = min(annual_income, ss_wage_base) * ss_rate
    
    # Medicare tax
    medicare_tax = annual_income * medicare_rate
    if annual_income > medicare_threshold:
        medicare_tax += (annual_income - medicare_threshold) * medicare_additional
    
    return ss_tax + medicare_tax


# ========== SESSION STATE INITIALIZATION ==========
def initialize_session_state():
    """Initialize Streamlit session state for first-time visitors."""
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'welcome'
    
    if 'current_profile' not in st.session_state:
        st.session_state.current_profile = None
    
    if 'uploaded_csv' not in st.session_state:
        st.session_state.uploaded_csv = None
    
    if 'saved_scenarios' not in st.session_state:
        st.session_state.saved_scenarios = []
    
    if 'show_comparison' not in st.session_state:
        st.session_state.show_comparison = False


# ========== MAIN APP FLOW ==========
def main():
    """Main application orchestration."""
    
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Project Atlas")
        
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["New Simulation", "Saved Scenarios", "About"],
            index=0,
        )
        
        st.markdown("---")
        
        # Sidebar info
        st.info(
            "**Tip**: Use 'Saved Scenarios' to compare your options side-by-side."
        )
    
    # Route based on navigation
    if page == "New Simulation":
        run_new_simulation()
    
    elif page == "Saved Scenarios":
        run_saved_scenarios_view()
    
    elif page == "About":
        display_about()


def run_new_simulation():
    """Run wizard directly - no mode selection."""
    from src.wizard.wizard_ui import run_transition_wizard
    run_transition_wizard()


def analyze_scenarios_summary():
    """Calculate and display summary statistics for all saved scenarios."""
    scenarios = get_all_scenarios()
    
    if not scenarios:
        st.info("No saved scenarios yet. Create and save scenarios to see analysis.")
        return
    
    # Parse all scenarios to extract data
    scenarios_dir = get_scenarios_directory()
    scenario_data_list = []
    rank_breakdown = {}
    
    for scenario_name in scenarios:
        filepath = os.path.join(scenarios_dir, f'{scenario_name}.json')
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            rank = data.get('user_rank', 'Unknown')
            pension = data.get('military_pension', 0)
            va_rating = data.get('va_rating', 0)
            salary = data.get('new_job_salary_annual', 0)
            savings = data.get('savings_available', 0)
            
            scenario_data_list.append({
                'name': scenario_name,
                'rank': rank,
                'pension': pension,
                'va_rating': va_rating,
                'salary': salary,
                'savings': savings
            })
            
            # Rank breakdown
            if rank not in rank_breakdown:
                rank_breakdown[rank] = 0
            rank_breakdown[rank] += 1
        except Exception as e:
            logger.warning(f"Could not parse scenario {scenario_name}: {e}")
            continue
    
    # Display metrics
    st.subheader("📊 All Saved Scenarios Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scenarios", len(scenario_data_list))
    
    with col2:
        avg_pension = sum(s['pension'] for s in scenario_data_list) / len(scenario_data_list) if scenario_data_list else 0
        st.metric("Avg Pension", f"${avg_pension:,.0f}/mo")
    
    with col3:
        avg_salary = sum(s['salary'] for s in scenario_data_list) / len(scenario_data_list) if scenario_data_list else 0
        st.metric("Avg New Salary", f"${avg_salary:,.0f}/yr")
    
    with col4:
        avg_savings = sum(s['savings'] for s in scenario_data_list) / len(scenario_data_list) if scenario_data_list else 0
        st.metric("Avg Savings", f"${avg_savings:,.0f}")
    
    # Breakdown by Rank
    st.subheader("Breakdown by Rank")
    
    if rank_breakdown:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            for rank in sorted(rank_breakdown.keys()):
                count = rank_breakdown[rank]
                st.write(f"• **{rank}**: {count} scenario(s)")
        
        with col2:
            # Chart
            import matplotlib.pyplot as plt
            ranks = list(rank_breakdown.keys())
            counts = list(rank_breakdown.values())
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.barh(ranks, counts, color='#1f77b4')
            ax.set_xlabel('Number of Scenarios')
            ax.set_title('Scenarios by Rank')
            ax.grid(axis='x', alpha=0.3)
            st.pyplot(fig)
    
    # Detailed table
    st.subheader("Detailed Scenario Data")
    
    if scenario_data_list:
        df_display = pd.DataFrame([
            {
                'Scenario': s['name'],
                'Rank': s['rank'],
                'Pension': f"${s['pension']:,.0f}",
                'VA Rating': f"{s['va_rating']}%",
                'Target Salary': f"${s['salary']:,.0f}",
                'Savings': f"${s['savings']:,.0f}",
            }
            for s in scenario_data_list
        ])
        st.dataframe(df_display, use_container_width=True)


def run_saved_scenarios_view():
    """Display saved scenarios and allow save/load/delete operations."""
    
    st.header("Saved Scenarios")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Save Current Scenario", "Load Scenario", "Manage Scenarios", "Analysis"])
    
    with tab1:
        st.subheader("Save Current Scenario")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            scenario_name = st.text_input(
                "Scenario Name",
                placeholder="e.g., Conservative Plan, Aggressive Growth",
                help="Give your scenario a descriptive name for easy identification"
            )
        
        with col2:
            st.write("")  # Spacing
            save_btn = st.button("💾 Save", use_container_width=True, key="save_scenario_btn")
        
        if save_btn:
            if scenario_name.strip():
                success, message = save_scenario(scenario_name.strip())
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
            else:
                st.warning("Please enter a scenario name")
    
    with tab2:
        st.subheader("Load Scenario")
        
        scenarios = get_all_scenarios()
        
        if not scenarios:
            st.info("No saved scenarios yet. Create and save a scenario from the 'Save Current Scenario' tab.")
        else:
            selected_scenario = st.selectbox(
                "Select a scenario to load",
                scenarios,
                help="Load all parameters from a previously saved scenario"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("📂 Load Scenario", use_container_width=True, key="load_scenario_btn"):
                    success, message = load_scenario(selected_scenario)
                    if success:
                        st.success(message)
                        st.info("Scenario loaded! Go to 'New Simulation' tab to view and modify the parameters.")
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                st.write("")  # Spacing
            
            # Show scenario preview
            with st.expander(f"Preview: {selected_scenario}"):
                scenarios_dir = get_scenarios_directory()
                filepath = os.path.join(scenarios_dir, f'{selected_scenario}.json')
                try:
                    with open(filepath, 'r') as f:
                        scenario_data = json.load(f)
                    
                    # Display key parameters
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Profile Settings:**")
                        st.write(f"- Rank: {scenario_data.get('user_rank', 'N/A')}")
                        st.write(f"- Years of Service: {scenario_data.get('user_years_of_service', 'N/A')}")
                        st.write(f"- Pension: ${scenario_data.get('military_pension', 'N/A'):,.0f}/mo")
                        st.write(f"- VA Rating: {scenario_data.get('va_rating', 'N/A')}%")
                    
                    with col2:
                        st.write("**Income Settings:**")
                        st.write(f"- New Job Salary: ${scenario_data.get('new_job_salary_annual', 'N/A'):,.0f}/yr")
                        st.write(f"- Job Start Month: {scenario_data.get('job_start_month', 'N/A')} months")
                        st.write(f"- Filing Status: {scenario_data.get('filing_status', 'N/A')}")
                        st.write(f"- State: {scenario_data.get('state', 'N/A')}")
                except:
                    st.warning("Could not preview scenario data")
    
    with tab3:
        st.subheader("Manage Scenarios")
        
        scenarios = get_all_scenarios()
        
        if not scenarios:
            st.info("No saved scenarios to manage.")
        else:
            st.write(f"**Total scenarios saved:** {len(scenarios)}")
            
            # Create a list with delete options
            for scenario in scenarios:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"{scenario}")
                
                with col2:
                    if st.button("View", key=f"view_{scenario}"):
                        st.session_state.preview_scenario = scenario
                
                with col3:
                    if st.button("🗑️", key=f"delete_{scenario}", help=f"Delete {scenario}"):
                        success, message = delete_scenario(scenario)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    with tab4:
        st.subheader("Performance Analysis")
        analyze_scenarios_summary()


def display_about():
    """Display about page."""
    
    st.header("About Project Atlas")
    
    st.markdown(
        """
        ### Mission
        
        Project Atlas is a **local-first financial simulator** designed for 
        transitioning military service members. It helps you answer the critical 
        question: **"Can I afford this transition?"**
        
        ### How It Works
        
        1. **Upload** your spending history (any CSV file with transactions)
        2. **Categorize** your expenses (mandatory, negotiable, optional)
        3. **Define** your transition scenario (target city, job timeline, salary)
        4. **Receive** a detailed month-by-month financial projection
        5. **Compare** multiple scenarios to find your best path forward
        
        ### Key Features
        
        **Local-First**: All data stays on your machine  
        **Tax-Aware**: Calculates federal, state, and FICA taxes  
        **VA-Informed**: Models retirement pay, VA benefits, and Tricare costs  
        **Risk Assessment**: Identifies financial challenges  
        **Scenario Comparison**: Side-by-side analysis of options  
        
        ### Technical
        
        - Built with Python & Streamlit
        - No internet required
        - Full PEP 8 compliance
        - Comprehensive error handling
        
        ### Support
        
        For questions or feedback, please reach out to your local military transition office.
        
        ---
        
        **Version**: 1.0.0 (MVP)  
        **Last Updated**: December 2024
        """
    )


# ========== HELPER FUNCTIONS ==========
def _generate_sample_transactions() -> pd.DataFrame:
    """Generate sample transaction data for demo purposes."""
    
    sample_data = {
        'date': pd.date_range(start='2024-01-01', periods=12, freq='M'),
        'description': [
            'Grocery Store', 'Rent', 'Utilities', 'Gas Station',
            'Restaurant', 'Gym Membership', 'Subscriptions', 'Phone Bill',
            'Insurance', 'Coffee Shop', 'Entertainment', 'Misc',
        ],
        'amount': [
            -150, -1200, -120, -60,
            -80, -30, -25, -60,
            -80, -8, -100, -50,
        ],
        'category': [
            'mandatory', 'mandatory', 'mandatory', 'mandatory',
            'negotiable', 'optional', 'negotiable', 'mandatory',
            'mandatory', 'optional', 'optional', 'unknown',
        ],
    }
    
    df = pd.DataFrame(sample_data)
    
    logger.info(f"Generated sample data: {len(df)} transactions")
    
    return df


# ========== RUN APPLICATION ==========
if __name__ == "__main__":
    main()

