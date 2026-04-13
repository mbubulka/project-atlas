"""
Pure functional tax calculator - no state, no closures, deterministic only.

Handles federal and state tax calculations for military retirement income.
VA compensation is excluded (tax-free).
"""


def calculate_federal_tax(taxable_income: float, filing_status: str = "married_jointly") -> float:
    """
    Calculate federal tax using 2026 IRS tax brackets.
    
    Args:
        taxable_income: Income after standard deduction (already reduced)
        filing_status: "married_jointly", "single", "head_of_household"
    
    Returns:
        Federal tax amount (float)
    """
    # 2026 Tax brackets (IRS)
    brackets = {
        "married_jointly": [
            (23200, 0.10),      # 10% up to $23,200
            (94300, 0.12),      # 12% from $23,200 to $94,300
            (201050, 0.22),     # 22% from $94,300 to $201,050
            (383900, 0.24),     # 24% from $201,050 to $383,900
            (487450, 0.32),     # 32% from $383,900 to $487,450
            (731200, 0.35),     # 35% from $487,450 to $731,200
            (float('inf'), 0.37) # 37% over $731,200
        ],
        "single": [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ],
        "head_of_household": [
            (17400, 0.10),
            (66550, 0.12),
            (169550, 0.22),
            (257350, 0.24),
            (308300, 0.32),
            (931200, 0.35),
            (float('inf'), 0.37)
        ]
    }
    
    if taxable_income <= 0:
        return 0.0
    
    brackets_list = brackets.get(filing_status, brackets["married_jointly"])
    tax = 0.0
    previous_limit = 0.0
    
    for bracket_limit, rate in brackets_list:
        if taxable_income <= previous_limit:
            break
        
        # Calculate income in this bracket
        income_in_bracket = min(taxable_income, bracket_limit) - previous_limit
        tax += income_in_bracket * rate
        previous_limit = bracket_limit
    
    return max(0.0, tax)


def calculate_standard_deduction(filing_status: str = "married_jointly") -> float:
    """
    Return 2026 standard deduction based on filing status.
    
    Args:
        filing_status: "married_jointly", "single", "head_of_household"
    
    Returns:
        Standard deduction amount (float)
    """
    standard_deductions = {
        "married_jointly": 23200,
        "single": 11600,
        "head_of_household": 17400,
    }
    return standard_deductions.get(filing_status, 23200)


def calculate_state_tax(taxable_income: float, state: str, military_pension_included: bool = True) -> float:
    """
    Calculate state tax accounting for military pension exemptions.
    
    Args:
        taxable_income: Annual gross pension income (before any deductions)
        state: Two-letter state code (VA, NC, MD, etc.)
        military_pension_included: Whether to apply military pension exemption
    
    Returns:
        Annual state tax amount (float)
    """
    # State-specific military pension exemptions (ANNUAL amounts)
    exemptions = {
        "VA": 40000.0,           # Virginia: $40k annual exemption
        "NC": float('inf'),      # North Carolina: full exemption
        "TX": 0.0,               # Texas: no state income tax
        "FL": 0.0,               # Florida: no state income tax
        "WA": 0.0,               # Washington: no state income tax
        "DC": 0.0,               # DC: no exemption
        "MD": 0.0,               # Maryland: no exemption
        "PA": 0.0,               # Pennsylvania: no exemption
        "CA": 0.0,               # California: no exemption
        "NY": 0.0,               # New York: no exemption
    }
    
    # State tax rates (2026 averages)
    tax_rates = {
        "VA": 0.04,              # Virginia: ~4% average (2-5.75% brackets)
        "NC": 0.00,              # North Carolina: 0% (fully exempt)
        "TX": 0.00,              # Texas: 0% (no income tax)
        "FL": 0.00,              # Florida: 0% (no income tax)
        "WA": 0.00,              # Washington: 0% (no income tax)
        "DC": 0.0675,            # DC: 6.75%
        "MD": 0.0575,            # Maryland: 5.75%
        "PA": 0.0307,            # Pennsylvania: 3.07% (flat)
        "CA": 0.093,             # California: 9.3%
        "NY": 0.065,             # New York: 6.5%
    }
    
    if taxable_income <= 0:
        return 0.0
    
    exemption = exemptions.get(state, 0.0) if military_pension_included else 0.0
    rate = tax_rates.get(state, 0.05)  # Default 5% for unknown states
    
    # Apply exemption (ANNUAL amounts)
    taxable = max(0.0, taxable_income - exemption)
    tax = taxable * rate
    
    return max(0.0, tax)


def calculate_net_income(
    gross_income: float,
    filing_status: str = "married_jointly",
    state: str = "VA",
    pre_tax_deductions: float = 0.0,
    va_disability_income: float = 0.0,
    va_disability_rating: int = 0
) -> dict:
    """
    Pure function: Calculate net income after federal and state taxes with VA offset logic.
    
    Args:
        gross_income: DFAS military retirement income (monthly in dollars)
        filing_status: "married_jointly", "single", "head_of_household"
        state: Two-letter state code
        pre_tax_deductions: Health insurance, SBP, LTC, etc. (monthly in dollars)
        va_disability_income: VA compensation amount (monthly, tax-free)
        va_disability_rating: VA rating percentage (0-100)
    
    Returns:
        Dictionary with:
            - federalTax: Federal tax amount (monthly)
            - stateTax: State tax amount (monthly)
            - netIncome: Take-home after taxes (monthly)
            - totalIncome: Gross + VA disability (monthly)
            - taxableIncome: Income subject to taxation (monthly)
    """
    # IMPORTANT: Convert monthly to annual for tax calculations
    # Tax brackets and exemptions are annual, so we must work with annual figures
    
    gross_annual = gross_income * 12.0
    deductions_annual = pre_tax_deductions * 12.0
    va_annual = va_disability_income * 12.0
    
    # VA OFFSET LOGIC (for ratings below 50%)
    # Under 50%: VA disability REPLACES/OFFSETS the pension portion
    # The offset amount is NOT taxed (it's tax-free VA)
    # Reduce gross pension by the offset amount for tax purposes
    if va_disability_rating < 50 and va_disability_income > 0:
        # VA offsets the pension - reduce taxable income by VA amount
        taxable_pension_annual = max(0.0, gross_annual - va_annual)
    else:
        # 50%+ (CRDP): Both pension and VA are received, only pension is taxed
        taxable_pension_annual = gross_annual
    
    # Adjust taxable pension by pre-tax deductions
    adjusted_taxable_pension_annual = taxable_pension_annual - deductions_annual
    
    # Get standard deduction (annual)
    standard_deduction_annual = calculate_standard_deduction(filing_status)
    
    # Calculate taxable income after standard deduction
    taxable_income_annual = max(0.0, adjusted_taxable_pension_annual - standard_deduction_annual)
    
    # Calculate federal tax on the reduced taxable income
    federal_tax_annual = calculate_federal_tax(taxable_income_annual, filing_status)
    
    # Calculate state tax on adjusted pension (with VA offset applied)
    state_tax_annual = calculate_state_tax(adjusted_taxable_pension_annual, state, military_pension_included=True)
    
    # Convert back to monthly
    federal_tax_monthly = federal_tax_annual / 12.0
    state_tax_monthly = state_tax_annual / 12.0
    
    # Calculate net income (pension take-home ONLY, NO VA disability included)
    # VA disability is TAX-FREE and added separately in combined take-home
    adjusted_gross_monthly = adjusted_taxable_pension_annual / 12.0
    net_income_monthly = adjusted_gross_monthly - federal_tax_monthly - state_tax_monthly
    
    # Total income = pension take-home + VA disability (when combined later)
    # But return them separately so caller controls the math
    
    return {
        "federalTax": round(federal_tax_monthly, 2),
        "stateTax": round(state_tax_monthly, 2),
        "netIncome": round(net_income_monthly, 2),  # Pension take-home ONLY
        "totalIncome": round(adjusted_gross_monthly + va_disability_income, 2),  # If combined
        "taxableIncome": round(taxable_income_annual / 12.0, 2),
    }


# Example usage (for testing)
if __name__ == "__main__":
    # Test case: $8,474 gross pension, $27 healthcare (VA, married)
    result = calculate_net_income(
        gross_income=8474,
        filing_status="married_jointly",
        state="VA",
        pre_tax_deductions=27,  # Healthcare + SBP
        va_disability_income=947.84
    )
    print(result)
