"""
Core data models for Project Atlas.

This module defines the TransitionProfile dataclass, which serves as the
single source of truth for all data flowing through the application.
All models receive and return TransitionProfile objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TransitionProfile:
    """
    Comprehensive profile for a military service member's financial transition.

    This dataclass is the central hub for all application data. It captures:
    - User identity and background
    - Current financial snapshot
    - What-if scenario parameters (levers)
    - Model computation outputs

    All model functions should accept and return instances of this class.
    """

    # ========== USER IDENTITY SECTION ==========
    user_name: str = ""
    """User's full name."""

    service_branch: str = ""
    """Military service branch (Army, Navy, Air Force, Marines, Space Force, Coast Guard)."""

    rank: str = ""
    """Final rank/grade at separation."""

    years_of_service: int = 0
    """Total years of active military service."""

    career_field: str = ""
    """Military or civilian career field (e.g., 'Operations Research', 'Data Scientist')."""

    separation_date: Optional[datetime] = None
    """Date of military separation (when they leave service)."""

    marital_status: str = "Single"
    """Marital status: 'Single', 'Married', 'Divorced', 'Widowed'."""

    dependents: int = 0
    """Number of dependent children."""

    # ========== FINANCIAL SNAPSHOT SECTION ==========
    current_savings: float = 0.0
    """Total liquid savings available (in dollars)."""

    monthly_expenses_mandatory: float = 0.0
    """Non-discretionary monthly expenses (rent, utilities, food basics) in dollars."""

    monthly_expenses_negotiable: float = 0.0
    """Semi-discretionary monthly expenses (subscriptions, dining out) in dollars."""

    monthly_expenses_optional: float = 0.0
    """Fully discretionary monthly expenses (entertainment, luxury items) in dollars."""

    transaction_history: List[Dict[str, any]] = field(default_factory=list)
    """
    Uploaded CSV transaction history. Each dict should contain:
    {
        'date': str (YYYY-MM-DD),
        'description': str,
        'amount': float,
        'category': str ('mandatory', 'negotiable', 'optional', 'unknown'),
        'payable_by_credit': bool (True if expense can be charged to CC, False for cash-only)
    }
    """

    current_annual_retirement_pay: float = 0.0
    """Expected annual military retirement pay (if applicable) in dollars."""

    current_va_disability_rating: int = 0
    """VA disability rating (0-100%)."""

    current_va_annual_benefit: float = 0.0
    """Current annual VA disability benefit in dollars."""

    spouse_annual_income: float = 0.0
    """Spouse's annual income (if applicable) in dollars."""

    other_annual_income: float = 0.0
    """Other household annual income (side hustles, investments, etc.) in dollars."""

    current_debt: float = 0.0
    """
    Current total outstanding debt (student loans, credit cards, car, mortgage, etc.) in dollars.
    """

    debt_payoff_priority: str = "minimum"
    """Debt payoff strategy: 'minimum', 'accelerated', 'avalanche', 'snowball'."""

    # ========== BENEFITS SECTION ==========
    plan_to_use_gi_bill: bool = False
    """Whether the service member plans to use GI Bill benefits."""

    gi_bill_transfer_eligible: bool = False
    """Whether the service member is eligible to transfer GI Bill benefits to dependents."""

    education_level: str = "bachelor"
    """Current education level: 'high_school', 'some_college', 'bachelor', 'master', 'doctorate'."""

    elect_sbp: bool = False
    """Whether electing Survivor Benefit Plan (SBP)."""

    sbp_beneficiary: str = "spouse"
    """SBP beneficiary type: 'spouse', 'child', 'spouse_and_children', 'none'."""

    filing_status: str = "single"
    """
    Tax filing status: 'single', 'married_filing_jointly', 'married_filing_separately',
    'head_of_household'.
    """

    # ========== WHAT-IF LEVERS SECTION ==========
    target_city: str = ""
    """Target city for relocation (e.g., 'Denver, CO', 'Austin, TX')."""

    target_state: str = ""
    """State of target city (for state income tax calculations)."""

    job_search_timeline_months: int = 6
    """Assumed duration of job search after separation (in months)."""

    estimated_annual_salary: float = 0.0
    """Estimated annual salary from new employment post-separation (in dollars)."""

    va_rating_assumption: Optional[int] = None
    """What-if VA disability rating assumption (may differ from current)."""

    healthcare_plan_choice: str = "tricare_select"
    """
    Healthcare plan choice: 'tricare_select', 'va_health', 'private_aca', 'spouse_employer'.
    """

    cost_of_living_adjustment_factor: float = 1.0
    """
    Multiplier for cost of living in target city vs. current location.
    E.g., 1.15 means 15% higher cost of living.
    """

    job_offer_certainty: float = 0.8
    """
    Subjective probability (0.0 to 1.0) that the job offer materializes
    within the job_search_timeline_months.
    """

    # ========== MODEL OUTPUTS SECTION ==========
    annual_take_home_pay: float = 0.0
    """
    Post-tax annual income from all sources (retirement + VA + salary).
    Calculated by retirement_pay_model.
    """

    monthly_take_home_pay: float = 0.0
    """Monthly take-home pay derived from annual_take_home_pay."""

    annual_healthcare_cost: float = 0.0
    """Total annual healthcare cost for the chosen plan. Calculated by healthcare_model."""

    monthly_healthcare_cost: float = 0.0
    """Monthly healthcare cost."""

    monthly_cash_flow: List[Dict[str, any]] = field(default_factory=list)
    """
    Month-by-month projection. Each dict contains:
    {
        'month': int (1, 2, 3, ...),
        'date': str (YYYY-MM-DD),
        'income': float,
        'expenses': float,
        'net_flow': float,
        'cumulative_savings': float
    }
    """

    final_cash_buffer: float = 0.0
    """
    Final cumulative savings after job_search_timeline_months.
    Calculated by buffer_simulator.
    """

    financial_verdict: str = "UNKNOWN"
    """
    Summary verdict: 'SURPLUS' (positive buffer), 'DEFICIT' (negative buffer),
    or 'BREAK_EVEN' (near zero). Calculated by buffer_simulator.
    """

    financial_verdict_confidence: float = 0.0
    """
    Confidence score (0.0 to 1.0) based on job_offer_certainty
    and other uncertainty factors.
    """

    risk_factors: List[str] = field(default_factory=list)
    """
    List of identified financial risks (e.g., 'High healthcare costs',
    'Long job search', 'Tight cash buffer').
    """

    recommendations: List[str] = field(default_factory=list)
    """
    AI-generated recommendations (e.g., 'Increase emergency fund before separation',
    'Consider Tricare Prime instead of Select').
    """

    # ========== METADATA SECTION ==========
    created_timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp when this profile was created."""

    last_updated_timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp when this profile was last modified."""

    metadata: Dict[str, any] = field(default_factory=dict)
    """
    Flexible storage for additional metadata (e.g., model versions,
    parameter tweaks, debugging info).
    """

    def __post_init__(self):
        """Validate and initialize fields after dataclass instantiation."""
        # Update timestamp
        self.last_updated_timestamp = datetime.now()

        # Coerce types (accept int, convert to float for numeric fields)
        self.current_savings = float(self.current_savings)
        self.monthly_expenses_mandatory = float(self.monthly_expenses_mandatory)
        self.monthly_expenses_negotiable = float(self.monthly_expenses_negotiable)
        self.monthly_expenses_optional = float(self.monthly_expenses_optional)
        self.estimated_annual_salary = float(self.estimated_annual_salary)
        self.annual_take_home_pay = float(self.annual_take_home_pay)
        self.monthly_take_home_pay = float(self.monthly_take_home_pay)
        self.annual_healthcare_cost = float(self.annual_healthcare_cost)
        self.monthly_healthcare_cost = float(self.monthly_healthcare_cost)
        self.final_cash_buffer = float(self.final_cash_buffer)

        # Validate VA rating
        if self.current_va_disability_rating < 0 or self.current_va_disability_rating > 100:
            raise ValueError(f"VA disability rating must be 0-100, got {self.current_va_disability_rating}")

        # Validate job search timeline
        if self.job_search_timeline_months < 1:
            raise ValueError(f"Job search timeline must be at least 1 month, " f"got {self.job_search_timeline_months}")

        # Validate cost of living adjustment
        if self.cost_of_living_adjustment_factor < 0.5 or self.cost_of_living_adjustment_factor > 2.0:
            raise ValueError(
                f"Cost of living adjustment must be between 0.5 and 2.0, "
                f"got {self.cost_of_living_adjustment_factor}"
            )

        # Validate job offer certainty
        if not (0.0 <= self.job_offer_certainty <= 1.0):
            raise ValueError(f"Job offer certainty must be 0.0-1.0, got {self.job_offer_certainty}")

    def total_monthly_expenses(self) -> float:
        """
        Calculate total monthly expenses across all categories.

        Returns:
            float: Sum of mandatory, negotiable, and optional expenses.
        """
        return self.monthly_expenses_mandatory + self.monthly_expenses_negotiable + self.monthly_expenses_optional

    def adjusted_total_monthly_expenses(self) -> float:
        """
        Calculate total monthly expenses adjusted for cost of living.

        Returns:
            float: Total expenses multiplied by cost_of_living_adjustment_factor.
        """
        return self.total_monthly_expenses() * self.cost_of_living_adjustment_factor

    def annual_expenses(self) -> float:
        """
        Calculate annual expenses.

        Returns:
            float: Total monthly expenses multiplied by 12.
        """
        return self.total_monthly_expenses() * 12

    def to_dict(self) -> Dict[str, any]:
        """
        Convert profile to dictionary for logging, serialization, or debugging.

        Returns:
            Dict: Dictionary representation of the profile.
        """
        return {
            "user_name": self.user_name,
            "service_branch": self.service_branch,
            "current_savings": self.current_savings,
            "target_city": self.target_city,
            "estimated_annual_salary": self.estimated_annual_salary,
            "job_search_timeline_months": self.job_search_timeline_months,
            "annual_take_home_pay": self.annual_take_home_pay,
            "final_cash_buffer": self.final_cash_buffer,
            "financial_verdict": self.financial_verdict,
        }


def create_empty_profile(user_name: str = "") -> TransitionProfile:
    """
    Factory function to create an empty TransitionProfile with defaults.

    Args:
        user_name (str): User's name.

    Returns:
        TransitionProfile: A new, empty profile ready to be populated.
    """
    return TransitionProfile(user_name=user_name)
