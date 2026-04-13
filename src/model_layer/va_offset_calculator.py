#!/usr/bin/env python3
"""
VA Disability Below 50% Calculator - Fixed Income Logic

Handles the complex case where VA disability below 50% rating:
- REPLACES military pension (called "offset")
- Is tax-free (vs pension which is taxed)
- Results in non-dollar-for-dollar take-home change

This module provides the correct calculation for military-to-civilian transitions
with VA disability ratings.
"""

from typing import Tuple, Dict

def calculate_va_offset_income(
    pension_monthly_pretax: float,
    sbp_monthly_cost: float = 0,
    pension_pretax_deductions: float = 0,
    va_disability_rating: int = 0,
    va_monthly_benefit: float = 0,
    estimated_tax_rate: float = 0.22,
) -> Dict[str, float]:
    """
    Calculate correct take-home income considering VA disability offset.
    
    For military retirees with VA disability:
    - 50%+: Get BOTH pension (taxed) + VA disability (tax-free)
    - 20-49%: VA disability REPLACES pension (offset), but VA is tax-free
    - <20%: Only pension (VA doesn't offset at this level)
    
    Args:
        pension_monthly_pretax: Military retirement pay before taxes/deductions
        sbp_monthly_cost: SBP (Survivor Benefit Plan) deduction
        pension_pretax_deductions: Pre-tax deductions (health insurance, etc.)
        va_disability_rating: VA disability percentage (0-100)
        va_monthly_benefit: VA disability monthly amount (tax-free)
        estimated_tax_rate: Federal income tax rate (default 22%)
    
    Returns:
        Dict with keys:
        - pension_takehome: Military pension take-home
        - va_taxfree: VA disability (tax-free by law)
        - primary_income_source: Which is primary ("pension" or "va_disability")
        - total_monthly_income: Total take-home income
        - income_type: "crdp" | "offset" | "pension_only"
        - note: Explanation of calculation
    
    Examples:
        # E-5 with 30% VA at $2,800/month
        result = calculate_va_offset_income(
            pension_monthly_pretax=3000,
            va_disability_rating=30,
            va_monthly_benefit=2800
        )
        # With 20% tax rate:
        # - Pension take-home: $3,000 * (1-0.22) = $2,340
        # - VA (tax-free): $2,800
        # - Result: $2,800 take-home (VA is better, even though nominally less)
        
        # E-5 with 50%+ VA at $3,200/month
        result = calculate_va_offset_income(
            pension_monthly_pretax=3000,
            va_disability_rating=50,
            va_monthly_benefit=3200
        )
        # With 20% tax rate:
        # - Pension take-home: $3,000 * (1-0.22) = $2,340
        # - VA (tax-free): $3,200
        # - Result: $2,340 + $3,200 = $5,540 (both combined)
    """
    
    # Calculate pension take-home (after taxes and deductions)
    pension_after_sbp = max(0, pension_monthly_pretax - sbp_monthly_cost)
    pension_taxable = max(0, pension_after_sbp - pension_pretax_deductions)
    federal_tax = pension_taxable * estimated_tax_rate
    pension_takehome = pension_taxable - federal_tax
    
    # VA disability is ALWAYS tax-free (by law) - this is key to the calculation
    va_taxfree = va_monthly_benefit if va_disability_rating > 0 else 0
    
    # Determine income based on VA rating
    if va_disability_rating >= 50:
        # ===== CRDP: Concurrent Retirement & Disability Pay =====
        # Get BOTH pension (taxed) + VA disability (tax-free) combined
        income_type = "crdp"
        total_income = pension_takehome + va_taxfree
        primary_source = "both"
        note = (
            f"CRDP Eligible (50%+): Receive full military pension (${pension_takehome:,.0f}/mo after tax) "
            f"PLUS tax-free VA disability (${va_taxfree:,.0f}/mo) = ${total_income:,.0f}/mo total"
        )
    
    elif va_disability_rating >= 20:
        # ===== OFFSET to Pension: VA Replaces Pension =====
        # VA disability replaces military pension (offset)
        # But VA is tax-free, so impact is non-dollar-for-dollar
        income_type = "offset"
        
        # Compare: taxed pension vs tax-free VA
        # Use whichever provides better take-home
        if va_taxfree >= pension_takehome:
            # VA is better (common for mid-rated vets)
            total_income = va_taxfree
            primary_source = "va_disability"
            note = (
                f"Offset to Pension (20-49%): VA disability (${va_taxfree:,.0f}/mo, tax-free) "
                f"replaces military pension (${pension_takehome:,.0f}/mo, after tax). "
                f"VA is better due to tax-free advantage. Take-home: ${total_income:,.0f}/mo"
            )
        else:
            # Pension is still better
            total_income = pension_takehome
            primary_source = "pension"
            note = (
                f"Offset to Pension (20-49%): VA disability (${va_taxfree:,.0f}/mo, tax-free) "
                f"replaces military pension. Military pension (${pension_takehome:,.0f}/mo, after tax) "
                f"is higher. Take-home: ${total_income:,.0f}/mo"
            )
    
    else:
        # ===== Pension Only: <20% VA rating =====
        # VA disability does not offset pension at this level
        # Only receive military pension; VA provides healthcare access
        income_type = "pension_only"
        total_income = pension_takehome
        primary_source = "pension"
        note = (
            f"Below 20% VA Rating: Only military pension (${pension_takehome:,.0f}/mo, after tax). "
            f"VA rating {va_disability_rating}% does not offset. "
            f"VA provides healthcare access only."
        )
    
    return {
        "pension_takehome": pension_takehome,
        "va_taxfree": va_taxfree,
        "total_monthly_income": total_income,
        "primary_income_source": primary_source,
        "income_type": income_type,
        "note": note,
    }


def calculate_monthly_benefit_comparison(
    pension_monthly_pretax: float,
    va_disability_rating: int,
    va_monthly_benefit: float,
    sbp_cost: float = 0,
    pretax_deductions: float = 0,
    estimated_tax_rate: float = 0.22,
) -> Dict:
    """
    Show detailed comparison of pension vs VA disability take-home.
    
    Useful for user education: answer "What's my actual take-home with VA?"
    
    Returns:
    - pension_gross, pension_tax, pension_net
    - va_gross (same as 'net' since tax-free), va_tax (0)
    - comparison: which is better and by how much
    """
    
    # Pension calculation
    pension_after_sbp = max(0, pension_monthly_pretax - sbp_cost)
    pension_taxable = max(0, pension_after_sbp - pretax_deductions)
    pension_tax = pension_taxable * estimated_tax_rate
    pension_net = pension_taxable - pension_tax
    
    # VA calculation (always net since tax-free)
    va_net = va_monthly_benefit if va_disability_rating > 0 else 0
    
    # Comparison
    if va_net > pension_net:
        difference = va_net - pension_net
        comparison_text = f"VA disability is better by ${difference:,.0f}/month (${difference*12:,.0f}/year)"
        better_choice = "va_disability"
    elif pension_net > va_net:
        difference = pension_net - va_net
        comparison_text = f"Military pension is better by ${difference:,.0f}/month (${difference*12:,.0f}/year)"
        better_choice = "pension"
    else:
        comparison_text = "Pension and VA disability are equal"
        better_choice = "equal"
    
    return {
        "pension": {
            "gross": pension_monthly_pretax,
            "after_sbp": pension_after_sbp,
            "taxable": pension_taxable,
            "federal_tax": pension_tax,
            "tax_rate": estimated_tax_rate,
            "net_takehome": pension_net,
        },
        "va_disability": {
            "gross": va_monthly_benefit,
            "federal_tax": 0,
            "tax_rate": 0,
            "note": "Tax-free by law",
            "net_takehome": va_net,
        },
        "comparison": {
            "text": comparison_text,
            "better_choice": better_choice,
            "difference": abs(va_net - pension_net),
        },
    }


if __name__ == "__main__":
    # Example 1: E-5 with 30% VA rating
    print("=" * 80)
    print("EXAMPLE 1: E-5 with 30% VA Rating (OFFSET scenario)")
    print("=" * 80)
    
    result = calculate_va_offset_income(
        pension_monthly_pretax=3000,
        va_disability_rating=30,
        va_monthly_benefit=2800,
        sbp_monthly_cost=50,
        pension_pretax_deductions=100,
    )
    
    print(f"Income Type: {result['income_type']}")
    print(f"Pension Take-home: ${result['pension_takehome']:,.0f}/mo")
    print(f"VA (Tax-free): ${result['va_taxfree']:,.0f}/mo")
    print(f"Primary Source: {result['primary_income_source']}")
    print(f"Total Take-home: ${result['total_monthly_income']:,.0f}/mo")
    print(f"\nNote: {result['note']}")
    
    # Example 2: E-5 with 50% VA rating
    print("\n" + "=" * 80)
    print("EXAMPLE 2: E-5 with 50% VA Rating (CRDP scenario)")
    print("=" * 80)
    
    result = calculate_va_offset_income(
        pension_monthly_pretax=3000,
        va_disability_rating=50,
        va_monthly_benefit=3200,
        sbp_monthly_cost=50,
        pension_pretax_deductions=100,
    )
    
    print(f"Income Type: {result['income_type']}")
    print(f"Pension Take-home: ${result['pension_takehome']:,.0f}/mo")
    print(f"VA (Tax-free): ${result['va_taxfree']:,.0f}/mo")
    print(f"Primary Source: {result['primary_income_source']}")
    print(f"Total Take-home: ${result['total_monthly_income']:,.0f}/mo")
    print(f"\nNote: {result['note']}")
    
    # Example 3: Detailed comparison
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Detailed Pension vs VA Comparison")
    print("=" * 80)
    
    comparison = calculate_monthly_benefit_comparison(
        pension_monthly_pretax=3000,
        va_disability_rating=30,
        va_monthly_benefit=2800,
        sbp_cost=50,
        pretax_deductions=100,
    )
    
    print("\nPENSION (Taxable):")
    print(f"  Gross: ${comparison['pension']['gross']:,.0f}")
    print(f"  Less SBP: ${comparison['pension']['after_sbp']:,.0f}")
    print(f"  Taxable: ${comparison['pension']['taxable']:,.0f}")
    print(f"  Federal Tax ({comparison['pension']['tax_rate']*100:.0f}%): -${comparison['pension']['federal_tax']:,.0f}")
    print(f"  Take-home: ${comparison['pension']['net_takehome']:,.0f}")
    
    print("\nVA DISABILITY (Tax-free):")
    print(f"  Gross: ${comparison['va_disability']['gross']:,.0f}")
    print(f"  Federal Tax: $0 (tax-free by law)")
    print(f"  Take-home: ${comparison['va_disability']['net_takehome']:,.0f}")
    
    print("\nCOMPARISON:")
    print(f"  {comparison['comparison']['text']}")
    print(f"  Better choice: {comparison['comparison']['better_choice']}")
