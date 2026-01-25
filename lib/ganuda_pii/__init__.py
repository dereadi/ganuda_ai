"""
ganuda-pii: Core PII Detection and Protection Library
Cherokee AI Federation - For the Seven Generations

CORE PACKAGE - Shared across all Assist applications

Usage:
    from ganuda_pii import PIIService
    from ganuda_pii.recognizers import veteran  # Domain-specific plugin

    service = PIIService()
    service.add_recognizers(veteran.get_recognizers())
"""

from .service import PIIService, BasePIIService
from .tokenizer import PIITokenizer

__version__ = "1.0.0"
__all__ = ["PIIService", "BasePIIService", "PIITokenizer"]
