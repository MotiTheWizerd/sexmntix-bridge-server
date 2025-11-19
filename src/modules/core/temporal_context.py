"""
Temporal Context Utility

Calculates temporal context fields from a date:
- date_iso: ISO format date string
- year, month, week_number: Extracted from date
- quarter: Quarter string (e.g., "2025-Q1")
- time_period: Relative time period classification
"""

from datetime import datetime, date
from typing import Dict, Any


class TemporalContextCalculator:
    """Calculate temporal context fields from a date"""

    @staticmethod
    def calculate_week_number(dt: date) -> int:
        """
        Calculate ISO week number for a date.
        
        Args:
            dt: Date object
            
        Returns:
            ISO week number (1-53)
        """
        return dt.isocalendar()[1]

    @staticmethod
    def calculate_quarter(dt: date) -> str:
        """
        Calculate quarter string (e.g., "2025-Q1").
        
        Args:
            dt: Date object
            
        Returns:
            Quarter string in format "YYYY-QN"
        """
        year = dt.year
        quarter = (dt.month - 1) // 3 + 1
        return f"{year}-Q{quarter}"

    @staticmethod
    def calculate_time_period(dt: date, reference_date: date = None) -> str:
        """
        Calculate relative time period classification.
        
        Thresholds:
        - recent: < 7 days ago
        - last-week: 7-14 days ago
        - last-month: 14-30 days ago
        - archived: > 30 days ago
        
        Args:
            dt: Date to classify
            reference_date: Reference date (defaults to today)
            
        Returns:
            Time period string: "recent" | "last-week" | "last-month" | "archived"
        """
        if reference_date is None:
            reference_date = date.today()
        
        days_diff = (reference_date - dt).days
        
        if days_diff < 7:
            return "recent"
        elif days_diff < 14:
            return "last-week"
        elif days_diff < 30:
            return "last-month"
        else:
            return "archived"

    @classmethod
    def calculate_temporal_context(
        cls,
        date_value: date | datetime | str,
        reference_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate all temporal context fields from a date.
        
        Args:
            date_value: Date as date, datetime, or ISO string
            reference_date: Reference date for time_period calculation (defaults to today)
            
        Returns:
            Dictionary with temporal context fields:
            {
                "date_iso": "2025-01-15",
                "year": 2025,
                "month": 1,
                "week_number": 3,
                "quarter": "2025-Q1",
                "time_period": "recent"
            }
        """
        # Convert to date object
        if isinstance(date_value, str):
            # Try parsing ISO format
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except ValueError:
                # Try date-only format
                dt = datetime.strptime(date_value, "%Y-%m-%d").date()
        elif isinstance(date_value, datetime):
            dt = date_value.date()
        elif isinstance(date_value, date):
            dt = date_value
        else:
            raise ValueError(f"Invalid date type: {type(date_value)}")

        return {
            "date_iso": dt.isoformat(),
            "year": dt.year,
            "month": dt.month,
            "week_number": cls.calculate_week_number(dt),
            "quarter": cls.calculate_quarter(dt),
            "time_period": cls.calculate_time_period(dt, reference_date)
        }

