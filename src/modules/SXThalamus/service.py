"""SXThalamus Service - Event-driven orchestrator for semantic message preprocessing"""

from typing import Optional

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger

from .config import SXThalamusConfig
from .exceptions import GeminiAPIError, GeminiTimeoutError
from .gemini import GeminiClient
from .prompts import SXThalamusPromptBuilder
from .handlers import ConversationHandler


class SXThalamusService:
    """
    Service for preprocessing AI messages using Google Gemini API.

    This service processes AI conversations through Gemini to semantically group and prepare
    long messages for better chunking and storage.

    Features:
    - Direct Gemini API integration
    - Semantic message grouping
    - Event-driven architecture
    - Comprehensive error handling and logging

    Architecture:
    - Service: Orchestration and event handling
    - Client: Low-level Gemini API communication
    - PromptBuilder: Prompt formatting and templates
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        config: Optional[SXThalamusConfig] = None
    ):
        """
        Initialize SXThalamus service.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance for telemetry
            config: Optional configuration (loads from env if None)
        """
        self.event_bus = event_bus
        self.logger = logger
        self.config = config or SXThalamusConfig.from_env()

        # Initialize Gemini client (API key loaded from environment)
        self.client = GeminiClient(
            model=self.config.model,
            timeout_seconds=self.config.timeout_seconds
        )

        # Initialize prompt builder
        self.prompt_builder = SXThalamusPromptBuilder()

        # Initialize conversation handler (delegates event handling)
        self.conversation_handler = ConversationHandler(
            logger=self.logger,
            process_message_func=self.process_message
        )

        self.logger.info(
            "SXThalamusService initialized",
            extra={
                "enabled": self.config.enabled,
                "model": self.config.model,
                "timeout": self.config.timeout_seconds
            }
        )

    async def process_message(
        self,
        message: str,
        prompt: Optional[str] = None
    ) -> str:
        """
        Process a message through Gemini API for semantic grouping.

        This method sends the message to Gemini for intelligent preprocessing
        that prepares it for better chunking.

        Args:
            message: The AI message to process
            prompt: Optional custom prompt (defaults to grouping prompt)

        Returns:
            Processed message response from Gemini

        Raises:
            GeminiAPIError: If Gemini API call fails
            GeminiTimeoutError: If API call times out
        """
        if not self.config.enabled:
            self.logger.debug("SXThalamus disabled, returning original message")
            return message

        # Build the prompt
        if not prompt:
            prompt = self.prompt_builder.build_semantic_grouping_prompt(message)

        self.logger.info(
            "Processing message through Gemini",
            extra={
                "message_length": len(message),
                "prompt_length": len(prompt)
            }
        )

        try:
            # Call Gemini API via client
            result = await self.client.generate_content(prompt)

            self.logger.info(
                "Gemini processing completed successfully",
                extra={
                    "result_length": len(result),
                    "result_preview": result[:500]  # First 500 chars
                }
            )

            # Log full result for debugging
            self.logger.info(f"📝 GEMINI RESPONSE:\n{result}\n{'='*80}")

            return result

        except (GeminiAPIError, GeminiTimeoutError) as e:
            self.logger.error(
                f"Gemini processing failed: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise

        except Exception as e:
            self.logger.error(
                f"Unexpected error during message processing: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise

    async def handle_conversation_stored(self, event_data):
        """
        Event handler for conversation.stored events.

        Delegates to ConversationHandler for processing.

        Args:
            event_data: Event data containing conversation details
        """
        await self.conversation_handler.handle_conversation_stored(event_data)

    async def close(self):
        """
        Cleanup resources.

        Called during application shutdown.
        """
        self.logger.info("SXThalamusService shutting down")
