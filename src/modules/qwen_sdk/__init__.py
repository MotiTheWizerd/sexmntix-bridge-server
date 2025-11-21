"""
Qwen SDK - Direct API client for Qwen models

This SDK makes direct HTTP requests to Qwen/OpenAI-compatible APIs,
bypassing the qwen CLI entirely for much faster performance.
"""

from .client import QwenClient
from .exceptions import QwenAPIError, QwenConfigError, QwenAuthError, QwenRequestError

__version__ = "0.2.0"
__all__ = [
    "QwenClient",
    "QwenAPIError",
    "QwenConfigError",
    "QwenAuthError",
    "QwenRequestError",
]
