"""AI service for LLM-powered insights."""
import logging
from typing import Optional, Any

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIService:
    """Service for AI-powered insights using LLMs."""

    def __init__(self):
        """Initialize AI service with LLM client."""
        try:
            self.llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model_name=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )
            logger.info(f"AI Service initialized with model {settings.LLM_MODEL}")
        except Exception as exc:
            logger.error(f"Failed to initialize AI service: {exc}")
            raise AIServiceError(f"Failed to initialize LLM client: {exc}") from exc

    def analyze_event(
        self, event_message: str, metadata: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Analyze event and generate AI-powered insights.
        
        Args:
            event_message: The event message to analyze
            metadata: Optional metadata associated with the event
            
        Returns:
            Dictionary containing analysis results with keys:
            - analysis: Text analysis from LLM
            - confidence_score: Confidence between 0.0 and 1.0
            - recommendations: List of recommended actions
            
        Raises:
            AIServiceError: If analysis fails
        """
        if not event_message or not event_message.strip():
            logger.warning("Empty event message received")
            return self._default_response("Empty event message")

        try:
            prompt = self._build_analysis_prompt(event_message, metadata or {})
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            analysis_text = response.content

            return {
                "analysis": analysis_text,
                "confidence_score": 0.85,
                "recommendations": self._extract_recommendations(analysis_text),
            }
        except Exception as exc:
            logger.error(f"Error during event analysis: {exc}", exc_info=True)
            raise AIServiceError(f"Event analysis failed: {exc}") from exc

    def generate_performance_report(self, events_summary: dict[str, Any]) -> str:
        """Generate performance report from aggregated event data.
        
        Args:
            events_summary: Dictionary containing event statistics
            
        Returns:
            Generated report text
            
        Raises:
            AIServiceError: If report generation fails
        """
        if not events_summary:
            logger.warning("Empty events summary provided for report")
            return "No events available for report generation."

        try:
            prompt = f"""
            Generate a concise performance report based on these event statistics:
            
            Total Events: {events_summary.get('total_events', 0)}
            By Severity: {events_summary.get('by_severity', {})}
            By Type: {events_summary.get('by_type', {})}
            
            Provide:
            1. Summary of findings
            2. Critical issues (if any)
            3. Recommended actions
            """

            response = self.llm.invoke([HumanMessage(content=prompt)])
            report = response.content

            logger.info("Performance report generated successfully")
            return report
            
        except Exception as exc:
            logger.error(f"Error during report generation: {exc}", exc_info=True)
            raise AIServiceError(f"Report generation failed: {exc}") from exc

    @staticmethod
    def _build_analysis_prompt(message: str, metadata: dict[str, Any]) -> str:
        """Build the analysis prompt for the LLM.
        
        Args:
            message: Event message
            metadata: Event metadata
            
        Returns:
            Formatted prompt string
        """
        return f"""
        Analyze the following event and provide insights:
        
        Event: {message}
        Metadata: {metadata}
        
        Provide analysis in the following structure:
        - Severity Assessment (low/medium/high/critical)
        - Root Cause (if identifiable)
        - Recommended Actions (list)
        - Confidence Level (0.0-1.0)
        """

    @staticmethod
    def _extract_recommendations(text: str) -> list[str]:
        """Extract recommendations from analysis text.
        
        Args:
            text: Analysis text from LLM
            
        Returns:
            List of recommendations (max 5)
        """
        lines = text.split("\n")
        recommendations = [
            line.strip("- ").strip()
            for line in lines
            if line.strip().startswith("-") and len(line.strip()) > 2
        ]
        return recommendations[:5]

    @staticmethod
    def _default_response(reason: str) -> dict[str, Any]:
        """Generate default response when analysis cannot be performed.
        
        Args:
            reason: Reason for default response
            
        Returns:
            Default response dictionary
        """
        return {
            "analysis": f"Analysis not available: {reason}",
            "confidence_score": 0.0,
            "recommendations": [],
        }


# Global AI service instance
ai_service = AIService()

__all__ = ["AIService", "AIServiceError", "ai_service"]
