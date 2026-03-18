#!/usr/bin/env python3
"""
Domain Tokenizer — Extends PII tokenization with infrastructure-aware patterns.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Task #1425: Consultation Ring Domain Tokenizer

Composes the existing PIIService (Presidio-based) with federation-specific
pattern matching for node names, IPs, internal jargon, API keys, and
database identifiers. Token map stays in-memory per request — NEVER
crosses the security boundary.

Token format: <TOKEN:CATEGORY:hexdigest> for infra patterns
             <TOKEN:hexdigest> for PII (via PIITokenizer)
"""

import hashlib
import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger("consultation_ring.tokenizer")

# Import tokenizer directly via spec loader to avoid ganuda_pii/__init__.py (which imports Presidio)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("_pii_tokenizer", "/ganuda/lib/ganuda_pii/tokenizer.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
PIITokenizer = _mod.PIITokenizer


# Infrastructure patterns to tokenize (node names, IPs, internal jargon).
# Each tuple: (pattern_name, regex, entity_type_label)
INFRA_PATTERNS = [
    # Node names (all *fin nodes + mac nodes)
    ("node_name", r"\b(redfin|bluefin|greenfin|owlfin|eaglefin|silverfin|bmasass|sasass2?|thunderduck)\b", "NODE"),
    # LAN IPs (192.168.132.x)
    ("lan_ip", r"\b192\.168\.132\.\d{1,3}\b", "LAN_IP"),
    # DMZ IPs (192.168.30.x)
    ("dmz_ip", r"\b192\.168\.30\.\d{1,3}\b", "DMZ_IP"),
    # VLAN IPs (192.168.10.x)
    ("vlan_ip", r"\b192\.168\.10\.\d{1,3}\b", "VLAN_IP"),
    # WireGuard IPs (10.100.0.x)
    ("wg_ip", r"\b10\.100\.0\.\d{1,3}\b", "WG_IP"),
    # Tailscale IPs (100.x.x.x)
    ("ts_ip", r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "TS_IP"),
    # Internal jargon that reveals architecture
    ("jargon", r"\b(longhouse|council|thermal[\s_-]?memory|design[\s_-]?constraint|sacred[\s_-]?fire|ganuda|stoneclad)\b", "INTERNAL_TERM"),
    # Internal service ports (colon-prefixed)
    ("service_port", r":(8000|8080|8003|8800|8801|8090|8091|8092|9400|5432|3000)\b", "SERVICE_PORT"),
    # Internal service paths
    ("service_path_ganuda", r"/ganuda/[\w/._-]+", "INTERNAL_PATH"),
    ("service_path_mac", r"/Users/Shared/ganuda/[\w/._-]+", "INTERNAL_PATH"),
    # Internal database names
    ("db_name", r"\b(zammad_production|cherokee_identity|cherokee_ops|cherokee_telemetry)\b", "INFRA_DB"),
    # Internal table names
    ("table_name", r"\b(thermal_memory_archive|jr_work_queue|duplo_tool_registry|ring_health|scrub_rules|council_votes|sag_events|token_ledger)\b", "INFRA_TABLE"),
    # API keys (Anthropic, OpenAI, Slack, generic sk-)
    ("api_key", r"(sk-ant-api[\w-]{20,}|sk-[\w-]{20,}|xoxb-[\w-]+)", "INFRA_SECRET"),
    # More internal jargon
    ("jargon_internal", r"\b(duplo|necklace|chain_protocol|web_ring|harness_tier|fire_guard|dawn_mist|jr_executor)\b", "INFRA_JARGON"),
    # FreeIPA / SSSD references
    ("freeipa", r"\b(FreeIPA|SSSD|ganuda-service-management)\b", "INFRA_AUTH"),
    # WireGuard config references
    ("wireguard", r"\b(WireGuard|wg0|wg-quick)\b", "INFRA_NET"),
    # Username
    ("username", r"\bdereadi\b", "INFRA_USER"),
]

# Fallback PII patterns — used when Presidio is unavailable.
# These are NOT a replacement for Presidio but ensure baseline PII scrubbing.
FALLBACK_PII_PATTERNS = [
    # US SSN (xxx-xx-xxxx)
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "PII_SSN"),
    # US phone numbers
    ("phone", r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "PII_PHONE"),
    # Email addresses
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "PII_EMAIL"),
    # Credit card numbers (basic 16-digit groups)
    ("credit_card", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "PII_CC"),
    # Person names preceded by common titles or contextual words
    # (intentionally broad — Presidio is better, this is the safety net)
    ("named_person", r"\b(?:Mr|Mrs|Ms|Dr|Patient|Veteran|Applicant|Claimant)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", "PII_PERSON"),
]

# NEVER_SEND: patterns that cause hard rejection, not tokenization.
# If these survive after tokenization, outbound_scrub will catch them,
# but we want to fail fast here.
NEVER_SEND_PATTERNS = [
    r"CHEROKEE_DB_PASS",
    r"secrets\.env",
    r"\.pem\b",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    r"password\s*=\s*\S+",
]


class DomainTokenizer:
    """Tokenizes PII + infrastructure terms before crossing trust boundary.

    Usage:
        dt = DomainTokenizer()
        tokenized, token_map, violations = dt.tokenize(text)
        if violations:
            raise SecurityError("NEVER_SEND violation")
        # ... send tokenized text across boundary ...
        original = dt.detokenize(response, token_map)
    """

    def __init__(self, salt: str = "consultation-ring-air-gap"):
        self._pii_tokenizer = PIITokenizer(salt=salt)
        self._pii_service = None  # Lazy-load Presidio (heavy import)
        self._token_map: Dict[str, str] = {}   # token -> original
        self._reverse_map: Dict[str, str] = {}  # original -> token

    def _get_pii_service(self):
        """Lazy-load PIIService to avoid Presidio import cost at module level."""
        if self._pii_service is None:
            try:
                from lib.ganuda_pii.service import PIIService
                self._pii_service = PIIService(token_salt="consultation-ring-air-gap")
            except ImportError:
                logger.warning("PIIService not available, PII detection disabled")
        return self._pii_service

    def _check_never_send(self, text: str) -> List[str]:
        """Check for NEVER_SEND patterns. Returns list of violations."""
        violations = []
        for pattern in NEVER_SEND_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"NEVER_SEND: {pattern}")
        return violations

    def _make_token(self, value: str, category: str) -> str:
        """Create deterministic token for a value. Same input -> same token."""
        digest = hashlib.sha256(value.encode()).hexdigest()[:12]
        token = f"<TOKEN:{category}:{digest}>"
        self._token_map[token] = value
        self._reverse_map[value] = token
        return token

    def _tokenize_fallback_pii(self, text: str) -> str:
        """Apply regex-based PII patterns as safety net when Presidio is unavailable."""
        result = text
        for name, pattern, category in FALLBACK_PII_PATTERNS:
            matches = list(re.finditer(pattern, result))
            for match in reversed(matches):
                # For named_person pattern, tokenize the full match (including title)
                original = match.group(0)
                if original not in self._reverse_map:
                    self._make_token(original, category)
                token = self._reverse_map[original]
                result = result[:match.start()] + token + result[match.end():]
        return result

    def _tokenize_infra(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace infrastructure patterns with deterministic tokens."""
        result = text

        for name, pattern, category in INFRA_PATTERNS:
            # Find all matches first, then replace to avoid re-matching tokens
            matches = list(re.finditer(pattern, result, re.IGNORECASE))
            # Process in reverse order to preserve string positions
            for match in reversed(matches):
                original = match.group(0)
                if original not in self._reverse_map:
                    self._make_token(original, category)
                token = self._reverse_map[original]
                result = result[:match.start()] + token + result[match.end():]

        return result, dict(self._token_map)

    def _outbound_scrub_check(self, text: str) -> List[str]:
        """Final validation via chain_protocol.outbound_scrub().

        This is the NEVER_SEND enforcement at the chain protocol level.
        Catches anything the local patterns missed via DB-driven scrub rules.
        Graceful fallback if DB is unavailable.
        """
        try:
            from lib.chain_protocol import outbound_scrub
            return outbound_scrub(text, ring_name="consultation_ring")
        except Exception as exc:
            logger.warning(
                "[DOMAIN_TOKENIZER] chain_protocol.outbound_scrub() unavailable: %s. "
                "Relying on local NEVER_SEND patterns only.", exc
            )
            return []

    def tokenize(self, text: str, user_id: str = "consultation") -> Tuple[str, Dict[str, str], List[str]]:
        """Full tokenization: PII + infrastructure patterns + NEVER_SEND check.

        Returns:
            (tokenized_text, token_map, violations)

            If violations is non-empty, the text MUST NOT be sent.
            Token map stays in-memory -- never crosses the boundary.
        """
        # Reset per-request maps
        self._token_map = {}
        self._reverse_map = {}

        # Step 1: NEVER_SEND check (fail fast on hard violations)
        violations = self._check_never_send(text)

        # Step 2: PII tokenization (Presidio preferred, fallback regex)
        pii_text = text
        presidio_ok = False
        pii_service = self._get_pii_service()
        if pii_service is not None:
            try:
                pii_tokenized, pii_map = pii_service.tokenize(text, user_id)
                pii_text = pii_tokenized
                presidio_ok = True
                # Integrate PII tokens into our maps for round-trip detokenize
                for token_hex, data in pii_map.items():
                    full_token = f"<TOKEN:{token_hex}>"
                    self._token_map[full_token] = data["original"]
                    self._reverse_map[data["original"]] = full_token
            except Exception as exc:
                logger.error(
                    "[DOMAIN_TOKENIZER] Presidio PII detection FAILED -- using fallback PII patterns. "
                    "Error: %s", exc
                )

        # Step 2b: Fallback PII patterns (when Presidio unavailable)
        if not presidio_ok:
            pii_text = self._tokenize_fallback_pii(pii_text)

        # Step 3: Infrastructure tokenization (our patterns)
        infra_text, _ = self._tokenize_infra(pii_text)

        # Step 4: NEVER_SEND enforcement via chain_protocol.outbound_scrub()
        scrub_violations = self._outbound_scrub_check(infra_text)
        violations.extend(scrub_violations)

        return infra_text, dict(self._token_map), violations

    def detokenize(self, text: str, token_map: Dict[str, str] = None) -> str:
        """Restore original terms from tokens.

        Uses provided token_map or falls back to instance's internal map.
        Called on the response AFTER it comes back across the boundary.
        """
        tmap = token_map or self._token_map
        result = text
        for token, original in tmap.items():
            result = result.replace(token, original)
        return result

    def count_tokens_by_type(self, token_map: Dict[str, str] = None) -> Dict[str, int]:
        """Count tokens by category for audit logging."""
        tmap = token_map or self._token_map
        counts: Dict[str, int] = {}
        for token in tmap.keys():
            # Extract category from <TOKEN:CATEGORY:digest>
            match = re.match(r"<TOKEN:([^:>]+):", token)
            category = match.group(1) if match else "PII"
            counts[category] = counts.get(category, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Round-trip self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_text = (
        "Our node redfin at 192.168.132.223 is running vLLM on :8000. "
        "Patient John Smith SSN 123-45-6789 needs help."
    )

    dt = DomainTokenizer()
    tokenized, token_map, violations = dt.tokenize(test_text)

    print("=" * 70)
    print("ORIGINAL:")
    print(test_text)
    print()
    print("TOKENIZED:")
    print(tokenized)
    print()
    print("TOKEN MAP:")
    for tok, orig in token_map.items():
        print(f"  {tok} -> {orig}")
    print()
    print("VIOLATIONS:", violations or "None")
    print()

    # Round-trip verification
    restored = dt.detokenize(tokenized, token_map)
    print("RESTORED:")
    print(restored)
    print()

    # Verify sensitive values are NOT in tokenized output
    must_not_appear = ["redfin", "192.168.132.223", ":8000", "John Smith", "123-45-6789"]
    all_clean = True
    for sensitive in must_not_appear:
        if sensitive in tokenized:
            print(f"  FAIL: '{sensitive}' found in tokenized output!")
            all_clean = False
        else:
            print(f"  PASS: '{sensitive}' not in tokenized output")

    print()
    # Verify round-trip
    if restored == test_text:
        print("ROUND-TRIP: PASS (restored == original)")
    else:
        print("ROUND-TRIP: FAIL (restored != original)")
        print(f"  Expected: {test_text}")
        print(f"  Got:      {restored}")

    print()
    print("TOKEN COUNTS:", dt.count_tokens_by_type(token_map))
    print("=" * 70)
