"""
ChromaDB Search Service

Handles search orchestration for ChromaDB collections.
Extracts business logic from route handlers.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from src.infrastructure.chromadb.client import ChromaDBClient
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.services.monitoring.transformers import SearchResultTransformer
from src.api.schemas.chromadb_viewer import (
    DocumentResponse,
    CollectionSearchRequest,
    CollectionQueryRequest,
    CollectionQueryResult
)


class ChromaDBSearchService:
    """Service for searching ChromaDB collections"""

    def __init__(
        self,
        chromadb_client: ChromaDBClient,
        embedding_service: Any,
        metrics_collector: Optional[ChromaDBMetricsCollector] = None
    ):
        self.chromadb_client = chromadb_client
        self.embedding_service = embedding_service
        self.metrics_collector = metrics_collector
        self.transformer = SearchResultTransformer()

    async def search_collection(
        self,
        collection_name: str,
        search_request: CollectionSearchRequest
    ) -> List[DocumentResponse]:
        """
        Search for documents within a specific collection.

        Args:
            collection_name: Name of the collection to search
            search_request: Search parameters (query, limit, filters, etc.)

        Returns:
            List of documents ranked by similarity

        Raises:
            HTTPException: If collection not found or search fails
        """
        # Validate embedding service
        if not self.embedding_service:
            raise HTTPException(
                status_code=503,
                detail="Embedding service not available"
            )

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(
            search_request.query
        )

        # Get the collection
        collection = self.chromadb_client.client.get_collection(collection_name)

        # Build include list (conditionally to avoid None values)
        include_list = ["documents", "metadatas", "distances"]
        if search_request.include_embeddings:
            include_list.append("embeddings")

        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=search_request.limit,
            where=search_request.filters,
            include=include_list
        )

        # Transform results
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            embeddings = (
                results.get("embeddings", [[]])[0]
                if search_request.include_embeddings
                else []
            )

            return self.transformer.transform_results(
                ids=ids,
                documents=docs,
                metadatas=metadatas,
                distances=distances,
                embeddings=embeddings,
                min_similarity=search_request.min_similarity
            )

        return []

    async def advanced_query(
        self,
        query_request: CollectionQueryRequest
    ) -> CollectionQueryResult:
        """
        Advanced query across multiple ChromaDB collections.

        Args:
            query_request: Query parameters including text, filters, and limits

        Returns:
            Results grouped by collection with similarity scores

        Raises:
            HTTPException: If query fails
        """
        # Validate embedding service
        if not self.embedding_service:
            raise HTTPException(
                status_code=503,
                detail="Embedding service not available"
            )

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(
            query_request.query
        )

        # Determine collections to search
        collections_to_search = await self._get_collections_to_search(
            query_request.collections
        )

        # Search each collection
        results_by_collection = {}
        total_results = 0

        for collection_name in collections_to_search:
            collection_docs = await self._search_single_collection(
                collection_name=collection_name,
                query_embedding=query_embedding,
                query_request=query_request
            )

            if collection_docs:
                results_by_collection[collection_name] = collection_docs
                total_results += len(collection_docs)

        return CollectionQueryResult(
            total_results=total_results,
            collections_searched=len(results_by_collection),
            results_by_collection=results_by_collection
        )

    async def _get_collections_to_search(
        self,
        specified_collections: Optional[List[str]]
    ) -> List[str]:
        """Get list of collections to search"""
        if specified_collections:
            return specified_collections

        # Get all collections from metrics
        if not self.metrics_collector:
            raise HTTPException(
                status_code=500,
                detail="Metrics collector not available for collection discovery"
            )

        collection_metrics = await self.metrics_collector.get_collection_metrics()
        return [
            c["collection_name"]
            for c in collection_metrics.get("collections", [])
        ]

    async def _search_single_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        query_request: CollectionQueryRequest
    ) -> List[DocumentResponse]:
        """Search a single collection with error handling"""
        try:
            collection = self.chromadb_client.client.get_collection(collection_name)

            # Build where filter
            where_filter = self._build_where_filter(query_request)

            # Build include list (conditionally to avoid None values)
            include_list = ["documents", "metadatas", "distances"]
            if query_request.include_embeddings:
                include_list.append("embeddings")

            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=query_request.limit,
                where=where_filter if where_filter else None,
                include=include_list
            )

            # Transform results
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                docs = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                embeddings = (
                    results.get("embeddings", [[]])[0]
                    if query_request.include_embeddings
                    else []
                )

                return self.transformer.transform_results(
                    ids=ids,
                    documents=docs,
                    metadatas=metadatas,
                    distances=distances,
                    embeddings=embeddings,
                    min_similarity=query_request.min_similarity
                )

            return []

        except Exception:
            # Skip collections that error out
            return []

    def _build_where_filter(
        self,
        query_request: CollectionQueryRequest
    ) -> Optional[Dict[str, str]]:
        """Build where filter from query request"""
        where_filter = {}

        if query_request.user_id:
            where_filter["user_id"] = query_request.user_id
        if query_request.project_id:
            where_filter["project_id"] = query_request.project_id
        if query_request.document_type:
            where_filter["document_type"] = query_request.document_type

        return where_filter if where_filter else None
