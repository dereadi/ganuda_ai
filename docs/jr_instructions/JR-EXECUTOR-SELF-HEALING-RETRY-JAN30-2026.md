# JR-EXECUTOR-SELF-HEALING-RETRY-JAN30-2026
## Phase 11: Add Self-Healing Retry Loop to Task Executor

**Priority:** P1 — Failed tasks stay failed despite reflection insights
**Target Node:** redfin
**Estimated Scope:** ~60 lines added to existing file
**Reference Repos:** becklabs/reflexion-framework, noahshinn/reflexion (NeurIPS 2023), LangGraph ResponderWithRetries
**Companion Document:** `ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FUTURE-JAN30-2026.md`

---

### Background

The task executor already has MAR Reflexion (Phase 3). When a task fails, `reflect_on_failure()` calls the LLM to analyze what went wrong and returns:

```python
{
    "success": False,
    "analysis": "The SQL INSERT failed because...",
    "improvements": ["Use ON CONFLICT", "Check column types"],
    "retry_suggested": True,
    "modified_approach": "Change the INSERT to use... "
}
```

But **nobody acts on this reflection**. The executor logs the improvements and returns failure. The reflection produces actionable insights that are discarded.

### The Pattern: Reflexion Agent Loop

From becklabs/reflexion-framework:
```python
for trial in range(max_retries):
    reward, message = agent.step()
    if reward == 1.0:
        break  # Success
    # Reflection is automatically appended to episodic memory
    # Next step() call uses reflection context
```

The key insight: each retry includes the **full reflection context** from the previous attempt. The LLM doesn't just retry — it retries with knowledge of what went wrong.

### Task: Add Retry Loop to process_queue_task()

**File to Modify:** `/ganuda/jr_executor/task_executor.py`

#### Step 1: Add Retry Constants

Add near the top of the `TaskExecutor` class:

```python
    # Phase 11: Self-Healing Retry Configuration
    MAX_RETRIES = 2  # Maximum retry attempts after initial failure
    RETRY_STRATEGIES = ['NONE', 'LAST_ATTEMPT', 'FULL_REFLECTION']
```

#### Step 2: Add Retry Method

Add to the `TaskExecutor` class:

```python
def _retry_with_reflection(self, task: dict, instructions: str,
                            failed_result: dict, reflection: dict,
                            attempt: int) -> dict:
    """
    Phase 11: Self-Healing Retry — retry failed task using reflection insights.

    Uses the Reflexion pattern (NeurIPS 2023):
    append reflection to context, re-extract steps, re-execute.

    Reference: becklabs/reflexion-framework agent.step() loop
    """
    print(f"[RETRY] Attempt {attempt}/{self.MAX_RETRIES} for: {task.get('title')}")

    # Build augmented instructions with reflection context
    failed_steps = failed_result.get('steps_executed', [])
    failed_details = []
    for s in failed_steps:
        if not s.get('success'):
            failed_details.append(f"- Step type '{s.get('type')}' failed: {s.get('error', 'unknown')}")

    reflection_context = f"""

## RETRY CONTEXT (Attempt {attempt})

### Previous Attempt Failed
{chr(10).join(failed_details)}

### Reflection Analysis
{reflection.get('analysis', 'No analysis available')}

### Suggested Improvements
{chr(10).join('- ' + imp for imp in reflection.get('improvements', []))}

### Modified Approach
{reflection.get('modified_approach', 'No modified approach suggested')}

## IMPORTANT: Apply the improvements above when generating code for this retry.
"""

    augmented_instructions = instructions + reflection_context

    # Re-extract steps with augmented context
    steps = self._extract_steps_from_instructions(augmented_instructions)

    if not steps:
        return {
            'success': False,
            'error': f'Retry {attempt}: No executable steps extracted from augmented instructions',
            'execution_mode': 'retry',
            'retry_attempt': attempt
        }

    # Execute the retry
    try:
        step_results = self.execute_steps(steps)

        if not step_results:
            return {
                'success': False,
                'error': f'Retry {attempt}: No steps executed',
                'execution_mode': 'retry',
                'retry_attempt': attempt
            }

        all_success = all(s.get('success') for s in step_results)

        result = {
            'success': all_success,
            'steps_executed': step_results,
            'execution_mode': 'retry',
            'retry_attempt': attempt,
            'error': None if all_success else f'Retry {attempt}: {sum(1 for s in step_results if not s.get("success"))} step(s) failed'
        }

        if all_success:
            print(f"[RETRY] SUCCESS on attempt {attempt}!")

        return result

    except Exception as e:
        return {
            'success': False,
            'error': f'Retry {attempt} execution error: {e}',
            'execution_mode': 'retry',
            'retry_attempt': attempt
        }
```

#### Step 3: Wire Into process_queue_task()

In the existing failure handling block (around line 776-800), after the reflection is generated, add the retry loop:

```python
            if not all_success:
                failed = [s for s in step_results if not s.get('success')]
                error_msg = f'{len(failed)} step(s) failed'
                result['error'] = error_msg

                # Phase 3: Use MAR Reflexion to analyze failure
                if LLM_REASONER_AVAILABLE:
                    failed_details = "; ".join([...])  # existing code
                    reflection = self.reflect_on_failure(task, error_msg, failed_details)
                    result['reflection'] = reflection

                    # Phase 11: Self-Healing Retry Loop
                    if reflection.get('retry_suggested') and LLM_REASONER_AVAILABLE:
                        for attempt in range(1, self.MAX_RETRIES + 1):
                            retry_result = self._retry_with_reflection(
                                task, instructions, result, reflection, attempt
                            )

                            if retry_result.get('success'):
                                # Retry succeeded — update result
                                result['success'] = True
                                result['steps_executed'] = retry_result['steps_executed']
                                result['error'] = None
                                result['retry_attempts'] = attempt
                                result['execution_mode'] = 'retry_success'
                                print(f"[RETRY] Task recovered after {attempt} retry(s)")
                                break
                            else:
                                # Retry failed — reflect again for next attempt
                                if attempt < self.MAX_RETRIES:
                                    reflection = self.reflect_on_failure(
                                        task, retry_result.get('error', ''),
                                        str(retry_result.get('steps_executed', []))
                                    )
                                    result['reflection'] = reflection
                        else:
                            result['retry_attempts'] = self.MAX_RETRIES
                            result['execution_mode'] = 'retry_exhausted'
                            print(f"[RETRY] All {self.MAX_RETRIES} retries exhausted")
```

### Safety Constraints

1. **Max 2 retries** — prevents infinite retry loops
2. **Only retries when reflection says `retry_suggested: true`** — the LLM decides if retry is worthwhile
3. **Each retry gets fresh reflection** — if retry 1 fails, re-reflect before retry 2
4. **Same security checks apply** — retried steps still go through forbidden pattern checks, path validation, etc.
5. **Retry outcome recorded** — Learning Store gets the full retry history

### Testing

```bash
# Queue a task known to fail (e.g., wrong column name)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (title, description, tags, instruction_content, status, assigned_jr, priority)
VALUES (
    'Test Self-Healing Retry',
    'Test that retry loop works when initial attempt fails',
    ARRAY['test', 'retry', 'phase-11'],
    E'## Test Task\n\nInsert a test row:\n\n\`\`\`sql\nINSERT INTO educational_content (title, slug, content_type, content, summary, is_published) VALUES (''Test Article'', ''test-retry'', ''article'', ''Test content'', ''Test summary'', true);\n\`\`\`',
    'pending',
    'Software Engineer Jr.',
    3
);
"

# Monitor for retry log lines
tail -f /ganuda/logs/jr_queue_worker.log | grep RETRY
```

### Files to Modify

| File | Change | Lines Added |
|------|--------|-------------|
| `/ganuda/jr_executor/task_executor.py` | Add `MAX_RETRIES`, `_retry_with_reflection()`, wire into `process_queue_task()` | ~60 |

---

*For Seven Generations*
