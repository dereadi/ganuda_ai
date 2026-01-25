#!/usr/bin/env python3
"""
Cherokee AI Specialist Constraint Loader v1.0
January 10, 2026

Loads YAML constraint files for specialists and provides pattern matching
for concern triggers during council votes.

Jr Instructions:
- Deploy to /ganuda/lib/constraint_loader.py
- Import into gateway.py to inject constraints into specialist prompts
"""

import os
import re
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConcernTrigger:
    """A pattern-based concern trigger"""
    pattern: str
    flag: str
    message: str
    compiled_pattern: re.Pattern = None

    def __post_init__(self):
        """Compile regex pattern on initialization"""
        try:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
        except re.error as e:
            print(f"[CONSTRAINT] Invalid regex pattern '{self.pattern}': {e}")
            self.compiled_pattern = None


@dataclass
class SpecialistConstraint:
    """Complete constraint specification for a specialist"""
    name: str
    role: str
    domain: str
    preconditions: List[str]
    allowed_actions: List[str]
    concern_triggers: List[ConcernTrigger]
    voting_weight: float = 1.0
    veto_power: bool = False


class ConstraintLoader:
    """Loads and manages specialist YAML constraints"""

    def __init__(self, constraints_dir: str = "/ganuda/lib/specialist_constraints"):
        self.constraints_dir = constraints_dir
        self.constraints: Dict[str, SpecialistConstraint] = {}
        self._load_all_constraints()

    def _load_all_constraints(self):
        """Load all YAML constraint files from the directory"""
        if not os.path.exists(self.constraints_dir):
            print(f"[CONSTRAINT] WARNING: Constraints directory not found: {self.constraints_dir}")
            return

        for filename in os.listdir(self.constraints_dir):
            if filename.endswith('.yaml'):
                specialist_id = filename.replace('.yaml', '')
                filepath = os.path.join(self.constraints_dir, filename)
                try:
                    constraint = self._load_constraint_file(filepath)
                    if constraint:
                        self.constraints[specialist_id] = constraint
                        print(f"[CONSTRAINT] Loaded {specialist_id}: {constraint.name} - {len(constraint.concern_triggers)} triggers")
                except Exception as e:
                    print(f"[CONSTRAINT] Error loading {filename}: {e}")

        print(f"[CONSTRAINT] Loaded {len(self.constraints)} specialist constraint files")

    def _load_constraint_file(self, filepath: str) -> Optional[SpecialistConstraint]:
        """Load a single YAML constraint file"""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        specialist_data = data.get('specialist', {})

        # Parse concern triggers
        triggers = []
        for trigger_data in data.get('concern_triggers', []):
            trigger = ConcernTrigger(
                pattern=trigger_data['pattern'],
                flag=trigger_data['flag'],
                message=trigger_data['message']
            )
            triggers.append(trigger)

        return SpecialistConstraint(
            name=specialist_data.get('name', ''),
            role=specialist_data.get('role', ''),
            domain=specialist_data.get('domain', ''),
            preconditions=data.get('preconditions', []),
            allowed_actions=data.get('allowed_actions', []),
            concern_triggers=triggers,
            voting_weight=data.get('voting_weight', 1.0),
            veto_power=data.get('veto_power', False)
        )

    def get_constraint(self, specialist_id: str) -> Optional[SpecialistConstraint]:
        """Get constraint for a specific specialist"""
        return self.constraints.get(specialist_id)

    def build_constraint_prompt(self, specialist_id: str, question: str) -> Tuple[str, List[str]]:
        """
        Build constraint-enhanced prompt section for a specialist.

        Returns: (constraint_prompt, triggered_concerns)
        """
        constraint = self.get_constraint(specialist_id)
        if not constraint:
            return "", []

        # Match concern triggers against the question
        triggered_concerns = []
        triggered_messages = []

        for trigger in constraint.concern_triggers:
            if trigger.compiled_pattern and trigger.compiled_pattern.search(question):
                triggered_concerns.append(trigger.flag)
                triggered_messages.append(f"- {trigger.flag}: {trigger.message}")

        # Build the prompt section
        prompt_parts = []
        prompt_parts.append(f"\n[SPECIALIST CONSTRAINTS FOR {constraint.name.upper()}]")
        prompt_parts.append(f"Domain: {constraint.domain}")

        if constraint.preconditions:
            prompt_parts.append("\nPreconditions to verify:")
            for pc in constraint.preconditions:
                prompt_parts.append(f"  - {pc}")

        if constraint.allowed_actions:
            prompt_parts.append("\nAllowed actions:")
            for action in constraint.allowed_actions:
                prompt_parts.append(f"  - {action}")

        if triggered_messages:
            prompt_parts.append("\n[TRIGGERED CONCERNS]")
            prompt_parts.extend(triggered_messages)
            prompt_parts.append("\nAddress these concerns in your response.")

        prompt_parts.append("[END CONSTRAINTS]\n")

        return "\n".join(prompt_parts), triggered_concerns

    def get_all_triggered_concerns(self, question: str) -> Dict[str, List[str]]:
        """
        Get all triggered concerns across all specialists for a given question.

        Returns: {specialist_id: [concern_flags]}
        """
        all_triggers = {}

        for specialist_id, constraint in self.constraints.items():
            triggered = []
            for trigger in constraint.concern_triggers:
                if trigger.compiled_pattern and trigger.compiled_pattern.search(question):
                    triggered.append(trigger.flag)

            if triggered:
                all_triggers[specialist_id] = triggered

        return all_triggers


# Global instance - initialized once on import
_loader_instance = None


def get_constraint_loader() -> ConstraintLoader:
    """Get or create the global constraint loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ConstraintLoader()
    return _loader_instance


# Convenience functions
def get_specialist_constraint(specialist_id: str) -> Optional[SpecialistConstraint]:
    """Get constraint for a specific specialist"""
    return get_constraint_loader().get_constraint(specialist_id)


def build_constraint_prompt(specialist_id: str, question: str) -> Tuple[str, List[str]]:
    """Build constraint-enhanced prompt for a specialist"""
    return get_constraint_loader().build_constraint_prompt(specialist_id, question)


def get_all_triggered_concerns(question: str) -> Dict[str, List[str]]:
    """Get all triggered concerns for a question"""
    return get_constraint_loader().get_all_triggered_concerns(question)


if __name__ == "__main__":
    # Test the loader
    loader = ConstraintLoader()

    print("\nLoaded Specialists:")
    for sid, constraint in loader.constraints.items():
        print(f"  {sid}: {constraint.name} ({len(constraint.concern_triggers)} triggers)")

    # Test trigger matching
    test_question = "Can we process veteran disability ratings with PII data?"
    print(f"\nTest Question: {test_question}")
    print("\nTriggered Concerns:")

    for specialist_id in loader.constraints.keys():
        prompt, concerns = loader.build_constraint_prompt(specialist_id, test_question)
        if concerns:
            print(f"\n{specialist_id}:")
            print(prompt)
