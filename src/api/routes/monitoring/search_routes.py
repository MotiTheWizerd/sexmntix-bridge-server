"""
ChromaDB Search API Routes

Provides semantic search endpoints for ChromaDB collections.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from src.api.dependencies.vector_storage import get_base_chromadb_client
from src.api.dependencies.services import get_chromadb_metrics_collector
from src.infrastructure.chromadb.client import ChromaDBClient
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.services.monitoring import ChromaDBSearchService
from src.api.schemas.chromadb_viewer import (
    DocumentResponse,
    CollectionSearchRequest,
    CollectionQueryRequest,
    CollectionQueryResult
)


router = APIRouter()


@router.post("/chromadb/collections/{collection_name}/search")
async def search_collection(
    collection_name: str,
    search_request: CollectionSearchRequest,
    request: Request,
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
) -> List[DocumentResponse]:
    """
    Search for documents within a specific collection using semantic similarity.

    Args:
        collection_name: Name of the collection to search
        search_request: Search parameters (query, limit, filters, etc.)

    Returns:
        List of documents ranked by similarity
    """
    try:
        # Get embedding service from app state
        embedding_service = request.app.state.embedding_service

        # Create search service
        search_service = ChromaDBSearchService(
            chromadb_client=chromadb_client,
            embedding_service=embedding_service
        )

        # Perform search
        return await search_service.search_collection(
            collection_name=collection_name,
            search_request=search_request
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed in collection '{collection_name}': {str(e)}"
        )


@router.post("/chromadb/query", response_model=CollectionQueryResult)
async def advanced_query(
    query_request: CollectionQueryRequest,
    request: Request,
    chromadb_client: ChromaDBClient = Depends(get_base_chromadb_client),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> CollectionQueryResult:
    """
    Advanced query across multiple ChromaDB collections.

    Allows searching across all collections or a subset, with filtering by
    user_id, project_id, and document type.

    Args:
        query_request: Query parameters including text, filters, and limits

    Returns:
        Results grouped by collection with similarity scores
    """
    try:
        # Get embedding service from app state
        embedding_service = request.app.state.embedding_service

        # Create search service
        search_service = ChromaDBSearchService(
            chromadb_client=chromadb_client,
            embedding_service=embedding_service,
            metrics_collector=metrics_collector
        )

        # Perform advanced query
        return await search_service.advanced_query(query_request)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Advanced query failed: {str(e)}"
        )
