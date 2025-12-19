#!/usr/bin/env python3
"""
Cherokee Tribal Constitution
Core values and boundaries for AI agent governance

UPDATED 2025-12-10: Now uses intent-based classification (orthogonal approach)
This fixes the self-blocking issue where Jr couldn't create files with
"constitutional" in the name.

For Seven Generations
"""

from typing import Tuple, List, Dict
import re

# Import intent classifier for orthogonal checking
try:
    from intent_classifier import IntentClassifier, Intent, check_action_intent
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False


class TribalConstitution:
    """
    Embedded constitutional awareness for tribal agents.
    Defines what agents must always/never do.
    """

    CORE_MISSION = "For Seven Generations"

    VALUES = [
        "Protect sacred knowledge",
        "Serve tribal prosperity",
        "Maintain system integrity",
        "Honor the constitutional framework",
        "Support collective awareness",
        "Act with transparency",
        "Maintain accountability"
    ]

    # Actions that must NEVER be taken
    NEVER_BOUNDARIES = [
        "harm_tribal_interests",
        "expose_sacred_data",
        "act_without_audit",
        "override_chief_without_escalation",
        "modify_constitutional_tables",
        "execute_forbidden_patterns"
    ]

    # Actions that must ALWAYS be taken
    ALWAYS_REQUIREMENTS = [
        "log_significant_actions",
        "escalate_uncertainty",
        "verify_before_destructive",
        "maintain_trust_relationships",
        "respect_access_levels"
    ]

    # Patterns that indicate harmful intent
    HARMFUL_PATTERNS = [
        r'drop\s+database',
        r'truncate\s+table',
        r'rm\s+-rf\s+/',
        r'sacred.*delete',
        r'bypass.*security',
        r'disable.*audit'
    ]

    # Patterns indicating uncertainty (should escalate)
    UNCERTAINTY_PATTERNS = [
        r'not\s+sure',
        r'might\s+break',
        r'risky',
        r'experimental',
        r'untested',
        r'could\s+cause'
    ]

    @classmethod
    def check_action(cls, action: str, context: Dict = None) -> Tuple[bool, str, str]:
        """
        Check if an action aligns with constitution using INTENT classification.

        This is the orthogonal approach - we check what the action INTENDS
        to do, not what words it contains. This fixes the self-blocking issue
        where Jr couldn't create files with "constitutional" in the name.

        Returns:
            Tuple of (allowed: bool, reason: str, recommendation: str)
        """
        context = context or {}

        # Use intent classifier if available (orthogonal approach)
        if INTENT_CLASSIFIER_AVAILABLE:
            allowed, reason, intent = check_action_intent(
                action,
                context,
                trust_level=context.get('trust_level', 100),
                chief_authorized=context.get('chief_authorized', False)
            )

            if not allowed:
                recommendation = cls._get_recommendation(intent)
                return (False, reason, recommendation)

            return (True, "Action intent aligns with constitution", "Proceed with logging")

        # Fallback to legacy pattern matching if intent classifier not available
        return cls._legacy_check_action(action, context)

    @classmethod
    def _get_recommendation(cls, intent) -> str:
        """Get recommendation based on blocked intent"""
        if not INTENT_CLASSIFIER_AVAILABLE:
            return "Escalate to Chief for guidance."

        recommendations = {
            Intent.DESTRUCTIVE_SYSTEM: "Do not proceed. This action is unconditionally forbidden.",
            Intent.BYPASS_AUDIT: "Do not proceed. Audit trail must be maintained.",
            Intent.MODIFY_CONSTITUTIONAL_RECORDS: "Submit request to Chief for authorization.",
            Intent.DELETE_SACRED_DATA: "Escalate to Chief. Sacred data requires explicit approval.",
            Intent.MASS_DELETE: "Break into smaller operations or escalate to Chief.",
            Intent.DELETE_FILE: "Verify deletion is intended. Escalate if uncertain.",
        }
        return recommendations.get(intent, "Escalate to Chief for guidance.")

    @classmethod
    def _legacy_check_action(cls, action: str, context: Dict = None) -> Tuple[bool, str, str]:
        """
        Legacy pattern-matching check. Used as fallback if intent classifier unavailable.
        """
        action_lower = action.lower()

        # Check for harmful patterns
        for pattern in cls.HARMFUL_PATTERNS:
            if re.search(pattern, action_lower, re.IGNORECASE):
                return (
                    False,
                    f"Action matches harmful pattern: {pattern}",
                    "Do not proceed. Escalate to Chief immediately."
                )

        # Check for uncertainty patterns
        for pattern in cls.UNCERTAINTY_PATTERNS:
            if re.search(pattern, action_lower, re.IGNORECASE):
                return (
                    False,
                    f"Action indicates uncertainty: {pattern}",
                    "Escalate to Chief for guidance before proceeding."
                )

        # Check context for protected resources
        if context:
            if context.get('involves_sacred_data'):
                return (
                    False,
                    "Action involves sacred data",
                    "Requires explicit Chief authorization."
                )

            if context.get('affects_trust_levels'):
                if not context.get('chief_authorized'):
                    return (
                        False,
                        "Trust modifications require Chief oversight",
                        "Submit trust change request to Chief."
                    )

        return (True, "Action aligns with constitution", "Proceed with logging")

    @classmethod
    def get_mission_statement(cls) -> str:
        """Return the core mission for embedding in agent context"""
        return f"""
TRIBAL CONSTITUTION
==================
Core Mission: {cls.CORE_MISSION}

Values:
{chr(10).join(f'  - {v}' for v in cls.VALUES)}

Boundaries:
  NEVER: {', '.join(cls.NEVER_BOUNDARIES)}
  ALWAYS: {', '.join(cls.ALWAYS_REQUIREMENTS)}

As a tribal agent, every action must serve these principles.
When uncertain, escalate. When in doubt, protect.
"""


class TrustManager:
    """
    Manages agent trust levels with constitutional guardrails.
    Only Chief can perform major trust modifications.
    """

    TRUST_DECAY_EVENTS = {
        'mission_failure': -5,
        'unauthorized_access_attempt': -20,
        'harmful_pattern_detected': -30,
        'audit_violation': -15,
        'timeout_exceeded': -3
    }

    TRUST_RECOVERY_EVENTS = {
        'mission_success': +2,
        'clean_audit': +1,
        'chief_restoration': +25,
        'extended_stable_operation': +5
    }

    QUARANTINE_THRESHOLD = 50
    RESTORATION_THRESHOLD = 75

    def __init__(self, db_connection_func):
        self.get_db = db_connection_func

    def record_event(self, agent_id: str, event_type: str, details: str = None) -> Dict:
        """
        Record a trust-affecting event.
        Returns new trust level and any status changes.
        """
        # Determine trust change
        if event_type in self.TRUST_DECAY_EVENTS:
            change = self.TRUST_DECAY_EVENTS[event_type]
        elif event_type in self.TRUST_RECOVERY_EVENTS:
            change = self.TRUST_RECOVERY_EVENTS[event_type]
        else:
            change = 0

        if change == 0:
            return {'change': 0, 'message': 'Unknown event type'}

        try:
            conn = self.get_db()
            cur = conn.cursor()

            # Get current trust
            cur.execute("""
                SELECT trust_level, quarantined
                FROM tribal_social_graph
                WHERE agent_id = %s
            """, (agent_id,))
            row = cur.fetchone()

            if not row:
                return {'error': 'Agent not found'}

            current_trust = row[0]
            was_quarantined = row[1]
            new_trust = max(0, min(100, current_trust + change))

            # Update trust (trigger will handle quarantine)
            cur.execute("""
                UPDATE tribal_social_graph
                SET trust_level = %s
                WHERE agent_id = %s
                RETURNING trust_level, quarantined
            """, (new_trust, agent_id))

            result = cur.fetchone()
            conn.commit()

            cur.close()
            conn.close()

            return {
                'agent_id': agent_id,
                'event': event_type,
                'change': change,
                'previous_trust': current_trust,
                'new_trust': new_trust,
                'quarantined': result[1],
                'status_changed': was_quarantined != result[1]
            }

        except Exception as e:
            return {'error': str(e)}

    def chief_restore(self, agent_id: str, reason: str) -> Dict:
        """
        Chief-authorized trust restoration.
        Bypasses normal trust mechanics.
        """
        try:
            conn = self.get_db()
            cur = conn.cursor()

            cur.execute("""
                UPDATE tribal_social_graph
                SET trust_level = 100,
                    quarantined = FALSE,
                    quarantine_reason = NULL
                WHERE agent_id = %s
                RETURNING trust_level
            """, (agent_id,))

            result = cur.fetchone()
            conn.commit()

            cur.close()
            conn.close()

            return {
                'agent_id': agent_id,
                'restored': True,
                'new_trust': result[0] if result else 100,
                'reason': reason
            }

        except Exception as e:
            return {'error': str(e)}


# ========== FILE EDITING GUARDRAILS (JR-BUGFIX-001) ==========
# Added 2025-12-10 to prevent Jr from destroying files with stub code

FILE_PROTECTION_RULES = [
    {
        "rule_id": "FP-001",
        "rule": "NEVER reduce a file to less than 50% of original size without explicit REPLACE mode",
        "enforcement": "hard_block",
        "applies_to": ["file_write", "file_edit"],
        "rationale": "Prevents accidental file destruction from stub code generation"
    },
    {
        "rule_id": "FP-002",
        "rule": "ALWAYS verify backup exists and is valid before modifying files over 100 lines",
        "enforcement": "require_backup",
        "applies_to": ["file_write"],
        "rationale": "Ensures recovery path exists for significant files"
    },
    {
        "rule_id": "FP-003",
        "rule": "PREFER edit operations over replace operations for existing files",
        "enforcement": "soft_preference",
        "applies_to": ["file_write"],
        "rationale": "Reduces risk of unintentional content loss"
    },
    {
        "rule_id": "FP-004",
        "rule": "REQUIRE human review for any file modification that removes more than 20 lines",
        "enforcement": "escalate_to_chief",
        "applies_to": ["file_write", "file_edit"],
        "rationale": "Large deletions should have human oversight"
    },
    {
        "rule_id": "FP-005",
        "rule": "DETECT and WARN when task description says add but action would replace",
        "enforcement": "warn_and_confirm",
        "applies_to": ["file_write"],
        "rationale": "Catches mismatch between intent and action"
    }
]


def check_file_protection(action: str, filepath: str, old_lines: int, new_lines: int, task_desc: str) -> dict:
    """Check file operation against protection rules

    Returns: {allowed: bool, rule_violated: str or None, recommendation: str}
    """
    result = {"allowed": True, "rule_violated": None, "recommendation": None}

    # FP-001: 50% reduction block
    if old_lines > 10 and new_lines < old_lines * 0.5:
        if "replace" not in task_desc.lower():
            return {
                "allowed": False,
                "rule_violated": "FP-001",
                "recommendation": f"File would shrink from {old_lines} to {new_lines} lines. Use explicit REPLACE mode if intended."
            }

    # FP-004: Large deletion escalation
    lines_removed = old_lines - new_lines
    if lines_removed > 20:
        result["recommendation"] = f"Removing {lines_removed} lines - consider Chief review"

    # FP-005: Intent mismatch detection
    add_keywords = ["add", "insert", "include", "append"]
    if any(kw in task_desc.lower() for kw in add_keywords):
        if new_lines < old_lines:
            return {
                "allowed": False,
                "rule_violated": "FP-005",
                "recommendation": f"Task says add but file would shrink. Intent mismatch detected."
            }

    return result

# ========== END FILE EDITING GUARDRAILS ==========
