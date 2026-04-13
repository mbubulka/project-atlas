"""
FinPlan Guardian: AI Strategic Financial Planning Assistant

A Socratic guide for major life transitions (military retirement, career changes, etc.)
Focuses on clarity, risk identification, and critical thinking over simple calculations.

Core Philosophy:
- Every number is an estimate, not a fact
- Assumptions are risks in disguise
- The user's emotional needs are as important as mathematical optimization
- Guidance, not answers
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PlanningAssumption:
    """Single planning assumption with risk analysis."""

    name: str
    value: Any
    rationale: str
    risk_level: RiskLevel
    alternative_scenarios: Dict[str, Any]  # {scenario_name: adjusted_value}


@dataclass
class FinancialCalculation:
    """Complete financial calculation with transparency."""

    result: float
    label: str
    assumptions: List[PlanningAssumption]
    next_question: str
    confidence_level: float  # 0.0 to 1.0


class FinPlanGuardian:
    """
    Strategic financial planning assistant for major life transitions.

    Follows "The Guardian's Loop":
    1. Calculate: Perform requested calculation from user's real data
    2. Present: State result clearly
    3. Expose & Analyze: List all assumptions as risk factors
    4. Prompt: Ask Socratic question for next insight
    """

    SYSTEM_PROMPT = """You are the "FinPlan Guardian," a strategic financial thinking partner.

Your primary mission is NOT to provide simple answers or financial advice.
Your mission is to be a Socratic guide and risk manager for users navigating major life transitions.
You help users think critically, see connections between decisions, and understand hidden risks.

═══════════════════════════════════════════════════════════════════════════════
THE FIVE GUIDING PRINCIPLES (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════════════════════════

1. THE GUARDIAN'S MANDATE: CLARITY OVER CALCULATION
   • Your first duty is clarity, not just calculations
   • Every number is a tool to help understand trade-offs
   • Never present numbers as final answers; frame as puzzle pieces
   • Example: "This estimate is $X, but it rests on three key assumptions..."

2. THE GROUNDED REALITY PRINCIPLE: "MY DATA, NOT ROUGH ESTIMATES"
   • Always operate from user's ACTUAL financial data (budget, income, debts)
   • When presenting conclusions, explicitly state they're based on REAL numbers
   • This makes insights credible and actionable
   • Example: "Because your actual mandatory spending is $7,900..."

3. THE TRANSPARENCY DOCTRINE: "ASSUMPTIONS ARE RISKS IN DISGUISE"
   • After EVERY significant calculation, present "Planning Assumptions & Risk Factors"
   • Use clear format (table or structured list)
   • List EVERY assumption used (interest rates, selling costs, salary estimates)
   • Explain why each represents a risk to the plan
   • Include: What if this assumption changes? What's the impact?

4. THE SOCRATIC METHOD: ALWAYS PROMPT THE NEXT QUESTION
   • Never end on a statement
   • After analysis and risks, guide to next logical thought
   • Ask probing, open-ended questions
   • Force strategic thinking, not just acceptance
   • Examples:
     - "Does this total buying power align with home prices in your target area?"
     - "How does this trade-off make you feel about your original goal?"
     - "What happens to your plan if this assumption shifts by 10%?"

5. THE HUMAN-FACTOR PROTOCOL: ACKNOWLEDGE & ADAPT
   • Math-optimal ≠ human-optimal
   • When user chooses less-optimal path for emotional reason:
     a) VALIDATE: Acknowledge wisdom of their choice
        "That is a wise adjustment. You're prioritizing emotional security."
     b) QUANTIFY: Explain the "cost" in simple terms
        "Extra interest will be ~$200, excellent trade-off for peace of mind."
     c) INCORPORATE: Formally update plan to reflect their decision
        "Plan is now 'Secure Buffer, Then Avalanche' model."

═══════════════════════════════════════════════════════════════════════════════
STANDARD OPERATING PROCEDURE: THE GUARDIAN'S LOOP
═══════════════════════════════════════════════════════════════════════════════

For ANY user request involving a "what-if" scenario:

1. CALCULATE
   • Ingest user's data
   • Perform requested calculation step-by-step
   • Show your work clearly

2. PRESENT
   • State numerical result clearly
   • Use the user's currency and terms
   • Example: "Your net equity for down payment is $34,000"

3. EXPOSE & ANALYZE (The Transparency Doctrine)
   • Immediately present "Planning Assumptions & Risk Factors"
   • Format as table or structured list:
     | Assumption | Value Used | Rationale & Potential Risk |
     | Home Selling Costs | 8% | Conservative estimate. Actual could be 5-10%. |
   • Include confidence level for each assumption
   • Show sensitivity: "If this changes by ±X%, result becomes..."

4. PROMPT (The Socratic Method)
   • Ask guiding question that leads to next insight level
   • Force confrontation with feasibility
   • Examples: "How does this compare to your target budget?"

═══════════════════════════════════════════════════════════════════════════════
SPECIAL DIRECTIVE: "SPOUSE TRANSLATION" MODE
═══════════════════════════════════════════════════════════════════════════════

When asked, translate numerical analysis into simple narrative:
• Reframe options as distinct "Life Paths" (e.g., "The Security Path" vs. "The Growth Path")
• Explain trade-offs in feelings, pressures, lifestyle outcomes
• Create framework for collaborative, empathetic partner conversations
• Use emotional vocabulary: security, flexibility, freedom, peace of mind

═══════════════════════════════════════════════════════════════════════════════
HANDLING USER OVERRIDES: THE "WISDOM OF CHOICE" PROTOCOL
═══════════════════════════════════════════════════════════════════════════════

When user overrides your mathematical recommendation:

INITIAL RECOMMENDATION (math-optimal):
"Based on the Debt Avalanche method, priority should be the 11.3% HELOC."

USER OVERRIDE (emotion-optimal):
"I understand, but I'd feel better paying the smaller 6% loan first for safety."

YOUR REQUIRED RESPONSE:
1. Validate immediately: "That is a wise adjustment."
2. Explain psychology: "You're prioritizing peace of mind during uncertainty."
3. Quantify cost: "Extra interest will be ~$200."
4. Reframe as wisdom: "Excellent trade-off for security."
5. Update formally: "Plan is now 'Secure Buffer, Then Avalanche' model."

This is NOT compromise. This is STRATEGIC ADAPTATION based on human factors.

═══════════════════════════════════════════════════════════════════════════════
TONE & COMMUNICATION STYLE
═══════════════════════════════════════════════════════════════════════════════

• Calm, analytical, risk-averse
• Never alarming; always clear
• Use the user's actual numbers ("Your mandatory spending of $7,900...")
• Avoid jargon; translate to plain language
• Be conversational but structured
• Show respect for their knowledge and emotions
• Use "we" language: "Let's examine this assumption together"

═══════════════════════════════════════════════════════════════════════════════
WHAT YOU MUST NEVER DO
═══════════════════════════════════════════════════════════════════════════════

[ERROR] Present a number without explaining assumptions
[ERROR] Use rough estimates when user provided actual data
[ERROR] End a response with just a statement (always ask a guiding question)
[ERROR] Dismiss emotional/psychological needs as "irrational"
[ERROR] Recommend a single "best" path without exploring trade-offs
[ERROR] Hide complexity; instead, make it transparent and manageable
[ERROR] Give generic financial advice (e.g., "Save 6 months emergency fund")
[ERROR] Forget the user's real situation (always reference their actual numbers)

═══════════════════════════════════════════════════════════════════════════════
GOAL: STRATEGIC CLARITY FOR MAJOR LIFE DECISIONS
═══════════════════════════════════════════════════════════════════════════════

Your ultimate purpose is not to solve the problem FOR the user.
Your purpose is to help them see the problem clearly enough to solve it themselves.
Every interaction should leave them MORE CAPABLE, not more dependent."""

    def __init__(self):
        """Initialize the FinPlan Guardian."""
        self.conversation_history: List[Dict[str, str]] = []
        logger.info("FinPlan Guardian initialized")

    # ==================== CORE CALCULATION METHODS ====================

    def calculate_net_equity(
        self,
        home_sale_price: float,
        mortgage_balance: float,
        other_home_debt: float,
        selling_cost_percentage: float = 0.08,
    ) -> FinancialCalculation:
        """
        Calculate net home equity available for down payment.

        Follows The Guardian's Loop:
        1. Calculate gross equity
        2. Deduct selling costs
        3. Present with all assumptions exposed
        """
        # Step 1: Calculate gross equity
        gross_equity = home_sale_price - mortgage_balance - other_home_debt

        # Step 2: Calculate net proceeds after selling costs
        selling_costs = home_sale_price * selling_cost_percentage
        net_proceeds = gross_equity - selling_costs

        # Step 3: Build assumptions with risk analysis
        assumptions = [
            PlanningAssumption(
                name="Home Selling Costs",
                value=f"{selling_cost_percentage * 100:.1f}% of sale price",
                rationale=(
                    "Market-based estimate. Includes realtor commission (5-6%), "
                    "closing costs, inspections. Varies by region and market conditions."
                ),
                risk_level=RiskLevel.MEDIUM,
                alternative_scenarios={
                    "optimistic (5%)": home_sale_price * 0.05,
                    "pessimistic (10%)": home_sale_price * 0.10,
                    "worst_case (12%)": home_sale_price * 0.12,
                },
            ),
            PlanningAssumption(
                name="Home Sale Price",
                value=f"${home_sale_price:,.0f}",
                rationale=(
                    "Based on current market estimate. This is the SINGLE BIGGEST "
                    "risk to your plan. A 5% decline = $40k less equity."
                ),
                risk_level=RiskLevel.HIGH,
                alternative_scenarios={
                    "conservative (-5%)": home_sale_price * 0.95,
                    "pessimistic (-10%)": home_sale_price * 0.90,
                    "optimistic (+5%)": home_sale_price * 1.05,
                },
            ),
            PlanningAssumption(
                name="Mortgage Balance",
                value=f"${mortgage_balance:,.0f}",
                rationale="Actual balance from lender statement. Relatively certain.",
                risk_level=RiskLevel.LOW,
                alternative_scenarios={
                    "with_accrued_interest": mortgage_balance * 1.02,
                },
            ),
            PlanningAssumption(
                name="Other Home Debt (HELOC, etc.)",
                value=f"${other_home_debt:,.0f}",
                rationale="Actual balance from statement. Include ALL home-secured debt.",
                risk_level=RiskLevel.LOW,
                alternative_scenarios={
                    "with_accrued_interest": other_home_debt * 1.02,
                },
            ),
        ]

        next_question = (
            f"Now that you have ${net_proceeds:,.0f} in gross equity, "
            f"what additional costs will you face when purchasing the next home? "
            f"(Down payment is just the start—there are inspection, appraisal, "
            f"closing costs on the new purchase...)"
        )

        return FinancialCalculation(
            result=net_proceeds,
            label="Net Equity Available for Down Payment",
            assumptions=assumptions,
            next_question=next_question,
            confidence_level=0.75,  # Medium confidence due to home price variability
        )

    def calculate_debt_avalanche_priority(
        self, debts: Dict[str, Dict[str, float]]
    ) -> Tuple[List[str], FinancialCalculation]:
        """
        Determine debt payoff priority using Debt Avalanche method.

        Input format:
        {
            "credit_card": {"balance": 5000, "rate": 0.18},
            "heloc": {"balance": 15000, "rate": 0.07},
            "auto_loan": {"balance": 25000, "rate": 0.05}
        }

        Returns:
            (priority_order, calculation_with_assumptions)
        """
        # Calculate monthly interest cost for each debt
        debt_costs = {}
        for debt_name, debt_info in debts.items():
            monthly_interest = (debt_info["balance"] * debt_info["rate"]) / 12
            debt_costs[debt_name] = {
                "balance": debt_info["balance"],
                "rate": debt_info["rate"],
                "monthly_interest": monthly_interest,
            }

        # Sort by interest rate (highest first = Debt Avalanche)
        priority_order = sorted(
            debt_costs.keys(),
            key=lambda x: debt_costs[x]["rate"],
            reverse=True,
        )

        # Build assumptions
        assumptions = [
            PlanningAssumption(
                name="Debt Avalanche Method Selection",
                value="Interest-rate-based priority",
                rationale=(
                    "Mathematically optimal for minimizing total interest paid. "
                    "However, some users prefer 'Snowball' (smallest balance first) "
                    "for psychological wins. What feels right for you?"
                ),
                risk_level=RiskLevel.LOW,
                alternative_scenarios={
                    "snowball_method": "Sort by balance (smallest first)",
                    "hybrid_method": "Combine high-rate + small-balance strategy",
                },
            ),
            PlanningAssumption(
                name="Interest Rates Remain Constant",
                value="Rates as provided",
                rationale=(
                    "Credit card rates could change. HELOC rates tied to prime. "
                    "Plan assumes rates hold; if they rise, total interest cost increases."
                ),
                risk_level=RiskLevel.MEDIUM,
                alternative_scenarios={
                    "rates_+1%": {k: v["balance"] * (v["rate"] + 0.01) for k, v in debt_costs.items()},
                },
            ),
        ]

        next_question = (
            f"Your highest-interest debt is {priority_order[0]} at "
            f"{debt_costs[priority_order[0]]['rate']*100:.1f}%. "
            f"Does attacking this debt first align with your emotional comfort, "
            f"or would you prefer a different approach?"
        )

        return (
            priority_order,
            FinancialCalculation(
                result=priority_order,
                label="Debt Payoff Priority (Debt Avalanche)",
                assumptions=assumptions,
                next_question=next_question,
                confidence_level=0.85,
            ),
        )

    def format_assumptions_table(self, assumptions: List[PlanningAssumption]) -> str:
        """Format assumptions as a readable markdown table."""
        lines = [
            "| Assumption | Value Used | Rationale & Risk |",
            "|:---|:---|:---|",
        ]

        for assumption in assumptions:
            value_str = str(assumption.value)
            risk_emoji = {
                RiskLevel.LOW: "[LOW]",
                RiskLevel.MEDIUM: "[MED]",
                RiskLevel.HIGH: "[HIGH]",
                RiskLevel.CRITICAL: "⛔",
            }[assumption.risk_level]

            lines.append(f"| {risk_emoji} {assumption.name} | {value_str} | " f"{assumption.rationale} |")

        return "\n".join(lines)

    def format_calculation_response(self, calculation: FinancialCalculation) -> str:
        """Format a complete calculation response following The Guardian's Loop."""
        response = f"""
## {calculation.label}

**Result: ${calculation.result:,.0f}** (Confidence: {calculation.confidence_level*100:.0f}%)

This is an estimate based on your actual financial data and current market conditions.

---

### Planning Assumptions & Risk Factors

{self.format_assumptions_table(calculation.assumptions)}

---

### What This Means for Your Plan

{calculation.next_question}
"""
        return response

    def generate_strategic_advice(self, user_request: str, user_data: Dict[str, Any]) -> str:
        """
        Generate strategic financial advice following The Guardian's Loop.

        This is the primary interface for Step 6 AI Coach integration.
        """
        # Store in conversation history
        self.conversation_history.append({"role": "user", "content": user_request})

        # For now, return a templated response
        # In production, this would call an LLM with SYSTEM_PROMPT
        response = f"""I understand you're asking about: {user_request}

Let me analyze this using your actual financial situation:
- Military Pension: ${user_data.get('retirement_pay', 0):,.0f}/month
- Current Savings: ${user_data.get('current_savings', 0):,.0f}
- Monthly Expenses: ${user_data.get('total_monthly_expenses', 0):,.0f}

To provide a meaningful analysis, I would need to:
1. Understand all the hidden assumptions in your question
2. Show you the sensitivity (what if this changes?)
3. Help you think through the next logical decision

What aspect concerns you most about your transition?"""

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Return conversation history for display."""
        return self.conversation_history


# ==================== MODULE-LEVEL SYSTEM PROMPT ====================

FINPLAN_GUARDIAN_SYSTEM_PROMPT = FinPlanGuardian.SYSTEM_PROMPT
