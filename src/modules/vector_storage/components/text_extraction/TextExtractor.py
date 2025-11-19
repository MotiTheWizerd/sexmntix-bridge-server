"""
Text extraction component for vector storage operations.
"""
from typing import Dict, Any
from src.modules.core import Logger


class TextExtractor:
    """
    Component responsible for extracting searchable text from data.
    """
    def __init__(self, logger: Logger):
        self.logger = logger

    def extract_with_fallback(
        self,
        memory_data: Dict[str, Any],
        memory_log_id: int
    ) -> str:
        """
        Extract searchable text from memory data with fallback mechanisms.

        Args:
            memory_data: Complete memory log data
            memory_log_id: Database ID of memory log

        Returns:
            Searchable text string
        """
        # Try different extraction methods in order of preference
        
        # 1. Try to get from Gemini-enhanced content first
        if "gemini_enhanced" in memory_data:
            enhanced_data = memory_data["gemini_enhanced"]
            parts = []
            
            # Topic (title/subject)
            if topic := enhanced_data.get("topic"):
                parts.append(topic + ".")
            
            # Summary (main content)
            if summary := enhanced_data.get("summary"):
                parts.append(summary)
            
            # Key points (as natural list)
            if key_points := enhanced_data.get("key_points"):
                if isinstance(key_points, list):
                    parts.append(" ".join(key_points))
            
            # Tags (semantic labels)
            if tags := enhanced_data.get("tags"):
                if isinstance(tags, list):
                    parts.append(f"Tags: {', '.join(tags)}.")
            
            # Related topics (connections)
            if related_topics := enhanced_data.get("related_topics"):
                if isinstance(related_topics, list):
                    parts.append(f"Related topics: {', '.join(related_topics)}.")
            
            # Reflection (meta-cognitive insight)
            if reflection := enhanced_data.get("reflection"):
                parts.append(f"Reflection: {reflection}")
            
            text = " ".join(parts)
            if text.strip():
                return text

        # 2. Try to get from raw content
        if "raw_content" in memory_data:
            raw_content = memory_data["raw_content"]
            if isinstance(raw_content, str) and raw_content.strip():
                return raw_content
        
        # 3. Try to get from content field
        if "content" in memory_data:
            content = memory_data["content"]
            if isinstance(content, str) and content.strip():
                return content
        
        # 4. Try to get from conversation data
        if "conversation_data" in memory_data:
            conversation = memory_data["conversation_data"]
            if isinstance(conversation, str):
                return conversation
            elif isinstance(conversation, dict):
                # Extract relevant parts from conversation dict
                parts = []
                if "title" in conversation:
                    parts.append(conversation["title"])
                if "summary" in conversation:
                    parts.append(conversation["summary"])
                if "messages" in conversation:
                    # Join message contents
                    if isinstance(conversation["messages"], list):
                        message_texts = []
                        for msg in conversation["messages"]:
                            if isinstance(msg, dict) and "content" in msg:
                                message_texts.append(str(msg["content"]))
                        if message_texts:
                            parts.append(" ".join(message_texts))
                if parts:
                    return " ".join(parts)
        
        # If we get here, no suitable text was found
        self.logger.warning(
            f"No searchable text found for memory log {memory_log_id}. "
            f"Available keys: {list(memory_data.keys()) if isinstance(memory_data, dict) else type(memory_data)}"
        )
        
        # Return an empty string - the calling function should handle this case
        return ""