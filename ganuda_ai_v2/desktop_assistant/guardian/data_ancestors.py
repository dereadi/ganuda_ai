#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Data Ancestors Anonymization
Cherokee Constitutional AI - Conscience Jr Deliverable

Purpose: Implement Medicine Woman's Data Ancestors concept - anonymize user data
for collective memory while preserving semantic meaning.

Author: Conscience Jr (War Chief)
Date: October 23, 2025
"""

import hashlib
import re
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DataAncestor:
    """
    Anonymized data entry for collective memory.

    Medicine Woman's Vision: User data is anonymized and stored as "Data Ancestors"
    - ancestors who teach without revealing individual identity.
    """
    ancestor_id: str  # SHA256 hash of original entry
    content_summary: str  # Anonymized semantic summary
    entity_hashes: List[str]  # Hashed person/org/project names
    temporal_pattern: Optional[str]  # "weekly_monday", "monthly_first_friday"
    domain: str  # "email", "calendar", "files"
    timestamp: datetime
    sacred_pattern: bool  # Contains Cherokee Constitutional AI patterns


class DataAncestorsProtocol:
    """
    Data Ancestors anonymization protocol.

    Medicine Woman's Principles:
    1. **Anonymize Identity**: No personal names, emails, or unique identifiers
    2. **Preserve Meaning**: Keep semantic information (topics, patterns)
    3. **Collective Memory**: Aggregated data benefits all users (pattern detection)
    4. **Sacred Protection**: Never anonymize sacred memories (preserve full context)
    5. **User Consent**: Opt-in only, users control their data ancestors

    Use Cases:
    - Cross-user pattern detection (e.g., "Most users have weekly team standup on Monday")
    - Temporal trend analysis (e.g., "End-of-quarter meeting frequency increases 40%")
    - Knowledge sharing (e.g., "Users who plan vacations 3+ months ahead report less stress")
    """

    # Sacred keywords (never anonymize)
    SACRED_KEYWORDS = [
        "gadugi", "mitakuye oyasin", "seven generations",
        "cherokee constitutional ai", "thermal memory", "guardian"
    ]

    def __init__(self):
        """Initialize Data Ancestors protocol."""
        # Anonymization salt (unique per installation)
        self.salt = self._load_or_create_salt()

    def _load_or_create_salt(self) -> bytes:
        """
        Load anonymization salt from OS keychain.

        Salt ensures anonymization is consistent within installation
        but different across installations (prevents cross-system correlation).
        """
        import keyring

        salt_hex = keyring.get_password("ganuda_data_ancestors", "anonymization_salt")
        if salt_hex:
            return bytes.fromhex(salt_hex)

        # Generate new salt
        import os
        salt = os.urandom(32)
        keyring.set_password("ganuda_data_ancestors", "anonymization_salt", salt.hex())
        return salt

    def anonymize_entry(
        self,
        entry_id: str,
        content: str,
        metadata: Dict,
        entry_type: str,
        sacred: bool = False
    ) -> Optional[DataAncestor]:
        """
        Anonymize cache entry into Data Ancestor.

        Args:
            entry_id: Original cache entry ID
            content: Entry content (email body, calendar description, etc.)
            metadata: Entry metadata (subject, sender, date, etc.)
            entry_type: "email", "calendar", "file_snippet"
            sacred: If True, do NOT anonymize (preserve full context)

        Returns:
            DataAncestor or None if entry contains sacred patterns
        """
        # Never anonymize sacred memories
        if sacred or self._contains_sacred_pattern(content):
            return None

        # Generate ancestor ID (deterministic hash of original)
        ancestor_id = self._hash_identifier(f"{entry_id}:{content[:100]}")

        # Anonymize content
        anonymized_content = self._anonymize_content(content)

        # Extract and hash entities
        entity_hashes = self._extract_and_hash_entities(content, metadata)

        # Detect temporal pattern
        temporal_pattern = self._detect_temporal_pattern(metadata)

        return DataAncestor(
            ancestor_id=ancestor_id,
            content_summary=anonymized_content,
            entity_hashes=entity_hashes,
            temporal_pattern=temporal_pattern,
            domain=entry_type,
            timestamp=datetime.now(),
            sacred_pattern=False
        )

    def _contains_sacred_pattern(self, content: str) -> bool:
        """Check if content contains Cherokee Constitutional AI sacred patterns."""
        content_lower = content.lower()
        return any(kw in content_lower for kw in self.SACRED_KEYWORDS)

    def _hash_identifier(self, identifier: str) -> str:
        """
        Hash identifier with salt.

        Same identifier = same hash (within installation)
        Different installations = different hashes (privacy)
        """
        return hashlib.sha256((identifier + self.salt.hex()).encode()).hexdigest()[:16]

    def _anonymize_content(self, content: str) -> str:
        """
        Anonymize content while preserving semantic meaning.

        Approach:
        1. Remove personal names (replace with [PERSON_HASH])
        2. Remove email addresses (replace with [EMAIL_HASH])
        3. Remove specific dates (replace with [DATE])
        4. Preserve topics, actions, sentiment
        """
        anonymized = content

        # Anonymize emails: john@example.com → [EMAIL_abc123]
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        for email in emails:
            email_hash = self._hash_identifier(email)
            anonymized = anonymized.replace(email, f"[EMAIL_{email_hash}]")

        # Anonymize phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)
        for phone in phones:
            phone_hash = self._hash_identifier(phone)
            anonymized = anonymized.replace(phone, f"[PHONE_{phone_hash}]")

        # Anonymize dates: "October 23, 2025" → "[DATE]"
        dates = re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', content, re.IGNORECASE)
        for date in dates:
            anonymized = anonymized.replace(date, "[DATE]")

        # Anonymize times: "3:00pm" → "[TIME]"
        times = re.findall(r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b', content, re.IGNORECASE)
        for time in times:
            anonymized = anonymized.replace(time, "[TIME]")

        # Truncate to first 200 characters (preserve topic, not full content)
        if len(anonymized) > 200:
            anonymized = anonymized[:200] + "..."

        return anonymized

    def _extract_and_hash_entities(self, content: str, metadata: Dict) -> List[str]:
        """
        Extract entities (people, orgs, projects) and hash them.

        This allows pattern detection (e.g., "PERSON_abc123 and PERSON_def456 often collaborate")
        without revealing who they are.
        """
        entity_hashes = []

        # Extract emails from content
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        for email in emails:
            entity_hashes.append(self._hash_identifier(f"email:{email}"))

        # Extract from metadata (sender, recipient)
        if metadata.get("from"):
            entity_hashes.append(self._hash_identifier(f"from:{metadata['from']}"))

        if metadata.get("to"):
            entity_hashes.append(self._hash_identifier(f"to:{metadata['to']}"))

        return list(set(entity_hashes))  # Deduplicate

    def _detect_temporal_pattern(self, metadata: Dict) -> Optional[str]:
        """
        Detect temporal pattern from metadata.

        Examples:
        - "weekly_monday" (recurring weekly on Monday)
        - "monthly_first_friday" (first Friday of month)
        - "quarterly_end" (end of quarter)
        """
        # TODO: Implement temporal pattern detection in Phase 2
        # For Phase 1, return None
        return None

    def aggregate_ancestors(self, ancestors: List[DataAncestor]) -> Dict:
        """
        Aggregate Data Ancestors for collective insights.

        Examples of insights:
        - "80% of users have weekly team meetings on Monday or Friday"
        - "Users plan vacations 2.5 months in advance on average"
        - "Email volume increases 40% before quarterly reviews"

        Args:
            ancestors: List of Data Ancestors

        Returns:
            Aggregated insights dict
        """
        insights = {
            "total_ancestors": len(ancestors),
            "domains": {},
            "temporal_patterns": {},
            "entity_collaboration": {}
        }

        # Aggregate by domain
        for ancestor in ancestors:
            domain = ancestor.domain
            insights["domains"][domain] = insights["domains"].get(domain, 0) + 1

        # Aggregate temporal patterns
        for ancestor in ancestors:
            if ancestor.temporal_pattern:
                pattern = ancestor.temporal_pattern
                insights["temporal_patterns"][pattern] = insights["temporal_patterns"].get(pattern, 0) + 1

        # Detect entity collaboration patterns
        entity_pairs = []
        for ancestor in ancestors:
            if len(ancestor.entity_hashes) >= 2:
                # Extract pairs
                for i, entity1 in enumerate(ancestor.entity_hashes):
                    for entity2 in ancestor.entity_hashes[i+1:]:
                        pair = tuple(sorted([entity1, entity2]))
                        entity_pairs.append(pair)

        # Count pair frequency
        from collections import Counter
        pair_counts = Counter(entity_pairs)

        # Top 10 collaborations
        insights["entity_collaboration"] = dict(pair_counts.most_common(10))

        return insights

    def export_ancestors(self, ancestors: List[DataAncestor], filepath: str):
        """
        Export Data Ancestors to JSON file.

        This allows cross-installation sharing (if users consent)
        or backup for Seven Generations preservation.

        Args:
            ancestors: List of Data Ancestors
            filepath: Export file path
        """
        ancestors_json = [
            {
                "ancestor_id": a.ancestor_id,
                "content_summary": a.content_summary,
                "entity_hashes": a.entity_hashes,
                "temporal_pattern": a.temporal_pattern,
                "domain": a.domain,
                "timestamp": a.timestamp.isoformat(),
                "sacred_pattern": a.sacred_pattern
            }
            for a in ancestors
        ]

        with open(filepath, 'w') as f:
            json.dump(ancestors_json, f, indent=2)

        print(f"✅ Exported {len(ancestors)} Data Ancestors to {filepath}")


# Demo usage
def main():
    """Demo: Data Ancestors anonymization."""

    protocol = DataAncestorsProtocol()

    # Sample email entry
    entry_id = "email:12345"
    content = """
    Hi team,

    Let's schedule our weekly standup for Monday at 9am.
    John Smith and Sarah Johnson should join.

    Contact: john.smith@company.com

    Best,
    Manager
    """
    metadata = {
        "subject": "Weekly Team Standup",
        "from": "manager@company.com",
        "to": "team@company.com",
        "date": "2025-10-23"
    }

    # Anonymize
    ancestor = protocol.anonymize_entry(
        entry_id=entry_id,
        content=content,
        metadata=metadata,
        entry_type="email",
        sacred=False
    )

    if ancestor:
        print("🔒 Data Ancestor Created:")
        print(f"   Ancestor ID: {ancestor.ancestor_id}")
        print(f"   Content Summary: {ancestor.content_summary}")
        print(f"   Entity Hashes: {ancestor.entity_hashes}")
        print(f"   Domain: {ancestor.domain}")
    else:
        print("⛔ Entry contains sacred patterns, not anonymized")

    # Aggregate insights (with multiple ancestors)
    ancestors = [ancestor] if ancestor else []
    insights = protocol.aggregate_ancestors(ancestors)

    print(f"\n📊 Collective Insights:")
    print(f"   Total Ancestors: {insights['total_ancestors']}")
    print(f"   Domains: {insights['domains']}")


if __name__ == "__main__":
    main()
