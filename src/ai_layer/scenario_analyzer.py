"""
Scenario Analyzer - Analyzes what-if scenarios using trained FLAN-T5 models.

Uses FLAN-T5 (trained in AIT716 Milestone C) to detect scenario intent,
then analyzes financial impact based on current profile + scenario parameters.

This is separate from profile-building (ChatFlowHandler).
Focused on: "What if I take 8 months? What if I use GI Bill?"
"""

import logging
from typing import Any, Dict, Optional

from src.ai_layer.orchestrator import NaturalLanguageParser
from src.ai_layer.scenario_tool_executor import ScenarioToolExecutor

# Optional: Try to load FLAN-T5, but don't crash if transformers is unavailable
try:
    from src.ai_layer.flan_t5_loader import FlanT5Loader
    FLAN_T5_AVAILABLE = True
except (ImportError, Exception) as e:
    FLAN_T5_AVAILABLE = False
    FlanT5Loader = None
    logging.warning(f"FLAN-T5 not available: {e}. Will use keyword-based fallback.")

# Optional: Try to load RAG Financial Advisor (Milestone E)
try:
    from src.ai_layer.rag_financial_advisor import RAGFinancialAdvisor
    RAG_AVAILABLE = True
except (ImportError, Exception) as e:
    RAG_AVAILABLE = False
    RAGFinancialAdvisor = None
    logging.error(f"❌ RAG Financial Advisor import failed: {type(e).__name__}: {e}. Will use intent-based fallback.")

logger = logging.getLogger(__name__)


class ScenarioAnalyzer:
    """
    Analyzes what-if scenarios using FLAN-T5 intent classification.
    
    Given:
    - Current financial profile (expenses, income, savings)
    - Scenario question ("What if takes 9 months?")
    
    Uses:
    - FLAN-T5 model (trained in AIT716 Milestone C) to detect intent
    - NaturalLanguageParser to extract parameters
    - Financial calculations to show impact
    
    Returns:
    - Extracted scenario parameters
    - Analysis and recommendations
    """
    
    def __init__(self):
        """Initialize with NaturalLanguageParser, RAG advisor, FLAN-T5, and tool executor."""
        self.parser = NaturalLanguageParser()
        self.flan_t5 = None
        self.rag_advisor = None  # Milestone E RAG system (primary path)
        self.tool_executor = ScenarioToolExecutor()  # Executes multi-step scenarios
        
        # Try to load RAG Financial Advisor (Milestone E) - PRIMARY PATH
        if RAG_AVAILABLE and RAGFinancialAdvisor is not None:
            try:
                logger.info("🚀 Loading RAG Financial Advisor...")
                self.rag_advisor = RAGFinancialAdvisor(config='production')
                logger.info("✅ RAG Financial Advisor loaded (Milestone E). Using hybrid RAG + intent-based routing.")
            except Exception as e:
                logger.error(f"❌ Failed to initialize RAG advisor: {type(e).__name__}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.rag_advisor = None
        else:
            logger.info("⚠️ RAG Financial Advisor not available. Using intent-based analysis only.")
        
        # Try to load FLAN-T5 if available (fallback for low-confidence RAG)
        if FLAN_T5_AVAILABLE and FlanT5Loader is not None:
            try:
                self.flan_t5 = FlanT5Loader()  # Loads trained model from Milestone C
                if self.flan_t5.is_available():
                    logger.info("✅ FLAN-T5 model loaded. Using as fallback for intent detection.")
                else:
                    logger.info("⚠️ FLAN-T5 model not available. Using fallback pattern matching.")
            except Exception as e:
                logger.warning(f"Failed to initialize FLAN-T5: {e}. Using keyword fallback.")
                self.flan_t5 = None
        else:
            logger.info("⚠️ FLAN-T5 not available. Using keyword-based fallback for intent detection.")
    
    def detect_scenario_intent(self, question: str) -> str:
        """
        Detect the intent of a scenario question using FLAN-T5 model (or keyword fallback).
        
        Uses trained FLAN-T5 from Milestone C to classify intent.
        Fallback to pattern matching if model unavailable.
        
        Returns one of:
        - 'job_search_timeline': "What if takes X months?"
        - 'gi_bill': "What if I use GI Bill?"
        - 'savings_runway': "How long can I live on savings?"
        - 'savings_sufficiency': "Do I have enough savings?"
        - 'expense_reduction': "What if I cut expenses?"
        - 'cash_position': "What's my cash after X months?"
        - 'va_disability': "What if my VA disability is X%?"
        - 'unknown': Couldn't determine
        """
        # Use FLAN-T5 model if available, otherwise use keyword fallback
        if self.flan_t5:
            return self.flan_t5.classify_scenario_intent(question)
        else:
            # Keyword-based fallback
            return self._keyword_classify_intent(question)
    
    def _keyword_classify_intent(self, question: str) -> str:
        """Keyword-based intent classification (used when FLAN-T5 unavailable or uncertain)."""
        q_lower = question.lower()
        
        # VA DISABILITY: Catch VA rating/disability scenarios (flexible to handle misspellings like "disablity")
        va_keywords = ['va', 'disability', 'disablity', 'rating', 'va rating']
        scenario_keywords = ['what if', 'if my', 'change', 'different', 'increase', 'higher', 'lower', 'decrease', 'have', 'had']
        if any(w in q_lower for w in va_keywords):
            # Match if: has scenario keywords OR contains percentage/number pattern (e.g., "50%", "at 50")
            if any(w in q_lower for w in scenario_keywords) or any(c.isdigit() for c in question):
                return 'va_disability'
        
        # EXPENSE REDUCTION: Explicitly catch debt/loan/expense reduction scenarios
        if any(w in q_lower for w in ['lower', 'reduce', 'cut', 'decrease', 'save', 'lower my', 'loan', 'equity', 'debt', 'payment', 'monthly', 'expense']):
            # Check if it mentions a dollar amount or specific savings
            if any(c.isdigit() for c in question) or any(w in q_lower for w in ['by', 'save', 'reduce']):
                return 'expense_reduction'
        
        if any(w in q_lower for w in ['how long', 'job search', 'months', 'how many', 'take', 'timeline']):
            return 'job_search_timeline'
        elif any(w in q_lower for w in ['gi bill', 'education', 'training', 'school']):
            return 'gi_bill'
        elif any(w in q_lower for w in ['runway', 'last', 'deplete', 'cash']):
            return 'savings_runway'
        elif any(w in q_lower for w in ['enough', 'sufficient', 'manage', 'afford']):
            return 'savings_sufficiency'
        elif any(w in q_lower for w in ['position', 'cash after', 'cash flow']):
            return 'cash_position'
        else:
            return 'unknown'
    
    def analyze_scenario(
        self,
        question: str,
        current_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a scenario question against the current profile.
        
        Uses Milestone E RAG (primary path) + FLAN-T5 intent detection fallback.
        
        For specific scenario calculation types (expense_reduction, gi_bill, etc.),
        bypasses RAG and uses profile-specific intent-based analysis.
        
        Args:
            question: User's scenario question
            current_profile: Dict with keys:
                - pension: monthly take-home
                - va_monthly: monthly VA income
                - estimated_civilian_salary: annual salary (converted to monthly)
                - job_search_timeline_months: expected months to find job
                - current_savings: total liquid savings
                - csv_mandatory_expenses: monthly
                - csv_negotiable_expenses: monthly
                - csv_optional_expenses: monthly
                - adjusted_prepaid_monthly: monthly
                - gi_bill_bah_monthly: monthly BAH if using GI Bill
                - user_locality, user_state: location
        
        Returns:
            Dict with:
            - intent: str (detected intent)
            - extracted_params: Dict (parameters found and computed)
            - analysis: str (human-readable analysis)
            - recommendation: str (what to do)
            - calculations: Dict (numerical breakdown)
            - execution_log: List of tool executions performed
            - source: str ('rag' if from Milestone E, 'analysis' if from intent-based)
        """
        
        # Step 0a: Check if this is a SCENARIO CALCULATION question
        # These require profile-specific analysis, not generic KB answers
        # Skip RAG for these; go straight to intent-based analysis
        scenario_keywords = {
            'expense_reduction': ['reduce', 'lower', 'cut', 'decrease', 'expense', 'spending', 'loan', 'debt', 'payment'],
            'gi_bill': ['gi bill', 'education', 'school', 'degree', 'mba', 'master', 'training', 'university'],
            'job_search_timeline': ['month', 'timeline', 'search', 'find', 'job', 'how long', 'how many', 'months'],
            'savings_runway': ['runway', 'last', 'deplete', 'months', 'how long'],
            'savings_sufficiency': ['enough', 'sufficient', 'manage', 'afford', 'zero savings'],
            'va_disability': ['va', 'disability', 'rating', 'va rating'],
        }
        q_lower = question.lower()
        force_intent_analysis = False
        detected_scenario_type = None
        
        for scenario_type, keywords in scenario_keywords.items():
            if any(kw in q_lower for kw in keywords):
                force_intent_analysis = True
                detected_scenario_type = scenario_type
                logger.info(f"🎯 Detected scenario calculation type: {scenario_type}. Using intent-based analysis.")
                break
        
        # Step 0b: Try Milestone E RAG first (primary path) - unless this is a scenario calculation
        rag_result = None
        if not force_intent_analysis and self.rag_advisor is not None:
            try:
                logger.info(f"📚 [MILESTONE E] Attempting RAG retrieval for: '{question[:60]}...'")
                rag_result = self.rag_advisor.retrieve_knowledge(question)
                
                if rag_result and isinstance(rag_result, dict):
                    confidence = rag_result.get('confidence', 0.0)
                    logger.info(f"🎯 [MILESTONE E] RAG confidence score: {confidence:.2f}")
                    
                    # If RAG is confident (>= 0.7), use the RAG answer
                    if confidence >= 0.7:
                        logger.info("✅ [MILESTONE E] Using RAG answer (confidence >= 0.7) - FACTUAL Q&A ROUTED TO MILESTONE E")
                        return {
                            'intent': 'rag_retrieved',
                            'question': question,
                            'extracted_params': rag_result.get('query_params', {}),
                            'analysis': rag_result.get('answer', ''),
                            'recommendation': rag_result.get('answer', ''),
                            'calculations': {},
                            'execution_log': [f"🎯 MILESTONE E RAG answered this (confidence: {confidence:.2f})", f"   Retrieval: {rag_result.get('retrieval_time_ms', 0)}ms"],
                            'success': True,
                            'source': 'rag',
                            'confidence': confidence,
                            'routing_decision': rag_result.get('routing_decision', 'rag_high_confidence')
                        }
                    else:
                        logger.info(f"⚠️  [MILESTONE E] RAG confidence too low ({confidence:.2f} < 0.7), using intent-based fallback")
            except Exception as e:
                logger.warning(f"❌ [MILESTONE E] RAG retrieval failed: {e}. Falling back to intent-based analysis")
                rag_result = None
        
        # Step 1: Detect intent (with None safety check for flan_t5) - FALLBACK PATH
        # Use pre-detected scenario type if available from Step 0a
        if detected_scenario_type:
            intent = detected_scenario_type
            logger.info(f"🧠 [MILESTONE C] Scenario detected: '{intent}' - Using FLAN-T5 analysis")
        else:
            intent = self.detect_scenario_intent(question)
            logger.info(f"🧠 [MILESTONE C] Intent detected: '{intent}' - Using FLAN-T5 for scenario analysis from question: '{question[:60]}...'")
        
        # Step 2: Extract parameters based on intent
        extracted_params = {}
        if intent == 'expense_reduction':
            # For expense reduction, extract the specific amount mentioned
            extracted_params = self.tool_executor.extract_expense_reduction_params(question)
        elif intent == 'gi_bill':
            # For GI Bill, extract degree and location
            extracted_params = self.tool_executor.extract_education_params(question, current_profile)
        elif intent == 'job_search_timeline':
            # For job search timeline, extract the timeline in months
            extracted_params = self.tool_executor.extract_timeline_params(question)
        elif intent == 'va_disability':
            # For VA disability rating changes, extract the new rating percentage
            extracted_params = self.tool_executor.extract_va_disability_params(question)
        
        # Step 3: Plan multi-step tools needed (if flan_t5 available)
        # For complex questions, this returns the sequence of tools to execute
        tool_plan = {}
        if self.flan_t5 and hasattr(self.flan_t5, 'plan_scenario_steps'):
            try:
                tool_plan = self.flan_t5.plan_scenario_steps(question, context=current_profile)
            except Exception as e:
                logger.warning(f"Failed to plan scenario steps: {e}. Using basic execution")
                tool_plan = {}
        
        # Step 4: Execute the tool plan
        # This orchestrates: parameter extraction → intermediate calculations → financial recalculation
        execution_result = self.tool_executor.execute_plan(tool_plan, current_profile, question, intent=intent)
        
        # Merge manually extracted params with tool execution params
        extracted_params.update(execution_result.get('extracted_params', {}))
        
        # Step 5: Ensure expense breakdown is always calculated and complete
        calculations = execution_result.get('calculations', {})
        
        # Always ensure expense_breakdown exists and is complete
        if 'expense_breakdown' not in calculations:
            calculations['expense_breakdown'] = {}
        
        # Compute expense values if not already there
        mandatory = calculations['expense_breakdown'].get('mandatory', current_profile.get('csv_mandatory_expenses', 0))
        negotiable = calculations['expense_breakdown'].get('negotiable', current_profile.get('csv_negotiable_expenses', 0))
        optional = calculations['expense_breakdown'].get('optional', current_profile.get('csv_optional_expenses', 0))
        prepaid = calculations['expense_breakdown'].get('prepaid', current_profile.get('adjusted_prepaid_monthly', 0))
        
        # Ensure all values are in the expense_breakdown
        calculations['expense_breakdown']['mandatory'] = mandatory
        calculations['expense_breakdown']['negotiable'] = negotiable
        calculations['expense_breakdown']['optional'] = optional
        calculations['expense_breakdown']['prepaid'] = prepaid
        
        # Calculate and store the totals
        baseline = mandatory + negotiable
        total = mandatory + negotiable + optional + prepaid
        calculations['expense_breakdown']['baseline_total'] = baseline
        calculations['expense_breakdown']['total'] = total
        
        # Step 6: Generate human-readable analysis
        analysis, recommendation = self._generate_response(
            intent,
            extracted_params,
            calculations,
            current_profile
        )
        
        # Step 7: Return with source attribution
        execution_log = execution_result.get('tool_execution_log', [])
        execution_log.insert(0, f"✅ [MILESTONE C - FLAN-T5] Handled scenario analysis for: {intent}")
        execution_log.append(f"📊 Recommendation generated by Milestone C (trained on 498 scenario Q&A pairs)")
        
        return {
            'intent': intent,
            'question': question,
            'extracted_params': extracted_params,
            'analysis': analysis,
            'recommendation': recommendation,
            'calculations': calculations,
            'execution_log': execution_log,
            'success': execution_result.get('success', False),
            'source': 'flan_t5_analysis'  # Scenario analysis from Milestone C
        }
    
    
    def _calculate_debt_to_income(self, essential_expenses: float, income: float) -> dict:
        """Calculate realistic debt-to-income ratio.
        
        Args:
            essential_expenses: Mandatory + Negotiable expenses
            income: Total monthly income
            
        Returns:
            Dict with DTI percentage and assessment
        """
        if income <= 0:
            return {'ratio': 100.0, 'status': 'Critical', 'assessment': 'No income'}
        
        ratio = (essential_expenses / income) * 100
        
        if ratio <= 36:
            status = '✅ Excellent'
            assessment = 'Sustainable - Well below 36% threshold'
        elif ratio <= 43:
            status = '✅ Good'
            assessment = 'Acceptable - Within standard lending guidelines'
        elif ratio <= 50:
            status = '⚠️ High'
            assessment = 'Tight but manageable - Consider expense cuts'
        else:
            status = '❌ Critical'
            assessment = 'Unsustainable - Require significant changes'
        
        return {
            'ratio': ratio,
            'status': status,
            'assessment': assessment,
            'sustainable': ratio <= 50
        }
    
    def _get_category_items(self, classification_map: Dict[str, str], final_amounts: Dict[str, float], category: str, limit: int = 3) -> str:
        """Extract top items from a category to build real descriptions.
        
        Args:
            classification_map: Dict of {item_description: category}
            final_amounts: Dict of {item_description: amount}
            category: 'mandatory', 'negotiable', 'optional', or 'prepaid'
            limit: Max number of items to show
            
        Returns:
            Comma-separated string of top items (by amount) in that category
        """
        # Find all items in this category, sorted by amount (descending)
        items_in_category = [
            (desc, final_amounts.get(desc, 0))
            for desc, cat in classification_map.items()
            if cat == category
        ]
        items_in_category.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N items
        top_items = [item[0] for item in items_in_category[:limit]]
        
        # Return as comma-separated string (truncate long names)
        return ', '.join([name[:30] + '...' if len(name) > 30 else name for name in top_items]) if top_items else category.title()
    
    def _generate_response(
        self,
        intent: str,
        extracted_params: Dict[str, Any],
        calculations: Dict[str, Any],
        current_profile: Dict[str, Any]
    ) -> tuple:
        """Generate human-readable analysis and recommendation."""
        
        if intent == 'gi_bill':
            # Get BAH from extracted params (calculated by tool executor) or from calculations
            bah = extracted_params.get('gi_bill_bah', 0) or calculations.get('gi_bill_bah', 0)
            degree = extracted_params.get('degree', 'program')
            location = extracted_params.get('location', 'your location')
            
            # Get income sources
            pension = current_profile.get('pension', 0)
            va_monthly = current_profile.get('va_monthly', 0)
            income_with_bah = pension + va_monthly + bah  # Calculate total income during school
            
            # Get expense breakdown
            exp_breakdown = calculations.get('expense_breakdown', {})
            mandatory = exp_breakdown.get('mandatory', 0)
            negotiable = exp_breakdown.get('negotiable', 0)
            optional = exp_breakdown.get('optional', 0)
            prepaid = exp_breakdown.get('prepaid', 0)
            baseline_total = exp_breakdown.get('baseline_total', 0)
            
            if bah == 0:
                analysis = "⚠️ No GI Bill BAH found. Go to Step 4 (Education) to configure your degree program and location."
                recommendation = "Complete the education section to see how BAH improves your financial position."
            else:
                # Calculate with essential spending only
                deficit_essential = max(0, baseline_total - income_with_bah)
                total_with_all = mandatory + negotiable + optional + prepaid
                
                # Calculate realistic DTI ratios
                essential_dti = self._calculate_debt_to_income(baseline_total, income_with_bah)
                full_dti = self._calculate_debt_to_income(total_with_all, income_with_bah)
                
                # Get actual classified items instead of generic examples
                classification_map = current_profile.get('csv_classification_map', {})
                final_amounts = current_profile.get('final_amounts', {})
                mandatory_items = self._get_category_items(classification_map, final_amounts, 'mandatory')
                negotiable_items = self._get_category_items(classification_map, final_amounts, 'negotiable')
                optional_items = self._get_category_items(classification_map, final_amounts, 'optional')
                prepaid_items = self._get_category_items(classification_map, final_amounts, 'prepaid')
                
                analysis = f"""
                **Using GI Bill for {degree.title()} in {location}**
                **→ Provides ${bah:,.0f}/month BAH**
                
                **Your Income During School:**
                - Pension: ${current_profile.get('pension', 0):,.0f}/mo
                - VA: ${current_profile.get('va_monthly', 0):,.0f}/mo
                - GI Bill BAH: ${bah:,.0f}/mo
                - **Total: ${income_with_bah:,.0f}/mo**
                
                **Monthly Expenses Breakdown:**
                - Mandatory ({mandatory_items}): ${mandatory:,.0f}
                - Negotiable ({negotiable_items}): ${negotiable:,.0f}
                - Optional ({optional_items}): ${optional:,.0f}
                - Prepaid ({prepaid_items}): ${prepaid:,.0f}
                - **Baseline (Essential): ${baseline_total:,.0f}** ← Mandatory + Negotiable
                
                **Debt-to-Income Ratio Analysis:**
                - Essential DTI: {essential_dti['ratio']:.1f}% {essential_dti['status']} ({essential_dti['assessment']})
                - Full DTI: {full_dti['ratio']:.1f}% (with optional/prepaid)
                
                **Financial Impact:**
                - With ESSENTIAL only: ${deficit_essential:,.0f}/mo gap
                - With ALL expenses: ${max(0, total_with_all - income_with_bah):,.0f}/mo gap
                
                **The BAH covers or nearly covers your essential expenses!**
                Your essential expenses are sustainable during school.
                """
                context = f"Degree: {degree}, Location: {location}, BAH: ${bah:,.0f}, Income: ${income_with_bah:,.0f}, Baseline: ${baseline_total:,.0f}, Essential DTI: {essential_dti['ratio']:.1f}%"
                recommendation = self._generate_recommendation_with_flan(
                    question=f"Using GI Bill for {degree} in {location}",
                    analysis=analysis,
                    intent=intent,
                    context=context
                )
                if not recommendation:
                    recommendation = "✅ **Strong option** - GI Bill provides stability for essential expenses during school."
                recommendation = self._sanitize_text(recommendation)
            
            recommendation = self._sanitize_text(recommendation)
            return analysis, recommendation
        
        elif intent == 'job_search_timeline':
            new_months = extracted_params.get('job_search_months',
                                             calculations.get('job_search_months', 6))
            deficit = calculations.get('monthly_deficit', 0)
            deficit_baseline = calculations.get('monthly_deficit_baseline', 0)
            runway = calculations.get('runway_months', 0)
            shortfall = calculations.get('shortfall', 0)
            
            # Get expense breakdown
            exp_breakdown = calculations.get('expense_breakdown', {})
            mandatory = exp_breakdown.get('mandatory', 0)
            negotiable = exp_breakdown.get('negotiable', 0)
            optional = exp_breakdown.get('optional', 0)
            prepaid = exp_breakdown.get('prepaid', 0)
            baseline_total = exp_breakdown.get('baseline_total', 0)
            
            military_income = current_profile.get('pension', 0) + current_profile.get('va_monthly', 0)
            available_credit = current_profile.get('available_credit', 0)
            
            # Calculate realistic DTI ratios
            essential_dti = self._calculate_debt_to_income(baseline_total, military_income)
            full_dti = self._calculate_debt_to_income(baseline_total + optional + prepaid, military_income)
            
            # Get actual classified items instead of generic examples
            classification_map = current_profile.get('csv_classification_map', {})
            final_amounts = current_profile.get('final_amounts', {})
            mandatory_items = self._get_category_items(classification_map, final_amounts, 'mandatory')
            negotiable_items = self._get_category_items(classification_map, final_amounts, 'negotiable')
            optional_items = self._get_category_items(classification_map, final_amounts, 'optional')
            prepaid_items = self._get_category_items(classification_map, final_amounts, 'prepaid')
            
            analysis = f"""
            **Job search taking {new_months} months**
            
            **Monthly Income (Pension + VA): ${military_income:,.0f}/mo**
            
            **Monthly Expenses:**
            - Mandatory ({mandatory_items}): ${mandatory:,.0f}
            - Negotiable ({negotiable_items}): ${negotiable:,.0f}
            - Optional ({optional_items}): ${optional:,.0f}
            - Prepaid ({prepaid_items}): ${prepaid:,.0f}
            - **Essential Baseline: ${baseline_total:,.0f}**
            
            **Debt-to-Income Ratio Analysis:**
            - Essential DTI: {essential_dti['ratio']:.1f}% {essential_dti['status']} ({essential_dti['assessment']})
            - Full DTI: {full_dti['ratio']:.1f}% (with optional/prepaid)
            
            **Monthly Gap:**
            - Essential only: ${deficit_baseline:,.0f}/mo deficit
            - Full spending: ${deficit:,.0f}/mo deficit
            - Savings runway: {runway:.1f} months (with full spending)
            - **Total Shortfall over {new_months} months: ${shortfall:,.0f}**
            """
            
            job_search_analysis = analysis
            
            if shortfall > 0:
                # Can't cover with expenses alone - need credit
                # Calculate savings from cutting expenses
                optional_savings_total = optional * new_months
                prepaid_savings_total = prepaid * new_months
                remaining_shortfall_after_optional = max(0, shortfall - optional_savings_total)
                monthly_credit_needed = remaining_shortfall_after_optional / new_months if new_months > 0 else remaining_shortfall_after_optional
                
                optional_sav = f"{optional_savings_total:,.0f}"
                prepaid_sav = f"{prepaid_savings_total:,.0f}"
                remaining_short = f"{remaining_shortfall_after_optional:,.0f}"
                monthly_credit = f"{monthly_credit_needed:,.0f}"
                avail_credit = f"{available_credit:,.0f}"
                
                analysis += f"""

                **Financial Strategy:**
                - Cut ALL optional: saves ${optional_sav}
                - Defer ALL prepaid: saves ${prepaid_sav}
                - Even with both cuts: **still short ${remaining_short}**
                - That's **${monthly_credit}/month** in credit card debt
                
                **Credit Risk Assessment:**
                - Total credit needed: ${remaining_short}
                - Your available credit: ${avail_credit}"""
                
                if available_credit >= remaining_shortfall_after_optional:
                    rec_optional = f"{optional:,.0f}"
                    rec_prepaid = f"{prepaid:,.0f}"
                    rec_credit = f"{monthly_credit_needed:,.0f}"
                    rec_available = f"{available_credit:,.0f}"
                    recommendation = f"⚠️ Even cutting all optional (${rec_optional}/mo) and deferring all prepaid (${rec_prepaid}/mo), you'd need ${rec_credit}/mo in credit card debt.\nYou have ${rec_available} available - enough to handle this scenario. Use credit as a bridge until you find employment."
                else:
                    shortfall_amount = remaining_shortfall_after_optional - available_credit
                    rec_credit = f"{monthly_credit_needed:,.0f}"
                    rec_available = f"{available_credit:,.0f}"
                    rec_short = f"{shortfall_amount:,.0f}"
                    recommendation = f"❌ **Critical:** Even with cuts, you'd need ${rec_credit}/mo in debt but only have ${rec_available} available credit. You'd be short ${rec_short}. Consider: (1) accelerating job search, (2) additional income source, or (3) larger expense cuts."
            else:
                # Can cover with expense cuts
                rec_optional = f"{optional:,.0f}"
                rec_fallback = f"⚠️ Cutting all optional (${rec_optional}/mo) covers the shortfall. Keep search focused on {new_months}-month timeline."
                recommendation = rec_fallback
            
            if not recommendation:
                context = f"Months: {new_months}, Monthly deficit: ${deficit:,.0f}, Optional savings: ${optional:,.0f}, Runway: {runway:.1f} months"
                recommendation = self._generate_recommendation_with_flan(
                    question=f"What if my job search takes {new_months} months?",
                    analysis=job_search_analysis,
                    intent=intent,
                    context=context
                )
            
            recommendation = self._sanitize_text(recommendation)
            
            return analysis, recommendation
        
        elif intent == 'savings_runway':
            monthly_deficit = calculations.get('monthly_deficit', 0)
            monthly_deficit_baseline = calculations.get('monthly_deficit_baseline', 0)
            runway = calculations.get('runway_months', 0)
            savings = calculations.get('savings', 0)
            
            # Get expense breakdown
            exp_breakdown = calculations.get('expense_breakdown', {})
            mandatory = exp_breakdown.get('mandatory', 0)
            negotiable = exp_breakdown.get('negotiable', 0)
            optional = exp_breakdown.get('optional', 0)
            prepaid = exp_breakdown.get('prepaid', 0)
            baseline_total = exp_breakdown.get('baseline_total', 0)
            total_with_optional = baseline_total + optional + prepaid
            
            military_income = current_profile.get('pension', 0) + current_profile.get('va_monthly', 0)
            
            # Calculate realistic DTI ratios
            essential_dti = self._calculate_debt_to_income(baseline_total, military_income)
            full_dti = self._calculate_debt_to_income(total_with_optional, military_income)
            
            if runway == float('inf'):
                analysis = f"""\u2705 **Your military income covers your expenses!** 
                
                - Monthly Income: ${military_income:,.0f}
                - Monthly Expenses: ${total_with_optional:,.0f}
                - **Surplus: ${military_income - total_with_optional:,.0f}/mo**
                
                **Debt-to-Income Ratio:**
                - Essential: {essential_dti['ratio']:.1f}% {essential_dti['status']}
                - Full: {full_dti['ratio']:.1f}%
                
                You don't need to draw on savings. Your military income is sustainable long-term.
                """
                context = f"Income: ${military_income:,.0f}, Expenses: ${total_with_optional:,.0f}, Essential DTI: {essential_dti['ratio']:.1f}%"
                rec_fallback = "You're in excellent financial position—no need to touch savings during transition."
            else:
                analysis = f"""
                **With ${savings:,.0f} in savings:**
                
                **Monthly Expenses Breakdown:**
                - Mandatory: ${mandatory:,.0f}
                - Negotiable: ${negotiable:,.0f}
                - Optional: ${optional:,.0f} (can cut)
                - Prepaid: ${prepaid:,.0f}
                - **Essential Baseline: ${baseline_total:,.0f}**
                - **With Optional: ${total_with_optional:,.0f}**
                
                **Debt-to-Income Ratio Analysis:**
                - Essential DTI: {essential_dti['ratio']:.1f}% {essential_dti['status']} ({essential_dti['assessment']})
                - Full DTI: {full_dti['ratio']:.1f}% (with optional/prepaid)
                
                **Runway at Military Income (${military_income:,.0f}/mo):**
                - Baseline only: {savings / monthly_deficit_baseline if monthly_deficit_baseline > 0 else float('inf'):.1f} months
                - Full spending: {runway:.1f} months
                
                **To extend runway:**
                - Cut optional: saves ${optional:,.0f}/mo (reduces DTI)
                - Defer prepaid: saves ${prepaid:,.0f}/mo
                - Cutting both restores sustainability
                """
                context = f"Savings: ${savings:,.0f}, Runway: {runway:.1f} months, Annual deficit: ${monthly_deficit*12:,.0f}, Essential DTI: {essential_dti['ratio']:.1f}%"
                rec_fallback = f"Plan employment within {runway:.0f} months. Cutting optional/prepaid improves DTI and extends runway significantly."
            
            # Generate recommendation using FLAN-T5
            recommendation = self._generate_recommendation_with_flan(
                question="How long can I live on my savings?",
                analysis=analysis,
                intent=intent,
                context=context
            )
            if not recommendation:
                recommendation = rec_fallback
            recommendation = self._sanitize_text(recommendation)
            
            return analysis, recommendation
        
        elif intent == 'savings_sufficiency':
            is_sufficient = calculations.get('is_sufficient', False)
            shortfall = calculations.get('shortfall', 0)
            savings = calculations.get('savings', 0)
            job_months = calculations.get('job_search_months', 6)
            deficit = calculations.get('monthly_deficit', 0)
            deficit_baseline = calculations.get('monthly_deficit_baseline', 0)
            
            # Get expense breakdown
            exp_breakdown = calculations.get('expense_breakdown', {})
            mandatory = exp_breakdown.get('mandatory', 0)
            negotiable = exp_breakdown.get('negotiable', 0)
            optional = exp_breakdown.get('optional', 0)
            prepaid = exp_breakdown.get('prepaid', 0)
            baseline_total = exp_breakdown.get('baseline_total', 0)
            total_with_optional = baseline_total + optional + prepaid
            
            military_income = current_profile.get('pension', 0) + current_profile.get('va_monthly', 0)
            
            # Calculate realistic DTI ratios
            essential_dti = self._calculate_debt_to_income(baseline_total, military_income)
            full_dti = self._calculate_debt_to_income(total_with_optional, military_income)
            
            if is_sufficient:
                total_needed_full = deficit * job_months
                total_needed_baseline = deficit_baseline * job_months
                buffer_with_optional = savings - total_needed_full
                buffer_baseline = savings - total_needed_baseline
                
                analysis = f"""
                ✅ **Yes, you have enough savings!**
                
                **For {job_months} months:**
                - Essential expenses only: ${total_needed_baseline:,.0f} needed → Buffer: ${buffer_baseline:,.0f} ✅
                - Full expenses: ${total_needed_full:,.0f} needed → Buffer: ${buffer_with_optional:,.0f}
                
                **Monthly Breakdown:**
                - Mandatory: ${mandatory:,.0f}
                - Negotiable: ${negotiable:,.0f}
                - Optional: ${optional:,.0f}
                - Prepaid: ${prepaid:,.0f}
                
                **Debt-to-Income Ratio Analysis:**
                - Essential DTI: {essential_dti['ratio']:.1f}% {essential_dti['status']}
                - Full DTI: {full_dti['ratio']:.1f}%
                
                Your savings provide a solid safety net. Your DTI is sustainable.
                """
                context = f"Savings: ${savings:,.0f}, Needed: ${total_needed_full:,.0f}, Buffer: ${buffer_with_optional:,.0f}, Essential DTI: {essential_dti['ratio']:.1f}%"
                rec_fallback = f"✅ You're set! You could even cut optional (${optional:,.0f}) and improve DTI further."
            else:
                total_needed = deficit * job_months
                cutting_optional = shortfall - optional if (shortfall - optional) > 0 else 0
                
                analysis = f"""
                ⚠️ **You would fall short by ${shortfall:,.0f} over {job_months} months.**
                
                **Monthly Breakdown:**
                - Mandatory: ${mandatory:,.0f}
                - Negotiable: ${negotiable:,.0f}
                - Optional: ${optional:,.0f} ← Can cut to save ${optional:,.0f}/mo
                - Prepaid: ${prepaid:,.0f} ← Can defer
                - **Essential Baseline: ${baseline_total:,.0f}**
                
                **Debt-to-Income Ratio Analysis:**
                - Essential DTI: {essential_dti['ratio']:.1f}% {essential_dti['status']} ({essential_dti['assessment']})
                - Full DTI: {full_dti['ratio']:.1f}%
                
                **If you cut optional spending:**
                - Monthly gap reduced from ${deficit:,.0f} to ${deficit_baseline:,.0f}
                - Shortfall reduced to ${cutting_optional:,.0f}
                - DTI improves to more sustainable level
                
                - Total needed for {job_months} months: ${total_needed:,.0f}
                - Your savings: ${savings:,.0f}
                """
                context = f"Shortfall: ${shortfall:,.0f}, Savings: ${savings:,.0f}, Essential DTI: {essential_dti['ratio']:.1f}%, Can cut: ${optional:,.0f}"
                rec_fallback = f"Cut optional (${optional:,.0f}/mo) or defer prepaid to eliminate shortfall and improve DTI."
            
            # Generate recommendation using FLAN-T5
            recommendation = self._generate_recommendation_with_flan(
                question="Do I have enough savings for this transition?",
                analysis=analysis,
                intent=intent,
                context=context
            )
            if not recommendation:
                recommendation = rec_fallback
            recommendation = self._sanitize_text(recommendation)
            return analysis, recommendation
        
        elif intent == 'expense_reduction':
            # Get expense breakdown
            exp_breakdown = calculations.get('expense_breakdown', {})
            mandatory = exp_breakdown.get('mandatory', 0)
            negotiable = exp_breakdown.get('negotiable', 0)
            optional = exp_breakdown.get('optional', 0)
            prepaid = exp_breakdown.get('prepaid', 0)
            baseline_total = exp_breakdown.get('baseline_total', 0)
            total_current = exp_breakdown.get('total', 0)
            
            # Get financial metrics
            military_income = current_profile.get('pension', 0) + current_profile.get('va_monthly', 0)
            civilian_income_monthly = current_profile.get('estimated_civilian_salary', 0) / 12
            total_income = military_income + civilian_income_monthly
            current_net = total_income - total_current
            
            # Check for multi-part category reductions (e.g., "reduce negotiable by $300 and mandatory by $600")
            has_multi_part = ('negotiable_reduction' in extracted_params or 
                             'mandatory_reduction' in extracted_params or 
                             'optional_reduction' in extracted_params or 
                             'prepaid_reduction' in extracted_params)
            
            # Check if user specified a specific reduction amount
            reduction_amount = extracted_params.get('reduction_amount', 0)
            
            if has_multi_part:
                # MULTI-PART REDUCTION with specific category cuts
                negotiable_reduction = extracted_params.get('negotiable_reduction', 0)
                mandatory_reduction = extracted_params.get('mandatory_reduction', 0)
                optional_reduction = extracted_params.get('optional_reduction', 0)
                prepaid_reduction = extracted_params.get('prepaid_reduction', 0)
                total_reduction = negotiable_reduction + mandatory_reduction + optional_reduction + prepaid_reduction
                
                # New category amounts
                negotiable_new = max(0, negotiable - negotiable_reduction)
                mandatory_new = max(0, mandatory - mandatory_reduction)
                optional_new = max(0, optional - optional_reduction)
                prepaid_new = max(0, prepaid - prepaid_reduction)
                
                new_total_expenses = negotiable_new + mandatory_new + optional_new + prepaid_new
                new_net_monthly = total_income - new_total_expenses
                monthly_improvement = new_net_monthly - current_net
                
                # Build multi-part breakdown
                reductions_str = []
                if negotiable_reduction > 0:
                    reductions_str.append(f"Negotiable: ${negotiable:,.0f} → ${negotiable_new:,.0f} (-${negotiable_reduction:,.0f})")
                if mandatory_reduction > 0:
                    reductions_str.append(f"Mandatory: ${mandatory:,.0f} → ${mandatory_new:,.0f} (-${mandatory_reduction:,.0f})")
                if optional_reduction > 0:
                    reductions_str.append(f"Optional: ${optional:,.0f} → ${optional_new:,.0f} (-${optional_reduction:,.0f})")
                if prepaid_reduction > 0:
                    reductions_str.append(f"Prepaid: ${prepaid:,.0f} → ${prepaid_new:,.0f} (-${prepaid_reduction:,.0f})")
                
                reductions_display = "\n".join(reductions_str)
                
                analysis = f"""
**Impact of multi-category expense reductions:**

**Current Expenses:**
- Negotiable: ${negotiable:,.0f}
- Mandatory: ${mandatory:,.0f}
- Optional: ${optional:,.0f}
- Prepaid: ${prepaid:,.0f}
- **Total: ${total_current:,.0f}**
- **Net Monthly: ${current_net:,.0f}**

**Proposed Category Changes:**
{reductions_display}

**After All Reductions:**
- New Total Expenses: ${new_total_expenses:,.0f}
- **New Net Monthly: ${new_net_monthly:,.0f}**
- **Monthly Improvement: +${monthly_improvement:,.2f}/month**

**Projected Savings:**
- 3 months: ${monthly_improvement * 3:,.2f}
- 6 months: ${monthly_improvement * 6:,.2f}
- 12 months: ${monthly_improvement * 12:,.2f}
"""
                
                if monthly_improvement > 0:
                    recommendation = f"✅ These reductions improve your cash flow by ${monthly_improvement:,.2f}/month, adding ${monthly_improvement * 6:,.0f} to your 6-month savings buffer."
                elif monthly_improvement < 0:
                    recommendation = f"⚠️ These reductions would reduce your cash flow by ${abs(monthly_improvement):,.2f}/month."
                else:
                    recommendation = f"These changes keep your monthly cash flow neutral at ${new_net_monthly:,.0f}/mo."
            
            elif reduction_amount > 0:
                # CALCULATE IMPACT OF EXPENSE REDUCTION
                # When user reduces expenses by $X, new expenses = current - $X
                # And new net income = total income - new expenses
                
                # Current state
                current_expenses = total_current
                current_net_monthly = total_income - current_expenses
                
                # After reduction
                reduced_expenses = current_expenses - reduction_amount  # SUBTRACT reduction from expenses
                new_net_monthly = total_income - reduced_expenses  # Higher expenses = lower net, Lower expenses = higher net
                
                # The improvement in monthly cash flow
                monthly_improvement = new_net_monthly - current_net_monthly  # Should be +$600
                
                analysis = f"""
**Impact of reducing monthly expenses by ${reduction_amount:,.2f}:**

**Current Financial Position:**
- Military Income: ${military_income:,.0f}/mo
- Civilian Income: ${civilian_income_monthly:,.0f}/mo
- **Total Income: ${total_income:,.0f}/mo**

**Monthly Expenses Breakdown:**
- Mandatory (keep): ${mandatory:,.0f}
- Negotiable (flexible): ${negotiable:,.0f}
- Optional (cut first): ${optional:,.0f}
- Prepaid (defer): ${prepaid:,.0f}
- **Current Total Expenses: ${current_expenses:,.0f}**
- **Current Net Monthly: ${current_net_monthly:,.0f}**

**After Reducing Expenses by ${reduction_amount:,.2f}:**
- New Total Expenses: ${reduced_expenses:,.0f}
- **New Net Monthly: ${new_net_monthly:,.0f}**
- **Monthly Improvement: +${monthly_improvement:,.2f}/month**

**Projected Savings:**
- 6 months: ${monthly_improvement * 6:,.2f}
- 12 months: ${monthly_improvement * 12:,.2f}
"""
                
                if monthly_improvement > 0:
                    # Generate more contextual recommendation about job search impact
                    baseline_deficit = mandatory + negotiable - military_income
                    
                    if baseline_deficit > 0:
                        # There's a deficit at essential spending - this reduction is critical
                        context = f"Monthly improvement: ${monthly_improvement:,.2f}. Baseline deficit: ${baseline_deficit:,.0f}. 6-month savings: ${monthly_improvement * 6:,.0f}. 12-month savings: ${monthly_improvement * 12:,.0f}."
                        
                        # Try FLAN-T5 generation first
                        recommendation = self._generate_recommendation_with_flan(
                            question=f"Reducing expenses by ${reduction_amount:,.0f}/month",
                            analysis=analysis,
                            intent=intent,
                            context=context
                        )
                        
                        # Fall back to hand-crafted if FLAN-T5 fails
                        if not recommendation:
                            if monthly_improvement >= baseline_deficit:
                                recommendation = f"✅ **Critical impact:** Reducing expenses by ${reduction_amount:,.2f}/month covers your essential spending gap. You can now sustain yourself on military+VA income alone."
                            else:
                                months_of_runway_gained = (reduction_amount * 12) / baseline_deficit if baseline_deficit > 0 else 0
                                recommendation = f"✅ Reducing expenses by ${reduction_amount:,.2f}/month helps bridge your deficit. This extends your job search runway by ~{months_of_runway_gained:.1f} months."
                    else:
                        # No deficit - this is additional savings/flexibility
                        context = f"Monthly improvement: ${monthly_improvement:,.2f}. Annual savings: ${monthly_improvement * 12:,.0f}. New monthly cash flow: ${new_net_monthly:,.0f}."
                        
                        # Try FLAN-T5 generation
                        recommendation = self._generate_recommendation_with_flan(
                            question=f"Reducing expenses by ${reduction_amount:,.0f}/month",
                            analysis=analysis,
                            intent=intent,
                            context=context
                        )
                        
                        # Fall back to hand-crafted if FLAN-T5 fails
                        if not recommendation:
                            savings_total = monthly_improvement * 12
                            recommendation = f"✅ Reducing expenses by ${reduction_amount:,.2f}/month adds ${savings_total:,.0f} to your annual savings buffer."
                elif monthly_improvement < 0:
                    recommendation = f"❌ This would actually worsen your position by ${abs(monthly_improvement):,.2f}/month."
                else:
                    recommendation = f"Your cash flow remains at ${new_net_monthly:,.0f}/month."
            
            else:
                # Generic response when no specific amount mentioned
                # Fixed reduction plan
                new_total_after_cuts = mandatory + negotiable
                monthly_savings_amount = optional + prepaid
                
                analysis = f"""
**Reducing expenses:**

**Current Monthly Spending:**
- Mandatory (keep): ${mandatory:,.0f}
- Negotiable (flexible): ${negotiable:,.0f}
- Optional (cut first): ${optional:,.0f} ← Easiest to reduce
- Prepaid (defer): ${prepaid:,.0f} ← Can postpone
- **Current Total: ${total_current:,.0f}**
- **Current Net Monthly: ${current_net:,.0f}**

**Priority Reduction Strategies:**
1. **Cut all optional:** Save ${optional:,.0f}/mo instantly
2. **Defer prepaid items:** Save ${prepaid:,.0f}/mo
3. **Reduce negotiable:** Find 10-20% savings in groceries, utilities
4. **Keep mandatory:** Housing & insurance aren't negotiable

**If you cut optional & defer prepaid:**
- New monthly: ${new_total_after_cuts:,.0f}
- New net monthly: ${total_income - new_total_after_cuts:,.0f}
- Monthly savings: ${monthly_savings_amount:,.0f}
- Over 6 months: ${monthly_savings_amount * 6:,.0f}
"""
                recommendation = f"Start by eliminating optional (${optional:,.0f}) and deferring prepaid (${prepaid:,.0f}). This saves ${monthly_savings_amount:,.0f} per month. This gives breathing room."
            
            return analysis, recommendation
        
        
        else:
            analysis = "I couldn't parse that scenario question. Try asking about:"
            recommendation = """
            - "What if my job search takes 9 months?"
            - "What if I use the GI Bill for a master's?"
            - "How many months can I cover with my savings?"
            - "What if I had zero savings going in?"
            - "What if I cut my optional spending?"
            """
            
            # Ensure recommendation text is clean (no embedded newlines)
            recommendation = self._sanitize_text(recommendation)
            return analysis, recommendation
    
    def _generate_recommendation_with_flan(self, question: str, analysis: str, intent: str, context: str = "") -> str:
        """
        Use FLAN-T5 to generate recommendation text.
        
        Prompt T5 to create natural language recommendation based on:
        - Original user question
        - Financial analysis performed
        - Scenario intent
        - Optional context (calculations, numbers, etc.)
        
        Returns clean, model-generated recommendation text.
        If T5 unavailable, returns None for fallback to hand-crafted text.
        """
        if not self.flan_t5 or not self.flan_t5.is_available():
            return None  # Fall back to hand-crafted if T5 not available
        
        try:
            # Create prompt specifically designed for recommendation generation
            prompt = f"""Based on this financial analysis:

{analysis}

The user asked: {question}

{f"Context: {context}" if context else ""}

Generate a brief, actionable recommendation (1-2 sentences, under 150 words). 
Start with ✅ if positive, ⚠️ if cautionary, or ❌ if critical:"""
            
            # Generate with FLAN-T5
            recommendation = self.flan_t5.generate(prompt, max_length=150)
            
            if recommendation:
                logger.info(f"✅ [MILESTONE C] Generated recommendation with FLAN-T5: {recommendation[:80]}")
                return self._sanitize_text(recommendation)
            else:
                logger.warning("[MILESTONE C] FLAN-T5 returned empty recommendation")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to generate with FLAN-T5: {e}. Using fallback.")
            return None
    
    def _sanitize_text(self, text: str) -> str:
        """Remove embedded newlines and collapse multiple spaces for text display."""
        if not isinstance(text, str):
            return str(text) if text else ""
        # Remove all newlines and carriage returns, then collapse multiple spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Collapse multiple whitespaces into single
        return text

