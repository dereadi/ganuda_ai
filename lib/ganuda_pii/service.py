"""
Core PII Service - Base implementation for all Assist apps
Cherokee AI Federation - CORE PACKAGE

This is the generic PII service. Domain-specific recognizers
are added via plugins (e.g., veteran, ssdi, healthcare).
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class BasePIIService(ABC):
    """Abstract base for PII services - defines the interface."""

    @abstractmethod
    def analyze(self, text: str) -> List[dict]:
        """Analyze text for PII entities."""
        pass

    @abstractmethod
    def redact(self, text: str) -> str:
        """Redact PII from text."""
        pass

    @abstractmethod
    def tokenize(self, text: str, user_id: str) -> Tuple[str, Dict]:
        """Tokenize PII for vault storage."""
        pass


class PIIService(BasePIIService):
    """
    Core PII Detection and Protection Service.

    Default entities detected:
    - US_SSN
    - PHONE_NUMBER
    - EMAIL_ADDRESS
    - LOCATION
    - DATE_TIME
    - US_DRIVER_LICENSE
    - CREDIT_CARD
    - US_BANK_NUMBER

    Add domain-specific recognizers via add_recognizers().
    """

    # Standard PII entities across all domains
    DEFAULT_SENSITIVE_ENTITIES = [
        "US_SSN",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "LOCATION",
        "DATE_TIME",
        "US_DRIVER_LICENSE",
        "CREDIT_CARD",
        "US_BANK_NUMBER",
    ]

    # Entities detected but preserved (contextually important)
    DEFAULT_PRESERVE_ENTITIES = [
        "PERSON",
    ]

    def __init__(
        self,
        sensitive_entities: Optional[List[str]] = None,
        preserve_entities: Optional[List[str]] = None,
        token_salt: Optional[str] = None
    ):
        """
        Initialize PII Service.

        Args:
            sensitive_entities: Override default sensitive entities
            preserve_entities: Override default preserve entities
            token_salt: Salt for tokenization (defaults to env var or fallback)
        """
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        self.sensitive_entities = sensitive_entities or self.DEFAULT_SENSITIVE_ENTITIES.copy()
        self.preserve_entities = preserve_entities or self.DEFAULT_PRESERVE_ENTITIES.copy()

        # Token salt from parameter, env, or default
        import os
        self.token_salt = token_salt or os.environ.get(
            "PII_TOKEN_SALT",
            "cherokee-ai-federation"
        )

        # Track custom recognizers for introspection
        self._custom_recognizers: List[str] = []

    def add_recognizers(self, recognizers: List[PatternRecognizer]) -> None:
        """
        Add domain-specific recognizers (plugin system).

        Args:
            recognizers: List of Presidio PatternRecognizer instances

        Example:
            from ganuda_pii.recognizers import veteran
            service.add_recognizers(veteran.get_recognizers())
        """
        for recognizer in recognizers:
            self.analyzer.registry.add_recognizer(recognizer)
            self._custom_recognizers.append(recognizer.name)

            # Auto-add the entity type to sensitive list if not present
            if hasattr(recognizer, 'supported_entities'):
                for entity in recognizer.supported_entities:
                    if entity not in self.sensitive_entities:
                        self.sensitive_entities.append(entity)

    def add_entity(self, entity_type: str, sensitive: bool = True) -> None:
        """Add an entity type to detection list."""
        target = self.sensitive_entities if sensitive else self.preserve_entities
        if entity_type not in target:
            target.append(entity_type)

    def analyze(self, text: str) -> List[dict]:
        """
        Analyze text for PII entities.

        Returns:
            List of dicts with: entity_type, start, end, score, text
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities + self.preserve_entities
        )
        return [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text": text[r.start:r.end]
            }
            for r in results
        ]

    def redact(self, text: str, placeholder: str = "<REDACTED>") -> str:
        """
        Redact PII for safe logging/storage.

        Args:
            text: Input text
            placeholder: Replacement text (default: <REDACTED>)

        Returns:
            Text with PII replaced by placeholder
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities
        )

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": placeholder})
            }
        )
        return anonymized.text

    # Alias for backward compatibility
    def redact_for_logging(self, text: str) -> str:
        """Alias for redact() - backward compatibility."""
        return self.redact(text)

    def tokenize(self, text: str, user_id: str) -> Tuple[str, Dict[str, dict]]:
        """
        Tokenize PII for vault storage.

        Args:
            text: Input text
            user_id: User identifier for deterministic tokens

        Returns:
            Tuple of (tokenized_text, token_mapping)
            Token mapping should be stored in secure vault only.
        """
        from .tokenizer import PIITokenizer
        tokenizer = PIITokenizer(self.token_salt)

        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities
        )

        return tokenizer.tokenize(text, results, user_id)

    # Alias for backward compatibility
    def tokenize_for_vault(self, text: str, user_id: str) -> Tuple[str, Dict[str, dict]]:
        """Alias for tokenize() - backward compatibility."""
        return self.tokenize(text, user_id)

    def get_recognizer_names(self) -> List[str]:
        """Return list of custom recognizers added."""
        return self._custom_recognizers.copy()

    def get_entity_types(self) -> Dict[str, List[str]]:
        """Return configured entity types."""
        return {
            "sensitive": self.sensitive_entities.copy(),
            "preserve": self.preserve_entities.copy()
        }
