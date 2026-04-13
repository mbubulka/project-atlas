"""
Profile builder for AI chat integration.

Converts extracted parameters from NaturalLanguageParser into TransitionProfile updates.
Validates completeness and triggers model reruns.
"""

import logging
from typing import Any, Dict, List, Tuple

from src.data_models import TransitionProfile
from src.model_layer.buffer_simulator import run_buffer_simulation
from src.model_layer.healthcare_model import compare_healthcare_costs
from src.model_layer.retirement_pay_model import calculate_take_home_pay

logger = logging.getLogger(__name__)


class ProfileBuilder:
    """Builds and updates TransitionProfile from extracted parameters."""

    # Required fields for basic profile (must-haves)
    REQUIRED_FIELDS = {
        "target_city",
        "estimated_annual_salary",
        "job_search_timeline_months",
        "current_savings",
    }

    # Optional fields (nice-to-have)
    OPTIONAL_FIELDS = {
        "rank",
        "years_of_service",
        "current_va_disability_rating",
        "healthcare_plan_choice",
        "job_offer_certainty",
    }

    @staticmethod
    def apply_parameters(
        profile: TransitionProfile,
        extracted_params: Dict[str, Any],
    ) -> Tuple[TransitionProfile, List[str]]:
        """
        Apply extracted parameters to profile.

        Args:
            profile: Existing TransitionProfile to update
            extracted_params: Dict from NaturalLanguageParser.extract_parameters()

        Returns:
            Tuple of (updated_profile, validation_messages)

        Example:
            >>> parser = NaturalLanguageParser()
            >>> params = parser.extract_parameters("Moving to Denver with $120K salary")
            >>> profile, msgs = ProfileBuilder.apply_parameters(profile, params)
            >>> if profile and not msgs:
            ...     print("Profile ready for models!")
        """
        validation_msgs = []

        # Apply each parameter if present
        if "target_city" in extracted_params and extracted_params["target_city"]:
            profile.target_city = extracted_params["target_city"]

        if "estimated_annual_salary" in extracted_params and extracted_params["estimated_annual_salary"]:
            salary = extracted_params["estimated_annual_salary"]
            if isinstance(salary, str):
                salary = float(salary.replace("$", "").replace(",", ""))
            profile.estimated_annual_salary = salary

        if "job_search_timeline_months" in extracted_params and extracted_params["job_search_timeline_months"]:
            months = extracted_params["job_search_timeline_months"]
            if isinstance(months, str):
                months = int(months)
            profile.job_search_timeline_months = months

        if "current_savings" in extracted_params and extracted_params["current_savings"]:
            savings = extracted_params["current_savings"]
            if isinstance(savings, str):
                savings = float(savings.replace("$", "").replace(",", ""))
            profile.current_savings = savings

        if "rank" in extracted_params and extracted_params["rank"]:
            profile.rank = extracted_params["rank"]

        if "years_of_service" in extracted_params and extracted_params["years_of_service"]:
            yos = extracted_params["years_of_service"]
            if isinstance(yos, str):
                yos = int(yos)
            profile.years_of_service = yos

        if "current_va_disability_rating" in extracted_params and extracted_params["current_va_disability_rating"]:
            rating = extracted_params["current_va_disability_rating"]
            if isinstance(rating, str):
                rating = int(rating)
            profile.current_va_disability_rating = rating

        if "healthcare_plan_choice" in extracted_params and extracted_params["healthcare_plan_choice"]:
            plan = extracted_params["healthcare_plan_choice"]
            valid_plans = ["tricare_select", "va_health", "private_aca", "spouse_employer"]
            if plan.lower() in valid_plans:
                profile.healthcare_plan_choice = plan.lower()
            else:
                validation_msgs.append(f"Invalid healthcare plan '{plan}'. Using default (tricare_select).")

        if "job_offer_certainty" in extracted_params and extracted_params["job_offer_certainty"]:
            certainty = extracted_params["job_offer_certainty"]
            if isinstance(certainty, str):
                certainty = float(certainty) / 100.0 if certainty.endswith("%") else float(certainty)
            if 0.0 <= certainty <= 1.0:
                profile.job_offer_certainty = certainty
            else:
                validation_msgs.append("Certainty must be 0-100%, using default (80%).")

        return profile, validation_msgs

    @staticmethod
    def get_completion_status(profile: TransitionProfile) -> Dict[str, Any]:
        """
        Check profile completeness for model readiness.

        Returns dict with:
        - is_ready: bool (can run models?)
        - missing_required: list of missing required fields
        - missing_optional: list of missing optional fields
        - completion_pct: 0-100 percentage filled

        Example:
            >>> status = ProfileBuilder.get_completion_status(profile)
            >>> if status['is_ready']:
            ...     print("Ready to run forecasts!")
        """
        filled = 0
        total = len(ProfileBuilder.REQUIRED_FIELDS) + len(ProfileBuilder.OPTIONAL_FIELDS)

        missing_required = []
        missing_optional = []

        # Check required fields
        for field in ProfileBuilder.REQUIRED_FIELDS:
            value = getattr(profile, field, None)
            if value and (not isinstance(value, str) or value.strip()):
                filled += 1
            else:
                missing_required.append(field)

        # Check optional fields
        for field in ProfileBuilder.OPTIONAL_FIELDS:
            value = getattr(profile, field, None)
            if value and (not isinstance(value, str) or value.strip()):
                filled += 1
            else:
                missing_optional.append(field)

        completion_pct = int((filled / total) * 100)
        is_ready = len(missing_required) == 0

        return {
            "is_ready": is_ready,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "completion_pct": completion_pct,
            "filled": filled,
            "total": total,
        }

    @staticmethod
    def run_models(profile: TransitionProfile) -> TransitionProfile:
        """
        Run all financial models with current profile.

        Returns updated profile with:
        - annual_take_home_pay
        - monthly_take_home_pay
        - annual_healthcare_cost
        - monthly_cash_flow
        - final_cash_buffer
        - financial_verdict

        Example:
            >>> profile = ProfileBuilder.run_models(profile)
            >>> print(f"Monthly cash flow: ${profile.monthly_take_home_pay:,.2f}")
        """
        try:
            # 1. Calculate retirement and VA income
            take_home = calculate_take_home_pay(profile)
            profile.annual_take_home_pay = take_home
            profile.monthly_take_home_pay = take_home / 12

            # 2. Calculate healthcare costs
            profile = compare_healthcare_costs(profile)
            # Healthcare costs are now stored in profile.annual_healthcare_cost

            # 3. Run buffer simulator (month-by-month projection)
            cash_flow, final_buffer, verdict = run_buffer_simulation(profile)
            profile.monthly_cash_flow = cash_flow
            profile.final_cash_buffer = final_buffer
            profile.financial_verdict = verdict

            logger.info(
                f"Models executed: verdict={verdict}, "
                f"buffer=${final_buffer:,.2f}, "
                f"monthly_income=${profile.monthly_take_home_pay:,.2f}"
            )

        except Exception as e:
            logger.error(f"Error running models: {e}")
            raise

        return profile

    @staticmethod
    def format_profile_summary(profile: TransitionProfile) -> str:
        """
        Format profile data into readable chat response.

        Returns formatted string for display to user.
        """
        parts = []

        # Identity section
        if profile.rank or profile.years_of_service:
            identity = []
            if profile.rank:
                identity.append(f"**Rank:** {profile.rank}")
            if profile.years_of_service:
                identity.append(f"**YOS:** {profile.years_of_service} years")
            if identity:
                parts.append("**Military Background**\n" + " | ".join(identity))

        # Transition parameters
        transition = []
        if profile.target_city:
            transition.append(f"**Target City:** {profile.target_city}")
        if profile.estimated_annual_salary:
            transition.append(f"**Estimated Salary:** ${profile.estimated_annual_salary:,.0f}/year")
        if profile.job_search_timeline_months:
            transition.append(f"**Job Search Timeline:** {profile.job_search_timeline_months} months")
        if profile.current_savings:
            transition.append(f"**Current Savings:** ${profile.current_savings:,.0f}")
        if transition:
            parts.append("**Transition Plan**\n" + " | ".join(transition))

        # Healthcare & VA
        healthcare_va = []
        if profile.current_va_disability_rating:
            healthcare_va.append(f"**VA Rating:** {profile.current_va_disability_rating}%")
        if profile.healthcare_plan_choice:
            healthcare_va.append(f"**Healthcare Plan:** {profile.healthcare_plan_choice}")
        if healthcare_va:
            parts.append("**Healthcare & Benefits**\n" + " | ".join(healthcare_va))

        # Financial forecast (if models have run)
        if profile.monthly_take_home_pay > 0:
            forecast = []
            forecast.append(f"**Monthly Income:** ${profile.monthly_take_home_pay:,.2f}")
            forecast.append(f"**Monthly Healthcare:** ${profile.monthly_healthcare_cost:,.2f}")
            forecast.append(f"**Final Cash Buffer:** ${profile.final_cash_buffer:,.2f}")
            forecast.append(f"**Verdict:** {profile.financial_verdict}")
            parts.append("**Financial Forecast**\n" + " | ".join(forecast))

        return "\n\n".join(parts) if parts else "No profile data yet."
