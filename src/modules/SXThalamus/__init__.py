"""
SXThalamus Module - AI message preprocessing via centralized LLM service

This module provides semantic grouping and preparation of long AI messages
before chunking and storage, using the centralized LLM service.

Main Components:
    - SXThalamusService: Main service for processing messages
    - SXThalamusConfig: Configuration management
    - SXThalamusPromptBuilder: Prompt templates

Architecture:
    - service: Event-driven orchestrator
    - prompts: Prompt templates and builders
    - config: Configuration management
    - handlers: Event handling logic

Usage:
    from src.modules.SXThalamus import SXThalamusService, SXThalamusConfig
    from src.modules.llm import LLMService

    # Initialize service
    service = SXThalamusService(
        event_bus=event_bus,
        logger=logger,
        llm_service=llm_service,
        config=SXThalamusConfig.from_env()
    )
"""

from .service import SXThalamusService
from .config import SXThalamusConfig
from .prompts import SXThalamusPromptBuilder
from .handlers import ConversationHandler
from .utils import combine_conversation_messages

__all__ = [
    "SXThalamusService",
    "SXThalamusConfig",
    "SXThalamusPromptBuilder",
    "ConversationHandler",
    "combine_conversation_messages",
]

__version__ = "0.3.0"
