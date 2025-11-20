from typing import Optional
from src.modules.qwen_sdk.client import QwenClient

class SXPrefrontalModel:
    """
    SXPrefrontal Model using Qwen SDK.
    """
    
    def __init__(self, cli_path: Optional[str] = None, working_dir: Optional[str] = None):
        """
        Initialize the model with QwenClient.
        
        Args:
            cli_path: Optional path to qwen executable.
            working_dir: Optional working directory.
        """
        self.client = QwenClient(cli_path=cli_path, working_dir=working_dir)
        
    def generate(self, prompt: str, timeout: int = 300) -> str:
        """
        Generate a response for the given prompt using Qwen.
        
        Args:
            prompt: The input prompt.
            timeout: Timeout in seconds.
            
        Returns:
            The generated response.
        """
        return self.client.ask(prompt, timeout=timeout)
