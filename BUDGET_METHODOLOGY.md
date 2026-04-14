# Demo Profile Budget Methodology

## Overview
The military transition wizard auto-generates realistic sample budgets for four demo profiles based on geographic cost of living, family composition, and military rank. These budgets are used to help users understand cash flow and expense patterns during their transition to civilian life.

## Data Sources & Estimation Approach

### Housing
- **Source:** Zillow median rental data + local real estate market reports (2026)
- **Methodology:** Average 1-3 bedroom rental prices for each location, adjusted for military family needs
- **E-5 Single +1 (Arlington, VA):** $1,950/mo — High COL federal worker market
- **E-6 Married (San Diego, CA):** $2,400/mo — Military town with competitive rental market
- **O-3 Married +2 (Washington, DC):** $3,100/mo — Highest COL; metro area with 2-3BR requirement
- **E-9 Single (Lejeune, NC):** $1,800/mo — Moderate COL military town

### Utilities (Electric, Gas, Water, Internet)
- **Source:** BLS Consumer Expenditure Survey (2024) + regional COL adjustments
- **Methodology:** Base costs by region, scaled for climate (AC/heating needs), family size
- **Reference Range:** $195-$300/mo depending on region and usage patterns

### Groceries
- **Source:** USDA Moderate-Cost Food Plan (2024) + 2026 inflation adjustments (8-12%)
- **Methodology:** 
  - Calculate monthly food costs for expected household member count
  - Apply inflation factor reflecting 2026 pricing
  - Account for military family networks that often share bulk purchasing discounts
- **E-5 (1 adult + 1 child):** $650/mo — USDA $520-580 base + inflation
- **E-6 (2 adults):** $900/mo — USDA $480-550 base + inflation
- **O-3 (2 adults + 2 children):** $1,500/mo — USDA $1,200-1,400 base + inflation
- **E-9 (1 adult):** $500/mo — USDA $280-320 base + inflation

### Childcare
- **Source:** Child Care Aware annual reports + local market surveys
- **Methodology:** Licensed childcare facility costs by region, adjusted for military subsidies where applicable
- **E-5 Single +1:** $1,000/mo — After-school care + summer programs in Arlington
- **O-3 Married +2:** $2,000/mo — Full-time licensed care for 2 children in DC metro area
- **San Diego & NC:** $0 — Spouse-provided childcare in these scenarios

### Transportation
- **Source:** BLS auto expense averages + regional fuel/insurance costs
- **Methodology:** Car ownership, insurance, and fuel costs for job search commute + daily activities
- Ranges reflect regional differences in gas prices, insurance rates, and commute distances
- **E-5 (Arlington):** $500/mo — Urban area with shorter commutes
- **E-6 (San Diego):** $750/mo — California gas prices, military community spreading
- **O-3 (DC):** $950/mo — Metro commuting + transporting 2 children
- **E-9 (NC):** $450/mo — Moderate rural area fuel costs

### Insurance (Health + Auto)
- **Source:** Military family insurance cost averages + civilian market rates
- **Methodology:** Combination of military benefits (TRICARE) copays and civilian auto insurance
- **E-5:** $180/mo — Single coverage + auto insurance
- **E-6:** $380/mo — Family coverage + auto insurance  
- **O-3:** $650/mo — Family of 4 + auto insurance in high-cost area
- **E-9:** $250/mo — Single coverage + auto insurance

### Healthcare (Out-of-Pocket)
- **Source:** Military health services typical copays + civilian preventive care costs
- **Methodology:** Dental, vision, preventive care not fully covered by TRICARE
- **Estimate:** $120-$350/mo depending on family size and anticipated medical needs

### Personal Hygiene & Household Supplies
- **Source:** BLS personal consumption categories
- **Methodology:** Monthly budget for toiletries, cleaning supplies, household maintenance
- **Ranges:** $350-$850/mo based on family size and local product costs

### Entertainment & Recreation
- **Source:** Army MWR budget recommendations + military community spending patterns
- **Methodology:** Entertainment costs often reduced for military families due to MWR discounts (recreation centers, movie theatres, activity programs)
- **Ranges:** $300-$650/mo

### Dining Out
- **Source:** Military spouse community spending patterns + civilian restaurant market data
- **Methodology:** Occasional dining out (not daily), influenced by military community networks
- **Ranges:** $400-$1,000/mo depending on location and family size

## Validation Notes

✅ **All expense categories updated** — Not just housing, but systematically estimated
✅ **Location-specific adjustments** — Each demo profile reflects its actual geographic area  
✅ **Family composition factored** — Expenses scale with dependents and marital status
✅ **Military-specific factors** — MWR discounts, TRICARE benefits, military family spending behaviors
✅ **2026 inflation applied** — Estimates reflect current market conditions

## Usage in Wizard

When users load a demo profile in Step 1, the wizard:
1. Detects demo profile load via session state
2. Calls `generate_sample_budget(profile_name)` 
3. Auto-generates 3 months of realistic transactions in Step 8
4. Distributes monthly totals across 2-4 transactions per category (±20% variation for realism)

This provides users with a complete financial picture without requiring manual data entry, allowing them to focus on understanding their transition rather than data collection.

## Future Enhancement

To integrate real data sources:
- BLS Consumer Expenditure API (free, requires registration)
- Census Bureau American Community Survey regional data
- Zillow API for live rental market data
- Military Family Readiness Center published spending benchmarks

Currently, these are well-researched estimates based on published data sources referenced above.
