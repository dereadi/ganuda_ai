# Jr Instruction: Create Recursive Task Decomposer Module

**Priority**: P0 — Core executor enhancement
**Council Vote**: 2adc1366 — PROCEED WITH CAUTION (0.823)
**Kanban**: #1768
**Assigned Jr**: Software Engineer Jr.

## Context

When the Jr executor processes multi-step instructions, some steps may fail or be skipped (e.g., SEARCH text mismatch, path issues). Currently, these partial failures are routed to the DLQ as a single failed task. This module adds recursive decomposition: after execution, unexecuted steps are extracted and re-queued as individual sub-tasks.

## Step 1: Create the recursive decomposer module

Create `/ganuda/jr_executor/recursive_decomposer.py`

```python
#!/usr/bin/env python3
"""
Recursive Task Decomposer for Cherokee Jr Executor

When a multi-step instruction fails to execute all steps, this module:
1. Parses the instruction for ### Step N: headers
2. Compares against executed step results
3. Creates sub-tasks for unexecuted steps
4. Queues them to jr_work_queue with parent_task_id linkage

Council Vote: 2adc1366 — PROCEED WITH CAUTION (0.823)
Constitutional Guardrails:
  - MAX_RECURSION_DEPTH = 3 (Turtle 7GEN CONCERN)
  - Full parent_task_id chain for transparency (Raven STRATEGY CONCERN)
  - Same assigned_jr, same path validation (Crawdad implicit security)

For Seven Generations - Cherokee AI Federation
"""

import re
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any

MAX_RECURSION_DEPTH = 3


def parse_step_headers(instructions: str) -> List[Dict]:
    """Parse ### Step N: headers from instruction markdown.

    Returns list of dicts with step_number, title, start_pos, end_pos, content.
    """
    pattern = r'###\s+Step\s+(\d+)[:\s]+(.*?)(?=\n)'
    matches = list(re.finditer(pattern, instructions))

    if not matches:
        return []

    steps = []
    for i, match in enumerate(matches):
        step_num = int(match.group(1))
        step_title = match.group(2).strip()
        start_pos = match.start()

        # End position is start of next step header, or end of document
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(instructions)

        content = instructions[start_pos:end_pos].strip()

        steps.append({
            'step_number': step_num,
            'title': step_title,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'content': content
        })

    return steps


def identify_unexecuted_steps(parsed_steps: List[Dict],
                               step_results: List[Dict]) -> List[Dict]:
    """Compare parsed steps against execution results to find unexecuted ones.

    A step is "unexecuted" if:
    - No corresponding result exists (step was never attempted)
    - The result has success=False and no checkpoint_hit

    Steps that succeeded or were skipped via checkpoint are excluded.
    """
    unexecuted = []

    for i, step in enumerate(parsed_steps):
        if i < len(step_results):
            result = step_results[i]
            # Skip steps that succeeded or were checkpoint-skipped
            if result.get('success') or result.get('checkpoint_hit'):
                continue
            # Step was attempted but failed — include for re-queue
            unexecuted.append(step)
        else:
            # Step was never attempted at all
            unexecuted.append(step)

    return unexecuted


def create_sub_instruction(step: Dict, parent_task_id: int,
                           parent_title: str) -> str:
    """Create a standalone instruction file for a single unexecuted step.

    The instruction preserves the original step content exactly,
    wrapped with metadata headers for traceability.
    """
    instruction = (
        f"# [RECURSIVE] {parent_title} - Step {step['step_number']}\n\n"
        f"**Parent Task**: #{parent_task_id}\n"
        f"**Auto-decomposed**: {datetime.now().isoformat()}\n"
        f"**Original Step Title**: {step['title']}\n\n"
        f"---\n\n"
        f"{step['content']}\n"
    )
    return instruction


def decompose_unexecuted_steps(task: Dict, instructions: str,
                                step_results: List[Dict]) -> List[Dict]:
    """Main decomposition entry point.

    Args:
        task: Original task dict from jr_work_queue
        instructions: Full instruction markdown text
        step_results: List of step execution results

    Returns:
        List of sub-task dicts that were queued, or empty list
    """
    import sys
    sys.path.insert(0, '/ganuda')

    # Check recursion depth
    parameters = task.get('parameters') or {}
    if isinstance(parameters, str):
        try:
            parameters = json.loads(parameters)
        except (json.JSONDecodeError, TypeError):
            parameters = {}

    depth = parameters.get('recursion_depth', 0)

    if depth >= MAX_RECURSION_DEPTH:
        print(f"[RECURSIVE] Max depth {MAX_RECURSION_DEPTH} reached for "
              f"task {task.get('id')} — routing to DLQ")
        return []  # Caller should route to DLQ

    # Parse step headers
    parsed_steps = parse_step_headers(instructions)
    if not parsed_steps:
        print("[RECURSIVE] No ### Step headers found — cannot decompose")
        return []

    # Find unexecuted steps
    unexecuted = identify_unexecuted_steps(parsed_steps, step_results)
    if not unexecuted:
        print(f"[RECURSIVE] All {len(parsed_steps)} steps executed — "
              "no decomposition needed")
        return []

    print(f"[RECURSIVE] {len(unexecuted)}/{len(parsed_steps)} steps "
          "unexecuted — decomposing")

    # Create and queue sub-tasks
    parent_id = task.get('id')
    parent_title = task.get('title', 'unknown')
    assigned_jr = task.get('assigned_jr', 'Software Engineer Jr.')
    sacred_fire = task.get('sacred_fire_priority', False)

    sub_tasks = []

    from lib.secrets_loader import get_db_config
    import psycopg2

    conn = psycopg2.connect(**get_db_config())

    try:
        cur = conn.cursor()

        for step in unexecuted:
            # Create instruction file
            sub_instruction = create_sub_instruction(
                step, parent_id, parent_title
            )

            # Write instruction file
            date_str = datetime.now().strftime('%b%d').upper()
            filename = (f"JR-RECURSIVE-{parent_id}-STEP"
                        f"{step['step_number']}-{date_str}-2026.md")
            filepath = f"/ganuda/docs/jr_instructions/{filename}"

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(sub_instruction)

            print(f"[RECURSIVE] Wrote sub-instruction: {filepath}")

            # Generate task_id hash
            task_id_hash = hashlib.md5(
                f"recursive-{parent_id}-step{step['step_number']}-"
                f"{datetime.now().isoformat()}".encode()
            ).hexdigest()

            # Build parameters with incremented recursion depth
            sub_params = json.dumps({
                'recursion_depth': depth + 1,
                'parent_step_number': step['step_number'],
                'original_task_id': parent_id
            })

            # Queue to jr_work_queue
            title = (f"[RECURSIVE] {parent_title} - Step "
                     f"{step['step_number']}: {step['title'][:60]}")

            cur.execute("""
                INSERT INTO jr_work_queue
                    (task_id, title, instruction_file, assigned_jr,
                     sacred_fire_priority, parent_task_id, parameters,
                     source, created_by, use_rlm, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s,
                        'recursive', 'executor', false, 'pending')
                RETURNING id
            """, (
                task_id_hash, title, filepath, assigned_jr,
                sacred_fire, parent_id, sub_params
            ))

            sub_id = cur.fetchone()[0]
            sub_tasks.append({
                'id': sub_id,
                'step_number': step['step_number'],
                'title': title,
                'filepath': filepath,
                'recursion_depth': depth + 1
            })

            print(f"[RECURSIVE] Queued sub-task #{sub_id}: {title}")

        # Log thermal memory breadcrumb
        try:
            cur.execute("""
                INSERT INTO thermal_memory_archive
                    (original_content, temperature_score,
                     sacred_pattern, metadata)
                VALUES (%s, %s, false, %s)
            """, (
                f"Recursive decomposition: Task #{parent_id} "
                f"'{parent_title}' decomposed into "
                f"{len(sub_tasks)} sub-tasks at depth {depth + 1}. "
                f"Steps: {[s['step_number'] for s in sub_tasks]}",
                50,
                json.dumps({
                    'type': 'recursive_decomposition',
                    'parent_task_id': parent_id,
                    'sub_task_ids': [s['id'] for s in sub_tasks],
                    'recursion_depth': depth + 1,
                    'timestamp': datetime.now().isoformat()
                })
            ))
        except Exception as tm_err:
            print(f"[RECURSIVE] Thermal memory log failed "
                  f"(non-fatal): {tm_err}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"[RECURSIVE] Decomposition failed: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

    print(f"[RECURSIVE] Decomposed {len(sub_tasks)} sub-tasks "
          f"from task #{parent_id}")
    return sub_tasks
```

## Verification

After creation, confirm:
1. File exists at `/ganuda/jr_executor/recursive_decomposer.py`
2. File contains `MAX_RECURSION_DEPTH = 3`
3. File contains `def decompose_unexecuted_steps`
4. File contains `def parse_step_headers`
5. File imports from `lib.secrets_loader`

## For Seven Generations
