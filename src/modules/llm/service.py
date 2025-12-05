"""
LLM Service - Centralized language model management

Handles user-specific model configuration and client caching.
"""

from typing import Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.core.telemetry.logger import get_logger
from src.services.user_config_service import UserConfigService
from src.database import DatabaseManager

from .client import GeminiClient
from .mistral_sdk.client import MistralClient

logger = get_logger(__name__)


class LLMService:
    """
    Centralized service for LLM operations.
    
    Manages user-specific model configuration and client caching.
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        default_timeout: float = 120.0
    ):
        """
        Initialize LLM service.
        
        Args:
            db_manager: Database manager for user config access
            default_timeout: Default timeout for API calls
        """
        self.db_manager = db_manager
        self.default_timeout = default_timeout
        self.user_config_service = UserConfigService()
        
        # Cache for user-specific clients
        self._client_cache: Dict[str, Union[GeminiClient, MistralClient]] = {}
        
        self.logger = logger
        self.logger.info("LLMService initialized")
    
    async def get_client(
        self,
        user_id: str,
        worker_type: str = "conversation_analyzer"
    ) -> Union[GeminiClient, MistralClient]:
        """
        Get or create Gemini client for specific user and worker.
        
        Args:
            user_id: User identifier
            worker_type: Type of worker (conversation_analyzer, memory_synthesizer)
            
        Returns:
            GeminiClient configured with user's preferred model
        """
        cache_key = f"{user_id}:{worker_type}"
        
        # Check cache
        if cache_key in self._client_cache:
            self.logger.debug(f"LLM client cache hit: {cache_key}")
            return self._client_cache[cache_key]
        
        # Fetch user config
        async with self.db_manager.session_factory() as session:
            user_config = await self.user_config_service.get_user_config(user_id, session)
            
            # Get worker-specific config
            worker_config = self.user_config_service.get_background_worker_config(
                user_config,
                worker_type=worker_type
            )
            
            model = worker_config["model"]
            
            self.logger.info(
                f"Creating LLM client for user {user_id}, worker {worker_type}, model: {model}"
            )
            
            # Create and cache client
            if model.startswith("mistral"):
                self.logger.info(
                    f"Creating Mistral LLM client for user {user_id}, worker {worker_type}, model: {model}"
                )
                client = MistralClient(
                    model=model,
                    timeout_seconds=self.default_timeout
                )
            else:
                self.logger.info(
                    f"Creating Gemini LLM client for user {user_id}, worker {worker_type}, model: {model}"
                )
                client = GeminiClient(
                    model=model,
                    timeout_seconds=self.default_timeout
                )
            
            self._client_cache[cache_key] = client
            
            return client
    
    async def generate_content(
        self,
        prompt: str,
        user_id: str,
        worker_type: str = "conversation_analyzer"
    ) -> str:
        """
        Generate content using user-specific model configuration.
        
        Args:
            prompt: The prompt to send to LLM
            user_id: User identifier
            worker_type: Type of worker requesting generation
            
        Returns:
            Generated text content
        """
        client = await self.get_client(user_id, worker_type)
        return await client.generate_content(prompt)
    
    def invalidate_cache(self, user_id: str) -> None:
        """
        Invalidate cached clients for a user.
        
        Call this when user updates their model preferences.
        
        Args:
            user_id: User identifier
        """
        keys_to_remove = [k for k in self._client_cache.keys() if k.startswith(f"{user_id}:")]
        
        for key in keys_to_remove:
            del self._client_cache[key]
            self.logger.debug(f"Invalidated LLM client cache: {key}")
    
    def clear_cache(self) -> None:
        """Clear entire client cache."""
        self._client_cache.clear()
        self.logger.info("Cleared all LLM client cache")
