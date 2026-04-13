"""
Wizard module for Project Atlas.

Provides guided step-by-step transition planning with coherent narrative flow.
"""

from .session_manager import (
    build_profile_from_session,
    get_wizard_state,
    save_profile_to_file,
    set_wizard_state,
)
from .summary_engine import (
    DecisionLever,
    DecisionRisk,
    DecisionSummary,
    FinancialMetrics,
    calculate_financial_metrics,
    generate_decision_summary,
    identify_levers,
    identify_risks,
)
from .whatif_tools import (
    ScenarioComparison,
    display_scenario_comparison,
    test_debt_payoff,
    test_expense_reduction,
    test_job_delay,
    test_salary_adjustment,
    test_va_rating,
)
from .wizard_flow import (
    step1_profile,
    step2_finances,
    step3_benefits,
    step4_transition,
)
from .wizard_ui import (
    display_decision_summary,
    display_progress_bar,
    initialize_wizard_state,
    run_transition_wizard,
)

__all__ = [
    "build_profile_from_session",
    "save_profile_to_file",
    "get_wizard_state",
    "set_wizard_state",
    "step1_profile",
    "step2_finances",
    "step3_benefits",
    "step4_transition",
    "FinancialMetrics",
    "DecisionRisk",
    "DecisionLever",
    "DecisionSummary",
    "calculate_financial_metrics",
    "identify_risks",
    "identify_levers",
    "generate_decision_summary",
    "ScenarioComparison",
    "test_salary_adjustment",
    "test_job_delay",
    "test_va_rating",
    "test_expense_reduction",
    "test_debt_payoff",
    "display_scenario_comparison",
    "initialize_wizard_state",
    "display_progress_bar",
    "run_transition_wizard",
    "display_decision_summary",
]
