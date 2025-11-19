"""
SXThalamus service initialization.

Handles conditional initialization of the SXThalamus service.
"""

from typing import Optional
from src.modules.core import EventBus, Logger
from src.modules.SXThalamus import SXThalamusService, SXThalamusConfig
from src.modules.llm import LLMService


def initialize_sxthalamus(
    event_bus: EventBus,
    logger: Logger,
    llm_service: LLMService
) -> Optional[SXThalamusService]:
    """Initialize SXThalamus service if enabled.

    Args:
        event_bus: Application event bus
        logger: Application logger
        llm_service: Centralized LLM service

    Returns:
        SXThalamusService instance if enabled, None otherwise
    """
    config = SXThalamusConfig.from_env()

    if not config.enabled:
        logger.info("SXThalamus service disabled in configuration")
        return None

    try:
        logger.info("Initializing SXThalamus service...")

        sxthalamus_service = SXThalamusService(
            event_bus=event_bus,
            logger=logger,
            llm_service=llm_service,
            config=config
        )

        # Subscribe to conversation.stored event
        event_bus.subscribe(
            "conversation.stored",
            sxthalamus_service.handle_conversation_stored
        )

        logger.info("SXThalamus service initialized and subscribed to conversation.stored")
        return sxthalamus_service

    except Exception as e:
        logger.error(f"Failed to initialize SXThalamus: {e}", exc_info=True)
        return None
