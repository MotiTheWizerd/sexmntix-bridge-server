"""
Ingestion metrics collector

Gathers metrics about vector ingestion rates and patterns from the database.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from src.modules.core import Logger
from src.database.models.memory_log import MemoryLog


class IngestionMetricsCollector:
    """Collects vector ingestion metrics from database"""

    def __init__(self, logger: Logger):
        """Initialize ingestion metrics collector

        Args:
            logger: Logger instance
        """
        self.logger = logger

    async def get_ingestion_metrics(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get vector ingestion metrics from database

        Args:
            db_session: Database session

        Returns:
            Dictionary with ingestion counts and breakdowns
        """
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
