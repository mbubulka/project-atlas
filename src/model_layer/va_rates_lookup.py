"""
VA Disability Compensation Rate Lookup

Official rates from military.com as of 2026.
Includes rates for 10%-100% disabilities with dependent status variations.

Usage:
    from src.model_layer.va_rates_lookup import get_va_monthly_benefit

    benefit = get_va_monthly_benefit(
        rating=50,
        marital_status="Married",
        num_children=1,
        num_dependent_parents=0
    )
"""


def get_va_monthly_benefit(
    rating: int,
    marital_status: str = "Single",
    num_children: int = 0,
    num_dependent_parents: int = 0,
    schoolchildren_over_18: int = 0,
) -> float:
    """
    Calculate monthly VA disability compensation based on rating and dependent status.

    Args:
        rating: VA disability rating (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
        marital_status: "Single", "Married", or "Divorced/Widowed"
        num_children: Number of children under 18 (affects spouse rating)
        num_dependent_parents: Number of dependent parents (0, 1, or 2)
        schoolchildren_over_18: Number of children over 18 in school

    Returns:
        Monthly VA benefit amount in dollars
    """

    # No disability
    if rating == 0:
        return 0.00

    # Base rates for single veteran (10%-20%)
    if rating == 10:
        return 180.42
    elif rating == 20:
        return 356.66

    # 30%-60% disability rates
    if rating in [30, 40, 50, 60]:
        rates_without_parents = {
            30: {
                "single": 552.47,
                "spouse_only": 617.47,
                "spouse_child": 666.47,
                "child_only": 595.47,
            },
            40: {
                "single": 795.84,
                "spouse_only": 882.84,
                "spouse_child": 947.84,
                "child_only": 853.84,
            },
            50: {
                "single": 1132.90,
                "spouse_only": 1241.90,
                "spouse_child": 1322.90,
                "child_only": 1205.90,
            },
            60: {
                "single": 1435.02,
                "spouse_only": 1566.02,
                "spouse_child": 1663.02,
                "child_only": 1523.02,
            },
        }

        rates_with_parents = {
            30: {
                "one_parent": 604.47,
                "two_parents": 656.47,
                "one_parent_child": 648.47,
                "two_parents_child": 700.47,
                "spouse_one_parent_child": 718.47,
                "spouse_two_parents_child": 770.47,
            },
            40: {
                "one_parent": 865.84,
                "two_parents": 935.84,
                "one_parent_child": 923.84,
                "two_parents_child": 993.84,
                "spouse_one_parent_child": 1017.84,
                "spouse_two_parents_child": 1087.84,
            },
            50: {
                "one_parent": 1220.90,
                "two_parents": 1308.90,
                "one_parent_child": 1293.90,
                "two_parents_child": 1381.90,
                "spouse_one_parent_child": 1410.90,
                "spouse_two_parents_child": 1498.90,
            },
            60: {
                "one_parent": 1540.02,
                "two_parents": 1645.02,
                "one_parent_child": 1628.02,
                "two_parents_child": 1733.02,
                "spouse_one_parent_child": 1768.02,
                "spouse_two_parents_child": 1873.02,
            },
        }

        # Calculate base rate based on dependent status
        if num_dependent_parents > 0:
            base_rates = rates_with_parents[rating]

            is_married = marital_status == "Married"
            has_children = num_children > 0

            if is_married and has_children:
                if num_dependent_parents == 1:
                    base = base_rates["spouse_one_parent_child"]
                else:
                    base = base_rates["spouse_two_parents_child"]
            elif has_children:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent_child"]
                else:
                    base = base_rates["two_parents_child"]
            elif is_married:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent"]
                else:
                    base = base_rates["two_parents"]
            else:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent"]
                else:
                    base = base_rates["two_parents"]
        else:
            base_rates = rates_without_parents[rating]

            is_married = marital_status == "Married"
            has_children = num_children > 0

            if is_married and has_children:
                base = base_rates["spouse_child"]
            elif is_married:
                base = base_rates["spouse_only"]
            elif has_children:
                base = base_rates["child_only"]
            else:
                base = base_rates["single"]

        # Add additional children
        additional_child_rates = {
            30: 32.00,
            40: 43.00,
            50: 54.00,
            60: 65.00,
        }

        # Only apply additional children if we already counted one in base (for spouse+child
        # scenario)
        if has_children and num_children > 1:
            additional = (num_children - 1) * additional_child_rates[rating]
            base += additional

        # Add schoolchildren over 18
        if schoolchildren_over_18 > 0:
            schoolchild_rates = {
                30: 105.00,
                40: 140.00,
                50: 176.00,
                60: 211.00,
            }
            base += schoolchildren_over_18 * schoolchild_rates[rating]

        return base

    # 70%-100% disability rates
    if rating in [70, 80, 90, 100]:
        rates_without_parents = {
            70: {
                "single": 1808.45,
                "spouse_only": 1961.45,
                "spouse_child": 2074.45,
                "child_only": 1910.45,
            },
            80: {
                "single": 2102.15,
                "spouse_only": 2277.15,
                "spouse_child": 2406.15,
                "child_only": 2219.15,
            },
            90: {
                "single": 2362.30,
                "spouse_only": 2559.30,
                "spouse_child": 2704.30,
                "child_only": 2494.30,
            },
            100: {
                "single": 3938.58,
                "spouse_only": 4158.17,
                "spouse_child": 4318.99,
                "child_only": 4085.43,
            },
        }

        rates_with_parents = {
            70: {
                "one_parent": 1931.45,
                "two_parents": 2054.45,
                "one_parent_child": 2033.45,
                "two_parents_child": 2156.45,
                "spouse_one_parent_child": 2197.45,
                "spouse_two_parents_child": 2320.45,
            },
            80: {
                "one_parent": 2242.15,
                "two_parents": 2382.15,
                "one_parent_child": 2359.15,
                "two_parents_child": 2499.15,
                "spouse_one_parent_child": 2546.15,
                "spouse_two_parents_child": 2686.15,
            },
            90: {
                "one_parent": 2520.30,
                "two_parents": 2678.30,
                "one_parent_child": 2652.30,
                "two_parents_child": 2810.30,
                "spouse_one_parent_child": 2862.30,
                "spouse_two_parents_child": 3020.30,
            },
            100: {
                "one_parent": 4114.82,
                "two_parents": 4291.06,
                "one_parent_child": 4261.67,
                "two_parents_child": 4437.91,
                "spouse_one_parent_child": 4495.23,
                "spouse_two_parents_child": 4671.47,
            },
        }

        # Calculate base rate
        if num_dependent_parents > 0:
            base_rates = rates_with_parents[rating]

            is_married = marital_status == "Married"
            has_children = num_children > 0

            if is_married and has_children:
                if num_dependent_parents == 1:
                    base = base_rates["spouse_one_parent_child"]
                else:
                    base = base_rates["spouse_two_parents_child"]
            elif has_children:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent_child"]
                else:
                    base = base_rates["two_parents_child"]
            elif is_married:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent"]
                else:
                    base = base_rates["two_parents"]
            else:
                if num_dependent_parents == 1:
                    base = base_rates["one_parent"]
                else:
                    base = base_rates["two_parents"]
        else:
            base_rates = rates_without_parents[rating]

            is_married = marital_status == "Married"
            has_children = num_children > 0

            if is_married and has_children:
                base = base_rates["spouse_child"]
            elif is_married:
                base = base_rates["spouse_only"]
            elif has_children:
                base = base_rates["child_only"]
            else:
                base = base_rates["single"]

        # Add additional children
        additional_child_rates = {
            70: 76.00,
            80: 87.00,
            90: 98.00,
            100: 109.11,
        }

        if has_children and num_children > 1:
            additional = (num_children - 1) * additional_child_rates[rating]
            base += additional

        # Add schoolchildren over 18
        if schoolchildren_over_18 > 0:
            schoolchild_rates = {
                70: 246.00,
                80: 281.00,
                90: 317.00,
                100: 352.45,
            }
            base += schoolchildren_over_18 * schoolchild_rates[rating]

        return base

    # Handle edge cases
    return 0.0
