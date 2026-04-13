"""
Wizard UI orchestrator.

Handles complete flow: Step 1 → 4 → Summary → What-Ifs
Navigation: back/forward buttons, progress indicator
"""

import logging
import traceback

import streamlit as st

from .session_manager import (
    build_profile_from_session,
    clear_wizard_session,
    initialize_wizard_session,
    save_profile_to_file,
)
from .wizard_flow import (
    step1_profile,
    step2_finances,
    step3_benefits,
    step3_debt_vs_savings,
    step4_transition,
)
from .summary_engine import format_months_value, generate_decision_summary
from .what_if_runner import run_what_if_analysis_for_question
# Import the simplified wizard with GLM salary integration
from ..ui_layer.wizard_simplified import run_simplified_wizard

logger = logging.getLogger(__name__)


def initialize_wizard_state():
    """Initialize wizard step tracking in session state."""
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_completed_steps" not in st.session_state:
        st.session_state.wizard_completed_steps = set()


def display_progress_bar():
    """Show progress through wizard steps."""
    steps = ["Profile", "Finances", "Benefits", "Transition", "Summary"]
    current = st.session_state.get("wizard_step", 1)

    # Format each step based on current progress
    formatted_steps = []
    for i, step in enumerate(steps):
        if i + 1 == current:
            # Current step - bold
            formatted_steps.append(f"**{step}**")
        elif i + 1 < current:
            # Completed step - strikethrough
            formatted_steps.append(f"~~{step}~~")
        else:
            # Future step - normal
            formatted_steps.append(step)

    # Join the formatted steps with arrows
    progress_text = " → ".join(formatted_steps)

    st.markdown(f"### {progress_text}")
    st.progress((current - 1) / 6, text=f"Step {current} of 6")


def display_cumulative_summary():
    """
    Display comprehensive cumulative summary of all collected data.

    Updates as user progresses through steps - shows everything
    filled in so far.
    """
    try:
        # Build profile from session for reference (used in error handling)
        _ = build_profile_from_session()

        st.markdown("### [PROFILE] Complete Profile Summary")

        # Show completion percentage
        wizard_step = st.session_state.get("wizard_step", 1)
        completion = min(int((wizard_step / 6) * 100), 100)
        st.progress(completion / 100, text=f"{completion}% Complete")

        # ===== STEP 1: MILITARY BACKGROUND =====
        st.subheader("1️⃣ Military Background")
        rank = st.session_state.get("user_rank", "—")
        yos = st.session_state.get("user_years_of_service", "—")
        branch = st.session_state.get("user_service_branch", "—")
        sep_date_obj = st.session_state.get("user_separation_date")
        sep_date = sep_date_obj.strftime("%b %d, %Y") if sep_date_obj else "—"
        marital = st.session_state.get("user_marital_status", "—")
        retire_loc = st.session_state.get("retirement_location", "—")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rank", rank)
            st.metric("Service", branch)
        with col2:
            st.metric("Years", f"{yos}y" if yos != "—" else "—")
            st.metric("Status", marital)

        st.write(f"**Separation:** {sep_date}")
        st.write(f"**Retire Location:** {retire_loc}")
        st.divider()

        # ===== STEP 2: FINANCIAL PICTURE =====
        st.subheader("2️⃣ Financial Picture")

        # Income
        # Stored as monthly pretax
        pension_monthly = st.session_state.get("military_pension", 0)
        # SBP deduction
        sbp_cost = st.session_state.get("sbp_monthly_cost", 0)
        # Health insurance, taxes, etc.
        pension_pretax_deductions = st.session_state.get("pension_pretax_expense", 0)
        # Take-home pension
        pension_takehome = pension_monthly - sbp_cost - pension_pretax_deductions

        # Validate and clamp pension to prevent negative values
        if pension_takehome < 0 and pension_monthly > 0:
            # Show warning about deductions
            st.warning(
                f"[WARNING] Your deductions exceed your pension!\n\n"
                f"Pension: ${pension_monthly:,.0f}/mo\n"
                f"SBP Cost: ${sbp_cost:,.0f}/mo\n"
                f"Other Deductions: ${pension_pretax_deductions:,.0f}/mo\n\n"
                f"**Reduce your deductions in Step 2 to prevent "
                f"negative income.**"
            )
            pension_takehome = 0

        # Stored as annual
        va_annual = st.session_state.get("va_annual_benefit", 0)
        spouse_income_annual = st.session_state.get("spouse_income_annual", 0)
        other_income_annual = st.session_state.get("other_income_annual", 0)
        current_paycheck = st.session_state.get("current_paycheck_monthly", 0)

        # Calculate monthly values
        va_monthly = va_annual / 12
        spouse_monthly = spouse_income_annual / 12
        other_monthly = other_income_annual / 12

        # Phase 1 income calculation
        # Active duty paycheck (takehome) + spouse (takehome) +
        # other (takehome)
        total_monthly_income = current_paycheck + spouse_monthly + other_monthly

        # Phase 2 income calculation
        # Corrected VA disability below 50% offset handling:
        # - 50%+: CRDP - get both pension (taxed) + VA disability (tax-free)
        # - 20-49%: Offset - VA (tax-free) replaces pension (taxed), different take-home
        # - <20%: Pension only - VA doesn't offset at this level
        va_rating = st.session_state.get("current_va_disability_rating", 0)
        
        # Use corrected VA offset calculation
        from src.model_layer.va_offset_calculator import calculate_va_offset_income
        
        # Estimate federal tax rate (22% default for most military retirees)
        estimated_tax_rate = 0.22
        
        va_calc = calculate_va_offset_income(
            pension_monthly_pretax=pension_monthly,
            sbp_monthly_cost=sbp_cost,
            pension_pretax_deductions=pension_pretax_deductions,
            va_disability_rating=va_rating,
            va_monthly_benefit=va_monthly,
            estimated_tax_rate=estimated_tax_rate,
        )
        
        # Military income from corrected VA offset
        military_takehome = va_calc["total_monthly_income"]
        total_phase2_income = military_takehome + spouse_monthly + other_monthly
        
        # Set phase 2 VA note based on income type
        if va_calc["income_type"] == "crdp":
            phase2_va_note = "[OK] CRDP Eligible: Full pension + full VA benefit combined"
        elif va_calc["income_type"] == "offset":
            if va_calc["primary_income_source"] == "va_disability":
                phase2_va_note = f"[INFO] VA Offset: Tax-free VA (${va_monthly:,.0f}) better than taxed pension (${pension_takehome:,.0f})"
            else:
                phase2_va_note = f"[INFO] VA Offset: Military pension (${pension_takehome:,.0f}) still better than VA (${va_monthly:,.0f})"
        else:
            if va_rating > 0:
                phase2_va_note = f"[INFO] Below Offset Level: Military pension only (VA {va_rating}% is <20%)"
            else:
                phase2_va_note = ""

        st.markdown("**Phase 1 Income Sources (Active Duty - Takehome)**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Active Duty",
                f"${current_paycheck:,.0f}" if current_paycheck else "—",
            )
            st.metric("Spouse", f"${spouse_monthly:,.0f}" if spouse_monthly else "—")
        with col2:
            st.metric(
                "Other Income",
                f"${other_monthly:,.0f}" if other_monthly else "—",
            )
            st.metric(
                "Total",
                (f"${total_monthly_income:,.0f}" if total_monthly_income else "—"),
            )

        st.markdown("**Phase 2 Income Sources (After Separation - Takehome)**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Pension (pretax)",
                f"${pension_monthly:,.0f}" if pension_monthly else "—",
            )
            st.metric(
                "Deductions",
                (f"-${sbp_cost + pension_pretax_deductions:,.0f}" if (sbp_cost + pension_pretax_deductions) else "—"),
            )
            # Display military income based on VA offset type
            if va_rating > 0:
                if va_calc["income_type"] == "crdp":
                    # CRDP: Show both components
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric(
                            "Pension (taxed)",
                            f"${pension_takehome:,.0f}" if pension_takehome else "—",
                        )
                    with col_b:
                        st.metric(
                            "VA Disability (tax-free, +)",
                            f"${va_monthly:,.0f}" if va_monthly else "—",
                            help="CRDP: Both combined"
                        )
                elif va_calc["income_type"] == "offset":
                    # OFFSET: VA replaces pension, show which is primary
                    if va_calc["primary_income_source"] == "va_disability":
                        st.metric(
                            "💵 Primary Income: VA Disability (tax-free, REPLACES pension)",
                            f"${va_monthly:,.0f}" if va_monthly else "—",
                            help=f"Tax-free VA ${va_monthly:,.0f} is better than taxed pension ${pension_takehome:,.0f}"
                        )
                    else:
                        st.metric(
                            "💵 Primary Income: Military Pension (after-tax)",
                            f"${pension_takehome:,.0f}" if pension_takehome else "—",
                            help=f"Pension ${pension_takehome:,.0f} is better than VA ${va_monthly:,.0f}"
                        )
                else:
                    # PENSION ONLY: <20% rating
                    st.metric(
                        "Pension (takehome, taxed)",
                        f"${pension_takehome:,.0f}" if pension_takehome else "—",
                        help=f"VA {va_rating}% does not offset; pension only"
                    )
            else:
                st.metric(
                    "Pension (takehome, taxed)",
                    f"${pension_takehome:,.0f}" if pension_takehome else "—",
                )
        with col2:
            st.metric(
                "Spouse (takehome)",
                f"${spouse_monthly:,.0f}" if spouse_monthly else "—",
            )
            st.metric(
                "Other (takehome)",
                f"${other_monthly:,.0f}" if other_monthly else "—",
            )
            st.metric(
                "Military Income (corrected)",
                f"${military_takehome:,.0f}" if military_takehome else "—",
                help=f"Accounts for VA offset and tax-free status ({va_calc['income_type']})"
            )
            st.metric(
                "Total Phase 2",
                f"${total_phase2_income:,.0f}" if total_phase2_income else "—",
            )

        if phase2_va_note:
            st.caption(phase2_va_note)

        # Expenses - use adjusted amounts if available, otherwise use sliders
        mandatory = st.session_state.get("monthly_expenses_mandatory", 0)
        negotiable = st.session_state.get("monthly_expenses_negotiable", 0)
        optional = st.session_state.get("monthly_expenses_optional", 0)

        # Check if user adjusted amounts in the classification adjuster
        adjusted_amounts = st.session_state.get("adjusted_amounts", {})

        if adjusted_amounts:
            # If adjustments exist, recalculate totals from adjusted amounts
            total_monthly_exp = sum(adjusted_amounts.values())
            st.markdown("**Monthly Expenses (Adjusted)**")
        else:
            # Otherwise use the slider values
            total_monthly_exp = mandatory + negotiable + optional
            st.markdown("**Monthly Expenses**")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Required", f"${mandatory:,.0f}" if mandatory else "—")
        with col2:
            st.metric("Flexible", f"${negotiable:,.0f}" if negotiable else "—")
        with col3:
            st.metric("Optional", f"${optional:,.0f}" if optional else "—")

        if total_monthly_exp > 0:
            yearly_exp = total_monthly_exp * 12
            info_text = f"**Total Monthly:** ${total_monthly_exp:,.0f} " f"(${yearly_exp:,.0f}/yr)"
            st.info(info_text)
            if adjusted_amounts:
                num_items = len(adjusted_amounts)
                caption_text = f"📝 {num_items} expense items adjusted from CSV"
                st.caption(caption_text)

        # Assets & Debts
        savings = st.session_state.get("current_savings", 0)
        debt = st.session_state.get("current_debt", 0)

        st.markdown("**Assets & Liabilities**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Savings", f"${savings:,.0f}" if savings else "—")
        with col2:
            st.metric("Debt", f"${debt:,.0f}" if debt else "—")

        st.divider()

        # ===== STEP 3: DEBT VS SAVINGS STRATEGY =====
        st.subheader("3️⃣ Debt vs Savings Strategy")

        has_debt = st.session_state.get("has_debt", False)
        strategy = st.session_state.get("debt_payoff_priority", "balanced")
        target_savings = st.session_state.get("target_savings_during_transition", 0)

        # Debt breakdown
        if has_debt:
            cc_balance = st.session_state.get("cc_balance", 0)
            car_loan = st.session_state.get("car_loan", 0)
            other_debt = st.session_state.get("other_debt", 0)

            st.markdown("**Debt Inventory**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Credit Cards",
                    f"${cc_balance:,.0f}" if cc_balance else "—",
                )
            with col2:
                st.metric("Car Loan", f"${car_loan:,.0f}" if car_loan else "—")
            with col3:
                st.metric("Other Debt", f"${other_debt:,.0f}" if other_debt else "—")
        else:
            st.write("✓ No debt reported")

        # Strategy selection
        strategy_labels = {
            "minimum": "🛡️ Build Reserves",
            "aggressive": "[FAST] Aggressive Payoff",
            "balanced": "⚖️ Balanced",
        }
        strategy_display = strategy_labels.get(strategy, "⚖️ Balanced")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Strategy", strategy_display)
        with col2:
            st.metric(
                "Savings Target",
                f"${target_savings:,.0f}" if target_savings else "—",
            )

        st.divider()

        # ===== STEP 4: MILITARY BENEFITS =====
        st.subheader("4️⃣ Military Benefits")

        va_rating = st.session_state.get("current_va_disability_rating", 0)
        healthcare = st.session_state.get("healthcare_plan_choice", "—")
        sbp = st.session_state.get("elect_sbp", False)
        gi_bill = st.session_state.get("plan_to_use_gi_bill", False)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("VA Disability", f"{va_rating}%" if va_rating else "—")
            st.metric("SBP", "✓ Elected" if sbp else "Not elected")
        with col2:
            st.metric("Healthcare", healthcare)
            st.metric("GI Bill", "✓ Yes" if gi_bill else "No")

        # GI Bill details if selected
        if gi_bill:
            gi_type = st.session_state.get("gi_bill_type", "post_9_11")
            months = st.session_state.get("gi_months_available", 36)
            bah = st.session_state.get("bah_estimate", 0)

            st.markdown(f"**GI Bill:** {gi_type}")
            st.write(f"• Months: {months}")
            if bah > 0:
                st.write(f"• BAH: ${bah:,.0f}/month")

        st.divider()

        # ===== STEP 5: TRANSITION PLAN =====
        st.subheader("5️⃣ Transition Plan")

        job_timeline = st.session_state.get("job_search_months", 0)
        job_salary = st.session_state.get("estimated_annual_salary", 0)
        career = st.session_state.get("target_career_field", "—")
        target_city = st.session_state.get("target_city", "—")

        # Map career field
        career_fields = {
            "technology": "🖥️ Technology/IT",
            "data_scientist": "🤖 Data Science",
            "data_analyst": "[STATS] Data Analytics",
            "operations_research": "🔬 Operations Research",
            "management": "[STATS] Management",
            "defense": "🛡️ Defense",
            "healthcare": "⚕️ Healthcare",
            "government": "🏛️ Government",
            "finance": "[MONEY] Finance",
            "consulting": "[CHART] Consulting",
            "education": "🎓 Education",
            "logistics": "📦 Logistics",
            "sales": "💼 Sales",
            "other": "❓ Other",
        }
        career_display = career_fields.get(career, f"❓ {career}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Career Field",
                career_display.split()[-1] if career_display != "—" else "—",
            )
            st.metric("Location", target_city)
        with col2:
            st.metric("Job Search", f"{job_timeline}mo" if job_timeline else "—")
            st.metric("Target Salary", f"${job_salary:,.0f}" if job_salary else "—")

        st.divider()

        # ===== FINANCIAL SUMMARY =====
        if total_monthly_exp > 0 and total_monthly_income > 0:
            st.subheader("💹 Financial Outlook")

            phase1_gap = total_monthly_income - total_monthly_exp

            if phase1_gap < 0:
                st.error(f"**Phase 1 (Active Duty) Gap:** " f"${abs(phase1_gap):,.0f}/month (shortfall)")
                st.write("*Need to cover with savings or job income*")
            else:
                st.success(f"**Phase 1 (Active Duty) Surplus:** " f"${phase1_gap:,.0f}/month")

            # Phase 2 (after separation with pension)
            phase2_gap = total_phase2_income - total_monthly_exp

            if phase2_gap < 0:
                st.error(f"**Phase 2 (Post-Separation) Gap:** " f"${abs(phase2_gap):,.0f}/month (shortfall)")
            else:
                st.success(f"**Phase 2 (Post-Separation) Surplus:** " f"${phase2_gap:,.0f}/month")

            # Phase 3 (with new job)
            if job_salary > 0:
                phase3_monthly = total_phase2_income + (job_salary / 12)
                phase3_surplus = phase3_monthly - total_monthly_exp
                st.success(f"**Phase 3 (New Job) Surplus:** " f"${phase3_surplus:,.0f}/month")

    except Exception as e:
        import traceback

        st.warning(f"Summary is loading... If this persists, there may " f"be an issue: {str(e)}")
        # Log the full error for debugging
        st.caption(f"Debug: {traceback.format_exc()}")


def run_transition_wizard():
    """
    Main wizard flow orchestrator using simplified wizard with GLM salary integration.
    
    Delegates to run_simplified_wizard() which includes:
    - GLM-based salary predictions
    - Step-by-step form flow (1-7)
    - Integrated AI summary
    - Classification adjuster
    """
    # Use the simplified wizard with GLM salary model
    run_simplified_wizard()
    return

    # Legacy code below (kept for reference only)
    st.set_page_config(page_title="Transition Wizard", page_icon="🧙", layout="wide")

    # Initialize state
    initialize_wizard_session()
    initialize_wizard_state()

    st.title("🧙 Transition Wizard")
    st.caption("Step-by-step decision support for military retirement transition")

    display_progress_bar()
    st.divider()

    current_step = st.session_state.wizard_step

    # Track if we're rendering hidden widgets for state persistence
    st.session_state._rendering_hidden_widgets = False

    # LAYOUT: Use 2-column layout for steps 1-5, single column for step 6
    if current_step < 6:
        col_form, col_summary = st.columns(2, gap="medium")

        # Render hidden step widgets to maintain session state
        # (Streamlit requirement) - Skip on Step 6 to avoid block structure issues
        # Note: These don't display to the user but are needed for widget
        # state persistence. Simply render them without capturing -
        # Streamlit will handle the rendering pipeline

        # Set flag to indicate we're rendering hidden widgets
        st.session_state._rendering_hidden_widgets = True

        # Keep Step 1 widgets rendered (hidden) if we're past Step 1
        # This ensures session state is preserved across steps
        if current_step > 1:
            try:
                with st.empty():
                    # Render Step 1 widgets invisibly to maintain state
                    step1_profile()
            except Exception:
                pass  # Silent fail - state preservation only

        # Keep Step 2 widgets rendered (hidden) if we're past Step 2
        # This ensures expense data stays in session state when on Step 3+
        if current_step > 2:
            try:
                with st.empty():
                    # Render Step 2 widgets invisibly to maintain state
                    step2_finances()
            except Exception:
                pass  # Silent fail - state preservation only

        # Keep Step 3 widgets rendered (hidden) if we're past Step 3
        # This ensures debt/savings strategy data stays in session
        # state when on Step 4+
        if current_step > 3:
            try:
                with st.empty():
                    # Render Step 3 widgets invisibly to maintain state
                    step3_debt_vs_savings()
            except Exception:
                pass  # Silent fail - state preservation only

        # Keep Step 4 widgets rendered (hidden) if we're past Step 4
        # This ensures benefits data stays in session state when on Step 5+
        if current_step > 4:
            try:
                with st.empty():
                    # Render Step 4 widgets invisibly to maintain state
                    step3_benefits()
            except Exception:
                pass  # Silent fail - state preservation only

        # Keep Step 5 widgets rendered (hidden) if we're past Step 5
        # This ensures transition plan data stays in session state when on Step 6
        # IMPORTANT: Only render if we're on step 6, not when we're about to
        # render step 5 normally below
        if current_step > 5:
            try:
                with st.empty():
                    # Render Step 5 widgets invisibly to maintain state
                    step4_transition()
            except Exception:
                pass  # Silent fail - state preservation only

        # Clear flag when done with hidden widgets
        st.session_state._rendering_hidden_widgets = False

    # LEFT COLUMN: Input Forms
    if current_step < 6:
        with col_form:
            # STEP 1: Profile
            if current_step == 1:
                st.header("Step 1 of 6: Your Military Profile")
                is_valid = step1_profile()

                st.markdown("---")
                col_nav_1, col_nav_2 = st.columns([1, 1])
                with col_nav_2:
                    if st.button("Next →", key="step1_next", use_container_width=True):
                        if is_valid:
                            # Explicitly persist Step 1 data to session state
                            # before navigating
                            st.session_state.wizard_completed_steps.add(1)
                            st.session_state.wizard_step = 2
                            st.rerun()
                        else:
                            st.error("Please complete all required fields " "before proceeding.")

            # STEP 2: Finances
            elif current_step == 2:
                st.header("Step 2 of 6: Financial Picture")
                try:
                    is_valid = step2_finances()
                except Exception as e:
                    st.error(f"Error loading Step 2: {str(e)}")
                    logger.exception("Error in step2_finances()")
                    is_valid = False

                st.markdown("---")
                col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 1, 1])
                with col_nav_1:
                    if st.button("← Back", key="step2_back", use_container_width=True):
                        st.session_state.wizard_step = 1
                        st.rerun()
                with col_nav_3:
                    if st.button("Next →", key="step2_next", use_container_width=True):
                        if is_valid:
                            st.session_state.wizard_completed_steps.add(2)
                            st.session_state.wizard_step = 3
                            st.rerun()
                        else:
                            st.error("Please complete all required fields " "before proceeding.")

            # STEP 3: Debt vs Savings Strategy
            elif current_step == 3:
                st.header("Step 3 of 6: Debt vs Savings Strategy")
                is_valid = step3_debt_vs_savings()

                st.markdown("---")
                col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 1, 1])
                with col_nav_1:
                    if st.button("← Back", key="step3_back", use_container_width=True):
                        st.session_state.wizard_step = 2
                        st.rerun()
                with col_nav_3:
                    if st.button("Next →", key="step3_next", use_container_width=True):
                        if is_valid:
                            st.session_state.wizard_completed_steps.add(3)
                            st.session_state.wizard_step = 4
                            st.rerun()
                        else:
                            st.error("Please complete all required fields " "before proceeding.")

            # STEP 4: Benefits (formerly STEP 3)
            elif current_step == 4:
                st.header("Step 4 of 6: Military Benefits")
                is_valid = step3_benefits()

                st.markdown("---")
                col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 1, 1])
                with col_nav_1:
                    if st.button("← Back", key="step4_back", use_container_width=True):
                        st.session_state.wizard_step = 3
                        st.rerun()
                with col_nav_3:
                    if st.button("Next →", key="step4_next", use_container_width=True):
                        if is_valid:
                            st.session_state.wizard_completed_steps.add(4)
                            st.session_state.wizard_step = 5
                            st.rerun()
                        else:
                            st.error("Please complete all required fields " "before proceeding.")

            # STEP 5: Transition (formerly STEP 4)
            elif current_step == 5:
                st.header("Step 5 of 6: Transition Plan")
                is_valid = step4_transition()

                st.markdown("---")
                col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 1, 1])
                with col_nav_1:
                    if st.button("← Back", key="step5_back", use_container_width=True):
                        st.session_state.wizard_step = 4
                        st.rerun()
                with col_nav_3:
                    if st.button(
                        "Generate Summary →",
                        key="step5_next",
                        use_container_width=True,
                    ):
                        if is_valid:
                            st.session_state.wizard_completed_steps.add(5)
                            st.session_state.wizard_step = 6
                            st.rerun()
                        else:
                            st.error("Please complete all required fields " "before proceeding.")

    # STEP 6: Summary & What-Ifs - handled separately outside col_form context
    # This avoids block structure issues when not using columns
    if current_step == 6:
        st.header("Step 6 of 6: Decision Summary")
        st.caption("Your personalized coaching session")

        try:
            # Build profile from collected inputs
            profile = build_profile_from_session()

            # Generate decision summary
            summary = generate_decision_summary(profile)

            # Create tabs for Summary and AI Coach
            tab_summary, tab_ai_coach = st.tabs(["[STATS] Summary", "🤖 AI Coach"])

            with tab_summary:
                # Display main decision summary
                display_decision_summary(summary)

                st.divider()

                # Initialize coaching engine
                from src.wizard.coaching_engine import CoachingEngine

                coach = CoachingEngine(profile)

                # Display Assumptions
                st.subheader("[PROFILE] Key Assumptions in Your Plan")
                st.caption(
                    "These are the critical assumptions your plan depends " "on. Let's explore the risks and what-ifs."
                )

                assumptions_df = []
                for assumption in coach.assumptions:
                    assumptions_df.append(
                        {
                            "Category": assumption.category,
                            "Assumption": assumption.description,
                            "Value": str(assumption.value),
                            "Confidence": assumption.confidence,
                            "Impact": assumption.impact,
                        }
                    )

                if assumptions_df:
                    import pandas as pd

                    df = pd.DataFrame(assumptions_df)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Category": st.column_config.TextColumn(width=120),
                            "Assumption": st.column_config.TextColumn(width=300),
                            "Value": st.column_config.TextColumn(width=150),
                            "Confidence": st.column_config.TextColumn(width=100),
                            "Impact": st.column_config.TextColumn(width=100),
                        },
                    )

                st.divider()

                # Display Coaching Questions (Interactive What-Ifs)
                st.subheader("🤔 Let's Test Your Assumptions")
                st.caption(
                    "Click on any question below to explore what-if " "scenarios and rerun your financial models"
                )

                # Display coaching questions as selectable buttons
                question_cols = st.columns(1)
                with question_cols[0]:
                    for i, q in enumerate(coach.coaching_questions):
                        if st.button(
                            f"💭 {q.question}",
                            key=f"coach_q_{i}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_coaching_question = i
                            st.session_state.show_what_if_analysis = True
                            st.rerun()

                        # Show details if this question is selected
                        if st.session_state.get("selected_coaching_question") == i and st.session_state.get(
                            "show_what_if_analysis", False
                        ):
                            with st.container(border=True):
                                st.markdown(f"**Context:** {q.context}")
                                if q.follow_up:
                                    st.markdown(f"**Follow-up:** {q.follow_up}")

                                # Run what-if analysis for this question
                                what_if_result = run_what_if_analysis_for_question(profile, q, coach)

                                if what_if_result:
                                    st.success("[OK] Models rerun with new scenario")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric(
                                            "Monthly Gap",
                                            what_if_result.get("monthly_gap", "N/A"),
                                            delta=what_if_result.get("monthly_gap_delta"),
                                        )
                                    with col2:
                                        st.metric(
                                            "Total Gap",
                                            what_if_result.get("total_gap", "N/A"),
                                            delta=what_if_result.get("total_gap_delta"),
                                        )
                                    with col3:
                                        st.metric(
                                            "Runway",
                                            what_if_result.get("runway", "N/A"),
                                            delta=what_if_result.get("runway_delta"),
                                        )

                                    st.markdown("#### Key Insights")
                                    insights = what_if_result.get("insights", [])
                                    for insight in insights:
                                        st.write(f"• {insight}")

                                    if st.button(
                                        "← Close what-if analysis",
                                        use_container_width=True,
                                        key=f"close_whatif_{i}",
                                    ):
                                        st.session_state.show_what_if_analysis = False
                                        st.session_state.selected_coaching_question = None
                                        st.rerun()

                st.divider()
                st.success("[OK] Summary generated successfully!")
                st.markdown("#### Navigation")
                col1, col2, col3 = st.columns(3)
                with col1:

                    def on_back_to_step5():
                        """Callback for back button - ensures proper state cleanup."""
                        # Clear what-if analysis state before going back
                        st.session_state.show_what_if_analysis = False
                        st.session_state.selected_coaching_question = None
                        # Preserve all step 5 data by setting current step
                        st.session_state.wizard_step = 5

                    st.button("← Back to Step 5", use_container_width=True, on_click=on_back_to_step5)
                with col2:
                    if st.button("📥 Export Profile", use_container_width=True):
                        filename = save_profile_to_file(profile)
                        st.success(f"Profile saved to: {filename}")
                with col3:
                    if st.button("[RESET] Start Over", use_container_width=True):
                        clear_wizard_session()
                        st.session_state.wizard_step = 1
                        st.rerun()

            with tab_ai_coach:
                st.markdown(
                    """
                ### 🤖 Ask your AI Financial Coach

                Have questions about your numbers? Want to explore scenarios?
                Ask anything about your transition plan and I'll rerun the math!

                **Example questions:**
                - "What if my job search takes 12 months?"
                - "Can I cut expenses and still be OK?"
                - "What's my runway with current savings?"
                - "How risky is my salary assumption?"
                - "What if my spouse loses their job?"
                """
                )

                try:
                    from src.wizard.financial_coach import FinancialCoach

                    # Initialize coach with current profile
                    if "financial_coach" not in st.session_state:
                        st.session_state.financial_coach = FinancialCoach(profile)
                        st.session_state.coach_messages = []

                    coach = st.session_state.financial_coach
                    messages = st.session_state.coach_messages

                    # Display chat history
                    for msg in messages:
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])

                    # User input
                    user_question = st.chat_input(
                        "Ask about your financial scenario...",
                        key="coach_question",
                    )

                    if user_question:
                        # Add and display user message
                        with st.chat_message("user"):
                            st.write(user_question)
                        messages.append({"role": "user", "content": user_question})

                        # Get coach response
                        try:
                            result = coach.answer_question(user_question)
                            response_text = result.get("response", "")

                            with st.chat_message("assistant"):
                                # Display source badge
                                source = result.get("source", "fallback")
                                confidence = result.get("confidence", 0.0)
                                
                                if source == "rag":
                                    st.caption("📚 **Knowledge Base** — Military finance data")
                                elif source == "analysis":
                                    st.caption("📊 **Financial Analysis** — Standard calculations")
                                else:
                                    st.caption("🔍 **Keyword Lookup** — Basic reference")
                                
                                # Display main response
                                st.markdown(response_text)
                                
                                # For RAG responses, show confidence and retrieval metrics
                                if source == "rag" and confidence > 0:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Confidence", f"{confidence:.0%}")
                                    with col2:
                                        retrieval_time = result.get("retrieval_time_ms", 0)
                                        st.metric("Retrieval", f"{retrieval_time:.0f}ms")

                                # Show insights if available
                                if result.get("insights"):
                                    with st.expander("[STATS] Key Metrics", expanded=False):
                                        for insight in result["insights"]:
                                            st.write(f"• {insight}")

                            messages.append({"role": "assistant", "content": response_text})
                            st.session_state.coach_messages = messages

                        except Exception as e:
                            st.error(f"Error analyzing your question: {str(e)}")

                except ImportError:
                    st.info("[INFO] AI coach module not available. " "Use the coaching questions tab above instead.")

        except Exception as e:
            st.error(f"[WARNING] Error generating coaching session: {str(e)}")
            st.code(traceback.format_exc(), language="python")
            st.info("Please check your inputs and try again.")
            if st.button("← Back to Step 5"):
                st.session_state.wizard_step = 5
                st.rerun()

    # RIGHT COLUMN: Cumulative Summary (only for steps 1-5)
    if current_step < 6:
        with col_summary:
            display_cumulative_summary()


def display_ai_helper():
    """
    Display AI-powered helper for answering questions throughout the wizard.

    Helps with:
    - Field explanations and guidance
    - What-if analysis
    - Decision recommendations
    """
    st.markdown("### 🤖 AI Assistant")
    st.caption("Ask questions about your options or get guidance")

    # Initialize wizard AI session if needed
    if "wizard_ai_messages" not in st.session_state:
        st.session_state.wizard_ai_messages = []

    if "wizard_ai_handler" not in st.session_state:
        try:
            from src.ai_layer.chat_flow import ChatFlowHandler

            st.session_state.wizard_ai_handler = ChatFlowHandler(use_ollama=False)
        except Exception as e:
            st.error(f"Could not initialize AI: {e}")
            st.session_state.wizard_ai_handler = None

    # Display message history
    for message in st.session_state.wizard_ai_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    user_question = st.chat_input(
        "Ask me about military benefits, financial planning, " "or the transition...",
        key="wizard_ai_input",
    )

    if user_question:
        # Add user message
        st.session_state.wizard_ai_messages.append({"role": "user", "content": user_question})

        with st.chat_message("user"):
            st.write(user_question)

        # Generate AI response
        with st.chat_message("assistant"):
            try:
                handler = st.session_state.wizard_ai_handler
                if handler:
                    # Context from current wizard state
                    context_info = f"""
Current Wizard Progress:
- Step: {st.session_state.get('wizard_step', 1)}/5
- Rank: {st.session_state.get('user_rank', 'Not set')}
- YOS: {st.session_state.get('user_years_of_service', 'Not set')} years
- Target Location: {st.session_state.get('target_city', 'Not set')}
- VA Rating: {st.session_state.get('current_va_disability_rating', 'Not set')}%

User Question: {user_question}
"""
                    response = handler.process_user_input(context_info)
                    ai_response = response.get(
                        "response",
                        "I'm not sure how to help with that. Please " "try another question.",
                    )
                    st.write(ai_response)

                    # Store response
                    st.session_state.wizard_ai_messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("AI assistant not available")
            except Exception as e:
                st.error(f"Error generating response: {e}")

    # Helpful prompts
    st.divider()
    st.caption("[INFO] Try asking:")
    prompts = [
        "What's the difference between SBP and Term Life?",
        "When should I start my job search?",
        "How do VA disability ratings work?",
        "What healthcare options do I have?",
    ]

    for prompt in prompts:
        if st.button(prompt, use_container_width=True, key=f"prompt_{prompt}"):
            st.session_state.wizard_ai_input = prompt
            st.rerun()


def display_decision_summary(summary):
    """
    Display formatted decision summary.

    Args:
        summary: DecisionSummary object from summary_engine
    """
    # Main viability statement
    if summary.is_viable:
        st.success("[OK] **Transition appears financially viable**")
    else:
        st.error("[WARNING] **Transition requires careful planning**")

    st.markdown(f"**Confidence:** {summary.confidence_level.upper()}")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Runway (months)",
            format_months_value(summary.metrics.runway_months),
            delta="Before running out of savings",
        )
    with col2:
        st.metric(
            "Phase 1 Gap",
            f"${summary.metrics.phase1_monthly_gap:,.0f}/mo",
            delta="Until job starts",
        )
    with col3:
        st.metric(
            "Phase 2 Surplus",
            f"${summary.metrics.phase2_monthly_surplus:,.0f}/mo",
            delta="After job starts",
        )
    with col4:
        st.metric(
            "5-Year Outlook",
            f"${summary.metrics.five_year_total:,.0f}",
            delta="Total net position",
        )

    st.divider()

    # Identified risks
    if summary.identified_risks:
        st.subheader("[WARNING] Key Risks")
        for risk in summary.identified_risks:
            if risk.severity == "critical":
                st.error(f"[HIGH] **{risk.name}** - {risk.description}")
            elif risk.severity == "high":
                st.warning(f"🟠 **{risk.name}** - {risk.description}")
            elif risk.severity == "moderate":
                st.info(f"[MED] **{risk.name}** - {risk.description}")
            else:
                st.info(f"[LOW] **{risk.name}** - {risk.description}")

    st.divider()

    # Decision levers
    if summary.decision_levers:
        st.subheader("[GOAL] Decision Levers (by sensitivity)")
        for lever in summary.decision_levers:
            st.write(
                f"**#{lever.sensitivity_rank}: {lever.name}**  "
                f"Current: ${lever.current_value:,.0f} | "
                f"Range: ${lever.low_value:,.0f} → ${lever.high_value:,.0f} | "
                f"Impact: ${lever.impact_high:,.0f} at high"
            )

    st.divider()

    # Break-even scenarios
    if summary.breakeven_scenarios:
        st.subheader("[MONEY] Break-Even Scenarios")
        for scenario in summary.breakeven_scenarios:
            st.write(f"- {scenario}")

    st.divider()

    # Recommendation
    st.subheader("[PROFILE] Recommendation")
    st.markdown(summary.recommendation)

    # Action items
    if summary.action_items:
        st.subheader("[OK] Next Steps")
        for i, action in enumerate(summary.action_items, 1):
            st.write(f"{i}. {action}")
