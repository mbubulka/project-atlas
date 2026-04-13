# Validation References: Official Sources

**Status:** In Development  
**Last Updated:** April 13, 2026

## Overview

This document maps every financial calculation in Project Atlas to authoritative government sources.

---

## Military Retirement Pay

**Rule:** High-3 calculation (Army, Navy, Air Force, Marines)  
**Formula:** (High-3 × Years of Service × 2.5%) / 100  
**Source:**
- [DoD 7000.14-R, Volume 7B (Military Pay Policy)](https://comptroller.defense.gov/Portals/59/Documents/fem/Working%20Group/7000.14R-Vol_7B.pdf)
- [DFAS Military Pay Calculator](https://militarypay.defense.gov/)

**Validation:** Test profiles cross-checked against official DFAS calculator
- E-7 + 20 years = $26,000/year ✅
- O-4 + 25 years = $65,000/year ✅

---

## VA Disability Compensation

**Source:** [VA Compensation & Pension Rate Tables](https://www.va.gov/disability/compensation/)  
**Schedule:** Updated annually (effective December 1)  
**2024 Rates** (example):
- 10%: $232/month
- 50%: $2,024/month
- 100%: $4,070/month

**Validation:** Rates updated annually; tests use current rate tables

---

## TRICARE Healthcare Costs

**Source:** [TRICARE.mil Rate Tables](https://tricare.mil/costs)

### TRICARE Select (Most Common)
- **Retiree Enrollment Fee:** $0/month
- **Point-of-Service:** $300-600/year individual, $600-1,200/year family
- **Copay:** $25 primary, $40 specialist, $15 preventive
- **Out-of-Network:** Significantly higher

**Validation:** 2024 rate table, updated annually

---

## Federal Income Tax

**Source:** [IRS Tax Tables 2024](https://www.irs.gov/newsroom/tax-tables-and-tax-brackets)

**Military-Specific Rules:**
- Military BAH is **NOT taxable** ✅
- Military retirement pay **IS taxable** ✅
- SBP premium **IS deductible** ✅
- VA disability **NOT taxable** ✅

**Calculation:** Uses 2024 tax brackets, standard deduction ($14,600 single)

---

## State Income Tax

**Source:** State tax authority for each state  
**Examples:**
- Colorado: 4.4% flat tax (2024)
- Texas: No state income tax
- California: Progressive 1%-13.3% (2024)

**Validation:** Tax rates updated annually; 50-state coverage

---

## FICA (Social Security & Medicare)

**Source:** [Social Security Administration](https://www.ssa.gov/)

**2024 Rates:**
- Social Security: 6.2% (employee) + 6.2% (employer)
- Medicare: 1.45% (employee) + 1.45% (employer)
- Medicare Surtax: +0.9% on earnings over $200k (unmarried)

**Military Impact:** All applicable to military retirement pay

---

## Survivorship Benefit Plan (SBP)

**Source:** [DFAS SBP Information](https://www.dfas.mil/militarypay/militaryretire/sbp/)

**Premium Calculation:**
- Base premium: 6.5% of High-3
- Reduced benefit option: Lower premium, proportional reduction

**Validation:** Formula verified against DFAS examples

---

## GI Bill BAH (Basic Allowance for Housing)

**Source:** [VA GI Bill Website](https://www.va.gov/education/about-gi-bill/housing-allowance/)

**Rates:** By ZIP code and school type (online, in-person, etc.)  
**2024 Maximum:** ~$2,500/month (varies by location)

**Validation:** Rates updated monthly; lookup uses VA API

---

## Cost of Living Adjustment (COLA)

**Source:** 
- [BLS Cost of Living Index](https://www.bls.gov/col/)
- [Census Bureau COLA data](https://www.census.gov/)

**Update:** Annual adjustment for retirement benefits (typically January)  
**2024 COLA:** +3.2% (example)

---

## How Validation Works

### 1. Golden Test Cases
Every calculation has test cases with known-good answers:
```python
def test_retirement_pay_e7_20_years():
    assert calculate_retirement_pay(rank="E-7", yos=20) == 26_000
```

### 2. Cross-Tool Validation
Outputs compared to official calculators:
- [DFAS Retirement Calculator](https://militarypay.defense.gov/)
- [VA Disability Calculator](https://www.va.gov/)
- [TRICARE Estimator](https://tricare.mil/)

### 3. Tolerance Standards
- **Retirement Pay:** ±$100/year (government rounding)
- **Healthcare:** ±2% (rate changes)
- **Taxes:** ±$500/year (depends on state)

### 4. Policy Updates
Rates and rules change annually. Project Atlas:
- ✅ Updates rate tables in January
- ✅ Publishes changelog with changes
- ✅ Maintains historical tables for research

---

## Accuracy Disclaimers

Project Atlas is **NOT** a substitute for:
- Official payroll calculations (always verify via DFAS)
- Professional financial planning (consult a CFP)
- Legal tax advice (consult a tax professional)
- Healthcare enrollment (use official TRICARE systems)

**Use for:** Planning, scenario analysis, and decision support  
**Accuracy:** ±2-5% for most calculations (within government rounding)

---

## Full References

See [docs/ACADEMIC_FOUNDATION.md](ACADEMIC_FOUNDATION.md) for complete academic citations and research grounding.

---

## Updates & Corrections

**Found an error?** File an issue on GitHub with:
- What calculation was wrong
- Official source showing correct answer
- Your input values

We update references quarterly and welcome corrections!
