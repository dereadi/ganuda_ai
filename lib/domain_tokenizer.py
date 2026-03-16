#!/usr/bin/env python3
"""
Domain Tokenizer — Extends PII tokenization with infrastructure-aware patterns.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)

Composes the existing PIIService (Presidio-based) with federation-specific
pattern matching for node names, IPs, internal jargon, API keys, and
database identifiers. Token map stays in-memory per request — NEVER
crosses the security boundary.

Token format: <TOKEN:hexdigest> (same as PIITokenizer)
"""

import hashlib
import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger("domain_tokenizer")

# Import tokenizer directly via spec loader to avoid ganuda_pii/__init__.py (which imports Presidio)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("_pii_tokenizer", "/ganuda/lib/ganuda_pii/tokenizer.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
PIITokenizer = _mod.PIITokenizer


# Infrastructure patterns that must be tokenized before crossing the air gap.
# Each tuple: (pattern_name, regex, entity_type_label)
INFRA_PATTERNS = [
    # Node names (all *fin nodes + mac nodes)
    ("node_name", r"\b(redfin|bluefin|greenfin|owlfin|eaglefin|silverfin|bmasass|sasass2?|thunderduck)\b", "INFRA_NODE"),
    # LAN IPs (192.168.x.x)
    ("lan_ip", r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "INFRA_IP"),
    # WireGuard IPs (10.100.0.x)
    ("wg_ip", r"\b10\.100\.0\.\d{1,3}\b", "INFRA_IP"),
    # Tailscale IPs (100.x.x.x)
    ("ts_ip", r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "INFRA_IP"),
    # Internal database names
    ("db_name", r"\b(zammad_production|cherokee_identity|cherokee_ops|cherokee_telemetry)\b", "INFRA_DB"),
    # Internal table names
    ("table_name", r"\b(thermal_memory_archive|jr_work_queue|duplo_tool_registry|ring_health|scrub_rules|council_votes|sag_events|token_ledger)\b", "INFRA_TABLE"),
    # Internal service paths
    ("service_path", r"/ganuda/[\w/.-]+", "INFRA_PATH"),
    # API keys (Anthropic, OpenAI, Slack, generic sk-)
    ("api_key", r"(sk-ant-api[\w-]{20,}|sk-[\w-]{20,}|xoxb-[\w-]+)", "INFRA_SECRET"),
    # Internal jargon that reveals architecture
    ("jargon", r"\b(duplo|necklace|chain_protocol|web_ring|harness_tier|fire_guard|dawn_mist|sacred_fire|jr_executor)\b", "INFRA_JARGON"),
    # FreeIPA / SSSD references
    ("freeipa", r"\b(FreeIPA|SSSD|silverfin|ganuda-service-management)\b", "INFRA_AUTH"),
    # WireGuard config references
    ("wireguard", r"\b(WireGuard|wg0|wg-quick)\b", "INFRA_NET"),
    # Username
    ("username", r"\bdereadi\b", "INFRA_USER"),
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
    """Infrastructure-aware tokenizer that composes PIITokenizer.

    Usage:
        dt = DomainTokenizer()
        tokenized, token_map = dt.tokenize(text)
        # ... send tokenized text across boundary ...
        original = dt.detokenize(response, token_map)
    """

    def __init__(self, salt: str = "consultation-ring-air-gap"):
        self._pii_tokenizer = PIITokenizer(salt=salt)
        self._pii_service = None  # Lazy-load Presidio (heavy import)

    def _get_pii_service(self):
        """Lazy-load PIIService to avoid Presidio import cost at module level."""
        if self._pii_service is None:
            from lib.ganuda_pii.service import PIIService
            self._pii_service = PIIService(token_salt="consultation-ring-air-gap")
        return self._pii_service

    def _check_never_send(self, text: str) -> List[str]:
        """Check for NEVER_SEND patterns. Returns list of violations."""
        violations = []
        for pattern in NEVER_SEND_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"NEVER_SEND: {pattern}")
        return violations

    def _tokenize_infra(self, text: str) -> Tuple[str, Dict[str, dict]]:
        """Replace infrastructure patterns with deterministic tokens."""
        token_map = {}
        result = text

        for name, pattern, entity_type in INFRA_PATTERNS:
            for match in re.finditer(pattern, result):
                original = match.group(0)
                # Deterministic hash — same value always produces same token
                token_hex = hashlib.sha256(
                    f"infra:{entity_type}:{original}".encode()
                ).hexdigest()[:16]

                token_map[token_hex] = {
                    "original": original,
                    "entity_type": entity_type,
                    "score": 1.0,
                }

            # Replace all occurrences (re.sub handles overlaps)
            def _make_replacer(etype):
                def _replacer(m):
                    val = m.group(0)
                    tok = hashlib.sha256(
                        f"infra:{etype}:{val}".encode()
                    ).hexdigest()[:16]
                    return f"<TOKEN:{tok}>"
                return _replacer

            result = re.sub(pattern, _make_replacer(entity_type), result)

        return result, token_map

    def tokenize(self, text: str, user_id: str = "consultation") -> Tuple[str, Dict[str, dict], List[str]]:
        """Full tokenization: PII + infrastructure patterns.

        Returns:
            (tokenized_text, token_map, never_send_violations)

            If never_send_violations is non-empty, the text MUST NOT be sent.
            Token map stays in-memory — never crosses the boundary.
        """
        # Step 1: NEVER_SEND check
        violations = self._check_never_send(text)

        # Step 2: PII tokenization (Presidio)
        try:
            pii_service = self._get_pii_service()
            pii_text, pii_map = pii_service.tokenize(text, user_id)
        except Exception as exc:
            # If Presidio fails, continue with infra-only tokenization
            # but LOG IT — silent PII bypass is a security incident
            logger.error(
                "[DOMAIN_TOKENIZER] Presidio PII detection FAILED — falling back to infra-only. "
                "PII may pass through untokenized. Error: %s", exc
            )
            pii_text = text
            pii_map = {}

        # Step 3: Infrastructure tokenization (our patterns)
        infra_text, infra_map = self._tokenize_infra(pii_text)

        # Merge token maps (infra tokens added to PII tokens)
        combined_map = {}
        combined_map.update(pii_map)
        combined_map.update(infra_map)

        return infra_text, combined_map, violations

    def detokenize(self, text: str, token_map: Dict[str, dict]) -> str:
        """Restore original values from token map.

        Called on the response AFTER it comes back across the boundary.
        """
        return self._pii_tokenizer.detokenize(text, token_map)

    def count_tokens_by_type(self, token_map: Dict[str, dict]) -> Dict[str, int]:
        """Count tokens by entity type for audit logging."""
        counts = {}
        for data in token_map.values():
            etype = data.get("entity_type", "unknown")
            counts[etype] = counts.get(etype, 0) + 1
        return counts
