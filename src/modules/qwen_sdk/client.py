"""
Direct API client for Qwen models

This client makes direct HTTP requests to Qwen/OpenAI-compatible APIs,
bypassing the qwen CLI for much faster performance (< 1 second vs 20+ seconds).
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import http.client
import urllib.parse

from .exceptions import QwenAPIError, QwenConfigError, QwenAuthError, QwenRequestError


class QwenClient:
    """
    Direct API client for Qwen models.
    
    This client makes HTTP requests directly to Qwen/OpenAI-compatible APIs,
    completely bypassing the qwen CLI for much faster performance.
    
    Configuration (in order of priority):
        1. Constructor parameters
        2. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
        3. .env file in current directory
    
    Example:
        >>> client = QwenClient(
        ...     api_key="your-api-key",
        ...     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        ...     model="qwen3-coder-plus"
        ... )
        >>> response = client.ask("What is Python?")
        >>> print(response)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ):
        """
        Initialize Qwen API client.
        
        Args:
            api_key: API key for authentication. If None, reads from OPENAI_API_KEY env var.
            base_url: Base URL for API. If None, reads from OPENAI_BASE_URL env var.
            model: Model name. If None, reads from OPENAI_MODEL env var.
            timeout: Request timeout in seconds (default: 60)
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
        
        Raises:
            QwenConfigError: If required configuration is missing
        """
        # Load from .env file if it exists
        self._load_env_file()
        
        # Get configuration with priority: params > env vars > CLI credentials
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("OPENAI_MODEL")
        
        # Try to load from CLI credentials if no API key provided
        if not self.api_key:
            cli_creds = self._load_cli_credentials()
            if cli_creds:
                self.api_key = cli_creds.get("access_token")
                
                # Use resource_url from credentials if available, otherwise default to DashScope
                if not self.base_url:
                    self.base_url = cli_creds.get("resource_url") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
                
                # Use Qwen default model if not specified
                if not self.model:
                    self.model = "qwen3-coder-plus"

        # Validate required config
        if not self.api_key:
            raise QwenConfigError(
                "API key is required. Set it via:\n"
                "  1. QwenClient(api_key='...')\n"
                "  2. OPENAI_API_KEY environment variable\n"
                "  3. .env file with OPENAI_API_KEY=...\n"
                "  4. Login via CLI: 'qwen auth login'"
            )
        
        if not self.base_url:
            raise QwenConfigError(
                "Base URL is required. Set it via:\n"
                "  1. QwenClient(base_url='...')\n"
                "  2. OPENAI_BASE_URL environment variable\n"
                "  3. .env file with OPENAI_BASE_URL=..."
            )
        
        if not self.model:
            raise QwenConfigError(
                "Model name is required. Set it via:\n"
                "  1. QwenClient(model='...')\n"
                "  2. OPENAI_MODEL environment variable\n"
                "  3. .env file with OPENAI_MODEL=..."
            )
        
        # Request settings
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Parse base URL
        self._parse_base_url()
    
    def _load_cli_credentials(self) -> Optional[Dict[str, Any]]:
        """Load credentials from Qwen CLI storage (~/.qwen/oauth_creds.json)"""
        try:
            home_dir = Path.home()
            creds_path = home_dir / ".qwen" / "oauth_creds.json"
            
            if not creds_path.exists():
                return None
                
            with open(creds_path, "r") as f:
                creds = json.load(f)
                
            # Check expiry
            if "expiry_date" in creds:
                expiry = creds["expiry_date"]
                # Add 5 minute buffer
                if time.time() * 1000 > expiry - (5 * 60 * 1000):
                    print("⚠️  Warning: Qwen CLI token is expired or expiring soon.")
                    return None
            
            return creds
            
        except Exception:
            return None

    def _load_env_file(self):
        """Load .env file if it exists in current directory"""
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and key not in os.environ:
                            os.environ[key] = value
    
    def _parse_base_url(self):
        """Parse base URL into host, port, and path components"""
        # Normalize URL (add scheme and /v1 if missing)
        url = self.base_url.strip()
        if not url.startswith("http"):
            url = f"https://{url}"
            
        if not url.endswith("/v1") and not url.endswith("/v1/"):
            url = f"{url}/v1"
            
        self.base_url = url
        
        parsed = urllib.parse.urlparse(self.base_url)
        self.scheme = parsed.scheme or "https"
        self.host = parsed.netloc
        self.base_path = parsed.path
        
        # Handle port
        if ":" in self.host:
            self.host, port_str = self.host.rsplit(":", 1)
            self.port = int(port_str)
        else:
            self.port = 443 if self.scheme == "https" else 80
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to Qwen and get a response.
        
        This makes a direct API call, bypassing the CLI entirely.
        Much faster than CLI approach (< 1 second vs 20+ seconds).
        
        Args:
            prompt: The question or command to send
            system_prompt: Optional system prompt to set context
            max_tokens: Override default max_tokens for this request
            temperature: Override default temperature for this request
        
        Returns:
            The response text from Qwen
        
        Raises:
            QwenRequestError: If the API request fails
            QwenAuthError: If authentication fails
        
        Example:
            >>> client = QwenClient()
            >>> response = client.ask("What is 2+2?")
            >>> print(response)  # "2+2 equals 4"
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request body
        request_body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
        }
        
        # Make API request
        response_data = self._make_request("/chat/completions", request_body)
        
        # Extract response text
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise QwenAPIError(f"Unexpected API response format: {e}")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to the API.
        
        Args:
            endpoint: API endpoint (e.g., "/chat/completions")
            data: Request body data
        
        Returns:
            Response data as dictionary
        
        Raises:
            QwenRequestError: If request fails
            QwenAuthError: If authentication fails
        """
        # Build full path
        path = self.base_path.rstrip("/") + endpoint
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "QwenSDK-Python/0.2.0",
        }
        
        body = json.dumps(data).encode("utf-8")
        
        # Make request
        try:
            if self.scheme == "https":
                conn = http.client.HTTPSConnection(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
            else:
                conn = http.client.HTTPConnection(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
            
            conn.request("POST", path, body, headers)
            response = conn.getresponse()
            response_body = response.read().decode("utf-8")
            
            # Handle response
            if response.status == 401:
                raise QwenAuthError("Invalid API key")
            
            if response.status != 200:
                try:
                    error_data = json.loads(response_body)
                    error_msg = error_data.get("error", {}).get("message", response_body)
                except:
                    error_msg = response_body
                raise QwenRequestError(response.status, error_msg)
            
            # Parse response
            try:
                return json.loads(response_body)
            except json.JSONDecodeError as e:
                # Truncate body if too long
                preview = response_body[:200] + "..." if len(response_body) > 200 else response_body
                raise QwenAPIError(f"Invalid JSON response: {e}. Body: {preview}")
            
        except http.client.HTTPException as e:
            raise QwenRequestError(0, f"HTTP error: {e}")
        except OSError as e:
            raise QwenRequestError(0, f"Network error: {e}")
        finally:
            conn.close()
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a multi-turn conversation to Qwen.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Example: [{"role": "user", "content": "Hello"}]
            max_tokens: Override default max_tokens
            temperature: Override default temperature
        
        Returns:
            The response text from Qwen
        
        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant"},
            ...     {"role": "user", "content": "What is Python?"},
            ... ]
            >>> response = client.chat(messages)
        """
        request_body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
        }
        
        response_data = self._make_request("/chat/completions", request_body)
        
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise QwenAPIError(f"Unexpected API response format: {e}")
