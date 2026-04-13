# Changelog

All notable changes to Project Atlas are documented below.

---

## [1.0.0] - 2026-04-13 🚀 Initial Public Release

### Added (Milestone E: RAG Optimization & Production Hardening)

#### Core Features
- ✅ **Retrieval-Augmented Generation (RAG) Pipeline**
  - FAISS dense passage retrieval (561 military Q&A pairs)
  - Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2)
  - FLAN-T5-base generator with confidence scoring
  - Graceful fallback chain for robustness

- ✅ **Financial Calculations**
  - Military retirement pay (High-3, FRS, BRS)
  - Healthcare cost modeling (Tricare, VA Health, ACA)
  - Tax-aware income projections (federal, state, FICA)
  - Civilian salary estimation (BLS-based)
  - Job search runway analysis

- ✅ **AI-Powered Financial Dashboard**
  - 10-step interactive wizard
  - Real-time scenario comparison
  - Natural language Q&A interface
  - Month-by-month cash flow visualization
  - Risk assessment & recommendations

#### Testing & Validation (v1.0)
- ✅ **569+ comprehensive tests**
  - 29 RAG integration tests
  - 15 performance benchmarks
  - ~525 existing unit/integration/fairness tests
- ✅ **Golden case validation** against DFAS, VA, TRICARE official calculators
- ✅ **Fairness audit** across military demographics (rank, gender, branch, family)
- ✅ **Performance benchmarks** (<50ms retrieval, <800ms generation)

#### Documentation
- ✅ Comprehensive README with quick-start guide
- ✅ ARCHITECTURE.md (system design & components)
- ✅ CONTRIBUTING.md (contribution guidelines & license)
- ✅ CODE_OF_CONDUCT.md (community standards)
- ✅ CITATION.cff (academic citation metadata)
- ✅ Deployment guide & troubleshooting
- ✅ Model limitations & fairness documentation

#### Production Readiness
- ✅ 100% local deployment (zero external APIs)
- ✅ SEC Rule 17a-4 compliance (audit trails)
- ✅ MIT license (open source)
- ✅ GitHub Actions CI/CD pipeline
- ✅ Error handling & graceful degradation
- ✅ Model pre-caching for consistent performance

---

## [Milestone D] - 2026-02-XX (Ethical Foundation)

### Added
- Governance framework & fairness methodology
- Bias mitigation strategies (data amplification 3x)
- Regulatory compliance analysis (HIPAA, FINRA, SEC 17a-4)
- Ethical reflection on local vs. cloud deployment
- What-If scenario consistency validation (67%±8% accuracy)

### Changed
- Expanded knowledge base: 556 Q&A pairs (from 521)
- Fairness-first model evaluation
- Stakeholder consent framework for military family data

---

## [Milestone C] - 2025-12-XX (Bias Audit)

### Added
- Comprehensive fairness audit across military populations
- LIME/SHAP explainability infrastructure
- Demographic parity metrics & analysis
- Data augmentation: 3x boost for underrepresented categories

### Fixed
- Housing affordability analysis: 54% accuracy improvement
- Identified bias in salary estimation (occupational gender segregation)
- Improved VA disability modeling for diverse service members

---

## [Milestone B] - 2025-10-XX (Data Science Baseline)

### Added
- 3-fold cross-validation framework
- ROUGE-L metric for Q&A accuracy (baseline: 0.0842)
- Synthetic data generation: 521 military profiles
- Unit and integration test suite

### Changed
- Refactored calculations into modular data layer
- Introduced explainability via LIME/SHAP

---

## [Milestone A] - 2025-08-XX (Foundation)

### Added
- Core financial calculator engine
- Military retirement pay calculations (High-3, FRS, BRS)
- Healthcare cost modeling (Tricare, VA, ACA)
- Tax-aware income projections
- Streamlit dashboard with cash flow visualization
- Month-by-month financial projections

---

## Known Issues

### v1.0
- ⚠️ **Memory usage:** FAISS index loading uses ~950 MB initially (not critical, models pre-cached)
- ⚠️ **Tax calculations:** Assumes single filer, no dependents; see [MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md)
- ⚠️ **Salary estimates:** Inherit occupational segregation from BLS data
- ⚠️ **Housing:** Doesn't account for discrimination/redlining effects

### Planned Fixes (v2.0)
- [ ] Support for lump-sum pension options
- [ ] Dual-military household scenarios
- [ ] Advanced tax situations (dependents, investments, business income)
- [ ] Improved salary estimation (augmented with female/minority data)
- [ ] Housing fairness analysis

---

## Deprecations

None yet (v1.0 is initial release)

---

## Security

### v1.0
- ✅ No credentials stored locally
- ✅ No external API calls (100% local processing)
- ✅ Dependencies pinned to known-good versions
- ✅ No telemetry or user tracking

### Reporting Security Issues
Found a vulnerability? Email [author email] (do not file public issue)

---

## Contributors

- **Michael Bubulka** — Project lead, primary author

### Acknowledgments
- Military financial transition domain experts
- ML fairness researchers (bias audit methodology)
- Military family members & veteran testers
- Academic advisors (AIT 716 & AIT 610)

---

## License

Project Atlas is licensed under MIT (open source).

- ✅ Commercial use: permitted
- ✅ Modification: permitted
- ✅ Distribution: permitted
- ✅ Private use: permitted

See [LICENSE](LICENSE) for full terms.

---

## Get Involved

- **Report bugs:** [GitHub Issues](../../issues)
- **Suggest features:** [GitHub Discussions](../../discussions)
- **Contribute code:** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Research collaboration:** Email [author email]

---

**Last Updated:** April 13, 2026  
**Maintained by:** Michael Bubulka  
**Repository:** [https://github.com/YOUR-USERNAME/project-atlas](https://github.com/YOUR-USERNAME/project-atlas)
