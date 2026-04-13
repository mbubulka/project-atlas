"""
Sustainability Calculator for ProjectAtlas

Answers the critical questions:
1. "Am I in trouble?" (Can I afford this transition?)
2. "How long will my plan last?" (Months of runway)
3. "What needs to change?" (Specific recommendations)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class RiskLevel(Enum):
    """Risk assessment levels."""

    GREEN = "[LOW] Healthy"
    YELLOW = "[MED] Caution"
    RED = "[HIGH] High Risk"


@dataclass
class SustainabilityResult:
    """Results from sustainability analysis."""

    risk_level: RiskLevel
    monthly_surplus: float
    months_of_runway: int
    critical_threshold: float
    status_summary: str
    recommendations: List[str]
    credit_card_buffer_months: Optional[int] = None  # How long CC can sustain the deficit
    prepaid_expiration_months: Optional[int] = None  # When prepaid expenses end
    combined_runway_months: Optional[int] = None  # Savings + CC combined runway

    def to_dict(self) -> dict:
        """Convert to dictionary for easy display."""
        return {
            "risk_level": self.risk_level.value,
            "monthly_surplus": self.monthly_surplus,
            "months_of_runway": self.months_of_runway,
            "critical_threshold": self.critical_threshold,
            "status_summary": self.status_summary,
            "recommendations": self.recommendations,
            "credit_card_buffer_months": self.credit_card_buffer_months,
            "prepaid_expiration_months": self.prepaid_expiration_months,
            "combined_runway_months": self.combined_runway_months,
        }


class SustainabilityCalculator:
    """
    Calculates financial sustainability for transition scenario.

    Core Logic:
    - Total monthly income = Military Pension + VA + New Job + Spouse + Other
    - Total monthly mandatory expenses = Housing + Healthcare + Insurance + Utilities + Food
    - Monthly surplus/deficit = Income - Mandatory Expenses
    - Runway = Liquid Savings / Monthly Deficit (if deficit)

    Risk Levels:
    - GREEN: Surplus >= $3,000/month + 12+ months runway
    - YELLOW: Surplus $1,000-$3,000/month OR 6-12 months runway
    - RED: Deficit OR < 6 months runway
    """

    # Critical thresholds
    HEALTHY_SURPLUS = 3000  # $3K/month = healthy buffer
    MINIMUM_RUNWAY = 12  # 12 months minimum for comfort
    CAUTION_RUNWAY = 6  # 6 months = caution territory

    @staticmethod
    def calculate(
        monthly_income: float,
        mandatory_expenses: float,
        liquid_savings: float,
        negotiable_expenses: float = 0,
        credit_card_limit: float = 0,
        prepaid_months_remaining: int = 0,
        expected_job_timeline_months: int = 6,
    ) -> SustainabilityResult:
        """
        Calculate sustainability and generate recommendations.

        Args:
            monthly_income: Total monthly income from all sources
            mandatory_expenses: Housing, healthcare, insurance, utilities, food
            liquid_savings: Cash available (checking + savings + accessible investments)
            negotiable_expenses: Discretionary spending (dining, entertainment, subscriptions)
            credit_card_limit: Available credit card capacity to bridge gaps
            prepaid_months_remaining: How many more months of prepaid coverage
            expected_job_timeline_months: When do you expect to land a job (for job search runway calc)

        Returns:
            SustainabilityResult with risk level and recommendations
        """

        # Calculate monthly surplus/deficit
        monthly_surplus = monthly_income - mandatory_expenses

        # Calculate runway with savings alone
        if monthly_surplus >= 0:
            # Positive cash flow - runway is theoretically infinite
            months_of_runway = 999  # Use high number to indicate indefinite
        else:
            # Negative cash flow - how long until savings depleted?
            if liquid_savings <= 0:
                months_of_runway = 0
            else:
                monthly_deficit = abs(monthly_surplus)
                months_of_runway = int(liquid_savings / monthly_deficit)

        # Calculate combined runway (savings + CC capacity)
        combined_runway_months = None
        if monthly_surplus < 0:
            total_available = liquid_savings + credit_card_limit
            if total_available > 0:
                monthly_deficit = abs(monthly_surplus)
                combined_runway_months = int(total_available / monthly_deficit)

        # Assess risk level with enhanced logic
        risk_level, status, recommendations = SustainabilityCalculator._assess_risk(
            monthly_surplus=monthly_surplus,
            months_of_runway=months_of_runway,
            liquid_savings=liquid_savings,
            credit_card_limit=credit_card_limit,
            combined_runway_months=combined_runway_months,
            mandatory_expenses=mandatory_expenses,
            negotiable_expenses=negotiable_expenses,
            monthly_income=monthly_income,
            prepaid_months_remaining=prepaid_months_remaining,
            expected_job_timeline_months=expected_job_timeline_months,
        )

        return SustainabilityResult(
            risk_level=risk_level,
            monthly_surplus=monthly_surplus,
            months_of_runway=months_of_runway if months_of_runway != 999 else None,
            critical_threshold=SustainabilityCalculator.HEALTHY_SURPLUS,
            status_summary=status,
            recommendations=recommendations,
            credit_card_buffer_months=combined_runway_months if monthly_surplus < 0 else None,
            prepaid_expiration_months=prepaid_months_remaining if prepaid_months_remaining > 0 else None,
            combined_runway_months=combined_runway_months,
        )

    @staticmethod
    def _assess_risk(
        monthly_surplus: float,
        months_of_runway: int,
        liquid_savings: float,
        credit_card_limit: float,
        combined_runway_months: Optional[int],
        mandatory_expenses: float,
        negotiable_expenses: float,
        monthly_income: float,
        prepaid_months_remaining: int,
        expected_job_timeline_months: int,
    ) -> tuple:
        """
        Assess risk level with smart logic accounting for CC capacity, prepaid timeline, and job search runway.

        Returns:
            (RiskLevel, status_summary, recommendations)
        """
        recommendations = []

        # SMART RISK ASSESSMENT LOGIC

        # Case 1: POSITIVE CASH FLOW (Surplus >= $0)
        if monthly_surplus >= 0:
            if monthly_surplus >= SustainabilityCalculator.HEALTHY_SURPLUS:
                risk_level = RiskLevel.GREEN
                status = f"[OK] **Healthy cash flow**. You have ${monthly_surplus:,.0f}/month surplus. This covers your expenses and builds savings."
                recommendations = [
                    "Continue current plan - you're in excellent shape",
                    "Consider accelerating debt paydown with excess cash flow",
                    "Build emergency fund to 6+ months of expenses",
                ]
            else:
                # Small surplus (between 0 and $3K)
                risk_level = RiskLevel.GREEN
                status = f"[OK] **Positive cash flow**. You have ${monthly_surplus:,.0f}/month surplus. You're covering expenses and growing savings."
                recommendations = [
                    "Current plan is sustainable long-term",
                    "Once job starts, increase to $3K+ monthly buffer",
                    "Consider negotiable expenses if tighter margins emerge",
                ]

        # Case 2: SMALL DEFICIT WITH STRONG BACKUP (Savings + CC can sustain)
        elif monthly_surplus < 0 and combined_runway_months and combined_runway_months >= expected_job_timeline_months:
            # Deficit exists BUT savings + CC can last longer than expected job timeline
            monthly_deficit = abs(monthly_surplus)

            if combined_runway_months >= 18:
                risk_level = RiskLevel.GREEN
                status = f"[OK] **Manageable deficit**. ${monthly_deficit:,.0f}/month shortfall, but you have {combined_runway_months} months of runway (savings + credit) before needing to find a job."
                recommendations = [
                    f"Your ${credit_card_limit:,.0f} credit card limit + ${liquid_savings:,.0f} savings = {combined_runway_months} months runway",
                    f"Target job search timeline: within {expected_job_timeline_months} months [OK]",
                    "At month 1, use savings. Extend CC toward month 12+ if needed.",
                    f"If prepaid expenses end in {prepaid_months_remaining} months, budget will tighten - account for that.",
                ]
            else:
                risk_level = RiskLevel.YELLOW
                status = f"[WARNING] **Limited runway**. ${monthly_deficit:,.0f}/month deficit. You have ~{combined_runway_months} months of combined runway (savings + CC)."
                recommendations = [
                    f"Your resources (${liquid_savings:,.0f} savings + ${credit_card_limit:,.0f} CC) last ~{combined_runway_months} months",
                    f"URGENT: Focus job search to complete within {min(combined_runway_months, expected_job_timeline_months)} months",
                    f"After month {prepaid_months_remaining}, expenses increase - plan for that transition",
                    "Consider negotiable/optional expense cuts NOW to extend runway",
                ]

        # Case 3: SMALL DEFICIT BUT GROWING SAVINGS (with prepaid benefit)
        elif monthly_surplus < 0 and prepaid_months_remaining > 0:
            monthly_deficit = abs(monthly_surplus)
            months_with_prepaid = int(liquid_savings / monthly_deficit) if monthly_deficit > 0 else 999

            if months_with_prepaid >= expected_job_timeline_months:
                risk_level = RiskLevel.YELLOW
                status = f"[WARNING] **Manageable with prepaid buffer**. ${monthly_deficit:,.0f}/month deficit, but covered for ~{months_with_prepaid} months (until prepaid expenses end at month {prepaid_months_remaining})."
                recommendations = [
                    f"Months 1-{prepaid_months_remaining}: Savings handle ${monthly_deficit:,.0f}/month deficit ({months_with_prepaid} months runway)",
                    f"Month {prepaid_months_remaining}+: Expenses increase when prepaid end → use CC or find job income",
                    f"TARGET: Secure job within {expected_job_timeline_months} months to cover the increase",
                    "Use credit card strategically toward end of prepaid period",
                ]
            else:
                risk_level = RiskLevel.RED
                status = f"[HIGH] **Time-sensitive risk**. ${monthly_deficit:,.0f}/month deficit + only {months_with_prepaid} months savings runway before prepaid ends."
                recommendations = [
                    "CRITICAL: Job search must complete ASAP",
                    f"Savings last ~{months_with_prepaid} months. Month {prepaid_months_remaining} brings cost increase.",
                    "Combine strategies: CC buffer + negotiable expense cuts + aggressive job search",
                    f"Break-even point: Need ${monthly_deficit:,.0f}/month additional income by month {prepaid_months_remaining + min(3, months_with_prepaid // 2)}",
                ]

        # Case 4: DEFICIT WITHOUT STRONG BACKUP
        elif months_of_runway and months_of_runway > 0:
            monthly_deficit = abs(monthly_surplus)

            if months_of_runway >= expected_job_timeline_months:
                risk_level = RiskLevel.YELLOW
                status = f"[WARNING] **Moderate risk**. ${monthly_deficit:,.0f}/month deficit, but {months_of_runway} months of savings runway."
                recommendations = [
                    f"Savings runway: {months_of_runway} months",
                    f"TARGET: Job search completion within {expected_job_timeline_months} months [OK]",
                    "Use first 3 months aggressively for job search",
                    "If job delayed, reduce negotiable/optional expenses",
                ]
            else:
                risk_level = RiskLevel.RED
                status = f"[HIGH] **High risk - urgent action needed**. ${monthly_deficit:,.0f}/month deficit with only {months_of_runway} months of runway."
                recommendations = [
                    "CRITICAL: Reduce monthly deficit IMMEDIATELY",
                    f"Current runway: {months_of_runway} months - not enough buffer",
                    "Action plan: (1) Cut negotiable expenses NOW, (2) Aggressive job search, (3) Consider spouse income increase if possible",
                    f"Need to cut ${monthly_deficit // 2 if monthly_deficit > 500 else monthly_deficit:,.0f}+ from budget",
                ]

        # Case 5: NO RUNWAY (Out of savings)
        else:
            risk_level = RiskLevel.RED
            status = f"[HIGH] **CRITICAL**. ${abs(monthly_surplus):,.0f}/month deficit with no savings runway remaining."
            recommendations = [
                "IMMEDIATE ACTION REQUIRED",
                "1. Cut expenses aggressively (eliminate optional, reduce negotiable)",
                "2. Explore spouse income increase or additional side income",
                "3. Consider line of credit/emergency borrowing if needed",
                "4. Job search is now a survival necessity - not optional",
                "5. Contact financial advisor or counselor for additional options",
            ]

        return risk_level, status, recommendations

    @staticmethod
    def retirement_date_impact(
        monthly_surplus: float,
        target_date: datetime,
    ) -> Dict:
        """
        Calculate impact on retirement timeline.

        If you have monthly surplus/deficit, how does it affect your ability
        to save for future retirement?
        """
        months_until_date = (target_date - datetime.now()).days // 30

        if monthly_surplus > 0:
            total_saveable = monthly_surplus * months_until_date
            impact = "POSITIVE - You can accelerate retirement savings"
        else:
            total_saveable = monthly_surplus * months_until_date
            impact = "NEGATIVE - You're drawing down savings"

        return {
            "months_until_date": months_until_date,
            "monthly_impact": monthly_surplus,
            "total_impact": total_saveable,
            "impact_description": impact,
        }

    @staticmethod
    def sensitivity_analysis(
        base_monthly_surplus: float,
        salary_scenarios: List[float],
        expense_scenarios: List[float],
    ) -> Dict:
        """
        Run sensitivity analysis: How do salary/expense changes affect sustainability?

        Returns:
            Dictionary of scenario outcomes
        """
        results = {}

        for salary in salary_scenarios:
            salary_delta = salary - 160000  # Assume base is 160K
            new_surplus = base_monthly_surplus + salary_delta
            results[f"Salary ${salary:,.0f}"] = {
                "monthly_surplus": new_surplus,
                "impact": "+$" + f"{salary_delta:,.0f}" if salary_delta > 0 else f"{salary_delta:,.0f}",
            }

        for expenses in expense_scenarios:
            expense_delta = base_monthly_surplus - expenses
            results[f"Expenses ${expenses:,.0f}"] = {
                "monthly_surplus": expense_delta,
                "impact": "+$" + f"{expense_delta:,.0f}" if expense_delta > 0 else f"{expense_delta:,.0f}",
            }

        return results


# Example usage
if __name__ == "__main__":
    # Test case: Your scenario
    result = SustainabilityCalculator.calculate(
        monthly_income=10000,  # $160K salary / 12 + pension + VA
        mandatory_expenses=8000,  # Housing, healthcare, food, insurance
        liquid_savings=50000,
    )

    print(f"Risk Level: {result.risk_level.value}")
    print(f"Monthly Surplus: ${result.monthly_surplus:,.0f}")
    print(f"Months of Runway: {result.months_of_runway}")
    print(f"Status: {result.status_summary}")
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
