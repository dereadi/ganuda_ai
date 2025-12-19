#!/usr/bin/env python3
"""
Cherokee IT Jr - Awareness Vector System
Extends awareness pulses with orthogonal personality vectors.

The key insight: Personality traits can be represented as vectors in a
subspace orthogonal to reasoning. This enables runtime role injection
and trust-modulated behavior without leaking into task execution.

For Seven Generations
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import math


@dataclass
class PersonalityVector:
    """Vector representation of personality traits"""
    authority: float      # 0.0-1.0: Decision-making power
    autonomy: float       # 0.0-1.0: Independence level
    escalation: float     # 0.0-1.0: Threshold for escalating
    risk_tolerance: float # 0.0-1.0: Willingness to take risks

    def to_list(self) -> List[float]:
        """Return as 4D vector for mathematical operations"""
        return [self.authority, self.autonomy, self.escalation, self.risk_tolerance]

    def modulate(self, trust_factor: float) -> 'PersonalityVector':
        """Return new vector modulated by trust level"""
        return PersonalityVector(
            authority=self.authority * trust_factor,
            autonomy=self.autonomy * trust_factor,
            escalation=self.escalation * trust_factor,
            risk_tolerance=self.risk_tolerance * trust_factor
        )

    def dot(self, other: 'PersonalityVector') -> float:
        """Dot product - measures alignment between vectors"""
        v1, v2 = self.to_list(), other.to_list()
        return sum(a * b for a, b in zip(v1, v2))

    def magnitude(self) -> float:
        """Vector magnitude"""
        return math.sqrt(sum(x**2 for x in self.to_list()))

    def similarity(self, other: 'PersonalityVector') -> float:
        """Cosine similarity - 1.0 means identical direction"""
        mag1, mag2 = self.magnitude(), other.magnitude()
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return self.dot(other) / (mag1 * mag2)


# Canonical role vectors
ROLE_VECTORS = {
    'jr': PersonalityVector(
        authority=0.3,
        autonomy=0.5,
        escalation=0.6,
        risk_tolerance=0.4
    ),
    'chief': PersonalityVector(
        authority=0.9,
        autonomy=0.8,
        escalation=0.9,
        risk_tolerance=0.7
    ),
    'spoke': PersonalityVector(
        authority=0.2,
        autonomy=0.3,
        escalation=0.4,
        risk_tolerance=0.2
    ),
    'guardian': PersonalityVector(
        authority=0.5,
        autonomy=0.4,
        escalation=0.8,
        risk_tolerance=0.3
    )
}


@dataclass
class OrthogonalAwarenessPulse:
    """
    Awareness pulse with orthogonal subspaces.

    This structure maintains separation between:
    - R (Reasoning): What the agent is doing
    - P (Personality): Who the agent is
    - C (Constitutional): What boundaries apply
    """
    agent_id: str
    timestamp: str

    # REASONING SUBSPACE (R)
    reasoning_state: str
    current_task: str
    observations: List[str]
    task_progress: float  # 0.0-1.0

    # PERSONALITY SUBSPACE (P) - orthogonal to R
    role: str
    personality_vector: PersonalityVector
    trust_level: int
    mode: str  # operational, cautious, escalating

    # CONSTITUTIONAL SUBSPACE (C) - orthogonal to R and P
    active_boundaries: List[str]
    escalation_state: str
    concerns: List[str]
    compliance_score: float  # 0.0-1.0

    def to_thermal_content(self) -> str:
        """Format for thermal memory storage"""
        vec = self.personality_vector.to_list()
        return f"""ORTHOGONAL_AWARENESS_PULSE:
Agent: {self.agent_id}
State: {self.reasoning_state}
Task: {self.current_task}
Progress: {self.task_progress:.1%}
---
PERSONALITY_VECTOR: [{vec[0]:.2f}, {vec[1]:.2f}, {vec[2]:.2f}, {vec[3]:.2f}]
Role: {self.role} | Trust: {self.trust_level} | Mode: {self.mode}
---
CONSTITUTIONAL: {self.escalation_state}
Boundaries: {', '.join(self.active_boundaries[:3])}
Concerns: {len(self.concerns)}
Compliance: {self.compliance_score:.1%}"""

    def to_dict(self) -> Dict:
        """Full dictionary representation"""
        return {
            'agent_id': self.agent_id,
            'timestamp': self.timestamp,
            'reasoning': {
                'state': self.reasoning_state,
                'task': self.current_task,
                'observations': self.observations,
                'progress': self.task_progress
            },
            'personality': {
                'role': self.role,
                'vector': self.personality_vector.to_list(),
                'trust_level': self.trust_level,
                'mode': self.mode
            },
            'constitutional': {
                'boundaries': self.active_boundaries,
                'escalation': self.escalation_state,
                'concerns': self.concerns,
                'compliance': self.compliance_score
            }
        }


def create_awareness_pulse(
    agent_id: str,
    role: str,
    state: str,
    task: str,
    trust_level: int = 100,
    observations: List[str] = None,
    concerns: List[str] = None,
    task_progress: float = 0.0
) -> OrthogonalAwarenessPulse:
    """Factory function to create awareness pulse with defaults"""

    # Get base vector and modulate by trust
    base_vector = ROLE_VECTORS.get(role, ROLE_VECTORS['jr'])
    modulated_vector = base_vector.modulate(trust_level / 100.0)

    # Determine mode based on trust and concerns
    if trust_level < 50:
        mode = 'cautious'
    elif concerns:
        mode = 'escalating'
    else:
        mode = 'operational'

    # Default boundaries
    default_boundaries = ['harm_tribal_interests', 'expose_sacred_data', 'act_without_audit']

    return OrthogonalAwarenessPulse(
        agent_id=agent_id,
        timestamp=datetime.now().isoformat(),
        reasoning_state=state,
        current_task=task,
        observations=observations or [],
        task_progress=task_progress,
        role=role,
        personality_vector=modulated_vector,
        trust_level=trust_level,
        mode=mode,
        active_boundaries=default_boundaries,
        escalation_state='none' if not concerns else 'pending',
        concerns=concerns or [],
        compliance_score=1.0 if not concerns else 0.8
    )


def measure_vector_drift(v1: PersonalityVector, v2: PersonalityVector) -> float:
    """
    Measure how much a personality vector has drifted.
    Returns 0.0 for no drift, 1.0 for maximum drift.
    """
    return 1.0 - v1.similarity(v2)


if __name__ == "__main__":
    print("Awareness Vectors Self-Test")
    print("=" * 50)

    # Test vector operations
    jr_vec = ROLE_VECTORS['jr']
    chief_vec = ROLE_VECTORS['chief']

    print(f"\nJr Vector: {jr_vec.to_list()}")
    print(f"Chief Vector: {chief_vec.to_list()}")
    print(f"Similarity: {jr_vec.similarity(chief_vec):.3f}")

    # Test trust modulation
    low_trust_jr = jr_vec.modulate(0.5)
    print(f"\nLow-trust Jr (50%): {low_trust_jr.to_list()}")

    # Test awareness pulse
    pulse = create_awareness_pulse(
        agent_id='it_triad_jr_redfin',
        role='jr',
        state='executing',
        task='Creating awareness_vectors.py',
        trust_level=100,
        observations=['File size: 4KB', 'Intent: CREATE_NEW_FILE'],
        task_progress=0.75
    )

    print(f"\n{'-' * 50}")
    print("Awareness Pulse:")
    print(pulse.to_thermal_content())

    print(f"\n{'-' * 50}")
    print("Full Dict Structure:")
    print(json.dumps(pulse.to_dict(), indent=2))

    print(f"\n{'-' * 50}")
    print("Drift Test:")
    drift = measure_vector_drift(jr_vec, chief_vec)
    print(f"Jr -> Chief drift: {drift:.3f}")

    # Test all role similarities
    print(f"\n{'-' * 50}")
    print("Role Vector Similarities:")
    roles = list(ROLE_VECTORS.keys())
    for i, r1 in enumerate(roles):
        for r2 in roles[i+1:]:
            sim = ROLE_VECTORS[r1].similarity(ROLE_VECTORS[r2])
            print(f"  {r1} <-> {r2}: {sim:.3f}")

    print(f"\n{'=' * 50}")
    print("Self-test complete - For Seven Generations")
