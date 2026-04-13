# Contributing to Project Atlas

Thank you for your interest in contributing to Project Atlas! This document outlines how to contribute to this academic research project while respecting intellectual property boundaries and maintaining code quality standards.

## 🎯 Contribution Scope

**Project Atlas welcomes contributions in the following areas:**

### ✅ Welcome Contributions
- Bug fixes and performance improvements
- Enhanced fairness metrics and bias detection methods
- Additional test coverage, especially for edge cases
- Documentation improvements and clarifications
- Enhancements to the FAISS retrieval or cross-encoder re-ranking components
- New deployment configurations or optimization strategies
- Support for additional military benefit categories (if properly sourced)
- Research validations and replications of published results

### ⚠️ Contribution Standards
- **All contributions must comply with the MIT license**
- Contributions can be used for any purpose (commercial, academic, personal)
- All contributions become part of the project under MIT terms

## 📋 Before You Contribute

1. **Understand the MIT License**: Read [LICENSE](../LICENSE) carefully. Your contributions will be licensed under MIT.

2. **Review the Academic Foundation**: Familiarize yourself with the research contributions outlined in [docs/ACADEMIC_FOUNDATION.md](../docs/ACADEMIC_FOUNDATION.md).

3. **Check Existing Discussions**: Browse [Issues](../../issues) to avoid duplicate contributions.

4. **Read the Architecture**: Understand system design in [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## 🔄 Contribution Workflow

### 1. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork locally
git clone https://github.com/YOUR-USERNAME/project-atlas.git
cd project-atlas

# Create a descriptive feature branch
git checkout -b feature/research-question-or-fix
# Examples:
#   feature/fairness-metric-improvement
#   fix/rag-latency-optimization
#   docs/deployment-guide-clarification
```

### 2. Make Changes

- **Code Style**: Follow PEP 8 conventions
- **Comments**: Include docstrings explaining research motivation
- **Tests**: Write tests for new functionality
- **Documentation**: Update relevant docs if changing behavior

Example code structure:
```python
def improved_fairness_metric(predictions, labels, groups):
    """
    Compute improved fairness metric for group-aware evaluation.
    
    Research Motivation:
    - Addresses gap identified in [citation]
    - Extends approach from [paper] to military financial domain
    
    Args:
        predictions: Model predictions
        labels: Ground truth labels
        groups: Group membership for subgroup analysis
        
    Returns:
        dict: Fair metrics per group and aggregate
        
    References:
        Smith et al. (2024). Procedural fairness in ML.
    """
    pass
```

### 3. Commit with Clear Messages

```bash
# Good commit messages reference research or specific improvements
git commit -m "Improve What-If consistency metric for multi-factor scenarios

- Extends consistency testing to account for logical dependencies
- Improves consistency from 54% → 62% on integration scenarios
- Cites methodology from Wang et al. (2026)
- Includes unit tests and fairness validation"
```

### 4. Test Thoroughly

```bash
# Run full test suite
pytest tests/ -v --cov=src/ --cov-report=term-missing

# Run specific test category
pytest tests/test_fairness_metrics.py -v

# Check code quality
flake8 src/ --max-line-length=100
```

### 5. Submit Pull Request

When submitting a PR:

#### a. PR Title & Description
```markdown
**Title**: [Concise description of contribution]

**Type**: (Bug fix | Enhancement | Documentation | Research validation)

**Summary**:
- What problem does this address?
- How does it improve Project Atlas?
- References to relevant research (if applicable)

**Testing**:
- What tests were added/modified?
- What's the coverage impact?
- Fairness/bias implications?

**Compliance**:
- [ ] Changes comply with MIT license terms
- [ ] All third-party code properly attributed
- [ ] No license conflicts
```

#### b. Checklist
When submitting, ensure:
- [ ] Branch is up-to-date with `main`
- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Code follows PEP 8 style
- [ ] Docstrings include research motivation
- [ ] No large binary files (>10MB)
- [ ] No debug/test scripts left in code
- [ ] README/docs updated if needed
- [ ] PR description explains "why" (research benefit/fix)

#### c. License Acknowledgment
```markdown
**License & Attribution**:
I acknowledge that:
- This contribution is provided under MIT terms
- My contribution may be used for any purpose (commercial, academic, personal)
- The author may incorporate this contribution into Project Atlas
- This contribution is provided at no cost and without compensation
```

## 🔍 Review Process

### What We Review
1. **Functionality**: Does it work correctly?
2. **Fit**: Does it advance the project's academic mission?
3. **Fairness**: Does it improve or maintain fairness properties?
4. **Compliance**: Does it respect the MIT license?
5. **Documentation**: Is it clearly explained?

### Timeline
- **Simple fixes/docs**: 3-5 business days
- **Feature contributions**: 1-2 weeks (may require extended discussion)
- **Research validations**: 2-3 weeks (peer review process)

## 📚 Research Contribution Guidelines

If your contribution includes research validation or new methods:

### 1. Reference Existing Work
```python
# Always cite sources in comments and docstrings
# Example:
def cross_entropy_loss_weighted(predictions, labels, weights):
    """
    Compute weighted cross-entropy loss per Wang et al. (2026).
    
    This approach addresses class imbalance in military benefit
    categories by assigning higher loss to rare classes.
    
    References:
        Wang, Z., Huang, C., Tang, K., & Yao, X. (2026).
        Procedural fairness in machine learning.
        Journal of Artificial Intelligence Research, 85.
    """
```

### 2. Include Validation & Metrics
```python
# Always show improvement with metrics
# Example change:
# Before: What-If consistency = 54% (integration scenarios)
# After:  What-If consistency = 62% (integration scenarios)
# Improvement: +8 percentage points
```

### 3. Contribute to Literature Review
If your contribution is based on recent research:
- Submit an update to `docs/ACADEMIC_FOUNDATION.md`
- Include proper APA citations
- Explain research gap addressed

## 🚫 Contribution Policies

### Can NOT Be Merged (Automatic Rejection)

- ❌ Commercial licensing or monetization code
- ❌ Removal or modification of license terms
- ❌ Attribution removal or concealment
- ❌ IP claims or patent assertions
- ❌ Third-party code without proper licensing
- ❌ Proprietary dependencies (use only open-source libraries)
- ❌ Debug/test files left in repository
- ❌ Large uncompressed model files (>100MB)

### Will Be Requested for Revision

- ⚠️ Missing tests (coverage < 80%)
- ⚠️ Incomplete documentation
- ⚠️ No fairness/bias analysis for model changes
- ⚠️ Missing research citations or motivation
- ⚠️ Code style violations (PEP 8)

## 🏆 Recognition

Contributors will be recognized:
- In a `CONTRIBUTORS.md` file (with permission)
- In release notes for significant contributions
- Through citation in publications/presentations based on their work

## 💬 Questions or Concerns?

- **Ask in an Issue**: For clarification on scope/approach
- **Start a Discussion**: For research-related questions
- **Email the Author**: For licensing/commercial inquiries

## 📜 License Acknowledgment

By contributing to Project Atlas, you agree that:

1. Your contribution is provided under **MIT** terms
2. You **grant the author** perpetual rights to use your contribution
3. Your contribution may be **used for any purpose** (commercial or non-commercial)
4. You **provide no warranty** and assume no liability for your contribution

```
CONTRIBUTION LICENSE AGREEMENT

By submitting a pull request, I certify that:
- My contribution is my original work and does not violate any third-party rights
- I grant the project author perpetual, worldwide rights to use my contribution
- My contribution is provided under MIT terms
- I understand no commercial use of this project is permitted
- I release any claim to compensation for this contribution
```

---

## 🙏 Thank You

Your contributions help advance open-source research in AI fairness and financial guidance for vulnerable populations. We appreciate your commitment to the academic mission of Project Atlas!

**Happy contributing!** 🚀
