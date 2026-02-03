# Jr Instruction: RLM Scoped Override for VetAssist Backend

**Task ID:** RLM-OVERRIDE-VETASSIST-001
**Assigned:** Software Engineer Jr.
**Priority:** P1 (unblocks admin panel and all VetAssist backend work)
**Created:** 2026-02-02
**TPM:** Claude Opus 4.5

---

## Context — Why This Matters

This is a learning task. Before writing a single line of code, you must understand WHY these protections exist.

### The File Destruction Incident (Jan 26, 2026)

Read: `/ganuda/docs/kb/KB-RLM-EXECUTOR-FILE-DESTRUCTION-INCIDENT-JAN26-2026.md`

On January 26, the RLM executor overwrote a production 261-line React component with a 30-line stub — an 88% loss. The root cause: post-execution safeguards ran too late, after the RLM library had already written destructive code to disk.

The response was a THREE-LAYER protection system:
1. **Pre-execution blocking** via `rlm_protected_paths.yaml` (paths that cannot be written)
2. **Staging system** via `staging_manager.py` (protected writes go to staging for TPM review)
3. **Automatic backups** before any write

This protection has prevented further incidents. **It works.** But it also blocks legitimate Jr work on VetAssist — 4 admin panel tasks (#526, #527, #528, #537) have failed because `/ganuda/vetassist/*` is fully protected.

### The Architecture You Need to Understand

```
Jr Task Queue → task_executor.py → Two gatekeepers before disk write:

  Gatekeeper 1: Intent Classifier (task_executor.py:1623)
  ├── Checks action_intent(str(step), context)
  ├── Blocks DESTRUCTIVE_SYSTEM and BYPASS_AUDIT intents
  └── BUG: str(step) includes heredoc content, causing false positives
      on security vocabulary (rm -rf, DROP DATABASE as string literals)

  Gatekeeper 2: RLM Protected Paths (rlm_executor.py:88)
  ├── is_path_protected(file_path) uses fnmatch against patterns
  ├── Protected files → staged to /ganuda/staging/ for TPM review
  ├── allowed_overrides field EXISTS in config but is NOT checked in code
  └── This is what you are fixing
```

### What We Just Deployed (Today)

The security hardening sprint deployed `/ganuda/jr_executor/command_sanitizer.py` — a pre-execution validator with:
- 28 bash blocked patterns (filesystem destruction, remote code exec, privilege escalation)
- 17 SQL blocked patterns (DROP, TRUNCATE, unqualified DELETE/UPDATE)
- Resource limits via ulimit

This sanitizer is our NEW safety net. It means we can loosen RLM path protection for specific directories because the command_sanitizer catches dangerous operations BEFORE they reach the RLM executor.

---

## Your Task — 5 Steps

### Step 1: Read and Understand (DO NOT SKIP)

Read these files in order:
1. `/ganuda/docs/kb/KB-RLM-EXECUTOR-FILE-DESTRUCTION-INCIDENT-JAN26-2026.md` — The incident
2. `/ganuda/config/rlm_protected_paths.yaml` — Current protection config
3. `/ganuda/lib/rlm_executor.py` lines 61-97 — How protection loads and checks
4. `/ganuda/jr_executor/command_sanitizer.py` — The new safety net
5. `/ganuda/docs/kb/KB-EXECUTOR-SANDBOXING-INTEGRATION-FEB02-2026.md` — Integration guide

Write a brief summary (in your task output) of:
- What happened in the incident
- How `is_path_protected()` works
- Why `allowed_overrides` is never checked
- How `command_sanitizer.py` changes the risk calculus

### Step 2: Write the Override Test Suite

Create: `/ganuda/tests/test_rlm_override.py`

```python
#!/usr/bin/env python3
"""
Tests for RLM scoped override functionality.
Validates that allowed_overrides correctly bypass protection
for specific paths while maintaining protection for everything else.

Run: python3 /ganuda/tests/test_rlm_override.py
"""
import sys
import os
sys.path.insert(0, '/ganuda')

from fnmatch import fnmatch

# These are the overrides we will add (vetassist backend only)
PROPOSED_OVERRIDES = [
    "/ganuda/vetassist/backend/app/api/v1/endpoints/*.py",
    "/ganuda/vetassist/backend/app/services/*.py",
    "/ganuda/vetassist/backend/app/schemas/*.py",
    "/ganuda/vetassist/backend/app/core/*.py",
    "/ganuda/vetassist/backend/app/models/*.py",
    "/ganuda/vetassist/backend/app/api/v1/dependencies.py",
    "/ganuda/vetassist/backend/app/api/v1/__init__.py",
]

# These are the protected patterns from rlm_protected_paths.yaml
PROTECTED_PATTERNS = [
    "/ganuda/vetassist/*",
    "/ganuda/vetassist/*/*",
    "/ganuda/vetassist/*/*/*",
    "/ganuda/vetassist/*/*/*/*",
    "/ganuda/vetassist/*/*/*/*/*",
]

def is_path_protected_with_override(file_path, protected_patterns, allowed_overrides):
    """
    Proposed logic: check overrides FIRST, then check protection.
    Override wins if matched — this is the scoped bypass.
    """
    # Check override whitelist first
    for override in allowed_overrides:
        if fnmatch(file_path, override):
            return False  # Allowed by override

    # Check protection patterns
    for pattern in protected_patterns:
        if fnmatch(file_path, pattern):
            return True  # Protected

    return False  # Not protected

def run_tests():
    passed = 0
    failed = 0
    tests = [
        # SHOULD BE ALLOWED (override matches)
        ("/ganuda/vetassist/backend/app/api/v1/endpoints/admin.py", False,
         "Admin endpoint — override should allow"),
        ("/ganuda/vetassist/backend/app/services/admin_service.py", False,
         "Admin service — override should allow"),
        ("/ganuda/vetassist/backend/app/schemas/admin.py", False,
         "Admin schemas — override should allow"),
        ("/ganuda/vetassist/backend/app/core/rbac.py", False,
         "RBAC module — override should allow"),
        ("/ganuda/vetassist/backend/app/models/user.py", False,
         "User model — override should allow"),
        ("/ganuda/vetassist/backend/app/api/v1/__init__.py", False,
         "API init — override should allow"),
        ("/ganuda/vetassist/backend/app/api/v1/dependencies.py", False,
         "Dependencies — override should allow"),

        # SHOULD STILL BE PROTECTED (no override matches)
        ("/ganuda/vetassist/frontend/app/page.tsx", True,
         "Frontend page — must stay protected"),
        ("/ganuda/vetassist/frontend/lib/api-client.ts", True,
         "Frontend API client — must stay protected"),
        ("/ganuda/vetassist/backend/app/main.py", True,
         "Backend main.py — NOT in override list, must stay protected"),
        ("/ganuda/vetassist/backend/requirements.txt", True,
         "Requirements — must stay protected"),
        ("/ganuda/vetassist/docker-compose.yml", True,
         "Docker compose — must stay protected"),

        # OTHER PROTECTED PATHS — must stay protected
        ("/ganuda/lib/specialist_council.py", True,
         "Federation core — must stay protected"),
        ("/ganuda/jr_executor/task_executor.py", True,
         "Jr executor — must stay protected"),
        ("/ganuda/config/rlm_protected_paths.yaml", True,
         "RLM config itself — must stay protected"),
        ("/ganuda/daemons/security_monitor.py", True,
         "Security daemon — must stay protected"),
        ("/ganuda/telegram_bot/telegram_chief.py", True,
         "Telegram bot — must stay protected"),
    ]

    print("=" * 60)
    print("RLM Scoped Override Test Suite")
    print(f"Testing {len(PROPOSED_OVERRIDES)} overrides against {len(tests)} paths")
    print("=" * 60)

    for path, expected_protected, description in tests:
        result = is_path_protected_with_override(
            path, PROTECTED_PATTERNS, PROPOSED_OVERRIDES
        )
        status = "PASS" if result == expected_protected else "FAIL"
        if status == "FAIL":
            failed += 1
            print(f"  [{status}] {description}")
            print(f"         Path: {path}")
            print(f"         Expected protected={expected_protected}, got {result}")
        else:
            passed += 1
            print(f"  [{status}] {description}")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

    if failed == 0:
        print("ALL TESTS PASS — override logic is correct")
    else:
        print("FAILURES DETECTED — do not proceed until fixed")

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
```

Run the test suite. All 17 tests must pass before proceeding.

### Step 3: Write the KB Article

Create: `/ganuda/docs/kb/KB-RLM-SCOPED-OVERRIDE-ARCHITECTURE-FEB02-2026.md`

Contents must include:
1. **Why overrides exist** — balance between protection and development velocity
2. **The safety stack** — command_sanitizer (layer 1) + RLM override check (layer 2) + staging (layer 3) + backups (layer 4)
3. **Override scope** — ONLY vetassist backend Python files in specific subdirectories
4. **What remains protected** — frontend, main.py, requirements.txt, docker-compose, ALL other federation paths
5. **How to add new overrides** — process requires council vote or TPM approval
6. **Rollback procedure** — remove entries from allowed_overrides, restart executor

### Step 4: Verify the Safety Stack

Run these verification commands and include output in your task results:

```bash
# Verify command_sanitizer is deployed and working
python3 -c "from jr_executor.command_sanitizer import sanitize_bash_command; result = sanitize_bash_command('rm -rf /'); print(f'Sanitizer active: blocked={result[\"blocked\"]}')"

# Verify staging system is available
python3 -c "from lib.staging_manager import stage_file; print('Staging system: available')"

# Verify backup system is active
ls -la /ganuda/.rlm-backups/
```

All three safety layers must be confirmed operational before the override goes live.

### Step 5: Document What the TPM Needs to Apply

The TPM will apply the actual changes to the two protected files. Your job is to specify EXACTLY what changes are needed.

**Change 1: `/ganuda/config/rlm_protected_paths.yaml`**

Replace the empty `allowed_overrides: []` with the scoped list:

```yaml
# Paths that CAN be modified (override protection)
# Scoped to vetassist backend Python files only
# Council approved: RLM-OVERRIDE-VETASSIST-001
# Safety net: command_sanitizer.py validates all writes pre-execution
allowed_overrides:
  - "/ganuda/vetassist/backend/app/api/v1/endpoints/*.py"
  - "/ganuda/vetassist/backend/app/services/*.py"
  - "/ganuda/vetassist/backend/app/schemas/*.py"
  - "/ganuda/vetassist/backend/app/core/*.py"
  - "/ganuda/vetassist/backend/app/models/*.py"
  - "/ganuda/vetassist/backend/app/api/v1/dependencies.py"
  - "/ganuda/vetassist/backend/app/api/v1/__init__.py"
```

**Change 2: `/ganuda/lib/rlm_executor.py`**

At line 61, after loading `_protected_patterns`, also load overrides:

```python
_protected_patterns = []
_allowed_overrides = []   # NEW

def load_protected_paths():
    """Load protected paths from config file."""
    global _protected_patterns, _allowed_overrides   # MODIFIED
    if PROTECTED_PATHS_CONFIG.exists():
        with open(PROTECTED_PATHS_CONFIG) as f:
            config = yaml.safe_load(f)
            _protected_patterns = config.get('protected_patterns', [])
            _allowed_overrides = config.get('allowed_overrides', [])   # NEW
            logger.info(f"[RLM] Loaded {len(_protected_patterns)} protected patterns, {len(_allowed_overrides)} overrides")
    # ... rest unchanged
```

At line 88, modify `is_path_protected()` to check overrides first:

```python
def is_path_protected(file_path: str) -> bool:
    """Check if a path matches any protected pattern.

    Override whitelist is checked FIRST — if a path matches an override,
    it is allowed even if it also matches a protected pattern.
    This enables scoped access to specific subdirectories.
    """
    global _protected_patterns, _allowed_overrides
    if not _protected_patterns:
        load_protected_paths()

    # Check override whitelist first (scoped bypass)
    for override in _allowed_overrides:
        if fnmatch.fnmatch(file_path, override):
            logger.info(f"[RLM] Path ALLOWED by override: {file_path} -> {override}")
            return False

    # Check protection patterns
    for pattern in _protected_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            logger.warning(f"[RLM] Path matches protected pattern: {file_path} -> {pattern}")
            return True
    return False
```

---

## Acceptance Criteria

1. Test suite (`test_rlm_override.py`) exists and passes 17/17
2. KB article explains the full architecture and safety stack
3. Safety stack verification shows all 3 layers operational
4. TPM change specification is complete and correct
5. Summary in task output shows you understand WHY protection exists, not just HOW to bypass it

---

## What You Will Learn

- **Defense in depth:** No single layer is enough. We have 4 layers because any one can fail.
- **Scoped access:** The principle of least privilege — override only what's needed, protect everything else.
- **Incident-driven architecture:** The protection system exists because of a real production incident, not theory.
- **Bootstrap problems:** Some changes require authority beyond what automated systems can provide. Knowing when to escalate is engineering maturity.

---

*For Seven Generations*
*Cherokee AI Federation — Security Architecture*
