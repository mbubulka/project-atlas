"""
What-if scenario tools for the wizard.

Allows users to test assumptions and see impact on decision.
Each tool: takes baseline profile + adjustment → calculates delta vs baseline
"""

from dataclasses import dataclass, replace
from typing import Dict

import streamlit as st

from src.data_models import TransitionProfile

from .summary_engine import (
    calculate_financial_metrics,
    format_months_value,
)


@dataclass
class ScenarioComparison:
    """Compare baseline vs variant scenario."""

    baseline_label: str
    variant_label: str
    baseline_metrics: Dict
    variant_metrics: Dict
    deltas: Dict  # What changed


def test_salary_adjustment(baseline_profile: TransitionProfile, adjusted_salary: float) -> ScenarioComparison:
    """
    What if you earn a different salary?

    Args:
        baseline_profile: Original profile
        adjusted_salary: New target salary

    Returns: Comparison showing impact
    """
    variant_profile = replace(baseline_profile, estimated_annual_salary=adjusted_salary)

    baseline_metrics = calculate_financial_metrics(baseline_profile)
    variant_metrics = calculate_financial_metrics(variant_profile)

    deltas = {
        "monthly_income_delta": variant_metrics.phase2_monthly_income - baseline_metrics.phase2_monthly_income,
        "monthly_surplus_delta": variant_metrics.phase2_monthly_surplus - baseline_metrics.phase2_monthly_surplus,
        "annual_surplus_delta": variant_metrics.phase2_annual_surplus - baseline_metrics.phase2_annual_surplus,
        "runway_delta": variant_metrics.runway_months - baseline_metrics.runway_months,
        "savings_after_gap_delta": variant_metrics.savings_after_gap - baseline_metrics.savings_after_gap,
    }

    return ScenarioComparison(
        baseline_label=f"Target: ${baseline_profile.estimated_annual_salary:,.0f}/yr",
        variant_label=f"Test: ${adjusted_salary:,.0f}/yr",
        baseline_metrics={
            "phase2_monthly_surplus": baseline_metrics.phase2_monthly_surplus,
            "runway": baseline_metrics.runway_months,
        },
        variant_metrics={
            "phase2_monthly_surplus": variant_metrics.phase2_monthly_surplus,
            "runway": variant_metrics.runway_months,
        },
        deltas=deltas,
    )


def test_job_delay(baseline_profile: TransitionProfile, delayed_months: int) -> ScenarioComparison:
    """
    What if the job offer is delayed?

    Args:
        baseline_profile: Original profile
        delayed_months: Additional months of job search

    Returns: Comparison showing impact
    """
    variant_profile = replace(baseline_profile, job_search_timeline_months=delayed_months)

    baseline_metrics = calculate_financial_metrics(baseline_profile)
    variant_metrics = calculate_financial_metrics(variant_profile)

    gap_cost = baseline_metrics.phase1_monthly_gap * (delayed_months - baseline_profile.job_search_timeline_months)

    deltas = {
        "additional_months": delayed_months - baseline_profile.job_search_timeline_months,
        "gap_cost": gap_cost,
        "runway_delta": variant_metrics.runway_months - baseline_metrics.runway_months,
        "savings_after_gap_delta": variant_metrics.savings_after_gap - baseline_metrics.savings_after_gap,
        "is_still_viable": variant_metrics.savings_after_gap >= 0,
    }

    return ScenarioComparison(
        baseline_label=f"Job timeline: {baseline_profile.job_search_timeline_months} months",
        variant_label=f"If delayed: {delayed_months} months",
        baseline_metrics={
            "runway": baseline_metrics.runway_months,
            "savings": baseline_metrics.savings_after_gap,
        },
        variant_metrics={
            "runway": variant_metrics.runway_months,
            "savings": variant_metrics.savings_after_gap,
        },
        deltas=deltas,
    )


def test_va_rating(baseline_profile: TransitionProfile, adjusted_rating: int) -> ScenarioComparison:
    """
    What if your VA rating changes?

    Args:
        baseline_profile: Original profile
        adjusted_rating: New VA disability rating (0-100)

    Returns: Comparison showing impact
    """
    # Calculate new VA benefit (rough estimate: $130/month per 10%)
    new_va_annual = (adjusted_rating / 10) * 130 * 12

    variant_profile = replace(
        baseline_profile,
        current_va_disability_rating=adjusted_rating,
        current_va_annual_benefit=new_va_annual,
    )

    baseline_metrics = calculate_financial_metrics(baseline_profile)
    variant_metrics = calculate_financial_metrics(variant_profile)

    deltas = {
        "monthly_income_delta": variant_metrics.phase1_monthly_income - baseline_metrics.phase1_monthly_income,
        "annual_benefit_delta": new_va_annual - baseline_profile.current_va_annual_benefit,
        "monthly_surplus_delta": variant_metrics.phase2_monthly_surplus - baseline_metrics.phase2_monthly_surplus,
        "runway_delta": variant_metrics.runway_months - baseline_metrics.runway_months,
    }

    return ScenarioComparison(
        baseline_label=f"VA rating: {baseline_profile.current_va_disability_rating}%",
        variant_label=f"If rated: {adjusted_rating}%",
        baseline_metrics={
            "monthly_income": baseline_metrics.phase1_monthly_income,
            "surplus": baseline_metrics.phase2_monthly_surplus,
        },
        variant_metrics={
            "monthly_income": variant_metrics.phase1_monthly_income,
            "surplus": variant_metrics.phase2_monthly_surplus,
        },
        deltas=deltas,
    )


def test_expense_reduction(baseline_profile: TransitionProfile, reduction_percent: float) -> ScenarioComparison:
    """
    What if you cut expenses?

    Args:
        baseline_profile: Original profile
        reduction_percent: Percent to reduce (e.g., 0.1 for 10% cut)

    Returns: Comparison showing impact
    """
    reduction_factor = 1.0 - reduction_percent

    variant_profile = replace(
        baseline_profile,
        monthly_expenses_mandatory=baseline_profile.monthly_expenses_mandatory * reduction_factor,
        monthly_expenses_negotiable=baseline_profile.monthly_expenses_negotiable * reduction_factor,
        monthly_expenses_optional=baseline_profile.monthly_expenses_optional * reduction_factor,
    )

    baseline_metrics = calculate_financial_metrics(baseline_profile)
    variant_metrics = calculate_financial_metrics(variant_profile)

    monthly_savings = baseline_metrics.phase1_monthly_expenses * reduction_percent

    deltas = {
        "monthly_expense_reduction": monthly_savings,
        "phase1_gap_delta": variant_metrics.phase1_monthly_gap - baseline_metrics.phase1_monthly_gap,
        "runway_delta": variant_metrics.runway_months - baseline_metrics.runway_months,
        "annual_savings": monthly_savings * 12,
    }

    return ScenarioComparison(
        baseline_label=f"Expenses: ${baseline_metrics.phase1_monthly_expenses:,.0f}/mo",
        variant_label=f"With {reduction_percent*100:.0f}% cut: ${variant_metrics.phase1_monthly_expenses:,.0f}/mo",
        baseline_metrics={
            "monthly_expenses": baseline_metrics.phase1_monthly_expenses,
            "gap": baseline_metrics.phase1_monthly_gap,
        },
        variant_metrics={
            "monthly_expenses": variant_metrics.phase1_monthly_expenses,
            "gap": variant_metrics.phase1_monthly_gap,
        },
        deltas=deltas,
    )


def test_debt_payoff(baseline_profile: TransitionProfile, accelerated: bool = False) -> ScenarioComparison:
    """
    What if you accelerate debt payoff?

    Args:
        baseline_profile: Original profile
        accelerated: True = aggressive payoff, False = minimum payments

    Returns: Comparison showing impact
    """
    payoff_strategy = "aggressive" if accelerated else "minimum"

    variant_profile = replace(baseline_profile, debt_payoff_priority=payoff_strategy)

    baseline_metrics = calculate_financial_metrics(baseline_profile)
    variant_metrics = calculate_financial_metrics(variant_profile)

    # Rough estimate: aggressive costs ~30% more monthly but pays off 50% faster
    if accelerated:
        additional_monthly_cost = baseline_profile.current_debt * 0.003  # ~0.3% of debt per month extra
        payoff_months_saved = (baseline_profile.current_debt / (baseline_profile.current_debt * 0.003)) / 2
    else:
        additional_monthly_cost = 0
        payoff_months_saved = 0

    deltas = {
        "additional_monthly_cost": additional_monthly_cost,
        "payoff_months_saved": payoff_months_saved,
        "total_debt_freed": baseline_profile.current_debt,
        "freed_in_months": (
            int((baseline_profile.current_debt / (baseline_profile.current_debt * 0.003)) / 2)
            if accelerated
            else int(baseline_profile.current_debt / (baseline_profile.current_debt * 0.001))
        ),
    }

    return ScenarioComparison(
        baseline_label="Debt payoff: Minimum payments",
        variant_label="Debt payoff: Aggressive/Accelerated",
        baseline_metrics={"monthly_cost": 0, "payoff_timeline": "slow"},
        variant_metrics={"monthly_cost": additional_monthly_cost, "payoff_timeline": "fast"},
        deltas=deltas,
    )


def display_scenario_comparison(comparison: ScenarioComparison) -> None:
    """
    Display side-by-side comparison of baseline vs variant.

    Args:
        comparison: ScenarioComparison object with metrics
    """
    col_baseline, col_variant, col_delta = st.columns(3)

    with col_baseline:
        st.subheader("[STATS] Baseline")
        st.caption(comparison.baseline_label)
        for key, value in comparison.baseline_metrics.items():
            if isinstance(value, float):
                # Handle infinity values for runway/months
                if key == "runway" and value == float("inf"):
                    st.metric(key.replace("_", " ").title(), "Indefinite")
                elif isinstance(value, float) and value == float("inf"):
                    st.metric(key.replace("_", " ").title(), "Indefinite")
                else:
                    st.metric(key.replace("_", " ").title(), f"${value:,.0f}")
            else:
                st.metric(key.replace("_", " ").title(), value)

    with col_variant:
        st.subheader("[GOAL] Variant")
        st.caption(comparison.variant_label)
        for key, value in comparison.variant_metrics.items():
            if isinstance(value, float):
                # Handle infinity values for runway/months
                if key == "runway" and value == float("inf"):
                    st.metric(key.replace("_", " ").title(), "Indefinite")
                elif isinstance(value, float) and value == float("inf"):
                    st.metric(key.replace("_", " ").title(), "Indefinite")
                else:
                    st.metric(key.replace("_", " ").title(), f"${value:,.0f}")
            else:
                st.metric(key.replace("_", " ").title(), value)

    with col_delta:
        st.subheader("[CHART] Delta")
        st.caption("Change from baseline")
        for key, value in comparison.deltas.items():
            if isinstance(value, float):
                # Handle infinity deltas
                if value == float("inf"):
                    st.success("Indefinite (improved)")
                elif value == float("-inf"):
                    st.error("Indefinite (worsened)")
                elif value > 0:
                    st.success(f"+${value:,.0f}")
                elif value < 0:
                    st.error(f"-${abs(value):,.0f}")
                else:
                    st.info("No change")
            elif isinstance(value, int):
                st.metric(key.replace("_", " ").title(), f"{value:+d}")
            elif isinstance(value, bool):
                status = "[OK] YES" if value else "[ERROR] NO"
                st.metric(key.replace("_", " ").title(), status)
            else:
                st.metric(key.replace("_", " ").title(), str(value))
