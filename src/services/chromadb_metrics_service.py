"""
ChromaDB Metrics Collection Service

Collects and aggregates metrics about ChromaDB operations:
- Collection stats (count, size, vectors)
- Ingestion metrics (vectors added over time)
- Search performance (latency, quality)
- Storage health (disk usage, growth rate)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from statistics import median

from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.infrastructure.chromadb.client import ChromaDBClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from src.database.models.memory_log import MemoryLog


@dataclass
class MetricEvent:
    """Single metric event"""
    timestamp: datetime
    metric_type: str
    value: float
    tags: Dict[str, Any]


class ChromaDBMetricsCollector(BaseService):
    """
    Collects and aggregates ChromaDB metrics.

    Features:
    - Real-time metric collection via EventBus
    - In-memory storage for recent events (last 1000)
    - Statistical aggregation (percentiles, averages)
    - Time-series data for dashboards
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        chromadb_client: ChromaDBClient,
        max_events: int = 1000
    ):
        super().__init__(event_bus, logger)
        self.chromadb_client = chromadb_client
        self.max_events = max_events

        # In-memory storage for recent events
        self.events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_events))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # Search quality tracking
        self.search_results: deque = deque(maxlen=max_events)

        # Register event handlers
        self._register_handlers()

        self.logger.info("ChromaDBMetricsCollector initialized")

    def _register_handlers(self):
        """Subscribe to ChromaDB-related events"""
        self.event_bus.subscribe("vector.stored", self._on_vector_stored)
        self.event_bus.subscribe("vector.searched", self._on_vector_searched)
        self.event_bus.subscribe("search.completed", self._on_search_completed)
        self.event_bus.subscribe("chromadb.error", self._on_chromadb_error)

    async def _on_vector_stored(self, data: Dict[str, Any]):
        """Track vector storage operations"""
        self.record_event(
            metric_type="vector.stored",
            value=1,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
            }
        )
        self.counters["vectors_stored_total"] += 1

    async def _on_vector_searched(self, data: Dict[str, Any]):
        """Track vector search operations"""
        duration_ms = data.get("duration_ms", 0)

        self.record_event(
            metric_type="vector.searched",
            value=duration_ms,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
                "collection_size": data.get("collection_size", 0),
            }
        )

        self.timers["search_latency"].append(duration_ms)
        self.counters["searches_total"] += 1

        # Track slow searches (>500ms)
        if duration_ms > 500:
            self.counters["slow_searches"] += 1

    async def _on_search_completed(self, data: Dict[str, Any]):
        """Track search quality metrics"""
        results = data.get("results", [])
        query = data.get("query", "")

        if not results:
            self.counters["searches_no_results"] += 1

        # Calculate average similarity
        if results:
            similarities = [r.get("similarity", 0) for r in results]
            avg_similarity = sum(similarities) / len(similarities)

            self.search_results.append({
                "timestamp": datetime.utcnow(),
                "query": query[:100],
                "result_count": len(results),
                "avg_similarity": avg_similarity,
                "similarities": similarities,
            })

            # Track similarity distribution
            for sim in similarities:
                if sim >= 0.8:
                    self.counters["similarity_high"] += 1
                elif sim >= 0.5:
                    self.counters["similarity_medium"] += 1
                elif sim >= 0.3:
                    self.counters["similarity_low"] += 1
                else:
                    self.counters["similarity_very_low"] += 1

    async def _on_chromadb_error(self, data: Dict[str, Any]):
        """Track ChromaDB errors"""
        self.counters["chromadb_errors"] += 1
        self.logger.error(f"ChromaDB error: {data.get('error')}")

    def record_event(
        self,
        metric_type: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None
    ):
        """Record a metric event"""
        event = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )
        self.events[metric_type].append(event)

    def get_percentile(self, metric: str, percentile: int) -> float:
        """Calculate percentile for a timer metric"""
        values = sorted(self.timers.get(metric, []))
        if not values:
            return 0.0
        idx = int(len(values) * percentile / 100)
        return values[min(idx, len(values) - 1)]

    def get_rate(self, metric: str, window_seconds: int = 60) -> float:
        """Calculate rate (events per second) over time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent = [e for e in self.events[metric] if e.timestamp > cutoff]
        return len(recent) / window_seconds if window_seconds > 0 else 0

    async def get_collection_metrics(self) -> Dict[str, Any]:
        """Get metrics about ChromaDB collections"""
        try:
            collections = self.chromadb_client.list_collections()

            collection_details = []
            total_vectors = 0

            for col_name in collections:
                # Parse collection name to get user/project info
                # Format: semantix_{hash16}
                try:
                    # Get collection to access count and metadata
                    # We need to iterate through possible user/project combinations
                    # For now, we'll just get basic info from the client
                    collection = self.chromadb_client.client.get_collection(col_name)
                    vector_count = collection.count()
                    total_vectors += vector_count

                    collection_details.append({
                        "collection_name": col_name,
                        "vector_count": vector_count,
                        "metadata": collection.metadata,
                        "user_id": collection.metadata.get("user_id", "unknown"),
                        "project_id": collection.metadata.get("project_id", "unknown"),
                    })
                except Exception as e:
                    self.logger.warning(f"Error getting collection {col_name}: {e}")

            # Sort by vector count
            collection_details.sort(key=lambda x: x["vector_count"], reverse=True)

            return {
                "total_collections": len(collections),
                "total_vectors": total_vectors,
                "collections": collection_details,
                "largest_collection": collection_details[0] if collection_details else None,
                "smallest_collection": collection_details[-1] if collection_details else None,
                "avg_vectors_per_collection": total_vectors / len(collections) if collections else 0,
            }
        except Exception as e:
            self.logger.error(f"Error getting collection metrics: {e}")
            return {
                "total_collections": 0,
                "total_vectors": 0,
                "collections": [],
                "error": str(e),
            }

    async def get_ingestion_metrics(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get vector ingestion metrics from database"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Today's count
            today_result = await db_session.execute(
                select(func.count(MemoryLog.id))
                .where(MemoryLog.created_at >= today_start)
            )
            today_count = today_result.scalar() or 0

            # This week
            week_result = await db_session.execute(
                select(func.count(MemoryLog.id))
                .where(MemoryLog.created_at >= week_start)
            )
            week_count = week_result.scalar() or 0

            # This month
            month_result = await db_session.execute(
                select(func.count(MemoryLog.id))
                .where(MemoryLog.created_at >= month_start)
            )
            month_count = month_result.scalar() or 0

            # Daily breakdown (last 30 days)
            daily_result = await db_session.execute(
                select(
                    func.date(MemoryLog.created_at).label('date'),
                    func.count(MemoryLog.id).label('count')
                )
                .where(MemoryLog.created_at >= now - timedelta(days=30))
                .group_by(func.date(MemoryLog.created_at))
                .order_by(func.date(MemoryLog.created_at))
            )
            daily_breakdown = [
                {"date": str(row.date), "count": row.count}
                for row in daily_result
            ]

            # Hourly breakdown (last 24 hours)
            hourly_result = await db_session.execute(
                select(
                    extract('hour', MemoryLog.created_at).label('hour'),
                    func.count(MemoryLog.id).label('count')
                )
                .where(MemoryLog.created_at >= now - timedelta(hours=24))
                .group_by(extract('hour', MemoryLog.created_at))
                .order_by(extract('hour', MemoryLog.created_at))
            )
            hourly_breakdown = [
                {"hour": int(row.hour), "count": row.count}
                for row in hourly_result
            ]

            # Calculate 30-day average
            avg_per_day = sum(item["count"] for item in daily_breakdown) / max(len(daily_breakdown), 1)

            return {
                "vectors_added_today": today_count,
                "vectors_added_this_week": week_count,
                "vectors_added_this_month": month_count,
                "avg_vectors_per_day": round(avg_per_day, 2),
                "daily_breakdown": daily_breakdown,
                "hourly_breakdown": hourly_breakdown,
            }
        except Exception as e:
            self.logger.error(f"Error getting ingestion metrics: {e}", exc_info=True)
            return {
                "vectors_added_today": 0,
                "vectors_added_this_week": 0,
                "vectors_added_this_month": 0,
                "error": str(e),
            }

    async def get_search_performance_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics"""
        search_latencies = self.timers.get("search_latency", [])

        if not search_latencies:
            return {
                "avg_search_latency": 0,
                "p50_search_latency": 0,
                "p95_search_latency": 0,
                "p99_search_latency": 0,
                "searches_today": 0,
                "slow_searches": 0,
            }

        # Calculate time-based metrics
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        searches_today = len([
            e for e in self.events.get("vector.searched", [])
            if e.timestamp >= today_start
        ])

        return {
            "avg_search_latency": round(sum(search_latencies) / len(search_latencies), 2),
            "median_search_latency": round(median(search_latencies), 2),
            "p50_search_latency": round(self.get_percentile("search_latency", 50), 2),
            "p95_search_latency": round(self.get_percentile("search_latency", 95), 2),
            "p99_search_latency": round(self.get_percentile("search_latency", 99), 2),
            "searches_today": searches_today,
            "searches_total": self.counters["searches_total"],
            "slow_searches": self.counters["slow_searches"],
            "searches_per_hour": round(self.get_rate("vector.searched", window_seconds=3600), 2),
        }

    async def get_search_quality_metrics(self) -> Dict[str, Any]:
        """Get search quality metrics"""
        if not self.search_results:
            return {
                "avg_similarity": 0,
                "searches_no_results": 0,
                "similarity_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "very_low": 0,
                }
            }

        # Calculate average similarity
        all_similarities = []
        for result in self.search_results:
            all_similarities.extend(result["similarities"])

        avg_similarity = sum(all_similarities) / len(all_similarities) if all_similarities else 0

        # Calculate average results returned
        avg_results = sum(r["result_count"] for r in self.search_results) / len(self.search_results)

        return {
            "avg_similarity": round(avg_similarity, 3),
            "median_similarity": round(median(all_similarities), 3) if all_similarities else 0,
            "avg_results_returned": round(avg_results, 2),
            "searches_no_results": self.counters["searches_no_results"],
            "searches_no_results_rate": round(
                self.counters["searches_no_results"] / max(len(self.search_results), 1) * 100, 2
            ),
            "similarity_distribution": {
                "high": self.counters["similarity_high"],
                "medium": self.counters["similarity_medium"],
                "low": self.counters["similarity_low"],
                "very_low": self.counters["similarity_very_low"],
            }
        }

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage health metrics"""
        try:
            base_path = self.chromadb_client.base_storage_path

            # Calculate total storage size
            total_size = 0
            if os.path.exists(base_path):
                for dirpath, dirnames, filenames in os.walk(base_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except OSError:
                            pass

            total_mb = total_size / (1024 * 1024)

            # Get disk usage
            import shutil
            disk_usage = shutil.disk_usage(base_path if os.path.exists(base_path) else ".")
            disk_total_gb = disk_usage.total / (1024**3)
            disk_free_gb = disk_usage.free / (1024**3)

            # Calculate average bytes per vector
            collection_metrics = await self.get_collection_metrics()
            total_vectors = collection_metrics.get("total_vectors", 0)
            avg_bytes_per_vector = total_size / total_vectors if total_vectors > 0 else 0

            # Storage health status
            utilization = (total_mb / (disk_total_gb * 1024)) * 100 if disk_total_gb > 0 else 0

            if utilization > 90:
                health_status = "critical"
            elif utilization > 75:
                health_status = "warning"
            else:
                health_status = "healthy"

            return {
                "total_storage_mb": round(total_mb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                "disk_used_gb": round((disk_total_gb - disk_free_gb), 2),
                "storage_utilization": round(utilization, 2),
                "avg_bytes_per_vector": round(avg_bytes_per_vector, 2),
                "total_vectors": total_vectors,
                "health_status": health_status,
            }
        except Exception as e:
            self.logger.error(f"Error getting storage metrics: {e}", exc_info=True)
            return {
                "total_storage_mb": 0,
                "error": str(e),
                "health_status": "unknown",
            }

    async def get_snapshot(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get complete metrics snapshot for UI"""
        try:
            collection_metrics = await self.get_collection_metrics()
            ingestion_metrics = await self.get_ingestion_metrics(db_session)
            search_performance = await self.get_search_performance_metrics()
            search_quality = await self.get_search_quality_metrics()
            storage_metrics = await self.get_storage_metrics()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "collections": collection_metrics,
                "ingestion": ingestion_metrics,
                "search_performance": search_performance,
                "search_quality": search_quality,
                "storage": storage_metrics,
                "counters": dict(self.counters),
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics snapshot: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
