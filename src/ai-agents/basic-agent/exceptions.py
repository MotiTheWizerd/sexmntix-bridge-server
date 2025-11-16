"""Custom exceptions for BasicAgent module"""


class BasicAgentError(Exception):
    """Base exception for BasicAgent errors"""
    pass


class GeminiAPIError(BasicAgentError):
    """Raised when Gemini API call fails"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class GeminiTimeoutError(BasicAgentError):
    """Raised when Gemini API call times out"""

    def __init__(self, timeout: float):
        self.timeout = timeout
        super().__init__(f"Gemini API call timed out after {timeout} seconds")


class GeminiAuthError(BasicAgentError):
    """Raised when Gemini API authentication fails"""

    def __init__(self, message: str = "Invalid or missing Gemini API key"):
        super().__init__(message)


class GeminiRateLimitError(BasicAgentError):
    """Raised when Gemini API rate limit is exceeded"""

    def __init__(self, message: str = "Gemini API rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)
