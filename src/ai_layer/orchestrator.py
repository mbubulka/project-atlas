"""
AI Orchestrator for Project Atlas.

This module handles natural language query parsing and profile construction.
It implements a "Bring Your Own Key" (BYOK) pattern for optional LLM integration,
making AI features optional rather than mandatory.

Supported modes:
1. Rule-based parsing (MVP, no LLM required)
2. OpenAI API (with user-provided key)
3. Local LLM via Ollama (with user-provided server)
4. Claude via Anthropic API (with user-provided key)

All modes are optional. The app functions fully without LLM integration.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.data_models import TransitionProfile, create_empty_profile

logger = logging.getLogger(__name__)


# ========== CONFIGURATION ==========

# Environment variables for API keys (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# ========== RULE-BASED PARSER (MVP) ==========


class NaturalLanguageParser:
    """
    Rule-based parser for transitioning military member queries.

    Extracts key parameters from natural language without requiring an LLM.

    Example inputs:
    - "Show me the forecast for moving to Denver. I'm assuming a 6-month job
       search, a 50% VA rating, and I'll use Tricare Select. My salary will be $120,000."

    - "I want to move to Austin, TX. I have 25 years of service, I'm an E-7.
       I expect to take 3 months to find a job and I think I can earn $130K."
    """

    # Regex patterns for extraction
    PATTERNS = {
        "city": r"(?:move|mov(?:ed|ing)|relocat(?:e|ing)|going|transition(?:ing)?)\s+(?:to\s+)?([A-Z][a-z]+)(?:\s*,\s*([A-Z]{2}))?",
        "salary": r"(?:expect.*?earn|salary|earn|earning|make|income|compensation)\s+(?:of\s+)?\$?([0-9,]+)\s*[kK]?|\$([0-9,]+)(?:\s*[kK])?(?:\s+salary)?",
        "va_rating": r"(\d+)\s*%?\s*(?:VA|disability|rating)",
        "job_search_months": r"(?:search\s+)?for\s+(\d+)\s*(?:month|months|mo)|(\d+)[-\s]?(?:month|months|mo)\s*(?:job\s+)?search",
        "years_of_service": r"(\d+)\s*(?:year|yr)s?\s*(?:of service|in service|service)",
        "rank": r"\b([EO]-?\d)\b",
        "job_offer_certainty": r"(?:confident|certainty|likely|probably|chance).*?(\d+)%",
        "current_savings": r"(?:savings|saved|account|emergency|about\s+\$).*?\$?([\d,]+(?:\.\d{2})?)",
        "tricare_plan": r"(?:tricare|healthcare).*?(select|prime|for life)",
        "expenses": r"(?:spend|expense).*?\$?([\d,]+(?:\.\d{2})?)",
    }

    @staticmethod
    def extract_parameters(query: str) -> Dict[str, Any]:
        """
        Extract parameters from natural language query using regex patterns.

        Args:
            query (str): User's natural language query.

        Returns:
            Dict[str, Any]: Extracted parameters (may have empty/None values).

        Example:
            >>> parser = NaturalLanguageParser()
            >>> params = parser.extract_parameters(
            ...     "Moving to Denver in 6 months with $100K salary"
            ... )
            >>> params['target_city']
            'Denver'
        """

        params = {}

        # Extract city (most important)
        city_match = re.search(NaturalLanguageParser.PATTERNS["city"], query, re.IGNORECASE)
        if city_match:
            city = city_match.group(1)
            # Normalize city format
            if "," not in city:
                # Try to infer state from known cities
                city = NaturalLanguageParser._normalize_city(city)
            params["target_city"] = city

        # Extract salary (with priority for "expect to earn")
        # Try specific patterns in order
        salary_str = None

        # First try: "expect to earn $X"
        expect_match = re.search(r"expect\s+(?:to\s+)?earn\s+(?:about\s+)?\$?([0-9,]+)", query, re.IGNORECASE)
        if expect_match:
            salary_str = expect_match.group(1)
        else:
            # Second try: general salary patterns
            salary_match = re.search(NaturalLanguageParser.PATTERNS["salary"], query, re.IGNORECASE)
            if salary_match:
                salary_str = salary_match.group(1) or salary_match.group(2) or ""

        if salary_str:
            salary_str = salary_str.replace(",", "")
            try:
                salary = float(salary_str)
                # If value is small (< 1000), assume it's in thousands (K)
                if salary < 1000:
                    salary *= 1000
                params["estimated_annual_salary"] = salary
            except ValueError:
                pass

        # Extract VA rating
        va_match = re.search(NaturalLanguageParser.PATTERNS["va_rating"], query, re.IGNORECASE)
        if va_match:
            try:
                params["current_va_disability_rating"] = int(va_match.group(1))
            except ValueError:
                pass

        # Extract job search timeline (months)
        months_match = re.search(NaturalLanguageParser.PATTERNS["job_search_months"], query, re.IGNORECASE)
        if months_match:
            try:
                # Handle multiple capture groups
                months_str = months_match.group(1) or months_match.group(2)
                if months_str:
                    params["job_search_timeline_months"] = int(months_str)
            except (ValueError, IndexError):
                pass

        # Extract years of service
        yos_match = re.search(NaturalLanguageParser.PATTERNS["years_of_service"], query, re.IGNORECASE)
        if yos_match:
            try:
                params["years_of_service"] = int(yos_match.group(1))
            except ValueError:
                pass

        # Extract rank
        rank_match = re.search(NaturalLanguageParser.PATTERNS["rank"], query, re.IGNORECASE)
        if rank_match:
            params["rank"] = rank_match.group(1).upper()

        # Extract job offer certainty
        certainty_match = re.search(NaturalLanguageParser.PATTERNS["job_offer_certainty"], query, re.IGNORECASE)
        if certainty_match:
            try:
                params["job_offer_certainty"] = int(certainty_match.group(1)) / 100.0
            except ValueError:
                pass

        # Extract current savings
        savings_match = re.search(NaturalLanguageParser.PATTERNS["current_savings"], query, re.IGNORECASE)
        if savings_match:
            savings_str = savings_match.group(1).replace(",", "")
            try:
                params["current_savings"] = float(savings_str)
            except ValueError:
                pass

        # Extract Tricare plan
        tricare_match = re.search(NaturalLanguageParser.PATTERNS["tricare_plan"], query, re.IGNORECASE)
        if tricare_match:
            plan_type = tricare_match.group(1).lower()
            params["healthcare_plan_choice"] = f"tricare_{plan_type}"

        logger.info(f"Extracted parameters: {params}")

        return params

    @staticmethod
    def _normalize_city(city: str) -> str:
        """
        Normalize city name to 'City, ST' format.

        Args:
            city (str): City name (may lack state).

        Returns:
            str: Normalized city string.
        """

        # Common city -> (city, state) mappings
        city_state_map = {
            "Denver": "Denver, CO",
            "Austin": "Austin, TX",
            "Dallas": "Dallas, TX",
            "Houston": "Houston, TX",
            "San Antonio": "San Antonio, TX",
            "Phoenix": "Phoenix, AZ",
            "Charlotte": "Charlotte, NC",
            "Raleigh": "Raleigh, NC",
            "Nashville": "Nashville, TN",
            "Memphis": "Memphis, TN",
            "Portland": "Portland, OR",
            "Seattle": "Seattle, WA",
            "New York": "New York, NY",
            "Los Angeles": "Los Angeles, CA",
            "San Diego": "San Diego, CA",
            "San Francisco": "San Francisco, CA",
            "Boston": "Boston, MA",
            "Chicago": "Chicago, IL",
            "Miami": "Miami, FL",
            "Washington": "Washington, DC",
            "Arlington": "Arlington, VA",
        }

        return city_state_map.get(city, f"{city}, CO")  # Default to CO if unknown


def parse_query_to_profile(query: str, user_name: str = "User") -> TransitionProfile:
    """
    Parse natural language query and build a TransitionProfile.

    This is the MVP approach: pure rule-based parsing, no LLM required.

    Args:
        query (str): User's natural language query.
        user_name (str): User's name.

    Returns:
        TransitionProfile: Partially populated profile with extracted parameters.

    Example:
        >>> profile = parse_query_to_profile(
        ...     "Moving to Denver in 6 months with $120K salary and 50% VA rating"
        ... )
        >>> profile.target_city
        'Denver, CO'
    """

    parser = NaturalLanguageParser()
    params = parser.extract_parameters(query)

    # Create profile with defaults
    profile = create_empty_profile(user_name=user_name)

    # Apply extracted parameters
    for key, value in params.items():
        if hasattr(profile, key) and value is not None:
            setattr(profile, key, value)

    logger.info(f"Built profile from query for {user_name}")

    return profile


# ========== LLM INTEGRATION (Optional) ==========


def parse_query_with_llm(
    query: str,
    user_name: str = "User",
    api_key: Optional[str] = None,
    llm_provider: str = "openai",
) -> TransitionProfile:
    """
    Parse query using an LLM (optional, "Bring Your Own Key").

    This is an advanced approach that uses an LLM to understand complex queries.
    Users must provide their own API key or local server.

    Args:
        query (str): User's natural language query.
        user_name (str): User's name.
        api_key (Optional[str]): LLM API key. If None, falls back to environment variable.
        llm_provider (str): 'openai', 'anthropic', or 'ollama'.

    Returns:
        TransitionProfile: Profile populated by LLM parsing.

    Raises:
        ValueError: If LLM not available or API key missing.

    Example:
        >>> profile = parse_query_with_llm(
        ...     "I'm moving to Denver with my family. I have 25 years in...",
        ...     api_key="sk-...",
        ...     llm_provider='openai'
        ... )
    """

    # Attempt rule-based parsing first as fallback
    fallback_profile = parse_query_to_profile(query, user_name)

    try:
        if llm_provider == "openai":
            return _parse_with_openai(query, user_name, api_key, fallback_profile)

        elif llm_provider == "anthropic":
            return _parse_with_anthropic(query, user_name, api_key, fallback_profile)

        elif llm_provider == "ollama":
            return _parse_with_ollama(query, user_name, fallback_profile)

        else:
            raise ValueError(f"Unknown LLM provider: {llm_provider}")

    except Exception as e:
        logger.warning(f"LLM parsing failed, falling back to rule-based: {e}")
        return fallback_profile


def _parse_with_openai(
    query: str,
    user_name: str,
    api_key: Optional[str],
    fallback_profile: TransitionProfile,
) -> TransitionProfile:
    """
    Parse using OpenAI API.

    Args:
        query (str): User's query.
        user_name (str): User's name.
        api_key (Optional[str]): OpenAI API key.
        fallback_profile (TransitionProfile): Fallback if LLM fails.

    Returns:
        TransitionProfile: Parsed profile.

    Raises:
        ValueError: If API key not provided.
    """

    key = api_key or OPENAI_API_KEY

    if not key:
        raise ValueError("OpenAI API key required. Provide via api_key parameter or OPENAI_API_KEY env var.")

    try:
        import openai

        openai.api_key = key
    except ImportError:
        raise ImportError("openai library not installed. Install via: pip install openai")

    prompt = _build_extraction_prompt(query)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial planning assistant for transitioning military members. Extract profile parameters from natural language queries and return JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        response_text = response["choices"][0]["message"]["content"]

        # Parse JSON response
        params = json.loads(response_text)

        # Merge with fallback
        profile = fallback_profile
        for key, value in params.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

        logger.info("Successfully parsed query with OpenAI")

        return profile

    except json.JSONDecodeError:
        logger.error("Failed to parse LLM JSON response")
        return fallback_profile


def _parse_with_anthropic(
    query: str,
    user_name: str,
    api_key: Optional[str],
    fallback_profile: TransitionProfile,
) -> TransitionProfile:
    """
    Parse using Anthropic Claude API.

    Args:
        query (str): User's query.
        user_name (str): User's name.
        api_key (Optional[str]): Anthropic API key.
        fallback_profile (TransitionProfile): Fallback if LLM fails.

    Returns:
        TransitionProfile: Parsed profile.

    Raises:
        ValueError: If API key not provided.
    """

    key = api_key or ANTHROPIC_API_KEY

    if not key:
        raise ValueError("Anthropic API key required. Provide via api_key parameter or ANTHROPIC_API_KEY env var.")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
    except ImportError:
        raise ImportError("anthropic library not installed. Install via: pip install anthropic")

    prompt = _build_extraction_prompt(query)

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system="You are a financial planning assistant for transitioning military members. Extract profile parameters from natural language queries and return JSON.",
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        # Parse JSON response
        params = json.loads(response_text)

        # Merge with fallback
        profile = fallback_profile
        for key, value in params.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

        logger.info("Successfully parsed query with Claude")

        return profile

    except json.JSONDecodeError:
        logger.error("Failed to parse LLM JSON response")
        return fallback_profile


def _parse_with_ollama(
    query: str,
    user_name: str,
    fallback_profile: TransitionProfile,
) -> TransitionProfile:
    """
    Parse using local Ollama server.

    Requires Ollama to be running locally (typically on port 11434).

    Args:
        query (str): User's query.
        user_name (str): User's name.
        fallback_profile (TransitionProfile): Fallback if LLM fails.

    Returns:
        TransitionProfile: Parsed profile.

    Raises:
        ConnectionError: If Ollama server not available.
    """

    try:
        import requests
    except ImportError:
        raise ImportError("requests library not installed. Install via: pip install requests")

    prompt = _build_extraction_prompt(query)

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "mistral",  # or other local model
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "")

        # Try to extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            params = json.loads(json_match.group())

            profile = fallback_profile
            for key, value in params.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)

            logger.info("Successfully parsed query with Ollama")

            return profile

    except Exception as e:
        logger.error(f"Ollama parsing failed: {e}")
        return fallback_profile


def _build_extraction_prompt(query: str) -> str:
    """
    Build a prompt for LLM to extract profile parameters.

    Args:
        query (str): User's query.

    Returns:
        str: Prompt for LLM.
    """

    prompt = f"""
Extract the following parameters from the user's query about their military transition:

Query: "{query}"

Return a JSON object with these fields (use null for missing values):
{{
  "target_city": "City, ST format (e.g., 'Denver, CO')",
  "estimated_annual_salary": "numeric salary (e.g., 120000)",
  "current_va_disability_rating": "VA rating 0-100",
  "job_search_timeline_months": "number of months",
  "years_of_service": "number of years",
  "rank": "military rank (e.g., 'E-7')",
  "job_offer_certainty": "probability 0.0-1.0",
  "current_savings": "numeric amount saved",
  "healthcare_plan_choice": "tricare_select, tricare_prime, va_health, or aca",
  "monthly_expenses_mandatory": "monthly mandatory expenses",
  "monthly_expenses_negotiable": "monthly negotiable expenses",
  "monthly_expenses_optional": "monthly optional expenses"
}}

Only return the JSON object, no other text.
"""

    return prompt


# ========== UTILITY FUNCTIONS ==========


def validate_profile_completeness(profile: TransitionProfile) -> Tuple[bool, List[str]]:
    """
    Check if profile has enough data to run simulation.

    Args:
        profile (TransitionProfile): Profile to validate.

    Returns:
        Tuple[bool, List[str]]: (is_complete, list_of_missing_fields)

    Example:
        >>> is_complete, missing = validate_profile_completeness(profile)
        >>> if not is_complete:
        ...     print(f"Please fill in: {missing}")
    """

    required_fields = [
        ("target_city", "Target city"),
        ("estimated_annual_salary", "Estimated salary"),
        ("current_savings", "Current savings"),
        ("monthly_expenses_mandatory", "Monthly expenses"),
    ]

    missing = []

    for field_name, display_name in required_fields:
        value = getattr(profile, field_name, None)

        if value is None or value == "" or (isinstance(value, (int, float)) and value == 0):
            missing.append(display_name)

    is_complete = len(missing) == 0

    return is_complete, missing


def suggest_next_steps(profile: TransitionProfile) -> List[str]:
    """
    Suggest what data/fields the user should fill in next.

    Args:
        profile (TransitionProfile): Current profile.

    Returns:
        List[str]: Suggested next steps.
    """

    suggestions = []

    if not profile.target_city:
        suggestions.append("📍 Where are you planning to move?")

    if profile.estimated_annual_salary == 0:
        suggestions.append("[MONEY] What salary are you targeting?")

    if profile.current_savings == 0:
        suggestions.append("🏦 How much do you have saved?")

    if profile.monthly_expenses_mandatory == 0:
        suggestions.append("[STATS] Upload your expenses to calculate mandatory spending")

    if profile.job_search_timeline_months == 0:
        suggestions.append("⏰ How long do you expect the job search to take?")

    return suggestions
