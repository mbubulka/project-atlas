"""
Pure functional VA disability benefit calculator - 2026 rates.
No state retention, deterministic only.

Source: VA.gov disability compensation rates effective 12/1/2025
"""


def get_va_disability_rate(rating: int, marital_status: str, num_dependents: int) -> float:
    """
    Calculate monthly VA disability benefit rate based on rating and family status.
    
    Args:
        rating: Disability rating (0, 10, 20, 30, ... 100)
        marital_status: "single" or "married"
        num_dependents: Number of dependents (0, 1, 2, etc.)
    
    Returns:
        Monthly VA benefit amount (float)
    """
    # Base rates: Single veteran, no dependents (2026 rates)
    single_rates = {
        0: 0.0,
        10: 180.42,
        20: 356.66,
        30: 552.47,
        40: 795.84,
        50: 1132.90,
        60: 1435.02,
        70: 1808.45,
        80: 2102.15,
        90: 2362.30,
        100: 3938.58,
    }
    
    # With spouse only (no children)
    spouse_only_rates = {
        30: 617.47,
        40: 882.84,
        50: 1241.90,
        60: 1566.02,
        70: 1961.45,
        80: 2277.15,
        90: 2559.30,
        100: 4158.17,
    }
    
    # With 1 child and spouse (no parents)
    married_1child_rates = {
        30: 666.47,
        40: 947.84,
        50: 1322.90,
        60: 1663.02,
        70: 2074.45,
        80: 2406.15,
        90: 2704.30,
        100: 4318.99,
    }
    
    # With 1 child only (no spouse or parents)
    single_1child_rates = {
        30: 596.47,
        40: 853.84,
        50: 1205.90,
        60: 1523.02,
        70: 1910.45,
        80: 2219.15,
        90: 2494.30,
        100: 4085.43,
    }
    
    # Additional child amounts (per child beyond first)
    additional_child_rates = {
        30: 32.00,
        40: 43.00,
        50: 54.00,
        60: 65.00,
        70: 76.00,
        80: 87.00,
        90: 98.00,
        100: 109.11
    }
    
    # Normalize marital status to lowercase
    marital_status = marital_status.lower() if marital_status else "single"
    is_married = marital_status in ("married", "married_filing_jointly")
    
    # Get base rate
    base_rate = single_rates.get(rating, 0.0)
    
    # Apply family status adjustments
    if num_dependents == 0:
        # No dependents
        if is_married:
            return spouse_only_rates.get(rating, base_rate)
        else:
            return base_rate
    
    elif num_dependents == 1:
        # 1 dependent
        if is_married:
            return married_1child_rates.get(rating, base_rate)
        else:
            return single_1child_rates.get(rating, base_rate)
    
    else:
        # 2+ dependents
        if is_married:
            # Start with married + 1 child, then add for additional children
            base = married_1child_rates.get(rating, base_rate)
            additional = additional_child_rates.get(rating, 0.0)
            return base + (additional * (num_dependents - 1))
        else:
            # Start with single + 1 child, then add for additional children
            base = single_1child_rates.get(rating, base_rate)
            additional = additional_child_rates.get(rating, 0.0)
            return base + (additional * (num_dependents - 1))


# Example usage
if __name__ == "__main__":
    # Test: Married with 1 child, 60% rating
    benefit = get_va_disability_rate(60, "married", 1)
    print(f"VA Benefit (60%, married, 1 child): ${benefit:,.2f}")
    
    # Test: Single, 40% rating
    benefit = get_va_disability_rate(40, "single", 0)
    print(f"VA Benefit (40%, single, 0 children): ${benefit:,.2f}")
