"""
AI Financial Coach for Step 6.

Provides intelligent responses to financial questions by:
1. Using trained FLAN-T5 to detect question intent
2. Running appropriate what-if analyses
3. Providing actionable insights based on the user's profile
"""

import logging
from typing import Any, Dict, Optional

from src.data_models import TransitionProfile
from src.wizard.coaching_engine import CoachingQuestion
from src.wizard.summary_engine import calculate_financial_metrics
from src.wizard.what_if_runner import run_what_if_analysis_for_question

logger = logging.getLogger(__name__)

# Optional: Use trained FLAN-T5 for intent detection if available
try:
    from src.ai_layer.flan_t5_loader import FlanT5Loader
    FLAN_T5_AVAILABLE = True
except ImportError:
    FLAN_T5_AVAILABLE = False
    logger.debug("FLAN-T5 not available, using keyword-based intent detection")

# Optional: Use Milestone E RAG advisor for evidence-backed retrieval
try:
    from src.ai_layer.rag_financial_advisor import RAGFinancialAdvisor
    RAG_ADVISOR_AVAILABLE = True
except ImportError:
    RAG_ADVISOR_AVAILABLE = False
    logger.debug("RAG Financial Advisor not available, using FLAN-T5-only routing")


class FinancialCoach:
    """
    Provides AI-powered financial coaching for transition planning.
    
    Hybrid architecture:
    - Primary: FLAN-T5 for intent detection (trained on Milestone C data)
    - Secondary: RAG retrieval for factual military finance Q&A (Milestone E)
    - Fallback: Keyword detection for robustness
    """

    def __init__(self, profile: TransitionProfile):
        """Initialize coach with user's profile."""
        self.profile = profile
        self.baseline_metrics = calculate_financial_metrics(profile)
        
        # Initialize Milestone E RAG advisor (if available)
        self.rag_advisor = None
        if RAG_ADVISOR_AVAILABLE:
            try:
                self.rag_advisor = RAGFinancialAdvisor(config='production')
                logger.info("✅ RAG Financial Advisor loaded (Milestone E)")
            except Exception as e:
                logger.warning(f"RAG advisor failed to initialize: {e} (falling back to FLAN-T5 only)")
                self.rag_advisor = None
        
        # Initialize trained FLAN-T5 for intent detection if available
        self.flan_t5 = None
        if FLAN_T5_AVAILABLE:
            try:
                self.flan_t5 = FlanT5Loader()
                if self.flan_t5.is_available():
                    logger.info("✅ Using trained FLAN-T5 for intent detection")
                else:
                    logger.debug("FLAN-T5 model not loaded, will use keyword fallback")
                    self.flan_t5 = None
            except Exception as e:
                logger.debug(f"FLAN-T5 initialization failed: {e}, using keyword fallback")

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer user's financial question with appropriate analysis.
        
        Hybrid routing strategy:
        1. Try Milestone E RAG retrieval (for factual Q&A)
        2. If confidence >= 0.7 → use RAG answer
        3. Else → fall back to trained FLAN-T5 intent detection + analysis
        4. Final fallback → keyword-based routing

        Args:
            question: User's question about their transition plan

        Returns:
            Dict with:
            - response: str (answer to user's question)
            - analysis: Dict with any relevant metrics
            - insights: List of actionable insights
            - source: str ('rag', 'analysis', or 'fallback')
            - confidence: float (for RAG-sourced answers)
            - retrieval_time_ms: float (for RAG-sourced answers)
        """
        # Try hybrid routing (RAG first, then fallback)
        return self._answer_question_hybrid(question)
    
    def _answer_question_hybrid(self, question: str) -> Dict[str, Any]:
        """
        Hybrid routing: RAG retrieval → FLAN-T5 intent detection → keyword fallback
        
        Implements confidence-based routing:
        - If RAG confidence >= 0.7: use RAG answer (mark source='rag')
        - Else: fall back to intent-based analysis (mark source='analysis')
        """
        question_lower = question.lower()
        
        # 1. Try RAG retrieval (Milestone E) if available
        if self.rag_advisor:
            try:
                rag_result = self.rag_advisor.retrieve_knowledge(question)
                confidence = rag_result.get('confidence', 0.0)
                routing_decision = rag_result.get('routing_decision', 'fallback')
                
                logger.debug(
                    f"RAG retrieval: confidence={confidence:.3f}, "
                    f"routing={routing_decision}"
                )
                
                # If confidence >= 0.7, use RAG answer
                if routing_decision == 'rag' and confidence >= 0.7:
                    rag_response = {
                        'response': rag_result.get('answer', 'No confident answer available'),
                        'analysis': {
                            'source': 'rag',
                            'confidence': confidence,
                            'retrieval_score': rag_result.get('retrieval_score', 0.0),
                            'rerank_score': rag_result.get('rerank_score', 0.0),
                        },
                        'insights': [
                            f"Retrieved from military finance knowledge base (confidence: {confidence:.0%})",
                            f"Evidence: {rag_result.get('evidence', '')[:100]}..."
                        ] if rag_result.get('evidence') else [],
                        'source': 'rag',
                        'confidence': confidence,
                        'retrieval_time_ms': rag_result.get('retrieval_time_ms', 0),
                    }
                    return self._ensure_response_format(rag_response)
                
                # Log that we're falling back due to low confidence
                logger.debug(
                    f"RAG confidence too low ({confidence:.3f} < 0.7), "
                    f"falling back to FLAN-T5 intent detection"
                )
                
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}, falling back to FLAN-T5")
        
        # 2. Fall back to FLAN-T5 intent detection + analysis
        return self._answer_question_intent_based(question)
    
    def _answer_question_intent_based(self, question: str) -> Dict[str, Any]:
        """
        Intent-based routing using FLAN-T5 (Milestone C model).
        
        Falls back to keyword detection if FLAN-T5 unavailable.
        This is the original routing logic, preserved for backward compatibility.
        """
        question_lower = question.lower()
        
        # Try FLAN-T5 intent detection first (uses trained model)
        intent = None
        if self.flan_t5:
            try:
                intent = self.flan_t5.classify_scenario_intent(question)
                logger.debug(f"FLAN-T5 detected intent: {intent}")
            except Exception as e:
                logger.debug(f"FLAN-T5 intent detection failed: {e}, using keyword fallback")
                intent = None
        
        # Route based on FLAN-T5 intent or keyword detection
        if intent == 'job_search_timeline' or (not intent and any(
            phrase in question_lower
            for phrase in [
                "how long", "job search", "take time", "months", "year off", "delay", "how many months"
            ]
        )):
            return self._ensure_response_format(self._analyze_job_timeline(question))
        
        elif intent == 'savings_runway' or (not intent and any(
            phrase in question_lower
            for phrase in [
                "runway", "savings", "last", "depleted", "emergency", "enough money", "cash"
            ]
        )):
            return self._ensure_response_format(self._analyze_runway(question))
        
        elif intent == 'savings_sufficiency' or (not intent and any(
            phrase in question_lower
            for phrase in [
                "enough", "sufficient", "cover", "afford", "support", "manage"
            ]
        )):
            return self._ensure_response_format(self._analyze_runway(question))  # Similar to runway
        
        elif (not intent and any(
            phrase in question_lower
            for phrase in [
                "pension", "percentage", "replace", "what %"
            ]
        )):
            return self._ensure_response_format(self._analyze_pension_replacement(question))
        
        elif (not intent and any(
            phrase in question_lower
            for phrase in [
                "salary", "income", "earn", "job offer", "lower", "reduce", "cut", "confident"
            ]
        )):
            return self._ensure_response_format(self._analyze_salary(question))
        
        elif (not intent and any(
            phrase in question_lower
            for phrase in [
                "expense", "spend", "cut", "reduce", "monthly", "budget", "afford"
            ]
        )):
            return self._ensure_response_format(self._analyze_expenses(question))
        
        elif (not intent and any(
            phrase in question_lower
            for phrase in [
                "spouse", "partner", "dependent", "family", "child", "income loss"
            ]
        )):
            return self._ensure_response_format(self._analyze_household(question))
        
        # Default fallback
        return self._ensure_response_format(self._provide_summary(question))
    
    def _route_and_analyze(self, question: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self._answer_question_intent_based(question)
    
    def _ensure_response_format(self, response_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all response dicts have properly formatted response strings.
        
        Fixes issues with text concatenation by ensuring:
        - Newlines are preserved (\n, \n\n)
        - No excessive whitespace
        - Proper markdown formatting
        """
        if 'response' in response_dict and response_dict['response']:
            # Get the response string
            resp_str = response_dict['response']
            
            # If it's not a string, convert it
            if not isinstance(resp_str, str):
                resp_str = str(resp_str)
            
            # Ensure it has proper newlines and no weird concatenation
            # Replace multiple newlines with exactly 2 (for markdown)
            resp_str = resp_str.replace('\n\n\n', '\n\n')
            resp_str = resp_str.replace('\r\n', '\n')
            
            # Update the response
            response_dict['response'] = resp_str
        
        return response_dict

    def _analyze_job_timeline(self, question: str) -> Dict[str, Any]:
        """Analyze impact of different job search timelines."""
        months = self.profile.job_search_timeline_months

        response = f"**Current Job Search Timeline:** {months} months\n\n"

        # Calculate current runway
        response += (
            f"With your current plan:\n"
            f"• Monthly gap during job search: "
            f"${self.baseline_metrics.phase1_monthly_gap:,.0f}\n"
            f"• Total gap needed: ${self.baseline_metrics.phase1_total_gap:,.0f}\n"
            f"• Runway before savings depleted: "
            f"{self.baseline_metrics.runway_months:.1f} months\n\n"
        )

        # Check if they're asking about delay
        if "delay" in question.lower() or "longer" in question.lower():
            response += (
                "If your job search takes **longer**, you'll need to either:\n"
                "1. **Cut expenses** - reduce monthly spending\n"
                "2. **Find interim income** - consulting, freelance work\n"
                "3. **Reduce job search timeline expectations** - "
                "aim for earlier start\n\n"
            )
            response += (
                f"**Critical point:** Your savings can only sustain "
                f"{self.baseline_metrics.runway_months:.1f} months of deficit spending.\n"
            )

        elif "year off" in question.lower() or "12 month" in question.lower():
            if self.baseline_metrics.runway_months >= 12:
                response += (
                    "[OK] **Good news:** You have enough savings to support a "
                    "full year off!\n\n"
                    "You could take a year-long sabbatical without requiring "
                    "interim income.\n"
                )
            else:
                response += (
                    "[WARNING] **Not feasible with current plan:** You only have "
                    f"{self.baseline_metrics.runway_months:.1f} months of runway.\n\n"
                    "A full year off would require either:\n"
                    "1. Cutting expenses significantly\n"
                    "2. Having additional savings/income source\n"
                    "3. Shortening the job search to 6-8 months\n"
                )

        return {
            "response": response,
            "analysis": {
                "current_months": months,
                "monthly_gap": self.baseline_metrics.phase1_monthly_gap,
                "runway_months": self.baseline_metrics.runway_months,
            },
            "insights": [
                f"Your runway is {self.baseline_metrics.runway_months:.1f} months",
                f"Each additional month of job search costs ${abs(self.baseline_metrics.phase1_monthly_gap):,.0f}",
            ],
        }

    def _analyze_runway(self, question: str) -> Dict[str, Any]:
        """Analyze savings runway and liquidity."""
        response = (
            f"**Your Financial Runway:**\n\n"
            f"Starting savings: ${self.baseline_metrics.starting_savings:,.0f}\n"
            f"Total gap during job search: ${self.baseline_metrics.phase1_total_gap:,.0f}\n"
            f"Remaining after gap: ${self.baseline_metrics.savings_after_gap:,.0f}\n\n"
            f"**Runway (months of survival):** "
            f"{self.baseline_metrics.runway_months:.1f} months\n\n"
        )

        if self.baseline_metrics.runway_months < 6:
            response += (
                "\n\n[WARNING] **Critical:** Your runway is less than 6 months. "
                "This is tight. You need to:\n"
                "1. Secure a job quickly (within 3-4 months)\n"
                "2. Have a backup income source ready\n"
                "3. Reduce expenses immediately\n\n"
            )
        elif self.baseline_metrics.runway_months < 12:
            response += (
                f"\n\n[STATS] **Moderate risk:** With {self.baseline_metrics.runway_months:.1f} months of runway, "
                "you have some flexibility but need focus:\n"
                "1. Target landing a job within this window\n"
                "2. Have contingency plans if search extends\n"
                "3. Consider part-time/contract work if needed\n\n"
            )
        else:
            response += (
                f"\n\n[OK] **Good position:** {self.baseline_metrics.runway_months:.1f} months of runway "
                "gives you flexibility to find the right opportunity.\n\n"
            )

        return {
            "response": response,
            "analysis": {
                "starting_savings": self.baseline_metrics.starting_savings,
                "runway_months": self.baseline_metrics.runway_months,
            },
            "insights": [
                f"You can sustain {self.baseline_metrics.runway_months:.1f} months without new income",
                f"Buffer remaining: ${self.baseline_metrics.savings_after_gap:,.0f}",
            ],
        }

    def _analyze_pension_replacement(self, question: str) -> Dict[str, Any]:
        """Analyze pension replacement ratio and income transition."""
        # Extract pension and military income from question if possible
        # For now, use profile data
        military_income_annual = self.profile.current_annual_retirement_pay
        military_income_monthly = military_income_annual / 12 if military_income_annual > 0 else 0
        
        # If we have monthly data instead, use that
        if military_income_monthly == 0:
            # Try to estimate from question or use profile takehome
            military_income_monthly = self.profile.current_savings  # Fallback
        
        pension_monthly = self.profile.current_annual_retirement_pay / 12
        pension_annual = self.profile.current_annual_retirement_pay
        
        # Calculate replacement ratio
        if military_income_monthly > 0:
            replacement_percentage = (pension_monthly / military_income_monthly) * 100
        else:
            replacement_percentage = 0
        
        response = (
            f"**Pension Income Analysis**\n\n"
            f"Military retirement income:\n"
            f"  • Monthly: ${military_income_monthly:,.0f}\n"
            f"  • Annual: ${military_income_annual:,.0f}\n\n"
            f"Pension income starting at separation:\n"
            f"  • Monthly: ${pension_monthly:,.0f}\n"
            f"  • Annual: ${pension_annual:,.0f}\n\n"
            f"**Replacement Ratio:** {replacement_percentage:.1f}% of military income\n\n"
        )
        
        if replacement_percentage >= 80:
            response += (
                "[OK] **Strong pension base:** Your pension replaces >80% of military income!\n"
                "This gives you stability during job search. Use this buffer to be selective "
                "with job offers.\n"
            )
        elif replacement_percentage >= 50:
            response += (
                "[GOOD] **Solid foundation:** Pension covers ~50-80% of living costs.\n"
                "You'll need civilian income to supplement, but have breathing room. "
                "Focus on quality job fit, not speed.\n"
            )
        else:
            response += (
                "[WARNING] **Income gap:** Pension covers <50% of current spending.\n"
                "You'll need to either:\n"
                "1. Cut expenses to match pension level\n"
                "2. Find civilian job quickly\n"
                "3. Use savings strategically\n"
            )
        
        response += (
            f"\n**Phase 2 Focus:** Once employed, your civilian income "
            f"(${self.profile.estimated_annual_salary:,.0f}/year) + pension "
            f"(${pension_annual:,.0f}/year) should fully support your transition.\n"
        )
        
        return {
            "response": response,
            "analysis": {
                "military_income_monthly": military_income_monthly,
                "pension_monthly": pension_monthly,
                "replacement_percentage": replacement_percentage,
            },
            "insights": [
                f"Pension replaces {replacement_percentage:.1f}% of military income",
                f"Combined pension + civilian income: ${(pension_annual + self.profile.estimated_annual_salary):,.0f}/year",
            ],
        }

    def _analyze_salary(self, question: str) -> Dict[str, Any]:
        """Analyze impact of salary variations."""
        current_salary = self.profile.estimated_annual_salary
        response = f"**Current Salary Assumption:** ${current_salary:,.0f}/year\n\n"

        if "lower" in question.lower() or "reduce" in question.lower():
            lower_salary = current_salary * 0.9
            response += f"If your actual salary is 10% lower (${lower_salary:,.0f}):\n\n"
            response += (
                "This would reduce your Phase 2 (after getting job) monthly income by "
                f"~${(current_salary - lower_salary) / 12:,.0f}.\n\n"
                "You'd need to adjust by:\n"
                "1. Cutting expenses or\n"
                "2. Extending job search less (get job faster) or\n"
                "3. Finding second income source\n"
            )

        elif "confident" in question.lower():
            response += (
                f"Your plan assumes you'll earn ${current_salary:,.0f}/year.\n\n"
                "This is a critical assumption. If salary is lower:\n"
                "• 10% lower → costs ~${(current_salary * 0.1) / 12:,.0f}/month\n"
                "• 20% lower → costs ~${(current_salary * 0.2) / 12:,.0f}/month\n\n"
                "Build a buffer by:\n"
                "1. Starting job search 1-2 months early\n"
                "2. Having backup opportunities at lower pay\n"
                "3. Planning expense cuts if needed\n"
            )

        return {
            "response": response,
            "analysis": {"current_salary": current_salary},
            "insights": [
                f"Salary assumption: ${current_salary:,.0f}/year",
                "10% salary miss = ~${(current_salary * 0.1) / 12:,.0f}/month impact",
            ],
        }

    def _analyze_expenses(self, question: str) -> Dict[str, Any]:
        """Analyze expense reduction options."""
        total_monthly = (
            self.profile.monthly_expenses_mandatory
            + self.profile.monthly_expenses_negotiable
            + self.profile.monthly_expenses_optional
        )

        response = (
            f"**Current Monthly Expenses:** ${total_monthly:,.0f}\n\n"
            f"• Mandatory (housing, food, essentials): "
            f"${self.profile.monthly_expenses_mandatory:,.0f}\n"
            f"• Negotiable (discretionary): "
            f"${self.profile.monthly_expenses_negotiable:,.0f}\n"
            f"• Optional (luxury items): "
            f"${self.profile.monthly_expenses_optional:,.0f}\n\n"
        )

        if "cut" in question.lower() or "reduce" in question.lower():
            cut_10 = total_monthly * 0.10
            cut_20 = total_monthly * 0.20

            response += (
                f"**Expense Cutting Options:**\n\n"
                f"• 10% cut (${cut_10:,.0f}/mo): "
                f"Reduce negotiable/optional spending\n"
                f"  → New monthly gap: "
                f"${self.baseline_metrics.phase1_monthly_gap - cut_10:,.0f}\n\n"
                f"• 20% cut (${cut_20:,.0f}/mo): "
                f"Significant lifestyle adjustment\n"
                f"  → New monthly gap: "
                f"${self.baseline_metrics.phase1_monthly_gap - cut_20:,.0f}\n\n"
            )

            if self.baseline_metrics.phase1_monthly_gap - cut_10 <= 0:
                response += "[OK] Good news: A 10% expense cut would close your " "monthly gap entirely!\n"
            elif self.baseline_metrics.phase1_monthly_gap - cut_20 <= 0:
                response += "[OK] A 20% expense cut would eliminate the monthly deficit.\n"
            else:
                response += (
                    "Even with 20% cuts, you'd still have a gap. " "Focus on income (job search speed) instead.\n"
                )

        return {
            "response": response,
            "analysis": {
                "total_monthly": total_monthly,
                "mandatory": self.profile.monthly_expenses_mandatory,
                "negotiable": self.profile.monthly_expenses_negotiable,
                "optional": self.profile.monthly_expenses_optional,
            },
            "insights": [
                f"Total monthly spending: ${total_monthly:,.0f}",
                f"Flexible cuts available: "
                f"${self.profile.monthly_expenses_negotiable + self.profile.monthly_expenses_optional:,.0f}",
            ],
        }

    def _analyze_household(self, question: str) -> Dict[str, Any]:
        """Analyze household income and dependency risks."""
        spouse_income = self.profile.spouse_annual_income
        monthly_spouse = spouse_income / 12 if spouse_income > 0 else 0

        response = f"**Household Income Analysis:**\n\n"

        if spouse_income > 0:
            response += (
                f"Your plan includes spouse income: ${spouse_income:,.0f}/year "
                f"(${monthly_spouse:,.0f}/month)\n\n"
                f"This is {(monthly_spouse / (self.baseline_metrics.phase1_monthly_income / 12) * 100):.0f}% "
                f"of your Phase 1 income.\n\n"
                "**Risk factors:**\n"
                "• Job loss by spouse → lose "
                f"${monthly_spouse:,.0f}/month\n"
                "• Career break (child care, health) → same impact\n"
                "• Reduced hours → partial income loss\n\n"
                "**Contingency:** Your runway assumes spouse income continues. "
                "Verify this is stable before transition.\n"
            )
        else:
            response += (
                "You're not planning on spouse/dependent income, which reduces "
                "household risk.\n\n"
                "This is actually a strength - your plan doesn't depend on "
                "multiple income sources.\n"
            )

        return {
            "response": response,
            "analysis": {
                "spouse_income": spouse_income,
                "dependents": self.profile.dependents,
            },
            "insights": [
                f"Spouse income: ${spouse_income:,.0f}/year",
                f"Plan vulnerability: Depends on {('spouse income' if spouse_income > 0 else 'single income')}",
            ],
        }

    def _provide_summary(self, question: str) -> Dict[str, Any]:
        """Provide financial summary when question doesn't match specific category."""
        response = (
            "**Your Financial Transition Summary:**\n\n"
            f"[STATS] **Baseline Scenario** (Current Plan):\n"
            f"• Military Pension: ${self.profile.current_annual_retirement_pay:,.0f}/year\n"
            f"• New Job Salary: ${self.profile.estimated_annual_salary:,.0f}/year\n"
            f"• Job Search Timeline: {self.profile.job_search_timeline_months} months\n"
            f"• Current Savings: ${self.profile.current_savings:,.0f}\n\n"
            f"**Phase 1 (During Job Search):**\n"
            f"• Monthly Gap: ${abs(self.baseline_metrics.phase1_monthly_gap):,.0f}\n"
            f"• Total Gap: ${self.baseline_metrics.phase1_total_gap:,.0f}\n"
            f"• Runway: {self.baseline_metrics.runway_months:.1f} months\n\n"
            f"**Phase 2 (After Job):**\n"
            f"• Monthly Surplus: ${self.baseline_metrics.phase2_monthly_surplus:,.0f}\n\n"
            "I can help you analyze specific scenarios. Try asking:\n"
            "- 'What if my job search takes 12 months?'\n"
            "- 'How much can I cut expenses?'\n"
            "- 'What's my runway with current savings?'\n"
            "- 'Is my salary assumption realistic?'\n"
        )

        return {
            "response": response,
            "analysis": {},
            "insights": [
                f"Current monthly gap: ${abs(self.baseline_metrics.phase1_monthly_gap):,.0f}",
                f"Runway: {self.baseline_metrics.runway_months:.1f} months",
            ],
        }

    # TODO: Future Analysis Methods (Not Yet Implemented)
    # def _analyze_debt_reduction(self, question: str) -> Dict[str, Any]:
    #     """Analyze debt payoff timelines and strategies.
    #     
    #     Would integrate with savings runway to determine:
    #     - Accelerated debt payoff scenarios
    #     - Credit card vs personal loan prioritization
    #     - Impact of transition income on debt elimination timeline
    #     
    #     Intent trigger: questions about credit cards, personal loans, debt elimination
    #     """
    #     pass
    #
    # def _analyze_mortgage_amortization(self, question: str) -> Dict[str, Any]:
    #     """Detailed mortgage analysis including amortization schedules.
    #     
    #     Would provide:
    #     - Monthly payment breakdowns (principal vs interest)
    #     - Refinance comparisons
    #     - Accelerated payoff scenarios
    #     - Impact of lump-sum payments from transition income
    #     
    #     Intent trigger: questions about mortgages, home equity, refinancing
    #     """
    #     pass
