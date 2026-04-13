"""
Dashboard module for Project Atlas.

This module handles all visualization and display logic for simulation results.
It follows Tufte's principles: maximize data-to-ink ratio, avoid chart junk,
and present information with clarity and precision.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_models import TransitionProfile


def display_dashboard(profile: TransitionProfile) -> None:
    """
    Display the complete financial simulation dashboard.

    Renders:
    1. Executive Summary (verdict, key metrics)
    2. Income & Expense Breakdown (clean visualizations)
    3. Month-by-Month Cash Flow (line chart with clarity)
    4. Risk Factors & Recommendations
    5. Scenario Comparison (if multiple scenarios saved)

    Args:
        profile (TransitionProfile): Completed simulation profile.
    """

    st.markdown("---")
    st.header("[STATS] Simulation Results")

    # Executive summary
    _display_executive_summary(profile)

    st.markdown("---")

    # Financial breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("[MONEY] Annual Income")
        _display_income_breakdown(profile)

    with col2:
        st.subheader("💸 Annual Expenses")
        _display_expense_breakdown(profile)

    st.markdown("---")

    # Cash flow projection
    st.subheader("[CHART] Cash Flow Projection")
    _display_cash_flow_chart(profile)

    st.markdown("---")

    # Risk factors and recommendations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("[WARNING] Risk Factors")
        _display_risk_factors(profile)

    with col2:
        st.subheader("[OK] Recommendations")
        _display_recommendations(profile)

    st.markdown("---")

    # Scenario actions
    _display_scenario_actions(profile)


def _display_executive_summary(profile: TransitionProfile) -> None:
    """
    Display the executive summary with verdict and key metrics.

    Args:
        profile (TransitionProfile): User's profile.
    """

    # Color code based on verdict
    verdict_colors = {
        "STRONG_SURPLUS": "[LOW]",
        "SURPLUS": "[LOW]",
        "BREAK_EVEN": "[MED]",
        "DEFICIT": "[HIGH]",
        "SEVERE_DEFICIT": "[HIGH]",
    }

    verdict_emoji = verdict_colors.get(profile.financial_verdict, "⚪")

    # Display verdict prominently
    st.metric(
        label=f"{verdict_emoji} Financial Verdict",
        value=profile.financial_verdict.replace("_", " "),
        delta=f"${profile.final_cash_buffer:,.0f}",
    )

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Annual Take-Home",
            f"${profile.annual_take_home_pay:,.0f}",
        )

    with col2:
        st.metric(
            "Monthly Expenses",
            f"${profile.adjusted_total_monthly_expenses():,.0f}",
        )

    with col3:
        st.metric(
            "Job Search Timeline",
            f"{profile.job_search_timeline_months} months",
        )

    with col4:
        st.metric(
            "Confidence",
            f"{profile.financial_verdict_confidence:.0%}",
        )


def _display_income_breakdown(profile: TransitionProfile) -> None:
    """
    Display income sources breakdown (Tufte-style).

    Args:
        profile (TransitionProfile): User's profile.
    """

    breakdown = profile.metadata.get("income_breakdown", {})

    # Create a clean table
    income_data = {
        "Source": [
            "Military Retirement",
            "VA Disability",
            "Salary",
            "Total Income",
        ],
        "Annual": [
            f"${breakdown.get('retirement_pay', 0):,.0f}",
            f"${breakdown.get('va_benefit', 0):,.0f}",
            f"${breakdown.get('salary', 0):,.0f}",
            f"${breakdown.get('gross_income', 0):,.0f}",
        ],
        "Monthly": [
            f"${breakdown.get('retirement_pay', 0) / 12:,.0f}",
            f"${breakdown.get('va_benefit', 0) / 12:,.0f}",
            f"${breakdown.get('salary', 0) / 12:,.0f}",
            f"${breakdown.get('gross_income', 0) / 12:,.0f}",
        ],
    }

    df = pd.DataFrame(income_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Tax breakdown
    st.caption("Taxes & Deductions")
    tax_data = {
        "Tax Type": ["Federal", "State", "FICA", "Total Taxes"],
        "Amount": [
            f"${breakdown.get('federal_tax', 0):,.0f}",
            f"${breakdown.get('state_tax', 0):,.0f}",
            f"${breakdown.get('fica_tax', 0):,.0f}",
            f"${breakdown.get('total_tax', 0):,.0f}",
        ],
    }
    df_tax = pd.DataFrame(tax_data)
    st.dataframe(df_tax, hide_index=True, use_container_width=True)


def _display_expense_breakdown(profile: TransitionProfile) -> None:
    """
    Display expense categories breakdown.

    Args:
        profile (TransitionProfile): User's profile.
    """

    # Expense data (unadjusted for COLA display)
    expense_data = {
        "Category": [
            "Mandatory",
            "Negotiable",
            "Optional",
            "Healthcare",
            "Total Monthly",
        ],
        "Monthly": [
            f"${profile.monthly_expenses_mandatory:,.0f}",
            f"${profile.monthly_expenses_negotiable:,.0f}",
            f"${profile.monthly_expenses_optional:,.0f}",
            f"${profile.monthly_healthcare_cost:,.0f}",
            f"${profile.adjusted_total_monthly_expenses() + profile.monthly_healthcare_cost:,.0f}",
        ],
        "Annual": [
            f"${profile.monthly_expenses_mandatory * 12:,.0f}",
            f"${profile.monthly_expenses_negotiable * 12:,.0f}",
            f"${profile.monthly_expenses_optional * 12:,.0f}",
            f"${profile.annual_healthcare_cost:,.0f}",
            f"${(profile.adjusted_total_monthly_expenses() + profile.monthly_healthcare_cost) * 12:,.0f}",
        ],
    }

    df = pd.DataFrame(expense_data)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _display_cash_flow_chart(profile: TransitionProfile) -> None:
    """
    Display month-by-month cash flow chart (Tufte-style minimalism).

    Args:
        profile (TransitionProfile): User's profile.
    """

    if not profile.monthly_cash_flow:
        st.warning("No cash flow data available.")
        return

    # Extract data
    months = [cf["month"] for cf in profile.monthly_cash_flow]
    cumulative = [cf["cumulative_savings"] for cf in profile.monthly_cash_flow]
    net_flow = [cf["net_flow"] for cf in profile.monthly_cash_flow]

    # Create figure with Tufte-style minimalism
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="white")

    # Plot cumulative savings line
    ax.plot(
        months,
        cumulative,
        linewidth=2.5,
        color="#1f77b4",
        marker="o",
        markersize=4,
        label="Cumulative Savings",
    )

    # Add zero line
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.8, alpha=0.3)

    # Fill region above/below zero
    ax.fill_between(
        months,
        0,
        cumulative,
        where=np.array(cumulative) >= 0,
        alpha=0.2,
        color="green",
        label="Positive Buffer",
    )
    ax.fill_between(
        months,
        0,
        cumulative,
        where=np.array(cumulative) < 0,
        alpha=0.2,
        color="red",
        label="Deficit",
    )

    # Tufte styling: minimal spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    # Labels
    ax.set_xlabel("Month", fontsize=11, fontweight="bold")
    ax.set_ylabel("Cumulative Savings ($)", fontsize=11, fontweight="bold")
    ax.set_title(
        f"Cash Flow Projection: {profile.job_search_timeline_months}-Month Timeline",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}K"))

    # Add legend
    ax.legend(loc="upper left", frameon=False, fontsize=10)

    # Grid (light)
    ax.grid(True, alpha=0.2, linestyle="-", linewidth=0.5)

    st.pyplot(fig, use_container_width=True)

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Starting Buffer", f"${profile.current_savings:,.0f}")
    with col2:
        st.metric("Final Buffer", f"${profile.final_cash_buffer:,.0f}")
    with col3:
        st.metric("Avg Monthly Net", f"${np.mean(net_flow):,.0f}")


def _display_risk_factors(profile: TransitionProfile) -> None:
    """
    Display identified risk factors.

    Args:
        profile (TransitionProfile): User's profile.
    """

    if not profile.risk_factors:
        st.success("[OK] No major risk factors identified!")
    else:
        for i, risk in enumerate(profile.risk_factors, 1):
            st.warning(f"**{i}. {risk}**")


def _display_recommendations(profile: TransitionProfile) -> None:
    """
    Display personalized recommendations.

    Args:
        profile (TransitionProfile): User's profile.
    """

    if not profile.recommendations:
        st.info("No recommendations at this time.")
    else:
        for i, rec in enumerate(profile.recommendations, 1):
            st.info(f"**{i}. {rec}**")


def _display_scenario_actions(profile: TransitionProfile) -> None:
    """
    Display buttons to save scenario or compare scenarios.

    Args:
        profile (TransitionProfile): User's profile.
    """

    col1, col2, col3 = st.columns(3)

    with col1:
        scenario_name = st.text_input(
            "Scenario Name",
            value=profile.target_city or "Scenario 1",
            key="scenario_name_input",
        )

        if st.button("💾 Save This Scenario", use_container_width=True):
            if "saved_scenarios" not in st.session_state:
                st.session_state.saved_scenarios = []

            # Store the profile
            st.session_state.saved_scenarios.append(
                {
                    "name": scenario_name,
                    "profile": profile,
                    "timestamp": pd.Timestamp.now(),
                }
            )

            st.success(f"[OK] Scenario '{scenario_name}' saved!")
            st.balloons()

    with col2:
        if st.button("[RESET] Run New Scenario", use_container_width=True):
            st.session_state.current_step = "input"
            st.rerun()

    with col3:
        if "saved_scenarios" in st.session_state and len(st.session_state.saved_scenarios) > 1:
            if st.button("[STATS] Compare Scenarios", use_container_width=True):
                st.session_state.show_comparison = True
                st.rerun()


def display_ai_scenario_comparisons() -> None:
    """
    Display AI-generated comparison statements for scenarios created from AI analysis.
    
    Shows the comparison narrative generated by AIScenarioStateManager.
    """
    if "saved_scenarios" not in st.session_state:
        return
    
    # Filter for AI scenarios that have comparison_to_baseline
    ai_scenarios = [
        s for s in st.session_state.saved_scenarios 
        if s.get('source') == 'ai_analysis' and 'comparison_to_baseline' in s
    ]
    
    if not ai_scenarios:
        return
    
    st.subheader("🤖 AI Analysis Comparisons")
    
    for scenario in ai_scenarios:
        with st.expander(f"📊 {scenario['name']}", expanded=True):
            # Show the original question
            st.caption(f"**Question:** {scenario.get('question', 'N/A')}")
            
            # Show the comparison statement
            if scenario.get('comparison_to_baseline'):
                st.info(f"**vs Baseline:** {scenario['comparison_to_baseline']}")
            
            # Show analysis and recommendation if available
            if scenario.get('analysis'):
                st.write(scenario['analysis'])
            
            if scenario.get('recommendation'):
                # Sanitize recommendation: remove all newlines and collapse multiple spaces
                clean_rec = scenario['recommendation'].replace('\n', ' ').replace('\r', ' ')
                clean_rec = ' '.join(clean_rec.split())  # Collapse multiple whitespaces
                st.write(f"**Recommendation:** {clean_rec}")


def display_scenario_comparison() -> None:
    """
    Display side-by-side comparison of saved scenarios.

    Retrieves scenarios from st.session_state.
    """

    if "saved_scenarios" not in st.session_state or not st.session_state.saved_scenarios:
        st.warning("No scenarios saved yet.")
        return

    st.header("[STATS] Scenario Comparison")
    
    # Show AI comparisons first if any exist
    display_ai_scenario_comparisons()
    
    st.divider()

    scenarios = st.session_state.saved_scenarios

    # Create comparison table
    comparison_data = []
    for scenario in scenarios:
        profile = scenario["profile"]
        comparison_data.append(
            {
                "Scenario": scenario["name"],
                "Target City": profile.target_city,
                "Salary": f"${profile.estimated_annual_salary:,.0f}",
                "Take-Home": f"${profile.annual_take_home_pay:,.0f}",
                "Final Buffer": f"${profile.final_cash_buffer:,.0f}",
                "Verdict": profile.financial_verdict,
                "Confidence": f"{profile.financial_verdict_confidence:.0%}",
            }
        )

    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, hide_index=True, use_container_width=True)

    # Visual comparison of key metrics
    st.subheader("Key Metrics Comparison")

    col1, col2 = st.columns(2)

    with col1:
        # Cash buffer comparison
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")

        names = [s["name"] for s in scenarios]
        buffers = [s["profile"].final_cash_buffer for s in scenarios]
        colors = ["green" if b > 0 else "red" for b in buffers]

        ax.barh(names, buffers, color=colors, alpha=0.7)
        ax.axvline(x=0, color="black", linestyle="-", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlabel("Final Cash Buffer ($)", fontweight="bold")
        ax.set_title("Final Buffer Comparison", fontweight="bold", pad=10)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}K"))

        st.pyplot(fig, use_container_width=True)

    with col2:
        # Annual take-home comparison
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")

        names = [s["name"] for s in scenarios]
        takeomes = [s["profile"].annual_take_home_pay for s in scenarios]

        ax.barh(names, takeomes, color="#1f77b4", alpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlabel("Annual Take-Home Pay ($)", fontweight="bold")
        ax.set_title("Annual Income Comparison", fontweight="bold", pad=10)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}K"))

        st.pyplot(fig, use_container_width=True)

    # Individual scenario details
    st.subheader("Detailed Scenario Breakdown")

    selected_scenario = st.selectbox(
        "Select scenario to view details:",
        options=[s["name"] for s in scenarios],
    )

    if selected_scenario:
        scenario = next(
            (s for s in scenarios if s["name"] == selected_scenario),
            None,
        )
        if scenario:
            st.write(f"**{selected_scenario}** - {scenario['timestamp']}")
            display_dashboard(scenario["profile"])


def load_sample_scenario(scenario_name: str = "E-7 Denver") -> None:
    """
    Load a pre-populated sample scenario into session state for demo purposes.

    Args:
        scenario_name: Name of sample scenario ("E-7 Denver", "O-3 Austin", "E-5 Portland")
    """
    from datetime import date, timedelta

    # Sample scenarios - use date objects, not datetime (Streamlit requires serializable types)
    samples = {
        "E-7 Denver": {
            "user_rank": "E-7",
            "user_years_of_service": 24,
            "user_service_branch": "Navy",
            "user_separation_date": date.today() + timedelta(days=60),
            "retirement_location": "Colorado",
            "user_marital_status": "Married",
            "military_pension": 2400,
            "current_paycheck_monthly": 6500,
            "current_va_disability_rating": 10,
            "va_annual_benefit": 1320,
            "spouse_income_annual": 45000,
            "monthly_expenses_mandatory": 3000,
            "monthly_expenses_negotiable": 1200,
            "monthly_expenses_optional": 400,
            "current_savings": 35000,
            "current_debt": 8000,
            "estimated_annual_salary": 85000,
            "job_search_months": 6,
            "healthcare_plan_choice": "tricare_select",
        },
        "O-3 Austin": {
            "user_rank": "O-3",
            "user_years_of_service": 10,
            "user_service_branch": "Air Force",
            "user_separation_date": date.today() + timedelta(days=90),
            "retirement_location": "Texas",
            "user_marital_status": "Married",
            "military_pension": 0,
            "current_paycheck_monthly": 8000,
            "current_va_disability_rating": 30,
            "va_annual_benefit": 5040,
            "spouse_income_annual": 65000,
            "monthly_expenses_mandatory": 4000,
            "monthly_expenses_negotiable": 1500,
            "monthly_expenses_optional": 800,
            "current_savings": 75000,
            "current_debt": 0,
            "estimated_annual_salary": 120000,
            "job_search_months": 3,
            "healthcare_plan_choice": "private_aca",
        },
        "E-5 Portland": {
            "user_rank": "E-5",
            "user_years_of_service": 12,
            "user_service_branch": "Army",
            "user_separation_date": date.today() + timedelta(days=120),
            "retirement_location": "Oregon",
            "user_marital_status": "Single",
            "military_pension": 0,
            "current_paycheck_monthly": 4500,
            "current_va_disability_rating": 0,
            "va_annual_benefit": 0,
            "spouse_income_annual": 0,
            "monthly_expenses_mandatory": 2500,
            "monthly_expenses_negotiable": 800,
            "monthly_expenses_optional": 300,
            "current_savings": 15000,
            "current_debt": 22000,
            "estimated_annual_salary": 65000,
            "job_search_months": 9,
            "healthcare_plan_choice": "va_health",
        },
    }

    # Load selected sample
    sample = samples.get(scenario_name, samples["E-7 Denver"])

    # Populate session state with sample data
    for key, value in sample.items():
        st.session_state[key] = value

    # Initialize wizard tracking
    st.session_state.using_sample_data = True
    st.session_state.wizard_step = 1
    st.session_state.wizard_completed_steps = set()


def display_empty_state() -> None:
    """
    Display welcome message and instructions for first-time users.

    This addresses the "cold start" problem.
    """

    st.header("📍 Project Atlas: Personal Transition Simulator")

    st.markdown(
        """
        Welcome, transitioning service member! Project Atlas helps you **"wargame"** your
        financial future by simulating major life decisions.

        ### How It Works

        1. **Upload** your transaction history (CSV)
        2. **Categorize** your expenses (mandatory, negotiable, optional)
        3. **Enter** your transition parameters (target city, job timeline, salary)
        4. **View** a complete financial forecast with month-by-month projections
        5. **Compare** multiple scenarios to find the best path forward

        ### Key Features

        - 🏠 **Local-First**: All your data stays on your computer
        - [STATS] **Visual Dashboard**: Clear charts and metrics
        - [WARNING] **Risk Assessment**: Identifies potential financial challenges
        - [OK] **Recommendations**: Personalized advice for your situation
        - [CHART] **Scenario Comparison**: Side-by-side analysis of different options

        ---
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        # Selector for which sample scenario
        sample_choice = st.radio(
            "Choose a sample scenario:",
            ["E-7 Denver", "O-3 Austin", "E-5 Portland"],
            horizontal=True,
        )

    with col2:
        if st.button("🎬 Try Sample Scenario", use_container_width=True):
            load_sample_scenario(sample_choice)
            st.session_state.simulation_mode = "wizard"
            st.rerun()

    # Display statistics or features
    st.markdown("---")
    st.markdown("**Sample Scenarios Available:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("E-7 → Denver", "6 months", "SURPLUS")
    with col2:
        st.metric("O-3 → Austin", "3 months", "STRONG_SURPLUS")
    with col3:
        st.metric("E-5 → Portland", "9 months", "BREAK_EVEN")

    st.markdown(
        """
        ---
        **ℹ️ For your own data:** Use the Classic Tabs or Wizard mode to upload your CSV transaction history.
        """
    )
