"""
Event data validation for internal handlers.

Provides validation and extraction utilities for event data
in memory log and mental note storage handlers.
"""

from typing import Dict, Any, Optional
from .config import InternalHandlerConfig


class EventDataValidator:
    """Validates and extracts data from storage events"""

    @staticmethod
    def validate_user_project(user_id: Any, project_id: Any) -> bool:
        """
        Check if user_id and project_id are present.

        Args:
            user_id: User identifier from event
            project_id: Project identifier from event

        Returns:
            True if both are truthy, False otherwise
        """
        return bool(user_id and project_id)

    @staticmethod
    def extract_memory_log_data(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate memory log event data.

        Args:
            event_data: Raw event payload

        Returns:
            Dict with validated fields, or None if validation fails
        """
        user_id = event_data.get(InternalHandlerConfig.USER_ID_FIELD)
        project_id = event_data.get(InternalHandlerConfig.PROJECT_ID_FIELD)
        memory_log_id = event_data.get(InternalHandlerConfig.MEMORY_LOG_ID_FIELD)

        if not EventDataValidator.validate_user_project(user_id, project_id):
            return None

        if not memory_log_id:
            return None

        return {
            "user_id": user_id,
            "project_id": project_id,
            "memory_log_id": memory_log_id,
            "raw_data": event_data.get(InternalHandlerConfig.RAW_DATA_FIELD, {})
        }

    @staticmethod
    def extract_mental_note_data(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate mental note event data.

        Args:
            event_data: Raw event payload

        Returns:
            Dict with validated fields, or None if validation fails
        """
        user_id = event_data.get(InternalHandlerConfig.USER_ID_FIELD)
        project_id = event_data.get(InternalHandlerConfig.PROJECT_ID_FIELD)
        mental_note_id = event_data.get(InternalHandlerConfig.MENTAL_NOTE_ID_FIELD)

        if not EventDataValidator.validate_user_project(user_id, project_id):
            return None

        if not mental_note_id:
            return None

        return {
            "user_id": user_id,
            "project_id": project_id,
            "mental_note_id": mental_note_id,
            "raw_data": event_data.get(InternalHandlerConfig.RAW_DATA_FIELD, {})
        }

    @staticmethod
    def extract_content_preview(
        raw_data: Dict[str, Any],
        length: int = InternalHandlerConfig.CONTENT_PREVIEW_LENGTH
    ) -> str:
        """
        Extract content preview for logging.

        Args:
            raw_data: Raw data dictionary containing content
            length: Maximum length of preview

        Returns:
            Content preview string or placeholder
        """
        content = raw_data.get(InternalHandlerConfig.CONTENT_FIELD, "")
        if content:
            return content[:length]
        return InternalHandlerConfig.NO_CONTENT_PLACEHOLDER

    @staticmethod
    def get_content_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed content information for debugging.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Dict with content metadata (exists, type, length)
        """
        content = raw_data.get(InternalHandlerConfig.CONTENT_FIELD, "")
        return {
            "exists": bool(content),
            "type": type(content).__name__,
            "length": len(content) if content else 0
        }
