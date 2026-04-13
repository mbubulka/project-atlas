"""
Coaching Engine: Implements Socratic method for Step 6 Summary.

This module transforms the final summary from a report into an interactive
coaching session that helps users think critically about their decisions.

Philosophy:
- Show all work (chain-of-thought reasoning)
- Identify assumptions explicitly
- Frame assumptions as risks/opportunities
- Ask thought-provoking questions without judgment
- Guide users to their own conclusions
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Assumption:
    """Represents a single assumption in the financial plan."""

    category: str  # "Income", "Expenses", "Debt", "Timing", "Market"
    description: str
    value: Any
    confidence: str  # "High", "Medium", "Low"
    impact: str  # "Critical", "Major", "Minor"
    risk_if_wrong: str

    def display(self):
        """Return formatted assumption for display."""
        return {
            "Category": self.category,
            "Assumption": self.description,
            "Value": self.value,
            "Confidence": self.confidence,
            "Impact": self.impact,
            "Risk if wrong": self.risk_if_wrong,
        }


@dataclass
class CoachingQuestion:
    """A thought-provoking question to guide user thinking."""

    category: str  # "Assumptions", "Risks", "Opportunities", "Timing", "Decisions"
    question: str
    context: str = ""
    follow_up: str = ""


class CoachingEngine:
    """
    Transforms financial summaries into coaching conversations.

    Implements Socratic method:
    1. Show the calculation (chain-of-thought)
    2. Identify all assumptions
    3. Frame assumptions as risks/opportunities
    4. Ask probing questions
    5. Let user reach their own conclusions
    """

    def __init__(self, profile):
        """Initialize coaching engine with user profile."""
        self.profile = profile
        self.assumptions: List[Assumption] = []
        self.coaching_questions: List[CoachingQuestion] = []
        self._build_assumptions()
        self._build_coaching_questions()

    def _build_assumptions(self):
        """Identify and categorize all assumptions in the financial plan."""

        # ===== INCOME ASSUMPTIONS =====
        self.assumptions.append(
            Assumption(
                category="Income",
                description="Military pension remains constant",
                value=f"${self.profile.current_annual_retirement_pay:,.0f}/yr",
                confidence="High" if self.profile.years_of_service >= 20 else "Medium",
                impact="Critical",
                risk_if_wrong="Lower retirement income forces expense cuts or delays other goals",
            )
        )

        # VA Disability assumption
        if self.profile.current_va_disability_rating > 0:
            self.assumptions.append(
                Assumption(
                    category="Income",
                    description=(f"VA rating remains at " f"{self.profile.current_va_disability_rating}%"),
                    value=f"${self.profile.current_va_annual_benefit:,.0f}/yr",
                    confidence="Medium",
                    impact="Major",
                    risk_if_wrong=("Rating changes could increase/decrease benefit " "significantly"),
                )
            )

        # Spouse income assumption
        spouse_income = getattr(self.profile, "spouse_annual_income", 0.0)
        if spouse_income > 0:
            self.assumptions.append(
                Assumption(
                    category="Income",
                    description="Spouse maintains current employment",
                    value=f"${spouse_income:,.0f}/yr",
                    confidence="Medium",
                    impact="Major",
                    risk_if_wrong=("Loss of spouse income creates immediate " "financial stress"),
                )
            )

        # New job assumption
        annual_salary = self.profile.estimated_annual_salary if self.profile.estimated_annual_salary > 0 else 0
        if annual_salary > 0:
            spouse_income = getattr(self.profile, "spouse_annual_income", 0.0)
            self.assumptions.append(
                Assumption(
                    category="Income",
                    description="New job starts as planned",
                    value=f"${annual_salary:,.0f}/yr",
                    confidence=("Low" if self.profile.job_search_timeline_months < 0 else "Medium"),
                    impact=("Critical" if annual_salary > spouse_income else "Major"),
                    risk_if_wrong=("Job delayed/lost creates cash flow crisis during " "transition"),
                )
            )

        # ===== EXPENSE ASSUMPTIONS =====
        total_expenses = (
            self.profile.monthly_expenses_mandatory
            + self.profile.monthly_expenses_negotiable
            + self.profile.monthly_expenses_optional
        )

        self.assumptions.append(
            Assumption(
                category="Expenses",
                description="Monthly expenses remain stable post-separation",
                value=f"${total_expenses:,.0f}/mo",
                confidence="Low",
                impact="Critical",
                risk_if_wrong=("Higher expenses reduce debt payoff and savings " "accumulation"),
            )
        )

        if self.profile.monthly_expenses_optional > 0:
            self.assumptions.append(
                Assumption(
                    category="Expenses",
                    description=("Optional/discretionary spending stays at " "current level"),
                    value=f"${self.profile.monthly_expenses_optional:,.0f}/mo",
                    confidence="Low",
                    impact="Minor",
                    risk_if_wrong=("This is your most flexible category and likely " "to increase during stress"),
                )
            )

        # ===== DEBT ASSUMPTIONS =====
        total_debt = self.profile.current_debt + (self.profile.cc_balance if hasattr(self.profile, "cc_balance") else 0)

        if total_debt > 0:
            self.assumptions.append(
                Assumption(
                    category="Debt",
                    description="Interest rates remain constant on existing debt",
                    value="Current rates",
                    confidence="Low",
                    impact="Major",
                    risk_if_wrong=("Rate increases during economic stress compound " "repayment burden"),
                )
            )

        # ===== TIMING ASSUMPTIONS =====
        if self.profile.separation_date:
            try:
                import time

                months_until = (self.profile.separation_date.timestamp() - time.time()) / (86400 * 30)
                sep_value = f"{months_until:.0f} months from now"
            except Exception:
                sep_value = "Scheduled date"
        else:
            sep_value = "Not yet scheduled"

        self.assumptions.append(
            Assumption(
                category="Timing",
                description="Separation occurs as scheduled",
                value=sep_value,
                confidence="High",
                impact="Critical",
                risk_if_wrong=("Delay affects benefit start dates and " "transition planning"),
            )
        )

        # ===== MARKET/ECONOMIC ASSUMPTIONS =====
        self.assumptions.append(
            Assumption(
                category="Market",
                description="No major economic recession during transition",
                value="Current economic conditions",
                confidence="Medium",
                impact="Major",
                risk_if_wrong=("Recession reduces job prospects and increases " "healthcare costs"),
            )
        )

    def _build_coaching_questions(self):
        """Generate thought-provoking questions based on profile."""

        # ===== QUESTIONS ABOUT ASSUMPTIONS =====
        spouse_income = getattr(self.profile, "spouse_annual_income", 0.0)
        if spouse_income > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Assumptions",
                    question=(f"How stable is your spouse's ${spouse_income:,.0f}/yr" " income?"),
                    context=("You've budgeted heavily on dual income. " "What's your backup plan if that changes?"),
                    follow_up=(
                        "What would happen to your monthly surplus if "
                        "they took a break (sabbatical, illness, "
                        "career change)?"
                    ),
                )
            )

        # Questions about new job
        annual_salary = self.profile.estimated_annual_salary if self.profile.estimated_annual_salary > 0 else 0
        if annual_salary > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Assumptions",
                    question=(
                        f"How confident are you that the " f"${annual_salary / 1000:.0f}K job will " "materialize?"
                    ),
                    context=(
                        f"Your plan relies heavily on this "
                        f"{self.profile.job_search_timeline_months}-month "
                        "timeline."
                    ),
                    follow_up=(
                        "What's your survival plan if it takes 6+ months "
                        "instead? Can you bridge the gap with just "
                        "pension and spouse income?"
                    ),
                )
            )

        # Questions about VA rating
        if self.profile.current_va_disability_rating > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Assumptions",
                    question=(
                        f"Have you considered appealing your VA rating "
                        f"({self.profile.current_va_disability_rating}%)?"
                    ),
                    context=(
                        "The VA often adjusts ratings after separation. " "Even a 10% increase would change your plan."
                    ),
                    follow_up=(
                        "Have you documented all your service-connected "
                        "conditions? Could new ones (hearing, sleep, "
                        "mental health) qualify?"
                    ),
                )
            )

        # ===== QUESTIONS ABOUT RISKS =====
        total_debt = self.profile.current_debt + (getattr(self.profile, "cc_balance", 0.0))
        if total_debt > self.profile.current_savings:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Risks",
                    question=(
                        f"You have ${total_debt:,.0f} debt but only "
                        f"${self.profile.current_savings:,.0f} liquid "
                        "savings."
                    ),
                    context=("An emergency (job loss, medical) would " "immediately trigger high-interest debt."),
                    follow_up=(
                        "What's your absolute minimum savings floor "
                        "before you're comfortable paying down debt "
                        "aggressively?"
                    ),
                )
            )

        # Expense cushion question
        monthly_surplus = self._calculate_monthly_surplus()
        if monthly_surplus < 1000:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Risks",
                    question=f"Your monthly surplus is only ${monthly_surplus:,.0f}.",
                    context=("That's tight. One unexpected expense could " "derail your plan."),
                    follow_up=(
                        "Which expense category has the most flexibility? "
                        "Could you trim mandatory expenses if needed?"
                    ),
                )
            )

        # ===== QUESTIONS ABOUT OPPORTUNITIES =====
        if self.profile.current_savings > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Opportunities",
                    question=("Have you maximized tax-advantaged accounts " "(Roth IRA, HSA)?"),
                    context=("You have taxable income now. These accounts could " "reduce taxes AND grow wealth."),
                    follow_up=(
                        "How much could you contribute annually? " "Tax savings might fund your debt payoff faster."
                    ),
                )
            )

        if getattr(self.profile, "elect_sbp", False):
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Opportunities",
                    question=("You've elected SBP. Have you modeled the " "break-even point?"),
                    context=(
                        "SBP costs ~$245/mo but provides survivor "
                        "protection. Is this the right choice for your "
                        "family?"
                    ),
                    follow_up=("What happens at age 75? 85? When does survivor " "income become the better deal?"),
                )
            )

        # ===== QUESTIONS ABOUT TIMING =====
        if self.profile.job_search_timeline_months > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Timing",
                    question=(
                        f"You're targeting a job "
                        f"{self.profile.job_search_timeline_months} months "
                        "after separation. Why that timeline?"
                    ),
                    context=(
                        "Earlier transitions mean less financial bridge "
                        "needed. Later transitions reduce career "
                        "disruption."
                    ),
                    follow_up=(
                        "Would starting earlier (landing job BEFORE "
                        "separation) change your financial picture "
                        "dramatically?"
                    ),
                )
            )

        # ===== QUESTIONS ABOUT DECISIONS =====
        total_debt = self.profile.current_debt
        if total_debt > 0:
            self.coaching_questions.append(
                CoachingQuestion(
                    category="Decisions",
                    question=("Are you rushing to pay off debt, or building a " "safety net first?"),
                    context=("These are competing goals. The 'right' answer " "depends on your risk tolerance."),
                    follow_up=(
                        "If a job falls through, would you regret paying "
                        "off debt instead of saving 6 months of "
                        "expenses?"
                    ),
                )
            )

        self.coaching_questions.append(
            CoachingQuestion(
                category="Decisions",
                question=("What's the ONE financial thing that keeps you up " "at night about this transition?"),
                context=("That's probably where your real risk is—not in " "the numbers, but in your comfort level."),
                follow_up=("What information or changes would help you sleep " "better?"),
            )
        )

    def _calculate_monthly_surplus(self) -> float:
        """Calculate phase 2 monthly surplus.
        
        Properly handles VA disability offset for ratings below 50%:
        - 50%+: CRDP - get both pension (taxed) + VA disability (tax-free)
        - 20-49%: Offset - VA replaces pension, but VA is tax-free (different take-home)
        - <20%: Pension only - VA doesn't offset at this level
        """
        from src.model_layer.va_offset_calculator import calculate_va_offset_income
        
        # Get base pension amounts
        pension_monthly_pretax = self.profile.current_annual_retirement_pay / 12
        sbp_cost = getattr(self.profile, "sbp_monthly_cost", 0)
        pension_pretax_deductions = getattr(self.profile, "pension_pretax_expense", 0)
        va_rating = self.profile.current_va_disability_rating
        va_benefit_annual = getattr(self.profile, "current_va_annual_benefit", 0.0)
        va_benefit_monthly = va_benefit_annual / 12 if va_benefit_annual > 0 else 0
        
        # Use corrected VA offset calculation
        va_calc = calculate_va_offset_income(
            pension_monthly_pretax=pension_monthly_pretax,
            sbp_monthly_cost=sbp_cost,
            pension_pretax_deductions=pension_pretax_deductions,
            va_disability_rating=va_rating,
            va_monthly_benefit=va_benefit_monthly,
            estimated_tax_rate=0.22,  # Default federal tax rate
        )
        
        # Military income from corrected VA offset logic
        military_income = va_calc["total_monthly_income"]
        
        # Other income sources
        spouse_monthly = getattr(self.profile, "spouse_annual_income", 0.0) / 12
        other_monthly = getattr(self.profile, "other_annual_income", 0.0) / 12
        
        total_income = military_income + spouse_monthly + other_monthly

        total_expenses = (
            self.profile.monthly_expenses_mandatory
            + self.profile.monthly_expenses_negotiable
            + self.profile.monthly_expenses_optional
        )

        return total_income - total_expenses

    def get_assumptions_table(self) -> List[Dict]:
        """Return formatted assumptions for display."""
        return [a.display() for a in self.assumptions]

    def get_coaching_questions(self, category: str = None) -> List[CoachingQuestion]:
        """Get coaching questions, optionally filtered by category."""
        if category:
            return [q for q in self.coaching_questions if q.category == category]
        return self.coaching_questions

    def get_critical_assumptions(self) -> List[Assumption]:
        """Return only the assumptions that could break the plan."""
        return [a for a in self.assumptions if a.impact == "Critical"]

    def generate_coaching_prompt(self) -> str:
        """Generate an opening coaching prompt based on the situation."""
        surplus = self._calculate_monthly_surplus()

        if surplus < 0:
            return (
                "[DEFICIT] Your plan shows a monthly deficit. "
                "Before we talk about your transition, we need to solve "
                "this. What expenses could you reduce? Or which income "
                "assumption needs revisiting?"
            )

        if surplus < 500:
            return (
                "[WARNING] Tight margins. Your surplus is real, but small. "
                "Let's talk about what could go wrong and how you'd adapt. "
                "What's your biggest concern about this transition?"
            )

        if self.profile.estimated_annual_salary > 0 and self.profile.job_search_timeline_months > 3:
            return (
                "[INFO] Your plan works IF the new job materializes. "
                "That's the critical assumption. How confident are you? "
                "And what's your backup if it takes longer than expected?"
            )

        return (
            "[OK] Your numbers work. Now let's make sure your "
            "assumptions are solid. Which of these concerns you most: "
            "your income, expenses, or debt?"
        )

    def generate_next_steps(self) -> List[str]:
        """Suggest investigation areas based on profile."""
        steps = []

        # Income investigation
        spouse_income = getattr(self.profile, "spouse_annual_income", 0.0)
        if spouse_income > 0:
            steps.append(
                "[ACTION] Confirm spouse income stability - Talk to HR " "about any restructuring or risk factors"
            )

        if self.profile.estimated_annual_salary > 0:
            steps.append(
                "[ACTION] Validate job timeline - Have you started " "applying? Do you have interviews lined up?"
            )

        # Expense investigation
        total_exp = (
            self.profile.monthly_expenses_mandatory
            + self.profile.monthly_expenses_negotiable
            + self.profile.monthly_expenses_optional
        )
        if self.profile.monthly_expenses_optional > total_exp * 0.15:
            steps.append(
                "[ACTION] Review discretionary spending - Optional " "expenses are 15%+ of budget. Any cuts available?"
            )

        # Debt investigation
        if self.profile.current_debt > 0:
            steps.append(
                "[ACTION] Consolidate/refinance check - Can you lower "
                "rates before separation? Credit likely better now."
            )

        # Benefits investigation
        if self.profile.current_va_disability_rating < 50:
            steps.append(
                "[ACTION] VA rating appeal - Has anything changed "
                "(new conditions)? Could you qualify for higher rating?"
            )

        # Savings investigation
        if self.profile.current_savings < 20000:
            steps.append(
                "[ACTION] Build emergency fund first - Before "
                "aggressive debt payoff, ensure 3-6 months of "
                "expenses saved"
            )

        return steps
