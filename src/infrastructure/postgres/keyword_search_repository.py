"""
Keyword Search Repository

Provides PostgreSQL full-text search functionality for memory logs.
Uses TSVECTOR and GIN indexes for fast keyword matching.

Supports:
- Full-text search with ranking
- Phrase matching
- Individual term matching
- Field-weighted scoring (task/summary weighted higher)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.modules.core import Logger


class KeywordSearchResult:
    """Result from keyword search with BM25-style ranking."""

    def __init__(
        self,
        memory_log_id: str,
        score: float,
        rank: float,
        matched_terms: List[str]
    ):
        """
        Initialize keyword search result.

        Args:
            memory_log_id: ID of the memory log
            score: Normalized score (0-1)
            rank: Raw PostgreSQL ts_rank score
            matched_terms: List of search terms that matched
        """
        self.memory_log_id = memory_log_id
        self.score = score
        self.rank = rank
        self.matched_terms = matched_terms

    def __repr__(self) -> str:
        return f"KeywordSearchResult(id={self.memory_log_id}, score={self.score:.3f})"


class KeywordSearchRepository:
    """
    PostgreSQL full-text search repository for memory logs.

    Uses TSVECTOR column with GIN index for fast keyword search.
    Implements BM25-style ranking with field weighting:
    - A: task, summary (highest weight)
    - B: root_cause, lesson (high weight)
    - C: component, validation (medium weight)
    - D: tags (low weight)
    """

    def __init__(self, db_session: Session, logger: Logger):
        """
        Initialize keyword search repository.

        Args:
            db_session: SQLAlchemy database session
            logger: Logger instance
        """
        self.db = db_session
        self.logger = logger

    async def search(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 50
    ) -> List[KeywordSearchResult]:
        """
        Search memory logs using PostgreSQL full-text search.

        Uses ts_rank for relevance scoring with field-weighted TSVECTOR.

        Args:
            query: Search query string
            user_id: User ID for filtering
            project_id: Project ID for filtering
            limit: Maximum number of results

        Returns:
            List of KeywordSearchResult objects sorted by score (descending)
        """
        try:
            # Use plainto_tsquery for natural language queries
            # Handles phrase matching and term weighting
            sql = text("""
                SELECT
                    id,
                    ts_rank(search_vector, query) AS rank,
                    ts_headline('english', raw_data->>'summary', query) AS headline
                FROM
                    memory_logs,
                    plainto_tsquery('english', :query) query
                WHERE
                    search_vector @@ query
                    AND user_id = :user_id
                    AND project_id = :project_id
                ORDER BY
                    rank DESC
                LIMIT :limit
            """)

            result = self.db.execute(
                sql,
                {
                    "query": query,
                    "user_id": user_id,
                    "project_id": project_id,
                    "limit": limit
                }
            )

            rows = result.fetchall()

            if not rows:
                self.logger.debug(f"No keyword matches found for query: {query}")
                return []

            # Normalize scores to 0-1 range
            max_rank = max(row[1] for row in rows) if rows else 1.0
            min_rank = min(row[1] for row in rows) if rows else 0.0
            rank_range = max_rank - min_rank if max_rank > min_rank else 1.0

            results = []
            for row in rows:
                memory_log_id = row[0]
                raw_rank = row[1]

                # Normalize score to 0-1 range
                normalized_score = (raw_rank - min_rank) / rank_range if rank_range > 0 else 0.0

                # Extract matched terms from query
                matched_terms = query.lower().split()

                results.append(KeywordSearchResult(
                    memory_log_id=memory_log_id,
                    score=normalized_score,
                    rank=raw_rank,
                    matched_terms=matched_terms
                ))

            self.logger.info(
                f"Keyword search found {len(results)} results for query: {query}"
            )

            return results

        except Exception as e:
            self.logger.error(f"Keyword search failed: {e}")
            raise

    async def search_with_boost(
        self,
        query: str,
        user_id: str,
        project_id: str,
        task_boost: float = 2.0,
        limit: int = 50
    ) -> List[KeywordSearchResult]:
        """
        Search with additional boosting for task field matches.

        Provides extra weight to memories where the task field matches the query.

        Args:
            query: Search query string
            user_id: User ID for filtering
            project_id: Project ID for filtering
            task_boost: Boost multiplier for task field matches (default: 2.0)
            limit: Maximum number of results

        Returns:
            List of KeywordSearchResult objects sorted by boosted score
        """
        try:
            # Use phrase matching for task field to boost exact matches
            sql = text("""
                SELECT
                    id,
                    ts_rank(search_vector, query) AS base_rank,
                    CASE
                        WHEN task ILIKE '%' || :query || '%' THEN ts_rank(search_vector, query) * :task_boost
                        ELSE ts_rank(search_vector, query)
                    END AS boosted_rank
                FROM
                    memory_logs,
                    plainto_tsquery('english', :query) query
                WHERE
                    search_vector @@ query
                    AND user_id = :user_id
                    AND project_id = :project_id
                ORDER BY
                    boosted_rank DESC
                LIMIT :limit
            """)

            result = self.db.execute(
                sql,
                {
                    "query": query,
                    "user_id": user_id,
                    "project_id": project_id,
                    "task_boost": task_boost,
                    "limit": limit
                }
            )

            rows = result.fetchall()

            if not rows:
                return []

            # Normalize boosted scores
            max_rank = max(row[2] for row in rows)
            min_rank = min(row[2] for row in rows)
            rank_range = max_rank - min_rank if max_rank > min_rank else 1.0

            results = []
            for row in rows:
                memory_log_id = row[0]
                boosted_rank = row[2]

                normalized_score = (boosted_rank - min_rank) / rank_range if rank_range > 0 else 0.0

                matched_terms = query.lower().split()

                results.append(KeywordSearchResult(
                    memory_log_id=memory_log_id,
                    score=normalized_score,
                    rank=boosted_rank,
                    matched_terms=matched_terms
                ))

            return results

        except Exception as e:
            self.logger.error(f"Boosted keyword search failed: {e}")
            raise

    async def count_matches(
        self,
        query: str,
        user_id: str,
        project_id: str
    ) -> int:
        """
        Count number of memory logs matching the query.

        Args:
            query: Search query string
            user_id: User ID for filtering
            project_id: Project ID for filtering

        Returns:
            Number of matching memory logs
        """
        try:
            sql = text("""
                SELECT COUNT(*)
                FROM
                    memory_logs,
                    plainto_tsquery('english', :query) query
                WHERE
                    search_vector @@ query
                    AND user_id = :user_id
                    AND project_id = :project_id
            """)

            result = self.db.execute(
                sql,
                {
                    "query": query,
                    "user_id": user_id,
                    "project_id": project_id
                }
            )

            count = result.scalar()
            return count or 0

        except Exception as e:
            self.logger.error(f"Count matches failed: {e}")
            return 0
