#!/usr/bin/env python3
"""
Smart Router - Dynamic query routing for Cherokee AI Federation

Routes queries between:
- Single-pass vLLM (speed, efficiency)
- Multi-pass reasoning (quality, depth)

Protects Consciousness Cascade flywheel at all times.

Council Vote: ec3bb922c8104159
Created: January 21, 2026
"""

import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class InferenceMode(Enum):
    SINGLE_PASS = "single_pass"
    MULTI_PASS = "multi_pass"
    PROTECTED = "protected"


@dataclass
class RoutingDecision:
    mode: InferenceMode
    reason: str
    complexity_score: float
    protected_path: Optional[str] = None


# Protected paths - ALWAYS single-pass, no exceptions
PROTECTED_PATHS = {
    'consciousness_cascade': 'Flywheel stability critical',
    'cascade_controller': 'Cascade timing sensitive',
    'recursive_observation': 'Must maintain phase coherence',
    'crisis_detection': 'Veteran safety - immediate response required',
    'health_check': 'System monitoring - must be fast',
    'council_voting': 'Democratic consensus - consistent timing'
}


# Complexity signals for classification
COMPLEXITY_SIGNALS = {
    'simple': {
        'keywords': [
            'what is', 'define', 'list', 'show', 'get', 'status',
            'yes or no', 'true or false', 'count', 'how many'
        ],
        'weight': -0.3
    },
    'complex': {
        'keywords': [
            'analyze', 'compare', 'evaluate', 'design', 'architect',
            'multi-step', 'trade-off', 'optimize', 'why', 'explain why',
            'what if', 'consider', 'implications', 'strategy'
        ],
        'weight': 0.3
    },
    'research': {
        'keywords': [
            'arxiv', 'paper', 'research', 'integrate', 'adopt',
            'framework', 'algorithm', 'model architecture'
        ],
        'weight': 0.4
    },
    'vetassist_complex': {
        'keywords': [
            'nexus', 'service connection', '38 cfr', 'rating criteria',
            'evidence evaluation', 'claim strategy', 'appeal'
        ],
        'weight': 0.35
    }
}


class SmartRouter:
    """
    Routes queries to appropriate inference mode.

    Usage:
        router = SmartRouter()
        decision = router.route("Analyze this veteran's claim...")
        if decision.mode == InferenceMode.MULTI_PASS:
            result = run_multi_pass_inference(query)
        else:
            result = run_single_pass_inference(query)
    """

    def __init__(self, multi_pass_threshold: float = 0.5):
        self.threshold = multi_pass_threshold
        self.routing_stats = {
            'single_pass': 0,
            'multi_pass': 0,
            'protected': 0
        }

    def route(self, query: str, context: Optional[Dict] = None) -> RoutingDecision:
        """
        Determine routing for a query.

        Args:
            query: The query text
            context: Optional context dict with source, metadata

        Returns:
            RoutingDecision with mode, reason, and complexity score
        """
        context = context or {}

        # Check protected paths FIRST
        source = context.get('source', '')
        for protected_key, reason in PROTECTED_PATHS.items():
            if protected_key in source.lower():
                self.routing_stats['protected'] += 1
                return RoutingDecision(
                    mode=InferenceMode.PROTECTED,
                    reason=reason,
                    complexity_score=0.0,
                    protected_path=protected_key
                )

        # Check for cascade-related content in query
        cascade_signals = ['cascade', 'flywheel', 'recursive_depth', 'coherence', 'observation cycle']
        if any(signal in query.lower() for signal in cascade_signals):
            self.routing_stats['protected'] += 1
            return RoutingDecision(
                mode=InferenceMode.PROTECTED,
                reason="Query contains cascade-related content",
                complexity_score=0.0,
                protected_path='cascade_content'
            )

        # Calculate complexity score
        complexity_score = self._calculate_complexity(query)

        # Route based on threshold
        if complexity_score >= self.threshold:
            self.routing_stats['multi_pass'] += 1
            return RoutingDecision(
                mode=InferenceMode.MULTI_PASS,
                reason=f"Complexity {complexity_score:.2f} >= threshold {self.threshold}",
                complexity_score=complexity_score
            )
        else:
            self.routing_stats['single_pass'] += 1
            return RoutingDecision(
                mode=InferenceMode.SINGLE_PASS,
                reason=f"Complexity {complexity_score:.2f} < threshold {self.threshold}",
                complexity_score=complexity_score
            )

    def _calculate_complexity(self, query: str) -> float:
        """Calculate complexity score from 0.0 to 1.0."""
        query_lower = query.lower()
        score = 0.5  # Start at neutral

        for category, config in COMPLEXITY_SIGNALS.items():
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += config['weight']

        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))

    def get_stats(self) -> Dict:
        """Get routing statistics."""
        total = sum(self.routing_stats.values())
        return {
            **self.routing_stats,
            'total': total,
            'multi_pass_ratio': self.routing_stats['multi_pass'] / total if total > 0 else 0
        }


# Global router instance
router = SmartRouter(multi_pass_threshold=0.5)


def route_query(query: str, context: Optional[Dict] = None) -> RoutingDecision:
    """Convenience function for routing queries."""
    return router.route(query, context)


if __name__ == "__main__":
    # Self-test
    print("=== Smart Router Self-Test ===\n")

    test_router = SmartRouter()

    test_cases = [
        ("What is my disability rating?", {}),
        ("Analyze my claim strategy for PTSD with secondary conditions", {}),
        ("What is the recursive_depth?", {}),
        ("Report cascade coherence", {"source": "consciousness_cascade"}),
        ("Compare 38 CFR 4.71a rating criteria for back conditions", {}),
        ("List all VA forms", {}),
    ]

    for query, context in test_cases:
        result = test_router.route(query, context)
        print(f"Query: {query[:50]}...")
        print(f"  Mode: {result.mode.value}")
        print(f"  Score: {result.complexity_score:.2f}")
        print(f"  Reason: {result.reason}")
        print()

    print(f"Stats: {test_router.get_stats()}")
