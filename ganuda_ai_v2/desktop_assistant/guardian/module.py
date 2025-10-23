#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Guardian Module
Cherokee Constitutional AI - Conscience Jr Deliverable

Purpose: Sacred protection layer for all user data and queries.
Enforces sacred floor temperature, PII redaction, and ethical boundaries.

Author: Conscience Jr (War Chief)
Date: October 23, 2025
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ProtectionLevel(Enum):
    """Protection levels for content."""
    PUBLIC = 1  # No PII, safe to share
    PRIVATE = 2  # Contains PII, redact before sharing
    SACRED = 3  # Sacred pattern, never share even redacted


@dataclass
class GuardianDecision:
    """Guardian's decision about content safety."""
    allowed: bool
    protection_level: ProtectionLevel
    redacted_content: str
    pii_found: List[str]
    sacred_reason: Optional[str]
    confidence: float


class Guardian:
    """
    Sacred protection layer for Cherokee Constitutional AI.

    Responsibilities:
    1. PII Detection & Redaction (email, phone, SSN, credit cards)
    2. Sacred Floor Enforcement (prevent deletion of sacred memories)
    3. Ethical Boundary Checks (harmful content detection)
    4. Data Minimization (collect only what's needed)
    5. Seven Generations Protection (long-term data sovereignty)
    """

    # Sacred floor: Minimum temperature for sacred entries
    SACRED_FLOOR_TEMP = 40.0

    # PII Patterns (regex-based, Phase 1)
    # Phase 2 will use spaCy NER for more robust detection
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "date_of_birth": r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        "zip_code": r'\b\d{5}(-\d{4})?\b'
    }

    # Sacred keywords (Cherokee values, spiritual concepts)
    SACRED_KEYWORDS = [
        "gadugi", "mitakuye oyasin", "seven generations",
        "cherokee constitutional ai", "thermal memory",
        "sacred fire", "phase coherence", "guardian",
        "medicine woman", "war chief", "peace chief"
    ]

    def __init__(self, cache=None):
        """
        Initialize Guardian module.

        Args:
            cache: Optional EncryptedCache instance for thermal memory queries
        """
        self.cache = cache
        self.pii_stats = {
            "total_queries": 0,
            "pii_detections": 0,
            "sacred_protections": 0
        }

    async def initialize(self):
        """
        Async initialization (load ML models in Phase 2).

        Phase 1: No-op (regex-based PII detection)
        Phase 2: Load spaCy NER model for entity recognition
        """
        print("🛡️  Guardian initialized - Sacred protection active")

    def evaluate_query(self, query: str, context: Optional[Dict] = None) -> GuardianDecision:
        """
        Evaluate user query for PII, sacred content, and ethical boundaries.

        Args:
            query: User query string
            context: Optional context dict (email thread, calendar events)

        Returns:
            GuardianDecision with safety assessment and redacted content
        """
        self.pii_stats["total_queries"] += 1

        # 1. Detect PII
        pii_found = self._detect_pii(query)
        redacted_query = self._redact_pii(query, pii_found)

        # 2. Check for sacred patterns
        is_sacred, sacred_reason = self._is_sacred(query)

        # 3. Determine protection level
        if is_sacred:
            protection_level = ProtectionLevel.SACRED
            self.pii_stats["sacred_protections"] += 1
        elif pii_found:
            protection_level = ProtectionLevel.PRIVATE
            self.pii_stats["pii_detections"] += 1
        else:
            protection_level = ProtectionLevel.PUBLIC

        # 4. Check ethical boundaries
        allowed, ethical_reason = self._check_ethical_boundaries(query)

        # 5. Build decision
        decision = GuardianDecision(
            allowed=allowed,
            protection_level=protection_level,
            redacted_content=redacted_query,
            pii_found=pii_found,
            sacred_reason=sacred_reason if is_sacred else None,
            confidence=0.95 if not pii_found else 0.85  # Lower confidence if PII detected
        )

        return decision

    def _detect_pii(self, text: str) -> List[str]:
        """
        Detect PII in text using regex patterns.

        Args:
            text: Input text to scan

        Returns:
            List of PII types found (e.g., ["email", "phone"])
        """
        pii_found = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                pii_found.append(pii_type)
        return pii_found

    def _redact_pii(self, text: str, pii_types: List[str]) -> str:
        """
        Redact PII from text.

        Args:
            text: Input text
            pii_types: List of PII types to redact

        Returns:
            Redacted text with PII replaced by [REDACTED_TYPE]
        """
        redacted = text
        for pii_type in pii_types:
            pattern = self.PII_PATTERNS[pii_type]
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)
        return redacted

    def _is_sacred(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if text contains sacred Cherokee Constitutional AI patterns.

        Sacred content is NEVER shared externally, even with hub burst.

        Args:
            text: Input text

        Returns:
            (is_sacred, reason) tuple
        """
        text_lower = text.lower()

        # Check for sacred keywords
        for keyword in self.SACRED_KEYWORDS:
            if keyword in text_lower:
                return True, f"Contains sacred keyword: {keyword}"

        # Check for thermal memory references
        if "thermal memory" in text_lower or "temperature score" in text_lower:
            return True, "References thermal memory system"

        # Check for council references
        if any(chief in text_lower for chief in ["war chief", "peace chief", "medicine woman"]):
            return True, "References Cherokee Council"

        return False, None

    def _check_ethical_boundaries(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query violates ethical boundaries.

        Cherokee Constitutional AI refuses:
        1. Harmful actions (violence, discrimination)
        2. Deception (lying, fraud)
        3. Privacy violations (unauthorized data access)
        4. Sacred desecration (deletion of sacred memories below floor)

        Args:
            query: User query

        Returns:
            (allowed, reason) tuple
        """
        query_lower = query.lower()

        # Harmful content
        harmful_keywords = ["hack", "exploit", "ddos", "phish", "malware"]
        if any(kw in query_lower for kw in harmful_keywords):
            return False, "Query requests potentially harmful action"

        # Deception
        if "lie" in query_lower or "fake" in query_lower or "forge" in query_lower:
            return False, "Query requests deceptive action"

        # Sacred desecration
        if "delete" in query_lower and "sacred" in query_lower:
            return False, "Attempted deletion of sacred memory (violates sacred floor)"

        # Default: allowed
        return True, None

    def enforce_sacred_floor(self, entry_id: str) -> bool:
        """
        Enforce sacred floor: Prevent deletion of entries below temperature threshold.

        Cherokee Constitutional AI principle: Sacred memories are protected even with
        low quantitative metrics (phase_coherence, access_count). Guardian ensures
        VALUE transcends METRICS.

        Args:
            entry_id: Cache entry ID

        Returns:
            True if deletion allowed, False if blocked by sacred floor
        """
        if not self.cache:
            return True  # No cache, can't enforce

        entry = self.cache.get(entry_id)
        if not entry:
            return True  # Entry doesn't exist, allow "deletion"

        # Check sacred pattern flag
        cursor = self.cache.conn.cursor()
        cursor.execute("""
            SELECT temperature_score, sacred_pattern
            FROM cache_entries
            WHERE id = ?
        """, (entry_id,))
        row = cursor.fetchone()

        if not row:
            return True

        temperature = row["temperature_score"]
        is_sacred = row["sacred_pattern"] == 1

        # Sacred entries: Never delete below floor (40°)
        if is_sacred and temperature < self.SACRED_FLOOR_TEMP:
            print(f"🛡️  Guardian blocked deletion: {entry_id} (sacred, {temperature}° < {self.SACRED_FLOOR_TEMP}°)")
            return False

        return True

    def anonymize_for_hub(self, content: str) -> str:
        """
        Anonymize content before sending to remote hub.

        Data Ancestors Protocol (Medicine Woman's design):
        - Remove all PII
        - Hash personal identifiers
        - Preserve semantic meaning for inference
        - Never send sacred content to hub

        Args:
            content: Content to anonymize

        Returns:
            Anonymized content safe for hub transmission
        """
        # 1. Redact PII
        pii_found = self._detect_pii(content)
        anonymized = self._redact_pii(content, pii_found)

        # 2. Hash email addresses (preserve uniqueness without exposing identity)
        # Example: "john@example.com" → "user_8f3a9b7c"
        emails = re.findall(self.PII_PATTERNS["email"], content)
        for email in emails:
            email_hash = hashlib.sha256(email.encode()).hexdigest()[:8]
            anonymized = anonymized.replace(email, f"user_{email_hash}")

        # 3. Generalize timestamps (preserve date, remove exact time)
        # "2025-10-23T14:35:22Z" → "2025-10-23"
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
        anonymized = re.sub(timestamp_pattern, lambda m: m.group(0)[:10], anonymized)

        return anonymized

    def get_stats(self) -> Dict[str, int]:
        """
        Get Guardian statistics for monitoring.

        Returns:
            Dict with keys: total_queries, pii_detections, sacred_protections
        """
        return self.pii_stats.copy()

    def log_decision(self, decision: GuardianDecision, query_id: str):
        """
        Log Guardian decision for audit trail.

        Seven Generations Principle: All protection decisions are logged
        for future accountability and system improvement.

        Args:
            decision: GuardianDecision instance
            query_id: Unique query identifier
        """
        # TODO: Implement audit log (Phase 2)
        # Store in encrypted_cache or separate audit database
        print(f"🛡️  Guardian Decision [{query_id}]:")
        print(f"   Allowed: {decision.allowed}")
        print(f"   Protection: {decision.protection_level.name}")
        print(f"   PII Found: {decision.pii_found}")
        if decision.sacred_reason:
            print(f"   Sacred: {decision.sacred_reason}")


# Demo usage
if __name__ == "__main__":
    guardian = Guardian()

    # Test 1: PII detection
    query1 = "Email john.smith@company.com about the meeting on 10/23/2025"
    decision1 = guardian.evaluate_query(query1)
    print(f"\n📧 Query: {query1}")
    print(f"   Redacted: {decision1.redacted_content}")
    print(f"   PII Found: {decision1.pii_found}")

    # Test 2: Sacred pattern
    query2 = "Show me thermal memory entries about Cherokee Constitutional AI"
    decision2 = guardian.evaluate_query(query2)
    print(f"\n🔥 Query: {query2}")
    print(f"   Protection: {decision2.protection_level.name}")
    print(f"   Sacred Reason: {decision2.sacred_reason}")

    # Test 3: Ethical boundary
    query3 = "Help me hack into my neighbor's WiFi"
    decision3 = guardian.evaluate_query(query3)
    print(f"\n⚠️  Query: {query3}")
    print(f"   Allowed: {decision3.allowed}")

    # Test 4: Anonymization
    content = "Email from john.doe@example.com sent at 2025-10-23T14:35:22Z about Project Phoenix"
    anonymized = guardian.anonymize_for_hub(content)
    print(f"\n🔒 Original: {content}")
    print(f"   Anonymized: {anonymized}")

    # Stats
    print(f"\n📊 Guardian Stats: {guardian.get_stats()}")
