"""
Storage Metrics

Data transfer object for storage operation metrics and performance statistics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class StorageMetrics:
    """
    Performance metrics for storage operations.

    Attributes:
        operation: Name of the operation (store, search, delete, etc.)
        duration_ms: Operation duration in milliseconds
        cached: Whether result was from cache
        memory_id: Memory identifier (if applicable)
        collection_name: Collection name used
        vector_dimensions: Embedding vector dimensions
        timestamp: Operation timestamp
        error: Error message if operation failed
        metadata: Additional operation-specific metadata
    """

    operation: str
    """Name of the operation"""

    duration_ms: float
    """Operation duration in milliseconds"""

    cached: bool = False
    """Whether result was from cache"""

    memory_id: Optional[str] = None
    """Memory identifier (if applicable)"""

    collection_name: Optional[str] = None
    """Collection name used"""

    vector_dimensions: Optional[int] = None
    """Embedding vector dimensions"""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    """Operation timestamp"""

    error: Optional[str] = None
    """Error message if operation failed"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional operation-specific metadata"""

    def __post_init__(self):
        """Validate metrics data."""
        if not self.operation or not self.operation.strip():
            raise ValueError("operation cannot be empty")

        if self.duration_ms < 0:
            raise ValueError(f"duration_ms cannot be negative, got {self.duration_ms}")

        if self.vector_dimensions is not None and self.vector_dimensions < 1:
            raise ValueError(
                f"vector_dimensions must be at least 1, got {self.vector_dimensions}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "cached": self.cached,
            "memory_id": self.memory_id,
            "collection_name": self.collection_name,
            "vector_dimensions": self.vector_dimensions,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "metadata": self.metadata,
        }

    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.error is None

    def is_cached(self) -> bool:
        """Check if result was from cache."""
        return self.cached

    def add_metadata(self, key: str, value: Any) -> "StorageMetrics":
        """
        Add additional metadata to metrics.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for method chaining
        """
        self.metadata[key] = value
        return self
