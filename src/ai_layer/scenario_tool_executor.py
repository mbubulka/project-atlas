"""
Scenario Tool Executor - Orchestrates multi-step scenario analysis.

Enables FLAN-T5 planning to be executed:
1. Extract parameters from natural language (e.g., degree type, location)
2. Call wizard tools/calculators to compute intermediate values (e.g., GI Bill BAH)
3. Integrate results into financial calculations

This bridges FLAN-T5 intent detection with actual modeling tools.
"""

import logging
import re
import sys
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import tax calculator for VA disability scenarios
try:
    from src.model_layer.tax_calculator import calculate_net_income
except ImportError:
    # Fallback for different import paths
    try:
        from model_layer.tax_calculator import calculate_net_income
    except ImportError:
        calculate_net_income = None


class ScenarioToolExecutor:
    """
    Executes multi-step scenario analysis plans created by FLAN-T5.
    
    Methods for each tool type:
    - extract_*: Extract parameters from user question using pattern matching + AI hints
    - calculate_*: Call existing calculators and model functions
    - recalculate_*: Recompute financial scenarios with new parameters
    """
    
    def execute_plan(
        self,
        tool_plan: dict,
        current_profile: Dict[str, Any],
        question: str,
        intent: str = 'unknown'
    ) -> Dict[str, Any]:
        """
        Execute a multi-step tool plan.
        
        Args:
            tool_plan: Dict returned by FlanT5Loader.plan_scenario_steps()
            current_profile: User's full financial profile from wizard
            question: Original user question
            intent: Detected intent (used when tool_plan is empty)
        
        Returns:
            Dict with:
            - intent: str
            - extracted_params: Dict of parameters extracted and computed
            - analysis: str (ready for display)
            - calculations: Dict of numerical values
        """
        result = {
            'intent': tool_plan.get('intent', intent),
            'extracted_params': {},
            'analysis': '',
            'calculations': {},
            'tool_execution_log': []
        }
        
        try:
            # If tool_plan is empty but we have a known intent, auto-generate the steps
            steps = tool_plan.get('steps', [])
            if not steps and intent in ['gi_bill', 'expense_reduction', 'job_search_timeline', 'savings_runway', 'savings_sufficiency', 'va_disability']:
                logger.info(f"🔄 Auto-generating tool plan for intent: {intent}")
                
                if intent == 'gi_bill':
                    steps = [
                        {'tool': 'extract_education_params', 'params': {}},
                        {'tool': 'calculate_gi_bill_bah', 'params': {}},
                    ]
                elif intent == 'expense_reduction':
                    steps = [
                        {'tool': 'extract_expense_reduction_params', 'params': {}},
                    ]
                elif intent == 'job_search_timeline':
                    steps = [
                        {'tool': 'extract_timeline_params', 'params': {}},
                    ]
                elif intent == 'va_disability':
                    steps = [
                        {'tool': 'extract_va_disability_params', 'params': {}},
                        {'tool': 'recalculate_va_scenario', 'params': {}},
                    ]
                # For savings_runway and savings_sufficiency, we use what's in profile already
                logger.info(f"✅ Generated {len(steps)} automatic steps for {intent}")
            
            for step in steps:
                tool_name = step['tool']
                step_params = step.get('params', {})
                
                logger.info(f"Executing tool: {tool_name}")
                
                # Route to appropriate handler
                if tool_name == 'extract_education_params':
                    params = self.extract_education_params(question, current_profile)
                    result['extracted_params'].update(params)
                    result['tool_execution_log'].append(f"✓ Extracted education: {params}")
                
                elif tool_name == 'calculate_gi_bill_bah':
                    bah = self.calculate_gi_bill_bah(
                        result['extracted_params'],
                        current_profile
                    )
                    result['extracted_params']['gi_bill_bah'] = bah
                    result['tool_execution_log'].append(f"✓ Computed BAH: ${bah:,.0f}/mo")
                
                elif tool_name == 'extract_timeline_params':
                    params = self.extract_timeline_params(question)
                    result['extracted_params'].update(params)
                    result['tool_execution_log'].append(f"✓ Extracted timeline: {params}")
                
                elif tool_name == 'extract_va_disability_params':
                    params = self.extract_va_disability_params(question)
                    result['extracted_params'].update(params)
                    result['tool_execution_log'].append(f"✓ Extracted VA disability rating: {params}")
                
                elif tool_name == 'recalculate_va_scenario':
                    calcs = self.recalculate_va_scenario(
                        current_profile,
                        result['extracted_params']
                    )
                    result['calculations'].update(calcs)
                    result['tool_execution_log'].append(f"✓ Recalculated VA disability scenario")
                
                elif tool_name == 'extract_expense_reduction_params':
                    params = self.extract_expense_reduction_params(question)
                    result['extracted_params'].update(params)
                    result['tool_execution_log'].append(f"✓ Extracted expense reduction: {params}")
                
                elif tool_name == 'recalculate_financial_scenario':
                    calcs = self.recalculate_financial_scenario(
                        current_profile,
                        result['extracted_params'],
                        tool_plan['intent']
                    )
                    result['calculations'].update(calcs)
                    result['tool_execution_log'].append(f"✓ Recalculated scenario")
            
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def extract_education_params(
        self,
        question: str,
        current_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract education parameters from question.
        
        Examples:
        - "What if I do a master's degree?" → {'degree': 'masters', 'location': 'current'}
        - "What if I go to school in Colorado?" → {'degree': 'bachelors', 'location': 'Colorado'}
        
        Returns:
            Dict with keys: degree, location, program (if detectable)
        """
        q_lower = question.lower()
        params = {}
        
        # Detect degree level
        if any(word in q_lower for word in ["master", "master's", "masters", "grad", "graduate"]):
            params['degree'] = 'master'
        elif any(word in q_lower for word in ["phd", "doctorate", "doctoral"]):
            params['degree'] = 'doctorate'
        elif any(word in q_lower for word in ["associate", "associates"]):
            params['degree'] = 'associate'
        else:
            params['degree'] = 'bachelor'  # default
        
        # Detect location
        location_match = re.search(r'in\s+(\w+(?:\s+\w+)?)', q_lower)
        if location_match:
            params['location'] = location_match.group(1).title()
        else:
            # Use current location from profile
            params['location'] = current_profile.get('user_locality', 'Current location')
        
        # Detect program type
        programs = ['engineering', 'business', 'nursing', 'education', 'computer science', 'technology']
        for program in programs:
            if program in q_lower:
                params['program'] = program.title()
                break
        
        return params
    
    def extract_timeline_params(self, question: str) -> Dict[str, Any]:
        """
        Extract job search timeline from question.
        
        Examples:
        - "What if it takes 9 months?" → {'job_search_months': 9}
        - "What if I take 6 more months?" → {'additional_months': 6}
        """
        params = {}
        
        # Look for numbers followed by 'month'
        number_match = re.search(r'(\d+)\s*month', question.lower())
        if number_match:
            months = int(number_match.group(1))
            if 'additional' in question.lower() or 'more' in question.lower():
                params['additional_months'] = months
            else:
                params['job_search_months'] = months
        
        return params
    
    def extract_va_disability_params(self, question: str) -> Dict[str, Any]:
        """
        Extract VA disability rating from question.
        
        Examples:
        - "What if my VA disability is 50%?" → {'va_disability_rating': 50}
        - "What if I had 30% VA rating?" → {'va_disability_rating': 30}
        - "VA disability 20%" → {'va_disability_rating': 20}
        - "higher at 50" → {'va_disability_rating': 50}
        """
        params = {}
        
        # Look for numbers followed by % or 'percent'
        rating_match = re.search(r'(\d+)\s*%', question.lower())
        if not rating_match:
            rating_match = re.search(r'(\d+)\s*percent', question.lower())
        
        # As fallback, look for standalone numbers between 0-100 in VA context
        if not rating_match:
            all_numbers = re.findall(r'(\d+)', question.lower())
            for num_str in all_numbers:
                rating = int(num_str)
                if 0 <= rating <= 100:
                    rating_match = type('Match', (), {'group': lambda self, i: num_str})()
                    break
        
        if rating_match:
            rating = int(rating_match.group(1))
            # Ensure rating is between 0 and 100
            if 0 <= rating <= 100:
                params['va_disability_rating'] = rating
        
        return params
    
    def extract_expense_reduction_params(self, question: str) -> Dict[str, Any]:
        """
        Extract expense reduction amounts from question - supports MULTI-PART questions.
        
        Examples:
        - "What if I lowered my home equity loan by 600?" → {'reduction_amount': 600}
        - "Reduce negotiable by $300 and mandatory by $600" → {'negotiable_reduction': 300, 'mandatory_reduction': 600}
        - "Can I save 500 a month?" → {'reduction_amount': 500}
        """
        params = {}
        question_lower = question.lower()
        
        # Expense categories to track
        categories = {
            'negotiable': ['negotiable', 'discretionary', 'flexible', 'entertainment', 'dining'],
            'mandatory': ['mandatory', 'essential', 'housing', 'utilities', 'food', 'groceries'],
            'optional': ['optional', 'luxury', 'subscriptions'],
            'prepaid': ['prepaid', 'insurance', 'renewal', 'annual']
        }
        
        # IMPROVED: Handle "Reduce negotiable by $300 and mandatory by $600"
        # Pattern: [category] by [amount] - works with leading reduce/cut/lower verb
        improved_pattern = r'(\w+)\s+(?:by|to|of)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\b'
        
        found_reductions = {}
        
        # First, try to find category-specific patterns with verb prefix
        # Pattern: "reduce [category] by $300"
        specific_patterns = [
            r'(?:reduce|cut|lower|trim)\s+(\w+)\s+(?:by\s*)?\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\w+)\s+(?:by\s*)?\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:reduction|cut|lower)',
        ]
        
        for pattern in specific_patterns:
            matches = re.finditer(pattern, question_lower)
            for match in matches:
                category_word = match.group(1).lower()
                amount_str = match.group(2).replace(',', '')
                amount = float(amount_str)
                
                # Find which category this belongs to
                for category, keywords in categories.items():
                    if category_word in keywords or any(kw in category_word for kw in keywords):
                        found_reductions[f"{category}_reduction"] = amount
                        break
        
        # If we didn't find specific categories, try looking for patterns like "negotiable by 300 and mandatory by 600"
        # Split on 'and' and try to parse each segment
        if not found_reductions and ' and ' in question_lower:
            parts = question_lower.split(' and ')
            for part in parts:
                # For each part, look for category name + amount
                found_in_this_part = False
                for category, keywords in categories.items():
                    # Check if this part mentions the category
                    for keyword in keywords:
                        if keyword in part:
                            # Now extract the amount from this part
                            amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', part)
                            if amount_match:
                                amount = float(amount_match.group(1).replace(',', ''))
                                found_reductions[f"{category}_reduction"] = amount
                                found_in_this_part = True
                            break
                    if found_in_this_part:
                        break
        
        # If we found category-specific reductions, return them all (MULTI-PART support)
        if found_reductions:
            params.update(found_reductions)
            # Set total_reduction for compatibility
            params['total_reduction'] = sum(found_reductions.values())
            return params
        
        # Fallback: Look for generic currency amounts (single amount or multiple)
        # This handles "reduce by 300 and 600" → both amounts
        all_amounts = re.findall(r'(?:by|save|lower|reduce|cut|reduce by)\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', question_lower)
        if all_amounts:
            # If multiple amounts found, attribute first to negotiable, second to mandatory, etc.
            amount_values = [float(a.replace(',', '')) for a in all_amounts]
            if len(amount_values) >= 2:
                # Multi-part question detected
                params['negotiable_reduction'] = amount_values[0]
                params['mandatory_reduction'] = amount_values[1]
                params['total_reduction'] = sum(amount_values)
            elif len(amount_values) == 1:
                params['reduction_amount'] = amount_values[0]
            return params
        
        # Also try simple dollar amounts alone
        dollar_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', question_lower)
        if dollar_matches:
            amount_values = [float(m.replace(',', '')) for m in dollar_matches]
            if len(amount_values) >= 2:
                # Multi-part question detected
                params['negotiable_reduction'] = amount_values[0]
                params['mandatory_reduction'] = amount_values[1]
                params['total_reduction'] = sum(amount_values)
            elif len(amount_values) == 1:
                params['reduction_amount'] = amount_values[0]
        
        return params
    
    def calculate_gi_bill_bah(
        self,
        extracted_params: Dict[str, Any],
        current_profile: Dict[str, Any]
    ) -> float:
        """
        Calculate GI Bill Basic Allowance for Housing (BAH).
        
        Uses more accurate BAH rates for military locations.
        Rates are approximate based on 2024-2025 VA BAH schedules.
        
        In a full implementation, this would:
        1. Look up exact zip code BAH rates from VA
        2. Account for rank and marital status
        3. Account for degree level (may affect BAH)
        
        Returns:
            Monthly BAH amount in dollars
        """
        
        # Check if already calculated in profile (from Step 2C)
        if current_profile.get('gi_bill_bah_monthly', 0) > 0:
            return current_profile.get('gi_bill_bah_monthly')
        
        # Get location from extracted params or profile
        location = extracted_params.get('location', 'average').lower()
        
        # Actual BAH rates for major military areas (E5 with dependent)
        # Source: Approximate VA BAH 2024-2025 rates
        bah_lookup = {
            'arlington': 2100,          # Arlington, VA (DC area)
            'virginia': 2000,           # General Virginia
            'washington dc': 2100,      # Washington, DC area
            'dc': 2100,
            'california': 1900,         # California average
            'san diego': 1850,          # San Diego, CA
            'san francisco': 2200,      # San Francisco, CA
            'los angeles': 1800,        # Los Angeles, CA
            'texas': 1400,              # Texas average
            'austin': 1500,             # Austin, TX
            'houston': 1400,            # Houston, TX
            'san antonio': 1350,        # San Antonio, TX
            'colorado': 1500,           # Colorado average
            'denver': 1500,             # Denver, CO
            'colorado springs': 1450,   # Colorado Springs, CO
            'north carolina': 1300,     # North Carolina average
            'fort bragg': 1350,         # Fort Bragg (Bragg), NC
            'fort liberty': 1350,       # Fort Liberty, NC
            'georgia': 1350,            # Georgia average
            'fort moore': 1350,         # Fort Moore, GA
            'florida': 1400,            # Florida average
            'jacksonville': 1400,       # Jacksonville, FL
            'base': 1350,               # Generic military base
            'average': 1400             # National average
        }
        
        # Check for exact location match
        for key in bah_lookup:
            if key in location:
                return bah_lookup[key]
        
        # Check for state abbreviations
        state_bah = {
            'va': 2000,
            'ca': 1900,
            'tx': 1400,
            'co': 1500,
            'nc': 1300,
            'ga': 1350,
            'fl': 1400,
            'ny': 2000
        }
        
        user_state = current_profile.get('user_state', '').lower()
        if user_state in state_bah:
            return state_bah[user_state]
        
        # Default fallback
        return bah_lookup['average']
    
    def recalculate_financial_scenario(
        self,
        current_profile: Dict[str, Any],
        extracted_params: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """
        Recalculate financial scenario with extracted parameters.
        
        This is the core calculation that uses the tools' outputs.
        Handles different intents and parameters.
        """
        
        calculations = {}
        
        # Base income and expenses
        pension = current_profile.get('pension', 0)
        va_monthly = current_profile.get('va_monthly', 0)
        civilian_salary_annual = current_profile.get('estimated_civilian_salary', 0)
        
        # Expense breakdown
        mandatory = current_profile.get('csv_mandatory_expenses', 0)
        negotiable = current_profile.get('csv_negotiable_expenses', 0)
        optional = current_profile.get('csv_optional_expenses', 0)
        prepaid = current_profile.get('adjusted_prepaid_monthly', 0)
        
        # Intelligent expense categorization
        # DEFAULT: Only mandatory + negotiable (essential expenses)
        # Only include optional/prepaid if scenario specifically mentions them
        baseline_expenses = mandatory + negotiable  # These are essential
        optional_available = optional + prepaid    # These are negotiable/committed
        
        # For most scenarios, use baseline (essential) expenses
        total_expenses = baseline_expenses
        
        # Special handling based on intent
        if intent == 'expense_reduction':
            # Expense reduction scenario: User cutting optional
            total_expenses = baseline_expenses + optional_available
            # Will be reduced based on extracted params
        elif intent == 'gi_bill':
            # GI Bill: User is in school, likely continuing all regular expenses
            # But let them know they could cut optional
            total_expenses = baseline_expenses + optional_available
        elif intent == 'job_search_timeline':
            # Job search: User may reduce discretionary spending
            # Use baseline initially, note that optional is available to cut
            total_expenses = baseline_expenses + optional_available
        elif intent == 'savings_runway' or intent == 'savings_sufficiency':
            # Savings questions: Show with full expenses to be conservative
            total_expenses = baseline_expenses + optional_available
        
        savings = current_profile.get('current_savings', 0)
        
        # GI Bill scenario - add BAH to income
        if intent == 'gi_bill':
            bah = extracted_params.get('gi_bill_bah', 0)
            income_with_bah = pension + va_monthly + bah
            
            # Calculate both with and without optional spending
            deficit_with_optional = max(0, total_expenses - income_with_bah)
            deficit_baseline_only = max(0, baseline_expenses - income_with_bah)
            
            calculations.update({
                'gi_bill_bah': bah,
                'income_with_bah': income_with_bah,
                'monthly_deficit_with_full_spending': deficit_with_optional,
                'monthly_deficit_essential_only': deficit_baseline_only,
                'savings_benefit': bah * current_profile.get('job_search_timeline_months', 6),
                'income_comparison': {
                    'without_bah': pension + va_monthly,
                    'with_bah': income_with_bah,
                    'bah_boost': bah
                },
                'expense_breakdown': {
                    'mandatory': mandatory,
                    'negotiable': negotiable,
                    'optional': optional,
                    'prepaid': prepaid,
                    'baseline_total': baseline_expenses,
                    'with_optional_total': total_expenses
                }
            })
        
        # Job search timeline scenario - update runway
        elif intent == 'job_search_timeline':
            job_months = extracted_params.get('job_search_months',
                                             current_profile.get('job_search_timeline_months', 6))
            
            military_income = pension + va_monthly
            monthly_deficit = max(0, total_expenses - military_income)
            monthly_deficit_baseline = max(0, baseline_expenses - military_income)
            total_deficit = monthly_deficit * job_months
            runway = savings / monthly_deficit if monthly_deficit > 0 else float('inf')
            
            calculations.update({
                'job_search_months': job_months,
                'monthly_deficit': monthly_deficit,
                'monthly_deficit_baseline': monthly_deficit_baseline,
                'total_deficit': total_deficit,
                'runway_months': runway,
                'savings': savings,
                'is_sufficient': savings >= total_deficit,
                'shortfall': max(0, total_deficit - savings),
                'expense_breakdown': {
                    'mandatory': mandatory,
                    'negotiable': negotiable,
                    'optional': optional,
                    'prepaid': prepaid,
                    'baseline_total': baseline_expenses,
                    'with_optional_total': total_expenses
                }
            })
        
        # Savings runway/sufficiency
        elif intent in ['savings_runway', 'savings_sufficiency']:
            military_income = pension + va_monthly
            monthly_deficit = max(0, total_expenses - military_income)
            monthly_deficit_baseline = max(0, baseline_expenses - military_income)
            runway = savings / monthly_deficit if monthly_deficit > 0 else float('inf')
            job_months = current_profile.get('job_search_timeline_months', 6)
            total_deficit = monthly_deficit * job_months
            
            calculations.update({
                'monthly_deficit': monthly_deficit,
                'monthly_deficit_baseline': monthly_deficit_baseline,
                'runway_months': runway,
                'savings': savings,
                'job_search_months': job_months,
                'total_deficit': total_deficit,
                'is_sufficient': savings >= total_deficit,
                'shortfall': max(0, total_deficit - savings),
                'expense_breakdown': {
                    'mandatory': mandatory,
                    'negotiable': negotiable,
                    'optional': optional,
                    'prepaid': prepaid,
                    'baseline_total': baseline_expenses,
                    'with_optional_total': total_expenses
                }
            })
        
        # Expense reduction (supports MULTI-PART questions like "reduce negotiable by $300 and mandatory by $600")
        elif intent == 'expense_reduction':
            military_income = pension + va_monthly
            
            # Check for specific category reductions (multi-part support)
            if 'negotiable_reduction' in extracted_params or 'mandatory_reduction' in extracted_params or 'optional_reduction' in extracted_params or 'prepaid_reduction' in extracted_params:
                # Multi-part reduction: Apply specific reductions to each category
                negotiable_reduced = max(0, negotiable - extracted_params.get('negotiable_reduction', 0))
                mandatory_reduced = max(0, mandatory - extracted_params.get('mandatory_reduction', 0))
                optional_reduced = max(0, optional - extracted_params.get('optional_reduction', 0))
                prepaid_reduced = max(0, prepaid - extracted_params.get('prepaid_reduction', 0))
                
                new_expenses = negotiable_reduced + mandatory_reduced + optional_reduced + prepaid_reduced
                new_baseline = mandatory_reduced + negotiable_reduced
                
                total_reduction = (negotiable - negotiable_reduced) + (mandatory - mandatory_reduced) + \
                                 (optional - optional_reduced) + (prepaid - prepaid_reduced)
                
            elif 'reduction_amount' in extracted_params:
                # Single amount reduction: Apply to optional first, then prepaid, then negotiable
                reduction_amount = extracted_params.get('reduction_amount', 0)
                optional_reduced = max(0, optional - reduction_amount)
                remaining = reduction_amount - (optional - optional_reduced)
                prepaid_reduced = max(0, prepaid - remaining) if remaining > 0 else prepaid
                remaining -= (prepaid - prepaid_reduced)
                negotiable_reduced = max(0, negotiable - remaining) if remaining > 0 else negotiable
                mandatory_reduced = mandatory
                
                new_expenses = negotiable_reduced + mandatory_reduced + optional_reduced + prepaid_reduced
                new_baseline = mandatory_reduced + negotiable_reduced
                total_reduction = reduction_amount
                
            else:
                # Default: Use 10% reduction
                reduction_percent = extracted_params.get('reduction_percent', 0.1)
                new_expenses = total_expenses * (1 - reduction_percent)
                new_baseline = baseline_expenses * (1 - reduction_percent)
                negotiable_reduced = negotiable * (1 - reduction_percent)
                mandatory_reduced = mandatory * (1 - reduction_percent)
                optional_reduced = optional * (1 - reduction_percent)
                prepaid_reduced = prepaid * (1 - reduction_percent)
                total_reduction = total_expenses - new_expenses
            
            new_deficit = max(0, new_expenses - military_income)
            old_deficit = max(0, total_expenses - military_income)
            
            calculations.update({
                'original_expenses': total_expenses,
                'reduced_expenses': new_expenses,
                'expense_reduction': total_reduction,
                'original_deficit': old_deficit,
                'new_deficit': new_deficit,
                'monthly_savings': old_deficit - new_deficit,
                'category_reductions': {
                    'mandatory_reduced': mandatory_reduced,
                    'negotiable_reduced': negotiable_reduced,
                    'optional_reduced': optional_reduced,
                    'prepaid_reduced': prepaid_reduced,
                },
                'expense_breakdown': {
                    'mandatory': mandatory,
                    'negotiable': negotiable,
                    'optional': optional,
                    'prepaid': prepaid,
                    'baseline_total': baseline_expenses,
                    'with_optional_total': total_expenses
                }
            })
        
        return calculations
    
    def recalculate_va_scenario(
        self,
        current_profile: Dict[str, Any],
        extracted_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recalculate financial impact of VA disability rating change.
        
        Args:
            current_profile: User's current financial profile
            extracted_params: {'va_disability_rating': new_rating}
        
        Returns:
            Dict with current/new calculations and delta analysis
        """
        
        calculations = {}
        
        try:
            if calculate_net_income is None:
                return {
                    'error': 'Tax calculator not available',
                    'analysis': 'Unable to calculate VA disability impact'
                }
            
            # Get current VA rating and new rating
            current_va_rating = current_profile.get('va_disability_rating', 0)
            new_va_rating = extracted_params.get('va_disability_rating', current_va_rating)
            
            # Get pension and other income info
            annual_pension_gross = current_profile.get('pension_annual_gross', 0)
            if not annual_pension_gross and 'pension' in current_profile:
                # Convert monthly to annual if needed
                pension_monthly = current_profile.get('pension', 0)
                annual_pension_gross = pension_monthly * 12
            
            filing_status = current_profile.get('filing_status', 'married')
            state = current_profile.get('state', 'VA')
            sbp_annual = (current_profile.get('sbp_monthly_cost', 0) * 12) if current_profile.get('sbp_monthly_cost') else 0
            
            # Calculate CURRENT scenario
            current_result = calculate_net_income(
                annual_pension_gross=annual_pension_gross,
                va_disability_rating=current_va_rating,
                filing_status=filing_status,
                state=state,
                sbp_annual=sbp_annual
            )
            
            # Calculate NEW scenario
            new_result = calculate_net_income(
                annual_pension_gross=annual_pension_gross,
                va_disability_rating=new_va_rating,
                filing_status=filing_status,
                state=state,
                sbp_annual=sbp_annual
            )
            
            current_take_home = current_result.get('netIncome', 0) / 12  # Convert to monthly
            new_take_home = new_result.get('netIncome', 0) / 12
            
            current_federal_tax = current_result.get('federal_tax', 0) / 12
            new_federal_tax = new_result.get('federal_tax', 0) / 12
            
            current_state_tax = current_result.get('state_tax', 0) / 12
            new_state_tax = new_result.get('state_tax', 0) / 12
            
            # VA disability amount (tax-free)
            current_va_monthly = current_profile.get('va_monthly_amount', 0)
            # Estimated new VA amount (rough estimate: 10% increase per rating increase if available)
            # For now, we'll note that VA amount depends on rating but keep current value as baseline
            new_va_monthly = current_va_monthly  # In reality, VA amount changes with rating
            
            # Calculate deltas
            delta_take_home = new_take_home - current_take_home
            delta_federal_tax = new_federal_tax - current_federal_tax
            delta_state_tax = new_state_tax - current_state_tax
            delta_monthly_income = delta_take_home  # Pension take-home change
            
            # Annual impact
            delta_annual = delta_take_home * 12
            
            calculations.update({
                'current_va_rating': current_va_rating,
                'new_va_rating': new_va_rating,
                'current_pension_take_home_monthly': current_take_home,
                'new_pension_take_home_monthly': new_take_home,
                'delta_pension_take_home_monthly': delta_take_home,
                'delta_pension_take_home_annual': delta_annual,
                'current_federal_tax_monthly': current_federal_tax,
                'new_federal_tax_monthly': new_federal_tax,
                'delta_federal_tax_monthly': delta_federal_tax,
                'current_state_tax_monthly': current_state_tax,
                'new_state_tax_monthly': new_state_tax,
                'delta_state_tax_monthly': delta_state_tax,
                'current_va_monthly': current_va_monthly,
                'new_va_monthly': new_va_monthly,
            })
            
        except Exception as e:
            logger.error(f"Error recalculating VA scenario: {str(e)}")
            calculations['error'] = str(e)
        
        return calculations
