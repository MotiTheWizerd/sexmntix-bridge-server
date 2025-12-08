from typing import Optional
from typing import Optional, Union
from src.modules.qwen_sdk.client import QwenClient
from src.modules.llm.mistral_sdk.client import MistralClient
from src.modules.llm.client import GeminiClient

class SXPrefrontalModel:
    """
    SXPrefrontal Model using Qwen SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "gemini",
        timeout: int = 60,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Initialize the model with a specific provider.

        Args:
            api_key: Optional API key for authentication
            base_url: Optional API base URL
            model: Optional model name
            provider: Provider name (qwen, mistral, gemini)
            timeout: Request timeout in seconds (default: 60)
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
        """
        self.provider = provider
        self.model_name = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.api_key = api_key
        self.base_url = base_url

        self.client: Union[QwenClient, MistralClient, GeminiClient]
        
        if provider == "gemini":
            self.client = GeminiClient(
                model=model or "gemini-2.5-flash",
                timeout_seconds=float(timeout)
            )
        elif provider == "mistral":
            self.client = MistralClient(
                model=model or "mistral-medium-2508",
                api_key=api_key,
                timeout_seconds=float(timeout)
            )
        else:
            # Default to Qwen
            self.client = QwenClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
                max_tokens=max_tokens,
                temperature=temperature
            )

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
        if self.provider == "qwen":
            return self.client.ask(
                prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature
            )
        elif self.provider == "mistral":
            # MistralClient.generate_content is async, need to handle in sync context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            import asyncio
            try:
                # Try to get existing event loop
                loop = asyncio.get_running_loop()
                # If we're here, loop is running - can't use asyncio.run()
                # Create a new loop in a thread instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.client.generate_content(full_prompt))
                    return future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run()
                return asyncio.run(self.client.generate_content(full_prompt))
                
        elif self.provider == "gemini":
            # GeminiClient is also async
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.client.generate_content(full_prompt))
                    return future.result()
            except RuntimeError:
                return asyncio.run(self.client.generate_content(full_prompt))
        
        return ""
