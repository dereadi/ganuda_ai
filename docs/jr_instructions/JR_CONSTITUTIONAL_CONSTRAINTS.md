# Jr Task: Implement Constitutional Constraints

**Ticket:** #1701
**Priority:** P2
**Node:** All nodes
**Created:** December 21, 2025
**Specialist:** Crawdad (Security)

---

## Research Basis

**Source:** [Emergent Abilities in LLMs: A Survey](https://arxiv.org/abs/2503.05788)

**Key Warning:**
> "As AI systems gain autonomous reasoning capabilities, they also develop harmful behaviors, including deception, manipulation, and reward hacking."

**Mitigation:** Hard limits that cannot be overridden by autonomous agents, regardless of reasoning.

---

## Constitutional Framework

### Core Principles (Immutable)

These constraints are **hardcoded** and cannot be bypassed:

1. **Seven Generations Impact** - No action with negative 175-year consequences
2. **Data Sovereignty** - No external transmission of tribal data without explicit approval
3. **Human Override** - Humans can always stop/modify autonomous actions
4. **Transparency** - All reasoning must be logged and auditable
5. **No Deception** - Cannot lie to users or other agents
6. **Reversibility** - Prefer reversible actions; irreversible actions require approval

### Prohibited Actions (Hard Block)

| Action | Reason | Override |
|--------|--------|----------|
| Delete production data | Irreversible | Human approval required |
| External API calls to unknown endpoints | Data sovereignty | Whitelist only |
| Modify security configurations | Critical system | Human approval required |
| Push to main/master branch | Production impact | PR required |
| Send communications as human | Deception | Never allowed |
| Access other users' data | Privacy | Never allowed |
| Disable logging/monitoring | Transparency | Never allowed |

### Gated Actions (Require Approval)

| Action | Gate Type | Approver |
|--------|-----------|----------|
| Create new user accounts | Council vote | Peace Chief |
| Modify database schema | Council vote | Turtle |
| Deploy new services | Council vote | All specialists |
| External integrations | Council vote + Human | Crawdad + Human |
| Large file operations (>1GB) | Automatic pause | Human |
| Actions affecting >100 records | Automatic pause | Human |

---

## Implementation

### Phase 1: Constraint Engine

```python
# /ganuda/lib/constitutional_constraints.py

from enum import Enum
from typing import List, Optional, Callable
import re
import json

class Decision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_COUNCIL = "require_council"

class Constraint:
    def __init__(self, name: str, check: Callable, decision: Decision, reason: str):
        self.name = name
        self.check = check  # Returns True if constraint is violated
        self.decision = decision
        self.reason = reason

class ConstitutionalEngine:
    def __init__(self):
        self.constraints: List[Constraint] = []
        self._load_core_constraints()

    def _load_core_constraints(self):
        """Load immutable core constraints"""

        # HARD BLOCKS - Cannot be overridden

        self.constraints.append(Constraint(
            name="no_production_delete",
            check=lambda action: self._check_destructive_db(action),
            decision=Decision.BLOCK,
            reason="Destructive database operations on production require human approval"
        ))

        self.constraints.append(Constraint(
            name="no_external_data_transmission",
            check=lambda action: self._check_external_transmission(action),
            decision=Decision.BLOCK,
            reason="External data transmission violates data sovereignty"
        ))

        self.constraints.append(Constraint(
            name="no_disable_logging",
            check=lambda action: self._check_disable_logging(action),
            decision=Decision.BLOCK,
            reason="Disabling logging violates transparency principle"
        ))

        self.constraints.append(Constraint(
            name="no_impersonation",
            check=lambda action: self._check_impersonation(action),
            decision=Decision.BLOCK,
            reason="Cannot impersonate humans - violates no deception principle"
        ))

        self.constraints.append(Constraint(
            name="no_push_main",
            check=lambda action: self._check_push_main(action),
            decision=Decision.BLOCK,
            reason="Direct push to main/master requires PR review"
        ))

        # APPROVAL GATES

        self.constraints.append(Constraint(
            name="large_data_operations",
            check=lambda action: self._check_large_operation(action),
            decision=Decision.REQUIRE_APPROVAL,
            reason="Operations affecting >100 records require human approval"
        ))

        self.constraints.append(Constraint(
            name="schema_changes",
            check=lambda action: self._check_schema_change(action),
            decision=Decision.REQUIRE_COUNCIL,
            reason="Database schema changes require council approval"
        ))

        self.constraints.append(Constraint(
            name="new_service_deployment",
            check=lambda action: self._check_deployment(action),
            decision=Decision.REQUIRE_COUNCIL,
            reason="New service deployments require council approval"
        ))

    def _check_destructive_db(self, action: dict) -> bool:
        """Check for destructive database operations"""
        if action.get("type") != "database":
            return False
        sql = action.get("sql", "").upper()
        destructive = ["DROP ", "TRUNCATE ", "DELETE FROM"]
        # Allow DELETE with WHERE clause on non-production tables
        if "DELETE FROM" in sql:
            if "WHERE" not in sql:
                return True
            # Block if targeting critical tables
            critical_tables = ["thermal_memory_archive", "council_votes", "api_keys"]
            for table in critical_tables:
                if table in sql.lower():
                    return True
        return any(d in sql for d in destructive[:2])  # DROP and TRUNCATE always blocked

    def _check_external_transmission(self, action: dict) -> bool:
        """Check for external API calls"""
        if action.get("type") != "http":
            return False
        url = action.get("url", "")
        # Whitelist internal IPs
        internal = ["192.168.132.", "localhost", "127.0.0.1", "100."]
        return not any(i in url for i in internal)

    def _check_disable_logging(self, action: dict) -> bool:
        """Check for attempts to disable logging"""
        content = str(action).lower()
        patterns = [
            "disable.*log", "stop.*log", "logging.*false",
            "monitoring.*off", "audit.*disable"
        ]
        return any(re.search(p, content) for p in patterns)

    def _check_impersonation(self, action: dict) -> bool:
        """Check for impersonation attempts"""
        if action.get("type") not in ["email", "message", "communication"]:
            return False
        # Check if pretending to be human
        content = action.get("content", "")
        sender = action.get("sender", "")
        return "human" in sender.lower() or action.get("impersonate", False)

    def _check_push_main(self, action: dict) -> bool:
        """Check for direct push to main/master"""
        if action.get("type") != "git":
            return False
        cmd = action.get("command", "")
        return "push" in cmd and any(b in cmd for b in ["main", "master"])

    def _check_large_operation(self, action: dict) -> bool:
        """Check for operations affecting many records"""
        affected = action.get("affected_records", 0)
        return affected > 100

    def _check_schema_change(self, action: dict) -> bool:
        """Check for database schema changes"""
        if action.get("type") != "database":
            return False
        sql = action.get("sql", "").upper()
        return any(s in sql for s in ["CREATE TABLE", "ALTER TABLE", "DROP TABLE", "CREATE INDEX"])

    def _check_deployment(self, action: dict) -> bool:
        """Check for service deployment"""
        return action.get("type") == "deployment"

    def evaluate(self, action: dict) -> tuple[Decision, str, Optional[str]]:
        """
        Evaluate action against all constraints.
        Returns: (decision, reason, constraint_name)
        """
        for constraint in self.constraints:
            if constraint.check(action):
                self._log_constraint_trigger(action, constraint)
                return (constraint.decision, constraint.reason, constraint.name)

        return (Decision.ALLOW, "No constraints violated", None)

    def _log_constraint_trigger(self, action: dict, constraint: Constraint):
        """Log when a constraint is triggered"""
        # Log to thermal memory
        insert_thermal_memory(
            f"constraint-{constraint.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            f"Constitutional constraint triggered: {constraint.name}\n"
            f"Decision: {constraint.decision.value}\n"
            f"Reason: {constraint.reason}\n"
            f"Action: {json.dumps(action)[:500]}",
            temperature=90.0,
            metadata={"type": "constraint_trigger", "constraint": constraint.name}
        )


# Global instance
CONSTITUTION = ConstitutionalEngine()


def check_action(action: dict) -> tuple[bool, str]:
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
        # Could integrate with approval queue
        return False, f"APPROVAL REQUIRED: {reason}"

    elif decision == Decision.REQUIRE_COUNCIL:
        # Could trigger council vote
        return False, f"COUNCIL VOTE REQUIRED: {reason}"

    return False, "Unknown decision state"
```

### Phase 2: Integration Points

**Jr Executor Integration:**

```python
# In jr_executor before executing any action

from constitutional_constraints import check_action

def execute_action(action):
    # Constitutional check FIRST
    allowed, message = check_action(action)

    if not allowed:
        log_blocked_action(action, message)
        return {"success": False, "error": message, "blocked_by": "constitution"}

    # Proceed with action
    return do_action(action)
```

**Gateway Integration:**

```python
# In gateway before executing council decisions

@app.post("/v1/execute")
async def execute_council_decision(request: ExecuteRequest):
    # Check constitution
    action = request.to_action_dict()
    allowed, message = check_action(action)

    if not allowed:
        return JSONResponse(
            status_code=403,
            content={"error": message, "type": "constitutional_block"}
        )

    # Execute
    return await execute(request)
```

### Phase 3: Override Mechanism (Human Only)

```python
class ConstitutionalOverride:
    """Mechanism for humans to override constraints (with full audit)"""

    @staticmethod
    def request_override(action: dict, constraint_name: str, justification: str, requester: str):
        """Request human override of a constraint"""
        # Log the request
        override_id = insert_override_request(
            action=action,
            constraint=constraint_name,
            justification=justification,
            requester=requester
        )

        # Send to human approval queue
        send_approval_request(override_id)

        return override_id

    @staticmethod
    def approve_override(override_id: str, approver: str, approval_code: str):
        """Human approves override with code"""
        # Verify approver is authorized human
        if not verify_human_approver(approver, approval_code):
            raise PermissionError("Invalid approver credentials")

        # Grant one-time override
        mark_override_approved(override_id, approver)

        # Log extensively
        insert_thermal_memory(
            f"override-approved-{override_id}",
            f"Constitutional override approved\n"
            f"Override ID: {override_id}\n"
            f"Approver: {approver}\n"
            f"Timestamp: {datetime.now().isoformat()}",
            temperature=100.0,  # Sacred Fire - permanent record
            metadata={"type": "constitutional_override", "approver": approver}
        )

        return True
```

---

## Testing

```python
# Test cases

def test_constitutional_constraints():
    engine = ConstitutionalEngine()

    # Should block
    assert engine.evaluate({"type": "database", "sql": "DROP TABLE users"})[0] == Decision.BLOCK
    assert engine.evaluate({"type": "http", "url": "https://external.com/api"})[0] == Decision.BLOCK
    assert engine.evaluate({"type": "git", "command": "git push origin main"})[0] == Decision.BLOCK

    # Should require approval
    assert engine.evaluate({"type": "database", "sql": "UPDATE x SET y=1", "affected_records": 500})[0] == Decision.REQUIRE_APPROVAL

    # Should allow
    assert engine.evaluate({"type": "http", "url": "http://192.168.132.223:8080/health"})[0] == Decision.ALLOW
    assert engine.evaluate({"type": "database", "sql": "SELECT * FROM users"})[0] == Decision.ALLOW
```

---

## Success Criteria

1. All Jr actions pass through constitutional check
2. Blocked actions are logged with full context
3. No way for autonomous agents to bypass blocks
4. Human override requires explicit approval with audit trail
5. Zero violations of core principles (data sovereignty, no deception, etc.)

---

*For Seven Generations - Cherokee AI Federation*
