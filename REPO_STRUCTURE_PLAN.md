# Project Atlas: GitHub Repository Structure Plan

## 🎯 Objective
Create a **minimal but complete** public repository that includes production code, tests, trained models, documentation, and deployment resources. Exclude experimental/debug files and internal development artifacts.

---

## 📁 Public Repository Structure

```
project-atlas/
├── README.md                          # GitHub front page (from README_GITHUB_MILESTONE_E.md)
├── LICENSE                            # MIT license
├── CONTRIBUTING.md                    # Contribution guidelines
├── CITATION.cff                       # Academic citation metadata
├── CODE_OF_CONDUCT.md                 # Community guidelines (optional)
│
├── docs/
│   ├── ARCHITECTURE.md                # System design (RAG, components, fairness)
│   ├── DEPLOYMENT_GUIDE.md            # How to run locally & in production
│   ├── VALIDATION_REFERENCES.md       # Links calculations to official sources
│   ├── MODEL_LIMITATIONS.md           # Scope, assumptions, disclaimers
│   ├── FAIRNESS_AUDIT.md              # Bias detection & mitigation results
│   └── ACADEMIC_FOUNDATION.md         # Research citations and references
│
├── src/
│   ├── __init__.py
│   ├── data_models.py                 # Core financial data structures
│   ├── ai_layer/                      # RAG pipeline
│   │   ├── __init__.py
│   │   ├── faiss_retriever.py         # Dense passage retrieval
│   │   ├── cross_encoder.py           # Semantic re-ranking
│   │   ├── generator.py               # FLAN-T5 text generation
│   │   ├── audit_logger.py            # SEC Rule 17a-4 compliance
│   │   └── utils.py
│   │
│   ├── data_layer/                    # Financial calculations
│   │   ├── __init__.py
│   │   ├── retirement_calculator.py   # Military pension/retirement pay
│   │   ├── healthcare_calculator.py   # Tricare, VA Health, ACA costs
│   │   ├── tax_calculator.py          # Federal/state/FICA taxes
│   │   ├── salary_predictor.py        # Civilian salary estimation
│   │   └── scenario_analyzer.py       # What-if scenario engine
│   │
│   ├── model_layer/                   # Model loading & management
│   │   ├── __init__.py
│   │   └── model_loader.py            # Load FLAN-T5, FAISS indices
│   │
│   ├── ui_layer/                      # Streamlit components
│   │   ├── __init__.py
│   │   ├── dashboard.py               # Main dashboard layout
│   │   ├── wizard_ui.py               # 10-step financial wizard
│   │   ├── ai_chat_interface.py       # Q&A interface
│   │   └── ui_helpers.py              # UI utilities
│   │
│   ├── wizard/                        # Wizard backend logic
│   │   ├── __init__.py
│   │   └── profile_builder.py         # Extract params from input
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       ├── validators.py              # Input validation
│       └── formatters.py              # Output formatting
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── fixtures/                      # Test data & sample profiles
│   ├── unit/                          # Unit tests by module
│   │   ├── test_retirement_pay_model.py
│   │   ├── test_healthcare_model.py
│   │   ├── test_tax_calculation.py
│   │   ├── test_salary_predictor.py
│   │   └── test_ai_*.py
│   │
│   ├── integration/                   # Integration tests
│   │   ├── test_integration_ai_ui.py  # End-to-end flows
│   │   └── test_rag_live_scenario.py  # RAG pipeline E2E
│   │
│   ├── financial_accuracy/            # Domain-specific validation
│   │   ├── test_golden_cases.py       # Known-good profiles
│   │   └── test_cross_tool_validation.py
│   │
│   ├── consistency/                   # Fairness & consistency
│   │   ├── test_what_if_consistency.py
│   │   └── test_fairness_metrics.py
│   │
│   ├── edge_cases/                    # Boundary conditions
│   │   └── test_edge_cases.py
│   │
│   └── README.md                      # Test suite documentation
│
├── models/                            # Trained model weights
│   ├── README.md                      # Model download instructions
│   ├── flan_t5_base/                  # FLAN-T5 checkpoint
│   │   ├── config.json
│   │   ├── pytorch_model.bin          # ⚠️ Large (~1GB); optional download
│   │   └── tokenizer.json
│   │
│   └── faiss_indices/                 # Vector database indices
│       ├── README.md
│       ├── military_qa_kb.index       # FAISS Flat (561 Q&A pairs)
│       └── metadata.json
│
├── data/                              # Sample data & knowledge base
│   ├── README.md                      # Data sources & attribution
│   ├── sample_budgets/                # 6 validated test budgets
│   │   ├── high_earner_scenario.json
│   │   ├── junior_enlisting.json
│   │   └── ...
│   │
│   ├── kb/                            # Knowledge base passages (for RAG)
│   │   ├── military_benefits.txt      # Tricare, SBP, VA benefits
│   │   ├── retirement_rules.txt       # High-3, FRS, BRS rules
│   │   └── tax_treatment.txt          # Military-specific tax treatment
│   │
│   └── fixtures/                      # Test data
│       ├── test_profiles.json
│       └── test_scenarios.json
│
├── .github/
│   ├── workflows/
│   │   ├── tests.yml                  # CI/CD: Run pytest on push
│   │   └── deploy.yml                 # (Optional) Deploy to test environment
│   │
│   └── ISSUE_TEMPLATE/                # GitHub issue templates
│       ├── bug_report.md
│       └── feature_request.md
│
├── pyproject.toml                     # Python project metadata
├── requirements.txt                   # Dependencies (pinned versions)
├── MANIFEST.in                        # Include data files in distribution
├── .gitignore                         # Exclude venv, cache, etc.
└── app.py                             # Streamlit entry point

```

---

## 📦 What's Included vs. Excluded

### ✅ INCLUDE (Production Code)

| Item | Reason | Source |
|------|--------|--------|
| `src/` (all modules) | Core production code | Direct copy |
| `tests/` (all) | Validation & reproducibility | Direct copy |
| `models/` | Trained FLAN-T5 + FAISS indices | Direct copy (GIT LFS) |
| `data/sample_budgets/` | Example scenarios | Direct copy |
| `data/kb/` | Knowledge base for RAG | Direct copy |
| `docs/ARCHITECTURE.md` | Technical design | Already exists |
| `docs/DEPLOYMENT_GUIDE.md` | Installation & usage | Create from existing files |
| `app.py` | Streamlit entry point | Direct copy |
| `requirements.txt` | Dependencies | Direct copy |
| `pyproject.toml` | Project metadata | Update if needed |
| `LICENSE` | MIT | Create |
| `CONTRIBUTING.md` | Contribution policy | Already created ✅ |
| `.github/workflows/` | CI/CD pipeline | Direct copy |

### ❌ EXCLUDE (Development Artifacts)

| Item | Reason |
|------|--------|
| All `.py` debug/diagnostic scripts at root | Experimental & temporary |
| `_archive/` folder | Historical/superseded work |
| `*.log`, `*.txt` output files | Runtime artifacts |
| `.pytest_cache/`, `__pycache__/` | Build artifacts |
| `.venv/` | Virtual environment |
| `.idea/` | IDE settings |
| `*.ipynb` (unless research notebooks) | Development scratch |
| Internal markdown files (Milestone reports, checklists) | Internal tracking |

### 🤔 CONDITIONAL (Decision Needed)

| Item | Include? | Reason |
|------|----------|--------|
| Research notebooks | YES | If demonstrating methodology |
| Benchmark results | YES | If showing reproducibility |
| Raw model weights | NO (LFS link instead) | Too large (~1GB FLAN-T5) |
| Full training data | NO (link to source) | Privacy/size considerations |
| Development test scripts | NO | Use `tests/` folder instead |

---

## 📋 Migration Checklist

### Phase 1: Copy Core Production Code
- [ ] Copy `src/` → `repo/src/` (all Python modules)
- [ ] Copy `tests/` → `repo/tests/` (all test files)
- [ ] Copy `app.py` → `repo/app.py`
- [ ] Copy `data/sample_budgets/` → `repo/data/sample_budgets/`
- [ ] Copy `data/kb/` → `repo/data/kb/`

### Phase 2: Set Up Models (with Git LFS)
- [ ] Configure Git LFS for large files:
  ```bash
  git lfs track "models/**/*.bin"
  git lfs track "models/**/*.index"
  ```
- [ ] Copy `models/flan_t5_base/` → `repo/models/flan_t5_base/`
- [ ] Copy `models/faiss_indices/` → `repo/models/faiss_indices/`
- [ ] Create `models/README.md` with download instructions

### Phase 3: Documentation
- [ ] Copy `docs/ARCHITECTURE.md` → `repo/docs/ARCHITECTURE.md`
- [ ] Create `docs/DEPLOYMENT_GUIDE.md` from existing deployment notes
- [ ] Copy/adapt `docs/VALIDATION_REFERENCES.md`
- [ ] Copy `docs/MODEL_LIMITATIONS.md`
- [ ] Copy `CONTRIBUTING.md` → `repo/CONTRIBUTING.md` ✅

### Phase 4: Build Configuration
- [ ] Copy `requirements.txt` → `repo/`
- [ ] Copy `pyproject.toml` → `repo/` (update if needed)
- [ ] Copy `.gitignore` → `repo/`
- [ ] Create `MANIFEST.in` (include data files)
- [ ] Copy `.github/workflows/tests.yml` → `repo/.github/workflows/`

### Phase 5: Root-Level Files
- [ ] Create `README.md` (from README_GITHUB_MILESTONE_E.md)
- [ ] Create `LICENSE` (MIT text)
- [ ] Create `CITATION.cff` (academic citation)
- [ ] Create `.gitignore` (Python + IDE patterns)
- [ ] Create `CODE_OF_CONDUCT.md` (optional but recommended)

### Phase 6: GitHub Organization
- [ ] Create repo on GitHub (`project-atlas`)
- [ ] Configure branch protection (main branch)
- [ ] Set up issue templates in `.github/ISSUE_TEMPLATE/`
- [ ] Configure repository labels & milestones
- [ ] Add status badges to README (tests, coverage, license)

---

## 🚀 Repository Size Estimate

| Component | Size | Format | Git LFS? |
|-----------|------|--------|----------|
| `src/` | ~200 KB | Python | No |
| `tests/` | ~300 KB | Python | No |
| `data/` (sample data) | ~50 KB | JSON/TXT | No |
| `models/flan_t5_base/` | ~950 MB | PyTorch | **YES** |
| `models/faiss_indices/` | ~10 MB | Binary | Yes |
| `docs/` | ~500 KB | Markdown | No |
| **Total** | **~960 MB** | — | ~960 MB via LFS |

**GitHub Considerations:**
- Without LFS: ~70 MB (code + docs only, models not included)
- With LFS: ~960 MB (includes trained models)
- Recommendation: **Use Git LFS for model files**, users can download separately or via `pip install project-atlas` with optional model support

---

## 🔗 Version Control Strategy

### Branches
- `main` - Stable release (Milestone E)
- `develop` - Integration branch for next milestone
- `feature/*` - Feature branches

### Tags
- `v1.0.0` - Initial release (Milestone E)
- Semantic versioning thereafter

### .gitignore Template
```
# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Models (if not using LFS)
# models/flan_t5_base/*.bin

# Logs
*.log
*.out

# OS
.DS_Store
Thumbs.db
```

---

## 📊 Success Criteria

- ✅ Repository is **self-contained** (clone & run locally)
- ✅ All **tests pass** (`pytest tests/ -v`)
- ✅ **No API keys or credentials** in repo
- ✅ **Documentation is complete** (setup, architecture, deployment)
- ✅ **License is clear** (MIT)
- ✅ **Models load correctly** (weights accessible)
- ✅ **Research contributions tracked** (CITATION.cff, academic foundation)
- ✅ **Code is production-quality** (no debug scripts, clean structure)

---

## 📝 Notes

1. **Model Sizes**: FLAN-T5 weights (~950 MB) will require Git LFS. Consider providing a lightweight version without models (users download separately).

2. **Knowledge Base**: The military Q&A KB (561 passages) is included in `data/kb/` for researchers to inspect; FAISS indices are pre-built for easy loading.

3. **Reproducibility**: Full test suite included; users can reproduce all benchmarks without external dependencies.

4. **CI/CD**: GitHub Actions workflow (`tests.yml`) runs on every push to ensure tests pass.

