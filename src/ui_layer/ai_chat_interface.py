"""
Streamlit AI advisor for financial scenario analysis.

Provides conversational Q&A about transition scenarios.
Powered by FLAN-T5 + RAG hybrid routing through FinancialCoach.
Routes to: RAG retrieval → FLAN-T5 intent detection → keyword fallback.
"""

import logging

import streamlit as st

from src.ai_layer.ollama_client import OllamaClient
from src.wizard.financial_coach import FinancialCoach
from src.data_models import TransitionProfile

logger = logging.getLogger(__name__)


def build_transition_profile_from_wizard_session() -> TransitionProfile:
    """
    Convert wizard session state into TransitionProfile for FinancialCoach.
    
    Maps all wizard steps to profile fields for FLAN-T5 + RAG routing.
    """
    profile = TransitionProfile(
        # Step 1: Military Profile
        rank=st.session_state.get('user_rank', 'Unknown'),
        years_of_service=st.session_state.get('user_years_of_service', 0),
        service_branch=st.session_state.get('user_service_branch', 'Unknown'),
        separation_date=st.session_state.get('user_separation_date', None),
        marital_status=st.session_state.get('user_marital_status', 'Unknown'),
        num_dependents=st.session_state.get('user_dependents', 0),
        
        # Step 2: Healthcare
        medical_plan=st.session_state.get('medical_plan', 'tricare_select'),
        vision_plan=st.session_state.get('vision_plan', 'tricare'),
        dental_plan=st.session_state.get('dental_plan', 'tricare'),
        
        # Step 3: Healthcare dependents & SBP
        medical_dependents_status=st.session_state.get('medical_dependents_status', 'self_only'),
        sbp_selected=st.session_state.get('sbp_checkbox', False),
        
        # Step 3b: Pension & VA Disability
        military_pension_gross=st.session_state.get('military_pension_gross', 0),
        va_rating=st.session_state.get('va_rating_slider', 0),
        va_monthly_custom=st.session_state.get('va_monthly_amount', 0),
        
        # Step 4: Civilian Career & Savings
        target_locality=st.session_state.get('user_locality', ''),
        target_state=st.session_state.get('user_state', ''),
        estimated_civilian_salary=st.session_state.get('estimated_civilian_salary', 0),
        job_search_timeline_months=st.session_state.get('job_search_timeline_months', 6),
        current_savings=st.session_state.get('current_savings', 0),
        available_credit=st.session_state.get('available_credit', 0),
        gi_bill_bah_monthly=st.session_state.get('gi_bill_bah_monthly', 0),
        
        # Step 5: GI Bill
        gi_program_type=st.session_state.get('gi_program_type', 'none'),
        
        # Step 6: Expenses (CSV or manual)
        monthly_mandatory_expenses=st.session_state.get('csv_mandatory_expenses', 0),
        monthly_negotiable_expenses=st.session_state.get('csv_negotiable_expenses', 0),
        monthly_optional_expenses=st.session_state.get('csv_optional_expenses', 0),
        monthly_prepaid_expenses=st.session_state.get(
            'adjusted_prepaid_monthly', 
            st.session_state.get('csv_prepaid_expenses', 0)
        ),
    )
    
    return profile


def build_context_from_wizard_session() -> dict:
    """Extract user data from wizard steps to populate AI context."""
    context = {}
    
    # Step 1: Military Profile
    context['rank'] = st.session_state.get('user_rank', 'Unknown')
    context['years_of_service'] = st.session_state.get('user_years_of_service', 'Unknown')
    context['service_branch'] = st.session_state.get('user_service_branch', 'Unknown')
    context['separation_date'] = st.session_state.get('user_separation_date', 'Unknown')
    context['marital_status'] = st.session_state.get('user_marital_status', 'Unknown')
    context['dependents'] = st.session_state.get('user_dependents', 0)
    context['current_military_takehome'] = st.session_state.get(
        'current_military_takehome_monthly', 0
    )
    
    # Step 2: Healthcare
    context['medical_plan'] = st.session_state.get('medical_plan', 'Unknown')
    context['vision_plan'] = st.session_state.get('vision_plan', 'Unknown')
    context['dental_plan'] = st.session_state.get('dental_plan', 'Unknown')
    
    # Step 3: SBP
    context['sbp_selected'] = st.session_state.get('sbp_checkbox', False)
    
    # Step 3b: Pension & Disability (CORRECT KEYS from wizard)
    context['military_pension'] = st.session_state.get('military_pension_gross', 0)
    context['va_rating'] = st.session_state.get('va_rating_slider', 0)
    context['va_monthly'] = st.session_state.get('va_monthly_amount', 0)
    
    # Step 4: Civilian Career (location stored in Step 1)
    # Location can come from either user_locality or career location fields
    locality = st.session_state.get('user_locality', '')
    state = st.session_state.get('user_state', '')
    context['target_location'] = f"{locality}, {state}".strip() if locality or state else 'Unknown'
    context['estimated_salary'] = st.session_state.get('estimated_civilian_salary', 0)
    context['job_search_months'] = st.session_state.get('job_search_timeline_months', 6)
    context['current_savings'] = st.session_state.get('current_savings', 0)
    context['available_credit'] = st.session_state.get('available_credit', 0)
    
    # Step 5: GI Bill
    context['gi_bill_type'] = st.session_state.get('gi_program_type', 'None')
    context['gi_bill_bah'] = st.session_state.get('gi_bill_bah_monthly', 0)
    
    # Step 6: Total expenses
    context['monthly_mandatory'] = st.session_state.get('csv_mandatory_expenses', 0)
    context['monthly_negotiable'] = st.session_state.get('csv_negotiable_expenses', 0)
    context['monthly_optional'] = st.session_state.get('csv_optional_expenses', 0)
    # Use adjusted_prepaid_monthly (corrected sinking fund from Step 7) if available, 
    # else raw CSV value
    context['monthly_prepaid'] = st.session_state.get(
        'adjusted_prepaid_monthly', st.session_state.get('csv_prepaid_expenses', 0)
    )
    
    return context


def initialize_ai_scenario_session() -> None:
    """Initialize Streamlit session state for scenario Q&A with FinancialCoach."""
    if "ai_scenario_messages" not in st.session_state:
        st.session_state.ai_scenario_messages = []
    if "ai_financial_coach" not in st.session_state:
        st.session_state.ai_financial_coach = None  # Will be lazily initialized


def render_ai_chat_interface() -> None:
    """
    Render AI financial advisor using FLAN-T5 + RAG hybrid routing.
    
    Features:
    - Powered by FinancialCoach (FLAN-T5 intent detection)
    - Falls back to RAG retrieval for factual questions
    - Falls back to keyword detection for robustness
    - Reads wizard data directly from session state (no data modification)
    - Provides "what if" scenario analysis
    """
    initialize_ai_scenario_session()
    
    # Build profile from wizard data for FinancialCoach routing
    try:
        profile = build_transition_profile_from_wizard_session()
        
        # Lazy initialize FinancialCoach (only once per session)
        if st.session_state.ai_financial_coach is None:
            st.session_state.ai_financial_coach = FinancialCoach(profile)
            logger.info("✅ FinancialCoach initialized with FLAN-T5 + RAG routing")
    except Exception as e:
        logger.error(f"Failed to build profile or initialize coach: {e}")
        st.error(f"AI initialization error: {e}")
        return
    
    # Build context for display (READ-ONLY display only)
    wizard_context = build_context_from_wizard_session()

    # Header
    st.header("[CHAT] AI Financial Scenario Advisor")
    st.markdown(
        """
    Ask "what if" questions about your transition. 
    I'll analyze scenarios based on your actual wizard data.
    
    **AI Engine:** FLAN-T5 intent detection + RAG retrieval + keyword fallback
    """
    )

    # DEBUG: Show what's being read from session state
    with st.expander("[DEBUG] Current Session Values", expanded=False):
        st.write("**Savings:**")
        st.write(f"- current_savings key in session: {'current_savings' in st.session_state}")
        st.write(f"- Value: {st.session_state.get('current_savings', 'NOT SET')}")
        st.write(f"- Type: {type(st.session_state.get('current_savings'))}")
        st.write(f"- build_context extracted: {wizard_context['current_savings']}")
        
        st.write("\n**Job Search Timeline:**")
        st.write(
            f"- job_search_timeline_months key in session: "
            f"{'job_search_timeline_months' in st.session_state}"
        )
        st.write(f"- Value: {st.session_state.get('job_search_timeline_months', 'NOT SET')}")
        st.write(f"- Type: {type(st.session_state.get('job_search_timeline_months'))}")
        st.write(f"- build_context extracted: {wizard_context['job_search_months']}")
        
        st.write("\n**Expenses:**")
        st.write(f"- Mandatory: {wizard_context['monthly_mandatory']}")
        st.write(f"- Negotiable: {wizard_context['monthly_negotiable']}")
        st.write(f"- Optional: {wizard_context['monthly_optional']}")
        st.write(f"- Prepaid: {wizard_context['monthly_prepaid']}")
        
        st.write("\n**Income:**")
        st.write(f"- Pension: {wizard_context['military_pension']}")
        st.write(f"- VA: {wizard_context['va_monthly']}")
        st.write(f"- Salary: {wizard_context['estimated_salary']}")

    # Display current profile snapshot
    with st.expander("[PROFILE] Your Loaded Profile (from Wizard)", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Rank", f"{wizard_context['rank']}")
            st.metric("YOS", f"{wizard_context['years_of_service']} years")
            st.metric("Service", f"{wizard_context['service_branch']}")
        
        with col2:
            st.metric("Target Location", wizard_context['target_location'])
            expected_salary = wizard_context['estimated_salary']
            st.metric(
                "Expected Salary", 
                f"${expected_salary:,.0f}/yr" if expected_salary > 0 else "Not entered"
            )
            st.metric("Job Search", f"{wizard_context['job_search_months']} months")
        
        with col3:
            current_savings = wizard_context['current_savings']
            st.metric(
                "Current Savings", 
                f"${current_savings:,.0f}" if current_savings > 0 else "Not entered"
            )
            available_credit = wizard_context['available_credit']
            st.metric(
                "Available Credit", 
                f"${available_credit:,.0f}" if available_credit > 0 else "Not entered"
            )
            military_pension = wizard_context['military_pension']
            st.metric(
                "Pension", 
                f"${military_pension:,.0f}/mo" if military_pension > 0 else "Not entered"
            )
    
    # Two-column layout: Chat on left, financials on right
    col_chat, col_financial = st.columns([2, 1], gap="medium")

    with col_chat:
        # Display chat history
        st.subheader("Conversation")
        chat_container = st.container(height=400, border=True)

        with chat_container:
            for msg in st.session_state.ai_scenario_messages:
                with st.chat_message(msg["role"]):
                    # Ensure proper markdown rendering with unsafe_allow_html for better formatting
                    st.markdown(msg["content"], unsafe_allow_html=True)

        # User input
        st.subheader("Your Question")
        user_input = st.chat_input(
            placeholder="Ask 'what if' scenarios... (e.g., 'What if job search takes 8 months?')",
            key="ai_scenario_input",
        )

        if user_input:
            # Add user message to history
            st.session_state.ai_scenario_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate response using FinancialCoach (FLAN-T5 + RAG routing)
            with st.spinner("Analyzing scenario with FLAN-T5 + RAG..."):
                try:
                    coach_result = st.session_state.ai_financial_coach.answer_question(user_input)
                    response = coach_result.get('response', 'Unable to generate response')
                    source = coach_result.get('source', 'unknown')
                    
                    # Ensure response is a string and properly formatted
                    if not isinstance(response, str):
                        response = str(response)
                    
                    # Clean up any formatting issues
                    import re
                    response = response.replace('\r\n', '\n')  # Normalize line endings
                    response = re.sub(r'\n{3,}', '\n\n', response)  # Remove excessive newlines (3+ → 2)
                    response = response.strip()  # Remove leading/trailing whitespace
                    
                    # Ensure response has minimal required length
                    if len(response) < 10:
                        logger.warning(f"Response too short: {len(response)} chars")
                        response = "Unable to generate a proper response. Please try again."
                    
                    # Log which routing was used
                    logger.debug(f"Question routed via: {source}")
                    if source == 'rag':
                        confidence = coach_result.get('confidence', 0.0)
                        logger.info(f"RAG answer (confidence: {confidence:.0%})")
                    
                except Exception as e:
                    logger.error(f"FinancialCoach error: {e}")
                    response = f"⚠️ Error processing question: {e}\n\nPlease try rephrasing your question."
            
            # Add assistant response to history
            st.session_state.ai_scenario_messages.append({
                "role": "assistant", 
                "content": response
            })
            
            st.rerun()

    with col_financial:
        st.subheader("[MONEY] Financial Baseline")
        
        # DEBUG: Even simpler - just show the values directly  
        st.write(f"**Savings from context: ${wizard_context['current_savings']:,.0f}**")
        
        # Always show current wizard values (not AI's internal state)
        total_expenses = (wizard_context['monthly_mandatory'] + 
                         wizard_context['monthly_negotiable'] + 
                         wizard_context['monthly_optional'] + 
                         wizard_context['monthly_prepaid'])
        
        income = (
            wizard_context['military_pension'] + 
            wizard_context['va_monthly'] + 
            (
                wizard_context['estimated_salary'] / 12 
                if wizard_context['estimated_salary'] > 0 else 0
            )
        )
        
        net = income - total_expenses
        
        st.metric("Total Monthly Income", f"${income:,.2f}")
        st.metric("Total Monthly Expenses", f"${total_expenses:,.2f}")
        
        if net >= 0:
            st.metric("[OK] Monthly Surplus", f"${net:,.2f}")
        else:
            st.metric("[ERROR] Monthly Deficit", f"${abs(net):,.2f}")
        
        st.divider()
        st.subheader("Your Runway")
        st.metric("[MONEY] Current Savings", f"${wizard_context['current_savings']:,.0f}")
        
        if net < 0 and wizard_context['current_savings'] > 0:
            months_runway = wizard_context['current_savings'] / abs(net)
            st.warning(f"Runway: {months_runway:.1f} months before depleting savings")
        
        # Expense breakdown explanation
        st.divider()
        st.subheader("[STATS] Expense Categories")
        st.markdown("""
        **During Job Search:**
        - [MANDATORY] Mandatory (100%): Must spend - rent, utilities, insurance
        - [NEGOTIABLE] Negotiable (variable): May reduce - food, phone, internet
        - [OPTIONAL] Optional (~0%): Don't spend - entertainment, dining out
        - [PREPAID] Prepaid (~0%): Don't spend - sinking fund items, discretionary
        
        **After Finding Job:**
        - All categories available again
        """)
        
        with st.expander("[INFO] How scenarios work"):
            total_shortfall_calc = (
                wizard_context['monthly_mandatory'] + wizard_context['monthly_negotiable']
            )
            st.markdown(f"""
            When you ask "what if", I calculate:
            1. **During {wizard_context['job_search_months']}-month search**: 
               Only mandatory + reduced negotiable
            2. **Savings consumed**: 
               ${total_shortfall_calc:,.0f}/mo × {wizard_context['job_search_months']} months
            3. **After finding job**: 
               Full salary kicks in + can resume all expenses
            4. **Your runway**: 
               How long {wizard_context['current_savings']:,.0f} covers the gap
            """)
        
        # Reset chat button
        st.divider()
        if st.button("[RESET] Clear Chat", use_container_width=True):
            st.session_state.ai_scenario_messages = []
            st.rerun()
