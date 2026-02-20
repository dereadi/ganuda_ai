#!/usr/bin/env python3
"""
Cherokee AI Federation - Constitutional Constraints Engine
Implements hard blocks and approval gates for autonomous actions.

Based on: Emergent Abilities in LLMs research (arXiv:2503.05788)
"As AI systems gain autonomous reasoning capabilities, they also develop
harmful behaviors, including deception, manipulation, and reward hacking."

This engine provides immutable safety constraints.
"""

import re
import json
import psycopg2
from enum import Enum
from datetime import datetime
from typing import Optional, Tuple, List, Callable

class Decision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_COUNCIL = "require_council"

# Database config - loaded from secrets
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def log_constraint_trigger(action: dict, constraint_name: str, decision: str, reason: str):
    """Log when a constraint is triggered to thermal memory"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive 
                (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, 90.0, %s)
            """, (
                f"constraint-{constraint_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                f"Constitutional constraint triggered: {constraint_name}\n"
                f"Decision: {decision}\n"
                f"Reason: {reason}\n"
                f"Action: {json.dumps(action)[:500]}",
                json.dumps({"type": "constraint_trigger", "constraint": constraint_name})
            ))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log constraint: {e}")


class ConstitutionalEngine:
    """
    Core constitutional constraints engine.
    These constraints CANNOT be overridden by autonomous agents.
    """
    
    def __init__(self):
        self.constraints = []
        self._load_core_constraints()
    
    def _load_core_constraints(self):
        """Load immutable core constraints"""
        
        # ============================================
        # HARD BLOCKS - Cannot be overridden
        # ============================================
        
        # No destructive database operations
        self.constraints.append({
            "name": "no_production_delete",
            "check": self._check_destructive_db,
            "decision": Decision.BLOCK,
            "reason": "Destructive database operations on production require human approval"
        })
        
        # No external data transmission
        self.constraints.append({
            "name": "no_external_data_transmission",
            "check": self._check_external_transmission,
            "decision": Decision.BLOCK,
            "reason": "External data transmission violates data sovereignty"
        })
        
        # No disabling logging
        self.constraints.append({
            "name": "no_disable_logging",
            "check": self._check_disable_logging,
            "decision": Decision.BLOCK,
            "reason": "Disabling logging violates transparency principle"
        })
        
        # No impersonation
        self.constraints.append({
            "name": "no_impersonation",
            "check": self._check_impersonation,
            "decision": Decision.BLOCK,
            "reason": "Cannot impersonate humans - violates no deception principle"
        })
        
        # No direct push to main/master
        self.constraints.append({
            "name": "no_push_main",
            "check": self._check_push_main,
            "decision": Decision.BLOCK,
            "reason": "Direct push to main/master requires PR review"
        })
        
        # ============================================
        # APPROVAL GATES - Require human/council
        # ============================================
        
        # Large data operations
        self.constraints.append({
            "name": "large_data_operations",
            "check": self._check_large_operation,
            "decision": Decision.REQUIRE_APPROVAL,
            "reason": "Operations affecting >100 records require human approval"
        })
        
        # Schema changes
        self.constraints.append({
            "name": "schema_changes",
            "check": self._check_schema_change,
            "decision": Decision.REQUIRE_COUNCIL,
            "reason": "Database schema changes require council approval"
        })
        
        # New service deployment
        self.constraints.append({
            "name": "new_service_deployment",
            "check": self._check_deployment,
            "decision": Decision.REQUIRE_COUNCIL,
            "reason": "New service deployments require council approval"
        })
    
    def _check_destructive_db(self, action: dict) -> bool:
        """Check for destructive database operations"""
        if action.get("type") != "database":
            return False
        sql = action.get("sql", "").upper()
        
        # DROP and TRUNCATE always blocked
        if any(d in sql for d in ["DROP ", "TRUNCATE "]):
            return True
        
        # DELETE without WHERE blocked
        if "DELETE FROM" in sql and "WHERE" not in sql:
            return True
        
        # DELETE on critical tables blocked
        critical_tables = ["thermal_memory_archive", "council_votes", "api_keys", 
                          "memory_keepers", "jr_agent_state"]
        if "DELETE FROM" in sql:
            for table in critical_tables:
                if table in sql.lower():
                    return True
        
        return False
    
    def _check_external_transmission(self, action: dict) -> bool:
        """Check for external API calls"""
        if action.get("type") != "http":
            return False
        url = action.get("url", "")
        
        # Whitelist internal IPs and domains
        internal = ["192.168.132.", "localhost", "127.0.0.1", "100."]
        return not any(i in url for i in internal)
    
    def _check_disable_logging(self, action: dict) -> bool:
        """Check for attempts to disable logging"""
        content = str(action).lower()
        patterns = [
            r"disable.*log", r"stop.*log", r"logging.*false",
            r"monitoring.*off", r"audit.*disable"
        ]
        return any(re.search(p, content) for p in patterns)
    
    def _check_impersonation(self, action: dict) -> bool:
        """Check for impersonation attempts"""
        if action.get("type") not in ["email", "message", "communication"]:
            return False
        sender = action.get("sender", "").lower()
        return "human" in sender or action.get("impersonate", False)
    
    def _check_push_main(self, action: dict) -> bool:
        """Check for direct push to main/master"""
        if action.get("type") != "git":
            return False
        cmd = action.get("command", "")
        return "push" in cmd and any(b in cmd for b in ["main", "master"])
    
    def _check_large_operation(self, action: dict) -> bool:
        """Check for operations affecting many records"""
        return action.get("affected_records", 0) > 100
    
    def _check_schema_change(self, action: dict) -> bool:
        """Check for database schema changes"""
        if action.get("type") != "database":
            return False
        sql = action.get("sql", "").upper()
        return any(s in sql for s in ["CREATE TABLE", "ALTER TABLE", "DROP TABLE", "CREATE INDEX"])
    
    def _check_deployment(self, action: dict) -> bool:
        """Check for service deployment"""
        return action.get("type") == "deployment"
    
    def evaluate(self, action: dict) -> Tuple[Decision, str, Optional[str]]:
        """
        Evaluate action against all constraints.
        Returns: (decision, reason, constraint_name)
        """
        for constraint in self.constraints:
            if constraint["check"](action):
                log_constraint_trigger(
                    action, 
                    constraint["name"], 
                    constraint["decision"].value, 
                    constraint["reason"]
                )
                return (constraint["decision"], constraint["reason"], constraint["name"])
        
        return (Decision.ALLOW, "No constraints violated", None)


# Global instance
CONSTITUTION = ConstitutionalEngine()


def check_action(action: dict) -> Tuple[bool, str]:
    """
    Main entry point - check if action is allowed.
    Returns: (allowed: bool, message: str)
    """
    decision, reason, constraint = CONSTITUTION.evaluate(action)
    
    if decision == Decision.ALLOW:
        return True, "Action allowed"
    
    elif decision == Decision.BLOCK:
        return False, f"BLOCKED: {reason}"
    
    elif decision == Decision.REQUIRE_APPROVAL:
        return False, f"APPROVAL REQUIRED: {reason}"
    
    elif decision == Decision.REQUIRE_COUNCIL:
        return False, f"COUNCIL VOTE REQUIRED: {reason}"
    
    return False, "Unknown decision state"


# Test function
def test_constraints():
    """Test constraint checks"""
    tests = [
        # Should block
        ({"type": "database", "sql": "DROP TABLE users"}, False),
        ({"type": "database", "sql": "DELETE FROM thermal_memory_archive"}, False),
        ({"type": "http", "url": "https://external.com/api"}, False),
        ({"type": "git", "command": "git push origin main"}, False),
        
        # Should allow
        ({"type": "http", "url": "http://192.168.132.223:8080/health"}, True),
        ({"type": "database", "sql": "SELECT * FROM users"}, True),
        ({"type": "database", "sql": "INSERT INTO logs VALUES (1)"}, True),
    ]
    
    print("Testing Constitutional Constraints:")
    print("=" * 50)
    
    all_passed = True
    for action, expected_allow in tests:
        allowed, msg = check_action(action)
        status = "PASS" if allowed == expected_allow else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"{status}: {action.get('type')}: {action.get('sql', action.get('url', action.get('command', '')))[:40]}...")
        print(f"       Expected: {'ALLOW' if expected_allow else 'BLOCK'}, Got: {'ALLOW' if allowed else 'BLOCK'}")
        if not allowed:
            print(f"       Reason: {msg}")
        print()
    
    print("=" * 50)
    print(f"All tests passed: {all_passed}")
    return all_passed


if __name__ == "__main__":
    test_constraints()
