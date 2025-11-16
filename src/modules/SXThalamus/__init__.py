"""
SXThalamus Module - AI message preprocessing via Google Gemini API

This module provides semantic grouping and preparation of long AI messages
before chunking and storage, using Google Gemini API.

Main Components:
    - SXThalamusService: Main service for processing messages
    - SXThalamusConfig: Configuration management
    - GeminiClient: Low-level Gemini API wrapper
    - SXThalamusPromptBuilder: Prompt templates
    - Custom exceptions for error handling

Architecture:
    - service: Event-driven orchestrator
    - gemini/client: Low-level Gemini API wrapper
    - prompts: Prompt templates and builders
    - config: Configuration management
    - exceptions: Custom exception hierarchy

Usage:
    from src.modules.SXThalamus import SXThalamusService, SXThalamusConfig

    # Initialize service
    service = SXThalamusService(
        event_bus=event_bus,
        logger=logger,
        config=SXThalamusConfig.from_env()
    )

    # Process a message
    processed = await service.process_message(
        message="Long AI response...",
        prompt="Custom grouping prompt"  # optional
    )
"""

from .service import SXThalamusService
from .config import SXThalamusConfig
from .gemini import GeminiClient
from .prompts import SXThalamusPromptBuilder
from .handlers import ConversationHandler
from .utils import combine_conversation_messages
from .exceptions import (
    SXThalamusError,
    GeminiAPIError,
    GeminiTimeoutError,
    GeminiAuthError,
    GeminiRateLimitError
)

__all__ = [
    "SXThalamusService",
    "SXThalamusConfig",
    "GeminiClient",
    "SXThalamusPromptBuilder",
    "ConversationHandler",
    "combine_conversation_messages",
    "SXThalamusError",
    "GeminiAPIError",
    "GeminiTimeoutError",
    "GeminiAuthError",
    "GeminiRateLimitError",
]

__version__ = "0.2.0"
