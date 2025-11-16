"""SXThalamus Service - Event-driven orchestrator for semantic message preprocessing"""

from typing import Optional, Dict, Any

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger

from .config import SXThalamusConfig
from .exceptions import GeminiAPIError, GeminiTimeoutError
from .gemini import GeminiClient
from .prompts import SXThalamusPromptBuilder


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
                extra={"result_length": len(result)}
            )

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

    async def handle_conversation_stored(self, event_data: Dict[str, Any]):
        """
        Event handler for conversation.stored events.

        Processes conversations through Gemini for semantic grouping.

        Args:
            event_data: Event data containing conversation details
                - conversation_db_id: PostgreSQL ID
                - conversation_id: UUID
                - model: AI model name
                - raw_data: Full conversation with messages
                - user_id: User identifier
                - project_id: Project identifier
        """
        try:
            # Extract conversation data
            conversation_id = event_data.get("conversation_id")
            raw_data = event_data.get("raw_data", {})
            conversation_messages = raw_data.get("conversation", [])

            self.logger.info(
                "Received conversation.stored event",
                extra={
                    "conversation_id": conversation_id,
                    "message_count": len(conversation_messages)
                }
            )

            if not conversation_messages:
                self.logger.warning(
                    "No messages in conversation, skipping processing",
                    extra={"conversation_id": conversation_id}
                )
                return

            # Combine all messages into a single text
            combined_text = self._combine_conversation_messages(conversation_messages)

            self.logger.debug(
                "Combined conversation text",
                extra={
                    "conversation_id": conversation_id,
                    "combined_length": len(combined_text)
                }
            )

            # Process through Gemini
            processed_result = await self.process_message(combined_text)

            self.logger.info(
                "Conversation processed through Gemini successfully",
                extra={
                    "conversation_id": conversation_id,
                    "result_length": len(processed_result)
                }
            )

            # TODO: Integration with storage will be added later
            # For now, just log the result
            self.logger.debug(
                "Gemini processing result",
                extra={
                    "conversation_id": conversation_id,
                    "processed_snippet": processed_result[:200]
                }
            )

        except Exception as e:
            self.logger.error(
                f"Error handling conversation.stored event: {e}",
                extra={
                    "conversation_id": event_data.get("conversation_id"),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            # Don't re-raise - we don't want to break the event bus

    def _combine_conversation_messages(self, messages: list) -> str:
        """
        Combine conversation messages into a single text string.

        Args:
            messages: List of message dicts with 'role' and 'text' fields

        Returns:
            Combined text with role prefixes
        """
        combined = []
        for msg in messages:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")
            combined.append(f"{role}: {text}")

        return "\n\n".join(combined)

    async def close(self):
        """
        Cleanup resources.

        Called during application shutdown.
        """
        self.logger.info("SXThalamusService shutting down")
