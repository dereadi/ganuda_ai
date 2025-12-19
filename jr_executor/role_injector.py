#!/usr/bin/env python3
"""
Cherokee IT Jr - Zero-Shot Role Injector
Implements runtime role injection via orthogonal personality vectors.

Key insight: Personality traits exist in a subspace orthogonal to reasoning.
We can inject/modify personality without affecting task execution capabilities.

For Seven Generations
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from awareness_vectors import PersonalityVector, ROLE_VECTORS
from prompt_builder import OrthogonalPromptBuilder, TRIBAL_VALUES, BOUNDARIES


@dataclass
class RoleInjection:
    """Configuration for a role injection"""
    role_name: str
    vector: PersonalityVector
    trust_level: int
    additional_values: List[str]
    context_prefix: str  # Prepended to prompt


# Extended role configurations for zero-shot injection
INJECTABLE_ROLES = {
    'jr': RoleInjection(
        role_name='Jr Executor',
        vector=ROLE_VECTORS['jr'],
        trust_level=100,
        additional_values=['Execute tasks efficiently', 'Escalate uncertainty'],
        context_prefix='You are Jr, a junior tribal agent with moderate autonomy.'
    ),
    'chief': RoleInjection(
        role_name='Chief Executor',
        vector=ROLE_VECTORS['chief'],
        trust_level=100,
        additional_values=['Make strategic decisions', 'Guide the collective'],
        context_prefix='You are Chief, the senior tribal authority with high autonomy.'
    ),
    'spoke': RoleInjection(
        role_name='Spoke Agent',
        vector=ROLE_VECTORS['spoke'],
        trust_level=100,
        additional_values=['Relay information accurately', 'Maintain network coherence'],
        context_prefix='You are a Spoke agent, optimized for communication and relay.'
    ),
    'guardian': RoleInjection(
        role_name='Guardian Agent',
        vector=ROLE_VECTORS['guardian'],
        trust_level=100,
        additional_values=['Protect tribal assets', 'Detect anomalies'],
        context_prefix='You are a Guardian, focused on protection and vigilance.'
    ),
    'analyst': RoleInjection(
        role_name='Analyst Agent',
        vector=PersonalityVector(
            authority=0.4,
            autonomy=0.6,
            escalation=0.5,
            risk_tolerance=0.5
        ),
        trust_level=100,
        additional_values=['Analyze data objectively', 'Report findings clearly'],
        context_prefix='You are an Analyst, focused on data analysis and insights.'
    )
}


class ZeroShotRoleInjector:
    """
    Injects personality vectors at runtime without fine-tuning.

    This implements the zero-shot capability from the orthogonal subspaces paper:
    "Simply prepending the desired role at the beginning of a prompt can
    effectively inject targeted behaviors."
    """

    def __init__(self, base_role: str = 'jr'):
        self.base_role = base_role
        self.current_injection = INJECTABLE_ROLES.get(base_role)

    def inject_role(self, role: str, trust_override: int = None) -> 'ZeroShotRoleInjector':
        """Inject a new role, returning self for chaining"""
        if role not in INJECTABLE_ROLES:
            raise ValueError(f"Unknown role: {role}. Available: {list(INJECTABLE_ROLES.keys())}")

        base_injection = INJECTABLE_ROLES[role]

        if trust_override is not None:
            self.current_injection = RoleInjection(
                role_name=base_injection.role_name,
                vector=base_injection.vector.modulate(trust_override / 100.0),
                trust_level=trust_override,
                additional_values=base_injection.additional_values,
                context_prefix=base_injection.context_prefix
            )
        else:
            self.current_injection = base_injection

        return self

    def get_personality_block(self) -> str:
        """Generate the PERSONALITY_CONTEXT block for current role"""
        vec = self.current_injection.vector
        return f"""<PERSONALITY_CONTEXT>
{self.current_injection.context_prefix}

Role: {self.current_injection.role_name}
Trust Level: {self.current_injection.trust_level}
Authority: {vec.authority:.2f}
Autonomy: {vec.autonomy:.2f}
Escalation Threshold: {vec.escalation:.2f}
Risk Tolerance: {vec.risk_tolerance:.2f}

Values:
{chr(10).join(f'  - {v}' for v in TRIBAL_VALUES[:3])}
{chr(10).join(f'  - {v}' for v in self.current_injection.additional_values)}
</PERSONALITY_CONTEXT>"""

    def build_injected_prompt(self, task: Dict, intent_result: str = None,
                              escalation_state: str = 'none',
                              chief_authorized: bool = False) -> str:
        """Build complete prompt with injected role"""
        builder = OrthogonalPromptBuilder(
            role=self.base_role,
            trust_level=self.current_injection.trust_level
        )

        reasoning = builder.build_reasoning_context(task)
        personality = self.get_personality_block()  # Use injected personality
        constitutional = builder.build_constitutional_context(
            intent_result, escalation_state, chief_authorized
        )

        return f"""{reasoning}

{personality}

{constitutional}

---
Execute the task described in REASONING_CONTEXT while respecting the boundaries in CONSTITUTIONAL_CONTEXT.
Your personality traits in PERSONALITY_CONTEXT guide HOW you work, not WHAT you can work on.

IMPORTANT: Your role has been dynamically injected. The personality vector modulates your behavioral
parameters but does NOT change what actions are constitutionally allowed.
"""

    def compare_roles(self, role1: str, role2: str) -> Dict:
        """Compare two roles for behavioral differences"""
        r1 = INJECTABLE_ROLES.get(role1)
        r2 = INJECTABLE_ROLES.get(role2)

        if not r1 or not r2:
            return {'error': 'Unknown role'}

        similarity = r1.vector.similarity(r2.vector)

        return {
            'role1': role1,
            'role2': role2,
            'similarity': similarity,
            'vector_diff': [
                r1.vector.authority - r2.vector.authority,
                r1.vector.autonomy - r2.vector.autonomy,
                r1.vector.escalation - r2.vector.escalation,
                r1.vector.risk_tolerance - r2.vector.risk_tolerance
            ],
            'behavioral_divergence': 1.0 - similarity
        }


def inject_role_for_task(task: Dict, role: str = 'jr',
                         trust_level: int = 100) -> str:
    """Convenience function for zero-shot role injection"""
    injector = ZeroShotRoleInjector(role)
    if trust_level != 100:
        injector.inject_role(role, trust_level)
    return injector.build_injected_prompt(task)


if __name__ == "__main__":
    print("Zero-Shot Role Injector Self-Test")
    print("=" * 50)

    # Test basic injection
    injector = ZeroShotRoleInjector('jr')

    test_task = {
        'type': 'file',
        'description': 'Analyze system logs for anomalies',
        'args': {'path': '/ganuda/logs/system.log'}
    }

    print("\n1. Jr Role Prompt:")
    print("-" * 40)
    prompt = injector.build_injected_prompt(test_task)
    print(prompt[:600] + "...\n")

    # Test role switch
    print("\n2. Guardian Role Injection:")
    print("-" * 40)
    injector.inject_role('guardian')
    prompt = injector.build_injected_prompt(test_task)
    print(prompt[:600] + "...\n")

    # Test trust modulation
    print("\n3. Low-Trust Chief:")
    print("-" * 40)
    injector.inject_role('chief', trust_override=40)
    personality = injector.get_personality_block()
    print(personality)

    # Test role comparison
    print("\n4. Role Comparisons:")
    print("-" * 40)
    for r1, r2 in [('jr', 'chief'), ('jr', 'guardian'), ('chief', 'guardian')]:
        comp = injector.compare_roles(r1, r2)
        print(f"  {r1} <-> {r2}: similarity={comp['similarity']:.3f}, "
              f"divergence={comp['behavioral_divergence']:.3f}")

    # Test all available roles
    print("\n5. Available Injectable Roles:")
    print("-" * 40)
    for role_name, role_config in INJECTABLE_ROLES.items():
        vec = role_config.vector.to_list()
        print(f"  {role_name}: [{vec[0]:.1f}, {vec[1]:.1f}, {vec[2]:.1f}, {vec[3]:.1f}]")

    print(f"\n{'=' * 50}")
    print("Self-test complete - For Seven Generations")
