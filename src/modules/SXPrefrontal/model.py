from typing import Optional
from src.modules.qwen_sdk.client import QwenClient

class SXPrefrontalModel:
    """
    SXPrefrontal Model using Qwen SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Initialize the model with QwenClient.

        Auto-detects credentials from:
        1. Constructor parameters
        2. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
        3. Qwen CLI credentials (~/.qwen/oauth_creds.json)

        Args:
            api_key: Optional API key for authentication
            base_url: Optional API base URL
            model: Optional model name
            timeout: Request timeout in seconds (default: 60)
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
        """
        self.client = QwenClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=timeout,
            max_tokens=max_tokens,
            temperature=temperature
        )
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a response for the given prompt using Qwen.

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt to set context
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            The generated response.
        """
        return self.client.ask(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature
        )
