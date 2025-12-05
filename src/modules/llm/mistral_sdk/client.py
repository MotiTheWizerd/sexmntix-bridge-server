"""Mistral API Client - Wrapper for Mistral AI SDK"""

import os
from typing import Optional, Any
from mistralai import Mistral
from dotenv import load_dotenv

from ..exceptions import LLMError

load_dotenv()


class MistralClient:
    """
    Wrapper for Mistral AI API.
    """

    def __init__(
        self,
        model: str = "mistral-tiny",
        api_key: Optional[str] = None,
        timeout_seconds: float = 120.0
    ):
        """
        Initialize Mistral API client.

        Args:
            model: Model identifier (default: mistral-tiny)
            api_key: Optional API key (defaults to MISTRAL_API_KEY env var)
            timeout_seconds: Request timeout in seconds (default: 120.0)
        """
        self.model = model
        self.timeout_seconds = timeout_seconds
        
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise LLMError("MISTRAL_API_KEY not found in environment variables")

        try:
            self.client = Mistral(api_key=self.api_key)
        except Exception as e:
            raise LLMError(f"Failed to initialize Mistral client: {e}")

    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Mistral API.

        Args:
            prompt: The prompt to send to Mistral

        Returns:
            Generated text content

        Raises:
            LLMError: If API call fails
        """
        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            
            if response and response.choices:
                return response.choices[0].message.content
            return ""

        except Exception as e:
            raise LLMError(f"Mistral API call failed: {e}")
