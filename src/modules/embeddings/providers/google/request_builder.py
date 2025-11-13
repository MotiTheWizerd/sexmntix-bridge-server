"""
Google Request Builder

Single Responsibility: Construct API request payloads for Google embedding API.

This component knows how to format text into the proper request structure
required by Google's Generative AI API.
"""

from typing import Dict, Any


class GoogleRequestBuilder:
    """
    Builds request payloads for Google Generative AI embedding API.

    Handles the specific payload format required by Google's API.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, model_name: str = "models/text-embedding-004"):
        """
        Initialize request builder.

        Args:
            model_name: Google embedding model name
        """
        self.model_name = model_name

    def build_embedding_url(self) -> str:
        """
        Build the full URL for embedding requests.

        Returns:
            Complete API endpoint URL
        """
        return f"{self.BASE_URL}/{self.model_name}:embedContent"

    def build_embedding_payload(self, text: str) -> Dict[str, Any]:
        """
        Build request payload for single text embedding.

        Args:
            text: Text to embed

        Returns:
            Request payload dict formatted for Google API
        """
        return {
            "model": self.model_name,
            "content": {
                "parts": [{"text": text}]
            }
        }
