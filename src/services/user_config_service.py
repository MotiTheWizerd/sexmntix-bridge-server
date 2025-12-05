"""
User Configuration Service

Fetches and caches user model preferences from the database.
"""

from typing import Optional, Dict, Any
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models.user import User
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class UserConfigService:
    """
    Service for fetching user-specific model configuration.
    
    Provides cached access to user model preferences stored in the database.
    """
    
    def __init__(self):
        """Initialize user config service with in-memory cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
    
    async def get_user_config(
        self, 
        user_id: str, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get user model configuration from database (with caching).
        
        Args:
            user_id: User identifier
            session: Database session
            
        Returns:
            Dictionary with user model preferences:
            {
                "foreground_model": "gpt-4",
                "background_workers": {...},
                "embedding_model": "models/text-embedding-004"
            }
        """
        # Check cache first
        if user_id in self._cache:
            self.logger.debug(f"User config cache hit for user {user_id}")
            return self._cache[user_id]
        
        # Fetch from database
        try:
            # Note: Ususer_id to string if it's an integer
            user_id_str = str(user_id)
            
            result = await session.execute(
                select(User).where(User.id == user_id_str)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                self.logger.warning(f"User {user_id} not found, using defaults")
                return self._get_default_config()
            
            config = {
                "background_workers": user.background_workers,
                "embedding_model": user.embedding_model
            }
            
            # Cache the config
            self._cache[user_id] = config
            self.logger.debug(f"Cached config for user {user_id}")
            
            return config
            
        except Exception as e:
            self.logger.error(
                f"Failed to fetch user config for {user_id}: {e}",
                exc_info=True
            )
            return self._get_default_config()
    
    def get_background_worker_config(
        self,
        user_config: Dict[str, Any],
        worker_type: str = "memory_synthesizer"
    ) -> Dict[str, str]:
        """
        Extract specific background worker configuration.
        
        Args:
            user_config: User configuration dictionary
            worker_type: Type of worker (e.g., "memory_synthesizer")
            
        Returns:
            Worker config dict with provider and model
        """
        workers = user_config.get("background_workers", {})
        worker_config = workers.get(worker_type, {})
        
        # Return with defaults if worker not configured
        return {
            "provider": worker_config.get("provider", "google"),
            "model": worker_config.get("model", "gemini-2.5-flash"),
            "enabled": worker_config.get("enabled", True)
        }

    def get_icm_config(
        self,
        user_config: Dict[str, Any],
        icm_type: str
    ) -> Dict[str, str]:
        """
        Extract configuration for a specific ICM component.

        Args:
            user_config: User configuration dictionary
            icm_type: Type of ICM (intent_icm, time_icm, world_view_icm)

        Returns:
            Dict with provider and model
        """
        icm_configs = user_config.get("icm_config", {})
        config = icm_configs.get(icm_type, {})
        
        # Defaults per type
        defaults = {
            "intent_icm": {"provider": "qwen", "model": None},
            "time_icm": {"provider": "qwen", "model": None},
            "world_view_icm": {"provider": "mistral", "model": "mistral-medium-2508"},
            "identity_icm": {"provider": "google", "model": "gemini-2.5-flash"}
        }
        
        default = defaults.get(icm_type, {"provider": "qwen", "model": None})
        
        return {
            "provider": config.get("provider", default["provider"]),
            "model": config.get("model", default["model"])
        }
    
    def invalidate_cache(self, user_id: str) -> None:
        """
        Invalidate cached config for a user.
        
        Call this when user updates their model preferences.
        
        Args:
            user_id: User identifier
        """
        if user_id in self._cache:
            del self._cache[user_id]
            self.logger.debug(f"Invalidated cache for user {user_id}")
    
    def clear_cache(self) -> None:
        """Clear entire config cache."""
        self._cache.clear()
        self.logger.info("Cleared all user config cache")
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        Get default configuration when user not found.
        
        Returns:
            Default config dictionary
        """
        return {
            "background_workers": {
                "conversation_analyzer": {
                    "provider": "google",
                    "model": "gemini-2.5-flash",
                    "enabled": True
                },
                "memory_synthesizer": {
                    "provider": "google",
                    "model": "gemini-2.5-flash",
                    "enabled": True
                }
            },
            "embedding_model": "models/text-embedding-004",
            "icm_config": {
                "intent_icm": {
                    "provider": "qwen",
                    "model": None
                },
                "time_icm": {
                    "provider": "qwen",
                    "model": None
                },
                "world_view_icm": {
                    "provider": "mistral",
                    "model": "mistral-medium-2508"
                }
            }
        }
