"""
Unit tests for SessionStateManager.

Tests session state initialization, navigation, and persistence.
"""

import pytest
from unittest.mock import patch

from src.ui_layer.session_manager import SessionStateManager


class TestSessionStateInitialize:
    """Test SessionStateManager initialization."""

    def test_initialize_creates_all_form_fields(self, mock_session_state):
        """All FORM_FIELDS keys should be initialized in session state."""
        # Mock streamlit st.session_state
        import streamlit as st

        with patch.object(st, "session_state", mock_session_state):
            SessionStateManager.initialize()

            for field in SessionStateManager.FORM_FIELDS.keys():
                assert field in mock_session_state, f"Field {field} not initialized"

    def test_initialize_creates_current_step(self, mock_session_state):
        """current_step should be initialized to 1."""
        import streamlit as st

        with patch.object(st, "session_state", mock_session_state):
            SessionStateManager.initialize()
            assert mock_session_state.get("current_step") == 1

    def test_initialize_creates_classification_state(self, mock_session_state):
        """Classification maps should be initialized."""
        import streamlit as st

        with patch.object(st, "session_state", mock_session_state):
            SessionStateManager.initialize()

            assert "csv_classification_map" in mock_session_state
            assert isinstance(mock_session_state.get("csv_classification_map"), dict)

    def test_initialize_creates_prepaid_tracker(self, mock_session_state):
        """Prepaid tracker should be initialized as empty list."""
        import streamlit as st

        with patch.object(st, "session_state", mock_session_state):
            SessionStateManager.initialize()

            assert "prepaid_tracker" in mock_session_state
            assert isinstance(mock_session_state.get("prepaid_tracker"), list)


class TestSessionStateNavigation:
    """Test step navigation."""

    def test_next_step_increments(self, default_session_state):
        """next_step() should increment current_step."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 1
            SessionStateManager.next_step()
            assert default_session_state["current_step"] == 2

    def test_prev_step_decrements(self, default_session_state):
        """prev_step() should decrement current_step."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 3
            SessionStateManager.prev_step()
            assert default_session_state["current_step"] == 2

    def test_next_step_does_not_exceed_max(self, default_session_state):
        """next_step() should not exceed max steps (11)."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 11
            default_session_state["total_steps"] = 11
            SessionStateManager.next_step()
            assert default_session_state["current_step"] == 11  # Should stay at 11

    def test_prev_step_does_not_go_below_min(self, default_session_state):
        """prev_step() should not go below 1."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 1
            SessionStateManager.prev_step()
            assert default_session_state["current_step"] == 1  # Should stay at 1


class TestSessionStateHelpers:
    """Test helper functions."""

    def test_is_first_step_true(self, default_session_state):
        """is_first_step() should return True when on step 1."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 1
            assert SessionStateManager.is_first_step() is True

    def test_is_first_step_false(self, default_session_state):
        """is_first_step() should return False when not on step 1."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 2
            assert SessionStateManager.is_first_step() is False

    def test_is_last_step_true(self, default_session_state):
        """is_last_step() should return True when on step 11."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 11
            default_session_state["total_steps"] = 11
            assert SessionStateManager.is_last_step() is True

    def test_is_last_step_false(self, default_session_state):
        """is_last_step() should return False when not on step 11."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            default_session_state["current_step"] = 7
            assert SessionStateManager.is_last_step() is False


class TestSessionStatePersistence:
    """Test session state data persistence across navigation."""

    def test_yos_persists_after_next_prev(self, default_session_state):
        """YOS (Years of Service) should persist after Next then Back."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            original_yos = 28
            default_session_state["user_years_of_service"] = original_yos
            default_session_state["current_step"] = 1

            # Navigate forward and back
            SessionStateManager.next_step()
            SessionStateManager.prev_step()

            assert (
                default_session_state["user_years_of_service"] == original_yos
            ), "YOS should persist"

    def test_dependents_persist_after_navigation(self, default_session_state):
        """Dependents should persist after navigation."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            original_deps = 2
            default_session_state["user_dependents"] = original_deps
            default_session_state["current_step"] = 1

            # Navigate forward and back
            SessionStateManager.next_step()
            SessionStateManager.next_step()
            SessionStateManager.prev_step()

            assert (
                default_session_state["user_dependents"] == original_deps
            ), "Dependents should persist"

    def test_pension_persists_after_navigation(self, default_session_state):
        """Pension should persist after navigation."""
        import streamlit as st

        with patch.object(st, "session_state", default_session_state):
            original_pension = 5500
            default_session_state["military_pension_gross"] = original_pension
            default_session_state["current_step"] = 1

            # Navigate through multiple steps
            for _ in range(3):
                SessionStateManager.next_step()

            for _ in range(2):
                SessionStateManager.prev_step()

            assert (
                default_session_state["military_pension_gross"] == original_pension
            ), "Pension should persist"
