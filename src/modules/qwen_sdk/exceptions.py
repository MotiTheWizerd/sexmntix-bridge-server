"""Custom exceptions for Qwen CLI SDK"""


class QwenCLIError(Exception):
    """Base exception for all Qwen CLI SDK errors"""
    pass


class QwenNotInstalledError(QwenCLIError):
    """Raised when qwen CLI is not found in the system"""
    
    def __init__(self):
        super().__init__(
            "Qwen CLI not found. Please install it first:\n"
            "  npm install -g @qwen-code/qwen-code@latest\n"
            "Or check: https://github.com/QwenLM/qwen-code"
        )


class QwenExecutionError(QwenCLIError):
    """Raised when qwen CLI command execution fails"""
    
    def __init__(self, command: str, stderr: str, exit_code: int):
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code
        super().__init__(
            f"Qwen CLI command failed (exit code {exit_code}):\n"
            f"Command: {command}\n"
            f"Error: {stderr}"
        )
