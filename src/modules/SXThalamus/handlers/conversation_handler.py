"""Conversation event handler for SXThalamus"""

from typing import Dict, Any, Callable, Awaitable

from src.modules.core.telemetry.logger import Logger
from ..utils.message_utils import combine_conversation_messages


class ConversationHandler:
    """
    Handles conversation.stored events and orchestrates message processing.

    This handler extracts conversation data from events, combines messages,
    and delegates to the processing function.
    """

    def __init__(
        self,
        logger: Logger,
        process_message_func: Callable[[str], Awaitable[str]]
    ):
        """
        Initialize conversation handler.

        Args:
            logger: Logger instance for telemetry
            process_message_func: Async function to process combined message text
        """
        self.logger = logger
        self.process_message = process_message_func

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
            combined_text = combine_conversation_messages(conversation_messages)

            self.logger.info(
                f"📤 SENDING TO GEMINI - Conversation ID: {conversation_id}",
                extra={
                    "conversation_id": conversation_id,
                    "combined_length": len(combined_text),
                    "combined_text": combined_text  # Full text
                }
            )

            self.logger.info(f"📤 INPUT TEXT:\n{combined_text}\n{'='*80}")

            # Process through Gemini (delegated to service)
            processed_result = await self.process_message(combined_text)

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
                f"✅ CONVERSATION PROCESSED - ID: {conversation_id}",
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
