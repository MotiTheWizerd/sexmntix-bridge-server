"""
BasicAgent Module

Event-driven agent for semantic conversation processing using Google Gemini API.

Architecture:
- service: Event-driven orchestrator
- client: Low-level Gemini API wrapper
- prompts: Prompt templates and builders
- config: Configuration management
- exceptions: Custom exception hierarchy
"""

from src.ai_agents.basic_agent.service import BasicAgentService
from src.ai_agents.basic_agent.client import GeminiClient
from src.ai_agents.basic_agent.prompts import PromptBuilder
from src.ai_agents.basic_agent.config import BasicAgentConfig
from src.ai_agents.basic_agent.exceptions import (
    BasicAgentError,
    GeminiAPIError,
    GeminiTimeoutError,
    GeminiAuthError,
    GeminiRateLimitError
)

__all__ = [
    "BasicAgentService",
    "GeminiClient",
    "PromptBuilder",
    "BasicAgentConfig",
    "BasicAgentError",
    "GeminiAPIError",
    "GeminiTimeoutError",
    "GeminiAuthError",
    "GeminiRateLimitError"
]
