"""
Monitoring API Routes

Provides endpoints for system monitoring and metrics:
- /monitoring/chromadb - ChromaDB metrics
- /monitoring/health/detailed - Comprehensive health check
- /monitoring/metrics - Overall system metrics
- /monitoring/chromadb/collections/* - ChromaDB viewer endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from typing import Dict, Any, List
import os
from pathlib import Path

from src.api.dependencies.database import get_db_session
from src.api.dependencies.services import get_chromadb_metrics_collector
from src.api.dependencies.vector_storage import get_base_chromadb_client
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.infrastructure.chromadb.client import ChromaDBClient
from src.api.schemas.chromadb_viewer import (
    CollectionDetailResponse,
    DocumentResponse,
    DocumentListResponse,
    CollectionSearchRequest,
    CollectionQueryRequest,
    CollectionQueryResult,
    StorageTreeResponse,
    StorageNode
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/chromadb")
async def get_chromadb_metrics(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """
    Get comprehensive ChromaDB metrics.

    Returns:
        - Collections: count, sizes, vectors
        - Ingestion: daily/weekly/monthly stats, timeline
        - Search Performance: latency percentiles, rates
        - Search Quality: similarity scores, result distribution
        - Storage: disk usage, health status
    """
    try:
        snapshot = await metrics_collector.get_snapshot(db_session)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ChromaDB metrics: {str(e)}")


@router.get("/chromadb/collections")
async def get_collection_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get detailed collection metrics"""
    try:
        return await metrics_collector.get_collection_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection metrics: {str(e)}")


@router.get("/chromadb/ingestion")
async def get_ingestion_metrics(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get vector ingestion metrics with time-series data"""
    try:
        return await metrics_collector.get_ingestion_metrics(db_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ingestion metrics: {str(e)}")


@router.get("/chromadb/search-performance")
async def get_search_performance_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get search performance metrics (latency, throughput)"""
    try:
        return await metrics_collector.get_search_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search performance metrics: {str(e)}")


@router.get("/chromadb/search-quality")
async def get_search_quality_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get search quality metrics (similarity scores, result distribution)"""
    try:
        return await metrics_collector.get_search_quality_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search quality metrics: {str(e)}")


@router.get("/chromadb/storage")
async def get_storage_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get storage health metrics"""
    try:
        return await metrics_collector.get_storage_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting storage metrics: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """
    Comprehensive health check including all subsystems.

    Returns health status for:
    - Database connection
    - ChromaDB
    - Storage
    - Overall metrics
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {}
    }

    # Database check
    try:
        result = await db_session.execute("SELECT 1")
        checks["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        checks["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        checks["status"] = "degraded"

    # ChromaDB check
    try:
        collection_metrics = await metrics_collector.get_collection_metrics()
        if "error" in collection_metrics:
            checks["checks"]["chromadb"] = {
                "status": "unhealthy",
                "message": collection_metrics["error"]
            }
            checks["status"] = "degraded"
        else:
            checks["checks"]["chromadb"] = {
                "status": "healthy",
                "message": f"{collection_metrics['total_collections']} collections, {collection_metrics['total_vectors']} vectors",
                "collections": collection_metrics["total_collections"],
                "vectors": collection_metrics["total_vectors"]
            }
    except Exception as e:
        checks["checks"]["chromadb"] = {
            "status": "unhealthy",
            "message": f"ChromaDB error: {str(e)}"
        }
        checks["status"] = "degraded"

    # Storage check
    try:
        storage_metrics = await metrics_collector.get_storage_metrics()
        if "error" in storage_metrics:
            checks["checks"]["storage"] = {
                "status": "warning",
                "message": storage_metrics["error"]
            }
        else:
            storage_status = storage_metrics.get("health_status", "unknown")
            checks["checks"]["storage"] = {
                "status": storage_status,
                "message": f"{storage_metrics['total_storage_mb']} MB used, {storage_metrics['storage_utilization']}% utilization",
                "disk_free_gb": storage_metrics.get("disk_free_gb", 0),
                "utilization": storage_metrics.get("storage_utilization", 0)
            }

            if storage_status in ["warning", "critical"]:
                checks["status"] = "degraded"
    except Exception as e:
        checks["checks"]["storage"] = {
            "status": "warning",
            "message": f"Storage check error: {str(e)}"
        }

    return checks


# ============================================================================
# ChromaDB Viewer Endpoints
# ============================================================================

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
    try:
        # Get the collection directly
        collection = chromadb_client.client.get_collection(collection_name)

        # Get vector count
        vector_count = collection.count()

        # Extract metadata
        metadata = collection.metadata or {}
        user_id = metadata.get("user_id")
        project_id = metadata.get("project_id")
        document_type = metadata.get("document_type")

        return CollectionDetailResponse(
            name=collection_name,
            vector_count=vector_count,
            metadata=metadata,
            user_id=user_id,
            project_id=project_id,
            document_type=document_type
        )

    except Exception as e:
        raise HTTPException(
            status_code=404 if "does not exist" in str(e).lower() else 500,
            detail=f"Error getting collection '{collection_name}': {str(e)}"
        )


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
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        # Get the collection
        collection = chromadb_client.client.get_collection(collection_name)

        # Get total count
        total_count = collection.count()

        # Get documents with pagination
        # ChromaDB doesn't have native offset/limit, so we fetch and slice
        result = collection.get(
            include=["documents", "metadatas", "embeddings" if include_embeddings else None],
            limit=min(offset + limit, total_count) if total_count > 0 else None
        )

        # Build document responses
        documents = []
        ids = result.get("ids", [])
        docs = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        embeddings = result.get("embeddings", []) if include_embeddings else []

        # Apply offset and limit
        start_idx = min(offset, len(ids))
        end_idx = min(offset + limit, len(ids))

        for i in range(start_idx, end_idx):
            doc_response = DocumentResponse(
                id=ids[i],
                document=docs[i] if i < len(docs) else {},
                metadata=metadatas[i] if i < len(metadatas) else {},
                embedding=embeddings[i] if i < len(embeddings) else None
            )
            documents.append(doc_response)

        return DocumentListResponse(
            collection_name=collection_name,
            total_count=total_count,
            documents=documents,
            offset=offset,
            limit=limit,
            has_more=(offset + limit) < total_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=404 if "does not exist" in str(e).lower() else 500,
            detail=f"Error listing documents in '{collection_name}': {str(e)}"
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
    try:
        # Get the collection
        collection = chromadb_client.client.get_collection(collection_name)

        # Get specific document
        result = collection.get(
            ids=[document_id],
            include=["documents", "metadatas", "embeddings" if include_embedding else None]
        )

        if not result["ids"]:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found in collection '{collection_name}'"
            )

        return DocumentResponse(
            id=result["ids"][0],
            document=result["documents"][0] if result.get("documents") else {},
            metadata=result["metadatas"][0] if result.get("metadatas") else {},
            embedding=result["embeddings"][0] if result.get("embeddings") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document '{document_id}': {str(e)}"
        )


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
        # Get embedding service
        embedding_service = request.app.state.embedding_service
        if not embedding_service:
            raise HTTPException(
                status_code=503,
                detail="Embedding service not available"
            )

        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(search_request.query)

        # Get the collection
        collection = chromadb_client.client.get_collection(collection_name)

        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=search_request.limit,
            where=search_request.filters,
            include=["documents", "metadatas", "distances", "embeddings" if search_request.include_embeddings else None]
        )

        # Build response
        documents = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            embeddings = results.get("embeddings", [[]])[0] if search_request.include_embeddings else []

            for i, doc_id in enumerate(ids):
                distance = distances[i] if i < len(distances) else 0.0
                similarity = 1.0 - distance  # Convert distance to similarity

                # Apply similarity filter
                if similarity < search_request.min_similarity:
                    continue

                doc_response = DocumentResponse(
                    id=doc_id,
                    document=docs[i] if i < len(docs) else {},
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    distance=distance,
                    similarity=similarity
                )
                documents.append(doc_response)

        return documents

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
        # Get embedding service
        embedding_service = request.app.state.embedding_service
        if not embedding_service:
            raise HTTPException(
                status_code=503,
                detail="Embedding service not available"
            )

        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query_request.query)

        # Get collections to search
        if query_request.collections:
            collections_to_search = query_request.collections
        else:
            # Get all collections
            collection_metrics = await metrics_collector.get_collection_metrics()
            collections_to_search = [c["collection_name"] for c in collection_metrics.get("collections", [])]

        # Search each collection
        results_by_collection = {}
        total_results = 0

        for collection_name in collections_to_search:
            try:
                collection = chromadb_client.client.get_collection(collection_name)

                # Build where filter
                where_filter = {}
                if query_request.user_id:
                    where_filter["user_id"] = query_request.user_id
                if query_request.project_id:
                    where_filter["project_id"] = query_request.project_id
                if query_request.document_type:
                    where_filter["document_type"] = query_request.document_type

                # Search
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=query_request.limit,
                    where=where_filter if where_filter else None,
                    include=["documents", "metadatas", "distances", "embeddings" if query_request.include_embeddings else None]
                )

                # Process results
                collection_docs = []
                if results and results.get("ids") and results["ids"][0]:
                    ids = results["ids"][0]
                    docs = results.get("documents", [[]])[0]
                    metadatas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]
                    embeddings = results.get("embeddings", [[]])[0] if query_request.include_embeddings else []

                    for i, doc_id in enumerate(ids):
                        distance = distances[i] if i < len(distances) else 0.0
                        similarity = 1.0 - distance

                        # Apply similarity filter
                        if similarity < query_request.min_similarity:
                            continue

                        doc_response = DocumentResponse(
                            id=doc_id,
                            document=docs[i] if i < len(docs) else {},
                            metadata=metadatas[i] if i < len(metadatas) else {},
                            embedding=embeddings[i] if i < len(embeddings) else None,
                            distance=distance,
                            similarity=similarity
                        )
                        collection_docs.append(doc_response)

                if collection_docs:
                    results_by_collection[collection_name] = collection_docs
                    total_results += len(collection_docs)

            except Exception as e:
                # Skip collections that error out
                continue

        return CollectionQueryResult(
            total_results=total_results,
            collections_searched=len(results_by_collection),
            results_by_collection=results_by_collection
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Advanced query failed: {str(e)}"
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
        base_path = chromadb_client.base_storage_path

        def build_tree(path: str) -> StorageNode:
            """Recursively build directory tree"""
            path_obj = Path(path)

            if path_obj.is_file():
                return StorageNode(
                    name=path_obj.name,
                    path=str(path_obj),
                    type="file",
                    size=path_obj.stat().st_size,
                    children=None
                )
            elif path_obj.is_dir():
                children = []
                try:
                    for child in sorted(path_obj.iterdir()):
                        children.append(build_tree(str(child)))
                except PermissionError:
                    pass

                return StorageNode(
                    name=path_obj.name if path_obj.name else "chromadb",
                    path=str(path_obj),
                    type="directory",
                    size=None,
                    children=children if children else None
                )
            else:
                return StorageNode(
                    name=path_obj.name,
                    path=str(path_obj),
                    type="unknown",
                    size=None,
                    children=None
                )

        def calculate_total_size(node: StorageNode) -> int:
            """Calculate total size recursively"""
            if node.type == "file" and node.size:
                return node.size
            elif node.children:
                return sum(calculate_total_size(child) for child in node.children)
            return 0

        # Build tree
        tree = build_tree(base_path)
        total_size = calculate_total_size(tree)

        return StorageTreeResponse(
            base_path=base_path,
            total_size=total_size,
            tree=tree
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building storage tree: {str(e)}"
        )
