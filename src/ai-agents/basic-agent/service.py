"""BasicAgent Service - Event-driven orchestrator for semantic chunking"""

from typing import Optional, Dict, Any

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger

from .config import BasicAgentConfig
from .client import GeminiClient
from .prompts import PromptBuilder
from .exceptions import GeminiAPIError, GeminiTimeoutError


class BasicAgentService:
    """
    Event-driven service for processing conversations with Google Gemini API.

    This service orchestrates conversation processing by:
    - Listening to conversation.stored events
    - Delegating API calls to GeminiClient
    - Using PromptBuilder for prompt formatting
    - Logging results and errors

    Architecture:
    - Service: Orchestration and event handling
    - Client: Low-level API communication
    - PromptBuilder: Prompt formatting
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        config: Optional[BasicAgentConfig] = None
    ):
        """
        Initialize BasicAgent service.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance for telemetry
            config: Optional configuration (loads from env if None)
        """
        self.event_bus = event_bus
        self.logger = logger
        self.config = config or BasicAgentConfig.from_env()

        # Initialize Gemini client (API key loaded from environment)
        self.client = GeminiClient(
            model=self.config.model,
            timeout_seconds=self.config.timeout_seconds
        )

        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()

        self.logger.info(
            "BasicAgentService initialized",
            extra={
                "enabled": self.config.enabled,
                "model": self.config.model,
                "timeout": self.config.timeout_seconds
            }
        )

    async def process_conversation(
        self,
        conversation_text: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Process a conversation through Gemini API for semantic chunking.

        Args:
            conversation_text: The conversation text to process
            custom_prompt: Optional custom prompt (defaults to semantic chunking prompt)

        Returns:
            Gemini's response with semantic chunks

        Raises:
            GeminiAPIError: If API call fails
            GeminiTimeoutError: If API call times out
        """
        if not self.config.enabled:
            self.logger.debug("BasicAgent disabled, returning original conversation")
            return conversation_text

        # Build the prompt
        if not custom_prompt:
            custom_prompt = self.prompt_builder.build_semantic_chunking_prompt(
                conversation_text
            )

        self.logger.info(
            "Processing conversation through Gemini",
            extra={
                "conversation_length": len(conversation_text),
                "prompt_length": len(custom_prompt)
            }
        )

        try:
            # Call Gemini API via client
            result = await self.client.generate_content(custom_prompt)

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
                f"Unexpected error during conversation processing: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise

    async def handle_conversation_stored(self, event_data: Dict[str, Any]):
        """
        Event handler for conversation.stored events.

        Processes conversations through Gemini for semantic chunking.

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

            self.logger.info(
                f"📤 SENDING TO GEMINI (BasicAgent) - Conversation ID: {conversation_id}",
                extra={
                    "conversation_id": conversation_id,
                    "combined_length": len(combined_text),
                    "combined_text": combined_text  # Full text
                }
            )

            self.logger.info(f"📤 INPUT TEXT:\n{combined_text}\n{'='*80}")

            # Process through Gemini
            processed_result = await self.process_conversation(combined_text)

            self.logger.info(
                "Conversation processed through Gemini successfully",
                extra={
                    "conversation_id": conversation_id,
                    "result_length": len(processed_result)
                }
            )

            # TODO: Integration with storage will be added later
            # For now, log the full result
            self.logger.info(
                f"✅ CONVERSATION PROCESSED (BasicAgent) - ID: {conversation_id}",
                extra={
                    "conversation_id": conversation_id,
                    "result_length": len(processed_result),
                    "result_full": processed_result  # Full result in extra
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
        self.logger.info("BasicAgentService shutting down")
