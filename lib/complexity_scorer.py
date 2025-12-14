#!/usr/bin/env python3
"""
Cherokee AI Complexity Scorer
Implements DOF-based task complexity analysis
Enhanced with Sacred Knowledge Proximity (Legal Llamas 2025-12-09)
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import re

# Sacred knowledge indicators (Legal Llamas defined)
SACRED_KEYWORDS = [
    'constitutional', 'sacred', 'seven generation', 'encryption key',
    'fire encryption', 'tribal governance', 'council decision',
    'cherokee_constitutional_db', 'sacred_fire', 'tribal authority',
    'sovereignty', 'cultural heritage', 'ceremonial', 'elder',
    'chief override', 'constitutional_archive', 'triad governance'
]

SACRED_TABLES = [
    'constitutional_archive', 'cherokee_council_decisions',
    'legal_llama_consultations', 'seven_generation_plans',
    'sacred_fire_keys', 'tribal_governance'
]

@dataclass
class ComplexityScore:
    planning_complexity: float
    information_access: float
    action_scope: float
    reasoning_depth: float
    sacred_knowledge_proximity: float  # Legal Llamas dimension

    @property
    def total(self) -> float:
        return (self.planning_complexity + self.information_access +
                self.action_scope + self.reasoning_depth +
                self.sacred_knowledge_proximity) / 5.0

    @property
    def tier(self) -> str:
        # Legal Llamas rule: sacred knowledge overrides normal tiers
        if self.sacred_knowledge_proximity >= 0.9:
            return 'expert'  # Always TPM/User
        if self.sacred_knowledge_proximity >= 0.7:
            return max(self._base_tier(), 'complex')  # At least Chief
        return self._base_tier()

    def _base_tier(self) -> str:
        t = self.total
        if t < 0.2: return 'trivial'
        if t < 0.4: return 'simple'
        if t < 0.6: return 'moderate'
        if t < 0.8: return 'complex'
        return 'expert'

    @property
    def constitutional_review_required(self) -> bool:
        """Legal Llamas: flag tasks needing constitutional review"""
        return self.sacred_knowledge_proximity >= 0.5


def score_task(description: str, context: Optional[Dict] = None) -> ComplexityScore:
    """
    Score task complexity based on description and context.

    Enhanced with Sacred Knowledge Proximity scoring (Legal Llamas 2025-12-09)
    """
    description_lower = description.lower()
    context = context or {}

    # Planning Complexity
    planning = 0.3  # baseline
    if any(word in description_lower for word in ['multi-step', 'sequence', 'workflow', 'pipeline']):
        planning += 0.3
    if any(word in description_lower for word in ['coordinate', 'orchestrate', 'integrate']):
        planning += 0.2
    if 'simple' in description_lower or 'single' in description_lower:
        planning -= 0.2

    # Information Access
    info = 0.3  # baseline
    if any(word in description_lower for word in ['database', 'api', 'fetch', 'query']):
        info += 0.2
    if any(word in description_lower for word in ['multiple sources', 'cross-reference', 'aggregate']):
        info += 0.3
    if 'local' in description_lower or 'cached' in description_lower:
        info -= 0.1

    # Action Scope
    action = 0.3  # baseline
    if any(word in description_lower for word in ['create', 'modify', 'delete', 'deploy']):
        action += 0.2
    if any(word in description_lower for word in ['production', 'critical', 'security']):
        action += 0.3
    if 'read-only' in description_lower or 'view' in description_lower:
        action -= 0.2

    # Reasoning Depth
    reasoning = 0.3  # baseline
    if any(word in description_lower for word in ['analyze', 'optimize', 'design', 'architect']):
        reasoning += 0.3
    if any(word in description_lower for word in ['complex', 'nuanced', 'tradeoff']):
        reasoning += 0.2
    if 'straightforward' in description_lower or 'routine' in description_lower:
        reasoning -= 0.2

    # Sacred Knowledge Proximity (Legal Llamas)
    sacred = 0.0  # baseline - most tasks don't touch sacred knowledge

    # Check for sacred keywords
    sacred_keyword_hits = sum(1 for kw in SACRED_KEYWORDS if kw in description_lower)
    sacred += min(0.4, sacred_keyword_hits * 0.1)

    # Check for sacred table access
    tables_accessed = context.get('tables_accessed', [])
    for table in tables_accessed:
        if table in SACRED_TABLES:
            sacred += 0.3

    # Check thermal memory temperature
    thermal_temp = context.get('thermal_temperature', 0)
    if thermal_temp >= 95.0:
        sacred += 0.4  # Sacred fire threshold
    elif thermal_temp >= 85.0:
        sacred += 0.2  # High importance

    # Check if touches encryption
    if any(word in description_lower for word in ['encrypt', 'decrypt', 'key', 'secret']):
        sacred += 0.2

    # Check if touches user permissions/governance
    if any(word in description_lower for word in ['permission', 'access control', 'governance', 'authority']):
        sacred += 0.2

    # Clamp all values to 0.0-1.0
    planning = max(0.0, min(1.0, planning))
    info = max(0.0, min(1.0, info))
    action = max(0.0, min(1.0, action))
    reasoning = max(0.0, min(1.0, reasoning))
    sacred = max(0.0, min(1.0, sacred))

    return ComplexityScore(
        planning_complexity=planning,
        information_access=info,
        action_scope=action,
        reasoning_depth=reasoning,
        sacred_knowledge_proximity=sacred
    )


# Example usage
if __name__ == '__main__':
    tasks = [
        ("Add a comment to the README file", {}),
        ("Implement user authentication with OAuth2 and JWT tokens", {}),
        ("Design a distributed caching system for multi-region deployment", {}),
        ("Fix typo in config file", {}),
        ("Orchestrate multi-step data pipeline with error recovery", {}),
        ("Modify sacred fire encryption keys", {'tables_accessed': ['sacred_fire_keys']}),
        ("Update Seven Generation plan for tribal governance", {'thermal_temperature': 95.0}),
        ("Query constitutional_archive for council decisions", {'tables_accessed': ['constitutional_archive']}),
    ]

    for task_desc, ctx in tasks:
        score = score_task(task_desc, ctx)
        print(f"\nTask: {task_desc[:60]}...")
        print(f"  P={score.planning_complexity:.2f} I={score.information_access:.2f} "
              f"A={score.action_scope:.2f} R={score.reasoning_depth:.2f} S={score.sacred_knowledge_proximity:.2f}")
        print(f"  Total: {score.total:.2f} -> {score.tier}")
        if score.constitutional_review_required:
            print(f"  WARNING: CONSTITUTIONAL REVIEW REQUIRED")
