"""
Expense Tool Router

Routes user questions about expenses to appropriate calculation functions.
Uses FLAN-T5 intent detection to identify what the user is asking for,
then executes deterministic calculation functions rather than LLM responses.

Examples:
- "Can you list my negotiable bills?" → get_negotiable_expenses()
- "What are my high-cost items?" → get_high_value_expenses()
- "Show me expenses by category" → get_expense_summary()
- "How much do I spend on optional items?" → get_optional_expenses()
"""

import pandas as pd
import streamlit as st
from typing import Optional, Dict, List, Tuple


def format_accounting(value: float) -> str:
    """Format value in accounting style: positive as $1,234.56, negative as $(1,234.56)"""
    if value < 0:
        return f"$({abs(value):,.2f})"
    else:
        return f"${value:,.2f}"


class ExpenseToolRouter:
    """Routes expense-related user queries to calculation functions"""

    TOOL_KEYWORDS = {
        "negotiable": ["negotiable", "flexible", "discretionary bills", "can reduce"],
        "mandatory": ["mandatory", "essential", "must pay", "non-negotiable"],
        "high_expense": ["high", "most expensive", "biggest expense", "costly"],
        "optional": ["optional", "luxury", "entertainment", "discretionary"],
        "summary": ["how much", "total", "break down", "summary", "overview"],
        "prepaid": ["prepaid", "renewal", "annual", "sinking fund"],
        "source": ["which", "where", "from which", "list of", "breakdown"],
    }

    @staticmethod
    def detect_intent(user_question: str) -> Optional[str]:
        """
        Detect user intent from question using keyword matching.
        Could be extended to use FLAN-T5 for more sophisticated detection.
        
        Returns: 
            - "list_negotiable": User wants list of negotiable expenses
            - "list_mandatory": User wants list of mandatory expenses
            - "list_optional": User wants list of optional expenses
            - "list_high_expense": User wants highest cost items
            - "summary": User wants overview/breakdown
            - "list_prepaid": User wants prepaid items
            - None: No specific intent detected, use LLM
        """
        question_lower = user_question.lower()
        
        # Check for negotiable expenses request
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["negotiable"]):
            if any(word in question_lower for word in ["bill", "expense", "list", "what"]):
                return "list_negotiable"
        
        # Check for mandatory expenses request
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["mandatory"]):
            if any(word in question_lower for word in ["bill", "expense", "list", "what"]):
                return "list_mandatory"
        
        # Check for high expense request
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["high_expense"]):
            if any(word in question_lower for word in ["expense", "item", "bill", "cost"]):
                return "list_high_expense"
        
        # Check for optional expenses request
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["optional"]):
            if any(word in question_lower for word in ["bill", "expense", "list", "what"]):
                return "list_optional"
        
        # Check for prepaid request
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["prepaid"]):
            if any(word in question_lower for word in ["item", "renewal", "list", "what"]):
                return "list_prepaid"
        
        # Check for general summary
        if any(kw in question_lower for kw in ExpenseToolRouter.TOOL_KEYWORDS["summary"]):
            if any(word in question_lower for word in ["spend", "expense", "breakdown", "total"]):
                return "summary"
        
        return None

    @staticmethod
    def route_query(intent: str, classification_map: Dict, final_amounts: Dict) -> Optional[Tuple]:
        """
        Route detected intent to appropriate calculation function.
        
        Returns:
            Tuple of (result_df, description) or None if intent not recognized
        """
        if intent == "list_negotiable":
            return ExpenseToolRouter.get_negotiable_expenses(classification_map, final_amounts)
        elif intent == "list_mandatory":
            return ExpenseToolRouter.get_mandatory_expenses(classification_map, final_amounts)
        elif intent == "list_optional":
            return ExpenseToolRouter.get_optional_expenses(classification_map, final_amounts)
        elif intent == "list_high_expense":
            return ExpenseToolRouter.get_high_value_expenses(classification_map, final_amounts)
        elif intent == "list_prepaid":
            return ExpenseToolRouter.get_prepaid_expenses(classification_map, final_amounts)
        elif intent == "summary":
            return ExpenseToolRouter.get_expense_summary(classification_map, final_amounts)
        else:
            return None

    @staticmethod
    def get_negotiable_expenses(classification_map: Dict, final_amounts: Dict) -> Tuple:
        """Extract negotiable (flexible) expenses"""
        items = [
            {
                "Expense": desc,
                "Monthly ($)": amount,
                "Annual ($)": amount * 12,
                "% of Total": 0,  # Calculated below
            }
            for desc, classification in classification_map.items()
            if classification == "negotiable"
            for amount in [final_amounts.get(desc, 0)]
            if amount > 0
        ]
        
        if not items:
            return pd.DataFrame(columns=["Expense", "Monthly ($)", "Annual ($)"]), "No negotiable expenses found"
        
        df = pd.DataFrame(items).sort_values("Monthly ($)", ascending=False)
        total = df["Monthly ($)"].sum()
        df["% of Total"] = (df["Monthly ($)"] / total * 100).round(1).astype(str) + "%"
        
        description = f"Found {len(df)} negotiable expense items totaling ${total:,.2f}/month"
        return df, description

    @staticmethod
    def get_mandatory_expenses(classification_map: Dict, final_amounts: Dict) -> Tuple:
        """Extract mandatory (essential) expenses"""
        items = [
            {
                "Expense": desc,
                "Monthly ($)": amount,
                "Annual ($)": amount * 12,
                "% of Total": 0,
            }
            for desc, classification in classification_map.items()
            if classification == "mandatory"
            for amount in [final_amounts.get(desc, 0)]
            if amount > 0
        ]
        
        if not items:
            return pd.DataFrame(columns=["Expense", "Monthly ($)", "Annual ($)"]), "No mandatory expenses found"
        
        df = pd.DataFrame(items).sort_values("Monthly ($)", ascending=False)
        total = df["Monthly ($)"].sum()
        df["% of Total"] = (df["Monthly ($)"] / total * 100).round(1).astype(str) + "%"
        
        description = f"Found {len(df)} mandatory expense items totaling ${total:,.2f}/month ({total/st.session_state.get('estimated_military_income', 1)*100:.0f}% of income)"
        return df, description

    @staticmethod
    def get_optional_expenses(classification_map: Dict, final_amounts: Dict) -> Tuple:
        """Extract optional (discretionary) expenses"""
        items = [
            {
                "Expense": desc,
                "Monthly ($)": amount,
                "Annual ($)": amount * 12,
                "% of Total": 0,
            }
            for desc, classification in classification_map.items()
            if classification == "optional"
            for amount in [final_amounts.get(desc, 0)]
            if amount > 0
        ]
        
        if not items:
            return pd.DataFrame(columns=["Expense", "Monthly ($)", "Annual ($)"]), "No optional expenses found"
        
        df = pd.DataFrame(items).sort_values("Monthly ($)", ascending=False)
        total = df["Monthly ($)"].sum()
        df["% of Total"] = (df["Monthly ($)"] / total * 100).round(1).astype(str) + "%"
        
        description = f"Found {len(df)} optional expense items totaling ${total:,.2f}/month (discretionary spending)"
        return df, description

    @staticmethod
    def get_high_value_expenses(classification_map: Dict, final_amounts: Dict, threshold: float = 500) -> Tuple:
        """Extract highest-cost expenses (default threshold: $500+/month)"""
        items = [
            {
                "Expense": desc,
                "Monthly ($)": amount,
                "Category": classification,
                "Annual ($)": amount * 12,
            }
            for desc, classification in classification_map.items()
            for amount in [final_amounts.get(desc, 0)]
            if amount >= threshold
        ]
        
        if not items:
            return pd.DataFrame(columns=["Expense", "Monthly ($)", "Category", "Annual ($)"]), f"No expenses found over ${threshold:,.0f}/month"
        
        df = pd.DataFrame(items).sort_values("Monthly ($)", ascending=False)
        total = df["Monthly ($)"].sum()
        
        description = f"Found {len(df)} high-value items (${threshold}+/month) totaling ${total:,.2f}/month"
        return df, description

    @staticmethod
    def get_prepaid_expenses(classification_map: Dict, final_amounts: Dict) -> Tuple:
        """Extract prepaid (annual renewal) expenses"""
        items = [
            {
                "Expense": desc,
                "Monthly Sinking ($)": amount,
                "Annual Cost ($)": amount * 12,
                "% of Total": 0,
            }
            for desc, classification in classification_map.items()
            if classification == "prepaid"
            for amount in [final_amounts.get(desc, 0)]
            if amount > 0
        ]
        
        if not items:
            return pd.DataFrame(columns=["Expense", "Monthly Sinking ($)", "Annual Cost ($)"]), "No prepaid expenses found"
        
        df = pd.DataFrame(items).sort_values("Annual Cost ($)", ascending=False)
        total = df["Monthly Sinking ($)"].sum()
        df["% of Total"] = (df["Monthly Sinking ($)"] / total * 100).round(1).astype(str) + "%"
        
        description = f"Found {len(df)} prepaid items requiring ${total:,.2f}/month sinking fund"
        return df, description

    @staticmethod
    def get_expense_summary(classification_map: Dict, final_amounts: Dict) -> Tuple:
        """Get summary breakdown by classification"""
        classifications = {}
        
        for desc, classification in classification_map.items():
            amount = final_amounts.get(desc, 0)
            if amount > 0:
                if classification not in classifications:
                    classifications[classification] = 0
                classifications[classification] += amount
        
        items = [
            {
                "Category": cat.capitalize(),
                "Monthly Total ($)": amount,
                "Annual Total ($)": amount * 12,
                "Count": sum(1 for c in classification_map.values() if c == cat),
            }
            for cat, amount in classifications.items()
        ]
        
        if not items:
            return pd.DataFrame(), "No expense data available"
        
        df = pd.DataFrame(items).sort_values("Monthly Total ($)", ascending=False)
        grand_total = df["Monthly Total ($)"].sum()
        df["% of Total"] = (df["Monthly Total ($)"] / grand_total * 100).round(1).astype(str) + "%"
        
        description = f"Expense breakdown: {len(df)} categories totaling ${grand_total:,.2f}/month"
        return df, description
