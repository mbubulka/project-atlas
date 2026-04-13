"""
Military Retirement Q&A Widget for ProjectAtlas

Simple integration of the Military Retirement QA tool into Streamlit UI.
"""

import streamlit as st
import json
import os
from typing import List, Dict, Optional


def load_military_retirement_qa_knowledge_base() -> List[Dict]:
    """Load military retirement Q&A pairs from knowledge base."""
    
    # Try multiple possible paths
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '../../data/military_retirement_qa.json'),
        os.path.join(os.path.dirname(__file__), '../../Milestone_B/military_retirement_qa_authenticated_498.json'),
        r"d:\AIT716\Milestone_B\military_retirement_qa_authenticated_498.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Handle different JSON formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'qa_pairs' in data:
                    return data['qa_pairs']
                else:
                    return data
            except Exception as e:
                st.warning(f"Could not load from {path}: {str(e)}")
                continue
    
    # Return empty list if no file found
    return []


def render_military_retirement_qa_widget():
    """Render Military Retirement Q&A widget in Streamlit."""
    
    st.markdown("## 🎖️ Military Retirement Advisor")
    st.markdown("Ask questions about military retirement benefits, calculations, and planning.")
    
    # Load knowledge base once (cached)
    if 'military_qa_kb' not in st.session_state:
        kb = load_military_retirement_qa_knowledge_base()
        st.session_state.military_qa_kb = kb
    
    kb = st.session_state.military_qa_kb
    
    if not kb:
        st.warning("[WARNING] Military Retirement Q&A knowledge base not loaded. Please ensure the data file is available.")
        st.info("Expected location: `data/military_retirement_qa.json` or `Milestone_B/military_retirement_qa_authenticated_498.json`")
        return
    
    st.success(f"✓ Knowledge base loaded: {len(kb)} Q&A pairs available")
    
    # =========== USER INPUT SECTION ===========
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_query = st.text_input(
            "Ask a military retirement question:",
            placeholder="e.g., How is military retirement pay calculated?",
            key="military_qa_input"
        )
    
    with col2:
        ask_button = st.button("Ask", type="primary", use_container_width=True)
    
    # =========== PROCESS QUERY ===========
    if ask_button and user_query:
        with st.spinner("Searching knowledge base..."):
            try:
                # Simple semantic search using string matching and similarity
                results = search_knowledge_base(user_query, kb, top_k=3)
                
                if results:
                    st.markdown("### Answer")
                    
                    # Display primary answer
                    best_result = results[0]
                    st.markdown(f"**Q:** {best_result['question']}")
                    st.markdown(f"**A:** {best_result['answer']}")
                    st.markdown(f"Match confidence: {best_result['score']:.1%}")
                    
                    # Show related Q&A pairs
                    if len(results) > 1:
                        with st.expander("📚 Related Q&A Pairs"):
                            for i, result in enumerate(results[1:], 1):
                                st.markdown(f"**Related {i}:**")
                                st.markdown(f"- Q: {result['question']}")
                                st.markdown(f"- A: {result['answer'][:200]}...")
                                st.markdown(f"- Relevance: {result['score']:.1%}")
                                st.divider()
                else:
                    st.info("No relevant answers found in knowledge base. Please try a different question.")
                    
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
    
    # =========== COMMON QUESTIONS SECTION ===========
    st.markdown("### [INFO] Frequently Asked Questions")
    
    common_questions = [
        "What is the survivor benefit plan?",
        "How is military retirement pay calculated?",
        "Can I work while receiving military retirement?",
        "What happens to my TSP after separation?",
        "How do I apply for VA disability benefits?",
        "What are my healthcare options after military service?",
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(common_questions):
        with cols[i % 2]:
            if st.button(question, key=f"faq_{i}", use_container_width=True):
                st.session_state.military_qa_input = question
                st.rerun()
    
    # =========== INFO SECTION ===========
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        This Military Retirement Advisor uses an authenticated knowledge base of 498 Q&A pairs 
        covering military retirement benefits, regulations, and planning.
        
        **Topics Covered:**
        - Retirement pay calculation and timeline
        - Survivor Benefit Plan (SBP)
        - Thrift Savings Plan (TSP) 
        - VA disability benefits
        - Healthcare options (TRICARE, CHCBP, FEHB)
        - Job search and transition support
        - Financial planning and tax treatment
        
        **How It Works:**
        1. Enter your question
        2. The tool searches the knowledge base for relevant Q&A pairs
        3. The most relevant answer is displayed with confidence score
        4. Related Q&A pairs are available for additional context
        
        **Data Source:**
        All answers are drawn from official military and VA resources.
        """)


def search_knowledge_base(
    query: str,
    knowledge_base: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    Simple search function using keyword matching.
    
    Args:
        query: User's question
        knowledge_base: List of Q&A pairs
        top_k: Number of results to return
    
    Returns:
        List of top matching Q&A pairs with scores
    """
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    scored_results = []
    
    for item in knowledge_base:
        # Get question and answer
        if 'question' in item:
            question = item['question']
        else:
            question = item.get('input_text', '')
        
        if 'answer' in item:
            answer = item['answer']
        else:
            answer = item.get('target_text', '')
        
        # Simple keyword matching score
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Count matching words
        qwords = set(question_lower.split())
        awords = set(answer_lower.split())
        
        matching_words = len(query_words & qwords) + len(query_words & awords) / 2
        
        # Boost score if query appears in question
        if query_lower in question_lower:
            score = 1.0
        else:
            # Calculate similarity as ratio of matching words
            total_words = len(query_words)
            score = matching_words / max(1, total_words) if total_words > 0 else 0
        
        if score > 0:
            scored_results.append({
                'question': question,
                'answer': answer,
                'score': score
            })
    
    # Sort by score descending and return top_k
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    return scored_results[:top_k]
