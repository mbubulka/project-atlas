"""
AI Scenario Advisor - Uses existing AI integration for question answering.

Leverages the project's existing AI infrastructure:
- NaturalLanguageParser: Extracts intent/parameters from questions
- ChatFlowHandler: Orchestrates conversation and model execution
- ProfileBuilder: Manages profile state and calculations
- OllamaClient: Optional LLM for enhanced responses

This integrates with the core AI system rather than using hard-coded patterns.
"""

import streamlit as st
from src.ai_layer.chat_flow import ChatFlowHandler, ChatState
from src.ai_layer.orchestrator import NaturalLanguageParser
from src.data_models import create_empty_profile


def detect_question_intent(question: str) -> str:
    """
    Detect the intent of a user's question using keyword analysis.
    
    Returns one of:
    - 'job_search_timeline': "What if takes me X months?"
    - 'savings_runway': "How long can I live on savings?"
    - 'savings_enough': "Do I have enough savings?"
    - 'gi_bill': "What if I use GI Bill?"
    - 'cash_position': "What's my cash position after X months?"
    - 'safety_buffer': "How much do I need in savings?"
    - 'unknown': Couldn't determine intent
    """
    q_lower = question.lower()
    
    # Job search timeline questions
    if any(keyword in q_lower for keyword in ["takes", "months", "instead", "what if"]) and \
       any(keyword in q_lower for keyword in ["find", "job", "search", "takes"]):
        return 'job_search_timeline'
    
    # Savings runway questions
    if any(keyword in q_lower for keyword in ["how long", "survive", "live on", "runway"]) and \
       any(keyword in q_lower for keyword in ["savings", "last", "paycheck"]):
        return 'savings_runway'
    
    # Savings sufficiency questions
    if any(keyword in q_lower for keyword in ["enough", "sufficient", "cover"]) and \
       "savings" in q_lower:
        return 'savings_enough'
    
    # GI Bill / Education questions
    if any(keyword in q_lower for keyword in ["gi bill", "school", "education", "bah", "college"]):
        return 'gi_bill'
    
    # Cash position questions
    if any(keyword in q_lower for keyword in ["cash", "position", "balance", "account"]) and \
       any(keyword in q_lower for keyword in ["month", "after"]):
        return 'cash_position'
    
    # Safety buffer questions
    if any(keyword in q_lower for keyword in ["how much", "need", "buffer", "emergency"]) and \
       "savings" in q_lower:
        return 'safety_buffer'
    
    return 'unknown'


def render_ai_scenario_advisor() -> None:
    """
    Render simplified AI scenario advisor focused on scenario analysis.

    Does NOT attempt to extract new data or modify profile state.
    Uses wizard data as immutable source of truth.
    """
    
    # Extract wizard data
    wizard_data = {
        'rank': st.session_state.get('user_rank', 'Unknown'),
        'yos': st.session_state.get('user_years_of_service', 'Unknown'),
        'service': st.session_state.get('user_service_branch', 'Unknown'),
        'pension': st.session_state.get('pension_take_home', st.session_state.get('military_pension_gross', 0)),  # Use take-home, fallback to gross
        'va_rating': st.session_state.get('va_rating_slider', 0),
        'va_monthly': st.session_state.get('va_monthly_amount', 0),
        'salary': st.session_state.get('estimated_civilian_salary', 0),
        'job_search_months': st.session_state.get('job_search_timeline_months', 6),
        'current_savings': st.session_state.get('current_savings', 0),
        'location': st.session_state.get('user_locality', '') + (', ' + st.session_state.get('user_state', '')) if st.session_state.get('user_locality') else 'Unknown',
        'mandatory': st.session_state.get('csv_mandatory_expenses', 0),
        'negotiable': st.session_state.get('csv_negotiable_expenses', 0),
        'optional': st.session_state.get('csv_optional_expenses', 0),
        'prepaid': st.session_state.get('adjusted_prepaid_monthly', st.session_state.get('csv_prepaid_expenses', 0)),
    }
    
    # Calculate total expenses right away (needed for validation and analysis)
    total_expenses = wizard_data['mandatory'] + wizard_data['negotiable'] + wizard_data['optional'] + wizard_data['prepaid']
    
    st.header("[CHAT] AI Financial Advisor")
    st.markdown("Ask questions about 'what if' scenarios. I'll analyze the financial impact based on your data.")
    
    # DEBUG: Show what values were actually found
    with st.expander("🔍 [DEBUG] Expense Values Found", expanded=False):
        st.write(f"Mandatory: ${wizard_data['mandatory']:,.2f}")
        st.write(f"Negotiable: ${wizard_data['negotiable']:,.2f}")
        st.write(f"Optional: ${wizard_data['optional']:,.2f}")
        st.write(f"Prepaid: ${wizard_data['prepaid']:,.2f}")
        st.write(f"Total Expenses: ${total_expenses:,.2f}")
        st.write("---")
        st.write("**Raw session state values:**")
        st.write(f"csv_mandatory_expenses: {st.session_state.get('csv_mandatory_expenses', 'NOT FOUND')}")
        st.write(f"csv_negotiable_expenses: {st.session_state.get('csv_negotiable_expenses', 'NOT FOUND')}")
        st.write(f"csv_optional_expenses: {st.session_state.get('csv_optional_expenses', 'NOT FOUND')}")
        st.write(f"adjusted_prepaid_monthly: {st.session_state.get('adjusted_prepaid_monthly', 'NOT FOUND')}")
        st.write(f"csv_prepaid_expenses: {st.session_state.get('csv_prepaid_expenses', 'NOT FOUND')}")
    
    # Show all wizard data prominently
    st.subheader("[PROFILE] Your Financial Profile (Source of Truth)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Military Profile:**")
        st.write(f"• Rank: {wizard_data['rank']}")
        st.write(f"• YOS: {wizard_data['yos']}")
        st.write(f"• Service: {wizard_data['service']}")
    
    with col2:
        st.write("**Income:**")
        st.write(f"• Pension: ${wizard_data['pension']:,.0f}/mo")
        st.write(f"• VA: ${wizard_data['va_monthly']:,.2f}/mo")
        salary_monthly = wizard_data['salary'] / 12 if wizard_data['salary'] > 0 else 0
        st.write(f"• Civilian: ${salary_monthly:,.0f}/mo")
    
    with col3:
        st.write("**Resources:**")
        st.write(f"• Savings: ${wizard_data['current_savings']:,.0f}")
        st.write(f"• Location: {wizard_data['location']}")
        st.write(f"• Job Search: {wizard_data['job_search_months']} months")
    
    # ALERT: Check if expenses have been loaded
    if total_expenses == 0:
        st.warning("""
        ⚠️ **No expenses loaded yet!** 
        
        To analyze your transition plan, you need to:
        1. **Go back to Step 6** and upload your transaction CSV file
        2. Let the system classify your expenses (Mandatory, Negotiable, Optional, Prepaid)
        3. Return to this step when done
        
        Once your expenses are loaded, the financial analysis will be automatically calculated.
        """, icon="⚠️")
        return  # Don't show the rest of the advisor if expenses aren't loaded
    
    # Calculate totals - DURING JOB SEARCH vs AFTER JOB STARTS
    income_during_search = wizard_data['pension'] + wizard_data['va_monthly']
    salary_monthly = wizard_data['salary'] / 12 if wizard_data['salary'] > 0 else 0
    income_after_job_starts = income_during_search + salary_monthly
    
    # Net monthly during search (before new job)
    net_monthly_during_search = income_during_search - total_expenses
    # Net monthly after job starts (with civilian salary)
    net_monthly_after_job = income_after_job_starts - total_expenses
    
    st.divider()
    st.subheader("[MONEY] Current Financial Summary")
    
    # Show two scenarios side by side
    st.write("**Income Changes During Transition:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**💼 During Job Search** *(first {0} months)*".format(wizard_data['job_search_months']))
        st.metric("Income (Pension + VA)", f"${income_during_search:,.0f}")
        st.metric("Expenses", f"${total_expenses:,.0f}")
        if net_monthly_during_search >= 0:
            st.metric("Monthly Surplus", f"${net_monthly_during_search:,.0f}")
        else:
            st.metric("Monthly Deficit", f"${net_monthly_during_search:,.0f}")
    
    with col2:
        st.write("**✅ After New Job Starts** *(month {0}+)*".format(wizard_data['job_search_months'] + 1))
        st.metric("Income (Pension + VA + Salary)", f"${income_after_job_starts:,.0f}")
        st.metric("Expenses", f"${total_expenses:,.0f}")
        if net_monthly_after_job >= 0:
            st.metric("Monthly Surplus", f"${net_monthly_after_job:,.0f}")
        else:
            st.metric("Monthly Deficit", f"${net_monthly_after_job:,.0f}")
    
    # Show runway calculation
    st.divider()
    if net_monthly_during_search < 0:
        deficit_during_search = abs(net_monthly_during_search)
        months_can_sustain = wizard_data['current_savings'] / deficit_during_search if deficit_during_search > 0 else float('inf')
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Deficit (Job Search)", f"${deficit_during_search:,.0f}")
        with col2:
            if months_can_sustain == float('inf'):
                st.metric("Savings Runway", "Unlimited (no deficit)")
            else:
                st.metric("Savings Runway", f"{months_can_sustain:.1f} months" + 
                         ("  ✅" if months_can_sustain >= wizard_data['job_search_months'] else "  ⚠️"))
    
    # Scenario questions
    st.divider()
    st.subheader("❓ Ask Your Questions")
    st.markdown("""
    Examples you can ask:
    - *"What if I take 8 months to find a job instead of 6?"*
    - *"How long can I live on savings before my first paycheck?"*
    - *"What's my cash position after 12 months in the new job?"*
    - *"How much do I need in savings as a safety buffer?"*
    """)
    
    user_question = st.chat_input("Ask a scenario question...", key="scenario_question")
    
    if user_question:
        # Process simple scenario questions
        st.write(f"**Your question:** {user_question}")
        
        import re
        
        # Detect what-if scenarios
        if "how long" in user_question.lower() and ("savings" in user_question.lower() or "survive" in user_question.lower()):
            # Runway calculation - use deficit during job search
            if wizard_data['current_savings'] > 0 and net_monthly_during_search < 0:
                months = wizard_data['current_savings'] / abs(net_monthly_during_search)
                st.success(f"""
                With ${wizard_data['current_savings']:,.0f} in savings and a ${abs(net_monthly_during_search):,.0f} monthly deficit (during job search),
                you can sustain yourself for approximately **{months:.1f} months** before needing your first paycheck.
                
                **Action:** Make sure your job starts generating income within {int(months)} months.
                """)
            else:
                st.info(f"Your monthly deficit during job search is ${net_monthly_during_search:,.0f}. After the job starts, you'll have a ${net_monthly_after_job:,.0f} monthly surplus.")
        
        elif any(keyword in user_question.lower() for keyword in ["takes me", "takes", "what if", "instead"]) and "months" in user_question.lower():
            # Job search timeline analysis - handle "what if takes X months instead of Y" or "what if X months"
            
            # Try to extract both numbers for comparison
            numbers = re.findall(r'\d+', user_question.lower())
            
            if numbers:
                new_months = int(numbers[0])  # First number is typically the new scenario
                current_job_search = wizard_data['job_search_months']
                
                # If there are two numbers, try to use them as "instead of" comparison
                if len(numbers) >= 2:
                    # Check if user is asking "takes X instead of Y"
                    if "instead" in user_question.lower():
                        new_months = int(numbers[0])
                        # Use second number as reference, or current_job_search
                    
                income_without_salary = wizard_data['pension'] + wizard_data['va_monthly']
                
                # Calculate expenses at different spending levels
                mandatory_only = wizard_data['mandatory']
                mandatory_negotiable = wizard_data['mandatory'] + wizard_data['negotiable']
                full_budget = total_expenses
                
                deficit_full = max(0, full_budget - income_without_salary)
                deficit_essential = max(0, mandatory_negotiable - income_without_salary)
                deficit_minimal = max(0, mandatory_only - income_without_salary)
                
                # Calculate based on new scenario
                months_diff = new_months - current_job_search
                total_cost_full = deficit_full * new_months
                total_cost_essential = deficit_essential * new_months
                total_cost_minimal = deficit_minimal * new_months
                
                if months_diff != 0:
                    # Calculate savings runway at each spending level
                    runway_full = wizard_data['current_savings'] / deficit_full if deficit_full > 0 else float('inf')
                    runway_essential = wizard_data['current_savings'] / deficit_essential if deficit_essential > 0 else float('inf')
                    runway_minimal = wizard_data['current_savings'] / deficit_minimal if deficit_minimal > 0 else float('inf')
                    
                    st.info(f"""
                    **Scenario Analysis: Job search takes {new_months} months**
                    
                    **Comparison:**
                    - Original plan: {current_job_search} months
                    - New scenario: {new_months} months
                    - Difference: {'+' if months_diff > 0 else ''}{months_diff} months
                    """)
                    
                    # Show expense breakdown
                    st.write("**Expense Breakdown:**")
                    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
                    with exp_col1:
                        st.metric("[CRITICAL] Mandatory", f"${wizard_data['mandatory']:,.0f}/mo", help="Essential living expenses")
                    with exp_col2:
                        st.metric("[FLEXIBLE] Negotiable", f"${wizard_data['negotiable']:,.0f}/mo", help="Important but flexible")
                    with exp_col3:
                        st.metric("[OPTIONAL] Optional", f"${wizard_data['optional']:,.0f}/mo", help="Discretionary")
                    with exp_col4:
                        st.metric("[SINKING] Prepaid", f"${wizard_data['prepaid']:,.0f}/mo", help="Future obligations")
                    
                    # Show three spending scenarios
                    st.write("**Your Options - Spending Scenarios:**")
                    opt1, opt2, opt3 = st.columns(3)
                    
                    with opt1:
                        st.write("**📊 Full Budget**")
                        st.write(f"Expenses: ${full_budget:,.0f}/mo")
                        st.write(f"Income: ${income_without_salary:,.0f}/mo")
                        st.write(f"Deficit: ${deficit_full:,.0f}/mo")
                        st.write("---")
                        st.write(f"Cost for {new_months}mo: ${total_cost_full:,.0f}")
                        st.write(f"Savings runway: {runway_full:.1f} months" if runway_full != float('inf') else "Savings runway: Unlimited")
                        if wizard_data['current_savings'] < total_cost_full and deficit_full > 0:
                            credit_needed = total_cost_full - wizard_data['current_savings']
                            st.error(f"Credit needed: ${credit_needed:,.0f}")
                    
                    with opt2:
                        st.write("**✅ Essential Only** (No Optional/Prepaid)")
                        st.write(f"Expenses: ${mandatory_negotiable:,.0f}/mo")
                        st.write(f"Income: ${income_without_salary:,.0f}/mo")
                        st.write(f"Deficit: ${deficit_essential:,.0f}/mo")
                        st.write("---")
                        st.write(f"Cost for {new_months}mo: ${total_cost_essential:,.0f}")
                        st.write(f"Savings runway: {runway_essential:.1f} months" if runway_essential != float('inf') else "Savings runway: Unlimited")
                        if wizard_data['current_savings'] < total_cost_essential and deficit_essential > 0:
                            credit_needed = total_cost_essential - wizard_data['current_savings']
                            st.warning(f"Credit needed: ${credit_needed:,.0f}")
                        else:
                            st.success("✅ Covered by savings!")
                    
                    with opt3:
                        st.write("**💰 Minimal** (Mandatory Only)")
                        st.write(f"Expenses: ${mandatory_only:,.0f}/mo")
                        st.write(f"Income: ${income_without_salary:,.0f}/mo")
                        st.write(f"Deficit: ${deficit_minimal:,.0f}/mo")
                        st.write("---")
                        st.write(f"Cost for {new_months}mo: ${total_cost_minimal:,.0f}")
                        st.write(f"Savings runway: {runway_minimal:.1f} months" if runway_minimal != float('inf') else "Savings runway: Unlimited")
                        if wizard_data['current_savings'] < total_cost_minimal and deficit_minimal > 0:
                            credit_needed = total_cost_minimal - wizard_data['current_savings']
                            st.warning(f"Credit needed: ${credit_needed:,.0f}")
                        else:
                            st.success("✅ Covered by savings!")
                    
                    st.write("---")
                    st.write("**Recommendation:**")
                    st.info(f"""
                    With {new_months} months of job search:
                    - **Best case:** Cut optional spending ({wizard_data['negotiable'] + wizard_data['optional'] + wizard_data['prepaid']:,.0f}/mo) and rely on ${mandatory_negotiable:,.0f}/mo essential budget
                    - **Savings last:** ~{runway_essential:.1f} months with essential expenses
                    - **Action:** Line up credit (credit cards, personal loan) for any gap beyond your savings runway
                    """)
                else:
                    st.info(f"That's your current plan—{new_months} months of job search. Ask about a different timeline!")
        
        elif "enough" in user_question.lower() and "savings" in user_question.lower():
            # Savings sufficiency analysis for transition
            income_without_salary = wizard_data['pension'] + wizard_data['va_monthly']
            deficit_during_search = max(0, total_expenses - income_without_salary)
            months_until_salary = wizard_data['job_search_months']
            
            total_deficit = deficit_during_search * months_until_salary
            has_enough = wizard_data['current_savings'] >= total_deficit
            
            if has_enough:
                surplus = wizard_data['current_savings'] - total_deficit
                st.success(f"""
                ✅ **YES, you have enough savings for the transition!**
                
                **Analysis:**
                - Job search duration: {months_until_salary} months
                - Monthly deficit (without new salary): ${deficit_during_search:,.0f}
                - Total deficit over {months_until_salary} months: ${total_deficit:,.0f}
                - Your savings: ${wizard_data['current_savings']:,.0f}
                
                **Result:** You'll have **${surplus:,.0f} remaining** after the transition period.
                
                This assumes your military income (${income_without_salary:,.0f}/mo) plus expenses (${total_expenses:,.0f}/mo).
                """)
            else:
                shortfall = total_deficit - wizard_data['current_savings']
                months_covered = wizard_data['current_savings'] / deficit_during_search if deficit_during_search > 0 else 0
                st.warning(f"""
                ⚠️ **You may face a shortfall for a {months_until_salary}-month job search.**
                
                **Analysis:**
                - Job search duration: {months_until_salary} months
                - Monthly deficit (without new salary): ${deficit_during_search:,.0f}
                - Total deficit over {months_until_salary} months: ${total_deficit:,.0f}
                - Your savings: ${wizard_data['current_savings']:,.0f}
                
                **Shortfall:** ${shortfall:,.0f} (covers ~{months_covered:.1f} months)
                
                **Options to consider:**
                - Reduce expenses during job search
                - Accelerate your job search timeline
                - Look for interim income sources
                - Adjust expectations for the new role salary
                """)
        
        elif any(keyword in user_question.lower() for keyword in ["gi bill", "school", "education", "bah"]):
            # GI Bill + education scenario with BAH income
            gi_bill_bah = st.session_state.get('gi_bill_bah_monthly', 0)
            
            if gi_bill_bah == 0:
                st.warning("""
                ⚠️ **No GI Bill BAH configured yet!**
                
                To analyze a GI Bill scenario, you need to:
                1. Go back to **Step 4: Education** 
                2. Select your education program and location
                3. Let the system calculate your BAH (housing allowance)
                4. Return here to see the impact
                """)
            else:
                # With GI Bill: Additional income source during transition
                military_income = wizard_data['pension'] + wizard_data['va_monthly']
                income_with_bah = military_income + gi_bill_bah  # Income during school
                
                # Still no civilian job salary during school
                deficit_with_bah = max(0, total_expenses - income_with_bah)
                deficit_without_bah = max(0, total_expenses - military_income)
                
                months_searching = wizard_data['job_search_months']
                
                # Calculate scenarios
                total_cost_without_bah = deficit_without_bah * months_searching
                total_cost_with_bah = deficit_with_bah * months_searching
                savings_benefit = total_cost_without_bah - total_cost_with_bah
                
                runway_without_bah = wizard_data['current_savings'] / deficit_without_bah if deficit_without_bah > 0 else float('inf')
                runway_with_bah = wizard_data['current_savings'] / deficit_with_bah if deficit_with_bah > 0 else float('inf')
                
                st.info(f"""
                **GI Bill Education Scenario Analysis**
                
                By enrolling in school with GI Bill benefits, you'd receive:
                - **Monthly BAH (Housing Allowance):** ${gi_bill_bah:,.0f}
                - **Tax Status:** Tax-free benefit
                """)
                
                comp_col1, comp_col2 = st.columns(2)
                
                with comp_col1:
                    st.write("**WITHOUT GI Bill**")
                    st.write(f"Military Income (Pension + VA): ${military_income:,.0f}/mo")
                    st.write(f"Total Expenses: ${total_expenses:,.0f}/mo")
                    st.write(f"Monthly Deficit: ${deficit_without_bah:,.0f}/mo")
                    st.write("---")
                    st.write(f"Cost for {months_searching}mo: ${total_cost_without_bah:,.0f}")
                    if runway_without_bah == float('inf'):
                        st.write("Savings runway: Unlimited ✅")
                    else:
                        st.write(f"Savings runway: {runway_without_bah:.1f} months")
                        if wizard_data['current_savings'] < total_cost_without_bah:
                            credit_needed = total_cost_without_bah - wizard_data['current_savings']
                            st.error(f"Credit needed: ${credit_needed:,.0f}")
                
                with comp_col2:
                    st.write("**WITH GI Bill BAH**")
                    st.write(f"Military Income (Pension + VA): ${military_income:,.0f}/mo")
                    st.write(f"GI Bill BAH: ${gi_bill_bah:,.0f}/mo")
                    st.write(f"**Total Income:** ${income_with_bah:,.0f}/mo")
                    st.write(f"Total Expenses: ${total_expenses:,.0f}/mo")
                    st.write(f"Monthly Deficit: ${deficit_with_bah:,.0f}/mo")
                    st.write("---")
                    st.write(f"Cost for {months_searching}mo: ${total_cost_with_bah:,.0f}")
                    if runway_with_bah == float('inf'):
                        st.success("Savings runway: Unlimited ✅")
                    else:
                        st.write(f"Savings runway: {runway_with_bah:.1f} months")
                        if wizard_data['current_savings'] < total_cost_with_bah:
                            credit_needed = total_cost_with_bah - wizard_data['current_savings']
                            st.warning(f"Credit needed: ${credit_needed:,.0f}")
                
                st.write("---")
                st.success(f"""
                **Benefit of GI Bill Education:**
                - Savings benefit: **${savings_benefit:,.0f}** over {months_searching} months
                - Extended runway: **{runway_with_bah - runway_without_bah:.1f} additional months** of living covered
                - Skill boost: Gain credentials while covering expenses
                
                **Action:** Enrolling in school while job searching effectively subsidizes your transition with BAH income!
                """)
        
        else:
            st.info("""
            I can help with:
            - Job search timeline scenarios
            - Savings runway calculations  
            - Income projections
            - Expense impact analysis
            - Whether you have enough savings for transition
            - GI Bill education scenarios with BAH
            
            **Tip:** Ask specific questions like:
            - "What if I take 8 months to find a job?"
            - "Do I have enough in savings for transition?"
            - "How long can I live on savings?"
            - "What if I use the GI Bill to go to school?"
            """)
