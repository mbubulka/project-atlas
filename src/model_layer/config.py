"""
Configuration and data tables for Project Atlas models.

This module contains reference data: tax brackets, VA benefit rates, healthcare
costs, and other lookup tables. By centralizing data here, we make it easy to
update rates as they change without touching model logic.

Long-term: These could be populated from APIs or external data sources.
For now: Hard-coded for MVP.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ========== STATE INCOME TAX BRACKETS ==========
# 2024 tax brackets by state (federal + state combined for simplicity)
# Format: state -> [(income_threshold, rate)]
# This is simplified; real implementation would handle filing status, deductions, etc.

STATE_TAX_RATES: Dict[str, float] = {
    # No state income tax
    "Alaska": 0.00,
    "Florida": 0.00,
    "Nevada": 0.00,
    "South Dakota": 0.00,
    "Tennessee": 0.00,
    "Texas": 0.00,
    "Washington": 0.00,
    "Wyoming": 0.00,
    # Low tax
    "Colorado": 0.044,
    "Georgia": 0.055,
    "Arizona": 0.0555,
    "Indiana": 0.0365,
    "Kentucky": 0.05,
    "Louisiana": 0.055,
    "Mississippi": 0.05,
    "Missouri": 0.055,
    "Montana": 0.075,
    "New Mexico": 0.059,
    "North Carolina": 0.0475,
    "North Dakota": 0.054,
    "Oklahoma": 0.065,
    "South Carolina": 0.07,
    "Utah": 0.0485,
    # Mid-range tax
    "Alabama": 0.05,
    "Arkansas": 0.055,
    "Connecticut": 0.069,
    "Delaware": 0.068,
    "Hawaii": 0.086,
    "Idaho": 0.058,
    "Illinois": 0.0495,
    "Iowa": 0.0685,
    "Kansas": 0.057,
    "Maine": 0.075,
    "Maryland": 0.0775,
    "Michigan": 0.0425,
    "Minnesota": 0.0885,
    "New Hampshire": 0.0,  # No income tax on wages
    "New Jersey": 0.0885,
    "New York": 0.065,
    "Ohio": 0.0399,
    "Pennsylvania": 0.0307,
    "Rhode Island": 0.0675,
    "Virginia": 0.0575,
    "West Virginia": 0.065,
    "Wisconsin": 0.0685,
    "Vermont": 0.0875,
    "Massachusetts": 0.05,
    # Default
    "DC": 0.0875,
}


# ========== FEDERAL INCOME TAX (Simplified) ==========
# 2024 federal tax brackets for single filer (simplified, no deductions)
# Format: [(income_threshold, marginal_rate)]

FEDERAL_TAX_BRACKETS: List[Tuple[float, float]] = [
    (0, 0.10),
    (11000, 0.12),
    (44725, 0.22),
    (95375, 0.24),
    (182800, 0.32),
    (231250, 0.35),
    (578125, 0.37),
]

# Standard deduction for single filer (2024)
FEDERAL_STANDARD_DEDUCTION = 13850


# ========== MILITARY RETIREMENT PAY ==========
# High-3 average pay × Years of Service × 2.5% = Annual Retirement Pay
# This is simplified; actual calculation is more nuanced.
# For demonstration, we'll use average enlisted/officer rates by rank.

MILITARY_RETIREMENT_FACTOR = 0.025  # 2.5% per year of service

# Average high-3 pay by rank (approximate 2024 values)
# These are examples; actual values depend on location, branch, experience
MILITARY_HIGH_3_BY_RANK: Dict[str, float] = {
    # Enlisted (E)
    "E1": 24000,
    "E2": 27000,
    "E3": 29000,
    "E4": 32000,
    "E5": 37000,
    "E6": 43000,
    "E7": 52000,
    "E8": 62000,
    "E9": 74000,
    # Officers (O)
    "O1": 38000,
    "O2": 46000,
    "O3": 58000,
    "O4": 72000,
    "O5": 90000,
    "O6": 115000,
    "O7": 145000,
    "O8": 175000,
}


# ========== VA DISABILITY BENEFITS ==========
# 2024 VA disability compensation by rating
# Format: rating -> annual_benefit_single (no dependents)

VA_DISABILITY_RATES: Dict[int, float] = {
    0: 0,
    10: 186.00 * 12,
    20: 361.00 * 12,
    30: 561.00 * 12,
    40: 784.00 * 12,
    50: 1061.00 * 12,
    60: 1348.00 * 12,
    70: 1703.00 * 12,
    80: 1986.00 * 12,
    90: 2235.00 * 12,
    100: 3737.00 * 12,  # Schedular rating max
}

# Note: Real implementation would interpolate between ratings
# For MVP, we'll round to nearest 10%


# ========== TRICARE COSTS (2024) ==========
# Annual out-of-pocket maxima and enrollment fees


@dataclass
class TricarePlan:
    """Represents a Tricare healthcare plan."""

    name: str
    annual_enrollment_fee: float
    """Annual fee to be eligible for the plan."""

    annual_deductible: float
    """Deductible per calendar year."""

    annual_out_of_pocket_max: float
    """Maximum annual out-of-pocket cost."""

    primary_care_copay: float
    """Copay for primary care visit."""

    specialist_copay: float
    """Copay for specialist visit."""

    generic_drug_copay: float
    """Copay for generic medication."""

    inpatient_copay: float
    """Copay for hospital admission."""


TRICARE_PLANS: Dict[str, TricarePlan] = {
    "tricare_select": TricarePlan(
        name="Tricare Select",
        annual_enrollment_fee=181.92,  # Group A retiree (2025)
        annual_deductible=150,  # Group A retiree network
        annual_out_of_pocket_max=4261,  # Group A retiree
        primary_care_copay=37,  # Group A retiree network
        specialist_copay=51,  # Group A retiree network
        generic_drug_copay=16,  # TRICARE retail network 30-day
        inpatient_copay=225,  # Group A retiree network admission
    ),
    "tricare_prime": TricarePlan(
        name="Tricare Prime",
        annual_enrollment_fee=372,  # Group A retiree (2025)
        annual_deductible=0,  # No deductible for Prime
        annual_out_of_pocket_max=3000,  # Group A retiree
        primary_care_copay=25,  # Group A retiree
        specialist_copay=38,  # Group A retiree
        generic_drug_copay=13,  # TRICARE Home Delivery
        inpatient_copay=193,  # Group A retiree admission
    ),
    "tricare_for_life": TricarePlan(
        name="Tricare for Life (age 65+)",
        annual_enrollment_fee=0,  # No enrollment fee for TFL
        annual_deductible=0,  # No deductible for TFL
        annual_out_of_pocket_max=3000,  # Same as Prime for those eligible
        primary_care_copay=25,  # Same as Prime
        specialist_copay=38,  # Same as Prime
        generic_drug_copay=13,  # Same as Prime
        inpatient_copay=193,  # Same as Prime
    ),
    "va_healthcare": TricarePlan(
        name="VA Healthcare (Service-Connected)",
        annual_enrollment_fee=0,  # No enrollment fee for VA
        annual_deductible=0,  # No deductible for VA
        annual_out_of_pocket_max=0,  # Free for service-connected disabilities
        primary_care_copay=0,  # Free for eligible veterans
        specialist_copay=0,  # Free for eligible veterans
        generic_drug_copay=0,  # Free for eligible veterans
        inpatient_copay=0,  # Free for eligible veterans
    ),
}


# ========== HEALTHCARE COST MULTIPLIERS ==========
# Relative cost of living adjustments for healthcare in different cities
# Base = 1.0 (national average)

HEALTHCARE_COLA_BY_CITY: Dict[str, float] = {
    "Austin, TX": 0.95,
    "Denver, CO": 1.05,
    "Dallas, TX": 0.92,
    "Houston, TX": 0.94,
    "San Antonio, TX": 0.90,
    "Phoenix, AZ": 0.98,
    "Charlotte, NC": 1.02,
    "Raleigh, NC": 1.01,
    "Nashville, TN": 0.96,
    "Memphis, TN": 0.91,
    "Portland, OR": 1.08,
    "Seattle, WA": 1.12,
    "New York, NY": 1.35,
    "Los Angeles, CA": 1.25,
    "San Diego, CA": 1.20,
    "San Francisco, CA": 1.40,
    "Boston, MA": 1.18,
    "Chicago, IL": 1.04,
    "Miami, FL": 1.06,
    "Washington, DC": 1.10,
}


# ========== COST OF LIVING MULTIPLIERS ==========
# Overall cost of living adjustment by city
# Base = 1.0 (national average, roughly Kansas City)

COLA_BY_CITY: Dict[str, float] = {
    "Austin, TX": 1.05,
    "Denver, CO": 1.12,
    "Dallas, TX": 0.98,
    "Houston, TX": 0.96,
    "San Antonio, TX": 0.93,
    "Phoenix, AZ": 1.02,
    "Charlotte, NC": 1.03,
    "Raleigh, NC": 1.04,
    "Nashville, TN": 1.01,
    "Memphis, TN": 0.92,
    "Portland, OR": 1.15,
    "Seattle, WA": 1.20,
    "New York, NY": 1.50,
    "Los Angeles, CA": 1.38,
    "San Diego, CA": 1.32,
    "San Francisco, CA": 1.60,
    "Boston, MA": 1.25,
    "Chicago, IL": 1.08,
    "Miami, FL": 1.10,
    "Washington, DC": 1.18,
    "Arlington, VA": 1.22,
    "Alexandria, VA": 1.20,
}


def get_state_from_city(city: str) -> str:
    """
    Extract state abbreviation from a city string.

    Args:
        city (str): City string (e.g., "Denver, CO").

    Returns:
        str: State abbreviation (e.g., "CO").
    """
    if "," in city:
        return city.split(",")[-1].strip()
    return "TX"  # Default fallback


def get_tax_rate_for_state(state: str) -> float:
    """
    Retrieve state income tax rate.

    Args:
        state (str): State abbreviation or full name.

    Returns:
        float: State income tax rate (0.0 to 1.0).
    """
    # Handle both abbreviations and full names
    if state in STATE_TAX_RATES:
        return STATE_TAX_RATES[state]

    # Try mapping by abbreviation (simple version)
    state_abbr_map = {
        "CO": "Colorado",
        "TX": "Texas",
        "VA": "Virginia",
        "NC": "North Carolina",
        "WA": "Washington",
    }

    if state in state_abbr_map and state_abbr_map[state] in STATE_TAX_RATES:
        return STATE_TAX_RATES[state_abbr_map[state]]

    # Default: assume 5% if not found
    return 0.05


def get_cola_for_city(city: str) -> float:
    """
    Retrieve cost of living adjustment multiplier for a city.

    Args:
        city (str): City name (e.g., "Denver, CO").

    Returns:
        float: COLA multiplier (1.0 = average).
    """
    if city in COLA_BY_CITY:
        return COLA_BY_CITY[city]
    return 1.0  # Default


def get_healthcare_cola_for_city(city: str) -> float:
    """
    Retrieve healthcare cost multiplier for a city.

    Args:
        city (str): City name.

    Returns:
        float: Healthcare COLA multiplier.
    """
    if city in HEALTHCARE_COLA_BY_CITY:
        return HEALTHCARE_COLA_BY_CITY[city]
    return 1.0  # Default
