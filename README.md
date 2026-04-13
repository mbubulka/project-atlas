# Project Atlas: Military Financial Transition Simulator with AI-Powered Analysis

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-569%2B%20comprehensive-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25%2B-green.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/doi-10.0000%2Fzenodo.0000000-blue.svg)](https://doi.org/)

---

## 🎖️ Mission

Project Atlas enables **military service members to make informed financial decisions** during **Career Transition Assistance Program (CTAP)** planning. Using local-first computation and AI-powered analysis, it answers the critical question:

> **"Can I afford this transition, and what are my real options?"**

✅ **All data stays on your computer. Zero external calls. 100% privacy.**

---

## 📋 What It Does

Project Atlas is an interactive financial simulator that helps you explore what-if scenarios for military-to-civilian transition:

### 🎯 Core Capabilities

| Feature | What It Solves |
|---------|---|
| **Military Retirement Calculator** | How much will my retirement pay be? (High-3, FRS, BRS rules) |
| **Healthcare Cost Modeling** | Tricare vs. VA vs. civilian insurance—which is cheapest for my family? |
| **Tax-Aware Projections** | What are my actual federal/state/FICA taxes in civilian life? |
| **Salary Estimator** | What civilian job market salary should I target? |
| **Cash Flow Analysis** | How long will my savings last during job search? |
| **What-If Scenarios** | What if my job search takes 9 months? What if I use GI Bill BAH? |
| **AI Q&A Advisor** | Ask questions in plain English—get personalized financial advice |

### 🚀 Technology Stack

| Layer | Component | Purpose |
|-------|-----------|---------|  
| **UI** | Streamlit | Interactive dashboard + 10-step financial wizard |
| **AI** | FLAN-T5 + FAISS RAG | Natural language Q&A with grounded knowledge |
| **Calculations** | Domain-specific models | Military retirement, healthcare, tax, salary |
| **Validation** | 569+ comprehensive tests | Accuracy vs. official calculators |
| **Fairness** | Demographic bias audit | Ensures equitable outcomes across populations |

---

## 🏗️ Architecture Overview

```
User Question: "What if my job search takes 9 months?"
        ↓
┌─────────────────────────────────────────────────┐
│  Natural Language Understanding                  │
│  (FLAN-T5 intent detection)                      │
└────────────┬────────────────────────────────────┘
             ↓
    ┌────────────────────┐
    │ Knowledge Retrieval │
    │ (FAISS vector DB)  │
    └────────┬───────────┘
             ↓
┌─────────────────────────────────────────────────┐
│ Financial Scenario Engine                       │
│ - Extract job search length from intent         │
│ - Run what-if analysis (savings runway, taxes)  │
│ - Generate recommendations                      │
└────────────┬────────────────────────────────────┘
             ↓
    "Your savings cover 11 months at current
     burn rate. Consider: (1) reduce burn by
     cutting $X/month, (2) accelerate offer
     timeline, (3) leverage GI Bill BAH while
     searching. See analysis below..."
```

**Read more:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** ([Download here](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git**

### Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/project-atlas.git
cd project-atlas

# 2. Create virtual environment
python -m venv .venv

# Activate it:
### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Running Tests

```bash
# Run all tests (569 comprehensive tests)
pytest tests/ -v

# Run specific category:
pytest tests/financial_accuracy/ -v    # Validation tests
pytest tests/consistency/ -v             # Fairness tests
pytest tests/integration/ -v             # End-to-end tests

# Generate coverage report
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Validation & Accuracy

Project Atlas is built with **military decision-support standards** in mind. Every calculation is validated against authoritative government sources.

### Validation Framework

| Document | What It Covers |
|----------|---|
| [docs/VALIDATION_REFERENCES.md](docs/VALIDATION_REFERENCES.md) | All calculations mapped to official DoD, VA, and IRS sources |
| [docs/MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md) | Clear scope, assumptions, and disclaimers |
| [docs/FAIRNESS_AUDIT.md](docs/FAIRNESS_AUDIT.md) | Bias detection & mitigation for military populations |
| [tests/financial_accuracy/test_golden_cases.py](tests/financial_accuracy/test_golden_cases.py) | Known-good profiles vs. official calculators |

### Example Validation

✅ **Retirement Pay**: Validated against [DoD High-3 Calculator](https://militarypay.defense.gov/)  
✅ **Tricare Costs**: Cross-checked with official [Tricare.mil](https://www.tricare.mil/) rate tables  
✅ **VA Disability Offset**: Verified against [VA Compensation Calculator](https://www.va.gov/)  
✅ **Tax Calculations**: IRS rules for military-specific deductions (military BAH, SBP, etc.)  

---

## 📈 Milestone Evolution (v1.0)

Project Atlas evolved through 5 research milestones:

### **Milestone A: Foundation**
- Core financial calculator engine
- Tricare, VA Health, and ACA healthcare modeling
- Tax-aware retirement calculations
- Streamlit dashboard with cash flow visualization

### **Milestone B: Data Science Baseline**
- 3-fold cross-validation framework
- ROUGE-L baseline metrics for Q&A accuracy
- LIME/SHAP explainability infrastructure
- Synthetic scenario generation (521 profiles)

### **Milestone C: Bias Audit & Amplification**
- Demographic fairness audit across income, housing, survivor benefits
- Amplified weak categories (housing, benefits) by 3x
- Achieved 54% improvement in housing cost predictions
- Expanded to 556 Q&A pairs + 561 military knowledge base

### **Milestone D: Ethical Reflection & Governance**
- Documented governance framework and bias mitigation
- Analyzed regulatory compliance (HIPAA, FINRA)
- Achieved 67%±8% consistency on What-If scenarios
- Published ethical reflection on deployment trade-offs

### **Milestone E: RAG Optimization & Production Hardening ⭐**
- **Implemented Retrieval-Augmented Generation (RAG)** with FAISS vector DB
- Enhanced answer quality with confidence-scored routing
- Optimized hyperparameters (k=1 retrieval, top-3 re-ranking)
- **569+ comprehensive tests** (29 RAG integration + 15 performance + 525 existing)
- Production-ready with deployment guide and explainability audit trail

---

## 🔍 Key Features

### 1. **The 10-Step Financial Wizard**
Walk through your military profile, benefits, healthcare, and lifestyle to build a comprehensive financial model:
- **Step 1:** Military Profile (rank, YOS, branch, income)
- **Steps 2-4:** Healthcare & Benefits (Tricare, SBP, GI Bill, VA disability)
- **Step 5:** Pension & VA Benefits
- **Step 6:** Civilian Career Salary Estimator
- **Step 7:** Budgeting & Expense Categories
- **Step 8:** CSV Upload for Quick Expense Classification (6 sample budgets)
- **Step 9:** Prepaid Insurance Management
- **Step 10:** Financial Summary + AI Advisor

### 2. **AI-Powered Q&A**
Ask questions about your financial transition in plain English. The system:
- Retrieves relevant military financial knowledge (FAISS)
- Re-ranks by semantic relevance (cross-encoder)
- Generates grounded answers (FLAN-T5)
- Logs everything for audit trail

**Example questions:**
- "What if my job search takes 6 months?"
- "How much will Tricare cost for my family?"
- "Should I take the SBP?"
- "When should I claim VA disability?"

### 3. **Scenario Comparison**
Build multiple scenarios and compare side-by-side:
- Conservative (assume 9-month job search, higher healthcare costs)
- Optimistic (6-month job search, employer health insurance)
- Risk-aware (medical event, dependent change, etc.)

### 4. **Explainability & Audit Trail**
Every answer is traceable:
- Which knowledge base passages were used?
- What confidence score? (0-1)
- What assumptions were made?
- What's the confidence interval on projections?

---

## 📚 Documentation

| Document | For Whom |
|----------|----------|
| [README.md](README.md) | **Everyone** — Overview & quick start |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **Developers** — System design, RAG pipeline, fairness strategy |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | **DevOps/Deployers** — Local setup, cloud deployment, config |
| [docs/VALIDATION_REFERENCES.md](docs/VALIDATION_REFERENCES.md) | **Verifiers** — Where calculations come from |
| [docs/MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md) | **Power Users** — What it can/can't do |
| [docs/FAIRNESS_AUDIT.md](docs/FAIRNESS_AUDIT.md) | **Researchers** — Bias detection & mitigation results |
| [CONTRIBUTING.md](CONTRIBUTING.md) | **Contributors** — How to submit PRs under MIT |
| [tests/README.md](tests/README.md) | **QA Engineers** — Test suite organization |

---

## 🔒 Privacy & Security

### Data Handling
- ✅ **All computations run locally** — No data sent to external services
- ✅ **No API calls** — Works offline after initial load
- ✅ **No cloud dependencies** — All models bundled locally
- ✅ **No user tracking** — No analytics, cookies, or telemetry
- ✅ **No credential storage** — No passwords saved

### Model Security
- ✅ FLAN-T5 from Google (open-source, audited)
- ✅ FAISS from Meta (battle-tested in production)
- ✅ All dependencies pinned to known-good versions
- ✅ No proprietary black-box components

### Audit Trail
- SEC Rule 17a-4 compliant logging (timestamp, user_id, question, passages, answer)
- Hash chains prevent tampering
- Optional export for compliance review

---

## 🧪 Test Coverage & Quality

Project Atlas includes **569+ comprehensive tests** validating:

### Financial Accuracy (125 tests)
- Retirement pay calculations vs. official DoD rules
- Healthcare cost projections vs. Tricare rate cards
- Tax calculations vs. IRS guidance
- Salary estimations vs. Bureau of Labor Statistics

### Fairness & Consistency (89 tests)
- Demographic fairness across income, race, gender, marital status
- What-If consistency (same scenario → same result)
- Bias detection using LIME/SHAP

### Integration & Performance (39 tests)
- End-to-end workflow (UI → calculator → output)
- RAG pipeline (retrieval → re-ranking → generation)
- Response time benchmarks (<50ms retrieval, <800ms generation)

### Edge Cases & Robustness (316 tests)
- Invalid inputs (negative income, impossible scenarios)
- Boundary conditions (age 0, 60+ years planning)
- Missing data (incomplete profiles)
- Error recovery (graceful fallbacks)

**Run tests:**
```bash
pytest tests/ -v --cov=src --cov-report=html
```

---

## 🎓 Research Foundation

Project Atlas is grounded in published research on:

- **Fairness in Machine Learning** — Bias detection, demographic parity, equalized odds
- **Retrieval-Augmented Generation** — FAISS dense retrieval, cross-encoder re-ranking
- **Explainable AI** — LIME/SHAP feature importance, confidence scoring
- **Military Finance** — Retirement rules, healthcare policy, tax treatment
- **User-Centered Design** — Accessible financial planning, scenario-based reasoning

**Full citations:** See [docs/ACADEMIC_FOUNDATION.md](docs/ACADEMIC_FOUNDATION.md)

---

## 💡 Use Cases

### **For Military Service Members**
Use Project Atlas to:
- Understand your true retirement income
- Compare healthcare options (Tricare vs. VA vs. civilian)
- Estimate civilian job search runway
- Build optimistic/conservative/risk scenarios
- Ask personalized Q&A about your transition

### **For Military Family Members**
Use Project Atlas to:
- Understand household finances after transition
- Plan for healthcare continuity
- Model different job market scenarios
- Ask questions without embarrassment (private, no judgment)

### **For Financial Counselors & Transition Specialists**
Use Project Atlas to:
- Show clients real scenarios (not worst-case fear-mongering)
- Enable clients to explore their own options
- Reduce counselor time on repetitive questions
- Document decision-making for compliance

### **For Military Family Researchers**
Use Project Atlas to:
- Validate financial models against real data
- Study barriers to successful transition
- Identify underrepresented populations
- Generate synthetic scenarios for analysis

### **For Policymakers**
Use Project Atlas to:
- Understand real financial constraints on service members
- Model impact of policy changes (SBP % increase, Tricare costs, etc.)
- Identify populations most vulnerable to financial stress
- Inform evidence-based transition policy

---

## 🚧 Known Limitations

Project Atlas is **not** a substitute for:
- Professional financial advice (consult a CFP)
- Legal advice (consult a JAG officer or tax attorney)
- Healthcare enrollment (use official enrollment systems)
- Official payroll calculations (verify via your service's system)

**Full limitations:** See [docs/MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md)

---

## 🤝 Contributing

Contributions are welcome — you can use, modify, and distribute them freely under the MIT license.

Contributions *should*:
- ✅ Fix bugs or improve performance
- ✅ Enhance fairness metrics or bias detection
- ✅ Add test coverage (especially edge cases)
- ✅ Improve documentation
- ✅ Add military benefit categories (if properly sourced)

Contributions *cannot*:
- ❌ Commercialize the software
- ❌ Remove license or attribution
- ❌ Introduce proprietary dependencies
- ❌ Claim ownership

**How to contribute:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📜 License

This software is licensed under the **MIT License** (open source).

### In Plain English:
- ✅ **Use freely:** Personal, academic, commercial — any purpose
- ✅ **Modify:** Change the code however you want
- ✅ **Distribute:** Share copies or derivatives
- ✅ **Commercial:** Sell it, charge for services, whatever
- ⚠️ **Attribution:** Give credit to the original author
- ⚠️ **No warranty:** Use at your own risk

**Full license text:** [LICENSE](LICENSE)

**Commercial licensing inquiries:** Contact the author

---

## 📖 Citation

If you use Project Atlas in research or publications, please cite:

**BibTeX:**
```bibtex
@software{bubulka2026_projectatlas,
  author = {Bubulka, Michael},
  title = {Project Atlas: Military Financial Transition Simulator with AI-Powered Analysis},
  year = {2026},
  url = {https://github.com/YOUR-USERNAME/project-atlas},
  version = {1.0.0},
  license = {MIT}
}
```

**APA:**
```
Bubulka, M. (2026). Project Atlas: Military financial transition simulator with AI-powered 
analysis (Version 1.0.0) [Computer software]. https://github.com/YOUR-USERNAME/project-atlas
```

**More formats:** [CITATION.cff](CITATION.cff)

---

## 🙋 Support & Questions

- **Questions about usage?** → [GitHub Discussions](../../discussions)
- **Found a bug?** → [GitHub Issues](../../issues)
- **Contributing?** → See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Privacy concerns?** → This is local-only; no data leaves your computer
- **Commercial licensing?** → Email the author

---

## 🎖️ Community

Project Atlas is built in the spirit of **open research for public good**. Our community includes:

- 🪖 Military service members and transitioning veterans
- 👨‍👩‍👧 Military family members and caregivers
- 🎓 Academic researchers in fairness, decision support, and military policy
- 💼 Financial counselors and transition specialists
- 🏛️ Policymakers and government researchers

**Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and feature updates.

---

## 🙏 Acknowledgments

Project Atlas was developed with support and feedback from:

- Military financial transition domain experts
- Active-duty and veteran service members
- Military family members and caregivers
- Academic researchers in fairness and explainability
- User testing participants and beta testers

Thank you for helping make military financial transitions less stressful and more empowered. 🇺🇸

---

**Last updated:** April 13, 2026  
**Version:** 1.0.0  
**Status:** ✅ Production Ready (Milestone E)
