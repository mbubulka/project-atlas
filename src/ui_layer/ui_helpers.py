"""
Project Atlas UI Helper Functions

Standardized UI components for professional appearance:
- Step headers with emojis and disclaimers
- Standardized error/warning/success messages  
- Topic-specific source references
"""

import streamlit as st


# ========== STANDARDIZED UI COMPONENTS ==========

def render_step_header(step_number: int, emoji: str, title: str, description: str = ""):
    """
    Render a standardized professional step header with emoji.
    
    Args:
        step_number: Step number (1-8)
        emoji: Emoji for this step
        title: Step title
        description: Optional description text
        
    Example:
        render_step_header(1, "👤", "Your Military Profile", "Let's start with your service details.")
    """
    st.markdown(f"## {emoji} Step {step_number}: {title}")
    if description:
        st.write(description)
    st.markdown("---")


def render_educational_disclaimer(topic_sources: dict = None):
    """
    Display a standardized educational disclaimer with topic-specific official sources.
    
    Args:
        topic_sources: Dict of {\"topic_name\": \"official_url\"}
        
    Example:
        render_educational_disclaimer({
            "VA Benefits": "https://www.va.gov/disability",
            "TRICARE Plans": "https://www.tricare.mil"
        })
    """
    st.info(
        "ℹ️ **Educational Purpose Only**: This tool is designed for personal financial planning and education. "
        "It is NOT financial advice and does NOT substitute for professional financial counseling. "
        "Always consult with a financial advisor before making major decisions. "
        "Refer to official sources below for authoritative information."
    )
    
    if topic_sources and len(topic_sources) > 0:
        st.markdown("**📚 Official Sources for This Section:**")
        for topic, url in topic_sources.items():
            # Extract domain name for cleaner display
            domain = url.split('//')[1].split('/')[0] if '//' in url else url
            st.markdown(f"- **{topic}**: [{domain}]({url})")
        st.markdown("---")


def format_federal_source_link(text: str, url: str = "https://www.irs.gov") -> str:
    """Helper to format federal source links (IRS, DFAS, VA, etc.)"""
    return f"[{text}]({url})"


# ========== STANDARDIZED MESSAGE COMPONENTS ==========

def show_success(message: str):
    """Display a success message with ✅ prefix."""
    st.success(f"✅ {message}")


def show_error(message: str):
    """Display an error message with ❌ prefix."""
    st.error(f"❌ {message}")


def show_warning(message: str):
    """Display a warning message with ⚠️ prefix."""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """Display an info message with ℹ️ prefix."""
    st.info(f"ℹ️ {message}")


def show_high_priority(message: str):
    """Display a high-priority/critical message with 🔴 prefix."""
    st.error(f"🔴 **CRITICAL**: {message}")


def show_low_priority(message: str):
    """Display a low-priority message with 🟢 prefix."""
    st.success(f"🟢 **GOAL**: {message}")


# ========== STANDARDIZED EXPANSION PANELS ==========

def show_debug_expander(title: str, content_fn):
    """
    Display a debug/developer expander panel (collapsed by default).
    
    Args:
        title: Expander title
        content_fn: Function that renders content inside expander
        
    Example:
        def show_my_debug():
            st.write("Debug info here")
        show_debug_expander("Debug: Income Calculation", show_my_debug)
    """
    with st.expander(f"🔍 {title} (Developers Only)", expanded=False):
        content_fn()


def show_reference_expander(title: str, content_fn):
    """
    Display a reference/informational expander panel (collapsed by default).
    
    Args:
        title: Expander title
        content_fn: Function that renders content inside expander
    """
    with st.expander(f"📋 {title}", expanded=False):
        content_fn()


# ========== OFFICIAL SOURCE REFERENCES ==========

SOURCES = {
    # Federal/Military
    "DFAS (Defense Finance & Accounting Service)": "https://www.dfas.mil",
    "Military Retirement Pay": "https://www.dfas.mil/militarypay/retirement",
    "Military Paycheck": "https://www.dfas.mil/militarypay/militarybasepaybook",
    
    # VA & Disability
    "VA Disability Benefits": "https://www.va.gov/disability",
    "VA Disability Ratings": "https://www.va.gov/disability/how-to-file-claim",
    "VA Healthcare": "https://www.va.gov",
    
    # Healthcare
    "TRICARE Plans": "https://www.tricare.mil",
    "TRICARE Enrollment": "https://www.tricare.mil/CoveredServices/Enrollment",
    "ACA Marketplace": "https://www.healthcare.gov",
    "Healthcare.gov": "https://www.healthcare.gov",
    
    # Tax & Financial
    "IRS Tax Information": "https://www.irs.gov",
    "IRS Tax Withholding Estimator": "https://apps.irs.gov/app/tax-withholding-estimator",
    "Social Security Administration": "https://www.ssa.gov",
    "Federal Student Aid": "https://studentaid.gov",
    
    # Career & Planning
    "Military.com Career Planning": "https://www.military.com/military-careers",
    "Military Financial Planning": "https://www.military.com/financial-planning",
    "Career One Stop": "https://www.careeronestop.org",
    
    # General Financial
    "USA.gov Debt Management": "https://www.usa.gov/debt-management",
    "Federal Trade Commission - Money": "https://www.consumer.ftc.gov/money",
    "Financial Advisor Locator (NAPFA)": "https://www.napfa.org/find-advisor",
}


def get_source(topic_key: str) -> str:
    """Get the official URL for a topic."""
    return SOURCES.get(topic_key, "https://www.usa.gov")


# ========== STEP-SPECIFIC DISCLAIMER SETS ==========

STEP_1_SOURCES = {
    "Military Pay Scales": "https://www.dfas.mil/militarypay/militarybasepaybook",
    "State Tax Information": "https://www.irs.gov",
}

STEP_2_SOURCES = {
    "TRICARE Plans": "https://www.tricare.mil",
    "VA Healthcare": "https://www.va.gov",
    "ACA Marketplace": "https://www.healthcare.gov",
}

STEP_3_SOURCES = {
    "Military Retirement Pay": "https://www.dfas.mil/militarypay/retirement",
    "VA Disability Benefits": "https://www.va.gov/disability",
    "Tax Calculator": "https://apps.irs.gov/app/tax-withholding-estimator",
}

STEP_4_SOURCES = {
    "Financial Planning": "https://www.military.com/financial-planning",
    "Debt Management": "https://www.usa.gov/debt-management",
}

STEP_7_SOURCES = {
    "Financial Planning": "https://www.military.com/financial-planning",
    "Career Planning": "https://www.military.com/military-careers",
}

STEP_8_SOURCES = {
    "Financial Advisor Search": "https://www.napfa.org/find-advisor",
    "Financial Planning": "https://www.military.com/financial-planning",
}
