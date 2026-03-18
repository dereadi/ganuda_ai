# Jr Instruction: PreFlect — Build Pre-Execution Self-Critique into Jr Executor

**Ticket**: PREFLECT-EPIC
**Council Vote**: Turtle slate vote, 5-2
**Estimated SP**: 5
**Assigned**: Peace Chief
**Depends On**: None (vLLM on localhost:8000 already running, task_executor.py already has LLM_REASONER_AVAILABLE)
**Specification**: `/ganuda/docs/jr_instructions/JR-PREFLECT-JR-EXECUTOR-MAR15-2026.md` (design spec)

---

## Objective

Add a pre-execution self-critique step to the Jr task executor. Before running steps, the Jr asks local vLLM: "Does this plan make sense? What could go wrong?" This catches bad decomposition, missing dependencies, impossible file paths, and security risks BEFORE they consume tokens and leave execution debris.

Based on DLQ analysis: ~10-15% of Jr task failures are preventable with a 30-second self-critique step.

## Current Execution Flow

```
Instructions → _extract_steps_from_instructions() → [HERE] → _preflight_hash_check() → execute_steps()
```

PreFlect inserts between step extraction and pre-flight hash check (task_executor.py, between lines 1040 and 1047).

## Implementation

### Step 1: Add PreFlect Method to TaskExecutor

In `/ganuda/jr_executor/task_executor.py`, add this method to the `TaskExecutor` class:

```python
def _preflect_critique(self, steps: list, task_context: str) -> dict:
    """
    Pre-execution self-critique via local vLLM.
    Returns: {action: PASS|MODIFY|FLAG, critique: str, revised_steps: list|None}
    """
    import time

    if not LLM_REASONER_AVAILABLE:
        logger.debug("[PREFLECT] LLM reasoner not available — skipping")
        return {"action": "PASS", "critique": "reasoner_unavailable", "revised_steps": None}

    # Build readable plan from steps
    plan_lines = []
    for i, step in enumerate(steps, 1):
        step_type = step.get('type', 'unknown')
        step_desc = step.get('description', step.get('content', str(step)))[:200]
        plan_lines.append(f"Step {i} ({step_type}): {step_desc}")
    plan_text = "\n".join(plan_lines)

    prompt = f"""You are a pre-execution reviewer for an automated task executor.
Review this execution plan and identify problems BEFORE execution.

TASK CONTEXT:
{task_context[:2000]}

EXECUTION PLAN:
{plan_text}

Check for:
1. Missing dependencies between steps (step 3 needs output from step 2?)
2. File paths that look wrong or don't exist
3. Security risks (chmod 777, hardcoded credentials, destructive commands)
4. Steps that will fail because of missing context
5. Steps in wrong order

Respond with EXACTLY one of:
ACTION: PASS
(if the plan looks reasonable)

ACTION: FLAG
CRITIQUE: <one sentence explaining the concern>
(if there's a concern but execution can proceed with caution)

ACTION: MODIFY
CRITIQUE: <one sentence explaining what's wrong>
REVISED_STEP_ORDER: <comma-separated step numbers in better order>
(if steps need reordering — do NOT rewrite steps, just reorder)
"""

    try:
        start = time.time()
        response = self.llm_reasoner.reason(
            prompt,
            max_tokens=300,
            temperature=0.1
        )
        latency_ms = int((time.time() - start) * 1000)

        response_text = response.strip() if response else ""

        # Parse action
        action = "PASS"
        critique = ""
        revised_steps = None

        if "ACTION: FLAG" in response_text:
            action = "FLAG"
            critique_match = re.search(r'CRITIQUE:\s*(.+)', response_text)
            critique = critique_match.group(1).strip() if critique_match else "unspecified concern"

        elif "ACTION: MODIFY" in response_text:
            action = "MODIFY"
            critique_match = re.search(r'CRITIQUE:\s*(.+)', response_text)
            critique = critique_match.group(1).strip() if critique_match else "reorder needed"
            order_match = re.search(r'REVISED_STEP_ORDER:\s*([\d,\s]+)', response_text)
            if order_match:
                try:
                    new_order = [int(x.strip()) - 1 for x in order_match.group(1).split(',')]
                    revised_steps = [steps[i] for i in new_order if i < len(steps)]
                except (ValueError, IndexError):
                    revised_steps = None
                    action = "FLAG"  # Downgrade to FLAG if reorder parsing fails
                    critique += " (reorder parse failed, proceeding with original order)"

        logger.info(f"[PREFLECT] {action} in {latency_ms}ms — {critique or 'plan looks good'}")

        # Log to task metadata
        self._log_preflect(action, critique, latency_ms)

        return {"action": action, "critique": critique, "revised_steps": revised_steps}

    except Exception as e:
        logger.warning(f"[PREFLECT] Failed: {e} — skipping (non-blocking)")
        return {"action": "PASS", "critique": f"preflect_error: {e}", "revised_steps": None}


def _log_preflect(self, action: str, critique: str, latency_ms: int):
    """Log PreFlect result to task metadata for metrics tracking."""
    try:
        if hasattr(self, '_current_task_id') and self._current_task_id:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE jr_work_queue
                SET parameters = COALESCE(parameters, '{}'::jsonb) || %s::jsonb
                WHERE task_id = %s
            """, (
                json.dumps({
                    "preflect_action": action,
                    "preflect_critique": critique[:500],
                    "preflect_latency_ms": latency_ms
                }),
                self._current_task_id
            ))
            conn.commit()
    except Exception as e:
        logger.debug(f"[PREFLECT] Metadata log failed: {e}")
```

### Step 2: Insert PreFlect Call into Execution Flow

In `/ganuda/jr_executor/task_executor.py`, in the `process_queue_task()` method, insert between step extraction (line ~1040) and pre-flight hash check (line ~1047):

```python
# After: steps = self._extract_steps_from_instructions(instructions)
# After: the "if not steps" check
# Before: preflight_results = self._preflight_hash_check(steps)

# PreFlect: Pre-execution self-critique
if os.environ.get('PREFLECT_ENABLED', 'true').lower() == 'true' and len(steps) >= 3:
    preflect = self._preflect_critique(
        steps=steps,
        task_context=f"Title: {task.get('title', 'unknown')}\nDescription: {task.get('description', '')[:500]}"
    )
    if preflect['action'] == 'MODIFY' and preflect['revised_steps']:
        logger.info(f"[PREFLECT] Reordering {len(steps)} steps per self-critique")
        steps = preflect['revised_steps']
    elif preflect['action'] == 'FLAG':
        logger.warning(f"[PREFLECT] Flagged: {preflect['critique']}")
        # Continue execution but flag is recorded in metadata
```

### Step 3: Add Feature Flag

No config file change needed. Uses environment variable `PREFLECT_ENABLED` (default: true).

To disable: add `Environment=PREFLECT_ENABLED=false` to the Jr executor's systemd unit file, or set in shell.

## Verification

1. **PASS test**: Submit a well-formed Jr task with ≥3 steps. Verify PreFlect returns PASS and task executes normally
2. **FLAG test**: Submit a task with a suspicious step (e.g., `chmod 777`). Verify PreFlect returns FLAG and metadata records it
3. **MODIFY test**: Submit a task with steps in wrong dependency order. Verify PreFlect reorders
4. **Skip test**: Submit a task with <3 steps. Verify PreFlect is skipped entirely
5. **Kill switch test**: Set `PREFLECT_ENABLED=false`. Verify no vLLM calls from PreFlect
6. **Failure resilience**: Block localhost:8000. Verify PreFlect fails gracefully and task proceeds
7. **Latency check**: PreFlect should complete in <2 seconds (300 tokens on local vLLM)

```sql
-- After a week, check PreFlect metrics
SELECT
    (parameters->>'preflect_action') as action,
    COUNT(*) as count,
    AVG((parameters->>'preflect_latency_ms')::int) as avg_latency_ms
FROM jr_work_queue
WHERE parameters ? 'preflect_action'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY parameters->>'preflect_action';
```

## Council Concerns as Features

- **Crawdad**: Local vLLM only — no query leaves the node
- **Turtle**: Feature flag + PASS-through on failure — fully reversible
- **Coyote**: Track modify rate — if >50% of tasks get modified, the critique is too aggressive
- **Peace Chief**: 20% token overhead cap — 300 max tokens for critique
- **Gecko**: No new services — runs inside existing Jr executor process

## What NOT To Do

- Do NOT send task content to external APIs — local vLLM only (Crawdad)
- Do NOT block task execution on PreFlect failure — always fail open
- Do NOT rewrite steps, only reorder — step content comes from the Jr instruction, not the critic
- Do NOT run PreFlect on tasks with <3 steps — overhead not worth it
- Do NOT add PreFlect to the research task path — research tasks have their own flow
