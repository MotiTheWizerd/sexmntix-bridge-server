"""
Quick fix script to add embedding generation to store_memory tool
"""

# Read the file
with open("src/modules/xcp_server/tools/store_memory/tool.py", "r") as f:
    content = f.read()

# Add imports
old_imports = """from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.memory_log_repository import MemoryLogRepository"""

new_imports = """from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.embeddings.providers.google import GoogleEmbeddingProvider
from src.modules.embeddings.models import ProviderConfig
from src.modules.embeddings.caching import EmbeddingCache
from src.modules.embeddings import EmbeddingService"""

content = content.replace(old_imports, new_imports)

# Add embedding service initialization in __init__
old_init = """        super().__init__(event_bus, logger)
        self.db_session_factory = db_session_factory

        # Initialize components
        self.config = StoreMemoryConfig()
        self.validator = MemoryArgumentValidator()
        self.builder = MemoryDataBuilder()
        self.formatter = MemoryResultFormatter()"""

new_init = """        super().__init__(event_bus, logger)
        self.db_session_factory = db_session_factory

        # Initialize embedding service
        embedding_config = ProviderConfig(
            provider_name="google",
            model_name="models/gemini-embedding-001",
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            timeout_seconds=30.0,
            max_retries=3
        )
        provider = GoogleEmbeddingProvider(embedding_config)
        cache = EmbeddingCache()
        self.embedding_service = EmbeddingService(
            event_bus=event_bus,
            logger=logger,
            provider=provider,
            cache=cache,
            cache_enabled=True
        )

        # Initialize components
        self.config = StoreMemoryConfig()
        self.validator = MemoryArgumentValidator()
        self.builder = MemoryDataBuilder()
        self.formatter = MemoryResultFormatter()"""

content = content.replace(old_init, new_init)

# Update _store_in_database method
old_store = """    async def _store_in_database(
        self,
        validated_args: Dict[str, Any],
        raw_data: Dict[str, Any]
    ):
        \"\"\"Store memory in database

        Args:
            validated_args: Validated arguments
            raw_data: Built raw_data structure

        Returns:
            MemoryLog: Stored memory log object
        \"\"\"
        async with self.db_session_factory() as db_session:
            repo = MemoryLogRepository(db_session)

            memory_log = await repo.create(
                task=validated_args["task"],
                agent=validated_args["agent"],
                date=datetime.utcnow(),
                raw_data=raw_data,
                user_id=validated_args["user_id"],
                project_id=validated_args["project_id"]
            )

            self.logger.info(f"Memory log stored with id: {memory_log.id}")

            return memory_log"""

new_store = """    async def _store_in_database(
        self,
        validated_args: Dict[str, Any],
        raw_data: Dict[str, Any]
    ):
        \"\"\"Store memory in database with embedding

        Args:
            validated_args: Validated arguments
            raw_data: Built raw_data structure

        Returns:
            MemoryLog: Stored memory log object
        \"\"\"
        # Generate embedding from content
        content = validated_args["content"]
        embedding_result = await self.embedding_service.generate_embedding(content)
        embedding_vector = embedding_result.embedding

        self.logger.info(f"Generated embedding for memory log - length: {len(embedding_vector) if embedding_vector else 'None'}")

        async with self.db_session_factory() as db_session:
            repo = MemoryLogRepository(db_session)

            memory_log = await repo.create(
                task=validated_args["task"],
                agent=validated_args["agent"],
                date=datetime.utcnow(),
                raw_data=raw_data,
                user_id=validated_args["user_id"],
                project_id=validated_args["project_id"],
                embedding=embedding_vector
            )

            self.logger.info(f"Memory log stored with id: {memory_log.id}, embedding: {memory_log.embedding is not None}")

            return memory_log"""

content = content.replace(old_store, new_store)

# Write back
with open("src/modules/xcp_server/tools/store_memory/tool.py", "w") as f:
    f.write(content)

print("Fixed store_memory tool!")
