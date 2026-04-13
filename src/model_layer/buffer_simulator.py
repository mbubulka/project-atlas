"""
Cash flow buffer simulator for Project Atlas.

This is the main model that orchestrates all calculations and projects
the user's savings over the job search timeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.data_models import TransitionProfile
from src.model_layer.healthcare_model import compare_healthcare_costs
from src.model_layer.retirement_pay_model import calculate_take_home_pay
from src.model_layer.salary_predictor import predict_salary

logger = logging.getLogger(__name__)


def run_buffer_simulation(profile: TransitionProfile) -> TransitionProfile:
    """
    Run the complete financial simulation pipeline.

    This orchestrates the entire model stack:
    1. Predict salary (using GLM or user estimate)
    2. Calculate take-home pay from all sources
    3. Estimate healthcare costs
    4. Project month-by-month cash flow during job search
    5. Determine financial verdict (SURPLUS/DEFICIT/BREAK_EVEN)
    6. Identify risk factors and recommendations

    Args:
        profile (TransitionProfile): User's profile (populated with inputs).

    Returns:
        TransitionProfile: Fully completed profile with all model outputs.

    Raises:
        ValueError: If critical input data is missing or invalid.
    """

    logger.info(f"=== Starting Financial Simulation for {profile.user_name} ===")

    # Validate inputs
    _validate_profile_for_simulation(profile)

    # Run models in sequence
    profile = predict_salary(profile)
    profile = calculate_take_home_pay(profile)
    profile = compare_healthcare_costs(profile)

    # Run the core simulation
    profile = _simulate_monthly_cash_flow(profile)

    # Calculate verdict
    profile = _calculate_financial_verdict(profile)

    # Generate risk factors and recommendations
    profile = _identify_risk_factors(profile)
    profile = _generate_recommendations(profile)

    logger.info(
        f"=== Simulation Complete ===\n"
        f"Final Verdict: {profile.financial_verdict}\n"
        f"Final Buffer: ${profile.final_cash_buffer:,.2f}\n"
        f"Risk Factors: {len(profile.risk_factors)}"
    )

    return profile


def _validate_profile_for_simulation(profile: TransitionProfile) -> None:
    """
    Validate that the profile has all required fields for simulation.

    Args:
        profile (TransitionProfile): Profile to validate.

    Raises:
        ValueError: If critical fields are missing or invalid.
    """

    required_fields = [
        ("user_name", str, "User name is required"),
        ("current_savings", float, "Current savings must be specified"),
        ("monthly_expenses_mandatory", float, "Monthly mandatory expenses required"),
        ("target_city", str, "Target city required"),
        ("job_search_timeline_months", int, "Job search timeline required"),
        ("estimated_annual_salary", float, "Estimated salary required"),
    ]

    for field_name, field_type, error_msg in required_fields:
        value = getattr(profile, field_name, None)

        if value is None or value == "":
            raise ValueError(f"{error_msg}")

        # For float fields, accept both int and float
        if field_type == float:
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be numeric, " f"got {type(value).__name__}")
        elif not isinstance(value, field_type):
            raise ValueError(f"{field_name} must be {field_type.__name__}, " f"got {type(value).__name__}")

    logger.info("Profile validation passed.")


def _simulate_monthly_cash_flow(profile: TransitionProfile) -> TransitionProfile:
    """
    Project month-by-month cash flow during the job search period.

    Assumptions:
    - User receives full monthly income starting immediately
    - User pays full monthly expenses (adjusted for COLA)
    - Job search occurs over job_search_timeline_months
    - After timeline expires, we assume employment begins

    Args:
        profile (TransitionProfile): User's profile with income calculated.

    Returns:
        TransitionProfile: Updated profile with monthly_cash_flow filled in.
    """

    monthly_cash_flow = []
    cumulative_savings = profile.current_savings

    monthly_income = profile.monthly_take_home_pay
    adjusted_monthly_expenses = profile.adjusted_total_monthly_expenses()

    # Determine when job starts (end of search timeline or sooner)
    job_start_month = int(profile.job_search_timeline_months * profile.job_offer_certainty)

    logger.info(
        f"Simulation parameters:\n"
        f"  Starting savings: ${cumulative_savings:,.2f}\n"
        f"  Monthly income: ${monthly_income:,.2f}\n"
        f"  Monthly expenses: ${adjusted_monthly_expenses:,.2f}\n"
        f"  Job start (expected): Month {job_start_month}"
    )

    for month in range(1, profile.job_search_timeline_months + 1):
        # Calculate date
        if profile.separation_date:
            month_date = profile.separation_date + timedelta(days=30 * (month - 1))
        else:
            month_date = datetime.now() + timedelta(days=30 * (month - 1))

        # During job search, user may not have salary income yet
        # Apply job offer certainty probabilistically
        if month <= job_start_month:
            # Likely to have secured job by this month
            income = monthly_income
        else:
            # Apply uncertainty: some probability of not yet employed
            income = monthly_income * profile.job_offer_certainty

        # Healthcare costs
        healthcare_cost = profile.monthly_healthcare_cost

        # Calculate net flow
        net_flow = income - adjusted_monthly_expenses - healthcare_cost
        cumulative_savings += net_flow

        # Record month
        monthly_record = {
            "month": month,
            "date": month_date.strftime("%Y-%m-%d"),
            "income": income,
            "expenses": adjusted_monthly_expenses,
            "healthcare_cost": healthcare_cost,
            "net_flow": net_flow,
            "cumulative_savings": cumulative_savings,
        }

        monthly_cash_flow.append(monthly_record)

        logger.debug(
            f"Month {month}: Income ${income:,.2f} - "
            f"Expenses ${adjusted_monthly_expenses:,.2f} - "
            f"Healthcare ${healthcare_cost:,.2f} = "
            f"Net ${net_flow:,.2f} | Cumulative ${cumulative_savings:,.2f}"
        )

    profile.monthly_cash_flow = monthly_cash_flow
    profile.final_cash_buffer = cumulative_savings

    logger.info(
        f"Final cash buffer after {profile.job_search_timeline_months} months: " f"${profile.final_cash_buffer:,.2f}"
    )

    return profile


def _calculate_financial_verdict(profile: TransitionProfile) -> TransitionProfile:
    """
    Determine the financial verdict based on final cash buffer.

    Verdict:
    - SURPLUS: Final buffer > 0 AND > 3 months of expenses
    - BREAK_EVEN: Final buffer between -5000 and 0
    - DEFICIT: Final buffer < -5000

    Args:
        profile (TransitionProfile): Profile with final_cash_buffer set.

    Returns:
        TransitionProfile: Updated profile with financial_verdict set.
    """

    buffer = profile.final_cash_buffer
    monthly_expenses = profile.adjusted_total_monthly_expenses()

    # Guard against zero/negative expenses
    if monthly_expenses <= 0:
        monthly_expenses = 1000  # Fallback minimum

    three_months_expenses = monthly_expenses * 3

    # Determine verdict
    if buffer > three_months_expenses:
        verdict = "STRONG_SURPLUS"
        confidence = 0.95
    elif buffer > 0:
        verdict = "SURPLUS"
        confidence = 0.85
    elif buffer > -5000:
        verdict = "BREAK_EVEN"
        confidence = 0.70
    elif buffer > -15000:
        verdict = "DEFICIT"
        confidence = 0.60
    else:
        verdict = "SEVERE_DEFICIT"
        confidence = 0.50

    # Adjust confidence based on job offer certainty
    confidence *= profile.job_offer_certainty

    profile.financial_verdict = verdict
    profile.financial_verdict_confidence = confidence

    logger.info(
        f"Financial Verdict: {verdict}\n"
        f"  Final Buffer: ${buffer:,.2f}\n"
        f"  Confidence: {confidence:.1%}\n"
        f"  3-Month Threshold: ${three_months_expenses:,.2f}"
    )

    return profile


def _identify_risk_factors(profile: TransitionProfile) -> TransitionProfile:
    """
    Identify financial risks in the scenario.

    Args:
        profile (TransitionProfile): Completed profile.

    Returns:
        TransitionProfile: Updated profile with risk_factors filled in.
    """

    risks = []

    # Risk: Negative cash flow
    if profile.final_cash_buffer < 0:
        risks.append(
            f"Negative cash buffer: ${profile.final_cash_buffer:,.0f}. "
            "Consider increasing savings or reducing expenses before separation."
        )

    # Risk: Tight margins
    monthly_net = 0
    if profile.monthly_cash_flow:
        monthly_net = profile.monthly_cash_flow[-1]["net_flow"]

    if abs(monthly_net) < profile.monthly_expenses_mandatory:
        risks.append("Tight monthly cash flow. Limited buffer for unexpected expenses.")

    # Risk: Low job certainty
    if profile.job_offer_certainty < 0.7:
        risks.append(
            f"Job offer uncertainty ({profile.job_offer_certainty:.0%}) is high. "
            "Consider extending job search timeline or increasing savings."
        )

    # Risk: High healthcare costs
    healthcare_ratio = profile.monthly_healthcare_cost / profile.monthly_take_home_pay
    if healthcare_ratio > 0.25:
        risks.append(
            f"Healthcare costs are {healthcare_ratio:.0%} of income. " "Review plan options or consider VA Health."
        )

    # Risk: Short job search timeline
    if profile.job_search_timeline_months < 3:
        risks.append("Very short job search timeline. Consider allowing more time " "to find the right opportunity.")

    profile.risk_factors = risks

    logger.info(f"Identified {len(risks)} risk factors")
    for i, risk in enumerate(risks, 1):
        logger.info(f"  {i}. {risk}")

    return profile


def _generate_recommendations(profile: TransitionProfile) -> TransitionProfile:
    """
    Generate personalized recommendations for the user.

    Args:
        profile (TransitionProfile): Completed profile.

    Returns:
        TransitionProfile: Updated profile with recommendations filled in.
    """

    recommendations = []

    # Savings recommendations
    if profile.final_cash_buffer < profile.monthly_expenses_mandatory * 6:
        recommendations.append("Build a 6-month emergency fund before separation. " "Current buffer is insufficient.")

    # Job search recommendations
    if profile.job_offer_certainty < 0.8:
        recommendations.append(
            "Secure a job offer before separation if possible. " "Reduces financial risk significantly."
        )

    # Expense management
    if profile.monthly_expenses_negotiable > profile.monthly_expenses_mandatory:
        recommendations.append(
            "Review negotiable expenses. Reducing discretionary spending " "could improve cash flow."
        )

    # Healthcare recommendations
    if profile.current_va_disability_rating >= 50:
        recommendations.append("Maximize VA Healthcare benefits. You may qualify for comprehensive coverage.")

    # Salary recommendations
    if profile.estimated_annual_salary < 80000:
        recommendations.append("Consider targeted job search in higher-wage markets (tech, consulting, federal roles).")

    # COLA recommendations
    if profile.cost_of_living_adjustment_factor > 1.15:
        recommendations.append(
            f"High cost of living in target city ({profile.cost_of_living_adjustment_factor:.1%}). "
            "Consider lower-cost regions or remote work."
        )

    profile.recommendations = recommendations

    logger.info(f"Generated {len(recommendations)} recommendations")
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"  {i}. {rec}")

    return profile


def sensitivity_analysis(profile: TransitionProfile, parameter: str, values: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying one parameter.

    Useful for "what-if" scenarios and understanding which parameters
    have the most impact on the final verdict.

    Args:
        profile (TransitionProfile): Base profile.
        parameter (str): Parameter to vary (e.g., 'job_search_timeline_months').
        values (List[float]): Values to test.

    Returns:
        Dict: Results of sensitivity analysis.

    Example:
        >>> results = sensitivity_analysis(
        ...     profile,
        ...     'estimated_annual_salary',
        ...     [80000, 100000, 120000, 140000]
        ... )
    """

    results = []

    for value in values:
        # Create a copy of the profile
        test_profile = profile

        # Set the parameter
        if hasattr(test_profile, parameter):
            setattr(test_profile, parameter, value)

        # Run simulation
        result = run_buffer_simulation(test_profile)

        results.append(
            {
                "parameter_value": value,
                "final_cash_buffer": result.final_cash_buffer,
                "financial_verdict": result.financial_verdict,
                "monthly_cash_flow": (result.monthly_cash_flow[-1]["net_flow"] if result.monthly_cash_flow else 0),
            }
        )

    logger.info(f"Sensitivity analysis for '{parameter}':")
    for r in results:
        logger.info(
            f"  {parameter}={r['parameter_value']} -> "
            f"Buffer=${r['final_cash_buffer']:,.0f}, "
            f"Verdict={r['financial_verdict']}"
        )

    return {
        "parameter": parameter,
        "results": results,
    }
