"""
AI Scenario Advisor v2 - Analyzes what-if scenarios using ScenarioAnalyzer.

Uses the project's AI integration:
- NaturalLanguageParser: Extracts parameters from questions  
- ScenarioAnalyzer: Detects intent and calculates financial impact
- Model calculations: Recalculates based on profile + scenario parameters

Focused on: "What if I take 9 months? What if I use GI Bill?"
"""

import logging
import streamlit as st

# Optional: Try to import ScenarioAnalyzer, but don't crash if dependencies missing
try:
    from src.ai_layer.scenario_analyzer import ScenarioAnalyzer
    SCENARIO_ANALYZER_AVAILABLE = True
except (ImportError, Exception) as e:
    SCENARIO_ANALYZER_AVAILABLE = False
    ScenarioAnalyzer = None
    import traceback
    logger_instance = logging.getLogger(__name__)
    logger_instance.error(f"❌ ScenarioAnalyzer import failed: {type(e).__name__}: {e}")
    logger_instance.error(traceback.format_exc())

# Import state manager for temp scenario creation and comparison
try:
    from src.ai_layer.ai_scenario_state_manager import AIScenarioStateManager
    STATE_MANAGER_AVAILABLE = True
except (ImportError, Exception) as e:
    STATE_MANAGER_AVAILABLE = False
    AIScenarioStateManager = None
    logging.warning(f"AIScenarioStateManager not available: {e}. Scenario saving will be limited.")

logger = logging.getLogger(__name__)


def initialize_temp_baseline() -> None:
    """
    Initialize or retrieve temp baseline profile.
    
    On first visit (no temp state), creates baseline from current wizard data.
    On subsequent questions, retrieves the same baseline for comparison.
    """
    if 'temp_baseline_profile' not in st.session_state:
        # Create baseline from current wizard state (on first AI question)
        st.session_state.temp_baseline_profile = {
            'user_rank': st.session_state.get('user_rank'),
            'user_years_of_service': st.session_state.get('user_years_of_service'),
            'user_service_branch': st.session_state.get('user_service_branch'),
            'pension': st.session_state.get('pension_take_home', st.session_state.get('military_pension_gross', 0)),
            'va_rating_slider': st.session_state.get('va_rating_slider', 0),
            'va_monthly': st.session_state.get('va_monthly_amount', 0),
            'estimated_civilian_salary': st.session_state.get('estimated_civilian_salary', 0),
            'job_search_timeline_months': st.session_state.get('job_search_timeline_months', 6),
            'current_savings': st.session_state.get('current_savings', 0),
            'available_credit': st.session_state.get('available_credit', 0),
            'user_locality': st.session_state.get('user_locality', ''),
            'user_state': st.session_state.get('user_state', ''),
            'csv_mandatory_expenses': st.session_state.get('csv_mandatory_expenses', 0),
            'csv_negotiable_expenses': st.session_state.get('csv_negotiable_expenses', 0),
            'csv_optional_expenses': st.session_state.get('csv_optional_expenses', 0),
            'adjusted_prepaid_monthly': st.session_state.get('adjusted_prepaid_monthly', st.session_state.get('csv_prepaid_expenses', 0)),
            'gi_bill_bah_monthly': st.session_state.get('gi_bill_bah_monthly', 0),
            'csv_classification_map': st.session_state.get('csv_classification_map', {}),
            'final_amounts': st.session_state.get('final_amounts', {}),
        }


def render_ai_scenario_advisor_integrated() -> None:
    """
    Render AI-powered scenario advisor with persistent temp baseline/analyzed pair.
    
    Architecture:
    1. Initialize temp_baseline_profile on first AI question
    2. For each question: create temp_analyzed_profile with AI changes
    3. Both available throughout conversation for deltas
    4. AI can naturally say "vs your baseline"
    """
    
    # Check if ScenarioAnalyzer is available
    if not SCENARIO_ANALYZER_AVAILABLE or ScenarioAnalyzer is None:
        st.warning("⚠️ AI scenario analysis is currently unavailable due to missing dependencies.")
        st.info("The app will continue working with standard financial calculations.")
        return
    
    # Initialize ScenarioAnalyzer
    if 'scenario_analyzer' not in st.session_state:
        st.session_state.scenario_analyzer = ScenarioAnalyzer()
    
    analyzer = st.session_state.scenario_analyzer
    
    # Build current profile from wizard data
    current_profile = {
        'user_rank': st.session_state.get('user_rank'),
        'user_years_of_service': st.session_state.get('user_years_of_service'),
        'user_service_branch': st.session_state.get('user_service_branch'),
        'pension': st.session_state.get('pension_take_home', st.session_state.get('military_pension_gross', 0)),
        'va_rating_slider': st.session_state.get('va_rating_slider', 0),
        'va_monthly': st.session_state.get('va_monthly_amount', 0),  # Matches what scenario_analyzer expects
        'estimated_civilian_salary': st.session_state.get('estimated_civilian_salary', 0),
        'job_search_timeline_months': st.session_state.get('job_search_timeline_months', 6),
        'current_savings': st.session_state.get('current_savings', 0),
        'available_credit': st.session_state.get('available_credit', 0),  # Credit cards, HELOC, etc.
        'user_locality': st.session_state.get('user_locality', ''),
        'user_state': st.session_state.get('user_state', ''),
        'csv_mandatory_expenses': st.session_state.get('csv_mandatory_expenses', 0),
        'csv_negotiable_expenses': st.session_state.get('csv_negotiable_expenses', 0),
        'csv_optional_expenses': st.session_state.get('csv_optional_expenses', 0),
        'adjusted_prepaid_monthly': st.session_state.get('adjusted_prepaid_monthly', st.session_state.get('csv_prepaid_expenses', 0)),
        'gi_bill_bah_monthly': st.session_state.get('gi_bill_bah_monthly', 0),
        'csv_classification_map': st.session_state.get('csv_classification_map', {}),
        'final_amounts': st.session_state.get('final_amounts', {}),
    }
    
    st.header("🤖 AI Scenario Advisor")
    st.markdown("Ask **what-if** questions to explore different transition scenarios. The AI understands natural language and recalculates your finances.")
    
    
    # Display current profile summary
    total_expenses = (current_profile.get('csv_mandatory_expenses', 0) + 
                     current_profile.get('csv_negotiable_expenses', 0) + 
                     current_profile.get('csv_optional_expenses', 0) + 
                     current_profile.get('adjusted_prepaid_monthly', 0))
    
    with st.expander("📊 Your Current Profile", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            military_income = (current_profile.get('pension', 0) + 
                             current_profile.get('va_monthly', 0))
            st.metric("Military Income", f"${military_income:,.0f}/mo")
        with col2:
            st.metric("Total Expenses", f"${total_expenses:,.0f}/mo")
        with col3:
            st.metric("Savings", f"${current_profile.get('current_savings', 0):,.0f}")
        with col4:
            st.metric("Job Search", f"{current_profile.get('job_search_timeline_months', 6)} months")
    
    st.divider()
    st.divider()
    
    # Chat interface
    st.subheader("❓ Ask Scenario Questions")
    st.markdown("""
    Examples the AI understands (try any rephrasing):
    - **Timeline:** "What if I take 8 months to find a job?"
    - **GI Bill:** "What if I use the GI Bill for school?"
    - **Savings:** "Do I have enough savings?", "How long can I live on savings?"
    - **Expenses:** "What if I cut optional spending?"
    """)
    
    # Initialize temp baseline on first question
    initialize_temp_baseline()
    
    # Display current baseline info
    with st.expander("📋 Your Baseline (for comparison)", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        baseline = st.session_state.temp_baseline_profile
        with col1:
            st.metric("Job Search", f"{baseline.get('job_search_timeline_months', 6)} months")
        with col2:
            st.metric("Optional Spend", f"${baseline.get('csv_optional_expenses', 0):,.0f}/mo")
        with col3:
            st.metric("GI Bill BAH", f"${baseline.get('gi_bill_bah_monthly', 0):,.0f}/mo")
        with col4:
            st.metric("Savings", f"${baseline.get('current_savings', 0):,.0f}")
    
    user_question = st.chat_input("Ask a what-if scenario question...", key="ai_scenario_question")
    
    if user_question:
        st.write(f"**Your question:** {user_question}")
        
        try:
            # Analyze the scenario using AI integration
            result = analyzer.analyze_scenario(user_question, current_profile)
            
            intent = result.get('intent')
            extracted = result.get('extracted_params', {})
            analysis = result.get('analysis', '')
            recommendation = result.get('recommendation', '')
            execution_log = result.get('execution_log', [])
            success = result.get('success', False)
            
            # Show AI's reasoning and tool execution steps
            if execution_log and success:
                with st.expander("🧠 AI Reasoning & Tools Executed", expanded=False):
                    st.caption("FLAN-T5 planned these steps and executed them:")
                    for step in execution_log:
                        st.write(step)
            
            # Show what was extracted
            if extracted and intent != 'unknown':
                with st.expander("🔍 Extracted & Computed Parameters", expanded=False):
                    for key, value in extracted.items():
                        if value is not None:
                            st.write(f"- **{key}**: {value}")
            
            # Show the analysis
            if intent != 'unknown':
                st.info(analysis)
                # Display recommendation with proper formatting
                if recommendation:
                    # Sanitize recommendation: remove all newlines and collapse multiple spaces
                    clean_rec = recommendation.replace('\n', ' ').replace('\r', ' ')
                    clean_rec = ' '.join(clean_rec.split())  # Collapse multiple whitespaces
                    
                    # Use st.success() for better text rendering without character wrapping
                    st.success(f"💡 **Recommendation:** {clean_rec}")
                
                # Create and store temp analyzed profile for persistent comparison
                if STATE_MANAGER_AVAILABLE and AIScenarioStateManager:
                    try:
                        # Create modified profile with AI-extracted parameters
                        analyzed_profile = AIScenarioStateManager.create_temp_analyzed_profile(
                            st.session_state.temp_baseline_profile,
                            extracted,
                            result.get('calculations', {})
                        )
                        
                        # Store as persistent temp state for follow-up questions
                        st.session_state.temp_analyzed_profile = analyzed_profile
                        st.session_state.last_ai_question = user_question
                        st.session_state.last_ai_intent = intent
                        
                        # Generate comparison statement
                        comparison = AIScenarioStateManager.generate_comparison_statement(
                            st.session_state.temp_baseline_profile,
                            analyzed_profile,
                            intent,
                            user_question
                        )
                        
                        # Display comparison to baseline (prominently)
                        with st.container(border=True):
                            st.markdown("### 📊 vs Your Baseline")
                            st.caption(comparison)
                        
                        # Add save button for this scenario
                        col_save, col_space = st.columns([1, 4])
                        with col_save:
                            if st.button("💾 Save This Scenario", use_container_width=True, key=f"save_ai_{abs(hash(user_question)) % 10000}"):
                                # Create scenario dict for saved_scenarios list
                                scenario = AIScenarioStateManager.create_named_scenario_from_ai(
                                    st.session_state.temp_baseline_profile,
                                    analyzed_profile,
                                    user_question,
                                    result
                                )
                                
                                # Initialize saved_scenarios if needed
                                if "saved_scenarios" not in st.session_state:
                                    st.session_state.saved_scenarios = []
                                
                                # Append to saved scenarios
                                st.session_state.saved_scenarios.append(scenario)
                                
                                st.success(f"✅ Scenario saved! You now have {len(st.session_state.saved_scenarios)} scenario(s) saved.")
                                st.info("Go to the [STATS] Compare Scenarios section in the Dashboard to see side-by-side comparison.")
                    
                    except Exception as e:
                        logger.warning(f"Could not create temp scenario for comparison: {e}")
                        st.caption("(Detailed comparison unavailable, but you can still manually save scenarios in Dashboard)")
            else:
                st.warning("""
                I couldn't understand that as a scenario question.
                
                Try asking about:
                - Job search timeline ("What if my search takes 9 months?")
                - GI Bill usage ("What if I use the GI Bill?")
                - Savings runway ("How many months can I cover with my savings?")
                - Savings sufficiency ("What if I had zero savings going in?")
                """)
            
            # Show detailed calculations for power users
            if intent != 'unknown' and extracted:
                with st.expander("📈 Detailed Calculations", expanded=False):
                    calc = result.get('calculations', {})
                    for key, value in calc.items():
                        if key not in ['intent', 'current_profile', 'scenario_params'] and value is not None:
                            st.write(f"**{key}:** {value}")
                
        except Exception as e:
            logger.exception("Error analyzing scenario")
            st.error(f"Error analyzing scenario: {str(e)}")
            st.info("Try rephrasing your question or asking about a specific scenario parameter.")
    
    # ===== DIAGNOSTIC SECTION (Debug AI System Status) =====
    st.divider()
    with st.expander("🔧 **AI System Diagnostics** (Debug Info)", expanded=False):
        st.write("**Which AI systems are loaded and being used?**\n")
        
        # Check analyzer status
        if 'scenario_analyzer' in st.session_state:
            analyzer = st.session_state.scenario_analyzer
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Milestone E (RAG - Factual Q&A):**")
                if analyzer.rag_advisor:
                    rag_status = "✅ **LOADED**"
                    if hasattr(analyzer.rag_advisor, 'rag_available'):
                        rag_status += f" - {len(analyzer.rag_advisor.knowledge_base) if analyzer.rag_advisor.knowledge_base else '?'} Q&A pairs"
                    st.markdown(rag_status)
                    st.caption("Used for: factual questions, definitions, explanations")
                else:
                    st.markdown("❌ **Not loaded** (will use FLAN-T5 only)")
            
            with col2:
                st.write("**Milestone C (FLAN-T5 - Scenario Analysis):**")
                if analyzer.flan_t5:
                    st.markdown("✅ **LOADED** - Intent detection ready")
                    st.caption("Used for: scenario what-ifs, parameter extraction, recommendations")
                else:
                    st.markdown("⚠️ **Not loaded** (will use keyword matching)")
        
        st.markdown("---")
        st.write("**Question Routing Logic:**")
        st.markdown("""
        1. **Is it a scenario question?** (job search, GI Bill, expenses, savings)
           - → YES: Use FLAN-T5 intent detection + calculations
           - → NO: Try RAG retrieval
        
        2. **RAG confidence >= 0.7?**
           - → YES: Return RAG answer (factual)
           - → NO: Fall back to FLAN-T5 or keyword matching
        """)
