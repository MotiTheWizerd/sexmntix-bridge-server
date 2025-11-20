"""
Qwen CLI SDK - Python wrapper for Qwen Code CLI

This SDK provides a programmatic Python interface to interact with the Qwen Code CLI tool.
It assumes that the qwen CLI is already installed and authenticated.
"""

from .client import QwenClient
from .exceptions import QwenCLIError, QwenNotInstalledError, QwenExecutionError

__version__ = "0.1.0"
__all__ = [
    "QwenClient",
    "QwenCLIError",
    "QwenNotInstalledError",
    "QwenExecutionError",
]
