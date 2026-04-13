"""
Ollama LLM Client - Optional enhancement for AI chat responses.

This module provides a client for interacting with Ollama (local LLM).
If Ollama is unavailable, the system gracefully falls back to rule-based responses.

Supports dev mode with local LLM enhancements while maintaining fallback
for demo mode (where Ollama may not be available).

Usage:
    client = OllamaClient()
    if client.is_available():
        enhanced_response = client.generate_response(prompt)
    else:
        # Use rule-based responses fallback
        pass
"""

from typing import Optional

import requests


class OllamaClient:
    """Client for Ollama LLM - with graceful degradation."""

    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "mistral"
    TIMEOUT = 5  # seconds

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        model: str = DEFAULT_MODEL,
        enabled: bool = True,
    ):
        """
        Initialize Ollama client.

        Args:
            host: Ollama server URL (default: localhost:11434)
            model: Model name to use (default: mistral)
            enabled: Whether to attempt Ollama integration (default: True)
        """
        self.host = host
        self.model = model
        self.enabled = enabled
        self._available = None  # Cache availability check

    def is_available(self) -> bool:
        """
        Check if Ollama server is available and responding.

        Returns:
            True if Ollama is running and accessible, False otherwise
        """
        if not self.enabled:
            return False

        if self._available is not None:
            return self._available

        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=self.TIMEOUT,
            )
            self._available = response.status_code == 200
        except (requests.RequestException, Exception):
            self._available = False

        return self._available

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
    ) -> Optional[str]:
        """
        Generate response using Ollama LLM.

        Args:
            prompt: User prompt/question
            system_prompt: System context for the model
            max_tokens: Maximum response length

        Returns:
            Generated response text, or None if generation fails
        """
        if not self.is_available():
            return None

        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "num_predict": max_tokens,
                },
                timeout=self.TIMEOUT * 3,  # Give LLM more time to respond
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except (requests.RequestException, ValueError, Exception):
            pass

        return None

    def enhance_response(
        self,
        rule_based_response: str,
        user_context: str,
        profile_summary: str,
    ) -> str:
        """
        Enhance rule-based response with LLM-generated content.

        If Ollama is available and can improve the response, returns enhanced version.
        Otherwise returns original rule-based response.

        Args:
            rule_based_response: Original response from rule engine
            user_context: User's last message/context
            profile_summary: Current profile summary

        Returns:
            Enhanced response (if LLM available) or original response
        """
        if not self.is_available():
            return rule_based_response

        system_prompt = (
            "You are a helpful financial planning assistant. "
            "Your role is to provide clear, actionable advice for retirement planning. "
            "Be conversational but professional. Keep responses concise (2-3 sentences max)."
        )

        prompt = (
            f"User context: {user_context}\n\n"
            f"Current profile: {profile_summary}\n\n"
            f"Base response to enhance: {rule_based_response}\n\n"
            f"Please provide a slightly enhanced/rephrased version that feels more "
            f"conversational while keeping the same key information."
        )

        enhanced = self.generate_response(
            prompt,
            system_prompt=system_prompt,
            max_tokens=300,
        )

        # Only use enhanced if it's reasonable length and doesn't look like an error
        if enhanced and len(enhanced) > 20 and len(enhanced) < 1000:
            return enhanced

        return rule_based_response

    def suggest_next_steps(
        self,
        profile_summary: str,
        completion_pct: int,
    ) -> Optional[str]:
        """
        Generate smart next-step suggestions using LLM.

        Args:
            profile_summary: Current profile summary
            completion_pct: Profile completion percentage (0-100)

        Returns:
            LLM-generated suggestion or None if unavailable
        """
        if not self.is_available():
            return None

        system_prompt = (
            "You are a financial planning advisor. Based on the profile provided, "
            "suggest the ONE most important next step the person should take. "
            "Be specific and actionable. Keep it to 1-2 sentences."
        )

        prompt = (
            f"Profile completion: {completion_pct}%\n\n"
            f"Profile summary:\n{profile_summary}\n\n"
            f"What should they focus on next?"
        )

        return self.generate_response(
            prompt,
            system_prompt=system_prompt,
            max_tokens=150,
        )

    def validate_response_quality(self, response: str) -> bool:
        """
        Quick validation that response looks reasonable.

        Args:
            response: Response text to validate

        Returns:
            True if response appears valid
        """
        if not response or not isinstance(response, str):
            return False

        # Check basic quality metrics
        if len(response.strip()) < 10:
            return False

        if len(response) > 5000:
            return False

        # Check for obvious errors/gibberish patterns
        if response.lower().startswith("error") or "traceback" in response.lower():
            return False

        return True
