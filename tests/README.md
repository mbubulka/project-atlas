"""
PYTEST TESTING GUIDE FOR PYCHARM

Military Retirement Planning Tool - FinPlanGuardian
Educational Purposes Only

===================================================================================================
QUICK START
===================================================================================================

1. SETUP IN PYCHARM:
   a. File → Settings → Tools → Python Integrated Tools
      Set "Default test runner" to "pytest"
   
   b. File → Project Structure → Mark "tests/" folder as "Test Sources Root"
   
   c. Terminal → Install dependencies:
      pip install pytest pytest-cov pytest-html flake8 pylint

2. RUN ALL TESTS:
   a. Right-click tests/ folder → "Run pytest in 'tests'"
   
   b. Or use Terminal:
      pytest tests/ -v

3. RUN SINGLE TEST FILE:
   Right-click tests/test_code_quality.py → "Run pytest in 'test_code_quality'"

4. RUN WITH COVERAGE:
   Terminal → pytest tests/ --cov=src --cov-report=html
   Then open htmlcov/index.html in browser


===================================================================================================
TEST SUITE ORGANIZATION
===================================================================================================

tests/
├── test_code_quality.py       (PEP8, Flake8, Naming Conventions)
├── test_edge_cases.py          (Boundary Conditions, Invalid Inputs)
├── test_disclaimers.py         (Educational Warnings, Liability)
├── test_ai_validation.py       (Verification Against Sources)
└── README.md                   (This file)


===================================================================================================
TEST SUITE 1: CODE QUALITY (test_code_quality.py)
===================================================================================================

PURPOSE:
Ensures code follows professional standards and best practices.

TESTS INCLUDED:
✓ Flake8 compliance (E/F level violations)
✓ No emoji characters (only ASCII)
✓ Line length enforcement (max 100 chars)
✓ Import organization (stdlib, third-party, local)
✓ Docstring presence
✓ Function naming (snake_case)
✓ Class naming (PascalCase)

HOW TO RUN:
- Right-click test_code_quality.py → Run
- Or: pytest tests/test_code_quality.py -v

EXPECTED OUTPUT:
✓ All tests passing
✓ Zero Flake8 E/F violations
✓ No emoji found

FIXING ISSUES:
- Remove emoji: Change "❌ Error" → "[ERROR]"
- Line length: Split long lines or use continuation
- Import order: Run: isort src/
- Missing docstrings: Add """ """ to functions


===================================================================================================
TEST SUITE 2: EDGE CASES (test_edge_cases.py)
===================================================================================================

PURPOSE:
Tests boundary conditions and invalid inputs to ensure robustness.

CRITICAL EDGE CASES TESTED:

A. PENSION CALCULATIONS:
   ✓ YOS < 20 (below pension eligibility)
   ✓ YOS = 20 (minimum eligibility)
   ✓ YOS > 50 (unrealistic but handled)
   ✓ Negative YOS (should error)
   ✓ Non-integer YOS (should error or convert)
   ✓ Invalid rank formats

B. VA DISABILITY:
   ✓ 0% rating (should be $0)
   ✓ 50% rating (mid-range)
   ✓ 100% rating (maximum)
   ✓ Over 100% (should error)
   ✓ Negative rating (should error)
   ✓ Monotonic increase verification

C. FINANCIAL VALUES:
   ✓ Zero savings (should calculate)
   ✓ Negative savings (should error)
   ✓ Zero salary (should calculate)
   ✓ Extreme salaries (should not overflow)

D. FAMILY SIZE:
   ✓ Size 1 (single person)
   ✓ Size 4 (standard family)
   ✓ Size 0 (invalid)
   ✓ Size 50 (unrealistic)
   ✓ Non-integer size (should error)
   ✓ Scaling validation (family size 4 > family size 1)

HOW TO RUN:
- Right-click test_edge_cases.py → Run
- Or: pytest tests/test_edge_cases.py -v
- Or specific test: pytest tests/test_edge_cases.py::TestPensionEdgeCases -v

EXPECTED OUTPUT:
✓ All edge cases handled gracefully
✓ Clear error messages for invalid inputs
✓ No crashes on extreme values

FAILING TESTS MEAN:
- Function doesn't validate inputs
- Error messages are unclear
- Edge cases not handled consistently


===================================================================================================
TEST SUITE 3: DISCLAIMERS (test_disclaimers.py)
===================================================================================================

PURPOSE:
Verifies that educational warnings and liability disclaimers are present.

CRITICAL: This tool must clearly state it is educational and verify users
understand it is not professional financial advice.

TESTS INCLUDED:
✓ Disclaimers present in module docstrings
✓ Critical functions have disclaimers
✓ Output includes "EDUCATIONAL USE" notice
✓ Sources are cited explicitly
✓ Tool limitations are listed
✓ Professional consultation is recommended
✓ Official source referrals present
✓ Error messages are educational

DISCLAIMER CHECKLIST:
[ ] Educational Purpose - "This is educational, not advice"
[ ] Legal Limitation - "Not financial/legal advice"
[ ] Source Attribution - "Based on DoD tables, VA.gov, etc."
[ ] Limitation Statement - "Does not include BRS, SBP, etc."
[ ] Professional Guidance - "Consult a financial advisor"
[ ] Official Source Referral - "Verify at VA.gov, IRS.gov, etc."

HOW TO RUN:
- Right-click test_disclaimers.py → Run
- Or: pytest tests/test_disclaimers.py -v

EXPECTED OUTPUT:
✓ Disclaimers found in key modules
✓ Sources attributed
✓ Professional guidance recommended
⚠️  Warnings print for missing disclaimers

FIXING ISSUES:
- Add to module docstring:
  """
  DISCLAIMER: Educational purposes only.
  Not financial advice. See sources below.
  Sources: VA.gov, OPM, IRS
  """
- Add to critical function:
  "Verify against official source: VA.gov"


===================================================================================================
TEST SUITE 4: AI VALIDATION (test_ai_validation.py)
===================================================================================================

PURPOSE:
CRITICAL - Ensures all calculations can be verified against official government
sources. This prevents AI-generated hallucinations and false claims.

TESTS INCLUDED:
✓ Military pension verified against DoD tables
✓ VA benefits verified against VA.gov rates
✓ Spending profiles justified with BLS data
✓ Claims are attributed to sources
✓ No false confidence statements
✓ Instructions provided for verification
✓ Salary recommendations use ranges (not absolutes)

VERIFIED CALCULATIONS:

MILITARY PENSION:
Source: 10 U.S.C. § 1406
Formula: 0.025 × Years_of_Service × Monthly_Base_Pay
Verified Values:
  ✓ E-5/20 YOS = $1,437/month
  ✓ E-7/24 YOS = $2,206/month
  ✓ O-5/26 YOS = $4,124/month

VA DISABILITY:
Source: VA.gov Official Schedule, 38 CFR Part 3
Verified Ranges:
  ✓ 0% = $0/month
  ✓ 20% = ~$354/month
  ✓ 40% = ~$786/month
  ✓ 100% = ~$3,800/month

SPENDING PROFILES:
Source: BLS Consumer Expenditure Survey (2024)
Guidelines:
  ✓ E-5 family of 4 ≈ $4,000-5,000/month
  ✓ O-4 family of 4 ≈ $8,000-10,000/month
  ✓ Spending should scale with family size

HOW TO RUN:
- Right-click test_ai_validation.py → Run
- Or: pytest tests/test_ai_validation.py -v
- Or with detailed output: pytest tests/test_ai_validation.py::TestMilitaryPensionVerification -v

EXPECTED OUTPUT:
✓ All pension calculations match verified amounts
✓ VA rates within official ranges
✓ Spending profiles cited to BLS
✓ Sources attributed in code

FAILING TESTS MEAN:
- Calculation doesn't match official government data
- Sources aren't cited
- AI-generated estimates are being used
- Claims lack verification


===================================================================================================
RUNNING ALL TESTS WITH FULL REPORTING
===================================================================================================

COMMAND 1: Run all tests with verbose output
pytest tests/ -v

COMMAND 2: Run with coverage report
pytest tests/ --cov=src --cov-report=html
# Opens htmlcov/index.html in browser

COMMAND 3: Run with detailed failure info
pytest tests/ -v --tb=long

COMMAND 4: Run specific test class
pytest tests/test_code_quality.py::TestPEP8Compliance -v

COMMAND 5: Run with markers
pytest -m "not slow" tests/  # Skip slow tests

COMMAND 6: Watch for changes (requires pytest-watch)
pip install pytest-watch
ptw tests/ -v

OUTPUT EXPLANATION:

✓ PASSED     = Test succeeded
✗ FAILED     = Test failed (look for red text error)
⊘ SKIPPED    = Test skipped (marked as skip)
⚠ WARNING    = Non-critical issue found

COVERAGE REPORT:
- Lines covered: % of code executed by tests
- Target: > 85% coverage for src/
- Focus on: Critical calculations, input validation


===================================================================================================
COMMON TEST FAILURES & FIXES
===================================================================================================

FAILURE 1: "No module named 'src'"
FIX: Ensure src/ folder exists and has __init__.py
  - Create: src/__init__.py (empty file)
  - Or: Run pytest from project root: pytest tests/

FAILURE 2: "ModuleNotFoundError: No module named 'military_reference_data'"
FIX: Check import path in test file
  - Should be: from src.test_data.military_reference_data import ...
  - Verify folder structure exists

FAILURE 3: Emoji test fails with "codec can't encode"
FIX: This means emojis are in code - remove them
  - Replace emoji with ASCII: [OK], [ERROR], [WARNING]

FAILURE 4: Line length test shows lines > 100 chars
FIX: Split long lines
  # Before:
  result = some_long_function_name(parameter1, parameter2, parameter3, parameter4)
  
  # After:
  result = some_long_function_name(
      parameter1, parameter2,
      parameter3, parameter4
  )

FAILURE 5: Flake8 reports "F401 imported but unused"
FIX: Remove unused imports
  - Or use: from module import * as _  (if intentional)

FAILURE 6: Test expects $1,437 but got $1,437.15
FIX: Rounding difference - both are correct
  - Update test to allow small tolerance:
  - assert abs(pension - expected) < 0.10


===================================================================================================
RUNNING TESTS IN PYCHARM UI
===================================================================================================

METHOD 1: Right-click Run (Easiest)
1. Right-click tests/ folder
2. Select "Run pytest in 'tests'" (if installed)
3. Output shows in "Run" tab at bottom

METHOD 2: Using PyCharm Run Menu
1. Top menu → Run → Edit Configurations
2. Click + → Python Tests → pytest
3. Set Target: tests/
4. Click Run (green play button)

METHOD 3: Terminal in PyCharm
1. View → Tool Windows → Terminal
2. Type: pytest tests/ -v
3. Press Enter

VIEWING TEST RESULTS:
- Green bar = All tests passed
- Red bar = Some tests failed
- Click test name to jump to code
- Click error message for details

DEBUG MODE:
1. Set breakpoint in test (click line number)
2. Right-click test → Debug 'test_...'
3. Step through execution with F10/F11


===================================================================================================
CONTINUOUS INTEGRATION
===================================================================================================

To run tests automatically on code changes:

OPTION 1: pytest-watch (recommended)
pip install pytest-watch
ptw tests/ -v

OPTION 2: Manual - press Up arrow in Terminal to re-run last command

OPTION 3: PyCharm - File → Settings → Tools → Python → pytest
Enable "Run tests when files change"


===================================================================================================
TEST REPORTING
===================================================================================================

GENERATE HTML REPORT:
pytest tests/ -v --cov=src --cov-report=html

FILES CREATED:
- htmlcov/index.html  (Open in browser)
- .coverage (data file)

GENERATING PDF REPORT:
pytest tests/ --cov=src --cov-report=term-missing > test_report.txt

SHARING TEST RESULTS:
- Email htmlcov/ folder zip
- Share test_report.txt summary
- Screenshot of pytest output showing [✓ passed]


===================================================================================================
EDUCATIONAL FOCUS
===================================================================================================

These tests are designed to teach:

1. CODE QUALITY
   - How to write professional Python (PEP8)
   - Why code standards matter
   - Tools for enforcing quality (Flake8, Pylint)

2. EDGE CASE THINKING
   - What can go wrong with inputs
   - How to validate user input
   - Graceful error handling

3. DISCLAIMER RESPONSIBILITY
   - Why disclaimers matter
   - How to write educational software responsibly
   - Legal and ethical considerations

4. VERIFICATION PRACTICES
   - How to ground claims in sources
   - Why AI claims need verification
   - Best practices for educational software

Each test failure is a LEARNING OPPORTUNITY, not a failure of the software.


===================================================================================================
NEXT STEPS
===================================================================================================

AFTER TESTS PASS:
1. Review code coverage: >85% target
2. Document any allowed warnings/exclusions
3. Create CI/CD pipeline (GitHub Actions, Jenkins, etc.)
4. Set up automated testing on commits
5. Review disclaimers with legal if making public

IF TESTS FAIL:
1. Read the failure message carefully
2. Look at expected vs actual values
3. Check source code for the issue
4. Make minimal fix
5. Re-run single test to verify
6. Run full suite to check for side effects


===================================================================================================
RESOURCES
===================================================================================================

PYTEST:
- https://docs.pytest.org/
- https://docs.pytest.org/en/stable/fixture.html

CODE QUALITY:
- https://www.python.org/dev/peps/pep-0008/
- https://flake8.pycqa.org/
- https://www.pylint.org/

OFFICIAL SOURCES FOR DATA:
- Military Pay: federalpay.org, military.com
- VA Benefits: VA.gov, 38 CFR
- IRS Tax: IRS.gov, TaxFoundation.org
- BLS Data: bls.gov/cex

EDUCATIONAL RESOURCES:
- PyTest Official Documentation
- Real Python pytest tutorial
- unittest (Python standard library)


===================================================================================================
"""
