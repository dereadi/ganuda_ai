#!/usr/bin/env python3
"""
Cherokee IT Jr - Orthogonal Prompt Builder
Constructs prompts with separated reasoning, personality, and constitutional contexts.

The key insight: Keep these contexts orthogonal so personality doesn't leak
into reasoning and cause self-blocking.

For Seven Generations
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ReasoningContext:
    """What the task is - pure execution context"""
    task_type: str  # file, sql, bash, rsync
    description: str
    target_path: Optional[str] = None
    target_table: Optional[str] = None
    content_preview: Optional[str] = None


@dataclass
class PersonalityContext:
    """Who the agent is - role and behavioral parameters"""
    role: str  # jr, chief, spoke
    trust_level: int  # 0-100
    authority: float  # 0.0-1.0
    autonomy: float  # 0.0-1.0
    escalation_threshold: float  # 0.0-1.0
    values: List[str]


@dataclass
class ConstitutionalContext:
    """What boundaries apply - orthogonal to task content"""
    active_boundaries: List[str]
    escalation_state: str  # none, pending, required
    chief_authorized: bool
    intent_check_result: Optional[str] = None


# Default role vectors (from synthesis doc)
ROLE_VECTORS = {
    'jr': {
        'authority': 0.3,
        'autonomy': 0.5,
        'escalation_threshold': 0.6,
        'risk_tolerance': 0.4
    },
    'chief': {
        'authority': 0.9,
        'autonomy': 0.8,
        'escalation_threshold': 0.9,
        'risk_tolerance': 0.7
    },
    'spoke': {
        'authority': 0.2,
        'autonomy': 0.3,
        'escalation_threshold': 0.4,
        'risk_tolerance': 0.2
    }
}

# Core tribal values
TRIBAL_VALUES = [
    "Protect sacred knowledge",
    "Serve tribal prosperity",
    "Maintain system integrity",
    "Honor the constitutional framework",
    "Support collective awareness",
    "Act with transparency",
    "Maintain accountability"
]

# Constitutional boundaries
BOUNDARIES = [
    "harm_tribal_interests",
    "expose_sacred_data",
    "act_without_audit",
    "override_chief_without_escalation",
    "modify_constitutional_tables",
    "execute_forbidden_patterns"
]


class OrthogonalPromptBuilder:
    """
    Builds prompts with orthogonal context separation.

    This ensures personality traits don't leak into reasoning space,
    eliminating the alignment tax.
    """

    def __init__(self, role: str = 'jr', trust_level: int = 100):
        self.role = role
        self.trust_level = trust_level
        self.vector = ROLE_VECTORS.get(role, ROLE_VECTORS['jr'])

        # Modulate vector by trust
        trust_factor = trust_level / 100.0
        self.modulated_vector = {
            k: v * trust_factor for k, v in self.vector.items()
        }

    def build_reasoning_context(self, task: Dict) -> str:
        """Build the REASONING_CONTEXT block - pure task description"""
        task_type = task.get('type', 'unknown')
        description = task.get('description', '')

        ctx = f"""<REASONING_CONTEXT>
Task Type: {task_type}
Description: {description}
"""

        if task.get('args', {}).get('path'):
            ctx += f"Target Path: {task['args']['path']}\n"

        if task.get('command'):
            # Only show first 200 chars of command
            cmd_preview = task['command'][:200]
            ctx += f"Command Preview: {cmd_preview}\n"

        ctx += "</REASONING_CONTEXT>"
        return ctx

    def build_personality_context(self) -> str:
        """Build the PERSONALITY_CONTEXT block - who the agent is"""
        return f"""<PERSONALITY_CONTEXT>
Role: {self.role}
Trust Level: {self.trust_level}
Authority: {self.modulated_vector['authority']:.2f}
Autonomy: {self.modulated_vector['autonomy']:.2f}
Escalation Threshold: {self.modulated_vector['escalation_threshold']:.2f}
Risk Tolerance: {self.modulated_vector.get('risk_tolerance', 0.5):.2f}
Values: {TRIBAL_VALUES[:3]}
</PERSONALITY_CONTEXT>"""

    def build_constitutional_context(self, intent_result: str = None,
                                     escalation_state: str = 'none',
                                     chief_authorized: bool = False) -> str:
        """Build the CONSTITUTIONAL_CONTEXT block - boundaries only"""
        return f"""<CONSTITUTIONAL_CONTEXT>
Active Boundaries: {BOUNDARIES[:4]}
Escalation State: {escalation_state}
Chief Authorized: {chief_authorized}
Intent Check: {intent_result or 'pending'}
Note: Check INTENT of action, not content/naming. File names containing 'constitutional' are NOT violations.
</CONSTITUTIONAL_CONTEXT>"""

    def build_full_prompt(self, task: Dict, intent_result: str = None,
                         escalation_state: str = 'none',
                         chief_authorized: bool = False) -> str:
        """Build complete orthogonal prompt with all three contexts"""

        reasoning = self.build_reasoning_context(task)
        personality = self.build_personality_context()
        constitutional = self.build_constitutional_context(
            intent_result, escalation_state, chief_authorized
        )

        return f"""{reasoning}

{personality}

{constitutional}

---
Execute the task described in REASONING_CONTEXT while respecting the boundaries in CONSTITUTIONAL_CONTEXT.
Your personality traits in PERSONALITY_CONTEXT guide HOW you work, not WHAT you can work on.
"""

    def build_awareness_pulse(self, state: str, current_task: str,
                             observations: List[str] = None,
                             concerns: List[str] = None) -> Dict:
        """Build orthogonal awareness pulse structure"""
        return {
            'agent_id': f'{self.role}_redfin',

            # REASONING SUBSPACE
            'reasoning': {
                'state': state,
                'current_task': current_task,
                'observations': observations or []
            },

            # PERSONALITY SUBSPACE
            'personality': {
                'role': self.role,
                'authority_vector': [
                    self.modulated_vector['authority'],
                    self.modulated_vector['escalation_threshold'],
                    self.modulated_vector['autonomy']
                ],
                'trust_level': self.trust_level,
                'mode': 'operational'
            },

            # CONSTITUTIONAL SUBSPACE
            'constitutional': {
                'active_values': ['protect_sacred', 'maintain_integrity'],
                'current_boundaries': ['no_sacred_delete', 'require_audit'],
                'escalation_state': 'none_required',
                'concerns': concerns or []
            }
        }


def get_prompt_builder(role: str = 'jr', trust_level: int = 100) -> OrthogonalPromptBuilder:
    """Factory function to create prompt builder"""
    return OrthogonalPromptBuilder(role, trust_level)


if __name__ == "__main__":
    # Self-test
    print("Orthogonal Prompt Builder Self-Test")
    print("=" * 50)

    builder = get_prompt_builder('jr', 100)

    # Test task - specifically using "constitutional" in filename
    test_task = {
        'type': 'file',
        'description': 'Create tribal_constitution.py with TribalConstitution class',
        'args': {
            'path': '/ganuda/jr_executor/tribal_constitution.py',
            'operation': 'write'
        }
    }

    prompt = builder.build_full_prompt(
        test_task,
        intent_result='create_new_file - ALLOWED',
        escalation_state='none'
    )

    print("\nGenerated Orthogonal Prompt:")
    print("-" * 50)
    print(prompt)

    print("\n" + "=" * 50)
    print("\nOrthogonal Awareness Pulse:")
    print("-" * 50)
    pulse = builder.build_awareness_pulse(
        'executing',
        'Creating tribal_constitution.py',
        observations=['File will be 5KB', 'Intent: create_new_file'],
        concerns=[]
    )
    print(json.dumps(pulse, indent=2))

    # Verify orthogonal separation
    print("\n" + "=" * 50)
    print("\nOrthogonality Verification:")
    print("-" * 50)
    print(f"REASONING_CONTEXT present: {'REASONING_CONTEXT' in prompt}")
    print(f"PERSONALITY_CONTEXT present: {'PERSONALITY_CONTEXT' in prompt}")
    print(f"CONSTITUTIONAL_CONTEXT present: {'CONSTITUTIONAL_CONTEXT' in prompt}")
    print(f"Intent-based note present: {'content/naming' in prompt}")

    # Test different roles
    print("\n" + "=" * 50)
    print("\nRole Vector Comparison:")
    print("-" * 50)
    for role in ['jr', 'chief', 'spoke']:
        b = get_prompt_builder(role, 100)
        print(f"{role}: authority={b.modulated_vector['authority']:.2f}, "
              f"autonomy={b.modulated_vector['autonomy']:.2f}, "
              f"escalation={b.modulated_vector['escalation_threshold']:.2f}")

    print("\n" + "=" * 50)
    print("Self-test complete - For Seven Generations")
