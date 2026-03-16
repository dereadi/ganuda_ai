# Jr Instruction: PreFlect — Pre-Execution Self-Critique for Jr Tasks

**Epic**: PREFLECT-EPIC (Cognitive Gaps Mar 15 2026)
**Council Vote**: Approved as Priority #1 in cognitive gap analysis
**Estimated SP**: 5
**Target File**: `/ganuda/jr_executor/jr_task_executor.py`

---

## Objective

Add a pre-execution self-critique step to the Jr task executor. Before executing a plan, the Jr asks itself: "What could go wrong with this plan? What am I assuming? What did I miss?" This catches errors BEFORE they consume tokens and leave debris.

## Research Basis

PreFlect pattern from recent AI research shows 10-15% accuracy improvement with 15-20% token overhead. The key insight: LLMs are better at critiquing plans than generating perfect ones on the first try.

## Design — Council Concerns as Features

### Crawdad (Security)
- PreFlect prompt MUST run on local vLLM only (localhost:8000). No external model sees task context.
- PreFlect output is NOT stored in thermal memory (ephemeral working memory only).

### Turtle (Reversibility)
- Feature flag: `PREFLECT_ENABLED` environment variable, default `true`.
- 2-week measurement window after deployment. If accuracy drops or token cost exceeds 20%, disable.
- Log comparison metrics: tasks WITH PreFlect vs. historical tasks WITHOUT.

### Coyote (False Positives)
- Track PreFlect interventions: how often does it modify the plan? How often does it block execution?
- If PreFlect modifies >50% of plans, the critique prompt is too aggressive — tune it down.
- Log `preflect_action`: `passed` (no changes), `modified` (plan adjusted), `flagged` (sent for review).

### Eagle Eye (Drift Detection)
- Log each PreFlect result with task_id, action taken, and critique text to jr_work_queue metadata.
- Weekly drift check: is PreFlect's modification rate stable or trending up/down?

### Peace Chief (Token Budget)
- Hard cap: PreFlect step uses max 300 tokens for critique, 200 tokens for revised plan.
- Total overhead must not exceed 20% of task's token budget.
- If task has <3 steps, skip PreFlect (not worth the overhead for trivial tasks).

### Gecko (No New Services)
- PreFlect runs INSIDE the existing Jr executor process. Same vLLM call pattern.
- No new service, no new port, no new systemd unit.

## Implementation

### Step 1: Add PreFlect prompt

In `jr_task_executor.py`, add a method `_preflect_critique(self, plan: str, task_context: str) -> dict`:

```python
PREFLECT_PROMPT = """You are a plan reviewer. Examine this execution plan and identify:
1. Assumptions that might be wrong
2. Steps that could fail and how
3. Missing error handling or edge cases
4. Whether the plan actually solves the stated problem

PLAN:
{plan}

TASK CONTEXT:
{task_context}

Respond with:
ACTION: [PASS|MODIFY|FLAG]
CRITIQUE: [Your analysis in 2-3 sentences]
REVISED_PLAN: [Only if ACTION is MODIFY — the improved plan. Otherwise "N/A"]
"""
```

### Step 2: Insert PreFlect into execution flow

In the main execution method, AFTER plan generation but BEFORE step execution:

```python
if os.environ.get('PREFLECT_ENABLED', 'true').lower() == 'true':
    if len(steps) >= 3:  # Skip for trivial tasks
        preflect_result = self._preflect_critique(plan_text, task_description)
        # Log the result
        self._log_preflect(task_id, preflect_result)
        if preflect_result['action'] == 'MODIFY':
            # Re-parse the revised plan into steps
            steps = self._parse_steps(preflect_result['revised_plan'])
        elif preflect_result['action'] == 'FLAG':
            # Log warning, continue with original plan but mark task as flagged
            logger.warning(f"[PREFLECT] Task {task_id} flagged: {preflect_result['critique']}")
```

### Step 3: Add logging

Add `preflect_action` and `preflect_critique` to the task's metadata/result storage. This feeds Eagle Eye's drift detection.

### Step 4: Add metrics

Track in thermal memory (temperature 40, ephemeral):
- `preflect_pass_rate`: % of tasks that pass without modification
- `preflect_modify_rate`: % of tasks where plan was improved
- `preflect_flag_rate`: % of tasks flagged for review
- `preflect_token_overhead`: average additional tokens per task

## Acceptance Criteria

1. PreFlect runs on all Jr tasks with ≥3 steps
2. Feature flag works — `PREFLECT_ENABLED=false` skips the step entirely
3. Token overhead is ≤20% per task
4. PreFlect critique runs on local vLLM only
5. Results are logged to task metadata
6. No new systemd service or port

## What NOT To Do

- Do NOT send task context to any external model
- Do NOT store PreFlect critiques in thermal memory at high temperature
- Do NOT block task execution on FLAG — just log and continue
- Do NOT add PreFlect to tasks with <3 steps
