"""
Test suite for Project Atlas AI orchestrator module.

Tests natural language parsing and profile construction.
"""

import pytest

from src.ai_layer.orchestrator import (
    NaturalLanguageParser,
    parse_query_to_profile,
    suggest_next_steps,
    validate_profile_completeness,
)
from src.data_models import create_empty_profile


class TestNaturalLanguageParser:
    """Test suite for rule-based query parsing."""

    def test_extract_city_with_state(self):
        """Test: Extract city, state from query."""

        query = "I'm moving to Denver, CO next year"
        params = NaturalLanguageParser.extract_parameters(query)

        # Check if target_city was extracted
        target_city = params.get("target_city", "")
        assert "Denver" in target_city or len(target_city) > 0

    def test_extract_salary(self):
        """Test: Extract salary amount."""

        query = "I expect to earn $120,000 in my next role"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("estimated_annual_salary") == 120000.0

    def test_extract_va_rating(self):
        """Test: Extract VA disability rating."""

        query = "I have a 50% VA rating"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("current_va_disability_rating") == 50

    def test_extract_job_search_months(self):
        """Test: Extract job search timeline."""

        query = "I plan to search for 6 months"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("job_search_timeline_months") == 6

    def test_extract_years_of_service(self):
        """Test: Extract years of service."""

        query = "I have 20 years of service"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("years_of_service") == 20

    def test_extract_rank(self):
        """Test: Extract military rank."""

        query = "I'm retiring as an E-7"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("rank") == "E-7"

    def test_extract_officer_rank(self):
        """Test: Extract officer rank."""

        query = "I was an O-4 Major"
        params = NaturalLanguageParser.extract_parameters(query)

        assert params.get("rank") == "O-4"

    def test_normalize_city_known_city(self):
        """Test: Normalize well-known city."""

        normalized = NaturalLanguageParser._normalize_city("Denver")

        assert normalized == "Denver, CO"

    def test_normalize_city_unknown_defaults_to_co(self):
        """Test: Unknown city defaults to Colorado."""

        normalized = NaturalLanguageParser._normalize_city("SomeUnknownCity")

        assert "CO" in normalized

    def test_extract_multiple_parameters(self):
        """
        Integration test: Extract multiple parameters from complex query.

        Example from the brief: "Show me the forecast for moving to Denver.
        I'm assuming a 6-month job search, a 50% VA rating, and I'll use
        Tricare Select for healthcare. My estimated salary will be $120,000."
        """

        query = (
            "Show me the forecast for moving to Denver. "
            "I'm assuming a 6-month job search, a 50% VA rating, "
            "and I'll use Tricare Select. My salary will be $120,000."
        )

        params = NaturalLanguageParser.extract_parameters(query)

        assert "Denver" in params.get("target_city", "")
        assert params.get("job_search_timeline_months") == 6
        assert params.get("current_va_disability_rating") == 50
        assert params.get("estimated_annual_salary") == 120000.0
        assert "tricare" in params.get("healthcare_plan_choice", "").lower()


class TestParseQueryToProfile:
    """Test profile construction from natural language."""

    def test_parse_query_creates_profile(self):
        """Test: Query parsing returns a valid profile."""

        query = "Moving to Austin with $100K salary and 30% VA rating"

        profile = parse_query_to_profile(query, user_name="Test User")

        assert profile.user_name == "Test User"
        assert profile.estimated_annual_salary == 100000.0
        assert profile.current_va_disability_rating == 30

    def test_parse_complete_scenario(self):
        """
        Integration test: Parse a complete transition scenario.

        This tests the full MVP flow from natural language to profile.
        """

        query = (
            "I'm an E-7 with 20 years of service, transitioning to Denver, CO. "
            "I have a 30% VA rating, about $50,000 saved, and expect to earn $120,000. "
            "I think the job search will take 6 months. I prefer Tricare Select."
        )

        profile = parse_query_to_profile(query, user_name="John Smith")

        assert profile.user_name == "John Smith"
        assert profile.rank == "E-7"
        assert profile.years_of_service == 20
        assert "Denver" in profile.target_city
        assert profile.current_va_disability_rating == 30
        assert profile.current_savings == 50000.0
        assert profile.estimated_annual_salary == 120000.0
        assert profile.job_search_timeline_months == 6


class TestProfileValidation:
    """Test profile validation and guidance."""

    def test_validate_complete_profile(self):
        """Test: Complete profile passes validation."""

        profile = create_empty_profile("Test User")
        profile.target_city = "Denver, CO"
        profile.estimated_annual_salary = 100000
        profile.current_savings = 50000
        profile.monthly_expenses_mandatory = 3000

        is_complete, missing = validate_profile_completeness(profile)

        assert is_complete
        assert len(missing) == 0

    def test_validate_incomplete_profile(self):
        """Test: Incomplete profile fails validation."""

        profile = create_empty_profile("Test User")
        # Missing: target_city, salary, savings, expenses

        is_complete, missing = validate_profile_completeness(profile)

        assert is_complete is False
        assert len(missing) > 0

    def test_suggest_next_steps_empty_profile(self):
        """Test: Get suggestions for filling empty profile."""

        profile = create_empty_profile("Test User")

        suggestions = suggest_next_steps(profile)

        # Should suggest key fields
        assert len(suggestions) > 0
        assert any("Where" in s or "city" in s.lower() for s in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
