"""
LLM service initialization.

Handles initialization of the centralized LLM service.
"""

from src.modules.core import Logger
from src.modules.llm import LLMService
from src.database import DatabaseManager


def initialize_llm_service(
    db_manager: DatabaseManager,
    logger: Logger
) -> LLMService:
    """Initialize centralized LLM service.

    Args:
        db_manager: Database manager for user config
        logger: Application logger

    Returns:
        LLMService instance
    """
    logger.info("Initializing LLM service...")

    llm_service = LLMService(
        db_manager=db_manager,
        default_timeout=30.0
    )

    logger.info("LLM service initialized")
    return llm_service
