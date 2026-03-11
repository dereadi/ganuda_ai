# JR INSTRUCTION: Executor Upgrade — Task-Type Routing + Artifact Verification

**Task**: Add semantic task-type routing and deliverable verification to the Jr executor
**Priority**: P1 — executor integrity
**Date**: 2026-03-11
**TPM**: Claude Opus
**Council Vote**: #1c14b3cf65e95fcd (executor quality), notification #healthy-diversity
**Story Points**: 8
**References**: aurelio-labs/semantic-router, lm-sys/RouteLLM, ulab-uiuc/LLMRouter

## Problem Statement

Two problems, one fix:

1. **Wrong Jr, wrong work**: Builder Jrs (SE Jr, Infra Jr) get assigned investigative tasks (audits, post-mortems). They execute steps mechanically but don't produce the expected analytical output. The executor doesn't know the difference between "write a script" and "investigate a security concern."

2. **Pipeline of lies**: The executor marks tasks "completed" after running steps, even when deliverables (report files, code fixes, test implementations) don't exist. 3 of 5 tasks queued Mar 10 were marked complete without actual output.

## What You're Building

### Feature 1: Task-Type Routing (DC-6 Gradient Principle)

Classify incoming tasks by archetype and route to the Jr that RESTS in that type of work.

**Three archetypes:**

| Archetype | Description | Route To |
|-----------|-------------|----------|
| BUILD | Write code, create files, deploy services, fix bugs | Software Engineer Jr., Infrastructure Jr. |
| THINK | Audit, investigate, research, analyze, assess risk | Research Jr., Synthesis Jr. |
| DOCUMENT | Write reports, post-mortems, documentation, summaries | Document Jr., Synthesis Jr. |

**How routing works:**

1. When a task enters the queue, embed its title + description using the greenfin embedding service
2. Compare against pre-defined route exemplars (see below)
3. Assign to the highest-scoring archetype
4. Map archetype to available Jr(s)
5. If the task already has an `assigned_jr` that matches the archetype, keep it. Only re-route if there's a mismatch.

**Route exemplars** (store these in a config dict, not hardcoded in logic):

```python
ROUTE_EXEMPLARS = {
    "BUILD": [
        "write a python script that",
        "create a systemd service",
        "deploy to production",
        "fix the bug in",
        "add a function to",
        "implement the feature",
        "create a timer that runs",
        "wire up the integration",
        "modify the code to",
        "build the API endpoint",
    ],
    "THINK": [
        "audit the security of",
        "investigate why",
        "research alternatives for",
        "analyze the failure",
        "assess the risk of",
        "evaluate the options",
        "review the architecture",
        "what are the implications of",
        "examine the logs for",
        "determine the root cause",
    ],
    "DOCUMENT": [
        "write a post-mortem",
        "document what happened",
        "create a report on",
        "summarize the findings",
        "write the design document",
        "produce a compliance matrix",
        "draft the specification",
        "write up the analysis",
        "create documentation for",
        "publish the results",
    ],
}
```

**Embedding call** to greenfin:

```python
import requests

def get_embedding(text):
    """Get embedding from greenfin embedding service."""
    try:
        resp = requests.post(
            "http://192.168.132.224:8003/embed",
            json={"text": text},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as e:
        logging.warning(f"Embedding failed, using fallback: {e}")
        return None
```

Check the actual greenfin embedding API format first — it may be different. Read `/ganuda/services/` for existing embedding client code.

**Fallback** (Coyote binding condition): If greenfin is down or embedding fails, fall back to keyword matching:
```python
KEYWORD_FALLBACK = {
    "BUILD": ["script", "service", "deploy", "fix", "create", "implement", "wire", "build"],
    "THINK": ["audit", "investigate", "research", "analyze", "assess", "evaluate", "review", "examine"],
    "DOCUMENT": ["post-mortem", "document", "report", "summarize", "specification", "write up"],
}
```

**Crawdad binding condition**: Before embedding, strip any content that looks like credentials (regex for passwords, API keys, connection strings). Do NOT send raw secrets to the embedding service.

### Feature 2: Artifact Verification

Before marking a task "completed", verify that expected deliverables exist.

**How it works:**

1. Parse the Jr instruction file for expected output files. Look for patterns like:
   - "Output to: `/ganuda/docs/...`"
   - "Write findings to: `/ganuda/docs/...`"
   - "Create `/ganuda/scripts/...`"
   - "Write a test case... `/ganuda/tests/...`"

2. Extract a list of expected file paths from the instruction.

3. After all steps execute, check each expected file:
   - Does the file exist?
   - Is it non-empty (> 0 bytes)?
   - Was it modified after the task started? (creation time > task start time)

4. If ANY expected deliverable is missing:
   - Set status to `failed` (not `completed`)
   - Set error_message to: `"Deliverables not found: /path/to/expected/file"`
   - Set progress_percent to the percentage of deliverables that DID land

5. If ALL deliverables exist:
   - Set status to `completed` as normal

**Parsing expected deliverables from instruction files:**

```python
import re

def extract_expected_deliverables(instruction_content):
    """Parse instruction markdown for expected output file paths."""
    patterns = [
        r'(?:Output to|Write (?:findings|report) to|Create|Deploy to)[:\s]+[`"]?(/ganuda/[^\s`"]+)',
        r'(?:Write a test case|Create test)[^`]*`(/ganuda/[^\s`]+)`',
        r'Target Files.*?CREATE\).*?`(/ganuda/[^\s`]+)`',
    ]
    deliverables = set()
    for pattern in patterns:
        matches = re.findall(pattern, instruction_content, re.IGNORECASE | re.DOTALL)
        deliverables.update(matches)
    return list(deliverables)
```

This regex approach will miss some cases. That's OK — it's better than checking nothing. Iterate.

**Optional: Add `deliverables` field to jr_work_queue**

If you want to be explicit rather than parsing, add a JSONB column:
```sql
ALTER TABLE jr_work_queue ADD COLUMN IF NOT EXISTS expected_deliverables JSONB DEFAULT '[]'::jsonb;
```

Then task creators can specify:
```python
expected_deliverables=["/ganuda/docs/security/AUDIT-JR-EXECUTOR-PRIVILEGES-MAR2026.md"]
```

Both approaches (parsing + explicit) can coexist. Explicit takes precedence if present.

## Target Files

- `/ganuda/jr_executor/task_executor.py` — main executor (MODIFY: add routing + verification)
- `/ganuda/jr_executor/jr_queue_client.py` — queue client (MODIFY: add deliverables field if using explicit approach)
- `/ganuda/lib/task_router.py` — new routing module (CREATE)
- `/ganuda/tests/test_task_routing.py` — routing tests (CREATE)
- `/ganuda/tests/test_artifact_verification.py` — verification tests (CREATE)

## Steps

### 1. Read existing executor code
Read `task_executor.py` and `jr_queue_client.py` fully. Understand the current flow from task pickup to completion marking.

### 2. Create task_router.py
Implement the routing logic in a separate module. Keep it clean and testable.

### 3. Wire routing into executor
When a task is picked up, if `assigned_jr` doesn't match the detected archetype, log a warning and optionally re-route. Don't break existing explicit assignments — routing is advisory for manually-assigned tasks, mandatory for auto-assigned ones.

### 4. Add artifact verification to completion path
Before the executor writes `status='completed'`, run the deliverable check. This is the critical path — don't let any task skip it.

### 5. Write tests
- `test_task_routing.py`: Test that BUILD/THINK/DOCUMENT exemplars classify correctly. Test fallback when greenfin is down. Test credential stripping.
- `test_artifact_verification.py`: Test that missing files → failed. Test that present files → completed. Test the instruction parser extracts paths correctly.

### 6. Migrate DB (optional)
If adding `expected_deliverables` column, run the ALTER TABLE. This is backward-compatible (default empty array).

## Constraints

- Do NOT break existing task execution — routing is additive, verification is additive
- Do NOT block task execution if greenfin embedding is down — fallback to keywords
- Do NOT send credentials or PII to the embedding service (Crawdad binding condition)
- Do NOT re-route tasks that have been explicitly assigned by the TPM — respect manual overrides
- Keep routing latency < 1 second. If embedding takes longer, use keyword fallback.
- Raven binding condition: verify greenfin embedding endpoint is responsive before wiring in. If latency > 2s, use keyword-only routing until resolved.

## Files to Read Before Starting

- `/ganuda/jr_executor/task_executor.py` — current executor
- `/ganuda/jr_executor/jr_queue_client.py` — current queue client
- `/ganuda/lib/specialist_council.py` — example of embedding usage in the council
- `/ganuda/services/research_worker.py` — may have greenfin embedding client code
- `https://github.com/aurelio-labs/semantic-router` — reference architecture for semantic routing

## Acceptance Criteria

- A "write a script" task routes to Software Engineer Jr.
- An "audit the security" task routes to Research Jr.
- A "write a post-mortem" task routes to Document Jr.
- If greenfin is down, keyword fallback routes correctly
- A task with missing deliverables is marked `failed`, not `completed`
- A task with all deliverables present is marked `completed`
- Existing tasks with explicit `assigned_jr` are not re-routed
- Tests pass: `python3 -m pytest tests/test_task_routing.py tests/test_artifact_verification.py`
- `python3 -c "import py_compile; py_compile.compile('jr_executor/task_executor.py', doraise=True)"` passes
- `python3 -c "import py_compile; py_compile.compile('lib/task_router.py', doraise=True)"` passes

## DO NOT

- Break existing task execution flow
- Send credentials to the embedding service
- Override explicit TPM task assignments
- Add hard dependencies on greenfin — always have a fallback
- Make routing decisions that take > 1 second
