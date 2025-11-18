"""
ChromaDB Viewer API Routes

Provides endpoints for browsing and exploring ChromaDB collections and documents.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies.vector_storage import get_base_chromadb_client
from src.infrastructure.chromadb.client import ChromaDBClient
from src.services.monitoring import CollectionViewerService
from src.repositories.chromadb import StorageRepository
from src.api.schemas.chromadb_viewer import (
    CollectionDetailResponse,
    DocumentResponse,
    DocumentListResponse,
    StorageTreeResponse
)


router = APIRouter()


@router.get("/chromadb/collections/{collection_name}/details", response_model=CollectionDetailResponse)
async def get_collection_details(
    collection_name: str,
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
) -> CollectionDetailResponse:
    """
    Get detailed information about a specific ChromaDB collection.

    Args:
        collection_name: Name of the collection

    Returns:
        Collection details including vector count, metadata, and isolation info
    """
    viewer_service = CollectionViewerService(chromadb_client)
    return await viewer_service.get_collection_details(collection_name)


@router.get("/chromadb/collections/{collection_name}/documents", response_model=DocumentListResponse)
async def list_collection_documents(
    collection_name: str,
    offset: int = 0,
    limit: int = 10,
    include_embeddings: bool = False,
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
) -> DocumentListResponse:
    """
    Browse documents in a collection with pagination.

    Args:
        collection_name: Name of the collection
        offset: Pagination offset (default: 0)
        limit: Maximum documents to return (default: 10, max: 100)
        include_embeddings: Include vector embeddings in response (default: False)

    Returns:
        Paginated list of documents with metadata
    """
    viewer_service = CollectionViewerService(chromadb_client)
    return await viewer_service.list_collection_documents(
        collection_name=collection_name,
        offset=offset,
        limit=limit,
        include_embeddings=include_embeddings
    )


@router.get("/chromadb/collections/{collection_name}/documents/{document_id}", response_model=DocumentResponse)
async def get_document_details(
    collection_name: str,
    document_id: str,
    include_embedding: bool = False,
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
) -> DocumentResponse:
    """
    Get a single document by ID from a collection.

    Args:
        collection_name: Name of the collection
        document_id: Unique document identifier
        include_embedding: Include vector embedding in response (default: False)

    Returns:
        Document details with metadata and optional embedding
    """
    viewer_service = CollectionViewerService(chromadb_client)
    return await viewer_service.get_document_details(
        collection_name=collection_name,
        document_id=document_id,
        include_embedding=include_embedding
    )


@router.get("/chromadb/storage-tree", response_model=StorageTreeResponse)
async def get_storage_tree(
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
) -> StorageTreeResponse:
    """
    Get the ChromaDB storage directory tree structure.

    Returns:
        Directory tree with file sizes and structure
    """
    try:
        storage_repo = StorageRepository(chromadb_client)
        return storage_repo.get_storage_tree()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building storage tree: {str(e)}"
        )
