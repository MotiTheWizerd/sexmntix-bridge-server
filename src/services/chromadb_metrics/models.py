"""
Data models for ChromaDB metrics

Defines structured data types for metric events and responses.
"""

from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class MetricEvent:
    """Single metric event with timestamp, type, value, and tags"""
    timestamp: datetime
    metric_type: str
    value: float
    tags: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return asdict(self)
