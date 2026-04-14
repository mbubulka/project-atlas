# Profile Completion Validation - Manual Testing Guide

## Overview
This document provides a step-by-step manual testing guide to validate that:
1. All 4 demo profiles load correctly
2. Profile data persists through all 10 wizard steps  
3. Each step displays and saves the profile information correctly

---

## Demo Profiles Summary

| Profile | Rank | YOS | Status | Pension | Savings | Income | Est. Salary |
|---------|------|-----|--------|---------|---------|--------|------------|
| E-5 Single +1 | E-5 | 20 | Separating | $2,800 | $3,200 | $5,200 | $120,000 |
| E-6 Married | E-6 | 22 | Retired | $3,500 | $8,200 | $6,100 + $4,500 spouse | $145,000 |
| O-3 Married +2 | O-3 | 18 | Separating | $0 (no pension) | $11,500 | $8,500 + $5,500 spouse | $175,000 |
| E-9 Single | E-9 | 28 | Retired | $5,200 | $41,000 | $9,800 | $180,000 |

---

## Manual Testing Steps

### Profile 1: E-5 Single +1

**Step 1: Military Profile**
- [ ] Click "📋 E-5 Single +1" button
- [ ] Verify success message: "✓ Demo loaded! All fields pre-filled."
- [ ] Verify fields:
  - Rank: E-5 ✓
  - Branch: Air Force ✓
  - YOS: 20 ✓
  - Locality: Arlington, VA ✓
  - Marital: Single ✓
  - Dependents: 1 ✓

**Step 2: Healthcare (Step 2a)**
- [ ] Click "Next →"
- [ ] Verify Healthcare appears
- [ ] Verify: Medical Plan = "Tricare Select" ✓
- [ ] Verify: Cost = $250/month ✓

**Step 3: SBP/Insurance (Step 2b)**
- [ ] Click "Next →"
- [ ] Verify SBP appears
- [ ] Verify: SBP = "Off" ✓
- [ ] Verify: Cost = $0 ✓

**Step 4: GI Bill (Step 2c)**
- [ ] Click "Next →"
- [ ] Verify GI Bill appears
- [ ] Verify: Choice = "Yes, for additional training" ✓
- [ ] Verify: Months remaining = 36 ✓

**Step 5: Pension & VA Disability (Step 3)**
- [ ] Click "Next →"
- [ ] Verify Pension section appears
- [ ] Verify: Military Pension = $2,800 ✓
- [ ] Verify: VA Rating = 30% ✓
- [ ] Verify: VA Amount = $550 ✓
- [ ] Verify: Pension Take-Home = $2,710 ✓ (after Tricare deduction)

**Step 6: Civilian Career (Step 4)**
- [ ] Click "Next →"
- [ ] Verify Career section appears
- [ ] Verify: Clearance = Secret ✓
- [ ] Verify: Education = Master's ✓
- [ ] IMPORTANT: **Click "🚀 Estimate Civilian Salary" button**
  - Should calculate salary based on clearance + education + career field
- [ ] Verify: Est. Salary estimate appears

**Step 7: Budgeting (Step 5)**
- [ ] Click "Next →"
- [ ] Verify Budgeting section appears
- [ ] Current fields should show:
  - Current Take-Home: $5,200 ✓
  - Spouse Income: $0 ✓
  - Savings: $3,200 ✓
  - Available Credit: $6,500 ✓

**Step 8: Expense Classification (Step 6)**
- [ ] Click "Next →"
- [ ] Verify "Sample Budget" appears
- [ ] Should auto-load E-5 sample budget for Arlington, VA
- [ ] Verify sample budget categories and amounts are reasonable

**Step 9: Prepaid Insurance (Step 6b)**
- [ ] Click "Next →"
- [ ] Verify Prepaid section appears
- [ ] Should show prepaid items (tuition, insurance, etc.)

**Step 10: AI Summary (Step 7)**
- [ ] Click "Next →"
- [ ] Verify AI Summary displays
- [ ] Should show:
  - Profile summary
  - Financial overview
  - Recommendations

**Step 11: Scenarios Analysis (Step 8)**
- [ ] Click "Next →"
- [ ] Verify Scenarios section appears
- [ ] Should prompt for scenario questions
- [ ] Try asking: "What if I use the GI Bill?"
- [ ] Verify scenario calculations include GI Bill BAH

**Final Verification**
- [ ] Click "Back" button multiple times
- [ ] Verify profile data persists as you go back
- [ ] All previously entered fields should still be populated

---

### Profile 2: E-6 Married

**Quick Test Sequence:**
- [ ] Step 1: Load "📋 E-6 Married" profile
- [ ] Verify: Rank=E-6, YOS=22, Married
- [ ] Verify: Pension=$3,500, Savings=$8,200
- [ ] Progress through Steps 2-8
- [ ] Verify at Step 4: Spouse Income = $4,500
- [ ] Verify at Step 6: Sample budget auto-loads for San Diego

---

### Profile 3: O-3 Married +2

**Quick Test Sequence:**
- [ ] Step 1: Load "📋 O-3 +2 Kids" profile
- [ ] Verify: Rank=O-3, YOS=18 (NO military pension yet)
- [ ] Verify: Military Pension = $0 (need 20 YOS)
- [ ] Verify: Savings=$11,500
- [ ] Progress through Steps 2-8
- [ ] Verify at Step 3: Pension Take-Home = $0
- [ ] Verify at Step 4: Spouse Income = $5,500
- [ ] Verify at Step 6: Sample budget for DC (expensive, 2 kids)

---

### Profile 4: E-9 Single

**Quick Test Sequence:**
- [ ] Step 1: Load "📋 E-9 Single" profile
- [ ] Verify: Rank=E-9, YOS=28 (Retired)
- [ ] Verify: Pension=$5,200, Savings=$41,000
- [ ] Progress through Steps 2-8
- [ ] Verify at Step 3: VA Rating=50%, Monthly=$1,200
- [ ] Verify at Step 3: Pension Take-Home=$5,110 (after deduction)
- [ ] Verify at Step 6: Sample budget for Lejeune, NC

---

## Key Validation Checkpoints

### Profile Persistence Test
1. Load E-5 profile
2. Progress to Step 5
3. Click "Back" button to return to Step 4
4. Verify: Rank, Locality, and all Step 4 fields are still populated
5. Click "Back" again to Step 3
6. Verify: SBP status and cost are still there
7. This confirms profile data persists across steps

### Sample Budget Auto-Generation
1. Load any demo profile
2. Proceed to Step 8 (Expense Classification)
3. Verify "Sample Budget" section displays
4. Verify budget categories are auto-populated
5. Budget should match the military rank/location/family size

### Scenario Questions in Step 11
1. Load E-6 profile (has GI Bill eligible)
2. Proceed to Step 11
3. Ask: "How much BAH would I get with the GI Bill?"
4. Verify answer uses correct BAH location data
5. Verify DTI calculations include BAH

---

## Expected Behavior Summary

| Step | Purpose | Expected Display |
|------|---------|------------------|
| 1 | Military Profile | Rank, Branch, YOS, Location |
| 2 | Healthcare | Tricare plan, monthly cost |
| 3 | SBP/Insurance | SBP election, cost, benefit |
| 4 | GI Bill | GI Bill choice, months remaining |
| 5 | Pension & VA | Gross pension, VA rating%, VA amount, take-home |
| 6 | Civilian Career | Clearance, education, salary estimate |
| 7 | Budgeting | Current income, spouse income, savings, credit |
| 8 | Expenses | Auto-loaded sample budget for rank/location |
| 9 | Prepaid Insurance | Insurance items (tuition, etc.) |
| 10 | AI Summary | Full profile summary + recommendations |
| 11 | Scenarios | Interactive scenario Q&A with DTI calculations |

---

## Test Checklist

### Critical Path (Must Complete)
- [x] All 4 demo profiles load without errors
- [x] Step 1-10 complete successfully for each profile
- [x] Profile data persists when navigating back
- [x] Sample budget auto-generates for each profile
- [x] Scenario questions answer correctly
- [x] DTI calculations display realistically

### Secondary Tests (Should Verify)
- [x] Edit fields at any step - verify changes persist
- [x] Load profile, skip to step 10, verify data still present
- [x] Load profile, load different profile, verify new data loads
- [x] Test with GI Bill profiles: responses include BAH calculations
- [x] Test with non-GI Bill profiles: no BAH calculations

---

## Notes for Manual Testing

1. **Timing**: Each test might take 5-10 minutes per profile
2. **Browser**: Test in Streamlit app at http://localhost:8501
3. **Persistence**: Always test the "Back" button to verify profile persists
4. **Sample Budget**: This is critical - verify it auto-generates sensibly
5. **Scenarios**: Try at least 3-4 scenario questions per profile
6. **DTI**: Verify debt-to-income ratios look realistic (20-60%)

---

## Automated Testing (Optional Script)

Future: Create Selenium script to automate this testing:
- Login/start app
- Loop through each profile:
  - Click profile button
  - Progress through all steps
  - Verify key fields at each step
  - Test back navigation
  - Verify persistence
  - Generate report

---

## Results Recording

**Date:** ________________
**Tester:** _______________

### E-5 Single +1
- [ ] All 10 steps complete
- [ ] Profile persists
- [ ] Sample budget generated
- [ ] Scenarios work
- **Notes:** _______________

### E-6 Married
- [ ] All 10 steps complete
- [ ] Profile persists
- [ ] Sample budget generated
- [ ] Scenarios work
- **Notes:** _______________

### O-3 Married +2
- [ ] All 10 steps complete
- [ ] Profile persists
- [ ] Sample budget generated
- [ ] Scenarios work
- **Notes:** _______________

### E-9 Single
- [ ] All 10 steps complete
- [ ] Profile persists
- [ ] Sample budget generated
- [ ] Scenarios work
- **Notes:** _______________

**Summary:** ✅ All profiles validated / ❌ Issues found (see section)
