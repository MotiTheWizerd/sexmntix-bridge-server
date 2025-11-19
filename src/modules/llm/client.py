"""Gemini API Client - Low-level wrapper for Google Gemini API"""

import asyncio
from typing import Optional

from google import genai

from .exceptions import GeminiAPIError, GeminiTimeoutError, GeminiAuthError
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """
    Low-level client for Google Gemini API.

    Handles API authentication, request execution, and response parsing.
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        timeout_seconds: float = 30.0
    ):
        """
        Initialize Gemini API client.

        Args:
            model: Model identifier (default: gemini-2.0-flash)
            timeout_seconds: Request timeout in seconds (default: 30.0)

        Raises:
            GeminiAuthError: If client initialization fails
        """
        self.model = model
        self.timeout_seconds = timeout_seconds

        try:
            self.client = genai.Client()
        except Exception as e:
            raise GeminiAuthError(f"Failed to initialize Gemini client: {e}")

    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Generated text content

        Raises:
            GeminiAPIError: If API call fails
            GeminiTimeoutError: If request times out
        """
        try:
            # Call API with timeout
            response = await asyncio.wait_for(
                self._make_api_call(prompt),
                timeout=self.timeout_seconds
            )

            # Extract text from response
            return self._extract_text(response)

        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout_seconds)

        except GeminiAPIError:
            raise

        except Exception as e:
            raise GeminiAPIError(f"Gemini API call failed: {e}")

    async def _make_api_call(self, prompt: str):
        """
        Make the actual API call to Gemini.

        Args:
            prompt: The prompt to send

        Returns:
            Raw API response

        Raises:
            GeminiAPIError: If API call fails
        """
        try:
            async with self.client.aio as async_client:
                response = await async_client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response

        except Exception as e:
            raise GeminiAPIError(f"Failed to call Gemini API: {e}")

    def _extract_text(self, response) -> str:
        """
        Extract text content from Gemini API response.

        Args:
            response: Raw API response

        Returns:
            Extracted text content

        Raises:
            GeminiAPIError: If text extraction fails
        """
        try:
            # Try different response formats
            if hasattr(response, 'text'):
                return response.text

            elif hasattr(response, 'candidates') and response.candidates:
                # Handle candidates structure
                candidate = response.candidates[0]
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        # Extract from parts
                        parts = candidate.content.parts
                        if parts and hasattr(parts[0], 'text'):
                            return parts[0].text
                    return str(candidate.content)
                return str(candidate)

            # Fallback: convert to string
            return str(response)

        except Exception as e:
            raise GeminiAPIError(f"Failed to extract text from response: {e}")
