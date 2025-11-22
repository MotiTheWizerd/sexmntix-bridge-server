"""
Threshold Preset Enum

Provides preset similarity thresholds for different search scenarios.
"""

from enum import Enum


class ThresholdPreset(str, Enum):
    """
    Preset similarity thresholds for different search use cases.

    Use cases:
    - HIGH_PRECISION: When you need highly relevant results only (0.7 threshold)
    - FILTERED: Balanced precision/recall for filtered searches (0.6 threshold)
    - DISCOVERY: Broad exploration mode for finding related content (0.3 threshold)
    """

    HIGH_PRECISION = "high_precision"
    """High precision mode - only highly relevant results (threshold: 0.7)"""

    FILTERED = "filtered"
    """Balanced mode for filtered searches (threshold: 0.6)"""

    DISCOVERY = "discovery"
    """Discovery mode - broad exploration (threshold: 0.3)"""

    @property
    def threshold(self) -> float:
        """
        Get the similarity threshold for this preset.

        Returns:
            Similarity threshold value (0.0 to 1.0)
        """
        return THRESHOLD_VALUES[self]

    @classmethod
    def from_string(cls, value: str) -> "ThresholdPreset":
        """
        Create preset from string value.

        Args:
            value: Preset name string

        Returns:
            ThresholdPreset enum value

        Raises:
            ValueError: If value is not a valid preset
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = [p.value for p in cls]
            raise ValueError(
                f"Invalid threshold preset: {value}. "
                f"Valid values: {', '.join(valid_values)}"
            )


# Mapping of presets to threshold values
THRESHOLD_VALUES = {
    ThresholdPreset.HIGH_PRECISION: 0.7,
    ThresholdPreset.FILTERED: 0.6,
    ThresholdPreset.DISCOVERY: 0.3,
}
