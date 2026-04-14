# Sample Budget Profiles for Testing

This folder contains 6 realistic budget CSV files representing **diverse military profiles** with spending that scales appropriately by rank and family size. Use these to test ProjectAtlas without creating your own budget data.

## Available Profile Budgets

| File | Profile | Monthly | Family Type |
|------|---------|---------|-------------|
| **E4_Single_Barracks.csv** | E-4 Single, Barracks | ~$1,370 | Junior enlisted, lives in barracks |
| **E5_Single_1Kid.csv** | E-5 Single, 1 Kid | ~$3,900 | Mid-enlisted, single parent |
| **E6_Married_NoKids.csv** | E-6 Married, No Kids | ~$4,425 | Senior enlisted, marriage, no dependents |
| **E8_Single_1Kid.csv** | E-8 Single, 1 Kid | ~$4,820 | Senior enlisted (Master Sergeant), single parent |
| **O1_Married_2Kids.csv** | O-1 Married, 2 Kids | ~$6,050 | Junior officer, family with 2 children |
| **O4_Married_3Kids.csv** | O-4 Married, 3 Kids | ~$8,385 | Senior officer (Major), large family |

## Spending Analysis by Rank

**Notice how expenses scale with rank:**

- **E-4 (barracks)**: $1,370 — basic living, no family
- **E-5 (with child)**: $3,900 — childcare adds ~$1,050/mo
- **E-6 (married)**: $4,425 — 2-income household, homes
- **E-8 (with child)**: $4,820 — high rank supports lifestyle + childcare
- **O-1 (married + 2 kids)**: $6,050 — officer housing, larger family
- **O-4 (married + 3 kids)**: $8,385 — senior officer, maximum complexity

## Key Variables Tested

✅ **Rank progression** — E4 → E5 → E6 → E8 → O1 → O4  
✅ **Living situations** — Barracks → Apartment → Mortgage  
✅ **Family complexity** — Single → Single parent → Married → Married + kids  
✅ **Childcare impact** — How single parents vs couples manage daycare costs  
✅ **Housing costs** — BAH/rent by rank and location  
✅ **Discretionary spending** — Dining, entertainment, activities scale with rank

---

## How to Use

### Quick Load in Step 8 (Classification)
When you reach **Step 8: Income & Expense Classification**, click the "📁 Load Sample Budget" button to see quick-load options for all 6 profiles. Select one and it will auto-populate your expense data.

### Manual Load
1. Open the wizard
2. Go to **Step 8: Income & Expense Classification**
3. Click "Select your YNAB/expense CSV file" file uploader
4. Navigate to `sample_budgets/` folder
5. Select the profile that matches your scenario (or create your own test variation)
6. Click "📥 Load File"

## CSV Format

Each file has the standard format:
```
Date,Description,Amount
2025-01-05,Rent/Mortgage Payment,1800
2025-01-07,Electricity and Gas,145
...
```

**Note:** The wizard uses this CSV to:
1. Parse all transactions
2. Auto-classify by category (mandatory, negotiable, optional, prepaid)
3. Calculate monthly expense totals
4. Enable what-if scenario testing

## Testing Tips

### Testing the "Common Sense Test"

Use these profiles to verify financial calculations:

1. **Profile Progression Test**
   - Run E5_Single → E5_Married_NoKids → E7_Married_1Kid
   - Verify: Expenses should scale with rank and dependents
   - Expected: Runway decreases as expenses increase (same savings)

2. **Single Parent Test**  
   - Compare O3_Single_1Kid vs O2_Married_2Kids
   - Verify: Single parent has ~$1,200 more monthly childcare burden
   - Expected: Runway impact clearly shown

3. **Large Family Test**
   - Run O5_Married_3Kids with varying civilian job salaries
   - Verify: Tool correctly handles $8,500/month expense base
   - Expected: Family needs ~$6,500+ monthly income to stay positive

4. **No-Kid Baseline**
   - E5_Married_NoKids as reference point
   - Verify: This is "minimum complexity" scenario
   - Expected: Tool handles basic married couple budgeting

## Customizing Profiles

To create your own test profile:

1. Copy any file: `E5_Single.csv` → `MyTestProfile.csv`
2. Edit in Excel or text editor:
   - Adjust amounts to match your scenarios
   - Add/remove expense items as needed
   - Keep the Date, Description, Amount columns
3. Save as CSV
4. Load in Step 8 of the wizard

## What Gets Auto-Classified

The wizard automatically sorts expenses into:

- **Mandatory** (≥$200/mo): Rent, utilities, insurance, healthcare, childcare
- **Negotiable** ($50-$200/mo): Groceries, household, transportation, some insurance
- **Optional** (<$50/mo): Dining out, entertainment, gym, personal care
- **Prepaid** (annual/semi-annual): Insurance renewals, healthcare, travel

**Example from E5_Single.csv:**
```
Mandatory: Rent ($1,450) + Utilities ($100) + ... = $2,000/mo
Negotiable: Groceries ($385) + Gas ($160) = $545/mo  
Optional: Dining Out ($95) + Gym ($50) + Entertainment ($40) = $185/mo
Prepaid: Insurance ($15/mo reserve for annual renewals)
TOTAL: ~$2,670/month
```

## Accuracy Notes

- Amounts are **realistic averages** for 2025-2026 military households
- They DO NOT represent any specific person
- They're based on:
  - BAH rates by region (VA/MD/DC area assumed)
  - Military pay scales (E4-O6 range)
  - TRICARE healthcare costs (not VA-specific)
  - Typical expense patterns from military family surveys
  - Childcare at military fair-market rates

## Troubleshooting

**"CSV won't load"**
- Verify three columns: Date, Description, Amount
- Date format: YYYY-MM-DD works best
- Amount: decimal numbers with no $ symbol

**"Expenses don't match my situation"**
- These are templates, not targets
- Edit the file to match YOUR actual expenses
- Use real bank data for accuracy testing

**"I want different profiles"**
- Create your own CSV following the format
- Place in this folder
- They'll auto-appear in the quick-load menu

---

**Ready to test?** Load a profile in Step 8 and start the "common sense test"! 🧪
