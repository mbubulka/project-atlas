"""
Wizard flow: 4-step guided transition planning.

Each step:
1. Collects inputs
2. Validates data
3. Shows mini-summary
4. Allows navigation (back/forward)
"""

from datetime import date

import pandas as pd
import streamlit as st

from .session_manager import get_step_summary, build_profile_from_session


def step1_profile() -> bool:
    """
    STEP 1: Tell Me About You

    Collects: Rank, YOS, Service Branch, Separation Date, Marital
    Status, Dependents
    Returns: True if valid and ready to continue
    """
    st.header("🎖️ Step 1: Tell Me About You")
    st.write("Let's start with your military background and family situation.")

    col1, col2 = st.columns(2)

    with col1:
        rank_options = [
            "E-1",
            "E-2",
            "E-3",
            "E-4",
            "E-5",
            "E-6",
            "E-7",
            "E-8",
            "E-9",
            "O-1",
            "O-2",
            "O-3",
            "O-4",
            "O-5",
            "O-6",
            "O-7",
            "O-8",
            "O-9",
        ]
        st.selectbox(
            "Your Rank (at separation)",
            rank_options,
            index=(
                rank_options.index(st.session_state.get("user_rank", "O-5"))
                if st.session_state.get("user_rank") in rank_options
                else 12
            ),
            key="user_rank",
        )

        st.slider(
            "Years of Service",
            min_value=0,
            max_value=40,
            value=st.session_state.get("user_years_of_service", 20),
            key="user_years_of_service",
            help="Total active duty service years",
        )

    with col2:
        branch_options = [
            "Army",
            "Navy",
            "Air Force",
            "Marines",
            "Space Force",
            "Coast Guard",
        ]
        st.selectbox(
            "Service Branch",
            branch_options,
            index=(
                branch_options.index(st.session_state.get("user_service_branch", "Navy"))
                if st.session_state.get("user_service_branch") in branch_options
                else 1
            ),
            key="user_service_branch",
        )

        st.date_input(
            "Separation Date",
            value=st.session_state.get("user_separation_date") or date.today(),
            key="user_separation_date",
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.radio(
            "Marital Status",
            ["Single", "Married", "Divorced/Widowed"],
            index=["Single", "Married", "Divorced/Widowed"].index(
                st.session_state.get("user_marital_status", "Single")
            ),
            key="user_marital_status",
            horizontal=True,
        )

    with col2:
        st.number_input(
            "Number of Dependents",
            min_value=0,
            max_value=10,
            value=st.session_state.get("user_dependents", 0),
            key="user_dependents",
        )

    st.markdown("---")

    # ========== RETIREMENT LOCATION ==========
    st.subheader("🏠 Where will you retire?")
    st.write("This helps us calculate location-based benefits " "(GI Bill BAH, taxes, cost of living).")

    col1, col2 = st.columns(2)

    from src.model_layer.bah_lookup import get_all_locations

    with col1:
        all_locations = get_all_locations()
        current_location = st.session_state.get("retirement_location", all_locations[0])

        # Find the index of current location, default to 0 if not found
        try:
            location_index = all_locations.index(current_location)
        except ValueError:
            location_index = 0

        help_text = "Choose your retirement state for accurate BAH " "and tax calculations"
        retirement_location = st.selectbox(
            "Select Your Retirement State",
            options=all_locations,
            index=location_index,
            help=help_text,
            key="retirement_location",
        )

        # Streamlit automatically syncs the selectbox value to session
        # state via the key

    with col2:
        # Display selected state and BAH estimate
        from src.model_layer.bah_lookup import get_bah_rate

        bah_estimate = get_bah_rate(retirement_location)
        bah_display = f"${bah_estimate:,.0f}/month"
        st.metric("Estimated BAH (E-5 w/ dependents)", bah_display)

    st.markdown("---")

    # Mini-summary
    st.info(f"**Profile Summary:** {get_step_summary(1)}")

    return True  # Step 1 is always valid


def step2_finances() -> bool:
    """
    STEP 2: What's Your Money Situation

    Collects: Retirement pay, SBP election, VA benefit, Spouse/Other income,
    Expenses, Savings, Debt
    Returns: True if expenses are entered and valid
    """
    st.header("[MONEY] Step 2: What's Your Money Situation")
    st.write("Let's map your income, expenses, and savings.")

    # ========== INCOME SECTION ==========
    st.subheader("Income Sources (Monthly)")

    col1, col2 = st.columns(2)

    with col1:
        help_text = "Your current base pay + BAH/BAS after all taxes " "and deductions"
        current_paycheck_monthly = st.number_input(
            "Current Active Duty Paycheck (takehome)",
            min_value=0.0,
            value=float(st.session_state.get("current_paycheck_monthly", 0.0)),
            step=100.0,
            key="current_paycheck_monthly",
            help=help_text,
        )

    with col2:
        help_text = "Your monthly retirement pay before deductions " "(from DOD retirement calculator)"
        military_pension_monthly = st.number_input(
            "Military Retirement Pay (pretax)",
            min_value=0.0,
            value=float(st.session_state.get("military_pension", 4000.0)),
            step=100.0,
            key="military_pension",
            help=help_text,
        )

    st.markdown("---")

    # ========== SBP DECISION ==========
    st.subheader("👨‍👩‍👧 Survivor Benefit Plan (SBP)")
    st.caption("Protects your family if you pass away - deducted from pension")

    elect_sbp = st.checkbox(
        "Will you elect SBP?",
        value=st.session_state.get("elect_sbp", False),
        key="elect_sbp",
    )

    sbp_monthly_cost = 0.0

    if elect_sbp:
        col_sbp1, col_sbp2 = st.columns(2)

        with col_sbp1:
            st.radio(
                "SBP Beneficiary",
                ["spouse_only", "spouse_and_children", "children_only"],
                format_func=lambda x: {
                    "spouse_only": "Spouse only",
                    "spouse_and_children": "Spouse & Children",
                    "children_only": "Children only",
                }[x],
                key="sbp_beneficiary",
            )

        with col_sbp2:
            # SBP cost varies by option (6-8% of pension)
            sbp_cost_pct = 0.07  # 7% average
            sbp_monthly_cost = (military_pension_monthly * 12 * sbp_cost_pct) / 12

            st.metric(
                "Monthly SBP Cost",
                f"${sbp_monthly_cost:,.0f}",
                delta=f"~{sbp_cost_pct*100:.0f}% of pension",
            )
    else:
        st.info("SBP will not be deducted from your pension")

    # Store SBP cost in session state for use in calculations
    st.session_state["sbp_monthly_cost"] = sbp_monthly_cost

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        help_text = "Health insurance, taxes, and other pretax " "deductions from your pension"
        pension_pretax_expense = st.number_input(
            "Pension Pretax Deductions",
            min_value=0.0,
            value=float(st.session_state.get("pension_pretax_expense", 0.0)),
            step=10.0,
            key="pension_pretax_expense",
            help=help_text,
        )

    with col2:
        # Calculate take-home pension (after all deductions)
        take_home_pension = military_pension_monthly - sbp_monthly_cost - pension_pretax_expense
        st.metric("Pension (takehome)", f"${take_home_pension:,.0f}/mo")

        # Validate deductions don't exceed pension
        total_deductions = sbp_monthly_cost + pension_pretax_expense
        if total_deductions > military_pension_monthly and military_pension_monthly > 0:
            st.warning(
                f"[WARNING] Deductions (${total_deductions:,.0f}) exceed pension "
                f"(${military_pension_monthly:,.0f}). Reduce deductions to prevent "
                f"negative take-home."
            )

    with col3:
        # Show deductions breakdown
        st.metric(
            "Total Deductions",
            f"${sbp_monthly_cost + pension_pretax_expense:,.0f}/mo",
            delta=f"SBP: ${sbp_monthly_cost:,.0f}, Other: ${pension_pretax_expense:,.0f}",
        )

    with col2:
        # VA Disability Rating slider
        help_text = "Estimate if you don't know (0% = no rating, " "100% = 100% disabled)"
        va_rating = st.slider(
            "VA Disability Rating (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("current_va_disability_rating", 30),
            step=10,
            key="current_va_disability_rating",
            help=help_text,
        )

        # Get marital status and dependents for VA calculation
        marital_status = st.session_state.get("user_marital_status", "Single")
        num_children = st.session_state.get("user_dependents", 0)

        # Calculate VA benefit using official military.com rates
        # based on dependents
        if va_rating > 0:
            from src.model_layer.va_rates_lookup import get_va_monthly_benefit

            va_monthly = get_va_monthly_benefit(
                rating=va_rating,
                marital_status=marital_status,
                num_children=num_children,
                num_dependent_parents=0,
                schoolchildren_over_18=0,
            )
        else:
            va_monthly = 0.0

        st.session_state.va_annual_benefit = va_monthly * 12

        st.write(f"**VA Disability Benefit:** ${va_monthly:,.0f}/month")
        dependents_text = ""
        if num_children > 0:
            dependents_text = f" with {num_children} dependent(s)"

        caption_text = f"(${va_monthly * 12:,.0f}/year, rated {marital_status.lower()}" f"{dependents_text})"
        st.caption(caption_text)

        # Show program eligibility details based on VA rating
        if va_rating >= 50:
            info_text = (
                "[OK] **CRDP Eligible:** Concurrent Retirement & "
                "Disability Pay - Get full pension + VA benefit "
                "combined"
            )
            st.info(info_text)
        elif va_rating >= 20:
            info_text = (
                "[WARNING] **Offset to Pension:** VA benefit reduces "
                "(offsets) your military retirement pay, but "
                "combined income is protected"
            )
            st.info(info_text)
        else:
            info_text = "[PROFILE] **Healthcare Access:** Eligible for VA healthcare based on " "service-connection"
            st.info(info_text)

    with col3:
        spouse_income_monthly = st.number_input(
            "Spouse Monthly Income (takehome)",
            min_value=0.0,
            value=float(st.session_state.get("spouse_income_annual", 0.0) / 12),
            step=100.0,
            key="spouse_income_monthly_input",
            help="Spouse's net monthly income after all taxes and deductions",
        )
        st.session_state.spouse_income_annual = spouse_income_monthly * 12

    col1, col2 = st.columns(2)

    with col1:
        other_income_monthly = st.number_input(
            "Other Monthly Income (takehome)",
            min_value=0.0,
            value=float(st.session_state.get("other_income_annual", 0.0) / 12),
            step=100.0,
            key="other_income_monthly_input",
            help="Other income after taxes (side gigs, rental income, etc.)",
        )
        st.session_state.other_income_annual = other_income_monthly * 12

    # Calculate VA amount to include (only if CRDP eligible,
    # rating >= 50%)
    va_annual = st.session_state.get("va_annual_benefit", 0)
    va_rating = st.session_state.get("current_va_disability_rating", 0)
    va_to_include = (va_annual / 12) if va_rating >= 50 else 0

    # Phase 1 = current (active duty paycheck still coming in,
    # NO retirement yet)
    # Phase 2 = after separation (retirement + VA kick in ~1 month
    # with back pay)
    # Phase 3 = after job found (add new job salary)
    phase1_monthly_income = current_paycheck_monthly + spouse_income_monthly + other_income_monthly
    phase2_pension_income = take_home_pension + va_to_include + spouse_income_monthly + other_income_monthly

    st.markdown("---")
    st.markdown("### [STATS] Income by Phase")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Phase 1 (Active Duty)", f"${phase1_monthly_income:,.0f}/mo")
        st.caption("Your current paycheck (before separation)")
    with col2:
        st.metric("Phase 2 (Pension Only)", f"${phase2_pension_income:,.0f}/mo")
        st.caption("After separation (~1 month for VA processing)")

    retirement_loc = st.session_state.get("retirement_location", "your selected state")
    info_text = (
        "[INFO] **Income Note:** Current paycheck, spouse, and other "
        "income shown are net/take-home. Military pension is "
        "pre-tax (from DOD calculator). "
        f"State tax estimates calculated for {retirement_loc}."
    )
    st.info(info_text)

    st.markdown("---")

    # ========== EXPENSES SECTION ==========
    st.subheader("Monthly Expenses")
    st.caption("Upload CSV to auto-detect categories, or enter estimates manually")

    # Check if CSV was already confirmed in a previous run
    csv_confirmed = st.session_state.get("csv_expenses_confirmed", False)

    # Option 1: Upload CSV for expense analysis
    with st.expander("📤 Upload Expense CSV (optional)", expanded=False):
        st.write("Upload a CSV with your transactions to auto-categorize expenses.")
        st.caption("Expected columns: Date, Description, Amount")

        expense_file = st.file_uploader("Select expenses CSV", type=["csv"], key="expense_csv_upload")

        if expense_file is not None:
            try:
                from src.data_layer.loader import clean_transaction_csv
                from src.ui_layer.classification_adjuster import (
                    display_classification_adjuster,
                )

                # Load and clean the CSV
                df_expenses = clean_transaction_csv(expense_file)
                st.success(f"Loaded {len(df_expenses)} transactions")

                # Let user classify them
                st.write("**Review and adjust expense categories:**")
                (
                    classification_map,
                    adjusted_df,
                ) = display_classification_adjuster(df_expenses)

                # Calculate totals by classification using the adjusted columns
                if not adjusted_df.empty and "adjusted_category" in adjusted_df.columns:
                    csv_mandatory = adjusted_df[adjusted_df["adjusted_category"] == "mandatory"]["amount"].sum() / 12
                    csv_negotiable = adjusted_df[adjusted_df["adjusted_category"] == "negotiable"]["amount"].sum() / 12
                    csv_optional = adjusted_df[adjusted_df["adjusted_category"] == "optional"]["amount"].sum() / 12

                    # Show totals for review before accepting
                    st.markdown("**CSV Expense Totals (Monthly):**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mandatory", f"${csv_mandatory:,.0f}")
                    with col2:
                        st.metric("Negotiable", f"${csv_negotiable:,.0f}")
                    with col3:
                        st.metric("Optional", f"${csv_optional:,.0f}")

                    # Add confirmation checkbox
                    st.markdown("---")
                    csv_confirmed = st.checkbox(
                        "✓ Accept these CSV expense calculations",
                        value=False,
                        key="csv_expenses_confirmed",
                    )

                    if csv_confirmed:
                        # Store in session state using consistent keys
                        st.session_state.monthly_expenses_mandatory = csv_mandatory
                        st.session_state.monthly_expenses_negotiable = csv_negotiable
                        st.session_state.monthly_expenses_optional = csv_optional
                        st.success("✓ Expenses categorized and saved")

            except Exception as e:
                st.error(f"Error processing expenses: {e}")
                import traceback

                st.debug(traceback.format_exc())

    # Option 2: Manual entry (fallback or preference)
    if not csv_confirmed:
        st.write("**Or enter expenses manually:**")
        st.caption("Budget breakdown by category (all monthly amounts)")

        # Add reset button if there are lingering CSV values
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Reset to Defaults", key="reset_expenses"):
                st.session_state.monthly_expenses_mandatory = 3500.0
                st.session_state.monthly_expenses_negotiable = 1200.0
                st.session_state.monthly_expenses_optional = 600.0
                st.rerun()

        # Full width columns for better readability
        markdown_text = "**Mandatory Expenses** (essentials: rent, utilities, food, " "insurance)"
        st.markdown(markdown_text)
        mandatory = st.number_input(
            "Monthly mandatory expenses",
            min_value=0.0,
            value=float(st.session_state.get("monthly_expenses_mandatory", 0.0)),
            step=100.0,
            key="monthly_expenses_mandatory",
        )

        markdown_text = "**Negotiable Expenses** (flexible: subscriptions, dining out, " "entertainment)"
        st.markdown(markdown_text)
        negotiable = st.number_input(
            "Monthly negotiable expenses",
            min_value=0.0,
            value=float(st.session_state.get("monthly_expenses_negotiable", 0.0)),
            step=100.0,
            key="monthly_expenses_negotiable",
        )

        markdown_text = "**Optional Expenses** (discretionary: luxury items, hobbies, " "gifts)"
        st.markdown(markdown_text)
        optional = st.number_input(
            "Monthly optional expenses",
            min_value=0.0,
            value=float(st.session_state.get("monthly_expenses_optional", 0.0)),
            step=100.0,
            key="monthly_expenses_optional",
        )
    else:
        # CSV was confirmed, use those values from the correct keys
        mandatory = st.session_state.get("monthly_expenses_mandatory", 0.0)
        negotiable = st.session_state.get("monthly_expenses_negotiable", 0.0)
        optional = st.session_state.get("monthly_expenses_optional", 0.0)

    total_monthly_expenses = mandatory + negotiable + optional
    st.metric("Total Monthly Expenses", f"${total_monthly_expenses:,.0f}")

    st.markdown("---")

    # Mini-summary
    st.info(f"**Financial Summary:** {get_step_summary(2)}")

    return total_monthly_expenses > 0  # Valid if expenses entered


def step3_debt_vs_savings() -> bool:
    """
    STEP 3: Debt vs Savings Strategy - POWERED BY THEMIS ENGINE

    Uses the THEMIS (Transition Handling and Emergency Management through
    Intelligent Strategy) decision engine to analyze financial position and
    recommend optimal strategy.

    Collects: Credit card debt, loans, interest rates, savings, payoff strategy
    Returns: True if strategy selected
    """
    st.header("[CREDIT] Step 3: THEMIS Transition Strategy")
    st.write(
        """
    THEMIS analyzes your financial situation and recommends the
    optimal allocation between debt paydown, savings building, and
    expense reduction during your transition.
    """
    )

    # Import THEMIS engine
    from src.model_layer.themis_decision_engine import (
        ExpenseBreakdown,
        FinancialPosition,
        ThemisDecisionEngine,
        TimingFactors,
    )

    # Initialize session variables if needed
    if "has_debt" not in st.session_state:
        st.session_state.has_debt = False
    if "debt_payoff_priority" not in st.session_state:
        st.session_state.debt_payoff_priority = "themis"

    # ========== STEP 1: GATHER FINANCIAL DATA ==========
    st.markdown("---")
    st.markdown("### [MONEY] Current Financial Position")
    st.caption("Your cash on hand and existing debt before transition")

    col1, col2 = st.columns(2)

    with col1:
        current_savings = st.number_input(
            "Current Savings / Cash on Hand ($)",
            min_value=0.0,
            value=float(st.session_state.get("current_savings", 50000.0)),
            step=5000.0,
            help="Liquid savings you have available right now",
            key="current_savings",
        )

    with col2:
        current_debt = st.number_input(
            "Current Total Debt ($)",
            min_value=0.0,
            value=float(st.session_state.get("current_debt", 0.0)),
            step=1000.0,
            help="Total of credit cards, loans, and other debts",
            key="current_debt",
        )

    # ========== STEP 2: GATHER INCOME DATA ==========
    st.markdown("---")
    st.markdown("### [STATS] Income Sources (Monthly - Phase 2 Takehome)")
    st.caption("After separation - all amounts in takehome")

    # Calculate pension (from Step 2)
    pension_monthly = st.session_state.get("military_pension", 0)
    sbp_cost = st.session_state.get("sbp_monthly_cost", 0)
    pension_pretax_deductions = st.session_state.get("pension_pretax_expense", 0)
    pension_takehome = pension_monthly - sbp_cost - pension_pretax_deductions

    # Validate pension calculation
    if pension_takehome < 0 and pension_monthly > 0:
        st.error(
            f"[WARNING] **Pension calculation error detected!**\n\n"
            f"Your deductions (${sbp_cost + pension_pretax_deductions:,.0f}) "
            f"exceed your pension (${pension_monthly:,.0f}).\n\n"
            f"**Go back to Step 2 and verify:**\n"
            f"• Pension amount: ${pension_monthly:,.0f}/mo\n"
            f"• SBP cost: ${sbp_cost:,.0f}/mo\n"
            f"• Other deductions: ${pension_pretax_deductions:,.0f}/mo"
        )
        pension_takehome = max(0, pension_takehome)  # Clamp to 0

    va_annual = st.session_state.get("va_annual_benefit", 0)
    spouse_income_annual = st.session_state.get("spouse_income_annual", 0)
    other_income_annual = st.session_state.get("other_income_annual", 0)
    va_rating = st.session_state.get("current_va_disability_rating", 0)

    # For Phase 2, only include VA if CRDP eligible (rating >= 50%)
    va_to_include = (va_annual / 12) if va_rating >= 50 else 0

    total_monthly_income = pension_takehome + va_to_include + (spouse_income_annual / 12) + (other_income_annual / 12)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pension (takehome)", f"${pension_takehome:,.0f}/mo")
    with col2:
        st.metric("VA Benefit", f"${va_to_include:,.0f}/mo")
    with col3:
        st.metric("Spouse (takehome)", f"${spouse_income_annual/12:,.0f}/mo")
    with col4:
        st.metric("Other (takehome)", f"${other_income_annual/12:,.0f}/mo")

    st.metric(
        "Total Monthly Income",
        f"${total_monthly_income:,.0f}",
        delta="Phase 2 after separation",
    )

    # ========== STEP 3: GATHER EXPENSE DATA ==========
    st.markdown("---")
    st.markdown("### 💸 Monthly Expenses")

    # Get expenses from Step 2
    mandatory_expenses = st.session_state.get("monthly_expenses_mandatory", 0)
    negotiable_expenses = st.session_state.get("monthly_expenses_negotiable", 0)
    optional_expenses = st.session_state.get("monthly_expenses_optional", 0)
    total_monthly_expenses = mandatory_expenses + negotiable_expenses + optional_expenses

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Required", f"${mandatory_expenses:,.0f}")
        st.caption("Housing, utilities, food, insurance")
    with col2:
        st.metric("Flexible", f"${negotiable_expenses:,.0f}")
        st.caption("Subscriptions, dining, entertainment")
    with col3:
        st.metric("Optional", f"${optional_expenses:,.0f}")
        st.caption("Hobbies, gifts, luxury")

    st.metric("Total Expenses", f"${total_monthly_expenses:,.0f}")

    # ========== STEP 4: GATHER DEBT DETAILS ==========
    st.markdown("---")
    st.markdown("### [CREDIT] Debt Details")

    has_debt = st.checkbox(
        "I have debt to manage (credit cards, loans, etc.)",
        value=st.session_state.get("has_debt", False),
        key="has_debt",
    )

    cc_balance = 0
    cc_rate = 18.0
    cc_limit = 10000
    other_debt_rate = 5.0

    if has_debt:
        st.caption("Enter each debt type below:")

        col1, col2 = st.columns(2)
        with col1:
            cc_balance = st.number_input(
                "Credit Card Balance ($)",
                min_value=0,
                value=st.session_state.get("cc_balance", 0),
                step=500,
                key="cc_balance",
            )

            cc_rate = st.slider(
                "CC Interest Rate (%)",
                min_value=0.0,
                max_value=30.0,
                value=st.session_state.get("cc_rate", 18.0),
                step=0.5,
                key="cc_rate",
            )

            cc_limit = st.number_input(
                "Credit Card Limit ($)",
                min_value=0,
                value=st.session_state.get("cc_limit", 10000),
                step=1000,
                key="cc_limit",
                help="Your total credit card limit",
            )

        with col2:
            car_loan = st.number_input(
                "Car Loan ($)",
                min_value=0,
                value=st.session_state.get("car_loan", 0),
                step=500,
                key="car_loan",
            )

            student_loans = st.number_input(
                "Student Loans ($)",
                min_value=0,
                value=st.session_state.get("student_loans", 0),
                step=500,
                key="student_loans",
            )

            personal_debt = st.number_input(
                "Other Debt ($)",
                min_value=0,
                value=st.session_state.get("personal_debt", 0),
                step=500,
                key="personal_debt",
            )

            car_loan + student_loans + personal_debt

            other_debt_rate = st.slider(
                "Average Interest Rate on Loans (%)",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.get("loan_rate", 5.0),
                step=0.5,
                key="loan_rate",
            )

    # ========== STEP 5: RUN THEMIS ENGINE ==========
    st.markdown("---")
    st.markdown("### [GOAL] THEMIS Analysis")

    # Calculate monthly gap
    monthly_gap = total_monthly_income - total_monthly_expenses

    # Create THEMIS input objects
    financial_position = FinancialPosition(
        current_savings=current_savings,
        current_debt=current_debt,
        cc_balance=cc_balance,
        cc_limit=cc_limit,
        cc_rate_percent=cc_rate,
        avg_loan_rate_percent=other_debt_rate,
        monthly_income=total_monthly_income,
        monthly_expenses_required=mandatory_expenses,
        monthly_expenses_flexible=negotiable_expenses,
        monthly_expenses_optional=optional_expenses,
    )

    expense_breakdown = ExpenseBreakdown(
        required=mandatory_expenses,
        flexible=negotiable_expenses,
        optional=optional_expenses,
    )

    timing = TimingFactors(
        months_to_pension=1,
        months_to_disability_decision=2,
        months_to_job=st.session_state.get("job_search_months", 3),
        months_in_current_status=0,
    )

    # Run THEMIS engine
    themis_engine = ThemisDecisionEngine()
    themis_recommendation = themis_engine.analyze_situation(
        financial_position=financial_position,
        expense_breakdown=expense_breakdown,
        timing=timing,
        available_monthly_surplus=monthly_gap if monthly_gap != 0 else None,
    )

    # Display THEMIS recommendation
    st.success(f"### ✓ THEMIS Recommendation: {themis_recommendation.strategy}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Debt Paydown",
            f"{themis_recommendation.debt_paydown_percent:.0%}",
            delta="of available funds",
        )
    with col2:
        st.metric(
            "Savings",
            f"{themis_recommendation.savings_percent:.0%}",
            delta="of available funds",
        )
    with col3:
        st.metric(
            "Expense Reduction",
            f"{themis_recommendation.expense_reduction_percent:.0%}",
            delta="of available funds",
        )

    # Show detailed rationale
    with st.expander("[PROFILE] See Full THEMIS Analysis", expanded=True):
        st.markdown(themis_recommendation.explain())

    # Show risk factors
    if themis_recommendation.risk_factors:
        st.warning("**Potential Risks:**\n" + "\n".join(f"- {risk}" for risk in themis_recommendation.risk_factors))

    # Show quick wins
    if themis_recommendation.quick_wins:
        st.info("**Quick Wins to Implement:**\n" + "\n".join(f"✓ {win}" for win in themis_recommendation.quick_wins))

    # ========== STEP 6: USER CONFIRMATION ==========
    st.markdown("---")
    st.markdown("### ✓ Accept THEMIS Recommendation?")

    accept_themis = st.radio(
        "Do you accept this THEMIS recommendation?",
        ["Yes, use THEMIS recommendation", "No, choose custom strategy"],
        key="accept_themis_recommendation",
        horizontal=True,
    )

    if accept_themis == "Yes, use THEMIS recommendation":
        st.session_state.themis_strategy_approved = True
        st.session_state.debt_payoff_priority = "themis"
        st.session_state.transition_strategy_selected = themis_recommendation.strategy
        st.success(f"[OK] THEMIS strategy saved: {themis_recommendation.strategy}")
    else:
        st.session_state.themis_strategy_approved = False

        # Fallback to manual selection
        st.markdown("---")
        st.markdown("### 🔧 Custom Strategy Selection")
        st.write("Choose your own allocation if you prefer a different approach:")

        strategy = st.radio(
            "Select your preferred strategy:",
            [
                "🛡️ Build Reserves (Prioritize savings)",
                "[FAST] Aggressive Payoff (Reduce debt burden)",
                "⚖️ Balanced (Mix of both)",
                "[GOAL] Use THEMIS (My calculated recommendation)",
            ],
            index=3,
            key="debt_payoff_priority_display",
        )

        strategy_map = {
            "🛡️ Build Reserves (Prioritize savings)": "minimum",
            "[FAST] Aggressive Payoff (Reduce debt burden)": "aggressive",
            "⚖️ Balanced (Mix of both)": "balanced",
            "[GOAL] Use THEMIS (My calculated recommendation)": "themis",
        }
        st.session_state["debt_payoff_priority"] = strategy_map.get(strategy, "balanced")
        st.session_state.transition_strategy_selected = strategy

        # Show explanation for selected strategy
        if "Reserves" in strategy:
            st.success(
                """
                **Build Reserves Strategy:**
                - Keep minimum debt payments
                - Build 3-6 month emergency fund
                - Better for uncertain job market
                """
            )
        elif "Aggressive" in strategy:
            st.error(
                """
                **Aggressive Payoff Strategy:**
                - Pay down high-interest debt first
                - Reduces monthly expense burden
                - Requires discipline during transition
                """
            )
        elif "THEMIS" in strategy:
            recommendation_text = f"Using THEMIS recommendation: " f"{themis_recommendation.strategy}"
            st.info(recommendation_text)
        else:
            balanced_strategy_text = """
                **Balanced Strategy:**
                - Split discretionary funds between debt & savings
                - Moderate risk, moderate reward
                - Most flexible approach
                """
            st.info(balanced_strategy_text)

    st.markdown("---")

    # Store THEMIS data for later use
    st.session_state.themis_recommendation = themis_recommendation

    st.info(f"**Step 3 Complete:** {get_step_summary(3)}")

    return True  # Step 3 is always valid


def step3_benefits() -> bool:
    """
    STEP 3: Military Benefits (The Unknowns)

    Collects: VA Disability Rating, GI Bill plan, Healthcare choice
    Returns: True (always valid - defaults provided)
    """
    st.header("🎖️ Step 3: Military Benefits (The Unknowns)")
    st.write("These factors affect your income and healthcare options.")

    # ========== VA DISABILITY RATING ==========
    st.subheader("VA Disability Rating")
    st.caption("This drives your VA benefits and healthcare eligibility " "(Set in Step 2)")

    va_rating = st.session_state.get("current_va_disability_rating", 30)
    monthly_va = (va_rating / 10) * 130
    annual_va = monthly_va * 12

    # Display the actual dollar amount prominently
    if va_rating == 0:
        st.warning(f"**At {va_rating}% rating:** No VA disability benefit")
    else:
        st.success(f"**At {va_rating}% rating:** ${monthly_va:,.0f}/month " f"(${annual_va:,.0f}/year)")

    # Show program details
    if va_rating >= 50:
        st.info(
            "✓ **CRDP Eligible:** Concurrent Retirement & " "Disability Pay - Get full pension + VA benefit " "combined"
        )
    elif va_rating >= 20:
        st.info(
            "• **Offset to Pension:** VA benefit reduces "
            "(offsets) your military retirement pay, but "
            "combined income protected"
        )
    else:
        st.info("• **Healthcare Access:** Eligible for VA " "healthcare based on service-connection")

    # Show impact visualization as expandable table
    with st.expander("[STATS] VA Rating Impact Reference"):
        import pandas as pd

        impact_ratings = [0, 10, 20, 30, 50, 70, 100]
        impacts_data = []
        for r in impact_ratings:
            # Use the same calculation as Step 2: ~$130/month per 10%
            monthly_va = (r / 10) * 130
            annual_va = monthly_va * 12
            impacts_data.append(
                {
                    "Rating": f"{r}%",
                    "Monthly Benefit": f"${monthly_va:,.0f}",
                    "Annual Benefit": f"${annual_va:,.0f}",
                }
            )

        df = pd.DataFrame(impacts_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("[INFO] Approximate VA disability benefits by rating " "(updated 2024-2025 rates)")

    st.markdown("---")

    # ========== GI BILL ==========
    st.subheader("📚 Education Benefits (GI Bill)")

    use_gi = st.checkbox(
        "Plan to use GI Bill?",
        value=st.session_state.get("plan_to_use_gi_bill", False),
        key="plan_to_use_gi_bill",
    )

    if use_gi:
        from src.model_layer.bah_lookup import get_bah_rate

        col1, col2 = st.columns(2)

        with col1:
            gi_type = st.radio(
                "Which GI Bill?",
                ["post_9_11", "montgomery"],
                format_func=lambda x: ("Post-9/11 GI Bill" if x == "post_9_11" else "Montgomery GI Bill"),
                key="gi_bill_type",
                horizontal=False,
            )

            st.selectbox(
                "Education level",
                ["bachelor", "master", "phd", "vocational", "bootcamp"],
                index=[
                    "bachelor",
                    "master",
                    "phd",
                    "vocational",
                    "bootcamp",
                ].index(st.session_state.get("education_level", "bachelor")),
                key="education_level",
            )

        with col2:
            months_available = st.slider(
                "Months available",
                min_value=0,
                max_value=36,
                value=st.session_state.get("gi_months_available", 36),
                step=1,
                key="gi_months_available",
                help="Typically 36 months, or more if Ruskin Ruling approved",
            )

            # Auto-calculate BAH from retirement location
            retirement_location = st.session_state.get("retirement_location", "Austin, TX (Metropolitan area)")
            auto_bah = get_bah_rate(retirement_location)

            bah_input_method = st.radio(
                "School location BAH:",
                ["Use retirement location", "Custom amount"],
                key="bah_input_method",
                horizontal=True,
            )

            if bah_input_method == "Use retirement location":
                bah_estimate = auto_bah
                st.session_state["bah_estimate"] = auto_bah
                st.caption(f"📍 Using {retirement_location} rate: ${auto_bah:,}/mo")
            else:
                bah_estimate = st.number_input(
                    "Estimated monthly BAH",
                    min_value=0,
                    value=st.session_state.get("bah_estimate", 2000),
                    step=100,
                    key="bah_estimate",
                    help="Enter custom BAH if school in different location",
                )

        # Show scenarios
        with st.expander("[INFO] GI Bill Impact Examples"):
            col_ex1, col_ex2, col_ex3 = st.columns(3)

            with col_ex1:
                st.metric(
                    "BAH Benefit (tax-free)",
                    (f"${bah_estimate:,.0f}/mo" if gi_type == "post_9_11" else "N/A"),
                    delta=(f"${bah_estimate * months_available:,.0f} total" if gi_type == "post_9_11" else ""),
                )

            with col_ex2:
                book_stipend = 41.67 if gi_type == "post_9_11" else 0
                st.metric(
                    "Book Stipend",
                    (f"${book_stipend:.0f}/mo" if gi_type == "post_9_11" else "$0/mo"),
                    delta=(f"${int(book_stipend * months_available):,.0f} total" if gi_type == "post_9_11" else ""),
                )

            with col_ex3:
                total_value = (bah_estimate + book_stipend) * months_available if gi_type == "post_9_11" else 200000
                st.metric(
                    f"{months_available}-Month Total",
                    f"${int(total_value):,.0f}",
                    delta="for education",
                )
        st.checkbox(
            "Transfer unused benefits to spouse/children?",
            value=st.session_state.get("gi_bill_transfer_eligible", False),
            key="gi_bill_transfer_eligible",
            help="Requires 10-year commitment from separation date",
        )

    st.markdown("---")

    # ========== HEALTHCARE ==========
    st.subheader("🏥 Healthcare Plan Choice")
    st.caption("Affects your monthly expenses and coverage options")

    healthcare_plan = st.radio(
        "Which healthcare plan after separation?",
        ["tricare_select", "tricare_prime", "va_health", "private_aca"],
        index=[
            "tricare_select",
            "tricare_prime",
            "va_health",
            "private_aca",
        ].index(st.session_state.get("healthcare_plan_choice", "tricare_select")),
        format_func=lambda x: {
            "tricare_select": "TRICARE Select",
            "tricare_prime": "TRICARE Prime",
            "va_health": "VA Healthcare",
            "private_aca": "Private/ACA",
        }[x],
        key="healthcare_plan_choice",
        horizontal=False,
    )

    # Healthcare cost comparison table
    with st.expander("[MONEY] Healthcare Cost Comparison"):
        import pandas as pd

        from src.data_models import TransitionProfile
        from src.model_layer.healthcare_model import (
            calculate_healthcare_benefits,
        )

        # Create a temporary profile to calculate healthcare costs
        temp_profile = TransitionProfile(
            target_city=st.session_state.get("target_city", "Austin, TX"),
            current_va_disability_rating=st.session_state.get("current_va_disability_rating", 0),
        )

        # Calculate costs for each plan
        plans = ["tricare_select", "tricare_prime", "va_health", "private_aca"]
        plan_names = [
            "TRICARE Select",
            "TRICARE Prime",
            "VA Healthcare",
            "Private/ACA",
        ]
        costs = []

        for plan_key, plan_name in zip(plans, plan_names):
            try:
                benefit = calculate_healthcare_benefits(temp_profile, plan_type=plan_key)
                annual_cost = benefit.get("annual_cost", 0)
                costs.append(
                    {
                        "Plan": plan_name,
                        "Annual Enrollment": benefit.get("enrollment_fee", "$0"),
                        "Annual Deductible": benefit.get("deductible", "$0"),
                        "Office Visit Copay": benefit.get("copay_office", "$0"),
                        "ER Copay": benefit.get("copay_er", "$0"),
                        "Est. Annual Cost": f"${int(annual_cost):,}",
                        "Best For": {
                            "tricare_select": "Flexibility + lower cost",
                            "tricare_prime": "Heavy users",
                            "va_health": "High disability rating",
                            "private_aca": "Non-military",
                        }.get(plan_key, "N/A"),
                    }
                )
            except Exception:
                # Fallback if model call fails
                costs.append(
                    {
                        "Plan": plan_name,
                        "Annual Enrollment": "See details",
                        "Annual Deductible": "See details",
                        "Office Visit Copay": "See details",
                        "ER Copay": "See details",
                        "Est. Annual Cost": "Varies",
                        "Best For": "Contact provider",
                    }
                )

        df_healthcare = pd.DataFrame(costs)
        st.dataframe(df_healthcare, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Show selected plan cost
        plan_descriptions = {
            "tricare_select": ("TRICARE Select - Good balance of cost and flexibility"),
            "tricare_prime": ("TRICARE Prime - Best if frequent healthcare user"),
            "va_health": ("VA Healthcare - Excellent if eligible (50%+ rating)"),
            "private_aca": ("Private/ACA - Alternative if no military benefits"),
        }
        st.caption("[INFO] **Your Selection:** " + plan_descriptions.get(healthcare_plan, "Select a plan"))

    st.markdown("---")

    # Mini-summary
    st.info(f"**Benefits Summary:** {get_step_summary(3)}")

    return True  # Step 3 always valid


def step4_transition() -> bool:
    """
    STEP 4: Your Transition Plan (Adjustable)

    Collects: Job timeline, Target salary, Location, Filing status
    Integrates: Salary predictor
    Returns: True if salary > 0 and job months valid
    """
    st.header("🚀 Step 4: Your Transition Plan")
    st.write("Define your job search timeline and target income.")

    # ========== JOB SEARCH TIMELINE ==========
    st.subheader("Job Search Timeline")

    # Get separation date to calculate actual start work date
    separation_date = st.session_state.get("user_separation_date", None)

    help_text = "Negative = before separation (landed job early). " "Positive = after separation (job search period)."
    job_months = st.slider(
        "Months until you start your new job (relative to separation date)",
        min_value=-2,
        max_value=12,
        value=st.session_state.get("job_search_months", 6),
        step=1,
        key="job_search_months",
        help=help_text,
    )

    if separation_date:
        from datetime import timedelta

        sep_date = pd.to_datetime(separation_date)
        work_start_date = sep_date + timedelta(days=job_months * 30)
        # Approximate months as 30 days
        st.info(f"📅 You'll start work around: " f"**{work_start_date.strftime('%B %Y')}**")
    else:
        st.warning("Please set your separation date in Step 1 first")

    if job_months < 0:
        st.success(f"[OK] Great! You're starting {abs(job_months)} months " f"BEFORE separation - no income gap!")
    elif job_months == 0:
        st.info("You'll start work right at separation - minimal gap")
    else:
        st.caption(f"⏳ You'll have a {job_months}-month income gap to " f"cover with savings/pension")

    # ========== WHAT-IF ANALYSIS: Job Search Impact ==========
    # Show financial impact of job search timeline change
    try:
        from .whatif_tools import test_job_delay

        # Build current profile to use as baseline
        profile = build_profile_from_session()

        # Get default job search months (typically 6)
        default_job_months = 6

        # Only show what-if if user changed the value
        if job_months != default_job_months:
            st.markdown("---")
            st.subheader(f"[MONEY] Financial Impact: {job_months}-Month Timeline")

            # Run what-if scenario
            scenario = test_job_delay(profile, job_months)

            # Display comparison
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Monthly Gap (Phase 1)",
                    f"${scenario.variant_metrics.get('phase1_gap', 0):,.0f}",
                    delta=f"vs ${scenario.baseline_metrics.get('phase1_gap', 0):,.0f} baseline",
                )

            with col2:
                st.metric(
                    "Total Gap (All Months)",
                    f"${scenario.variant_metrics.get('total_gap', 0):,.0f}",
                    delta="Amount needed from savings",
                )

            with col3:
                runway = scenario.variant_metrics.get("runway_months", 0)
                st.metric("Runway (Months)", f"{runway:.1f}", delta="Before running out of savings")

            # Show key insights
            if scenario.key_insights:
                with st.expander("[STATS] Detailed Impact Analysis"):
                    for insight in scenario.key_insights:
                        st.write(f"• {insight}")
    except Exception as e:
        # Silent fail - what-if is supplementary
        pass

    st.markdown("---")

    # ========== DESIRED CAREER FIELD ==========
    st.subheader("[GOAL] Desired Career Field")
    st.write("Select your target field to help estimate realistic salary ranges.")

    career_fields = {
        "technology": ("Technology/IT (Software, Systems, Cybersecurity)"),
        "data_scientist": ("Data Science (Machine Learning, AI, Analytics)"),
        "data_analyst": ("Data Analytics (Analytics, BI, Business Intelligence)"),
        "operations_research": ("Operations Research (Optimization, Modeling, Analysis)"),
        "management": ("Management/Leadership (Program Manager, Director)"),
        "defense": "Defense Contractor (Intelligence, Engineering)",
        "healthcare": ("Healthcare (Nursing, Clinical, Administration)"),
        "government": ("Government/Federal (Civil Service, GS)"),
        "finance": ("Finance/Accounting (Banking, Accounting, Analysis)"),
        "consulting": ("Consulting (Business, Management, Strategy)"),
        "education": ("Education/Training (Teaching, Instructional Design)"),
        "logistics": ("Logistics/Supply Chain (Operations, Planning)"),
        "sales": ("Sales/Business Development (Account Exec, Sales)"),
        "other": "Other/Undecided",
    }

    help_text = "This helps align salary estimates with industry norms"
    career_field = st.selectbox(
        "Select Your Target Career Field",
        options=list(career_fields.keys()),
        format_func=lambda x: career_fields[x],
        index=list(career_fields.keys()).index(st.session_state.get("target_career_field", "technology")),
        key="target_career_field",
        help=help_text,
    )

    st.caption(f"📍 Selected: {career_fields[career_field]}")

    st.markdown("---")

    # ========== TARGET SALARY ==========
    st.subheader("Target Annual Salary")
    st.write("Enter your target salary, or use the salary predictor " "to estimate based on percentile scenarios.")

    salary = st.number_input(
        "Your Target Annual Salary",
        min_value=0.0,
        value=float(st.session_state.get("estimated_annual_salary", 130000.0)),
        step=5000.0,
        key="estimated_annual_salary",
        help="Your estimated civilian salary in the first year",
    )

    # Show salary range scenarios using profile data
    with st.expander("[STATS] View Salary Range Scenarios", expanded=False):
        st.info(
            f"These scenarios show conservative, mid, and optimistic "
            f"salary outcomes for **{career_fields[career_field]}**."
        )

        # Create a temporary profile with current salary estimate
        from src.data_models import TransitionProfile
        from src.model_layer.salary_predictor import estimate_salary_range

        try:
            temp_profile = TransitionProfile(estimated_annual_salary=salary)
            range_dict = estimate_salary_range(temp_profile, low_percentile=0.75, high_percentile=1.25)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Conservative (25%)", f"${range_dict['low']:,.0f}")
            with col2:
                st.metric("Target (Mid)", f"${range_dict['mid']:,.0f}")
            with col3:
                st.metric("Optimistic (25%+)", f"${range_dict['high']:,.0f}")

            st.caption("These ranges help you test different outcomes " "in the 'What-If' scenarios later.")
        except Exception as e:
            error_msg = f"Could not generate salary scenarios: {str(e)}"
            st.warning(error_msg)

    st.markdown("---")

    # ========== LOCATION ==========
    st.subheader("🏠 Retirement Location (From Step 1)")

    # Display the location already selected in Step 1
    retirement_location = st.session_state.get("retirement_location", "Not set")
    retirement_state = st.session_state.get("retirement_state", "")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"📍 **Location:** {retirement_location}")

    with col2:
        state_text = retirement_state if retirement_state else "Auto-detected"
        st.info(f"🗺️ **State:** {state_text}")

    st.caption("This location was set in Step 1 and is used for BAH, " "healthcare costs, and tax calculations.")

    # Store the retirement location for transition calculations
    st.session_state["target_city"] = retirement_location
    st.session_state["target_state"] = retirement_state

    st.markdown("---")

    # ========== TAX FILING ==========
    st.subheader("[MONEY] Tax Filing Status")
    st.write("Automatically set based on your marital status from Step 1, " "but you can override if needed.")

    # Auto-determine tax filing status from marital status
    marital_status = st.session_state.get("user_marital_status", "Single")
    auto_filing = {
        "Single": "single",
        "Married": "married_joint",
        "Divorced/Widowed": "head_of_household",
    }.get(marital_status, "single")

    # Display what was selected in Step 1
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"👤 **Step 1 Marital Status:** {marital_status}")
    with col2:
        auto_filing_display = auto_filing.replace("_", " ").title()
        st.info(f"[PROFILE] **Recommended Filing:** {auto_filing_display}")
    st.radio(
        "Tax Filing Status",
        [
            "single",
            "married_joint",
            "married_separate",
            "head_of_household",
        ],
        index=[
            "single",
            "married_joint",
            "married_separate",
            "head_of_household",
        ].index(st.session_state.get("filing_status", auto_filing)),
        format_func=lambda x: {
            "single": "Single",
            "married_joint": "Married Filing Jointly",
            "married_separate": "Married Filing Separately",
            "head_of_household": "Head of Household",
        }[x],
        key="filing_status",
        horizontal=True,
    )

    st.caption(
        "[INFO] Modify only if your filing status differs from your "
        "marital status (e.g., married but filing separately for "
        "tax purposes)."
    )

    st.markdown("---")

    # Mini-summary
    st.info(f"**Transition Plan:** {get_step_summary(4)}")

    return salary > 0 and job_months >= -2  # Valid if salary set and job timing is reasonable
