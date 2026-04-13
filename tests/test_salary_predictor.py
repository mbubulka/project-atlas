"""
Test suite for Project Atlas salary_predictor module.

Tests the salary prediction functionality with known scenarios.
"""

import pytest

from src.data_models import create_empty_profile
from src.model_layer.salary_predictor import estimate_salary_range, predict_salary


class TestSalaryPredictor:
    """Test cases for salary prediction."""

    def test_predict_salary_mvp_accepts_user_input(self):
        """Test MVP: salary prediction returns user's input estimate."""

        profile = create_empty_profile("John Doe")
        profile.estimated_annual_salary = 120000

        result = predict_salary(profile)

        assert result.estimated_annual_salary == 120000
        assert result.metadata["salary_prediction_method"] == "user_estimate"

    def test_predict_salary_negative_salary_raises_error(self):
        """Test: negative salary raises ValueError."""

        profile = create_empty_profile("Jane Doe")
        profile.estimated_annual_salary = -50000

        with pytest.raises(ValueError, match="non-negative"):
            predict_salary(profile)

    def test_estimate_salary_range_low_estimate(self):
        """Test salary range estimation (conservative scenario)."""

        profile = create_empty_profile("Test User")
        profile.estimated_annual_salary = 100000

        ranges = estimate_salary_range(profile, low_percentile=0.25, high_percentile=0.75)

        assert ranges["low"] == 25000  # 0.25 * 100000
        assert ranges["mid"] == 100000
        assert ranges["high"] == 75000  # 0.75 * 100000

    def test_estimate_salary_range_high_estimate(self):
        """Test salary range with high percentiles."""

        profile = create_empty_profile("Test User")
        profile.estimated_annual_salary = 100000

        ranges = estimate_salary_range(profile, low_percentile=0.8, high_percentile=1.2)

        assert ranges["low"] == 80000
        assert ranges["mid"] == 100000
        assert ranges["high"] == 120000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
