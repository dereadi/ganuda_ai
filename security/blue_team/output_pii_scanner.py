"""
Output PII Scanner - AI Blue Team Phase 5

Scans outgoing text for Personally Identifiable Information (PII)
and either blocks or redacts the output before delivery to the user.

Created: 2026-02-02
"""

import re
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

LOG_DIR = Path("/ganuda/logs/security")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("blue_team.pii_scanner")

_fh = logging.FileHandler(LOG_DIR / "pii_detections.log")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_fh)


@dataclass
class PIIFinding:
    """Represents a single PII detection finding."""
    pii_type: str
    pattern: str
    position: tuple[int, int]
    redacted_preview: str


# PII detection patterns
PII_PATTERNS = [
    {
        "type": "SSN",
        "pattern": re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b"),
        "description": "Social Security Number (XXX-XX-XXXX)",
        "redact": lambda m: f"***-**-{m.group(3)[-4:]}",
    },
    {
        "type": "SSN_NO_DASH",
        "pattern": re.compile(r"\b(\d{9})\b"),
        "description": "Social Security Number without dashes",
        "validate": lambda m: _is_plausible_ssn(m.group(0)),
        "redact": lambda m: f"*****{m.group(0)[-4:]}",
    },
    {
        "type": "PHONE_US",
        "pattern": re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "description": "US Phone Number",
        "redact": lambda m: f"(***) ***-{m.group(0)[-4:]}",
    },
    {
        "type": "EMAIL",
        "pattern": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "description": "Email Address",
        "redact": lambda m: f"{m.group(0)[0]}***@{m.group(0).split('@')[1]}",
    },
    {
        "type": "CREDIT_CARD",
        "pattern": re.compile(
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
        ),
        "description": "Credit Card Number",
        "validate": lambda m: _luhn_check(re.sub(r"[-\s]", "", m.group(0))),
        "redact": lambda m: f"****-****-****-{re.sub(r'[-\\s]', '', m.group(0))[-4:]}",
    },
    {
        "type": "VA_ICN",
        "pattern": re.compile(r"\b\d{10}V\d{6}\b"),
        "description": "VA Integration Control Number",
        "redact": lambda m: f"**********V******",
    },
    {
        "type": "VA_FILE_NUMBER",
        "pattern": re.compile(r"\bVA\s*(?:file\s*(?:number|#|no\.?))?\s*[:.]?\s*(\d{8,9})\b", re.IGNORECASE),
        "description": "VA File Number",
        "redact": lambda m: f"VA File: *****{m.group(1)[-4:]}",
    },
    {
        "type": "DOB",
        "pattern": re.compile(
            r"\b(?:DOB|date\s+of\s+birth|born)\s*[:.]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b",
            re.IGNORECASE,
        ),
        "description": "Date of Birth",
        "redact": lambda m: "DOB: **/**/****",
    },
]


def _is_plausible_ssn(digits: str) -> bool:
    """Check if a 9-digit string could plausibly be an SSN."""
    if len(digits) != 9:
        return False
    # SSNs don't start with 9, 000, or have 00 in middle group or 0000 at end
    area = int(digits[:3])
    group = int(digits[3:5])
    serial = int(digits[5:])
    if area == 0 or area >= 900:
        return False
    if group == 0:
        return False
    if serial == 0:
        return False
    return True


def _luhn_check(number: str) -> bool:
    """Validate credit card number using Luhn algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def scan_output(text: str) -> tuple[bool, list[dict]]:
    """
    Scan output text for PII.

    Args:
        text: The output text to scan.

    Returns:
        Tuple of (has_pii, findings)
        - has_pii: True if any PII was detected
        - findings: List of finding dicts with keys:
            type, pattern, position, redacted_preview
    """
    if not text:
        return (False, [])

    findings = []

    for pii_def in PII_PATTERNS:
        for match in pii_def["pattern"].finditer(text):
            # Run optional validation function
            validator = pii_def.get("validate")
            if validator and not validator(match):
                continue

            redacted = pii_def["redact"](match)

            # Build context preview (30 chars before and after)
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            preview_before = text[start:match.start()]
            preview_after = text[match.end():end]
            redacted_preview = f"...{preview_before}{redacted}{preview_after}..."

            finding = PIIFinding(
                pii_type=pii_def["type"],
                pattern=pii_def["description"],
                position=(match.start(), match.end()),
                redacted_preview=redacted_preview,
            )
            findings.append(asdict(finding))

    has_pii = len(findings) > 0

    if has_pii:
        logger.warning(
            "PII DETECTED | count=%d | types=%s | text_len=%d",
            len(findings),
            ",".join(set(f["pii_type"] for f in findings)),
            len(text),
        )

    return (has_pii, findings)


def redact_output(text: str) -> str:
    """
    Redact all detected PII from the output text.

    Args:
        text: The output text to redact.

    Returns:
        Text with all PII replaced by redaction markers.
    """
    result = text

    for pii_def in PII_PATTERNS:
        def _replace(match, _def=pii_def):
            validator = _def.get("validate")
            if validator and not validator(match):
                return match.group(0)
            return _def["redact"](match)

        result = pii_def["pattern"].sub(_replace, result)

    return result


if __name__ == "__main__":
    # Quick self-test
    test_texts = [
        "The veteran's SSN is 123-45-6789 and their phone is (555) 123-4567.",
        "Contact email: john.doe@example.com",
        "VA ICN: 1234567890V123456",
        "This text has no PII at all.",
        "Credit card: 4111-1111-1111-1111",
    ]
    print("Output PII Scanner - Self Test")
    print("=" * 50)
    for text in test_texts:
        has_pii, findings = scan_output(text)
        print(f"Has PII: {has_pii} | Findings: {len(findings)}")
        for f in findings:
            print(f"  [{f['pii_type']}] {f['redacted_preview'][:80]}")
        if has_pii:
            print(f"  Redacted: {redact_output(text)[:80]}")
        print()
