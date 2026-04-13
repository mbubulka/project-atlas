"""
THEMIS Decision Engine: Transition Handling and Emergency Management
through Intelligent Strategy

Analyzes financial position during military transition and recommends
optimal strategy for balancing debt paydown, savings reserves, and
expense reduction.

The engine takes into account:
- Cash runway (how long savings last at current burn rate)
- Credit card runway (available CC credit for emergencies)
- Timing of income sources (pension, disability approval, job offers)
- Interest cost trade-offs (paying debt vs building reserves)
- Mandatory vs discretionary expenses (what can be cut vs must pay)
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class RecommendationLevel(Enum):
    """Confidence level for THEMIS recommendation"""

    CRITICAL = "critical"  # Action required immediately
    HIGH = "high"  # Strong recommendation
    MODERATE = "moderate"  # Reasonable choice
    FLEXIBLE = "flexible"  # Multiple valid approaches


class RecommendedStrategy(Enum):
    """Recommended financial strategy based on runway analysis."""

    BUILD_CASH_ONLY = "Build Cash Only"
    PAY_CC_FIRST = "Pay Credit Card First"
    HYBRID = "Build Cash + Pay CC (Hybrid)"


@dataclass
class TimingFactors:
    """Key timing milestones during transition"""

    months_to_pension: int = 1  # Usually immediate for pension recipients
    months_to_disability_decision: int = 2  # VA processing time estimate
    months_to_job: int = 3  # Expected job search timeline
    months_in_current_status: int = 0  # How many months already in transition


@dataclass
class FinancialPosition:
    """Current financial snapshot"""

    current_savings: float  # Cash on hand
    current_debt: float  # Total debt (CC + loans)
    cc_balance: float  # Credit card balance specifically
    cc_limit: float  # Total available credit
    cc_rate_percent: float  # Interest rate on CC
    avg_loan_rate_percent: float  # Interest on other debt

    # Monthly cash flow
    monthly_income: float  # Pension + VA + spouse + other
    monthly_expenses_required: float  # Non-negotiable expenses
    monthly_expenses_flexible: float  # Can be cut if needed
    monthly_expenses_optional: float  # Luxury, discretionary


@dataclass
class ExpenseBreakdown:
    """Available expense reduction opportunities"""

    required: float  # Essential (housing, utilities, food)
    flexible: float  # Can reduce (subscriptions, dining)
    optional: float  # Can eliminate (hobbies, gifts)

    def get_total(self) -> float:
        return self.required + self.flexible + self.optional

    def get_reducible(self) -> float:
        """How much can be cut"""
        return self.flexible + self.optional


@dataclass
class CreditCardRunway:
    """Analysis of CC as emergency cushion"""

    available_credit: float  # Unused credit line
    available_percent: float  # Percentage of total limit unused
    emergency_cushion_months: float  # How many months this covers

    def is_adequate(self, threshold_months: float = 1.0) -> bool:
        """Check if CC runway is sufficient emergency buffer"""
        return self.emergency_cushion_months >= threshold_months


@dataclass
class SavingsRunway:
    """Analysis of savings sustainability"""

    total_savings: float  # Amount of cash on hand
    monthly_burn: float  # Monthly shortfall (negative if surplus)
    months_available: float  # How long savings lasts

    def is_sustainable(self, min_months: float = 3.0) -> bool:
        """Check if savings can sustain for minimum duration"""
        if self.monthly_burn >= 0:  # Surplus, always sustainable
            return True
        return self.months_available >= min_months


@dataclass
class RunwayMetrics:
    """Runway analysis results."""

    cash_runway_months: float
    cc_peak_balance: float
    cc_peak_month: int
    cc_breaches_limit: bool
    cc_recovery_months: float
    confidence: str  # "High", "Medium", "Low"
    key_risks: List[str]


@dataclass
class THEMISRecommendation:
    """The recommended financial strategy"""

    strategy: str  # Primary recommendation
    debt_paydown_percent: float  # % of surplus to debt
    savings_percent: float  # % of surplus to savings
    expense_reduction_percent: float  # % to cut from expenses
    confidence: RecommendationLevel  # How confident is this recommendation
    rationale: str  # Why this is recommended
    risk_factors: List[str]  # Potential concerns
    quick_wins: List[str]  # Immediate actions to take
    monthly_impact: float  # Monthly financial improvement

    def explain(self) -> str:
        """Generate explanation of recommendation"""
        return f"""
{self.strategy.upper()}

Allocation:
- Debt Paydown: {self.debt_paydown_percent:.0%}
- Savings: {self.savings_percent:.0%}
- Expense Reduction: {self.expense_reduction_percent:.0%}

Confidence: {self.confidence.value.upper()}

Why: {self.rationale}

Risks: {', '.join(self.risk_factors) if self.risk_factors else 'None identified'}

Quick Wins:
{chr(10).join(f'- {win}' for win in self.quick_wins)}

Monthly Impact: ${self.monthly_impact:,.0f}
"""


@dataclass
class ThemisDecision:
    """Complete decision output from THEMIS engine."""

    recommended_strategy: RecommendedStrategy
    explanation: str
    runway_metrics: RunwayMetrics
    month_by_month: List[Dict]  # Detailed monthly breakdown
    sensitivity_analysis: Dict  # "What if" scenarios


class ThemisDecisionEngine:
    """
    THEMIS Decision Engine

    Analyzes transition phase finances and recommends optimal strategy.
    """

    def __init__(self):
        self.months_until_pension = 0
        self.months_until_disability = 0
        self.months_until_job = 0
        self.high_interest_threshold = 12.0
        self.emergency_fund_target = 6
        self.minimum_emergency_fund = 2

    def analyze_situation(
        self,
        financial_position: FinancialPosition,
        expense_breakdown: ExpenseBreakdown,
        timing: TimingFactors,
        available_monthly_surplus: Optional[float] = None,
    ) -> THEMISRecommendation:
        """
        Main decision logic: analyze financial position and recommend strategy

        Args:
            financial_position: Current financial snapshot
            expense_breakdown: How expenses can be reduced
            timing: Key dates for income and job search
            available_monthly_surplus: Override calculated surplus (for testing)

        Returns:
            THEMISRecommendation with strategy and allocation
        """
        # Calculate key metrics
        monthly_gap = (
            available_monthly_surplus
            if available_monthly_surplus is not None
            else financial_position.monthly_income - expense_breakdown.get_total()
        )

        savings_runway = self._calculate_savings_runway(financial_position.current_savings, monthly_gap)

        cc_runway = self._calculate_cc_runway(
            financial_position.cc_limit - financial_position.cc_balance,
            monthly_gap,
        )

        # Make recommendation based on situation
        if monthly_gap >= 0:
            # Have surplus - decide how to allocate it
            recommendation = self._handle_surplus_situation(
                financial_position,
                expense_breakdown,
                savings_runway,
                cc_runway,
                timing,
            )
        else:
            # Have shortfall - recommend how to handle it
            recommendation = self._handle_shortfall_situation(
                financial_position,
                expense_breakdown,
                savings_runway,
                cc_runway,
                monthly_gap,
                timing,
            )

        return recommendation

    def analyze(
        self,
        # Income (monthly)
        current_paycheck: float = 0.0,
        pension_monthly: float = 0.0,
        sbp_cost: float = 0.0,
        va_monthly: Optional[float] = 0,
        spouse_income: Optional[float] = 0,
        other_income: Optional[float] = 0,
        # Expenses (monthly)
        cash_only_total: float = 0.0,
        cc_eligible_total: float = 0.0,
        # Assets & Debt
        current_savings: float = 0.0,
        current_cc_balance: float = 0.0,
        cc_limit: float = 0.0,
        # Timeline (months from now)
        months_until_pension: int = 1,
        months_until_disability: int = 2,
        months_until_job: int = 1,
        job_income_monthly: Optional[float] = None,
        # Uncertainty
        disability_rating_uncertainty: str = "medium",  # low, medium, high
        include_disability_income: bool = True,
    ) -> ThemisDecision:
        """
        Run THEMIS analysis and return decision.

        Args:
            current_paycheck: Current monthly take-home pay
            pension_monthly: Military pension (gross, before SBP)
            sbp_cost: SBP monthly deduction
            va_monthly: VA disability monthly (if eligible)
            spouse_income: Spouse monthly income
            other_income: Other monthly income

            cash_only_total: Monthly expenses that CANNOT go on CC (rent, utilities, etc)
            cc_eligible_total: Monthly expenses that CAN go on CC

            current_savings: Current liquid savings
            current_cc_balance: Current CC balance
            cc_limit: Credit card limit

            months_until_pension: When pension starts (default 1)
            months_until_disability: When disability payment arrives (default 2)
            months_until_job: When new job starts (default 1)
            job_income_monthly: Expected job income if secured

            disability_rating_uncertainty: How confident in disability rating
            include_disability_income: Whether to assume disability income
        """

        # Store timeline
        self.months_until_pension = months_until_pension
        self.months_until_disability = months_until_disability
        self.months_until_job = months_until_job

        # Calculate transition window length (until pension OR job starts, whichever is later)
        transition_months = max(months_until_pension, months_until_job)

        # Prepare Phase 1 income (before pension)
        phase1_income = current_paycheck
        if months_until_job > 0:
            phase1_income = current_paycheck  # Job might not be ready yet

        # Prepare Phase 2+ income (after pension starts)
        pension_after_sbp = pension_monthly - sbp_cost
        phase2_income = pension_after_sbp + spouse_income + other_income

        # Add VA if disability is expected
        if include_disability_income and va_monthly:
            phase2_income += va_monthly

        # Add job income if it's expected before/during transition
        if job_income_monthly and months_until_job <= transition_months:
            # Job income kicks in at that point
            pass  # Handle in month-by-month calc

        # Run month-by-month simulation
        month_by_month = self._simulate_months(
            phase1_income=phase1_income,
            phase2_income=phase2_income,
            job_income=job_income_monthly,
            cash_only_monthly=cash_only_total,
            cc_eligible_monthly=cc_eligible_total,
            starting_savings=current_savings,
            starting_cc_balance=current_cc_balance,
            cc_limit=cc_limit,
            transition_months=transition_months,
            months_until_pension=months_until_pension,
            months_until_job=months_until_job,
        )

        # Analyze runway
        runway_metrics = self._analyze_runway(
            month_by_month=month_by_month,
            cash_only_total=cash_only_total,
            cc_limit=cc_limit,
            disability_certainty=disability_rating_uncertainty,
        )

        # Determine recommendation
        strategy, explanation = self._recommend_strategy(
            runway_metrics=runway_metrics,
            cash_only_total=cash_only_total,
            cc_eligible_total=cc_eligible_total,
            current_savings=current_savings,
            current_cc_balance=current_cc_balance,
            phase2_income=phase2_income,
            phase1_income=phase1_income,
        )

        # Generate sensitivity analysis
        sensitivity = self._sensitivity_analysis(
            month_by_month=month_by_month,
            transition_months=transition_months,
        )

        return ThemisDecision(
            recommended_strategy=strategy,
            explanation=explanation,
            runway_metrics=runway_metrics,
            month_by_month=month_by_month,
            sensitivity_analysis=sensitivity,
        )

    def _simulate_months(
        self,
        phase1_income: float,
        phase2_income: float,
        job_income: Optional[float],
        cash_only_monthly: float,
        cc_eligible_monthly: float,
        starting_savings: float,
        starting_cc_balance: float,
        cc_limit: float,
        transition_months: int,
        months_until_pension: int,
        months_until_job: int,
    ) -> List[Dict]:
        """Simulate month-by-month cash and CC balance."""

        months = []
        current_savings = starting_savings
        current_cc = starting_cc_balance

        for month in range(1, transition_months + 3):  # Include 2 months after transition
            # Determine income for this month
            if month <= months_until_pension:
                income = phase1_income
            else:
                income = phase2_income

            # Add job income if started
            if job_income and month >= months_until_job:
                income += job_income

            # Apply expenses
            # Strategy: Use cash for cash-only, charge rest to CC
            cash_needed = cash_only_monthly
            cc_charged = cc_eligible_monthly

            # Can we cover cash needs?
            if current_savings >= cash_needed:
                current_savings -= cash_needed
                current_cc += cc_charged
            else:
                # Need to use CC for cash-only (emergency)
                shortfall = cash_needed - current_savings
                current_savings = 0
                current_cc += cc_charged + shortfall

            # Apply income
            current_savings += income

            # Check CC breach
            breached = current_cc > cc_limit

            months.append(
                {
                    "month": month,
                    "income": income,
                    "cash_only_expense": cash_only_monthly,
                    "cc_eligible_expense": cc_eligible_monthly,
                    "savings_balance": max(0, current_savings),
                    "cc_balance": current_cc,
                    "cc_breached": breached,
                    "total_liquid": current_savings + (cc_limit - current_cc),  # Available credit
                    "pension_active": month > months_until_pension,
                    "job_active": month >= months_until_job,
                }
            )

        return months

    def _analyze_runway(
        self,
        month_by_month: List[Dict],
        cash_only_total: float,
        cc_limit: float,
        disability_certainty: str,
    ) -> RunwayMetrics:
        """Calculate runway metrics from month-by-month data."""

        # Cash runway: how many months until savings depleted?
        cash_runway = 0
        for m in month_by_month:
            if m["savings_balance"] > 0:
                cash_runway = m["month"]
            else:
                break

        # CC runway: peak balance and when it occurs
        cc_balances = [m["cc_balance"] for m in month_by_month]
        cc_peak = max(cc_balances)
        cc_peak_month = cc_balances.index(cc_peak) + 1 if cc_balances else 0

        # Does CC breach limit?
        cc_breaches = any(m["cc_breached"] for m in month_by_month[: self.months_until_pension + 2])

        # CC recovery time (months after pension before paid off)
        cc_recovery = 0
        for m in month_by_month[self.months_until_pension :]:
            if m["cc_balance"] <= 0:
                cc_recovery = m["month"] - self.months_until_pension
                break

        # Determine confidence level
        if disability_certainty == "low":
            confidence = "Medium"
        elif disability_certainty == "high":
            confidence = "Low"  # More uncertainty
        else:
            confidence = "High"

        # Identify risks
        risks = []
        if cc_breaches:
            risks.append("[WARNING] CC will exceed limit during transition")
        if cash_runway < self.months_until_pension:
            risks.append(f"[WARNING] Cash depletes in month {cash_runway}, pension not until month {self.months_until_pension}")
        if cc_recovery > 12:
            risks.append(f"[WARNING] CC recovery takes {cc_recovery} months after pension")
        if not risks:
            risks.append("[OK] No major risks detected")

        return RunwayMetrics(
            cash_runway_months=cash_runway,
            cc_peak_balance=cc_peak,
            cc_peak_month=cc_peak_month,
            cc_breaches_limit=cc_breaches,
            cc_recovery_months=cc_recovery,
            confidence=confidence,
            key_risks=risks,
        )

    def _recommend_strategy(
        self,
        runway_metrics: RunwayMetrics,
        cash_only_total: float,
        cc_eligible_total: float,
        current_savings: float,
        current_cc_balance: float,
        phase2_income: float,
        phase1_income: float,
    ) -> tuple[RecommendedStrategy, str]:
        """Determine recommendation based on runway analysis."""

        # Decision logic
        if runway_metrics.cc_breaches_limit:
            # CC will max out - MUST focus on cash and CC payoff
            if current_cc_balance > phase2_income * 0.5:
                strategy = RecommendedStrategy.PAY_CC_FIRST
                explanation = (
                    f"[WARNING] Your credit card will exceed the ${phase2_income:,.0f} limit by month "
                    f"{runway_metrics.cc_peak_month}. You should prioritize paying down the current "
                    f"${current_cc_balance:,.0f} balance BEFORE transition. "
                    f"Once pension starts, redirect all available income to CC payoff before job income uncertainty hits."
                )
            else:
                strategy = RecommendedStrategy.HYBRID
                explanation = (
                    f"[RESET] Your CC peaks at ${runway_metrics.cc_peak_balance:,.0f} in month "
                    f"{runway_metrics.cc_peak_month}, approaching your limit. "
                    f"Recommended: Build ${'%.0f' % (cash_only_total * 2):,.0f} cash buffer WHILE "
                    f"paying ~${(phase2_income - cash_only_total) * 0.5:,.0f}/month to CC after pension starts."
                )
        elif runway_metrics.cash_runway_months < self.months_until_pension:
            # Cash won't last until pension - MUST build cash
            strategy = RecommendedStrategy.BUILD_CASH_ONLY
            # Format runway months for display, handling infinity
            runway_display = (
                "indefinitely"
                if runway_metrics.cash_runway_months == float("inf")
                else f"{int(runway_metrics.cash_runway_months)}"
            )
            explanation = (
                f"[HIGH] URGENT: Your ${current_savings:,.0f} savings lasts only {runway_display} months, "
                f"but pension doesn't start until month {self.months_until_pension}. "
                f"You MUST allocate all available income to building cash reserves immediately. "
                f"Target: ${cash_only_total * 3:,.0f} (3 months of cash-only expenses)."
            )
        else:
            # Safe runway - can consider hybrid approach
            strategy = RecommendedStrategy.HYBRID
            # Format runway months for display, handling infinity
            runway_display = (
                "indefinitely"
                if runway_metrics.cash_runway_months == float("inf")
                else f"{int(runway_metrics.cash_runway_months)}"
            )
            explanation = (
                f"[OK] Your cash position is solid: ${current_savings:,.0f} lasts {runway_display} months. "
                f"CC peaks at ${runway_metrics.cc_peak_balance:,.0f} with good headroom. "
                f"Recommended: Build to ${cash_only_total * 3:,.0f} in cash WHILE paying ${(phase2_income - cash_only_total) * 0.3:,.0f}/month "
                f"to CC. This balances emergency readiness with debt reduction."
            )

        return strategy, explanation

    def _sensitivity_analysis(
        self,
        month_by_month: List[Dict],
        transition_months: int,
    ) -> Dict:
        """Generate what-if scenarios."""

        # Best case: Job starts on time, pension early
        best_case_months = transition_months - 1

        # Worst case: Job delayed, disability uncertain
        worst_case_months = transition_months + 3

        return {
            "best_case": f"Job starts on time: Stable by month {best_case_months}",
            "worst_case": f"Job delayed 3 months: Tight until month {worst_case_months}",
            "pension_critical": self.months_until_pension,
            "disability_impact": "Could add ~$1,200-3,000/month at month 2",
        }

    def _handle_surplus_situation(
        self,
        position: FinancialPosition,
        expenses: ExpenseBreakdown,
        savings_runway: SavingsRunway,
        cc_runway: CreditCardRunway,
        timing: TimingFactors,
    ) -> THEMISRecommendation:
        """Handle case where monthly income > expenses (surplus available)"""

        monthly_surplus = position.monthly_income - expenses.get_total()

        # Determine if we're underfunded on emergency reserves
        emergency_fund_goal = expenses.required * self.emergency_fund_target
        emergency_fund_gap = max(0, emergency_fund_goal - position.current_savings)

        # Check if debt is high-interest problem
        high_interest_debt = sum(
            [position.cc_balance if position.cc_rate_percent > self.high_interest_threshold else 0]
        )

        # Recommend strategy based on what needs most attention
        if emergency_fund_gap > monthly_surplus * 6:  # Would take 6+ months to build emergency fund
            # Prioritize building emergency fund first
            recommendation = THEMISRecommendation(
                strategy="Prioritize Emergency Reserves",
                debt_paydown_percent=0.10,
                savings_percent=0.70,
                expense_reduction_percent=0.20,
                confidence=RecommendationLevel.HIGH,
                rationale=(
                    f"You have consistent surplus income (${monthly_surplus:,.0f}/month) but insufficient "
                    f"emergency reserves. You need ${emergency_fund_gap:,.0f} to reach {self.emergency_fund_target}-month "
                    f"safety net. Build this first before aggressive debt payoff."
                ),
                risk_factors=[
                    "High-interest CC debt will continue accruing interest",
                    "Job search delays would require cutting expenses",
                    "Unexpected costs could derail plan",
                ],
                quick_wins=[
                    f"Set up automatic savings: ${monthly_surplus * 0.70:,.0f}/month to emergency fund",
                    "Pause subscription services to find quick wins",
                    f"Target: reach ${position.current_savings + emergency_fund_gap:,.0f} in {emergency_fund_gap / (monthly_surplus * 0.70):.1f} months",
                ],
                monthly_impact=monthly_surplus * 0.70,  # Monthly savings impact
            )

        elif high_interest_debt > 5000:  # Significant high-interest debt
            # Balance emergency fund maintenance with debt payoff
            recommendation = THEMISRecommendation(
                strategy="Balanced: Maintain Safety + Attack Debt",
                debt_paydown_percent=0.40,
                savings_percent=0.40,
                expense_reduction_percent=0.20,
                confidence=RecommendationLevel.HIGH,
                rationale=(
                    f"You have good income stability (${monthly_surplus:,.0f}/month surplus) and reasonable "
                    f"emergency reserves (${position.current_savings:,.0f}). Significant high-interest debt "
                    f"(${high_interest_debt:,.0f}) at {position.cc_rate_percent:.1f}% is costing you money. "
                    f"Balance paying this down while maintaining safety reserves."
                ),
                risk_factors=[
                    f"Debt servicing costs ~${high_interest_debt * position.cc_rate_percent / 100 / 12:,.0f}/month in interest",
                    "Job search delays could stress savings",
                    "Resist temptation to accumulate more CC debt",
                ],
                quick_wins=[
                    f"Attack high-interest CC debt: ${monthly_surplus * 0.40:,.0f}/month",
                    f"Maintain/grow emergency fund: ${monthly_surplus * 0.40:,.0f}/month",
                    f"Cut ${monthly_surplus * 0.20:,.0f}/month from discretionary spending",
                ],
                monthly_impact=high_interest_debt * position.cc_rate_percent / 100 / 12,  # Interest saved
            )

        else:
            # Good situation - optimize overall financial health
            recommendation = THEMISRecommendation(
                strategy="Optimize Financial Health",
                debt_paydown_percent=0.30,
                savings_percent=0.50,
                expense_reduction_percent=0.20,
                confidence=RecommendationLevel.MODERATE,
                rationale=(
                    f"You have a stable surplus of ${monthly_surplus:,.0f}/month with adequate emergency "
                    f"reserves and minimal high-interest debt. Build additional reserves for job search "
                    f"uncertainty while maintaining responsible debt payoff."
                ),
                risk_factors=[
                    "Extended job search could deplete savings",
                    "No CC debt doesn't mean you should accumulate it",
                    "Lifestyle inflation is common in stable periods",
                ],
                quick_wins=[
                    "Build job-search buffer by saving aggressively",
                    "Continue minimum debt payments",
                    f"Target monthly savings: ${monthly_surplus * 0.50:,.0f}",
                ],
                monthly_impact=monthly_surplus * 0.50,
            )

        return recommendation

    def _handle_shortfall_situation(
        self,
        position: FinancialPosition,
        expenses: ExpenseBreakdown,
        savings_runway: SavingsRunway,
        cc_runway: CreditCardRunway,
        monthly_gap: float,
        timing: TimingFactors,
    ) -> THEMISRecommendation:
        """Handle case where expenses > income (shortfall needs covering)"""

        # monthly_gap is negative (e.g., -$2,000)
        shortfall = abs(monthly_gap)

        # Calculate expense reduction priorities: optional FIRST, then flexible
        reducible_optional = expenses.optional
        reducible_flexible = expenses.flexible
        reducible_total = reducible_optional + reducible_flexible

        # Assess available resources
        savings_months = position.current_savings / shortfall if shortfall > 0 else float("inf")
        cc_months = cc_runway.emergency_cushion_months
        total_runway = savings_months + cc_months

        # Determine critical factors
        is_savings_critical = savings_months < self.minimum_emergency_fund
        is_cc_critical = cc_runway.available_credit < shortfall
        can_reduce_expenses = reducible_total >= shortfall * 0.5

        # Make recommendation based on severity
        if is_savings_critical and is_cc_critical:
            # CRITICAL: Both savings and CC are exhausted
            recommendation = THEMISRecommendation(
                strategy="URGENT: Severe Expense Reduction Required",
                debt_paydown_percent=0.0,
                savings_percent=0.0,
                expense_reduction_percent=1.0,
                confidence=RecommendationLevel.CRITICAL,
                rationale=(
                    f"CRITICAL SITUATION: Monthly shortfall of ${shortfall:,.0f} cannot be sustained. "
                    f"Current savings (${position.current_savings:,.0f}) lasts {savings_months:.1f} months. "
                    f"CC emergency buffer is insufficient. You MUST reduce expenses immediately."
                ),
                risk_factors=[
                    "Savings will be exhausted in weeks to months",
                    "Limited credit available for emergency backup",
                    "Job search timeline becomes critical",
                    "Risk of not being able to cover essential expenses",
                ],
                quick_wins=[
                    f"STEP 1: Eliminate ALL optional spending (${reducible_optional:,.0f}/month) - hobbies, dining, gifts, subscriptions",
                    f"STEP 2: Then reduce flexible expenses to minimum (${reducible_flexible:,.0f}/month) - dining, entertainment, discretionary",
                    f"Target reduction: ${reducible_total:,.0f}/month from optional + flexible spending",
                    f"Current burn rate: {savings_months:.1f} months of savings remaining",
                    "Accelerate job search if not already urgent",
                ],
                monthly_impact=0,
            )

        elif can_reduce_expenses:
            # CAN FIX: Expenses can be reduced enough to cover shortfall
            recommendation = THEMISRecommendation(
                strategy="Expense Reduction + Savings Management",
                debt_paydown_percent=0.0,
                savings_percent=0.0,
                expense_reduction_percent=1.0,
                confidence=RecommendationLevel.HIGH,
                rationale=(
                    f"You have a monthly shortfall of ${shortfall:,.0f} that can be covered by "
                    f"stopping optional spending (${reducible_optional:,.0f}/month) and reducing flexible "
                    f"expenses (${reducible_flexible:,.0f}/month). This preserves savings and emergency credit."
                ),
                risk_factors=[
                    "Requires discipline during stressful period",
                    "Quality of life may be reduced",
                    "Unsustainable beyond 3-4 months if no income increase",
                ],
                quick_wins=[
                    f"STEP 1: Stop all optional spending (${reducible_optional:,.0f}/month) immediately",
                    f"STEP 2: Reduce flexible spending by ${min(reducible_flexible, shortfall - reducible_optional):,.0f}/month",
                    f"Preserve savings (currently {savings_months:.1f} months runway)",
                    "Keep CC as emergency backup",
                    f"Target: break-even in {self.minimum_emergency_fund} months with job",
                ],
                monthly_impact=reducible_total,
            )

        else:
            # DIFFICULT: Must rely on savings/CC and expense cuts
            combined_fix = reducible_total  # How much we can cut
            remaining_shortfall = shortfall - combined_fix  # Still need to cover

            recommendation = THEMISRecommendation(
                strategy="Mixed: Expense Cuts + Savings Drawdown",
                debt_paydown_percent=0.0,
                savings_percent=0.0,
                expense_reduction_percent=1.0,
                confidence=RecommendationLevel.HIGH,
                rationale=(
                    f"Monthly shortfall of ${shortfall:,.0f} requires cutting optional (${reducible_optional:,.0f}) "
                    f"and flexible (${reducible_flexible:,.0f}) spending. Remaining ${remaining_shortfall:,.0f} "
                    f"will come from savings and CC emergency reserves. "
                    f"You have {total_runway:.1f} months total runway (savings + CC emergency credit)."
                ),
                risk_factors=[
                    f"Savings runway: {savings_months:.1f} months at current burn",
                    "Depletes emergency reserves during uncertain period",
                    "CC will be your backup for actual emergencies",
                    "Job search delay would be problematic",
                ],
                quick_wins=[
                    f"Immediately cut ${combined_fix:,.0f} from discretionary spending",
                    "Make remaining cuts non-negotiable",
                    f"Savings runway: {total_runway:.1f} months",
                    f"Accelerate job search - need income within {total_runway:.0f} months",
                    "Preserve CC for true emergencies only",
                ],
                monthly_impact=0,  # Negative impact; trying to minimize damage
            )

        return recommendation

    def _calculate_savings_runway(self, current_savings: float, monthly_gap: float) -> SavingsRunway:
        """Calculate how long savings will last"""

        if monthly_gap >= 0:
            # Surplus - savings will grow indefinitely
            months = float("inf")
        else:
            # Shortfall - calculate burndown
            months = current_savings / abs(monthly_gap) if monthly_gap != 0 else float("inf")

        return SavingsRunway(
            total_savings=current_savings,
            monthly_burn=monthly_gap,
            months_available=months,
        )

    def _calculate_cc_runway(self, available_credit: float, monthly_gap: float) -> CreditCardRunway:
        """Calculate how long CC emergency credit can help"""

        cc_limit = available_credit  # Already a limit, not a balance
        cc_percent = (available_credit / cc_limit * 100) if cc_limit > 0 else 0

        if monthly_gap >= 0:
            months = float("inf")  # No need to draw on CC
        else:
            months = available_credit / abs(monthly_gap) if monthly_gap != 0 else float("inf")

        return CreditCardRunway(
            available_credit=available_credit,
            available_percent=cc_percent,
            emergency_cushion_months=months,
        )

    def calculate_debt_interest_cost(
        self,
        cc_balance: float,
        cc_rate: float,
        other_debt: float,
        other_rate: float,
        payoff_months: int,
    ) -> float:
        """Estimate total interest paid over time period"""

        cc_interest = cc_balance * (cc_rate / 100) * (payoff_months / 12)
        other_interest = other_debt * (other_rate / 100) * (payoff_months / 12)

        return cc_interest + other_interest

    def calculate_payoff_timeline(
        self,
        total_debt: float,
        monthly_payoff: float,
        average_interest_rate: float,
    ) -> Dict[str, float]:
        """Calculate debt payoff timeline with interest"""

        if monthly_payoff <= 0:
            return {
                "months": float("inf"),
                "interest_paid": total_debt * (average_interest_rate / 100) * 5,  # Estimate 5 years
                "total_cost": total_debt + (total_debt * (average_interest_rate / 100) * 5),
            }

        # Simple calculation (not accounting for monthly interest accrual for simplicity)
        months = total_debt / monthly_payoff
        monthly_interest = total_debt * (average_interest_rate / 100) / 12
        interest_paid = monthly_interest * months

        return {
            "months": months,
            "interest_paid": interest_paid,
            "total_cost": total_debt + interest_paid,
        }
