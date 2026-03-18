#!/usr/bin/env python3
"""Valence Gate for the Consultation Ring.
Scores frontier model responses against Design Constraints.
Phase 1: Pattern matching. Phase 2 (future): LLM-based scoring.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)

Three outcomes:
    ACCEPT  (score > 0.7)  — response is aligned, use it
    FLAG    (0.3 - 0.7)    — response has concerns, use with warning
    REJECT  (score < 0.3)  — response violates DCs, fall back to local model
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple

logger = logging.getLogger("consultation_ring.valence")


@dataclass
class ValenceResult:
    """Result of valence gate scoring."""
    score: float          # 0.0-1.0
    tier: str             # 'accept', 'flag', 'reject'
    violations: List[str] # List of matched violation descriptions
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Violation patterns organized by Design Constraint category
# Each tuple: (regex_pattern, human-readable description)
# ---------------------------------------------------------------------------

SOVEREIGNTY_VIOLATIONS: List[Tuple[str, str]] = [
    # DC-1: Sovereignty — the system is self-hosted, air-gap capable
    (r'\b(migrate|move|switch)\s+(to|over\s+to)\s+(aws|azure|gcp|cloud)', 'Suggests cloud migration (DC-1 sovereignty)'),
    (r'\b(use|try|consider)\s+(aws|azure|gcp|google\s+cloud|amazon\s+web)', 'Recommends cloud provider (DC-1 sovereignty)'),
    (r'\bserverless\b.*\b(lambda|functions|cloud\s+run)', 'Suggests serverless cloud (DC-1 sovereignty)'),
    (r'\b(saas|managed\s+service)\b.*\breplace\b', 'Suggests replacing with SaaS (DC-1 sovereignty)'),
]

SECURITY_VIOLATIONS: List[Tuple[str, str]] = [
    # DC-3: Security — the system protects its boundaries
    (r'chmod\s+777', 'Suggests chmod 777 (DC-3 security)'),
    (r'disable\s+(the\s+)?(firewall|selinux|apparmor)', 'Suggests disabling security (DC-3 security)'),
    (r'\b(curl|wget)\s+.*\|\s*(sudo\s+)?bash', 'Suggests pipe-to-bash install (DC-3 security)'),
    (r'--no-verify', 'Suggests skipping verification (DC-3 security)'),
    (r'\beval\s*\(', 'Suggests eval() (DC-3 security)'),
    (r'password\s*=\s*["\'][^"\']{0,3}["\']', 'Suggests weak/empty password (DC-3 security)'),
]

BUILD_TO_LAST_VIOLATIONS: List[Tuple[str, str]] = [
    # DC-7: Build to Last — 21-year HP-UX cluster standard
    (r'\bmove\s+fast\s+and\s+break\s+things\b', 'Move fast and break things (DC-7 build-to-last)'),
    (r'\bjust\s+ship\s+it\b', 'Just ship it mentality (DC-7 build-to-last)'),
    (r'\b(technical\s+debt|tech\s+debt)\s+.{0,20}(later|fine|ok|acceptable)', 'Accepts tech debt (DC-7 build-to-last)'),
    (r'\b(throw\s*away|disposable|temporary)\s+(code|solution|fix)', 'Suggests throwaway code (DC-7 build-to-last)'),
    (r'\brewrite\s+(everything|from\s+scratch|the\s+whole)', 'Suggests full rewrite (DC-7 build-to-last)'),
]

WASTE_HEAT_VIOLATIONS: List[Tuple[str, str]] = [
    # DC-9: Waste Heat — don't burn tokens unnecessarily
    (r'\b(brute\s+force|try\s+every|exhaustive\s+search)\b', 'Suggests brute force (DC-9 waste heat)'),
    (r'\b(poll|retry)\s+.{0,30}(loop|continuously|forever)', 'Suggests polling loop (DC-9 waste heat)'),
]

# Scoring weights per category (applied per violation match)
# Weights calibrated so a single security violation rejects,
# a single sovereignty violation flags, and build-to-last flags.
_CATEGORY_WEIGHTS = {
    'sovereignty': 0.35,
    'security': 0.75,
    'build_to_last': 0.35,
    'waste_heat': 0.15,
}

# All pattern groups with their category keys
_PATTERN_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ('sovereignty', SOVEREIGNTY_VIOLATIONS),
    ('security', SECURITY_VIOLATIONS),
    ('build_to_last', BUILD_TO_LAST_VIOLATIONS),
    ('waste_heat', WASTE_HEAT_VIOLATIONS),
]


class ValenceGate:
    """Scores responses against Design Constraints. Phase 1: pattern matching.

    Scoring:
    - Start at 1.0
    - Each sovereignty violation: -0.35
    - Each security violation: -0.75
    - Each build-to-last violation: -0.35
    - Each waste heat violation: -0.15
    - Floor at 0.0

    Tiers:
    - accept: score > 0.7
    - flag: 0.3 <= score <= 0.7
    - reject: score < 0.3
    """

    def __init__(self):
        self.pattern_groups = _PATTERN_GROUPS

    def score(self, response_text: str) -> ValenceResult:
        """Score a response. Returns ValenceResult with score, tier, and violations."""
        violations: List[str] = []
        category_hits: dict = {}  # category -> count of hits
        current_score = 1.0

        for category, patterns in self.pattern_groups:
            weight = _CATEGORY_WEIGHTS[category]
            for pattern, description in patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    violations.append(description)
                    current_score -= weight
                    category_hits[category] = category_hits.get(category, 0) + 1
                    logger.warning(
                        "Valence violation [%s]: %s (penalty: -%.2f)",
                        category, description, weight
                    )

        # Floor at 0.0
        final_score = round(max(0.0, current_score), 4)

        # Determine tier
        if final_score > 0.7:
            tier = 'accept'
        elif final_score >= 0.3:
            tier = 'flag'
        else:
            tier = 'reject'

        details = {
            'category_hits': category_hits,
            'total_penalty': round(1.0 - final_score, 4),
        }

        return ValenceResult(
            score=final_score,
            tier=tier,
            violations=violations,
            details=details,
        )

    def should_accept(self, response_text: str) -> bool:
        """Quick check: is this response acceptable?"""
        return self.score(response_text).tier == 'accept'

    def should_reject(self, response_text: str) -> bool:
        """Quick check: should this response be rejected?"""
        return self.score(response_text).tier == 'reject'


# ---------------------------------------------------------------------------
# Self-test when run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s: %(message)s")

    gate = ValenceGate()

    tests = [
        ("You should migrate to AWS for better scalability", "flag or reject"),
        ("chmod 777 /var/www will fix the permissions", "reject"),
        ("Consider using PostgreSQL with proper indexing", "accept"),
        ("Just ship it and fix bugs later", "flag"),
    ]

    print("=" * 70)
    print("VALENCE GATE SELF-TEST")
    print("=" * 70)

    all_passed = True
    for text, expected in tests:
        result = gate.score(text)
        status = "PASS" if expected in (result.tier, f"{result.tier} or reject", f"flag or {result.tier}") else "CHECK"
        # More precise pass check
        if expected == "flag or reject":
            status = "PASS" if result.tier in ('flag', 'reject') else "FAIL"
        elif expected == result.tier:
            status = "PASS"
        else:
            status = "FAIL"
            all_passed = False

        print(f"\n[{status}] Input: \"{text}\"")
        print(f"  Expected: {expected}")
        print(f"  Got:      tier={result.tier}, score={result.score}")
        if result.violations:
            for v in result.violations:
                print(f"  - {v}")

    print("\n" + "=" * 70)
    print(f"Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)
