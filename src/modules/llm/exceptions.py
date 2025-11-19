"""Custom exceptions for LLM module"""


class LLMError(Exception):
    """Base exception for all LLM errors"""
    pass


class GeminiAPIError(LLMError):
    """Raised when Gemini API call fails"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class GeminiTimeoutError(LLMError):
    """Raised when Gemini API call times out"""

    def __init__(self, timeout: float):
        self.timeout = timeout
        super().__init__(f"Gemini API call timed out after {timeout} seconds")


class GeminiAuthError(LLMError):
    """Raised when Gemini API authentication fails"""

    def __init__(self, message: str = "Invalid or missing Gemini API key"):
        super().__init__(message)


class GeminiRateLimitError(LLMError):
    """Raised when Gemini API rate limit is exceeded"""

    def __init__(self, message: str = "Gemini API rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)
