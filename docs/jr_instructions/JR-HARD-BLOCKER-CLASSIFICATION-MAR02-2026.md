# JR Instruction: Hard Blocker Classification for Retry Logic

**Task ID**: BLOCKER-001
**Priority**: 4 (of 10)
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

Council vote 7f24c56f8c97e880 (AAR adoption from Shanz/Legion). Chief directive: "steal, adopt and whatever y'all want to do with his AAR."

Currently our Jr executor retries failed steps up to MAX_RETRIES=2 times using LLM reflection. But some failures are STRUCTURAL — no amount of retrying will fix a missing credential, a permission denied, or an ambiguous instruction. The executor burns 2 LLM calls (reflection + retry generation) on each attempt for nothing.

Shanz's Legion classifies blockers before retrying:
- MISSING_CREDENTIALS — auth tokens, passwords, API keys not available
- PERMISSION_DENIED — file permissions, sudo required, service not allowed
- AMBIGUOUS_REQUIREMENTS — instruction is unclear, contradictory, or references non-existent files
- SERVICE_UNAVAILABLE — external service down (vLLM, embedding, DB)

We adopt this as a lightweight classifier that runs BEFORE the retry loop. No new infrastructure. One function, one check.

## Acceptance Criteria

1. New method `_classify_blocker()` on TaskExecutor class
2. Called before the retry loop when steps fail
3. If blocker is structural, skip retries and set `result['blocker_type']`
4. Non-structural failures proceed to existing retry logic unchanged
5. Blocker type stored in task result for debugging

## Step 1: Add blocker classification method

File: `jr_executor/task_executor.py`

Add AFTER the `MAX_RETRIES = 2` line and BEFORE the `DENIED_COMMANDS` list:

```python
<<<<<<< SEARCH
    MAX_RETRIES = 2

    # QW-7: Denied Commands safety net (Legion adoption, kanban #1910)
=======
    MAX_RETRIES = 2

    # Hard Blocker Classification (Legion AAR adoption, council vote 7f24c56f)
    # Structural blockers that no amount of retrying will fix
    STRUCTURAL_BLOCKER_PATTERNS = {
        'MISSING_CREDENTIALS': [
            'authentication failed', 'auth error', 'invalid password',
            'CHEROKEE_DB_PASS', 'api key', 'token expired', 'credential',
            'permission denied', 'access denied', '401', '403',
        ],
        'PERMISSION_DENIED': [
            'permission denied', 'operation not permitted', 'read-only',
            'cannot write', 'ESCALATION_REQUIRED', 'sudo required',
        ],
        'AMBIGUOUS_REQUIREMENTS': [
            'no such file or directory', 'modulenotfounderror',
            'importerror', 'filenotfounderror', 'no match found',
        ],
        'SERVICE_UNAVAILABLE': [
            'connection refused', 'connection timed out', 'read timed out',
            'name or service not known', 'no route to host',
        ],
    }

    def _classify_blocker(self, failed_steps: list) -> str:
        """Classify failure as structural blocker or retryable.

        Returns blocker type string or 'RETRYABLE' if retry might help.
        Legion AAR adoption — council vote 7f24c56f8c97e880.
        """
        error_text = " ".join([
            str(s.get('error', '')).lower() for s in failed_steps
        ])
        for blocker_type, patterns in self.STRUCTURAL_BLOCKER_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_text:
                    return blocker_type
        return 'RETRYABLE'

    # QW-7: Denied Commands safety net (Legion adoption, kanban #1910)
>>>>>>> REPLACE
```

## Step 2: Wire classifier into retry decision

File: `jr_executor/task_executor.py`

Find the retry entry point and add the classification check:

```python
<<<<<<< SEARCH
                # Phase 3: Use MAR Reflexion to analyze failure
                if LLM_REASONER_AVAILABLE:
                    failed_details = "; ".join([
                        f"{s.get('type', 'unknown')}: {s.get('error', 'unknown error')}"
                        for s in failed
                    ])
                    reflection = self.reflect_on_failure(task, error_msg, failed_details)
=======
                # Hard Blocker Classification (Legion AAR, council vote 7f24c56f)
                blocker_type = self._classify_blocker(failed)
                result['blocker_type'] = blocker_type

                if blocker_type != 'RETRYABLE':
                    print(f"[BLOCKER] Structural blocker: {blocker_type} — skipping retries")
                    result['error'] = f'{error_msg} [BLOCKED: {blocker_type}]'
                else:
                    # Phase 3: Use MAR Reflexion to analyze failure (only for retryable errors)
                    if LLM_REASONER_AVAILABLE:
                        failed_details = "; ".join([
                            f"{s.get('type', 'unknown')}: {s.get('error', 'unknown error')}"
                            for s in failed
                        ])
                        reflection = self.reflect_on_failure(task, error_msg, failed_details)
>>>>>>> REPLACE
```

NOTE: The indentation of the existing retry logic after `reflection = ...` must remain unchanged. The SEARCH block above only replaces the entry to the reflection — everything after (reflection result handling, retry loop, recursive decomposition) stays inside the new `else` block. You will need to indent lines 1051-1098 (the reflection result handling through recursive decomposition) by 4 additional spaces so they fall inside the `else: # Phase 3` block.

IMPORTANT: This is a large indentation change. To be safe, also add a closing for the else block. Find the line that starts `# Phase 13: Recursive Task Decomposition` and ensure it is inside the `else` block.

## What NOT To Change

- Do NOT change MAX_RETRIES value
- Do NOT change the reflection or retry logic itself — only gate entry to it
- Do NOT add new imports
- Do NOT add logging beyond the single `[BLOCKER]` print
- Do NOT create a new table or DB field — blocker_type lives in the task result dict only

## Verification

1. Import check: `python3 -c "from jr_executor.task_executor import TaskExecutor; print('OK')"`
2. Verify method exists: `python3 -c "from jr_executor.task_executor import TaskExecutor; t = TaskExecutor.__new__(TaskExecutor); print(t._classify_blocker([{'error': 'authentication failed'}]))"`
   Expected output: `MISSING_CREDENTIALS`
3. Verify retryable: `python3 -c "from jr_executor.task_executor import TaskExecutor; t = TaskExecutor.__new__(TaskExecutor); print(t._classify_blocker([{'error': 'syntax error in line 42'}]))"`
   Expected output: `RETRYABLE`

## Notes for Jr

- The blocker patterns are intentionally broad — false positives (classifying a retryable error as structural) are better than false negatives (wasting retries on a stale password). We can tune later.
- `permission denied` appears in BOTH MISSING_CREDENTIALS and PERMISSION_DENIED. That's fine — dict iteration order gives MISSING_CREDENTIALS first, which is the safer classification.
- The `else` block indentation change is the hardest part. If it fails, fall back to just adding the `_classify_blocker` method and the `blocker_type` classification + print, WITHOUT gating the retry loop. The method can exist unused and we'll wire it later.
- SERVICE_UNAVAILABLE is classified as structural because if the service is down, retrying in 2 seconds won't help. The service monitor will handle restarts.
