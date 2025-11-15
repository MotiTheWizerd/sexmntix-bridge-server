"""
Percentile Calculator

Calculates percentile values from a list of values.
"""

from typing import List


class PercentileCalculator:
    """Calculates percentile values."""

    @staticmethod
    def calculate(values: List[float], percentile: int) -> float:
        """
        Calculate percentile for a list of values.

        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        sorted_values = sorted(values)
        if not sorted_values:
            return 0.0
        idx = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]
