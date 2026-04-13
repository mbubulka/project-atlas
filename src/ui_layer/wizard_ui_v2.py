"""
ProjectAtlas Wizard UI - Clean, step-by-step interface

8 Steps to financial sustainability:
1. User Profile (Military info)
2. Healthcare (Medical, vision, dental)
3. Income (Pension, VA slider with auto-calc, new job)
4. Upload YNAB CSV (Import actual spending data)
5. Review Classifications (Mandatory/Negotiable/Optional)
6. Assets & Debts
7. Sustainability Summary
8. Results & Recommendations
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

from src.data_layer.loader import DataCleaningError, clean_transaction_csv
from src.model_layer.sustainability_calculator import SustainabilityCalculator
from src.model_layer.va_rates_lookup import get_va_monthly_benefit
from src.ui_layer.classification_adjuster import (
    display_classification_adjuster,
)
from src.ui_layer.session_manager import SessionStateManager
from src.ui_layer.ui_helpers import (
    render_step_header,
    render_educational_disclaimer,
    show_success,
    show_error,
    show_warning,
    show_info,
    show_debug_expander,
    show_reference_expander,
    STEP_1_SOURCES,
    STEP_2_SOURCES,
    STEP_3_SOURCES,
    STEP_4_SOURCES,
    STEP_7_SOURCES,
    STEP_8_SOURCES,
)


def _calculate_federal_tax(gross_income: float, filing_status: str = "single") -> float:
    """
    Federal income tax calculation (2026 brackets).

    Args:
        gross_income: Annual gross income
        filing_status: "single", "married", or "divorced"
    """
    # 2026 standard deductions
    if filing_status.lower() == "married":
        standard_deduction = 29200  # Married filing jointly 2026
    else:
        standard_deduction = 14600  # Single 2026

    taxable_income = max(0, gross_income - standard_deduction)

    # 2026 tax brackets (same rates, different limits based on filing status)
    if filing_status.lower() == "married":
        brackets = [
            (23200, 0.10),  # 10% on first $23,200
            (94300, 0.12),  # 12% on amount over $23,200 up to $94,300
            (201050, 0.22),  # 22% on amount over $94,300 up to $201,050
            (float("inf"), 0.24),  # 24% on amount over $201,050
        ]
    else:
        # Single brackets
        brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (float("inf"), 0.24),
        ]

    tax = 0
    previous_limit = 0

    for limit, rate in brackets:
        if taxable_income > limit:
            tax += (limit - previous_limit) * rate
            previous_limit = limit
        else:
            tax += (taxable_income - previous_limit) * rate
            break

    return max(0, tax)


def _calculate_state_tax(gross_income: float, state: str = "VA", filing_status: str = "single") -> float:
    """
    Simplified state income tax calculation.
    Virginia: 2-5.75% depending on income level.
    Other states would need their own rates.
    """
    if state == "VA":
        if gross_income < 3000:
            return 0
        elif gross_income < 17000:
            return gross_income * 0.02
        else:
            return gross_income * 0.0575
    return 0  # Default for other states


def _calculate_takehome_from_gross(gross_income: float, state: str = "VA") -> float:
    """Calculate after-tax take-home pay from gross income."""
    federal_tax = _calculate_federal_tax(gross_income)
    state_tax = _calculate_state_tax(gross_income, state)
    return max(0, gross_income - federal_tax - state_tax)


def render_step_1_profile():
    """Step 1: User Profile - Military service information."""
    render_step_header(
        step_number=1,
        emoji="👤",
        title="Your Military Profile",
        description="Let's start with your military service information."
    )
    render_educational_disclaimer(STEP_1_SOURCES)

    col1, col2 = st.columns(2)

    with col1:
        rank_options = ["E-7", "E-8", "E-9", "O-3", "O-4", "O-5", "O-6"]
        rank_value = st.session_state.get("user_rank", "O-5")
        rank_index = rank_options.index(rank_value) if rank_value in rank_options else 5
        st.selectbox(
            "Military Rank/Pay Grade",
            rank_options,
            index=rank_index,
            key="user_rank",
        )
        st.number_input(
            "Years of Service (at separation)",
            min_value=0,
            max_value=50,
            value=st.session_state.get("user_years_of_service", 28),
            key="user_years_of_service",
        )
        branch_options = ["Army", "Navy", "Air Force", "Marines", "Coast Guard", "Space Force"]
        branch_value = st.session_state.get("user_service_branch", "Navy")
        branch_index = branch_options.index(branch_value) if branch_value in branch_options else 1
        st.selectbox(
            "Service Branch",
            branch_options,
            index=branch_index,
            key="user_service_branch",
        )

    with col2:
        st.text_input(
            "Career Field (e.g., ORSA, SWO, Pilot)",
            value=st.session_state.get("user_career_field", "ORSA"),
            key="user_career_field",
        )
        st.text_input(
            "City/County/Locality",
            value=st.session_state.get("user_locality", "Arlington"),
            key="user_locality",
            help="Where you plan to live (e.g., Arlington, TX or Fairfax County, VA)",
        )
        st.date_input(
            "Separation/Retirement Date",
            value=st.session_state.get("user_separation_date", date(2026, 6, 1)),
            key="user_separation_date",
        )
        state_options = ["VA", "MD", "DC", "NC", "PA", "NY", "TX", "CA", "FL", "Other"]
        state_value = st.session_state.get("user_state", "VA")
        state_index = state_options.index(state_value) if state_value in state_options else 0
        st.selectbox(
            "State of Residence",
            state_options,
            index=state_index,
            key="user_state",
            help="Used to calculate state income tax",
        )
        marital_options = ["Single", "Married", "Divorced/Widowed"]
        marital_value = st.session_state.get("user_marital_status", "Married")
        marital_index = marital_options.index(marital_value) if marital_value in marital_options else 1
        st.radio(
            "Marital Status",
            marital_options,
            index=marital_index,
            key="user_marital_status",
            horizontal=True,
        )

    st.number_input(
        "Number of Dependents (children, parents, etc.)",
        min_value=0,
        max_value=10,
        value=st.session_state.get("user_dependents", 0),
        key="user_dependents",
    )


def render_step_2_healthcare():
    """Step 2: Healthcare - Medical, vision, dental plans."""
    render_step_header(
        step_number=2,
        emoji="🏥",
        title="Healthcare Coverage",
        description="Choose your healthcare plans. Post-retirement costs will be included in your monthly expenses."
    )
    render_educational_disclaimer(STEP_2_SOURCES)

    # TRICARE 2026 monthly rates (approximate for retirees)
    TRICARE_RATES = {
        "Tricare Prime - Individual": 32,
        "Tricare Prime - Family": 90,
        "Tricare Select - Individual": 0,  # No monthly premium, embedded in Select
        "Tricare Select - Family": 67,
        "VA Health": 0,
        "ACA Marketplace": 0,  # User will specify
        "Private/Employer": 0,  # User will specify
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Medical Coverage")
        plan_options = ["Tricare Prime", "Tricare Select", "VA Health", "ACA Marketplace", "Private/Employer"]
        plan_value = st.session_state.get("medical_plan", "Tricare Prime")
        plan_index = plan_options.index(plan_value) if plan_value in plan_options else 0
        medical_plan = st.selectbox(
            "Plan Type",
            plan_options,
            index=plan_index,
            key="medical_plan",
            help="TRICARE plans are military-exclusive. Active Duty Tricare is free; Retiree costs shown below.",
        )

        coverage_options = ["Individual", "Family"]
        coverage_value = st.session_state.get("medical_coverage_type", "Family")
        coverage_index = coverage_options.index(coverage_value) if coverage_value in coverage_options else 1
        coverage_type = st.radio(
            "Coverage",
            coverage_options,
            index=coverage_index,
            key="medical_coverage_type",
            horizontal=True,
            help="Individual = you only; Family = you + spouse/dependents",
        )

    with col2:
        st.subheader("Dependent Coverage")
        num_covered = st.number_input(
            "Dependents/Family Members Covered",
            min_value=0,
            max_value=10,
            value=st.session_state.get("medical_dependents", 2),
            key="medical_dependents",
            help="Beyond yourself (included). E.g., spouse=1, spouse+2kids=3",
        )

    with col3:
        st.subheader("Estimated Retiree Cost")

        # Auto-calculate TRICARE monthly cost
        if medical_plan.startswith("Tricare"):
            key_lookup = f"{medical_plan} - {coverage_type}"
            monthly_cost = TRICARE_RATES.get(key_lookup, 0)
            st.metric(
                "Monthly Cost (Post-Retirement)",
                f"${monthly_cost:,.0f}",
                delta="Pre-tax deductible",
                help="Will be deducted from your pension before tax calculation",
            )
            st.session_state["tricare_monthly_cost"] = monthly_cost
        else:
            # For non-TRICARE plans
            custom_cost = st.number_input(
                "Monthly Premium ($)",
                min_value=0,
                value=st.session_state.get("medical_custom_cost", 0),
                step=25,
                key="medical_custom_cost",
            )
            st.session_state["tricare_monthly_cost"] = custom_cost

    st.markdown("---")

    # Display TRICARE rates reference
    def show_tricare_ref():
        st.write(
            """
        **TRICARE Prime** (HMO-style, needs referrals):
        - Individual: ~$32/month
        - Family: ~$90/month
        
        **TRICARE Select** (PPO-style, no referrals):
        - Individual: No monthly premium (but deductibles apply)
        - Family: ~$67/month
        
        *Rates shown are approximate 2026 estimates. See [tricare.mil](https://www.tricare.mil) for current rates.*
        
        **Note**: Active Duty TRICARE is covered by DoD and free. These costs apply AFTER you retire.
        """
        )
        vision_options = ["Tricare Vision", "VA Vision", "None", "Employer"]
        vision_value = st.session_state.get("vision_plan", "Tricare Vision")
        vision_index = vision_options.index(vision_value) if vision_value in vision_options else 0
        st.selectbox(
            "Vision Coverage",
            vision_options,
            index=vision_index,
            key="vision_plan",
        )
    
    show_reference_expander("2026 TRICARE Rates (Retirees) - Reference", show_tricare_ref)

    with col3:
        dental_options = ["Tricare Dental", "Dental Plan", "None", "Employer"]
        dental_value = st.session_state.get("dental_plan", "Tricare Dental")
        dental_index = dental_options.index(dental_value) if dental_value in dental_options else 0
        st.selectbox(
            "Dental Coverage",
            dental_options,
            index=dental_index,
            key="dental_plan",
        )

    # Estimated monthly healthcare costs
    st.markdown("---")
    st.write("**Estimated Monthly Healthcare Costs** (will be calculated in next steps)")
    st.info("These costs will be factored into your mandatory expenses calculation.")


def render_step_3_income():
    """Step 3: Income - Pension, VA (slider with auto-calc), new job, spouse, other."""
    render_step_header(
        step_number=3,
        emoji="💰",
        title="Income Sources",
        description="Enter all your income from different sources. These are non-overlapping."
    )
    render_educational_disclaimer(STEP_3_SOURCES)

    col1, col2 = st.columns(2)

    # Get state for tax calculations
    user_state = st.session_state.get("user_state", "VA")
    user_marital_status = st.session_state.get("user_marital_status", "Single")

    with col1:
        st.subheader("Military Pension")
        pension_gross = st.number_input(
            "Gross Monthly Military Pension ($)",
            min_value=0,
            value=st.session_state.get("military_pension_gross", 3500),
            step=100,
            key="military_pension_gross",
            help="Gross amount before taxes",
        )

        # Gross deductions (come out before taxes)
        st.markdown("**Pre-Tax Deductions (from pension):**")

        # Get TRICARE cost from Step 2 (healthcare)
        tricare_monthly = st.session_state.get("tricare_monthly_cost", 0)

        # Show TRICARE as read-only if already selected in Step 2
        if tricare_monthly > 0:
            st.metric("TRICARE (from Step 2)", f"${tricare_monthly:,.0f}", delta="Auto-calculated")
            st.session_state["tricare_cost"] = tricare_monthly

        # Allow override or manual entry of additional deductions
        tricare_override = st.number_input(
            "Adjust TRICARE if needed ($)",
            min_value=0,
            value=st.session_state.get("tricare_cost_manual", tricare_monthly),
            step=10,
            key="tricare_cost_manual",
            help="Override the amount from Step 2 if needed",
        )
        tricare_final = tricare_override if tricare_override != tricare_monthly else tricare_monthly

        ltc_monthly = st.number_input(
            "Long-Term Care Insurance ($)",
            min_value=0,
            value=st.session_state.get("ltc_cost", 0),
            step=10,
            key="ltc_cost",
            help="If deducted from pension before taxes",
        )
        other_pretax = st.number_input(
            "Other Pre-Tax Deductions (TSP, Roth, etc.) ($)",
            min_value=0,
            value=st.session_state.get("other_pretax", 0),
            step=10,
            key="other_pretax",
            help="Employee contributions to retirement/savings plans deducted from pension",
        )

        total_pretax_deductions = tricare_final + ltc_monthly + other_pretax
        pension_after_deductions = pension_gross - total_pretax_deductions

        # Calculate take-home (pension is taxed federally but not FICA)
        pension_annual_gross = pension_after_deductions * 12
        pension_federal_tax = _calculate_federal_tax(pension_annual_gross, filing_status=user_marital_status) / 12
        pension_state_tax = (
            _calculate_state_tax(pension_annual_gross, state=user_state, filing_status=user_marital_status) / 12
        )
        pension_takehome = pension_after_deductions - pension_federal_tax - pension_state_tax

        st.metric("Monthly Take-Home", f"${pension_takehome:,.0f}", delta=f"After pre-tax deductions & taxes")

        def show_pension_breakdown():
            st.write(f"Gross Pension: ${pension_gross:,.0f}")
            st.write(f"Pre-Tax Deductions: -${total_pretax_deductions:,.0f}")
            st.write(f"After Deductions: ${pension_after_deductions:,.0f}")
            st.write(f"Federal Tax: -${pension_federal_tax:,.0f}")
            st.write(f"State Tax: -${pension_state_tax:,.0f}")
            st.write(f"**Take-Home: ${pension_takehome:,.0f}**")
        
        show_reference_expander("Pension Breakdown", show_pension_breakdown)

        st.session_state["military_pension"] = pension_takehome
        st.session_state["military_pension_takehome"] = pension_takehome
        st.session_state["pension_pretax_deductions"] = total_pretax_deductions
        st.session_state["tricare_cost"] = tricare_final  # Save final TRICARE amount

        st.subheader("VA Disability Benefits")
        st.write("Select your disability rating. VA benefit is **automatically calculated** based on your dependents.")

        # Define a callback to save the VA rating when the slider changes
        def save_va_rating():
            st.session_state["va_rating"] = st.session_state["va_rating_slider"]

        # VA Rating Slider with callback to persist the value
        va_rating = st.slider(
            "VA Disability Rating (%)",
            min_value=0,
            max_value=100,
            step=10,
            value=st.session_state.get("va_rating", 0),
            key="va_rating_slider",
            on_change=save_va_rating,
            help="Slide to your disability rating (10%, 20%, 30%, etc.)",
        )

        # Ensure va_rating is in session state for Step 6
        if "va_rating" not in st.session_state:
            st.session_state["va_rating"] = va_rating

        # Get dependents from Step 1
        marital_status = SessionStateManager.get("user_marital_status", "Single")
        num_children = SessionStateManager.get("user_dependents", 0)

        va_monthly = get_va_monthly_benefit(
            rating=va_rating,
            marital_status=marital_status,
            num_children=num_children,
            num_dependent_parents=0,
        )

        # Store computed VA info for later use
        st.session_state["va_monthly_amount"] = va_monthly

        if va_rating >= 50:
            # CDRP eligible: VA is additional income
            st.metric(
                "Monthly VA Benefit (Tax-Free)",
                f"${va_monthly:,.2f}",
                delta=f"@ {va_rating}% CDRP-eligible (added to income)",
            )
            show_success(f"CDRP Eligible at {va_rating}%: VA disability benefit is ADDED to your monthly income.")
        elif va_rating > 0:
            # Below 50%: VA is a tax offset, not income
            st.metric(
                "Monthly VA Benefit (Tax-Free)", f"${va_monthly:,.2f}", delta=f"@ {va_rating}% (NOT counted as income)"
            )
            st.info(
                f"ℹ️ **Below 50% Threshold ({va_rating}%)**: VA disability benefit provides a **tax break** but does NOT count as additional income for financial planning purposes (one-time offset rule applies)."
            )
        else:
            st.metric("Monthly VA Benefit", "$0.00", delta="No disability rating selected")

    with col2:
        st.subheader("New Job / Civil Employment")

        # Add salary estimator button
        col_salary, col_estimator = st.columns([3, 1])
        with col_salary:
            salary_gross_annual = st.number_input(
                "Annual Salary (Gross) ($)",
                min_value=0,
                step=10000,
                key="new_job_salary_annual",
                help="Gross salary before taxes",
            )
        with col_estimator:
            st.write("")  # Spacing
            if st.button(
                "💼 Estimate", key="go_to_career_estimator", help="Use GLM model to estimate salary based on rank & YOS"
            ):
                st.session_state.current_tab = "career"
                st.rerun()

        # Calculate take-home (salary is taxed federal, state, and FICA)
        salary_federal_tax = _calculate_federal_tax(salary_gross_annual, filing_status=user_marital_status)
        salary_state_tax = _calculate_state_tax(
            salary_gross_annual, state=user_state, filing_status=user_marital_status
        )
        salary_fica = salary_gross_annual * 0.0765  # Social Security 6.2% + Medicare 1.45%
        salary_takehome_annual = salary_gross_annual - salary_federal_tax - salary_state_tax - salary_fica
        salary_takehome_monthly = salary_takehome_annual / 12

        st.metric("Monthly Take-Home", f"${salary_takehome_monthly:,.0f}", delta=f"After federal, state, & FICA")
        st.session_state["new_job_salary_monthly"] = salary_takehome_monthly

        st.number_input(
            "Job Start Month (1-12, or 0 if not yet scheduled)",
            min_value=0,
            max_value=12,
            value=st.session_state.get("job_start_month", 6),
            key="job_start_month",
        )

    st.markdown("---")
    st.subheader("Other Income")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.number_input(
            "Spouse Monthly Income ($)",
            min_value=0,
            value=st.session_state.get("spouse_income_monthly", 0),
            step=500,
            key="spouse_income_monthly",
        )

    with col2:
        st.number_input(
            "Rental Income (monthly, if any)",
            min_value=0,
            value=st.session_state.get("rental_income_monthly", 0),
            step=100,
            key="rental_income_monthly",
        )

    with col3:
        st.number_input(
            "Other Income (monthly)",
            min_value=0,
            value=st.session_state.get("other_income_monthly", 0),
            step=100,
            key="other_income_monthly",
        )
    # INCOME SUMMARY SECTION
    st.markdown("---")
    st.subheader("📊 Monthly Income Summary (All Take-Home)")

    # Use the local variables calculated above, not re-reading from session_state
    # (pension_takehome, va_rating, va_monthly, salary_takehome_monthly are already in scope)
    # Get any additional values from session_state that may not have been displayed yet
    salary_takehome = salary_takehome_monthly  # From the salary calculation above
    spouse_income = st.session_state.get("spouse_income_monthly", 0)
    rental_income = st.session_state.get("rental_income_monthly", 0)
    other_income = st.session_state.get("other_income_monthly", 0)

    # Determine if VA counts as income (use the va_rating and va_monthly just calculated above)
    if va_rating >= 50:
        va_income_count = va_monthly
        va_note = f"✅ CDRP ({va_rating}%)"
    else:
        va_income_count = 0
        va_note = f"ℹ️ Tax break ({va_rating}%)"

    # Calculate total
    total_income = pension_takehome + va_income_count + salary_takehome + spouse_income + rental_income + other_income

    # Display breakdown
    col_label, col_amount = st.columns([3, 1])

    with col_label:
        st.write("**Income Source**")
    with col_amount:
        st.write("**Monthly**")

    st.write("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Military Pension (Take-Home)")
    with col2:
        st.write(f"${pension_takehome:,.0f}")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"VA Disability {va_note}")
    with col2:
        if va_income_count > 0:
            st.write(f"${va_income_count:,.0f}")
        else:
            st.write(f"*${va_monthly:,.0f} (not counted)*")

    if salary_takehome > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"New Job/Salary (Take-Home)")
        with col2:
            st.write(f"${salary_takehome:,.0f}")

    if spouse_income > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Spouse Income")
        with col2:
            st.write(f"${spouse_income:,.0f}")

    if rental_income > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Rental Income")
        with col2:
            st.write(f"${rental_income:,.0f}")

    if other_income > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Other Income")
        with col2:
            st.write(f"${other_income:,.0f}")

    st.write("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("**Total Monthly Income**")
    with col2:
        st.metric("Total", f"${total_income:,.0f}", label_visibility="collapsed")


def render_step_4_upload_expenses():
    """Step 5 (numerically): Upload YNAB CSV - Import actual spending data."""
    render_step_header(
        step_number=5,
        emoji="📥",
        title="Upload Your Expenses",
        description="Upload your YNAB export or transaction CSV to import actual spending data. We'll automatically classify expenses as **Mandatory**, **Negotiable**, or **Optional**."
    )

    st.markdown("---")
    st.write("### How to Export from YNAB:")
    show_info(
        """
1. Log in to YNAB
2. Go to **Settings → Export**
3. Select date range
4. Download as **CSV**
5. Upload the file below
    """
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Select CSV or Excel file from YNAB or your bank",
        type=["csv", "xlsx", "xls"],
        help="File should contain: Date, Description, Amount columns",
    )

    if uploaded_file is not None:
        try:
            # Load and clean the CSV
            df = clean_transaction_csv(uploaded_file)
            show_success(f"Loaded {len(df)} transactions")

            # Store in session state
            st.session_state["uploaded_expenses_df"] = df

            # Show preview
            with st.expander("Preview Data (first 10 rows)"):
                st.dataframe(df.head(10), use_container_width=True)

            st.write(f"**Date Range:** {df['date'].min()} to {df['date'].max()}" if "date" in df.columns else "")

        except DataCleaningError as e:
            show_error(f"Error loading file: {e}")
            show_info("Please ensure your file has these columns: **Date**, **Description**, **Amount**")
        except Exception as e:
            show_error(f"Unexpected error: {str(e)}")
            show_info("Check file format and try again")
    else:
        st.markdown("---")
        st.write("Or use **sample data** for now:")
        if st.button("Load Sample Expenses"):
            sample_data = {
                "date": pd.date_range("2025-01-01", periods=12, freq="M"),
                "description": [
                    "Rent",
                    "Groceries",
                    "Utilities",
                    "Car Payment",
                    "Gas",
                    "Dining Out",
                    "Netflix",
                    "GymMembership",
                    "Insurance",
                    "Phone",
                    "Shopping",
                    "Entertainment",
                ],
                "amount": [2000, 600, 150, 400, 100, 300, 15, 50, 200, 80, 200, 150],
                "category": [
                    "mandatory",
                    "mandatory",
                    "mandatory",
                    "mandatory",
                    "mandatory",
                    "negotiable",
                    "optional",
                    "negotiable",
                    "mandatory",
                    "mandatory",
                    "optional",
                    "optional",
                ],
            }
            df = pd.DataFrame(sample_data)
            st.session_state["uploaded_expenses_df"] = df
            show_success("Sample data loaded")
            st.rerun()


def render_step_5_classify_expenses():
    """Step 6 (numerically): Review & Adjust Expense Classifications."""
    render_step_header(
        step_number=6,
        emoji="📋",
        title="Review Expense Classifications",
        description="The system has automatically categorized your expenses. Review and adjust as needed."
    )
    
    show_info("Tip: Mark expenses as **'Prepaid'** to zero out their monthly cost. Perfect for items you've already paid in advance (insurance, services, etc.)")

    # Check if we have uploaded data
    if "uploaded_expenses_df" not in st.session_state or st.session_state["uploaded_expenses_df"] is None:
        show_warning("Please upload your expenses in Step 5 first.")
        return

    df = st.session_state["uploaded_expenses_df"]

    # Use the classification adjuster
    classifications, adjusted_df = display_classification_adjuster(df)

    # Store classified expenses
    st.session_state["classified_expenses"] = adjusted_df
    st.session_state["expense_classifications"] = classifications

    st.markdown("---")
    show_success("Classifications reviewed. Continue to Step 7 when ready.")


def render_step_7_assets_debts():
    """Step 4 (numerically): Assets & Debts - Needed for runway calculations."""
    render_step_header(
        step_number=4,
        emoji="🏦",
        title="Assets & Debts",
        description="Enter your financial assets and liabilities. These are used to calculate your financial runway."
    )
    render_educational_disclaimer(STEP_4_SOURCES)

    st.subheader("Assets (Available Money)")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.number_input("Checking Account ($)", min_value=0, step=1000, key="asset_checking")

    with col2:
        st.number_input("Savings Account ($)", min_value=0, step=1000, key="asset_savings")

    with col3:
        st.number_input("Investments / Brokerage ($)", min_value=0, step=5000, key="asset_investments")

    st.markdown("---")
    st.subheader("Real Estate")
    col1, col2 = st.columns(2)

    with col1:
        st.number_input("Home Value ($)", min_value=0, step=10000, key="asset_home_value")

    with col2:
        st.number_input("Home Mortgage Remaining ($)", min_value=0, step=10000, key="debt_mortgage")

    st.markdown("---")
    st.subheader("Debts (Liabilities)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.number_input("Credit Card Debt ($)", min_value=0, step=1000, key="debt_cc")

    with col2:
        st.number_input("Auto Loans ($)", min_value=0, step=1000, key="debt_auto")

    with col3:
        st.number_input("Other Debt ($)", min_value=0, step=1000, key="debt_other")

    with col4:
        st.number_input(
            "Available CC Capacity ($)",
            min_value=0,
            step=1000,
            key="debt_cc_limit",
            help="Unused credit card limit available to bridge gaps",
        )


def render_step_6_sustainability_summary():
    """Step 7: Sustainability Check - CRITICAL: Post-June 1st scenario when military pay stops."""
    render_step_header(
        step_number=7,
        emoji="📊",
        title="Financial Sustainability Check",
        description="🔴 **CRITICAL QUESTION**: After June 1st when your military paycheck STOPS, how long can you survive on just **Pension + VA + Spouse income**?"
    )
    render_educational_disclaimer(STEP_7_SOURCES)

    # Get all income components
    military_pension_takehome = st.session_state.get("military_pension_takehome", 0)
    va_rating = st.session_state.get("va_rating", 0)
    va_monthly_takehome = st.session_state.get("va_monthly_amount", 0)
    salary_takehome = st.session_state.get("new_job_salary_monthly", 0)
    spouse_income = st.session_state.get("spouse_income_monthly", 0)
    rental_income = st.session_state.get("rental_income_monthly", 0)
    other_income = st.session_state.get("other_income_monthly", 0)

    # DEBUG: Show what we read from session state (hidden by default)
    def show_income_debug():
        va_rating_from_step3 = st.session_state.get("va_rating_step3", "NOT FOUND")
        st.write(
            f"**VA Rating from Step 3 slider: {va_rating_from_step3}%** | **Current va_rating in session: {va_rating}%** | **VA Amount: ${va_monthly_takehome:,.0f}**"
        )
        st.write(f"**military_pension_takehome**: ${military_pension_takehome:,.0f}")
        st.write(f"**va_rating**: {va_rating}%")
        st.write(f"**va_monthly_takehome**: ${va_monthly_takehome:,.0f}")
        st.write(f"**salary_takehome**: ${salary_takehome:,.0f}")
        st.write(f"**spouse_income**: ${spouse_income:,.0f}")
        st.write(f"**rental_income**: ${rental_income:,.0f}")
        st.write(f"**other_income**: ${other_income:,.0f}")
    
    show_debug_expander("Full Income Values", show_income_debug)

    # CRDP Logic: Only add VA if rating >= 50%
    if va_rating >= 50:
        va_income = va_monthly_takehome
        va_note = f"✅ CDRP ({va_rating}%) - ADDED"
    else:
        va_income = 0
        va_note = f"ℹ️ Tax break ({va_rating}%) - NOT COUNTED"

    # POST-JUNE-1 INCOME (WITHOUT NEW JOB) - THE CRITICAL SCENARIO
    post_june_income = military_pension_takehome + va_income + spouse_income + rental_income + other_income

    # FOR COMPARISON: Income WITH new job
    with_job_income = post_june_income + salary_takehome

    # Get expenses
    total_mandatory = st.session_state.get("csv_mandatory_expenses", 0) or 0
    negotiable_expenses = st.session_state.get("csv_negotiable_expenses", 0) or 0
    optional_expenses = st.session_state.get("csv_optional_expenses", 0) or 0
    total_all = total_mandatory + negotiable_expenses + optional_expenses

    if total_all == 0 and "csv_classification_map" not in st.session_state:
        st.info("ℹ️ No expenses uploaded. You can still view projections.")

    # Liquid savings
    liquid_savings = (
        st.session_state.get("asset_checking", 0)
        + st.session_state.get("asset_savings", 0)
        + st.session_state.get("asset_investments", 0) * 0.5
    )

    st.markdown("---")
    st.subheader("📊 Two Scenarios:")

    # Expense selection buttons
    st.write("**Select which expenses to include:**")
    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:
        if st.button("📋 Mandatory Only", key="expense_mandatory", use_container_width=True):
            st.session_state.expense_filter = "mandatory"

    with col_exp2:
        if st.button("📋 Mandatory + Negotiable", key="expense_mand_neg", use_container_width=True):
            st.session_state.expense_filter = "mandatory_negotiable"

    with col_exp3:
        if st.button("📋 All (Mandatory + Negotiable + Optional)", key="expense_all", use_container_width=True):
            st.session_state.expense_filter = "all"

    # Initialize expense filter if not set
    if "expense_filter" not in st.session_state:
        st.session_state.expense_filter = "mandatory"

    # Calculate expenses based on selected filter
    if st.session_state.expense_filter == "mandatory":
        display_expenses = total_mandatory
        expense_breakdown = f"${total_mandatory:,.0f} (Mandatory)"
    elif st.session_state.expense_filter == "mandatory_negotiable":
        display_expenses = total_mandatory + negotiable_expenses
        expense_breakdown = f"${total_mandatory:,.0f} (Mandatory) + ${negotiable_expenses:,.0f} (Negotiable)"
    else:  # "all"
        display_expenses = total_all
        expense_breakdown = (
            f"${total_mandatory:,.0f} (M) + ${negotiable_expenses:,.0f} (N) + ${optional_expenses:,.0f} (O)"
        )

    st.caption(f"**Active filter:** {expense_breakdown}")
    st.markdown("---")

    # Calculate which expenses to use based on filter BEFORE tabs so both can access
    if st.session_state.expense_filter == "mandatory":
        calc_mandatory = total_mandatory
        calc_negotiable = 0
    elif st.session_state.expense_filter == "mandatory_negotiable":
        calc_mandatory = total_mandatory
        calc_negotiable = negotiable_expenses
    else:  # "all"
        calc_mandatory = total_mandatory
        calc_negotiable = negotiable_expenses + optional_expenses

    # Get credit card limit for enhanced risk assessment (before tabs)
    credit_card_limit = st.session_state.get("debt_cc_limit", 0)
    if credit_card_limit == 0:
        credit_card_limit = 5000  # Default assumption

    # Calculate prepaid months remaining (before tabs)
    classifications = st.session_state.get("expense_classifications", {})
    prepaid_items = [v for v in classifications.values() if v == "prepaid"] if isinstance(classifications, dict) else []
    prepaid_months = 12 if any(prepaid_items) else 0

    tab1, tab2 = st.tabs(["🔴 CRITICAL: Without Job", "🟢 GOAL: With Job"])

    with tab1:
        st.markdown("### 🔴 POST-JUNE 1: WITHOUT New Job")
        st.markdown(f"**Pension + VA + Spouse only. NO new salary yet.**")

        result_critical = SustainabilityCalculator.calculate(
            monthly_income=post_june_income,
            mandatory_expenses=calc_mandatory,
            liquid_savings=liquid_savings,
            negotiable_expenses=calc_negotiable,
            credit_card_limit=credit_card_limit,
            prepaid_months_remaining=prepaid_months,
            expected_job_timeline_months=6,  # 6 months to find a job
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Income", f"${post_june_income:,.0f}")
            # Show breakdown
            st.caption(f"[MONEY] Pension: ${military_pension_takehome:,.0f}")
            st.caption(f"⚕️ VA ({va_rating}%): ${va_monthly_takehome:,.0f} {va_note}")
            if spouse_income > 0:
                st.caption(f"👥 Spouse: ${spouse_income:,.0f}")
        with col2:
            st.metric("Expenses", f"${display_expenses:,.0f}")
        with col3:
            # Show deficit or surplus with appropriate label
            surplus_value = result_critical.monthly_surplus
            if surplus_value < 0:
                metric_label = "Monthly Deficit"
                metric_value = f"${abs(surplus_value):,.0f}"
            else:
                metric_label = "Monthly Surplus"
                metric_value = f"${surplus_value:,.0f}"
            st.metric(
                metric_label,
                metric_value,
                delta=f"{surplus_value:+,.0f}",
                delta_color="inverse" if surplus_value < 0 else "normal",
            )

        # Debug: Verify math (hidden by default)
        def show_verify_debug():
            total_expenses_in_calc = calc_mandatory + calc_negotiable
            st.write(f"**Income**: ${post_june_income:,.0f}")
            st.write(f"**Display Expenses**: ${display_expenses:,.0f}")
            st.write(f"**Calc Total** (mandatory + negotiable): ${total_expenses_in_calc:,.0f}")
            st.write(
                f"**Manual Math**: ${post_june_income:,.0f} - ${display_expenses:,.0f} = ${post_june_income - display_expenses:,.0f}"
            )
            st.write(f"**Calculator Result**: {surplus_value:+,.0f}")
            if abs((post_june_income - display_expenses) - surplus_value) > 1:
                show_warning("Numbers don't match! Check calculator logic.")
        
        show_debug_expander("Verify Numbers", show_verify_debug)

        st.markdown("---")
        st.markdown(f"### {result_critical.risk_level.value}")
        st.write(result_critical.status_summary)

        if result_critical.months_of_runway and result_critical.months_of_runway != 999:
            runway_months = result_critical.months_of_runway
            st.error(f"⏰ **RUNWAY: {runway_months} MONTHS** | You MUST find a job before savings deplete!")
            st.write(
                f"*${liquid_savings:,.0f} savings ÷ ${abs(result_critical.monthly_surplus):,.0f} monthly deficit = {runway_months} months*"
            )
        elif result_critical.monthly_surplus >= 0:
            show_success("RUNWAY: Indefinite | Pension covers expenses - no urgency!")

        st.markdown("---")
        for i, rec in enumerate(result_critical.recommendations, 1):
            st.write(f"{i}. {rec}")

    with tab2:
        st.markdown("### 🟢 POST-JOB START: WITH New Job")
        st.markdown(f"**Once you land a job at your target salary.**")

        result_with_job = SustainabilityCalculator.calculate(
            monthly_income=with_job_income,
            mandatory_expenses=calc_mandatory,
            liquid_savings=liquid_savings,
            negotiable_expenses=calc_negotiable,
            credit_card_limit=credit_card_limit,
            prepaid_months_remaining=prepaid_months,
            expected_job_timeline_months=6,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Income", f"${with_job_income:,.0f}", f"+${salary_takehome:,.0f} from job")
        with col2:
            st.metric("Expenses", f"${display_expenses:,.0f}")
        with col3:
            # Show deficit or surplus with appropriate label
            surplus_value = result_with_job.monthly_surplus
            if surplus_value < 0:
                metric_label = "Monthly Deficit"
                metric_value = f"${abs(surplus_value):,.0f}"
            else:
                metric_label = "Monthly Surplus"
                metric_value = f"${surplus_value:,.0f}"
            st.metric(
                metric_label,
                metric_value,
                delta=f"{surplus_value:+,.0f}",
                delta_color="normal" if surplus_value >= 0 else "inverse",
            )

        st.markdown("---")
        st.markdown(f"### {result_with_job.risk_level.value}")
        st.write(result_with_job.status_summary)

        st.markdown("---")
        for i, rec in enumerate(result_with_job.recommendations, 1):
            st.write(f"{i}. {rec}")


def render_step_8_results():
    """Step 8: Results & Next Steps."""
    render_step_header(
        step_number=8,
        emoji="🎯",
        title="Your Transition Plan",
        description="Here's your personalized financial transition plan."
    )
    render_educational_disclaimer(STEP_8_SOURCES)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("What's Working Well")
        # Analysis would go here
        st.write("- Your military pension provides stable baseline income")
        st.write("- New job salary meets your minimum threshold")
        st.write("- Liquid savings provide runway for transition")

    with col2:
        st.subheader("What Needs Attention")
        st.write("- Review discretionary expenses for potential cuts")
        st.write("- Confirm job start date to ensure income timeline")
        st.write("- Monitor healthcare costs in first 6 months")

    st.markdown("---")
    st.subheader("Next Steps")
    st.write(
        """
    1. **Review this plan with your spouse** - Ensure alignment on financial decisions
    2. **Track your actual expenses** - Compare to projections in first 3 months
    3. **Confirm job offer & start date** - Lock in income timeline
    4. **Revisit in 90 days** - Adjust based on actual spending
    5. **Keep this plan updated** - Re-run scenario if circumstances change
    """
    )

    st.markdown("---")
    st.subheader("Export Your Scenario")

    if st.button("💾 Save This Scenario", use_container_width=True):
        scenario_data = SessionStateManager.get_all()
        # Would save to JSON file here
        st.success("Scenario saved! You can load it later to revisit your plan.")


def run_wizard():
    """Main wizard orchestration."""

    # Initialize session state
    SessionStateManager.initialize()

    # Display progress
    current_step, total_steps = SessionStateManager.get_step_progress()
    progress = current_step / total_steps
    st.progress(progress, text=f"Step {current_step} of {total_steps}")

    # Render current step
    step_renderers = [
        None,  # Step 0 (unused)
        render_step_1_profile,
        render_step_2_healthcare,
        render_step_3_income,
        render_step_7_assets_debts,  # Step 4
        render_step_4_upload_expenses,  # Step 5
        render_step_5_classify_expenses,  # Step 6
        render_step_6_sustainability_summary,  # Step 7
        render_step_8_results,  # Step 8
    ]

    if current_step >= 1 and current_step < len(step_renderers):
        step_renderers[current_step]()

    # Navigation buttons
    st.markdown("---")
    col_prev, col_next = st.columns([1, 1])

    with col_prev:
        if not SessionStateManager.is_first_step():
            if st.button("← Back", use_container_width=True):
                SessionStateManager.prev_step()
                st.rerun()

    with col_next:
        if not SessionStateManager.is_last_step():
            if st.button("Next →", use_container_width=True):
                SessionStateManager.next_step()
                st.rerun()
        else:
            if st.button("Start Over", use_container_width=True):
                SessionStateManager.reset()
                st.rerun()
