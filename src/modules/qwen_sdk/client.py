"""Main client for interacting with Qwen Code CLI"""

import subprocess
import shutil
from typing import Optional
from pathlib import Path

from .exceptions import QwenNotInstalledError, QwenExecutionError


class QwenClient:
    """
    Python client for Qwen Code CLI.
    
    This client wraps the qwen CLI tool and provides a programmatic interface.
    
    Prerequisites:
        - qwen CLI must be installed: npm install -g @qwen-code/qwen-code@latest
        - qwen CLI must be authenticated (run 'qwen' and complete auth)
    
    Example:
        >>> client = QwenClient()
        >>> response = client.ask("Explain what this code does")
        >>> print(response)
    """
    
    def __init__(self, cli_path: Optional[str] = None, working_dir: Optional[str] = None):
        """
        Initialize Qwen CLI client.
        
        Args:
            cli_path: Path to qwen executable. If None, searches in system PATH.
            working_dir: Working directory for CLI commands. Defaults to current directory.
        
        Raises:
            QwenNotInstalledError: If qwen CLI is not found.
        """
        self.cli_path = cli_path or self._find_qwen_cli()
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        if not self.cli_path:
            raise QwenNotInstalledError()
    
    def _find_qwen_cli(self) -> Optional[str]:
        """Find qwen CLI in system PATH."""
        return shutil.which("qwen")
    
    def ask(self, prompt: str, timeout: Optional[int] = 300) -> str:
        """
        Send a prompt to Qwen and get a response.
        
        This is the most basic operation - send a question/command and get the response.
        Uses qwen's non-interactive mode with the -p/--prompt flag.
        
        Args:
            prompt: The question or command to send to Qwen
            timeout: Maximum time to wait for response in seconds (default: 300)
        
        Returns:
            The response from Qwen as a string
        
        Raises:
            QwenExecutionError: If the CLI command fails
        
        Example:
            >>> client = QwenClient()
            >>> response = client.ask("What files are in this directory?")
            >>> print(response)
        """
        try:
            # Use qwen's non-interactive mode with -p flag
            # This is the proper way to use qwen CLI programmatically
            result = subprocess.run(
                [self.cli_path, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.working_dir)
            )
            
            if result.returncode != 0:
                raise QwenExecutionError(
                    command=f"qwen -p '{prompt[:50]}...'",
                    stderr=result.stderr,
                    exit_code=result.returncode
                )
            
            # Parse the output to extract just the response
            return self._parse_response(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise QwenExecutionError(
                command=f"qwen -p '{prompt[:50]}...'",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=-1
            )
    
    def _parse_response(self, raw_output: str) -> str:
        """
        Parse raw CLI output to extract the actual response.
        
        This is a basic parser - we'll improve it as we learn more about the output format.
        """
        # For now, just return the raw output
        # We'll refine this as we test and see what the actual output looks like
        return raw_output.strip()
    
    def check_version(self) -> str:
        """
        Get the installed qwen CLI version.
        
        Returns:
            Version string (e.g., "0.2.3")
        
        Example:
            >>> client = QwenClient()
            >>> print(client.check_version())
            0.2.3
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise QwenExecutionError(
                    command="qwen --version",
                    stderr=result.stderr,
                    exit_code=result.returncode
                )
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise QwenExecutionError(
                command="qwen --version",
                stderr="Command timed out",
                exit_code=-1
            )
    
    def is_available(self) -> bool:
        """
        Check if qwen CLI is available and working.
        
        Returns:
            True if qwen CLI is installed and accessible, False otherwise
        
        Example:
            >>> client = QwenClient()
            >>> if client.is_available():
            ...     print("Qwen is ready!")
        """
        try:
            self.check_version()
            return True
        except (QwenExecutionError, QwenNotInstalledError):
            return False
