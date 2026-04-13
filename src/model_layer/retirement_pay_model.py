"""
Retirement pay and take-home pay model for Project Atlas.

Calculates post-tax income from all sources:
- Military retirement pay
- VA disability benefits (with CRDP offset logic)
- New civilian salary

VA Disability Compensation Rules:
- Rating >= 50%: CRDP (Concurrent Retirement & Disability Pay) eligible
  → Receive full pension + full VA benefit (both are additional income)
- Rating < 50%: Offset applies
  → VA benefit does NOT add to total income; instead it replaces portion of pension
  → Pays some pension as tax-free VA benefit (tax treatment changes, not income amount)
- Rating < 20%: Minimal/no additional benefit

Sources:
- DFAS: https://www.dfas.mil/militarymembers/pay-and-allowances/disability/crdp-crsc/
- VA Rates (2026): military.com (official DoD rates by rating and dependent status)
- See: src/model_layer/va_rates_lookup.py for official VA rate tables
"""

import logging

from src.data_models import TransitionProfile
from src.model_layer.config import (
    FEDERAL_STANDARD_DEDUCTION,
    FEDERAL_TAX_BRACKETS,
    MILITARY_HIGH_3_BY_RANK,
    MILITARY_RETIREMENT_FACTOR,
    VA_DISABILITY_RATES,
    get_tax_rate_for_state,
)

logger = logging.getLogger(__name__)


def calculate_take_home_pay(profile: TransitionProfile) -> TransitionProfile:
    """
    Calculate annual and monthly take-home pay from all sources.

    Sources of income:
    1. Military Retirement Pay (if applicable)
    2. VA Disability Benefits (CRDP vs Offset based on rating)
    3. New Civilian Salary

    VA Disability Logic (per DFAS):
    - Rating >= 50%: CRDP eligible → Full pension + full VA = additional income
    - Rating < 50%: Offset applies → VA does NOT increase total income
                    (pays some pension as tax-free VA instead)

    Taxes:
    1. Federal income tax (progressive brackets)
    2. State income tax
    3. FICA (Social Security + Medicare) - only on salary

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        TransitionProfile: Updated profile with:
            - annual_take_home_pay
            - monthly_take_home_pay
    """

    # Calculate gross income from each source
    retirement_pay = _calculate_retirement_pay(profile)
    va_rating = profile.va_rating_assumption or profile.current_va_disability_rating
    va_benefit = _calculate_va_benefit(profile)
    salary = profile.estimated_annual_salary

    # CRDP Logic: Only add VA benefit to gross income if rating >= 50%
    # Below 50%, VA offsets pension (changes tax treatment, not total income)
    if va_rating >= 50:
        # CRDP eligible: Get both full pension and full VA benefit
        gross_income = retirement_pay + va_benefit + salary
        crdp_status = "CRDP (Concurrent Pay)"
    else:
        # Offset applies: VA doesn't increase income, just changes tax treatment
        gross_income = retirement_pay + salary  # VA offsets, not added
        crdp_status = "Offset (VA reduces taxable portion)"

    logger.info(
        f"Gross income breakdown ({crdp_status}):\n"
        f"  Retirement: ${retirement_pay:,.2f}\n"
        f"  VA Benefit: ${va_benefit:,.2f} ({crdp_status})\n"
        f"  Salary: ${salary:,.2f}\n"
        f"  Total: ${gross_income:,.2f}\n"
        f"  VA Rating: {va_rating}%"
    )

    # Calculate taxes
    federal_tax = _calculate_federal_income_tax(gross_income)
    state_tax = _calculate_state_income_tax(gross_income, profile.target_state)
    fica_tax = _calculate_fica_tax(salary)  # FICA only on salary, not retirement/VA

    total_tax = federal_tax + state_tax + fica_tax

    logger.info(
        f"Tax breakdown:\n"
        f"  Federal: ${federal_tax:,.2f}\n"
        f"  State: ${state_tax:,.2f}\n"
        f"  FICA: ${fica_tax:,.2f}\n"
        f"  Total: ${total_tax:,.2f}"
    )

    # Calculate take-home
    annual_take_home = gross_income - total_tax
    monthly_take_home = annual_take_home / 12.0

    profile.annual_take_home_pay = annual_take_home
    profile.monthly_take_home_pay = monthly_take_home

    logger.info(f"Take-home pay:\n" f"  Annual: ${annual_take_home:,.2f}\n" f"  Monthly: ${monthly_take_home:,.2f}")

    # Store breakdown in metadata for transparency
    profile.metadata["income_breakdown"] = {
        "gross_income": gross_income,
        "retirement_pay": retirement_pay,
        "va_benefit": va_benefit,
        "salary": salary,
        "crdp_status": crdp_status,
        "va_rating": va_rating,
        "federal_tax": federal_tax,
        "state_tax": state_tax,
        "fica_tax": fica_tax,
        "total_tax": total_tax,
    }

    return profile


def _calculate_retirement_pay(profile: TransitionProfile) -> float:
    """
    Calculate military retirement pay.

    Formula: High-3 Average × Years of Service × 2.5%

    Note: This is simplified. Real calculation accounts for:
    - Branch-specific adjustments
    - Creditable service vs. actual service
    - Survivor Benefit Plan (SBP) deductions

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        float: Annual retirement pay.
    """

    if profile.years_of_service < 20:
        # Less than 20 years = no retirement pay
        logger.info(f"No military retirement: only {profile.years_of_service} years " f"of service (need 20)")
        return 0.0

    # Get High-3 average from rank lookup
    high_3 = MILITARY_HIGH_3_BY_RANK.get(profile.rank, 50000)

    retirement_pay = high_3 * profile.years_of_service * MILITARY_RETIREMENT_FACTOR

    logger.info(
        f"Retirement pay: ${high_3:,.0f} (High-3) × "
        f"{profile.years_of_service} years × 2.5% = ${retirement_pay:,.2f}"
    )

    return retirement_pay


def _calculate_va_benefit(profile: TransitionProfile) -> float:
    """
    Calculate annual VA disability benefit amount.

    This returns the benefit amount from official VA rate tables.
    The CRDP offset logic (whether to include in gross income) is handled
    by calculate_take_home_pay(), not here.

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        float: Annual VA disability benefit based on rating (from VA rate table).
    """

    # If a "what-if" assumption exists, use that; otherwise use current rating
    rating = profile.va_rating_assumption or profile.current_va_disability_rating

    # Round to nearest 10% (VA rates table only has 10% increments)
    rating_rounded = round(rating / 10) * 10
    rating_rounded = max(0, min(100, rating_rounded))  # Clamp 0-100

    benefit = VA_DISABILITY_RATES.get(rating_rounded, 0.0)

    logger.info(f"VA disability benefit: {rating_rounded}% rating = ${benefit:,.2f}/year")

    return benefit


def _calculate_federal_income_tax(gross_income: float) -> float:
    """
    Calculate federal income tax using 2024 tax brackets.

    Simplified: Uses standard deduction, single filing status.

    Args:
        gross_income (float): Total gross income.

    Returns:
        float: Federal income tax owed.
    """

    # Apply standard deduction
    taxable_income = max(0, gross_income - FEDERAL_STANDARD_DEDUCTION)

    tax = 0.0
    prev_threshold = 0.0

    for threshold, rate in FEDERAL_TAX_BRACKETS:
        if taxable_income <= threshold:
            break

        # Tax on income in this bracket
        income_in_bracket = min(taxable_income, threshold) - prev_threshold
        tax += income_in_bracket * rate

        prev_threshold = threshold

    return tax


def _calculate_state_income_tax(gross_income: float, target_state: str) -> float:
    """
    Calculate state income tax.

    Simplified: Flat tax rate per state (no deductions).

    Args:
        gross_income (float): Total gross income.
        target_state (str): Target state.

    Returns:
        float: State income tax owed.
    """

    state_rate = get_tax_rate_for_state(target_state)
    tax = gross_income * state_rate

    return tax


def _calculate_fica_tax(salary_only: float) -> float:
    """
    Calculate FICA tax (Social Security + Medicare).

    Note: FICA is only assessed on W-2 wages, not on retirement pay or VA benefits.

    Args:
        salary_only (float): Salary from new job.

    Returns:
        float: FICA tax owed.
    """

    # Social Security: 6.2% on first $168,600 (2024)
    ss_wage_base = 168600
    ss_rate = 0.062

    ss_tax = min(salary_only, ss_wage_base) * ss_rate

    # Medicare: 2.9% on all wages + 0.9% additional on earnings over $200,000
    medicare_rate = 0.029
    medicare_tax = salary_only * medicare_rate

    if salary_only > 200000:
        additional_medicare = (salary_only - 200000) * 0.009
        medicare_tax += additional_medicare

    return ss_tax + medicare_tax


def get_effective_tax_rate(profile: TransitionProfile) -> float:
    """
    Calculate the effective tax rate on total income.

    Args:
        profile (TransitionProfile): User's profile.

    Returns:
        float: Effective tax rate (0.0 to 1.0).
    """

    annual_income = profile.annual_take_home_pay + profile.metadata.get("income_breakdown", {}).get("total_tax", 0.0)

    if annual_income == 0:
        return 0.0

    total_tax = profile.metadata.get("income_breakdown", {}).get("total_tax", 0.0)
    return total_tax / annual_income


def calculate_marginal_tax_rate(gross_income: float, target_state: str) -> float:
    """
    Calculate the marginal tax rate (federal + state) on the next dollar earned.

    Useful for understanding incentives for additional income.

    Args:
        gross_income (float): Current gross income.
        target_state (str): Target state.

    Returns:
        float: Marginal tax rate (0.0 to 1.0).
    """

    # Find federal marginal rate
    taxable_income = max(0, gross_income - FEDERAL_STANDARD_DEDUCTION)
    fed_rate = 0.10  # Default

    for threshold, rate in reversed(FEDERAL_TAX_BRACKETS):
        if taxable_income >= threshold:
            fed_rate = rate
            break

    # Add state rate
    state_rate = get_tax_rate_for_state(target_state)

    # Approximate FICA (doesn't apply to retirement/VA, but applies to salary)
    fica_rate = 0.062 + 0.029  # SS + Medicare

    return fed_rate + state_rate + fica_rate
