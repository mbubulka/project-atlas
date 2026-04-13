"""
Chat flow orchestration for AI-powered profile building.

Manages conversation state, parameter extraction, and model reruns.
Implements conversational interface with natural language input.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.ai_layer.ollama_client import OllamaClient
from src.ai_layer.orchestrator import NaturalLanguageParser
from src.ai_layer.profile_builder import ProfileBuilder
from src.data_models import TransitionProfile, create_empty_profile

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Single message in conversation."""

    role: str  # "user" or "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatState:
    """Complete conversation state."""

    profile: TransitionProfile = field(default_factory=create_empty_profile)
    messages: List[ChatMessage] = field(default_factory=list)
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    last_extraction: Optional[str] = None
    models_run: bool = False


class ChatFlowHandler:
    """
    Manages AI chat conversation flow.

    Responsibilities:
    1. Parse user input with NaturalLanguageParser
    2. Update profile with extracted parameters
    3. Run models when ready
    4. Generate helpful responses with next steps
    """

    def __init__(self, use_ollama: bool = True):
        """Initialize chat flow handler.

        Args:
            use_ollama: Enable optional Ollama integration (default: True)
        """
        self.parser = NaturalLanguageParser()
        self.state = ChatState()
        self.ollama_client = OllamaClient(enabled=use_ollama)

    def process_user_input(self, user_message: str) -> Dict[str, Any]:
        """
        Process user input message.

        Args:
            user_message: User's natural language input

        Returns:
            Dict with:
            - assistant_message: str (response to show user)
            - profile_updated: bool (was profile changed?)
            - models_run: bool (were models executed?)
            - status: completion status
            - profile_summary: formatted profile display

        Example:
            >>> handler = ChatFlowHandler()
            >>> result = handler.process_user_input(
            ...     "I'm moving to Denver with a $120K salary"
            ... )
            >>> print(result['assistant_message'])
            "Got it! Moving to Denver, expecting $120,000/year..."
        """
        # Add user message to history
        self.state.messages.append(ChatMessage(role="user", content=user_message))

        # Extract parameters from input
        extracted = self.parser.extract_parameters(user_message)
        self.state.last_extraction = json.dumps(extracted, indent=2)

        profile_updated = False
        models_run = False
        validation_msgs = []

        # Apply extracted parameters to profile
        if extracted:
            self.state.profile, validation_msgs = ProfileBuilder.apply_parameters(self.state.profile, extracted)
            self.state.extracted_params.update(extracted)
            profile_updated = True
            logger.info(f"Applied parameters: {list(extracted.keys())}")

        # Check if profile is ready for models
        status = ProfileBuilder.get_completion_status(self.state.profile)

        # Run models if we have all required fields and haven't already
        if status["is_ready"] and not self.state.models_run:
            try:
                self.state.profile = ProfileBuilder.run_models(self.state.profile)
                self.state.models_run = True
                models_run = True
                logger.info("Models executed successfully")
            except Exception as e:
                logger.error(f"Error running models: {e}")
                validation_msgs.append(f"Error running forecast: {str(e)}")

        # Generate response message
        assistant_message = self._generate_response(user_message, extracted, status, validation_msgs, models_run)

        # Try to enhance with Ollama if available
        profile_summary = ProfileBuilder.format_profile_summary(self.state.profile)
        enhanced = self.ollama_client.enhance_response(assistant_message, user_message, profile_summary)
        if enhanced != assistant_message:
            assistant_message = enhanced
            logger.info("Response enhanced with Ollama LLM")

        # Add assistant response to history
        self.state.messages.append(ChatMessage(role="assistant", content=assistant_message))

        return {
            "assistant_message": assistant_message,
            "profile_updated": profile_updated,
            "models_run": models_run,
            "status": status,
            "profile_summary": profile_summary,
            "validation_messages": validation_msgs,
        }

    def _generate_response(
        self,
        user_input: str,
        extracted: Dict[str, Any],
        status: Dict[str, Any],
        validation_msgs: List[str],
        models_run: bool,
    ) -> str:
        """Generate helpful assistant response."""
        parts = []

        # Acknowledgment
        if extracted:
            extracted_list = list(extracted.keys())
            if len(extracted_list) == 1:
                parts.append(f"Got it! I've noted your {extracted_list[0]}.")
            else:
                parts.append(f"Thanks! I've captured: {', '.join(extracted_list)}.")
        else:
            parts.append("I didn't catch any specific data from that message.")

        # Validation messages
        if validation_msgs:
            parts.append("\n".join([f"[WARNING] {msg}" for msg in validation_msgs]))

        # Models ran
        if models_run:
            parts.append(
                f"\n[OK] **Forecast ready!** Based on your profile:\n"
                f"- Monthly income: ${self.state.profile.monthly_take_home_pay:,.2f}\n"
                f"- Final buffer: ${self.state.profile.final_cash_buffer:,.2f}\n"
                f"- Verdict: **{self.state.profile.financial_verdict}**"
            )

        # Completion status with next steps
        if status["is_ready"] and not models_run:
            parts.append("[OK] Profile complete! Ready to generate forecast.")
        elif not status["is_ready"]:
            parts.append(f"\n[PROFILE] **Profile {status['completion_pct']}% complete**")
            if status["missing_required"]:
                parts.append(f"Still need: {', '.join(status['missing_required'])}")
            if status["missing_optional"] and status["missing_optional"]:
                parts.append(
                    f"Optional: {', '.join(status['missing_optional'][:3])} "
                    f"({len(status['missing_optional'])} available)"
                )

        # Suggested next steps
        parts.append("\n[INFO] **What's next?** You can ask:")
        if not status["is_ready"]:
            parts.append('- "What if I save for 9 months before looking for a job?"')
            parts.append('- "My salary will be $110K"')
        else:
            parts.append('- "What if I move to Austin instead?"')
            parts.append('- "My VA rating is 30%"')
            parts.append('- "Show me the month-by-month breakdown"')

        return "\n".join(parts)

    def reset(self) -> None:
        """Reset conversation state."""
        self.state = ChatState()
        logger.info("Chat state reset")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation as list for Streamlit."""
        return [{"role": msg.role, "content": msg.content} for msg in self.state.messages]

    def export_profile(self) -> Dict[str, Any]:
        """Export current profile as dict."""
        return {
            "target_city": self.state.profile.target_city,
            "estimated_annual_salary": self.state.profile.estimated_annual_salary,
            "job_search_timeline_months": self.state.profile.job_search_timeline_months,
            "current_savings": self.state.profile.current_savings,
            "rank": self.state.profile.rank,
            "years_of_service": self.state.profile.years_of_service,
            "current_va_disability_rating": self.state.profile.current_va_disability_rating,
            "healthcare_plan_choice": self.state.profile.healthcare_plan_choice,
            "annual_take_home_pay": self.state.profile.annual_take_home_pay,
            "final_cash_buffer": self.state.profile.final_cash_buffer,
            "financial_verdict": self.state.profile.financial_verdict,
        }
