"""
AI Scenario State Manager - Manages temporary and saved scenario states for comparison.

Enables:
1. Creating temp scenario profiles from AI analysis results
2. Preserving baseline profile for comparison
3. Generating delta statements ("X better than baseline")
4. Auto-saving AI-analyzed scenarios for comparison
"""

import logging
from copy import deepcopy
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIScenarioStateManager:
    """
    Manages scenario state during AI analysis.
    
    Responsibilities:
    - Create isolated temp profiles from AI extraction results
    - Preserve baseline for comparison
    - Track baseline vs analyzed delta
    - Generate comparison narratives
    """
    
    @staticmethod
    def create_temp_analyzed_profile(
        baseline_profile: Dict[str, Any],
        extracted_params: Dict[str, Any],
        calculations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a modified profile with AI-extracted parameters applied.
        
        Does NOT mutate baseline_profile.
        
        Args:
            baseline_profile: Original user profile (read-only)
            extracted_params: Parameters extracted by AI (e.g., job_search_months=9)
            calculations: Computed values from scenario analysis
        
        Returns:
            New dict representing the analyzed scenario (safe for comparison)
        """
        # Deep copy to avoid any reference sharing
        analyzed_profile = deepcopy(baseline_profile)
        
        # Apply extracted parameters
        # These override baseline values
        if 'job_search_timeline_months' in extracted_params:
            analyzed_profile['job_search_timeline_months'] = extracted_params['job_search_timeline_months']
        
        if 'gi_bill_bah_monthly' in extracted_params:
            analyzed_profile['gi_bill_bah_monthly'] = extracted_params['gi_bill_bah_monthly']
        
        if 'expense_reduction' in extracted_params:
            # Apply expense reduction to optional spending
            reduction = extracted_params['expense_reduction']
            if 'csv_optional_expenses' in analyzed_profile:
                analyzed_profile['csv_optional_expenses'] = max(
                    0,
                    analyzed_profile['csv_optional_expenses'] - reduction
                )
        
        if 'negotiable_reduction' in extracted_params:
            # Apply reduction to negotiable expenses
            reduction = extracted_params['negotiable_reduction']
            if 'csv_negotiable_expenses' in analyzed_profile:
                analyzed_profile['csv_negotiable_expenses'] = max(
                    0,
                    analyzed_profile['csv_negotiable_expenses'] - reduction
                )
        
        # Store calculations as metadata for later comparison
        analyzed_profile['_ai_analysis'] = {
            'extracted_params': extracted_params,
            'calculations': calculations,
            'is_temp_from_ai': True
        }
        
        logger.info(f"✅ Created temp analyzed profile with {len(extracted_params)} parameters")
        
        return analyzed_profile
    
    @staticmethod
    def generate_comparison_statement(
        baseline_profile: Dict[str, Any],
        analyzed_profile: Dict[str, Any],
        intent: str,
        question: str
    ) -> str:
        """
        Generate a comparison statement between baseline and analyzed profile.
        
        Examples:
        - "This scenario extends your runway by 2 months vs baseline"
        - "Using the GI Bill would reduce your expenses by $800/month vs baseline"
        - "Job search of 9 months is 3 months longer than your baseline 6 months"
        
        Args:
            baseline_profile: Original profile
            analyzed_profile: Profile with AI changes applied
            intent: Detected intent from AI
            question: Original user question
        
        Returns:
            String with comparison statement
        """
        statements = []
        
        # Compare job search timelines
        baseline_timeline = baseline_profile.get('job_search_timeline_months', 6)
        analyzed_timeline = analyzed_profile.get('job_search_timeline_months', 6)
        if baseline_timeline != analyzed_timeline:
            delta = analyzed_timeline - baseline_timeline
            direction = "longer" if delta > 0 else "shorter"
            statements.append(
                f"Job search scenario is {abs(delta)} months {direction} than your baseline ({baseline_timeline} months)"
            )
        
        # Compare GI Bill BAH
        baseline_bah = baseline_profile.get('gi_bill_bah_monthly', 0)
        analyzed_bah = analyzed_profile.get('gi_bill_bah_monthly', 0)
        if baseline_bah != analyzed_bah and analyzed_bah > 0:
            statements.append(
                f"Using GI Bill would provide ${analyzed_bah:,.0f}/month BAH (vs ${baseline_bah:,.0f}/month currently)"
            )
        
        # Compare expenses
        baseline_optional = baseline_profile.get('csv_optional_expenses', 0)
        analyzed_optional = analyzed_profile.get('csv_optional_expenses', 0)
        if baseline_optional != analyzed_optional:
            delta = baseline_optional - analyzed_optional
            if delta > 0:
                statements.append(
                    f"This scenario reduces optional expenses by ${delta:,.0f}/month (${analyzed_optional:,.0f} vs baseline ${baseline_optional:,.0f})"
                )
        
        baseline_negotiable = baseline_profile.get('csv_negotiable_expenses', 0)
        analyzed_negotiable = analyzed_profile.get('csv_negotiable_expenses', 0)
        if baseline_negotiable != analyzed_negotiable:
            delta = baseline_negotiable - analyzed_negotiable
            if delta > 0:
                statements.append(
                    f"Negotiable expenses reduced by ${delta:,.0f}/month (${analyzed_negotiable:,.0f} vs baseline ${baseline_negotiable:,.0f})"
                )
        
        # TODO: Add runway comparison when we have financial calculations
        # (requires integration with financial models)
        
        if not statements:
            statements.append("This scenario has similar parameters to your baseline.")
        
        return " | ".join(statements)
    
    @staticmethod
    def create_named_scenario_from_ai(
        baseline_profile: Dict[str, Any],
        analyzed_profile: Dict[str, Any],
        user_question: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a named scenario dict for saving to saved_scenarios list.
        
        Format matches dashboard.py's saved_scenarios structure:
        {
            "name": str,
            "profile": Dict,
            "timestamp": Timestamp,
            "source": "ai_analysis",
            "question": str,
            "analysis": str,
            "recommendation": str
        }
        
        Args:
            baseline_profile: Original profile
            analyzed_profile: Modified profile with AI changes
            user_question: Original question asked
            result: Full result dict from scenario_analyzer.analyze_scenario()
        
        Returns:
            Scenario dict ready to append to saved_scenarios list
        """
        import pandas as pd
        
        # Create short name from question (first 40 chars)
        short_question = user_question[:40]
        if len(user_question) > 40:
            short_question += "..."
        
        # Generate comparison for name
        intent = result.get('intent', 'unknown')
        comparison = AIScenarioStateManager.generate_comparison_statement(
            baseline_profile,
            analyzed_profile,
            intent,
            user_question
        )
        
        scenario = {
            "name": f"AI: {short_question}",
            "profile": analyzed_profile,
            "timestamp": pd.Timestamp.now(),
            "source": "ai_analysis",
            "question": user_question,
            "analysis": result.get('analysis', ''),
            "recommendation": result.get('recommendation', ''),
            "comparison_to_baseline": comparison,
            "baseline_profile": baseline_profile,  # Store for later comparison operations
            "intent": intent,
        }
        
        logger.info(f"✅ Created scenario from AI analysis: '{scenario['name']}'")
        
        return scenario
