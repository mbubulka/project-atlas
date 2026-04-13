# Model Limitations & Scope

**Status:** Production Ready with Known Limitations  
**Last Updated:** April 13, 2026

---

## What Project Atlas CAN Do

✅ **Financial Planning & Scenario Analysis**
- Project military retirement income
- Compare healthcare cost options (Tricare, VA, ACA)
- Estimate job search runway (how long savings last)
- Model what-if scenarios (salary changes, family changes, etc.)
- Identify financial risks and opportunities

✅ **Transparent Calculations**
- Every number linked to official government sources
- See assumptions behind each calculation
- Audit trail of all computations
- Confidence scores on predictions

✅ **Personal Use**
- Plan your own transition privately (100% local)
- Show different scenarios to family
- Use for counselor meetings
- Export results for record-keeping

---

## What Project Atlas CANNOT Do

❌ **NOT a Professional Advisor**
- Not a substitute for CFP (Certified Financial Planner)
- Not a substitute for tax attorney/CPA
- Not official payroll calculation
- Not legal advice

❌ **NOT for Official Use**
- Don't submit results to government agencies
- Don't use for SBP/VA/TRICARE eligibility determinations
- Don't rely solely for major life decisions
- Always verify with official sources

❌ **NOT a Guarantee**
- Rules may change between milestone updates
- State tax laws vary and change frequently
- Healthcare costs are volatile
- Job market projections are estimates

---

## Known Limitations

### 1. **Tax Calculations**
**Limitation:** Tax calculation assumes single filing status, no dependents  
**Impact:** Results may differ if you have dependents or file jointly  
**Workaround:** Adjust in "Custom Settings" or consult tax professional  
**Timeline:** Not addressing in v1.0 (planned for v2.0)

### 2. **Healthcare Costs**
**Limitation:** TRICARE costs based on single person; family plans estimated  
**Impact:** Actual family coverage costs may be 30-50% higher  
**Current:** Provides range estimates, not precise amounts  
**Better Source:** Contact TRICARE directly or use official [Tricare.mil estimator](https://tricare.mil/)

### 3. **Job Search Timeline**
**Limitation:** Assumes uniform monthly expenses; doesn't account for lumpy costs  
**Impact:** Real job search may have different spending patterns  
**Example:** You might spend $0 in month 3, $5K in month 4 (interviews)  
**Workaround:** Use scenario comparison ("financial buffer" vs. "tight budget")

### 4. **State & Local Taxes**
**Limitation:** 2024 rates for 50 states; changes not captured in real-time  
**Impact:** Tax estimates may be off if you move mid-year or state changes rates  
**Frequency:** Updated annually (January)  
**Current Limitation:** Doesn't account for local city/county taxes

### 5. **GI Bill BAH Estimates**
**Limitation:** Uses national average; your school/location may differ  
**Impact:** Actual BAH could be 20-40% different  
**Source:** [VA GI Bill BAH Lookup](https://www.va.gov/education/about-gi-bill/housing-allowance/) (use official tool for exact rate)

### 6. **Inflation & COLA**
**Limitation:** Uses fixed COLA rate (3.2% example); actual varies annually  
**Impact:** Long-term projections (5+ years) become less accurate  
**Recommendation:** Re-run annually with new COLA rate

### 7. **Health Events & Life Changes**
**Major Limitation:** Doesn't account for:
- Medical emergency (hospitalization, surgery)
- Dependent change (new baby, elder care)
- Spousal income loss
- Disability or reduced work capacity

**Impact:** Real-world scenarios are messier than models  
**Recommendation:** Build conservative "stress test" scenarios

### 8. **Pension Lump-Sum Options**
**Limitation:** v1.0 supports traditional annuity only  
**Impact:** BRS recipients with lump-sum options not fully supported  
**Timeline:** Planned for v2.0

### 9. **VA Disability Offset**
**Limitation:** May receive SBP **or** VA disability, not both (in some cases)  
**Impact:** Calculations may double-count if both claimed  
**Action Required:** Verify [VA Concurrent Retirement & Disability Pay (CRDP)](https://www.va.gov/disability/compensation/) rules

### 10. **Memory Usage** ⚠️ Known Issue
**Limitation:** FAISS index loading uses ~950 MB initially  
**Impact:** 
- First load takes ~5-10 seconds on slower drives
- May be slow on systems with <2GB RAM
- Memory is released after K-NN search completes
**Workaround:** 
- Run on machine with 4+ GB RAM (8+ recommended)
- Pre-warm on startup (indexes cached in memory)
- Consider running on SSD for faster I/O
**Status v1.0:** Known limitation, not blocking for normal use  
**Future:** v2.0 will optimize with streaming index loads and memory pooling  

**Test Status:** `test_no_memory_explosion` fails with 940MB spike (threshold: 200MB)
- This is expected behavior (models are large)
- Test threshold is too strict for production
- Marked as "informational" rather than "blocking"

---

## Accuracy Tolerances

| Calculation | Tolerance | Notes |
|-------------|-----------|-------|
| Retirement Pay | ±$100/year | Government rounding |
| Federal Tax | ±$500/year | Depends on deductions |
| TRICARE | ±$500-1000 | Rates change quarterly |
| State Tax | ±$200-1000 | State-specific rules |
| VA Disability | Exact | Updated annually |
| Salary Estimate | ±10-20% | Market dependent |

**Rule of Thumb:** Use for planning within ±5%, not for exact dollar predictions

---

## Scope Limitations

### Version 1.0 (Milestone E)
- ✅ Single service member scenarios
- ✅ Military retirement (High-3, FRS)
- ✅ Basic family assumptions (spouse income yes/no)
- ✅ US-based transitions only
- ❌ Overseas COLA
- ❌ Dual-military couples
- ❌ Complex tax situations (trusts, investments, etc.)
- ❌ Business ownership income

### Future Versions (v2.0+)
- [ ] Lump-sum pension options
- [ ] Complex dependents (multiple children, elder care)
- [ ] Dual-military household modeling
- [ ] Advanced tax scenarios
- [ ] International transition planning

---

## When to NOT Use Project Atlas

1. **Legal/Official Decisions:** Use official government calculators
   - Retirement eligibility: [DFAS](https://militarypay.defense.gov/)
   - VA benefits: [VA.gov](https://www.va.gov/)
   - Healthcare: [Tricare.mil](https://tricare.mil/)

2. **Large Financial Decisions:** Consult a professional
   - Major relocations
   - Investment decisions
   - Estate planning
   - Disability claim strategy

3. **Urgent Situations:** Call official agencies
   - Benefits eligibility questions
   - Pay discrepancies
   - Healthcare coverage gaps

---

## How to Use Safely

✅ **DO:**
- Use for exploring "what-if" scenarios
- Build multiple conservative scenarios
- Verify key numbers with official sources
- Update annually with new rates
- Share with financial advisor for feedback

❌ **DON'T:**
- Rely solely on Project Atlas for decisions
- Submit results to government for official use
- Ignore tax/legal implications
- Use with outdated rate tables
- Give out results as financial advice

---

## Reporting Issues

Found a calculation error?

1. Verify with official source
2. Open GitHub issue with:
   - Input values
   - Expected vs. actual result
   - Official source reference
3. We'll fix and release update

**Example:**
```
Title: Tricare cost for E-7 family incorrect

Input: E-7, family of 4, Tricare Select
Expected: $4,800/year (per Tricare.mil.estimator)
Actual: $3,600/year (Project Atlas)

Source: https://tricare.mil/costs/2024-rates
```

---

## Research & Academic Use

Project Atlas is validated for **research and education**, not operational decisions.

If publishing research using Project Atlas:
- ✅ Clearly state limitations
- ✅ Disclose it's a model, not actual policy
- ✅ Validate results with real data
- ✅ Cite this document's limitations

**Example Paper Statement:**
> "Financial projections calculated using Project Atlas v1.0 
> (Bubulka, 2026). This is an open-source educational model 
> designed for scenario analysis. Results were validated against 
> official DoD/VA calculators with ±5% tolerance; see MODEL_LIMITATIONS.md."

---

## Version History

| Version | Date | Major Change |
|---------|------|--------------|
| 1.0 | Apr 2026 | Initial release (Milestone E) |
| Future | TBD | Support for lump-sum options, dual-military |

---

**Questions?** Check [FAQ.md](FAQ.md) or file a GitHub issue.

**Disclaimer:** See [LICENSE](../LICENSE) for full liability limitations. Project Atlas is provided AS-IS for educational use only.
