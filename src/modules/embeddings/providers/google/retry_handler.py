"""
Retry Handler

Single Responsibility: Implement retry logic with exponential backoff.

This component provides a reusable retry mechanism that can be used across
different API operations.
"""

import asyncio
from typing import Callable, TypeVar, Any
from src.modules.embeddings.exceptions import ProviderError

T = TypeVar('T')


class RetryHandler:
    """
    Handles retry logic with exponential backoff.

    Provides configurable retry behavior for API calls.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        provider_name: str = "unknown"
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay_seconds: Base delay between retries (exponentially increases)
            provider_name: Provider name for error messages
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay_seconds
        self.provider_name = provider_name

    async def execute_with_retry(
        self,
        operation: Callable[[], Any],
        error_handler: Callable[[Exception, int, bool], None] = None
    ) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation: Async callable to execute
            error_handler: Optional callback to handle exceptions
                          Called with (exception, attempt_number, is_final_attempt)

        Returns:
            Result from the operation

        Raises:
            ProviderError: If max retries exceeded or unrecoverable error
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                result = await operation()
                return result

            except Exception as e:
                last_exception = e
                is_final_attempt = (attempt == self.max_retries - 1)

                # Call error handler if provided
                if error_handler:
                    try:
                        error_handler(e, attempt, is_final_attempt)
                    except Exception as handler_exception:
                        # Error handler raised an exception (likely final attempt)
                        raise handler_exception

                # If not final attempt, sleep with exponential backoff
                if not is_final_attempt:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # Should never reach here due to raises in loop, but just in case
        raise ProviderError(
            self.provider_name,
            f"Max retries ({self.max_retries}) exceeded. Last error: {str(last_exception)}",
            last_exception
        )

    def calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay for given attempt.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        return self.retry_delay * (2 ** attempt)
