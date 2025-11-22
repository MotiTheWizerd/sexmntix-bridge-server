"""
Hybrid Search Orchestrator

Combines vector similarity search (70%) with keyword search (30%) for optimal retrieval.

Strategy:
- Execute vector and keyword searches in parallel
- Normalize scores to 0-1 range
- Apply weighted combination: 0.7 * vector_score + 0.3 * keyword_score
- Use Reciprocal Rank Fusion (RRF) for score merging
- Deduplicate and rank final results
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import asyncio

from src.modules.core import Logger
from src.infrastructure.chromadb.models.search_result import SearchResult
from src.infrastructure.postgres.keyword_search_repository import (
    KeywordSearchRepository,
    KeywordSearchResult
)


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""

    vector_weight: float = 0.7  # 70% weight to vector similarity
    keyword_weight: float = 0.3  # 30% weight to keyword matching
    use_rrf: bool = True  # Use Reciprocal Rank Fusion
    rrf_k: int = 60  # RRF constant (typical value: 60)
    task_boost: float = 2.0  # Boost for task field matches in keyword search


class HybridSearchOrchestrator:
    """
    Orchestrates hybrid search combining vector and keyword search.

    Implements 70/30 weighting strategy:
    - Vector similarity: 70% (semantic understanding)
    - Keyword matching: 30% (exact term matching)

    Uses Reciprocal Rank Fusion (RRF) for robust score merging.
    """

    def __init__(
        self,
        keyword_repository: KeywordSearchRepository,
        logger: Logger,
        config: Optional[HybridSearchConfig] = None
    ):
        """
        Initialize hybrid search orchestrator.

        Args:
            keyword_repository: PostgreSQL keyword search repository
            logger: Logger instance
            config: Hybrid search configuration (optional)
        """
        self.keyword_repo = keyword_repository
        self.logger = logger
        self.config = config or HybridSearchConfig()

    async def search(
        self,
        query: str,
        vector_results: List[SearchResult],
        user_id: str,
        project_id: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Execute hybrid search combining vector and keyword results.

        Args:
            query: Search query string
            vector_results: Results from vector similarity search
            user_id: User ID for filtering
            project_id: Project ID for filtering
            limit: Maximum number of final results

        Returns:
            Combined and reranked search results
        """
        try:
            # Execute keyword search in parallel with vector search results processing
            keyword_results = await self.keyword_repo.search_with_boost(
                query=query,
                user_id=user_id,
                project_id=project_id,
                task_boost=self.config.task_boost,
                limit=limit * 3  # Retrieve more for better merging
            )

            if not keyword_results:
                self.logger.info("No keyword results, returning vector results only")
                return vector_results[:limit]

            if not vector_results:
                self.logger.info("No vector results, returning keyword results only")
                return self._convert_keyword_results(keyword_results[:limit])

            # Merge results using RRF or weighted combination
            if self.config.use_rrf:
                merged_results = self._merge_with_rrf(
                    vector_results,
                    keyword_results,
                    limit
                )
            else:
                merged_results = self._merge_with_weights(
                    vector_results,
                    keyword_results,
                    limit
                )

            self.logger.info(
                f"Hybrid search merged {len(vector_results)} vector + "
                f"{len(keyword_results)} keyword results into {len(merged_results)} final results"
            )

            return merged_results

        except Exception as e:
            self.logger.error(f"Hybrid search failed: {e}")
            # Fallback to vector results only
            return vector_results[:limit]

    def _merge_with_rrf(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[KeywordSearchResult],
        limit: int
    ) -> List[SearchResult]:
        """
        Merge results using Reciprocal Rank Fusion (RRF).

        RRF Formula: score = sum(1 / (k + rank_i))
        where k is a constant (typically 60) and rank_i is the rank in each list.

        RRF is more robust than simple score averaging and handles different
        score scales gracefully.

        Args:
            vector_results: Vector search results
            keyword_results: Keyword search results
            limit: Maximum number of results

        Returns:
            Merged and ranked results
        """
        k = self.config.rrf_k

        # Build RRF scores
        rrf_scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}

        # Add vector results
        for rank, result in enumerate(vector_results, start=1):
            doc_id = result.memory_log_id
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                self.config.vector_weight / (k + rank)
            )
            result_map[doc_id] = result

        # Add keyword results
        for rank, kw_result in enumerate(keyword_results, start=1):
            doc_id = kw_result.memory_log_id
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                self.config.keyword_weight / (k + rank)
            )

            # If not in result_map, convert keyword result to SearchResult
            if doc_id not in result_map:
                result_map[doc_id] = self._convert_single_keyword_result(kw_result)

        # Sort by RRF score (descending)
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build final results with updated scores
        merged_results = []
        for doc_id in sorted_ids[:limit]:
            result = result_map[doc_id]
            # Update similarity score with RRF score (normalized)
            result.similarity = rrf_scores[doc_id]
            merged_results.append(result)

        return merged_results

    def _merge_with_weights(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[KeywordSearchResult],
        limit: int
    ) -> List[SearchResult]:
        """
        Merge results using weighted score combination.

        Formula: final_score = (0.7 * vector_score) + (0.3 * keyword_score)

        Args:
            vector_results: Vector search results
            keyword_results: Keyword search results
            limit: Maximum number of results

        Returns:
            Merged and ranked results
        """
        # Build score maps
        vector_scores: Dict[str, float] = {
            r.memory_log_id: r.similarity for r in vector_results
        }
        keyword_scores: Dict[str, float] = {
            r.memory_log_id: r.score for r in keyword_results
        }

        # Combine all unique document IDs
        all_doc_ids: Set[str] = set(vector_scores.keys()) | set(keyword_scores.keys())

        # Calculate weighted scores
        weighted_scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {r.memory_log_id: r for r in vector_results}

        for doc_id in all_doc_ids:
            vector_score = vector_scores.get(doc_id, 0.0)
            keyword_score = keyword_scores.get(doc_id, 0.0)

            weighted_scores[doc_id] = (
                self.config.vector_weight * vector_score +
                self.config.keyword_weight * keyword_score
            )

            # Add to result map if not present
            if doc_id not in result_map:
                # Find keyword result to convert
                kw_result = next(
                    (kr for kr in keyword_results if kr.memory_log_id == doc_id),
                    None
                )
                if kw_result:
                    result_map[doc_id] = self._convert_single_keyword_result(kw_result)

        # Sort by weighted score (descending)
        sorted_ids = sorted(
            weighted_scores.keys(),
            key=lambda x: weighted_scores[x],
            reverse=True
        )

        # Build final results
        merged_results = []
        for doc_id in sorted_ids[:limit]:
            result = result_map[doc_id]
            result.similarity = weighted_scores[doc_id]
            merged_results.append(result)

        return merged_results

    def _convert_keyword_results(
        self,
        keyword_results: List[KeywordSearchResult]
    ) -> List[SearchResult]:
        """
        Convert keyword search results to SearchResult format.

        Args:
            keyword_results: List of keyword search results

        Returns:
            List of SearchResult objects
        """
        return [
            self._convert_single_keyword_result(kr)
            for kr in keyword_results
        ]

    def _convert_single_keyword_result(
        self,
        keyword_result: KeywordSearchResult
    ) -> SearchResult:
        """
        Convert a single keyword result to SearchResult.

        Args:
            keyword_result: Keyword search result

        Returns:
            SearchResult object
        """
        # Note: This creates a minimal SearchResult
        # The actual memory data will be fetched separately if needed
        return SearchResult(
            memory_log_id=keyword_result.memory_log_id,
            similarity=keyword_result.score,
            distance=1.0 - keyword_result.score,  # Convert score to distance
            metadata={},  # Will be populated by caller
            document={}  # Will be populated by caller
        )
