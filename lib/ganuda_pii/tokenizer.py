"""
PII Tokenizer - Generates deterministic tokens for vault storage
Cherokee AI Federation - CORE PACKAGE

Tokens are deterministic: same PII + same user = same token
This allows deduplication while maintaining security.
"""

import hashlib
from typing import Dict, List, Tuple, Any


class PIITokenizer:
    """
    Generates secure, deterministic tokens for PII values.

    Tokens are:
    - Deterministic: Same input produces same token
    - User-scoped: Different users get different tokens for same PII
    - Salted: Requires salt to reverse (stored separately)
    """

    def __init__(self, salt: str):
        """
        Initialize tokenizer with salt.

        Args:
            salt: Secret salt for token generation
        """
        self.salt = salt

    def generate_token(
        self,
        value: str,
        user_id: str,
        entity_type: str,
        token_length: int = 16
    ) -> str:
        """
        Generate deterministic token for a PII value.

        Args:
            value: The PII value to tokenize
            user_id: User identifier
            entity_type: Type of PII (e.g., US_SSN)
            token_length: Length of token (default 16 chars)

        Returns:
            Hexadecimal token string
        """
        token_input = f"{self.salt}:{user_id}:{entity_type}:{value}"
        full_hash = hashlib.sha256(token_input.encode()).hexdigest()
        return full_hash[:token_length]

    def tokenize(
        self,
        text: str,
        analyzer_results: List[Any],
        user_id: str
    ) -> Tuple[str, Dict[str, dict]]:
        """
        Replace all PII in text with tokens.

        Args:
            text: Original text
            analyzer_results: Results from Presidio analyzer
            user_id: User identifier for token scoping

        Returns:
            Tuple of:
            - tokenized_text: Text with PII replaced by <TOKEN:xxx>
            - token_map: Dict mapping tokens to original values
        """
        token_map = {}
        tokenized_text = text

        # Process in reverse order to maintain string positions
        sorted_results = sorted(
            analyzer_results,
            key=lambda x: x.start,
            reverse=True
        )

        for result in sorted_results:
            original = text[result.start:result.end]
            token = self.generate_token(
                value=original,
                user_id=user_id,
                entity_type=result.entity_type
            )

            token_map[token] = {
                "original": original,
                "entity_type": result.entity_type,
                "score": result.score
            }

            tokenized_text = (
                tokenized_text[:result.start] +
                f"<TOKEN:{token}>" +
                tokenized_text[result.end:]
            )

        return tokenized_text, token_map

    def detokenize(self, text: str, token_map: Dict[str, dict]) -> str:
        """
        Replace tokens with original values.

        Args:
            text: Tokenized text
            token_map: Mapping from tokens to original values

        Returns:
            Original text with PII restored
        """
        result = text
        for token, data in token_map.items():
            placeholder = f"<TOKEN:{token}>"
            result = result.replace(placeholder, data["original"])
        return result
