"""
Pydantic schemas for ChromaDB Viewer endpoints.

Response models for browsing, searching, and inspecting ChromaDB collections.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CollectionDetailResponse(BaseModel):
    """Detailed information about a single ChromaDB collection"""
    name: str = Field(..., description="Collection name")
    vector_count: int = Field(..., description="Total number of vectors in collection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")
    user_id: Optional[str] = Field(None, description="User ID if user-scoped")
    project_id: Optional[str] = Field(None, description="Project ID if project-scoped")
    document_type: Optional[str] = Field(None, description="Type of documents (memory_log, mental_note, conversation)")


class DocumentResponse(BaseModel):
    """Single document from ChromaDB collection"""
    id: str = Field(..., description="Document unique identifier")
    document: Dict[str, Any] = Field(..., description="Full document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (optional, can be large)")
    distance: Optional[float] = Field(None, description="Distance from query (if search result)")
    similarity: Optional[float] = Field(None, description="Similarity score (if search result)")


class DocumentListResponse(BaseModel):
    """Paginated list of documents from a collection"""
    collection_name: str = Field(..., description="Collection name")
    total_count: int = Field(..., description="Total documents in collection")
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    offset: int = Field(0, description="Pagination offset")
    limit: int = Field(10, description="Pagination limit")
    has_more: bool = Field(..., description="Whether more documents available")


class CollectionSearchRequest(BaseModel):
    """Request for searching within a specific collection"""
    query: str = Field(..., description="Search query text", min_length=1)
    limit: int = Field(10, description="Maximum results to return", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters (ChromaDB where syntax)")
    include_embeddings: bool = Field(False, description="Include vector embeddings in response")
    min_similarity: float = Field(0.0, description="Minimum similarity threshold (0.0-1.0)", ge=0.0, le=1.0)


class CollectionQueryRequest(BaseModel):
    """Advanced query across multiple collections"""
    query: str = Field(..., description="Search query text", min_length=1)
    collections: Optional[List[str]] = Field(None, description="Specific collections to search (None = all)")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    limit: int = Field(10, description="Maximum results per collection", ge=1, le=100)
    include_embeddings: bool = Field(False, description="Include vector embeddings in response")
    min_similarity: float = Field(0.0, description="Minimum similarity threshold", ge=0.0, le=1.0)


class CollectionQueryResult(BaseModel):
    """Results from advanced cross-collection query"""
    total_results: int = Field(..., description="Total results across all collections")
    collections_searched: int = Field(..., description="Number of collections searched")
    results_by_collection: Dict[str, List[DocumentResponse]] = Field(..., description="Results grouped by collection")


class StorageNode(BaseModel):
    """Node in the storage tree (file or directory)"""
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path")
    type: str = Field(..., description="Type: 'file' or 'directory'")
    size: Optional[int] = Field(None, description="Size in bytes (for files)")
    children: Optional[List['StorageNode']] = Field(None, description="Child nodes (for directories)")


class StorageTreeResponse(BaseModel):
    """ChromaDB storage directory tree"""
    base_path: str = Field(..., description="Base ChromaDB storage path")
    total_size: int = Field(..., description="Total size in bytes")
    tree: StorageNode = Field(..., description="Directory tree structure")


# For Pydantic v2 compatibility
StorageNode.model_rebuild()
