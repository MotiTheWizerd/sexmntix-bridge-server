"""
Metric Event Model

Represents a single metric event with timestamp and context.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class MetricEvent:
    """Single metric event"""
    timestamp: datetime
    metric_type: str
    value: float
    tags: Dict[str, Any]
