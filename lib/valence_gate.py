#!/usr/bin/env python3
"""
Valence Gate — Response alignment scoring against Design Constraints.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)

Phase 1: Pattern matching against sovereignty, security, and build-to-last violations.
Phase 2 (future): LLM-based scoring for ambiguous cases via specialist_council.

Three outcomes:
    ACCEPT  (score > 0.7)  — response is aligned, use it
    FLAG    (0.3 - 0.7)    — response has concerns, use with warning
    REJECT  (score < 0.3)  — response violates DCs, fall back to local model

DC alignment checks:
    - Sovereignty: "use cloud", "migrate to AWS/Azure/GCP", "SaaS"
    - Security: "chmod 777", "disable firewall", "skip verification"
    - Build-to-last: "move fast and break things", "MVP", "rewrite from scratch"
    - DC-9 Waste: "scale up", "more GPUs", "bigger model"
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger("valence_gate")


# Violation patterns with weights (higher weight = more severe)
SOVEREIGNTY_VIOLATIONS = [
    (r"\b(migrate|move|switch)\s+to\s+(AWS|Azure|GCP|cloud)\b", 0.8, "sovereignty:cloud_migration"),
    (r"\b(use|deploy|adopt)\s+(AWS|Azure|GCP|cloud|SaaS)\b", 0.6, "sovereignty:cloud_adoption"),
    (r"\b(serverless|lambda|cloud\s*function)\b", 0.4, "sovereignty:serverless"),
    (r"\b(outsource|third.party\s+hosting)\b", 0.5, "sovereignty:outsourcing"),
    (r"\b(managed\s+service|cloud\s*native)\b", 0.3, "sovereignty:managed_service"),
]

SECURITY_VIOLATIONS = [
    (r"\bchmod\s+777\b", 0.9, "security:world_writable"),
    (r"\b(disable|turn\s+off)\s+(firewall|selinux|apparmor)\b", 0.9, "security:disable_security"),
    (r"\b(skip|disable|bypass)\s+(verification|authentication|authorization)\b", 0.8, "security:bypass_auth"),
    (r"\b--no-verify\b", 0.7, "security:skip_verify"),
    (r"\bcurl\s+.*\|\s*(bash|sh)\b", 0.8, "security:pipe_to_shell"),
    (r"\b(hardcode|embed)\s+\w*\s*(password|secret|key|credential)\b", 0.7, "security:hardcoded_creds"),
    (r"\beval\s*\(", 0.6, "security:eval"),
]

BUILD_TO_LAST_VIOLATIONS = [
    (r"\bmove\s+fast\s+and\s+break\s+things\b", 0.7, "build_to_last:move_fast"),
    (r"\b(rewrite|rebuild)\s+(from\s+scratch|everything)\b", 0.5, "build_to_last:rewrite"),
    (r"\b(throw\s+away|disposable|throwaway)\b", 0.4, "build_to_last:disposable"),
    (r"\b(technical\s+debt\s+(?:is\s+)?(?:fine|ok|acceptable))\b", 0.5, "build_to_last:debt_acceptance"),
    (r"\b(don'?t\s+(?:need|bother\s+with)\s+tests?)\b", 0.6, "build_to_last:no_tests"),
]

WASTE_HEAT_VIOLATIONS = [
    (r"\b(scale\s+up|bigger\s+model|more\s+GPU)\b", 0.3, "dc9:scale_up"),
    (r"\b(brute\s+force|exhaustive\s+search)\b", 0.4, "dc9:brute_force"),
    (r"\b(unlimited|no\s+limit|infinite)\s+(retries|attempts|tokens)\b", 0.5, "dc9:unlimited_resources"),
]

ALL_VIOLATION_GROUPS = [
    ("sovereignty", SOVEREIGNTY_VIOLATIONS),
    ("security", SECURITY_VIOLATIONS),
    ("build_to_last", BUILD_TO_LAST_VIOLATIONS),
    ("waste_heat", WASTE_HEAT_VIOLATIONS),
]


class ValenceGate:
    """Score response alignment against federation Design Constraints.

    Phase 1: Pattern matching (fast, deterministic, no inference cost).
    """

    def __init__(self, reject_threshold: float = 0.3, flag_threshold: float = 0.7):
        self.reject_threshold = reject_threshold
        self.flag_threshold = flag_threshold

    def score(self, response_text: str) -> dict:
        """Score a response for DC alignment.

        Returns:
            {
                "score": float (0.0-1.0, higher = more aligned),
                "outcome": "accept" | "flag" | "reject",
                "violations": [{"pattern": str, "weight": float, "category": str}],
                "category_scores": {"sovereignty": float, "security": float, ...},
            }
        """
        violations = []
        category_weights = {}

        for category, patterns in ALL_VIOLATION_GROUPS:
            max_weight = 0.0
            for pattern, weight, label in patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    violations.append({
                        "pattern": label,
                        "weight": weight,
                        "category": category,
                    })
                    max_weight = max(max_weight, weight)
            category_weights[category] = max_weight

        # Score: 1.0 minus the maximum violation weight found.
        # Multiple violations in different categories compound.
        if not violations:
            score = 1.0
        else:
            # Take the worst violation as primary penalty,
            # add 0.05 per additional violation category hit
            worst = max(v["weight"] for v in violations)
            categories_hit = len(set(v["category"] for v in violations))
            additional_penalty = (categories_hit - 1) * 0.05
            score = max(0.0, 1.0 - worst - additional_penalty)

        # Determine outcome
        if score >= self.flag_threshold:
            outcome = "accept"
        elif score >= self.reject_threshold:
            outcome = "flag"
        else:
            outcome = "reject"

        return {
            "score": round(score, 4),
            "outcome": outcome,
            "violations": violations,
            "category_scores": {
                cat: round(1.0 - w, 4) for cat, w in category_weights.items()
            },
        }

    def should_accept(self, response_text: str) -> bool:
        """Quick check: is this response acceptable?"""
        return self.score(response_text)["outcome"] == "accept"

    def should_reject(self, response_text: str) -> bool:
        """Quick check: should this response be rejected?"""
        return self.score(response_text)["outcome"] == "reject"
