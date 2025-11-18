"""
Collection Viewer Service

Handles collection browsing and document retrieval logic.
Extracts business logic from route handlers.
"""

from typing import Optional
from fastapi import HTTPException
import logging
import traceback

from src.infrastructure.chromadb.client import ChromaDBClient
from src.api.schemas.chromadb_viewer import (
    CollectionDetailResponse,
    DocumentResponse,
    DocumentListResponse
)

logger = logging.getLogger(__name__)


class CollectionViewerService:
    """Service for viewing ChromaDB collections and documents"""

    # Pagination limits
    MAX_LIMIT = 100
    MIN_LIMIT = 1

    def __init__(self, chromadb_client: ChromaDBClient):
        self.chromadb_client = chromadb_client

    async def get_collection_details(
        self,
        collection_name: str
    ) -> CollectionDetailResponse:
        """
        Get detailed information about a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection details including vector count and metadata

        Raises:
            HTTPException: If collection not found
        """
        try:
            # Get the collection
            collection = self.chromadb_client.client.get_collection(collection_name)

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

    async def list_collection_documents(
        self,
        collection_name: str,
        offset: int = 0,
        limit: int = 10,
        include_embeddings: bool = False
    ) -> DocumentListResponse:
        """
        Browse documents in a collection with pagination.

        Args:
            collection_name: Name of the collection
            offset: Pagination offset
            limit: Maximum documents to return
            include_embeddings: Include vector embeddings in response

        Returns:
            Paginated list of documents

        Raises:
            HTTPException: If collection not found
        """
        try:
            # Log incoming request
            logger.info(f"[CollectionViewerService.list_collection_documents] Starting request")
            logger.info(f"[CollectionViewerService] collection_name={collection_name}")
            logger.info(f"[CollectionViewerService] offset={offset}, limit={limit}, include_embeddings={include_embeddings}")

            # Validate and normalize limit
            limit = self._normalize_limit(limit)
            logger.info(f"[CollectionViewerService] Normalized limit={limit}")

            # Get the collection
            logger.info(f"[CollectionViewerService] Getting collection '{collection_name}'...")
            collection = self.chromadb_client.client.get_collection(collection_name)
            logger.info(f"[CollectionViewerService] Collection retrieved successfully")

            # Get total count
            total_count = collection.count()
            logger.info(f"[CollectionViewerService] Total count={total_count}")

            # Build include list (conditionally to avoid None values)
            include_list = ["documents", "metadatas"]
            if include_embeddings:
                include_list.append("embeddings")

            logger.info(f"[CollectionViewerService] Include list constructed: {include_list}")
            logger.info(f"[CollectionViewerService] Include list types: {[type(x) for x in include_list]}")
            logger.info(f"[CollectionViewerService] Contains None: {None in include_list}")

            fetch_limit = min(offset + limit, total_count) if total_count > 0 else None
            logger.info(f"[CollectionViewerService] Calling collection.get() with include={include_list}, limit={fetch_limit}")

            # Get documents with pagination
            result = collection.get(
                include=include_list,
                limit=fetch_limit
            )

            logger.info(f"[CollectionViewerService] collection.get() completed successfully")

            # Build document responses with offset/limit
            documents = self._build_document_list(
                result=result,
                offset=offset,
                limit=limit,
                include_embeddings=include_embeddings
            )

            logger.info(f"[CollectionViewerService] Built {len(documents)} document responses")

            return DocumentListResponse(
                collection_name=collection_name,
                total_count=total_count,
                documents=documents,
                offset=offset,
                limit=limit,
                has_more=(offset + limit) < total_count
            )

        except Exception as e:
            # Detailed error logging
            error_type = type(e).__name__
            error_msg = str(e)

            # Build include list for error reporting
            error_include_list = ["documents", "metadatas"]
            if include_embeddings:
                error_include_list.append("embeddings")

            logger.error(f"[CollectionViewerService] ========== ERROR OCCURRED ==========")
            logger.error(f"[CollectionViewerService] Error type: {error_type}")
            logger.error(f"[CollectionViewerService] Error message: {error_msg}")
            logger.error(f"[CollectionViewerService] Collection: {collection_name}")
            logger.error(f"[CollectionViewerService] Parameters: offset={offset}, limit={limit}, include_embeddings={include_embeddings}")
            logger.error(f"[CollectionViewerService] Include list used: {error_include_list}")
            logger.error(f"[CollectionViewerService] Full traceback:\n{traceback.format_exc()}")
            logger.error(f"[CollectionViewerService] =====================================")

            raise HTTPException(
                status_code=404 if "does not exist" in str(e).lower() else 500,
                detail={
                    "error": error_msg,
                    "error_type": error_type,
                    "operation": "list_collection_documents",
                    "collection_name": collection_name,
                    "parameters": {
                        "offset": offset,
                        "limit": limit,
                        "include_embeddings": include_embeddings
                    },
                    "include_list_used": error_include_list,
                    "traceback": traceback.format_exc()
                }
            )

    async def get_document_details(
        self,
        collection_name: str,
        document_id: str,
        include_embedding: bool = False
    ) -> DocumentResponse:
        """
        Get a single document by ID from a collection.

        Args:
            collection_name: Name of the collection
            document_id: Unique document identifier
            include_embedding: Include vector embedding in response

        Returns:
            Document details with metadata

        Raises:
            HTTPException: If collection or document not found
        """
        try:
            # Log incoming request
            logger.info(f"[CollectionViewerService.get_document_details] Starting request")
            logger.info(f"[CollectionViewerService] collection_name={collection_name}, document_id={document_id}")
            logger.info(f"[CollectionViewerService] include_embedding={include_embedding}")

            # Get the collection
            logger.info(f"[CollectionViewerService] Getting collection '{collection_name}'...")
            collection = self.chromadb_client.client.get_collection(collection_name)
            logger.info(f"[CollectionViewerService] Collection retrieved successfully")

            # Build include list (conditionally to avoid None values)
            include_list = ["documents", "metadatas"]
            if include_embedding:
                include_list.append("embeddings")

            logger.info(f"[CollectionViewerService] Include list: {include_list}")
            logger.info(f"[CollectionViewerService] Calling collection.get() for document_id={document_id}")

            # Get specific document
            result = collection.get(
                ids=[document_id],
                include=include_list
            )

            logger.info(f"[CollectionViewerService] collection.get() completed")

            if not result["ids"]:
                logger.warning(f"[CollectionViewerService] Document '{document_id}' not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Document '{document_id}' not found in collection '{collection_name}'"
                )

            logger.info(f"[CollectionViewerService] Document retrieved successfully")

            return DocumentResponse(
                id=result["ids"][0],
                document=result["documents"][0] if result.get("documents") else {},
                metadata=result["metadatas"][0] if result.get("metadatas") else {},
                embedding=result["embeddings"][0] if result.get("embeddings") else None
            )

        except HTTPException:
            raise
        except Exception as e:
            # Detailed error logging
            error_type = type(e).__name__
            error_msg = str(e)

            # Build include list for error reporting
            error_include_list = ["documents", "metadatas"]
            if include_embedding:
                error_include_list.append("embeddings")

            logger.error(f"[CollectionViewerService] ========== ERROR OCCURRED ==========")
            logger.error(f"[CollectionViewerService] Error type: {error_type}")
            logger.error(f"[CollectionViewerService] Error message: {error_msg}")
            logger.error(f"[CollectionViewerService] Collection: {collection_name}, Document ID: {document_id}")
            logger.error(f"[CollectionViewerService] include_embedding={include_embedding}")
            logger.error(f"[CollectionViewerService] Include list used: {error_include_list}")
            logger.error(f"[CollectionViewerService] Full traceback:\n{traceback.format_exc()}")
            logger.error(f"[CollectionViewerService] =====================================")

            raise HTTPException(
                status_code=500,
                detail={
                    "error": error_msg,
                    "error_type": error_type,
                    "operation": "get_document_details",
                    "collection_name": collection_name,
                    "document_id": document_id,
                    "parameters": {
                        "include_embedding": include_embedding
                    },
                    "include_list_used": error_include_list,
                    "traceback": traceback.format_exc()
                }
            )

    def _normalize_limit(self, limit: int) -> int:
        """Validate and normalize pagination limit"""
        if limit > self.MAX_LIMIT:
            return self.MAX_LIMIT
        if limit < self.MIN_LIMIT:
            return self.MIN_LIMIT
        return limit

    def _build_document_list(
        self,
        result: dict,
        offset: int,
        limit: int,
        include_embeddings: bool
    ) -> list[DocumentResponse]:
        """Build list of DocumentResponse objects with pagination"""
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

        return documents
