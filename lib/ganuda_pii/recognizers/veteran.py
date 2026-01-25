"""
Veteran-specific PII recognizers for VetAssist
Cherokee AI Federation - DOMAIN PLUGIN

This module contains recognizers optimized for veteran data:
- Enhanced SSN detection with military context
- VA File Number detection
- Military service number patterns

Usage:
    from ganuda_pii import PIIService
    from ganuda_pii.recognizers import veteran

    service = PIIService()
    service.add_recognizers(veteran.get_recognizers())
"""

from presidio_analyzer import PatternRecognizer, Pattern
from typing import List


def get_recognizers() -> List[PatternRecognizer]:
    """
    Get all veteran-specific recognizers.

    Returns:
        List of PatternRecognizer instances
    """
    return [
        _create_ssn_recognizer(),
        _create_va_file_recognizer(),
        _create_service_number_recognizer(),
    ]


def _create_ssn_recognizer() -> PatternRecognizer:
    """
    Enhanced SSN recognizer with veteran context.

    Higher confidence when near veteran-related keywords.
    """
    return PatternRecognizer(
        supported_entity="US_SSN",
        name="VeteranSSNRecognizer",
        patterns=[
            Pattern(
                name="SSN_DASHED",
                regex=r"\b([0-9]{3})-([0-9]{2})-([0-9]{4})\b",
                score=0.85
            ),
            Pattern(
                name="SSN_SPACED",
                regex=r"\b([0-9]{3}) ([0-9]{2}) ([0-9]{4})\b",
                score=0.85
            ),
            Pattern(
                name="SSN_CONTINUOUS",
                regex=r"\b([0-9]{9})\b",
                score=0.4  # Lower for bare 9-digit (could be other IDs)
            ),
        ],
        context=["ssn", "social", "security", "number", "veteran", "va", "military"]
    )


def _create_va_file_recognizer() -> PatternRecognizer:
    """
    VA File Number recognizer.

    VA file numbers are typically 7-9 digits, sometimes prefixed with 'C'.
    Context words boost confidence.
    """
    return PatternRecognizer(
        supported_entity="VA_FILE_NUMBER",
        name="VAFileNumberRecognizer",
        patterns=[
            Pattern(
                name="VA_FILE_WITH_PREFIX",
                regex=r"\b[Cc][0-9]{7,9}\b",
                score=0.75
            ),
            Pattern(
                name="VA_FILE_PLAIN",
                regex=r"\b[0-9]{7,9}\b",
                score=0.5  # Lower without prefix
            ),
        ],
        context=["va", "file", "number", "claim", "veteran", "benefits", "c-file"]
    )


def _create_service_number_recognizer() -> PatternRecognizer:
    """
    Military Service Number recognizer.

    Pre-1974 service numbers varied by branch. Common patterns:
    - Army: 2 letters + 7 digits (RA1234567)
    - Navy: 6-9 digits
    - Air Force: AF + 7 digits
    """
    return PatternRecognizer(
        supported_entity="MILITARY_SERVICE_NUMBER",
        name="MilitaryServiceNumberRecognizer",
        patterns=[
            Pattern(
                name="ARMY_SERVICE_NUMBER",
                regex=r"\b[A-Z]{2}[0-9]{7}\b",
                score=0.7
            ),
            Pattern(
                name="AIR_FORCE_SERVICE_NUMBER",
                regex=r"\bAF[0-9]{7}\b",
                score=0.8
            ),
        ],
        context=["service", "number", "military", "army", "navy", "air force", "veteran"]
    )


# Entity types exported by this plugin
ENTITY_TYPES = [
    "US_SSN",           # Enhanced, not new
    "VA_FILE_NUMBER",   # New entity type
    "MILITARY_SERVICE_NUMBER",  # New entity type
]
