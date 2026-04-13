"""
Summary engine: Synthesizes all wizard inputs into a decision narrative.

Takes: Complete profile from all 4 steps
Does: Runs all calculations (taxes, runway, break-even, sensitivities)
Returns: Structured decision summary with narrative, risks, levers, and recommendation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Union

import streamlit as st

from src.data_models import TransitionProfile
from src.model_layer.healthcare_model import get_mixed_healthcare_costs
from src.model_layer.retirement_pay_model import (
    get_effective_tax_rate,
)
from src.model_layer.va_offset_calculator import calculate_va_offset_income


def format_months_value(value: Union[int, float]) -> Union[str, int]:
    """
    Format a months value, handling infinity gracefully.

    Args:
        value: A numeric value representing months

    Returns: "Indefinite" if infinity, otherwise the integer value
    """
    if isinstance(value, float) and value == float("inf"):
        return "Indefinite"
    return int(value) if isinstance(value, float) else value


@dataclass
class FinancialMetrics:
    """Calculated financial metrics for decision summary."""

    # Phase 1 (During job search)
    phase1_monthly_income: float = 0.0
    phase1_monthly_expenses: float = 0.0
    phase1_monthly_gap: float = 0.0
    phase1_total_gap: float = 0.0

    # Phase 2 (After job starts)
    phase2_monthly_income: float = 0.0
    phase2_monthly_expenses: float = 0.0
    phase2_monthly_surplus: float = 0.0
    phase2_annual_surplus: float = 0.0

    # Liquidity
    starting_savings: float = 0.0
    savings_after_gap: float = 0.0
    runway_months: float = 0.0
    emergency_fund_depletion_month: float = 0.0

    # Taxes
    effective_tax_rate: float = 0.0
    marginal_tax_rate: float = 0.0
    annual_taxes: float = 0.0

    # Healthcare
    annual_healthcare_cost: float = 0.0
    monthly_healthcare_cost: float = 0.0

    # 5-year outlook
    five_year_total: float = 0.0


@dataclass
class DecisionRisk:
    """Represents a risk factor."""

    name: str
    description: str
    severity: str  # 'low', 'moderate', 'high', 'critical'
    impact: str  # How it affects the decision
    mitigation: str  # What to do about it


@dataclass
class DecisionLever:
    """Represents a lever (what moves the outcome)."""

    name: str
    current_value: float
    low_value: float
    high_value: float
    impact_low: float  # Financial impact if set to low
    impact_high: float  # Financial impact if set to high
    sensitivity_rank: int  # 1 = most sensitive


@dataclass
class DecisionSummary:
    """Complete decision synthesis."""

    # Viability
    is_viable: bool
    viability_statement: str
    confidence_level: str  # 'low', 'moderate', 'high'

    # Metrics
    metrics: FinancialMetrics

    # Risks
    primary_risks: List[DecisionRisk] = field(default_factory=list)

    # Levers
    primary_levers: List[DecisionLever] = field(default_factory=list)

    # Break-even analysis
    breakeven_scenarios: Dict[str, str] = field(default_factory=dict)

    # Confidence scenarios
    conservative_scenario: Dict[str, float] = field(default_factory=dict)
    balanced_scenario: Dict[str, float] = field(default_factory=dict)
    aggressive_scenario: Dict[str, float] = field(default_factory=dict)

    # Recommendation
    recommendation: str = ""
    action_items: List[str] = field(default_factory=list)

    # Key assumptions
    key_assumptions: List[str] = field(default_factory=list)

    @property
    def identified_risks(self) -> List[DecisionRisk]:
        """Alias for primary_risks for backward compatibility."""
        return self.primary_risks

    @property
    def decision_levers(self) -> List[DecisionLever]:
        """Alias for primary_levers for backward compatibility."""
        return self.primary_levers


def calculate_financial_metrics(profile: TransitionProfile) -> FinancialMetrics:
    """
    Run all financial calculations for the profile.

    Returns: FinancialMetrics with all computed values
    """
    metrics = FinancialMetrics()

    # ========== PHASE 1: DURING JOB SEARCH ==========
    # Income during job search (retirement + VA + spouse)
    # Use corrected VA offset calculation (not simple addition)
    pension_monthly = profile.current_annual_retirement_pay / 12
    sbp_cost = getattr(profile, "sbp_monthly_cost", 0)
    pension_deductions = getattr(profile, "pension_pretax_expense", 0)
    va_rating = profile.current_va_disability_rating
    va_benefit_annual = profile.current_va_annual_benefit
    va_benefit_monthly = va_benefit_annual / 12 if va_benefit_annual > 0 else 0
    
    # Calculate corrected military income (handles offset for <50% ratings)
    va_calc = calculate_va_offset_income(
        pension_monthly_pretax=pension_monthly,
        sbp_monthly_cost=sbp_cost,
        pension_pretax_deductions=pension_deductions,
        va_disability_rating=va_rating,
        va_monthly_benefit=va_benefit_monthly,
        estimated_tax_rate=0.22,  # Default federal tax rate
    )
    
    military_income_monthly = va_calc["total_monthly_income"]
    spouse_monthly = profile.spouse_annual_income / 12
    other_monthly = getattr(profile, "other_annual_income", 0) / 12
    
    metrics.phase1_monthly_income = military_income_monthly + spouse_monthly + other_monthly

    # Expenses
    metrics.phase1_monthly_expenses = (
        profile.monthly_expenses_mandatory + profile.monthly_expenses_negotiable + profile.monthly_expenses_optional
    )

    # Gap
    metrics.phase1_monthly_gap = metrics.phase1_monthly_income - metrics.phase1_monthly_expenses
    metrics.phase1_total_gap = metrics.phase1_monthly_gap * profile.job_search_timeline_months

    # ========== PHASE 2: AFTER JOB STARTS ==========
    # Same military income + new job salary
    phase2_monthly_income = military_income_monthly + spouse_monthly + other_monthly + (profile.estimated_annual_salary / 12)
    metrics.phase2_monthly_income = phase2_monthly_income

    # Expenses remain same
    metrics.phase2_monthly_expenses = metrics.phase1_monthly_expenses

    # Surplus
    metrics.phase2_monthly_surplus = metrics.phase2_monthly_income - metrics.phase2_monthly_expenses
    metrics.phase2_annual_surplus = metrics.phase2_monthly_surplus * 12

    # ========== LIQUIDITY ==========
    metrics.starting_savings = profile.current_savings
    metrics.savings_after_gap = metrics.starting_savings + metrics.phase1_total_gap

    if metrics.phase1_monthly_gap > 0:
        # Surplus covers gap, so savings grow
        metrics.runway_months = float("inf") if metrics.phase1_monthly_gap >= metrics.phase1_monthly_expenses else 999
    else:
        # Deficit. How many months until savings depleted?
        if abs(metrics.phase1_monthly_gap) > 0:
            metrics.runway_months = metrics.starting_savings / abs(metrics.phase1_monthly_gap)
        else:
            metrics.runway_months = float("inf")

    metrics.emergency_fund_depletion_month = metrics.runway_months

    # ========== TAXES ==========
    metrics.effective_tax_rate = get_effective_tax_rate(profile)
    # Tax on military + other income during phase 1, plus new job salary in phase 2
    phase1_annual_income = metrics.phase1_monthly_income * 12
    metrics.annual_taxes = (phase1_annual_income + profile.estimated_annual_salary) * metrics.effective_tax_rate

    # ========== HEALTHCARE ==========
    healthcare_profile = profile
    healthcare_profile.current_va_disability_rating = st.session_state.get("unified_va_disability_rating", 30)
    try:
        costs = get_mixed_healthcare_costs(
            profile=healthcare_profile,
            member_medical_plan=profile.healthcare_plan_choice,
            dependent_medical_plan=profile.healthcare_plan_choice,
            member_vision_plan="tricare_vision",
            dependent_vision_plan="tricare_vision",
            member_dental_plan="tricare_dental",
            dependent_dental_plan="tricare_dental",
            family_size=max(1, profile.dependents + 1),
        )
        metrics.annual_healthcare_cost = costs.get("total_annual", 0.0)
        metrics.monthly_healthcare_cost = costs.get("total_monthly", 0.0)
    except Exception:
        metrics.annual_healthcare_cost = 3000  # Default estimate
        metrics.monthly_healthcare_cost = 250

    return metrics


def identify_risks(profile: TransitionProfile, metrics: FinancialMetrics) -> List[DecisionRisk]:
    """Identify primary risks in the transition plan."""
    risks = []

    # Risk 1: Health coverage gap
    if metrics.emergency_fund_depletion_month < 36:  # Less than 3 years
        risks.append(
            DecisionRisk(
                name="Health Coverage Gap",
                description=f"Emergency fund depletes in {metrics.emergency_fund_depletion_month:.1f} months",
                severity="high" if metrics.emergency_fund_depletion_month < 12 else "moderate",
                impact="Limited ability to absorb unexpected costs",
                mitigation=f"Build emergency fund to 6+ months expenses (need ${metrics.phase1_monthly_expenses * 6:,.0f})",
            )
        )

    # Risk 2: Job timing uncertainty
    if profile.job_search_timeline_months > 6:
        risks.append(
            DecisionRisk(
                name="Job Search Duration Risk",
                description=f"Assuming {profile.job_search_timeline_months}-month job search",
                severity="moderate",
                impact=(
                    f"Each extra month costs ${metrics.phase1_monthly_gap * -1:,.0f}"
                    if metrics.phase1_monthly_gap < 0
                    else "Delayed income start"
                ),
                mitigation=f"Start job search immediately; consider contract roles; explore side income",
            )
        )

    # Risk 3: Income assumption uncertainty
    if profile.estimated_annual_salary < 100000:
        risks.append(
            DecisionRisk(
                name="Salary Assumption Risk",
                description=f"Target salary ${profile.estimated_annual_salary:,.0f}",
                severity="moderate",
                impact=f"±$10K salary change = ±${10000/12:,.0f}/month impact",
                mitigation="Get job offers in writing; test market for your skills; have backup plan",
            )
        )

    # Risk 4: VA rating uncertainty
    va_rating = st.session_state.get("unified_va_disability_rating", 30)
    if va_rating == 30 or va_rating == 50:  # Common uncertainty points
        risks.append(
            DecisionRisk(
                name="VA Rating Assumption Risk",
                description=f"Current rating: {va_rating}% (assumed/estimated)",
                severity="low",
                impact=f"Rating change ±10% = ±$1,200/month impact",
                mitigation="Request VA rating review if pending; plan conservatively",
            )
        )

    # Risk 5: Debt payoff pressure
    if profile.current_debt > 0:
        debt_ratio = profile.current_debt / max(metrics.phase2_monthly_surplus * 12, 1)
        if debt_ratio > 1:
            risks.append(
                DecisionRisk(
                    name="Debt Payoff Timeline",
                    description=f"${profile.current_debt:,.0f} debt vs ${metrics.phase2_annual_surplus:,.0f}/year surplus",
                    severity="moderate",
                    impact="Limits financial flexibility",
                    mitigation=f"Accelerate payoff in first {int(profile.current_debt / max(metrics.phase2_monthly_surplus, 1))} months after job starts",
                )
            )

    return sorted(risks, key=lambda r: ["low", "moderate", "high", "critical"].index(r.severity), reverse=True)


def identify_levers(profile: TransitionProfile, metrics: FinancialMetrics) -> List[DecisionLever]:
    """Identify what moves the outcome (primary levers)."""
    levers = []

    # Lever 1: VA Rating
    va_current = st.session_state.get("unified_va_disability_rating", 30)
    # Rough estimate: 10% disability ~$130/month, scales roughly linearly
    va_low_impact = (20 / 10) * 130 / 12  # At 20%
    va_high_impact = (50 / 10) * 130 / 12  # At 50%
    levers.append(
        DecisionLever(
            name="VA Disability Rating",
            current_value=va_current,
            low_value=20,
            high_value=70,
            impact_low=va_low_impact,
            impact_high=va_high_impact,
            sensitivity_rank=1,
        )
    )

    # Lever 2: Job Start Delay
    delay_impact = metrics.phase1_monthly_gap * -1  # Each month costs this much
    levers.append(
        DecisionLever(
            name="Job Search Duration",
            current_value=profile.job_search_timeline_months,
            low_value=3,
            high_value=12,
            impact_low=delay_impact * 3,
            impact_high=delay_impact * 12,
            sensitivity_rank=2,
        )
    )

    # Lever 3: Target Salary
    salary_sensitivity = 10000 / 12  # $10K salary = $833/month impact
    levers.append(
        DecisionLever(
            name="Estimated Annual Salary",
            current_value=profile.estimated_annual_salary,
            low_value=max(50000, profile.estimated_annual_salary * 0.8),
            high_value=profile.estimated_annual_salary * 1.2,
            impact_low=-salary_sensitivity,
            impact_high=salary_sensitivity,
            sensitivity_rank=3,
        )
    )

    # Lever 4: Monthly Expenses
    expense_reduction = metrics.phase1_monthly_expenses * 0.1 / 12  # 10% cut
    levers.append(
        DecisionLever(
            name="Monthly Expenses",
            current_value=metrics.phase1_monthly_expenses,
            low_value=metrics.phase1_monthly_expenses * 0.8,
            high_value=metrics.phase1_monthly_expenses * 1.2,
            impact_low=expense_reduction,
            impact_high=-expense_reduction,
            sensitivity_rank=4,
        )
    )

    return levers


def generate_decision_summary(profile: TransitionProfile) -> DecisionSummary:
    """
    Generate complete decision summary with narrative.

    Returns: DecisionSummary with all synthesis
    """
    # Calculate metrics first
    metrics = calculate_financial_metrics(profile)

    # Calculate 5-year outlook: Phase 2 annual surplus * 5 years
    metrics.five_year_total = metrics.phase2_annual_surplus * 5

    # Initialize summary with required arguments
    summary = DecisionSummary(
        is_viable=False,  # Will be updated below
        viability_statement="",  # Will be updated below
        confidence_level="low",  # Will be updated below
        metrics=metrics,
    )

    # Identify risks
    summary.primary_risks = identify_risks(profile, summary.metrics)

    # Identify levers
    summary.primary_levers = identify_levers(profile, summary.metrics)

    # ========== VIABILITY ASSESSMENT ==========
    if summary.metrics.savings_after_gap >= 0 and summary.metrics.phase2_monthly_surplus > 0:
        summary.is_viable = True
        summary.viability_statement = "[OK] **VIABLE**: You can afford this transition"

        if summary.metrics.savings_after_gap > profile.monthly_expenses_mandatory * 6:
            summary.confidence_level = "high"
        elif summary.metrics.savings_after_gap > profile.monthly_expenses_mandatory * 3:
            summary.confidence_level = "moderate"
        else:
            summary.confidence_level = "low"
    else:
        summary.is_viable = False
        summary.viability_statement = "[WARNING] **CAUTION**: Potential financial shortfall"
        summary.confidence_level = "low"

    # ========== BREAK-EVEN SCENARIOS ==========
    # Scenario 1: Retire now vs work 1 more year
    if profile.years_of_service >= 19:
        years_1_more = profile.years_of_service + 1
        # Use the actual retirement pay from user input
        # Rough pension calc: 2.5% per year of service (used for delta only)
        pension_multiplier = 0.025
        pension_current = profile.current_annual_retirement_pay
        pension_1yr_more = profile.current_annual_retirement_pay * (
            1 + (pension_multiplier * (years_1_more - profile.years_of_service))
        )
        additional_annual = pension_1yr_more - pension_current
        summary.breakeven_scenarios["Retire now vs 1 more year"] = f"+${additional_annual:,.0f}/year by waiting 1 year"

    # Scenario 2: Job delayed 6 months
    delayed_cost = summary.metrics.phase1_monthly_gap * 6
    summary.breakeven_scenarios["Job delayed 6 months"] = f"${delayed_cost:+,.0f} impact on runway"

    # ========== CONFIDENCE SCENARIOS ==========
    # Conservative: Lower salary, higher expenses, longer job search
    conservative_salary = profile.estimated_annual_salary * 0.9
    conservative_monthly = (
        profile.current_annual_retirement_pay
        + profile.current_va_annual_benefit
        + conservative_salary
        + profile.spouse_annual_income
    ) / 12
    summary.conservative_scenario = {
        "monthly_net": conservative_monthly - summary.metrics.phase1_monthly_expenses,
        "description": "Low salary estimate, current expenses",
    }

    # Balanced: Current assumptions
    summary.balanced_scenario = {
        "monthly_net": summary.metrics.phase2_monthly_surplus,
        "description": "Target salary met, current expenses",
    }

    # Aggressive: Higher salary, lower expenses
    aggressive_salary = profile.estimated_annual_salary * 1.1
    aggressive_expenses = summary.metrics.phase1_monthly_expenses * 0.9
    aggressive_monthly = (
        profile.current_annual_retirement_pay
        + profile.current_va_annual_benefit
        + aggressive_salary
        + profile.spouse_annual_income
    ) / 12
    summary.aggressive_scenario = {
        "monthly_net": aggressive_monthly - aggressive_expenses,
        "description": "High salary estimate, 10% expense reduction",
    }

    # ========== KEY ASSUMPTIONS ==========
    summary.key_assumptions = [
        f"VA rating stays at {st.session_state.get('unified_va_disability_rating', 30)}%",
        f"Job search takes {profile.job_search_timeline_months} months",
        f"Target salary: ${profile.estimated_annual_salary:,.0f}/year",
        f"Current CRDP/tax law remains in effect",
        f"TRICARE eligibility maintained after separation",
        f"No major health events or expenses",
    ]

    # ========== RECOMMENDATION ==========
    if summary.is_viable and summary.confidence_level in ["high", "moderate"]:
        if len(summary.primary_risks) <= 2:
            summary.recommendation = "[LOW] **PROCEED WITH CONFIDENCE** - Low to moderate risk"
        else:
            summary.recommendation = "[MED] **PROCEED WITH CAUTION** - Moderate risk, plan mitigation"
    elif summary.is_viable:
        summary.recommendation = "[MED] **PROCEED WITH PREPARATION** - Tight margins, needs planning"
    else:
        summary.recommendation = "[HIGH] **RECONSIDER OR PLAN B** - Significant shortfall"

    # ========== ACTION ITEMS ==========
    summary.action_items = [
        f"✓ Build {profile.job_search_timeline_months}-month emergency fund (${summary.metrics.phase1_monthly_expenses * profile.job_search_timeline_months:,.0f})",
        f"✓ Start job search {profile.job_search_timeline_months}+ months before separation",
        f"✓ Lock in healthcare plan before separation",
    ]

    if len(summary.primary_risks) > 0:
        top_risk = summary.primary_risks[0]
        summary.action_items.append(f"✓ Address #{top_risk.name}: {top_risk.mitigation}")

    return summary


# Placeholder for rank-to-base-pay conversion (needs to be added)
# This should map O-5, E-7, etc to base pay for pension calculations
