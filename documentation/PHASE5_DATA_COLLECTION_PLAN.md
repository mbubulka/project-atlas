# Phase 5: Real Data Collection Plan
## Targeted Gap Filling from Milestone D Bias Analysis (30-50 Q&A Pairs)

**Created:** April 3, 2026  
**Objective:** Collect authenticated, real Q&A pairs targeting weaknesses revealed by LIME/attention/fairness analysis in Milestone D  
**Scope:** Zero synthesis—only paraphrasing of authoritative sources  
**Target Output:** 30-50 new real pairs → 551-571 total dataset for Milestone E retraining

---

## 1. Category Breakdown & Collection Targets

### Category 1: Housing Subcategories (Target: 12 pairs)
**Why:** Weak category with LIME-revealed confusion between VA loans, conventional mortgages, tax programs

| Subcategory | Q&A Count | Primary Sources | Validation |
|-------------|-----------|-----------------|-----------|
| **Property Downsizing** | 3 | r/military, r/veterans, Military.com blogs | Upvoted 50+, author verified military |
| **State Tax Programs** | 3 | Virginia/Florida/Texas tax.gov, MilitaryOneSource articles | Official .gov or MOS transcript |
| **HELOC vs Cash-Out Refi** | 3 | Financial advisor blogs (veteran-focused), MilitaryOneSource | Advisor credentials checked |
| **VA Loan Assumptions** | 3 | DFAS/VA.gov documentation, VA loan lender FAQs | Official .mil/.gov domain |

**Collection Method:**
```
Step 1: Search DFAS.mil "VA Loan" + "housing" FAQs
        → Extract 2-3 Q&A pairs with exact answer authority
Step 2: Mine r/military top posts (all time) "housing", "mortgage", "downsizing"
        → Screenshot + save authenticity markers (upvote count, author flair)
Step 3: Contact MilitaryOneSource via licensing (authorized use of transcripts)
        → Request 3 redacted housing consultation summaries
Step 4: Search Military.com advisor blogs for property tax + downsizing scenarios
        → Verify author credentials (CPA, CFP, or military background)
```

---

### Category 2: Survivor Benefits (Target: 10 pairs)
**Why:** LIME shows confusion between SBP, SGLI, VGLI, DIC; timing decisions unclear

| Subcategory | Q&A Count | Primary Sources | Validation |
|-------------|-----------|-----------------|-----------|
| **SBP Election Timing** | 3 | DFAS SCAADM, VA Decision Brief | Official DFAS publication |
| **SGLI vs SBP Interaction** | 2 | VA.gov SBP page + MilitaryOneSource | Exact quote from VA.gov |
| **Divorced Spouse SBP** | 2 | Military law blogs, CivMilSpouseCol forum | Posted by verified lawyer/advisor |
| **DIC + SBP Overlap** | 3 | VA Dependency & Indemnity Comp doc | Official VA publication |

**Collection Method:**
```
Step 1: Download DFAS "SBP Election & Timing" official publication
        → Extract 3 Q&A pairs with exact authority
Step 2: Search VA.gov "what is SBP" + "SGLI interaction"
        → Screenshot exact Q&A pairing from page
Step 3: Mine CivMilSpouseCol (private forum, may need credentials)
        → Request 2 Q&A pairs from moderators
Step 4: Search NCLVS (National Consumer Law Center) military law resources
        → Find 2 pairs on former spouse SBP rulings
```

---

### Category 3: Multi-Benefit Planning (Target: 10 pairs)
**Why:** Attention analysis shows weak cross-category concept linking (pension+TSP+SBP+TRICARE combos)

| Subcategory | Q&A Count | Primary Sources | Validation |
|-------------|-----------|-----------------|-----------|
| **Pension + TSP Strategy** | 3 | MilitaryOneSource, r/personalfinance military threads | MOS transcript or 100+ upvotes |
| **Healthcare + Pension Timing** | 3 | TRICARE eligibility docs + DFAS | Official .mil/.gov source |
| **SBP + Survivor TRICARE** | 2 | VA benefits coordination page | Official VA.gov documentation |
| **TSP Withdrawal + Survivor Benefits** | 2 | TSP official guides + military finance blogs | Author CFP/CPA verified |

**Collection Method:**
```
Step 1: Search DFAS "Pension + TSP" coordination documents
        → Extract 3 pairs on real-world scenarios
Step 2: Mine r/personalfinance "military", "military retirement", "SES" tags (top 100 posts)
        → Capture 3 multi-benefit planning threads with author military flair
Step 3: Pull TRICARE survivor benefits page Q&A section
        → 2 pairs on survivor TRICARE eligibility
Step 4: TSP official website "survivor benefits" section
        → 2 pairs on TSP withdrawal rules for heirs
```

---

### Category 4: Edge Cases & Specialty (Target: 5 pairs)
**Why:** Rarely discussed but real: Reserve Component, medically-retired, lender documentation rules

| Subcategory | Q&A Count | Primary Sources | Validation |
|-------------|-----------|-----------------|-----------|
| **Reserve Component TRICARE** | 2 | VA.gov Reserve benefits, DFAS Reserve TRICARE brochure | Official publication |
| **Medically-Retired Specifics** | 2 | VA Disability Compendium, PEB decision guides | Official VA/DoD publication |
| **Lender Income Verification** | 1 | Financial advisor case study or VA loan lender FAQ | Lender website or advisor blog |

**Collection Method:**
```
Step 1: Search DFAS "Reserve Component" + "TRICARE" documentation
        → 2 pairs on Reserve-specific benefits
Step 2: Download VA Disability Compendium + PEB guides
        → Extract 2 pairs on medically-retired distinctions
Step 3: Review Veteran or Quicken Loans VA loan FAQ
        → Find 1 pair on lender income documentation rules
```

---

## 2. Source Authority Ranking (Priority Order)

**Tier 1 (Highest Authority—Use First)**
1. DFAS.mil official publications (SCAADM, retirement guides, FAQ)
2. VA.gov official pages + Disability Compendium
3. TSP official website
4. TRICARE documentation (health.mil)
5. PCS/PEB official DoD guides

**Tier 2 (Very High—Use After Tier 1)**
6. MilitaryOneSource transcripts (with licensing)
7. VA loan lender official FAQs (Veteran, Quicken Loans, VA)
8. DFAS payroll benefit summaries

**Tier 3 (High—Use for Validation)**
9. Reddit r/military + r/veterans (upvote 50+, author military flair)
10. Military.com advisor blogs (author credentials verified)
11. r/personalfinance with military tag (upvote 100+, explained responses)

**Tier 4 (Specialist—Use for Niche Topics)**
12. CivMilSpouseCol forum (verified military family member)
13. NCLVS military law resources (lawyer-authored)
14. Military-focused financial advisor blogs (CPA/CFP author)

---

## 3. Collection Workflow (Step-by-Step)

### Phase 5.1: Tier 1 Authority Mining (Days 1-2)
```
☐ Day 1:
  ☐ Download DFAS SBP/Survivor benefits guide
    → Extract Q&A pairs on timing, SGLI interaction, DIC overlap
  ☐ Download DFAS "VA Loan Housing" section
    → Extract Q&A on loan assumptions, primary residence rules
  ☐ Visit VA.gov SBP page + copy Q&A section
    → Capture 2-3 pairs on SBP basics
  ☐ Download TSP survivor benefits PDF
    → Extract Q&A on withdrawal rules, heir designations

☐ Day 2:
  ☐ Review TRICARE Reserve Component brochure
    → Extract Q&A on Reserve TRICARE eligibility
  ☐ Download VA Disability Compendium
    → Find Q&A on medically-retired vs normal retirement
  ☐ Mine VA benefits coordination page
    → Extract 2-3 pairs on multi-benefit overlap
```

**Output:** ~18-20 pairs from official sources

### Phase 5.2: MilitaryOneSource + Lender FAQs (Days 3-4)
```
☐ Day 3:
  ☐ Contact MilitaryOneSource licensing team
    → Request authorization to use 3-5 de-identified transcripts
    → Specify housing + SBP topics
  ☐ Search VA loan lender FAQs (Veteran, Quicken, VA)
    → Find Q&A on income documentation, debt-to-income limits
  ☐ Mine military financial advisor blogs
    → Extract 2-3 pairs on TSP + Pension strategy

☐ Day 4:
  ☐ Receive MOS transcripts + extract Q&A
  ☐ Compile lender Q&A findings
  ☐ Validate all Tier 2 pairs have clear authority
```

**Output:** ~5-8 pairs from Tier 2

### Phase 5.3: Reddit + Forum Mining (Days 5-6)
```
☐ Day 5:
  ☐ Search r/military top 100 posts: "housing", "property", "downsizing"
    → Save 3 best threads with upvote count + author flair
  ☐ Search r/veterans top 50: "SBP", "SGLI", "survivor"
    → Save 2 best threads
  ☐ Search r/personalfinance top 50 with "military" tag
    → Save 3 best "multi-benefit planning" threads

☐ Day 6:
  ☐ Extract Q&A from saved threads (upvote 50+ only)
  ☐ Verify author military flair or credentials
  ☐ Paraphrase user question + top-rated response
```

**Output:** ~8-10 pairs from Tier 3

### Phase 5.4: Validation & Deduplication (Day 7)
```
☐ Day 7:
  ☐ Compare all 31-38 new pairs against existing 521
    → Check for semantic overlap (cosine similarity >0.85)
    → Remove duplicates
  ☐ Verify each pair has clear source attribution
  ☐ Check category distribution across all 3 folds
  ☐ Export as JSON: phase5_new_pairs.json (format matching phase4)
```

**Output:** 30-50 net new, deduplicated pairs

---

## 4. Q&A Pair Format (JSON Schema)

```json
{
  "question": "What is the difference between SGLI and SBP?",
  "answer": "SGLI (Servicemembers' Group Life Insurance) is a government-provided term life insurance during active duty... SBP (Survivor Benefit Plan) is a monthly annuity for survivors... They serve different purposes and can be elected together.",
  "category": "survivor_benefits",
  "source": "VA.gov SBP page + DFAS SCAADM publication",
  "source_type": "official_publication",
  "confidence": 0.95,
  "is_synthetic": false,
  "notes": "Directly quoted from VA.gov with DFAS verification"
}
```

---

## 5. Validation Criteria (Quality Gate)

✅ **Pass:**
- Source is Tier 1, 2, or 3 with clear attribution
- Q&A pair is specific (not generic)
- Answer is unambiguous and factual
- `is_synthetic: false` only (paraphrasing is OK)
- Not >0.85 semantic overlap with existing 521 pairs

❌ **Fail:**
- Source is Tier 4+ without special justification
- Answer is vague or speculative
- Synthetic generation detected
- Semantic duplicate of existing pair
- Missing source attribution

---

## 6. Integration Plan (Post-Collection)

### Step 1: Load & Deduplicate
```python
import json
from sklearn.metrics.pairwise import cosine_similarity

# Load existing 521 pairs
with open('military_retirement_qa_merged_664_phase4.json') as f:
    existing = json.load(f)

# Load new pairs
with open('phase5_new_pairs.json') as f:
    new_pairs = json.load(f)

# Compute semantic similarity (embeddings)
# Remove pairs with similarity > 0.85 to existing set
```

### Step 2: Create Phase 5 Stratified Folds
```python
# Stratify by category (especially housing, survivor_benefits)
# Maintain balance across 3 folds:
#   Fold 1: ~190 train / 95 val
#   Fold 2: ~190 train / 95 val
#   Fold 3: ~191 train / 95 val

# Save as phase5_folds/fold_0/1/2.json
```

### Step 3: Retrain FLAN-T5 on Phase 5 Dataset
```python
# Use same training script from Milestone D
# Expected improvement: +5-10% semantic similarity on weak categories
```

---

## 7. Timeline & Milestones

| Week | Task | Deliverable |
|------|------|-------------|
| Week 1 (Day 1-2) | Tier 1 authority mining | **18-20 official pairs** |
| Week 1 (Day 3-4) | MOS + lender FAQs | **5-8 Tier 2 pairs** |
| Week 1 (Day 5-6) | Reddit + forum mining | **8-10 Tier 3 pairs** |
| Week 1 (Day 7) | Validation + dedup | **30-50 net new pairs** |
| Week 2 | Load + stratify folds | **phase5_folds ready** |
| Week 2 | Retrain models | **3 fold models trained** |
| Week 2 | Final evaluation | **Milestone E complete** |

---

## 8. Success Metrics

### Collection Phase
- ✅ Collected 30-50 new real pairs from Tier 1/2/3 sources
- ✅ Zero synthetic pairs (100% authentic)
- ✅ <5% semantic duplication with existing 521
- ✅ All pairs have clear source attribution

### Training Phase (Milestone E)
- ✅ Housing semantic similarity: 0.65+ (vs 0.35 baseline)
- ✅ Survivor benefits semantic similarity: 0.60+ (vs 0.35 baseline)
- ✅ Multi-benefit planning BLEU: +15% vs Milestone D
- ✅ Training loss monotonically decreases
- ✅ No overfitting (val loss stable after epoch 2)

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| MOS licensing delays | Fallback: use only published MOS blog articles (no transcript) |
| Reddit post deletions | Archive threads immediately upon discovery |
| Source attribution loss | Maintain metadata.json with full source URLs + access dates |
| Semantic duplication high (>5%) | Use more aggressive dedup threshold (0.80) or rebalance sources |
| Weak category improvement <5% | Increase deep-dive content focus on edge cases in collection |

---

## 10. Next Action: Start Day 1

```bash
# Create working directories
mkdir -p phase5_working
cd phase5_working

# Start Day 1 mining
# 1. Download DFAS SBP guide
# 2. Copy VA.gov SBP page Q&A
# 3. Download TSP survivor benefits PDF
# 4. Extract Q&A → phase5_new_pairs_tier1.json

# Commit progress
git add phase5_working/
git commit -m "Phase 5 collection: Tier 1 mining start (Day 1)"
```

---

**Document Status:** Ready for execution  
**Last Updated:** April 3, 2026  
**Next Review:** After Phase 5.1 (Day 2 completion)
