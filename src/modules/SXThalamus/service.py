"""SXThalamus Service - Event-driven orchestrator for semantic message preprocessing"""

from typing import Optional

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger
from src.modules.llm import LLMService

from .config import SXThalamusConfig
from .prompts import SXThalamusPromptBuilder
from .handlers import ConversationHandler


class SXThalamusService:
    """
    Service for preprocessing AI messages using Google Gemini API.

    This service processes AI conversations through Gemini to semantically group and prepare
    long messages for better chunking and storage.

    Features:
    - Direct Gemini API integration via centralized LLM service
    - Semantic message grouping
    - Event-driven architecture
    - Comprehensive error handling and logging

    Architecture:
    - Service: Orchestration and event handling
    - LLMService: Centralized LLM client management
    - PromptBuilder: Prompt formatting and templates
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        llm_service: LLMService,
        config: Optional[SXThalamusConfig] = None
    ):
        """
        Initialize SXThalamus service.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance for telemetry
            llm_service: Centralized LLM service
            config: Optional configuration (loads from env if None)
        """
        self.event_bus = event_bus
        self.logger = logger
        self.llm_service = llm_service
        self.config = config or SXThalamusConfig.from_env()

        # Initialize prompt builder
        self.prompt_builder = SXThalamusPromptBuilder()

        # Initialize conversation handler (delegates event handling)
        self.conversation_handler = ConversationHandler(
            logger=self.logger,
            process_message_func=self.process_message_with_context,
            event_bus=self.event_bus
        )

        self.logger.info(
            "SXThalamusService initialized",
            extra={
                "enabled": self.config.enabled,
                "timeout": self.config.timeout_seconds
            }
        )
    
    async def process_message_with_context(
        self,
        message: str,
        user_id: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Process a message through Gemini API with user context.
        
        This method uses the centralized LLM service to fetch user-specific
        model configuration and process the message.

        Args:
            message: The AI message to process
            user_id: User identifier for fetching model config
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
                "user_id": user_id,
                "message_length": len(message),
                "prompt_length": len(prompt)
            }
        )

        try:
            # Use centralized LLM service
            result = await self.llm_service.generate_content(
                prompt=prompt,
                user_id=user_id,
                worker_type="conversation_analyzer"
            )

            self.logger.info(
                "Gemini processing completed successfully",
                extra={
                    "user_id": user_id,
                    "result_length": len(result),
                    "result_preview": result[:500]  # First 500 chars
                }
            )

            # Log full result for debugging
            self.logger.info(f"📝 GEMINI RESPONSE:\n{result}\n{'='*80}")

            return result

        except Exception as e:
            self.logger.error(
                f"Gemini processing failed: {e}",
                extra={"error_type": type(e).__name__, "user_id": user_id},
                exc_info=True
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
