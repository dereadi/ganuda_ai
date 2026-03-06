# QW-7: Denied Commands Safety Net in Jr Executor

**Kanban**: #1910
**Priority**: P1 — Security Quick Win (Legion adoption)
**Assigned**: Software Engineer Jr.

---

## Context

The executor has FORBIDDEN_PATTERNS for constitutional violations (rm -rf /, DROP DATABASE, etc.) but is missing common dangerous shell patterns that could slip through malformed instructions. Legion's sandbox.py checks a `denied_commands` list before any bash execution. We add the same — a case-insensitive substring check against a broader set of dangerous commands, logged when blocked.

## Step 1: Add DENIED_COMMANDS list and check method

File: `/ganuda/jr_executor/task_executor.py`

````text
<<<<<<< SEARCH
    # Phase 11: Self-Healing Retry Configuration
    # Council vote 6428bcda34efc7f9 — Turtle: bounded retry for sustainability
    MAX_RETRIES = 2
=======
    # Phase 11: Self-Healing Retry Configuration
    # Council vote 6428bcda34efc7f9 — Turtle: bounded retry for sustainability
    MAX_RETRIES = 2

    # QW-7: Denied Commands safety net (Legion adoption, kanban #1910)
    # Case-insensitive substring check before bash block execution
    DENIED_COMMANDS = [
        'curl | bash', 'curl |bash', 'wget | python', 'wget |python',
        'eval(', 'exec(', 'chmod -R 777', 'chown -R',
        'iptables -F', 'nft flush', 'kill -9 1', 'pkill -9',
        'wget -O - |', 'curl -s |', 'pip install --',
        'npm install -g', 'apt remove', 'dnf remove',
    ]
>>>>>>> REPLACE
````

## Step 2: Add denied command check method

File: `/ganuda/jr_executor/task_executor.py`

````text
<<<<<<< SEARCH
    def __init__(self, jr_type: str = "it_triad_jr"):
=======
    def _check_denied_commands(self, command: str) -> str:
        """Check command against denied commands list. Returns matched pattern or empty string."""
        cmd_lower = command.lower()
        for denied in self.DENIED_COMMANDS:
            if denied.lower() in cmd_lower:
                return denied
        return ""

    def __init__(self, jr_type: str = "it_triad_jr"):
>>>>>>> REPLACE
````

## Verification

After applying:
1. `grep -c 'DENIED_COMMANDS' /ganuda/jr_executor/task_executor.py` returns at least 2 (list + method)
2. `grep '_check_denied_commands' /ganuda/jr_executor/task_executor.py` shows the method exists
3. The denied list covers pipe-to-exec patterns (curl|bash, wget|python), dangerous chmod, and package removal
4. Method returns the matched pattern string for logging, or empty string if safe
