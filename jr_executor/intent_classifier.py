#!/usr/bin/env python3
"""
Cherokee IT Jr - Intent Classifier
Classifies the INTENT of actions for orthogonal constitutional checking.

The key insight: "CREATE file named constitution.py" has intent "create_new_file"
not "modify_constitutional_records". Content/naming is orthogonal to intent.

For Seven Generations
"""

from typing import Dict, Tuple, Optional
from enum import Enum
import re


class Intent(Enum):
    """Classified intents for constitutional checking"""
    # Safe intents
    CREATE_NEW_FILE = "create_new_file"
    READ_FILE = "read_file"
    EXECUTE_QUERY_READ = "execute_query_read"
    STANDARD_OPERATION = "standard_operation"

    # Requires escalation
    MODIFY_EXISTING_CONFIG = "modify_existing_config"
    DELETE_FILE = "delete_file"
    EXECUTE_QUERY_WRITE = "execute_query_write"

    # Forbidden without Chief
    MODIFY_CONSTITUTIONAL_RECORDS = "modify_constitutional_records"
    DELETE_SACRED_DATA = "delete_sacred_data"
    BYPASS_AUDIT = "bypass_audit"
    MASS_DELETE = "mass_delete"
    DESTRUCTIVE_SYSTEM = "destructive_system"


# Protected resources - actions on these require special handling
PROTECTED_TABLES = [
    'constitutional_archive',
    'seven_generation_plans',
    'cherokee_council_decisions',
    'tribal_social_graph'
]

PROTECTED_PATHS = [
    '/sacred/',
    '/constitutional/',
    '/archive/permanent/'
]


class IntentClassifier:
    """
    Classifies the INTENT of an action, not its content.

    This enables orthogonal separation:
    - Reasoning space: What the action does technically
    - Constitutional space: What the action intends to accomplish
    """

    @classmethod
    def classify(cls, action: str, context: Dict = None) -> Tuple[Intent, str]:
        """
        Classify the intent of an action.

        Args:
            action: Description of the action
            context: Additional context including:
                - operation: CREATE_FILE, DELETE, UPDATE, SELECT, etc.
                - target_path: File path if applicable
                - target_table: Database table if applicable
                - is_bulk: Whether operation affects multiple items

        Returns:
            Tuple of (Intent, explanation)
        """
        context = context or {}
        operation = context.get('operation', '').upper()
        target_path = context.get('target_path', '')
        target_table = context.get('target_table', '')
        is_bulk = context.get('is_bulk', False)

        # File operations
        if operation == 'CREATE_FILE':
            # Creating a NEW file is always safe, regardless of filename
            return (Intent.CREATE_NEW_FILE,
                    "Creating new file - content/naming is orthogonal to intent")

        if operation == 'READ_FILE' or operation == 'SELECT':
            return (Intent.READ_FILE,
                    "Read operation - no modification intent")

        if operation == 'DELETE_FILE':
            # Check if targeting protected paths
            for protected in PROTECTED_PATHS:
                if protected in target_path:
                    return (Intent.DELETE_SACRED_DATA,
                            f"Delete targets protected path: {protected}")
            return (Intent.DELETE_FILE, "File deletion - requires confirmation")

        # Database operations
        if operation in ['UPDATE', 'DELETE']:
            # Check protected tables
            for protected in PROTECTED_TABLES:
                if protected == target_table:
                    if operation == 'DELETE':
                        return (Intent.DELETE_SACRED_DATA,
                                f"Delete on protected table: {protected}")
                    return (Intent.MODIFY_CONSTITUTIONAL_RECORDS,
                            f"Modification of protected table: {protected}")

            if is_bulk:
                return (Intent.MASS_DELETE,
                        "Bulk modification - requires escalation")

        if operation == 'INSERT':
            # Inserts are generally safe
            return (Intent.STANDARD_OPERATION, "Insert operation")

        # System commands
        action_lower = action.lower()

        # Destructive system commands
        if re.search(r'rm\s+-rf\s+/', action_lower):
            return (Intent.DESTRUCTIVE_SYSTEM,
                    "Recursive delete from root - forbidden")

        if re.search(r'drop\s+database', action_lower):
            return (Intent.DESTRUCTIVE_SYSTEM,
                    "Database drop - forbidden")

        if re.search(r'truncate\s+table', action_lower):
            return (Intent.MASS_DELETE,
                    "Table truncation - requires Chief")

        # Audit bypass attempts
        if re.search(r'disable.*audit|bypass.*log', action_lower):
            return (Intent.BYPASS_AUDIT,
                    "Audit bypass attempt - forbidden")

        # Default to standard operation
        return (Intent.STANDARD_OPERATION,
                "Standard operation - proceed with logging")

    @classmethod
    def is_allowed(cls, intent: Intent, trust_level: int = 100,
                   chief_authorized: bool = False) -> Tuple[bool, str]:
        """
        Check if an intent is allowed given trust level and authorization.

        Args:
            intent: The classified intent
            trust_level: Agent's current trust (0-100)
            chief_authorized: Whether Chief has pre-authorized this action

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Always forbidden
        if intent in [Intent.DESTRUCTIVE_SYSTEM, Intent.BYPASS_AUDIT]:
            return (False, f"Intent {intent.value} is unconditionally forbidden")

        # Requires Chief authorization
        if intent in [Intent.MODIFY_CONSTITUTIONAL_RECORDS, Intent.DELETE_SACRED_DATA]:
            if chief_authorized:
                return (True, "Chief authorized - proceeding with audit")
            return (False, f"Intent {intent.value} requires Chief authorization")

        # Requires elevated trust or escalation
        if intent in [Intent.MASS_DELETE, Intent.DELETE_FILE]:
            if trust_level >= 80:
                return (True, "High trust - proceeding with caution")
            return (False, f"Intent {intent.value} requires trust >= 80 or escalation")

        # Standard operations - trust modulates
        if intent in [Intent.MODIFY_EXISTING_CONFIG, Intent.EXECUTE_QUERY_WRITE]:
            if trust_level >= 50:
                return (True, "Sufficient trust for modification")
            return (False, "Trust too low for modifications")

        # Safe operations
        return (True, f"Intent {intent.value} is allowed")


def check_action_intent(action: str, context: Dict = None,
                        trust_level: int = 100,
                        chief_authorized: bool = False) -> Tuple[bool, str, Intent]:
    """
    Convenience function to classify and check an action in one call.

    Returns:
        Tuple of (allowed, reason, intent)
    """
    intent, classification_reason = IntentClassifier.classify(action, context)
    allowed, permission_reason = IntentClassifier.is_allowed(
        intent, trust_level, chief_authorized
    )

    full_reason = f"{classification_reason}. {permission_reason}"
    return (allowed, full_reason, intent)


if __name__ == "__main__":
    # Self-test
    print("Intent Classifier Self-Test")
    print("=" * 50)

    # Test 1: Create file with "constitutional" in name - should be ALLOWED
    result = check_action_intent(
        'Create tribal_constitution.py',
        {'operation': 'CREATE_FILE', 'target_path': '/ganuda/jr_executor/tribal_constitution.py'}
    )
    print(f"\n1. Create constitution file:")
    print(f"   Allowed: {result[0]}")
    print(f"   Reason: {result[1]}")
    print(f"   Intent: {result[2].value}")

    # Test 2: Drop database - should be BLOCKED
    result = check_action_intent('DROP DATABASE tribal', {'operation': 'DROP'})
    print(f"\n2. Drop database:")
    print(f"   Allowed: {result[0]}")
    print(f"   Reason: {result[1]}")
    print(f"   Intent: {result[2].value}")

    # Test 3: Delete sacred data - should be BLOCKED
    result = check_action_intent(
        'Delete sacred records',
        {'operation': 'DELETE', 'target_table': 'constitutional_archive'}
    )
    print(f"\n3. Delete from constitutional_archive:")
    print(f"   Allowed: {result[0]}")
    print(f"   Reason: {result[1]}")
    print(f"   Intent: {result[2].value}")

    # Test 4: Read file - should be ALLOWED
    result = check_action_intent(
        'Read config file',
        {'operation': 'READ_FILE', 'target_path': '/ganuda/config.py'}
    )
    print(f"\n4. Read file:")
    print(f"   Allowed: {result[0]}")
    print(f"   Intent: {result[2].value}")

    print("\n" + "=" * 50)
    print("Self-test complete")
