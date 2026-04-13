"""
Root conftest.py for pytest configuration and shared fixtures.

Provides fixtures for both tests/ and root-level test files.

NOTE: test_wizard_flow_e2e import is commented out due to relative import issues.
Each test file should set up its own fixtures as needed.
"""

import pytest

# Disabled: test_wizard_flow_e2e has relative import issues that break conftest loading
# from test_wizard_flow_e2e import setup_test_session


# @pytest.fixture
# def session():
#     """Fixture: Set up complete session state for E2E testing."""
#     return setup_test_session()
