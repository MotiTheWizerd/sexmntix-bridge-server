"""
Text validation component.

Responsible for validating and cleaning text inputs for embedding generation.
"""

from typing import List
from ....exceptions import InvalidTextError


class TextValidator:
    """
    Validates and cleans text inputs for embedding generation.
    
    Single responsibility: Ensure text inputs are valid and properly formatted.
    """
    
    def validate_single(self, text: str) -> str:
        """
        Validate and clean a single text input.
        
        Args:
            text: Text to validate
            
        Returns:
            Cleaned text (stripped of whitespace)
            
        Raises:
            InvalidTextError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise InvalidTextError("Text cannot be empty")
        return text.strip()
    
    def validate_batch(self, texts: List[str]) -> List[str]:
        """
        Validate and clean a batch of text inputs.
        
        Args:
            texts: List of texts to validate
            
        Returns:
            List of cleaned texts (stripped, empty texts removed)
            
        Raises:
            InvalidTextError: If texts list is empty or contains no valid texts
        """
        if not texts:
            raise InvalidTextError("Texts list cannot be empty")
        
        cleaned = [t.strip() for t in texts if t.strip()]
        
        if not cleaned:
            raise InvalidTextError("No valid texts provided")
        
        return cleaned
