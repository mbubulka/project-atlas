"""
What-If Analysis Runner: Executes financial scenario analysis for coaching questions.

This module takes a coaching question and runs the appropriate financial models
to generate what-if scenarios with updated metrics and insights.
"""

from typing import Any, Dict, List, Optional

from src.data_models import TransitionProfile
from src.wizard.summary_engine import calculate_financial_metrics


def run_what_if_analysis_for_question(
    profile: TransitionProfile,
    coaching_question,
    coach,
) -> Optional[Dict[str, Any]]:
    """
    Run what-if analysis based on selected coaching question.

    Args:
        profile: Current user's TransitionProfile
        coaching_question: CoachingQuestion object selected
        coach: CoachingEngine instance

    Returns:
        Dict with what-if analysis results including metrics and insights
    """

    question_text = coaching_question.question.lower()
    result = {
        "monthly_gap": "N/A",
        "monthly_gap_delta": None,
        "total_gap": "N/A",
        "total_gap_delta": None,
        "runway": "N/A",
        "runway_delta": None,
        "insights": [],
    }

    try:
        # Get baseline metrics from current profile
        baseline = calculate_financial_metrics(profile)

        # Detect what-if scenario from question content
        insights = []

        # ===== SCENARIO 1: Extended Job Search =====
        if "job" in question_text and (
            "longer" in question_text
            or "6+" in question_text
            or "more months" in question_text
            or "how long" in question_text
        ):
            # Run with extended job search (add 3 months)
            extended_profile_dict = {k: getattr(profile, k) for k in profile.__dataclass_fields__}
            extended_profile_dict["job_search_timeline_months"] = profile.job_search_timeline_months + 3
            extended_profile = TransitionProfile(**extended_profile_dict)

            extended = calculate_financial_metrics(extended_profile)

            result["monthly_gap"] = f"${extended.phase1_monthly_gap:,.0f}"
            result["monthly_gap_delta"] = f"vs ${baseline.phase1_monthly_gap:,.0f}"
            result["total_gap"] = f"${extended.phase1_total_gap:,.0f}"
            result["total_gap_delta"] = f"vs ${baseline.phase1_total_gap:,.0f}"
            result["runway"] = f"{extended.runway_months:.1f} months"
            result["runway_delta"] = f"vs {baseline.runway_months:.1f} months"

            gap_increase = extended.phase1_total_gap - baseline.phase1_total_gap
            if gap_increase > 0:
                insights.append(f"3-month delay increases total gap by " f"${gap_increase:,.0f}")
            if extended.runway_months < 3:
                insights.append(
                    "[WARNING] Extended job search depletes savings quickly - " "consider cost reduction or additional income"
                )
            else:
                insights.append(
                    f"You still have {extended.runway_months:.1f} months " "of runway - manageable timeline"
                )

        # ===== SCENARIO 2: Salary Uncertainty =====
        elif "confident" in question_text or "salary" in question_text:
            # Run with 10% salary reduction
            reduced_profile_dict = {k: getattr(profile, k) for k in profile.__dataclass_fields__}
            reduced_salary = profile.estimated_annual_salary * 0.9
            reduced_profile_dict["estimated_annual_salary"] = reduced_salary
            reduced_profile = TransitionProfile(**reduced_profile_dict)

            reduced = calculate_financial_metrics(reduced_profile)

            phase2_gap = reduced.phase2_monthly_expenses - reduced.phase2_monthly_income
            baseline_phase2_gap = baseline.phase2_monthly_expenses - baseline.phase2_monthly_income

            result["monthly_gap"] = f"${phase2_gap:,.0f}"
            result["monthly_gap_delta"] = f"vs ${baseline_phase2_gap:,.0f}"
            result["total_gap"] = f"${reduced.phase1_total_gap:,.0f}"
            result["total_gap_delta"] = f"vs ${baseline.phase1_total_gap:,.0f}"

            insights.append(
                f"10% salary reduction: " f"${profile.estimated_annual_salary:,.0f} → " f"${reduced_salary:,.0f}"
            )
            if phase2_gap > 0:
                insights.append(
                    "[WARNING] Lower salary creates persistent monthly shortfall - " "would require expense reduction"
                )
            else:
                insights.append("Still achievable with modest salary reduction if " "needed")

        # ===== SCENARIO 3: Spouse Income =====
        elif "spouse" in question_text:
            # Run with spouse income reduced to 0
            no_spouse_profile_dict = {k: getattr(profile, k) for k in profile.__dataclass_fields__}
            no_spouse_profile_dict["spouse_annual_income"] = 0.0
            no_spouse_profile = TransitionProfile(**no_spouse_profile_dict)

            no_spouse = calculate_financial_metrics(no_spouse_profile)

            result["monthly_gap"] = f"${no_spouse.phase1_monthly_gap:,.0f}"
            result["monthly_gap_delta"] = f"vs ${baseline.phase1_monthly_gap:,.0f}"
            result["total_gap"] = f"${no_spouse.phase1_total_gap:,.0f}"
            result["total_gap_delta"] = f"vs ${baseline.phase1_total_gap:,.0f}"
            result["runway"] = f"{no_spouse.runway_months:.1f} months"
            result["runway_delta"] = f"vs {baseline.runway_months:.1f} months"

            spouse_income = getattr(profile, "spouse_annual_income", 0.0)
            if spouse_income > 0:
                insights.append(f"Plan is heavily dependent on spouse's " f"${spouse_income:,.0f}/yr income")
            if no_spouse.runway_months < 12:
                insights.append(
                    "[WARNING] Loss of spouse income creates critical liquidity "
                    "gap - emergency fund only covers "
                    f"{no_spouse.runway_months:.1f} months"
                )

        # ===== SCENARIO 4: Expense Reduction =====
        elif "expense" in question_text or "cut" in question_text or "reduce" in question_text:
            # Run with 10% expense reduction
            reduced_expense_profile_dict = {k: getattr(profile, k) for k in profile.__dataclass_fields__}
            total_expenses = (
                profile.monthly_expenses_mandatory
                + profile.monthly_expenses_negotiable
                + profile.monthly_expenses_optional
            )
            reduction = total_expenses * 0.10
            reduced_expense_profile_dict["monthly_expenses_negotiable"] = profile.monthly_expenses_negotiable - (
                reduction * 0.5
            )
            reduced_expense_profile_dict["monthly_expenses_optional"] = profile.monthly_expenses_optional - (
                reduction * 0.5
            )
            reduced_expense_profile = TransitionProfile(**reduced_expense_profile_dict)

            reduced_exp = calculate_financial_metrics(reduced_expense_profile)

            result["monthly_gap"] = f"${reduced_exp.phase1_monthly_gap:,.0f}"
            result["monthly_gap_delta"] = f"vs ${baseline.phase1_monthly_gap:,.0f}"
            result["total_gap"] = f"${reduced_exp.phase1_total_gap:,.0f}"
            result["total_gap_delta"] = f"vs ${baseline.phase1_total_gap:,.0f}"
            result["runway"] = f"{reduced_exp.runway_months:.1f} months"
            result["runway_delta"] = f"vs {baseline.runway_months:.1f} months"

            insights.append(f"10% expense reduction saves " f"${reduction:,.0f}/month during job search")
            if reduced_exp.phase1_monthly_gap <= 0:
                insights.append("[OK] 10% expense cut closes monthly gap entirely - " "plan becomes sustainable")
            else:
                insights.append(
                    f"Still leaves ${reduced_exp.phase1_monthly_gap:,.0f} " f"monthly gap - may need larger cuts"
                )

        # ===== SCENARIO 5: Year Off / No Job Search =====
        elif "year off" in question_text or "take time" in question_text:
            # Run with 12-month job search delay (year off)
            year_off_profile_dict = {k: getattr(profile, k) for k in profile.__dataclass_fields__}
            year_off_profile_dict["job_search_timeline_months"] = 12
            year_off_profile = TransitionProfile(**year_off_profile_dict)

            year_off = calculate_financial_metrics(year_off_profile)

            result["monthly_gap"] = f"${year_off.phase1_monthly_gap:,.0f}"
            result["monthly_gap_delta"] = f"vs ${baseline.phase1_monthly_gap:,.0f}"
            result["total_gap"] = f"${year_off.phase1_total_gap:,.0f}"
            result["total_gap_delta"] = f"vs ${baseline.phase1_total_gap:,.0f}"
            result["runway"] = f"{year_off.runway_months:.1f} months"
            result["runway_delta"] = f"vs {baseline.runway_months:.1f} months"

            gap_for_year = year_off.phase1_total_gap - baseline.phase1_total_gap
            insights.append(f"Taking a year off (12-month delay) increases total gap " f"by ${gap_for_year:,.0f}")
            if year_off.runway_months < 12:
                insights.append(
                    "[WARNING] CRITICAL: Your savings would be depleted BEFORE "
                    "you reach 12 months - year off is not feasible"
                )
                insights.append(f"Maximum sustainable delay is " f"{baseline.runway_months:.0f} months")
            else:
                insights.append(
                    f"[OK] You have enough savings to support "
                    f"{year_off.runway_months:.1f} months off - "
                    "year off is feasible"
                )

        # ===== DEFAULT: Generic scenario =====
        else:
            insights.append("Analyzing your financial flexibility...")
            insights.append(f"Current monthly gap: ${baseline.phase1_monthly_gap:,.0f}")
            insights.append(f"Current runway: {baseline.runway_months:.1f} months")

        result["insights"] = insights

    except Exception as e:
        result["insights"] = [f"Error running analysis: {str(e)}. Please check your inputs."]

    return result
