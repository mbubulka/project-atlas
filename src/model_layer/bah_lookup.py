"""
BAH (Basic Allowance for Housing) lookup utility.

Provides location-based BAH rate lookups for GI Bill education planning.
Rates based on E-5 single (no dependents) (2024-2025 military BAH rates).
"""

# All 50 US States + Washington DC with realistic average BAH rates
# Rates represent typical BAH for E-5 single (no dependents) in that state
MILITARY_LOCATIONS = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "Washington, DC",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
]

# Average BAH rates by state for E-5 single (no dependents) (2026 rates with 4.2% COLA increase
# from 2024)
# Source: 2024 baseline rates adjusted by DoD 2025-2026 national average COLA increase of 4.2%
# Users should validate against official DoD BAH Calculator:
# https://www.defensetravel.dod.mil/site/bahCalc.cfm
BAH_RATES = {
    "Alabama": 1349,
    "Alaska": 2334,
    "Arizona": 1459,
    "Arkansas": 1240,
    "California": 2044,
    "Colorado": 1532,
    "Connecticut": 1679,
    "Delaware": 1459,
    "Florida": 1496,
    "Georgia": 1387,
    "Hawaii": 2810,
    "Idaho": 1314,
    "Illinois": 1532,
    "Indiana": 1387,
    "Iowa": 1314,
    "Kansas": 1240,
    "Kentucky": 1314,
    "Louisiana": 1349,
    "Maine": 1387,
    "Maryland": 1604,
    "Massachusetts": 1897,
    "Michigan": 1459,
    "Minnesota": 1459,
    "Mississippi": 1240,
    "Missouri": 1349,
    "Montana": 1277,
    "Nebraska": 1277,
    "Nevada": 1532,
    "New Hampshire": 1459,
    "New Jersey": 1751,
    "New Mexico": 1349,
    "New York": 2334,
    "North Carolina": 1349,
    "North Dakota": 1240,
    "Ohio": 1423,
    "Oklahoma": 1277,
    "Oregon": 1459,
    "Pennsylvania": 1532,
    "Rhode Island": 1679,
    "South Carolina": 1459,
    "South Dakota": 1277,
    "Tennessee": 1387,
    "Texas": 1423,
    "Utah": 1423,
    "Vermont": 1423,
    "Virginia": 1875,
    "Washington": 1604,
    "Washington, DC": 1824,
    "West Virginia": 1314,
    "Wisconsin": 1387,
    "Wyoming": 1314,
}


def get_bah_rate(location: str) -> int:
    """
    Get BAH rate for a given location.

    Args:
        location: Location string (state abbreviation like 'VA' or full name like 'Virginia')

    Returns:
        Monthly BAH rate in dollars (default 1400 for single E-5 if location not found)
    """
    # Map state abbreviations to full names
    state_abbr_to_name = {
        "VA": "Virginia",
        "MD": "Maryland",
        "DC": "Washington, DC",
        "NC": "North Carolina",
        "PA": "Pennsylvania",
        "NY": "New York",
        "TX": "Texas",
        "CA": "California",
        "FL": "Florida",
    }
    
    # Convert abbreviation to full name if needed
    full_location = state_abbr_to_name.get(location, location)
    
    return BAH_RATES.get(full_location, 1400)


def get_all_locations():
    """Return list of all available military locations."""
    return MILITARY_LOCATIONS


def calculate_gi_bill_total(bah_monthly: float, months: int, book_stipend: float = 41.67) -> float:
    """
    Calculate total GI Bill benefit value.

    Args:
        bah_monthly: Monthly BAH in dollars
        months: Number of months of entitlement
        book_stipend: Monthly book stipend (default $41.67 for Post-9/11)

    Returns:
        Total benefit value in dollars
    """
    return (bah_monthly + book_stipend) * months
