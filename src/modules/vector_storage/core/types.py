"""
Shared types and interfaces for vector storage operations.
"""
from typing import List, Dict, Any, Optional, Tuple, Protocol
from dataclasses import dataclass


@dataclass
class MemorySearchRequest:
    """
    Request object for memory search operations.
    """
    query: str
    user_id: str
    project_id: str
    limit: int = 10
    where_filter: Optional[Dict[str, Any]] = None
    min_similarity: float = 0.0
    enable_temporal_decay: bool = False
    half_life_days: float = 30.0


@dataclass
class MemorySearchResult:
    """
    Result object for memory search operations.
    """
    id: str
    document: str
    metadata: Dict[str, Any]
    similarity_score: float


class VectorStorageComponent(Protocol):
    """
    Protocol defining the interface for vector storage components.
    """
    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> Tuple[str, List[float]]:
        ...

    async def search_similar_memories(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[Dict[str, Any]]:
        ...

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        ...

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> bool:
        ...

    async def count_memories(
        self,
        user_id: str,
        project_id: str
    ) -> int:
        ...

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        mental_note_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        ...

    async def search_mental_notes(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        session_id: Optional[str] = None,
        note_type: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        ...

    async def store_conversation_vector(
        self,
        conversation_db_id: int,
        conversation_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        session_id: Optional[str] = None,
        gemini_analysis: List[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[float]]]:
        ...

    async def search_similar_conversations(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        ...
