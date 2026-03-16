# Jr Instruction: Code Review Gate via sasass2 Qwen2.5-Coder:32b

**Task**: Add automated code review gate to Jr task executor using sasass2 Ollama
**Priority**: P2
**Story Points**: 3
**Ticket**: Fleet Stretch (83dfa34d)
**Date**: 2026-03-15

## Context

Jr code tasks currently generate code → validate syntax → save. There is no review step. The sasass2 node runs Qwen2.5-Coder:32b via Ollama at 192.168.132.242:11434 — a 32B parameter code-specialized model ideal for reviewing Jr output before it's written to disk.

This gate adds a "second pair of eyes" between syntax validation and file write. If the reviewer rejects the code, the task fails gracefully with the review feedback. If the reviewer is unreachable (sasass2 down), the gate is SKIPPED (not blocking) — soft gate, not hard gate.

## Files to Modify

### `/ganuda/jr_executor/jr_task_executor.py`

#### Step 1: Add `_review_code_with_sasass2()` method (~30 lines)

Add this method to the JrTaskExecutor class, near the other helper methods (after `_validate_code_syntax()`):

```python
def _review_code_with_sasass2(self, code: str, task_content: str, language: str) -> tuple:
    """Send generated code to sasass2 Qwen2.5-Coder:32b for review.

    Returns (approved: bool, feedback: str).
    Soft gate: returns (True, "reviewer_unavailable") if sasass2 is down.
    """
    import requests

    review_prompt = f"""Review this {language} code generated for the following task.

TASK: {task_content[:500]}

CODE:
```{language}
{code[:3000]}
```

Review criteria:
1. Security: No command injection, no hardcoded credentials, no unsafe eval/exec
2. Correctness: Does the code accomplish the task described?
3. Style: Reasonable variable names, no dead code, imports used
4. Safety: No destructive operations (rm -rf, DROP TABLE, etc.) without safeguards

Respond with EXACTLY one of:
APPROVE: <one-line reason>
REJECT: <specific issue that must be fixed>"""

    try:
        resp = requests.post(
            "http://192.168.132.242:11434/api/generate",
            json={
                "model": "qwen2.5-coder:32b",
                "prompt": review_prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200},
            },
            timeout=60,
        )
        if resp.status_code != 200:
            print(f"[{self.agent_id}] CODE_REVIEW: sasass2 returned {resp.status_code}, skipping gate")
            return True, "reviewer_unavailable"

        review = resp.json().get("response", "").strip()
        print(f"[{self.agent_id}] CODE_REVIEW: {review[:200]}")

        if review.upper().startswith("REJECT"):
            return False, review
        return True, review

    except requests.exceptions.ConnectionError:
        print(f"[{self.agent_id}] CODE_REVIEW: sasass2 unreachable, skipping gate")
        return True, "reviewer_unavailable"
    except requests.exceptions.Timeout:
        print(f"[{self.agent_id}] CODE_REVIEW: sasass2 timeout, skipping gate")
        return True, "reviewer_timeout"
    except Exception as e:
        print(f"[{self.agent_id}] CODE_REVIEW: error {e}, skipping gate")
        return True, f"reviewer_error: {e}"
```

#### Step 2: Wire the gate into `_execute_code_task()` (line ~854-862)

After syntax validation passes and BEFORE the file is saved, add the review gate. Find this section:

```python
        # Determine output path
        output_path = self._extract_code_output_path(task_content, language)
```

Insert BEFORE that line:

```python
        # Code review gate — sasass2 Qwen2.5-Coder:32b (soft gate)
        review_approved, review_feedback = self._review_code_with_sasass2(
            clean_code, task_content, language
        )
        if not review_approved:
            print(f"[{self.agent_id}] CODE_REVIEW_REJECTED: {review_feedback[:200]}")
            self._record_fara_mistake(language, clean_code, f"Review rejected: {review_feedback}")
            return False, f"Code review rejected by sasass2: {review_feedback}"

        if review_feedback not in ("reviewer_unavailable", "reviewer_timeout"):
            print(f"[{self.agent_id}] CODE_REVIEW_APPROVED: {review_feedback[:100]}")
```

#### Step 3: Include review metadata in task result

When the code task succeeds (line ~870), include the review status in the result message:

```python
review_status = "reviewed" if "APPROVE" in review_feedback.upper() else review_feedback
return True, f"Code generated and saved to {output_path} [{review_status}]"
```

## Acceptance Criteria

1. Code tasks that pass syntax validation are sent to sasass2 for review
2. If sasass2 REJECTS: task fails, FARA mistake is recorded, feedback returned
3. If sasass2 APPROVES: task continues to file save
4. If sasass2 is DOWN or TIMES OUT: gate is skipped, task continues (soft gate)
5. Review prompt is truncated (code: 3000 chars, task: 500 chars) to fit context window
6. No new imports at module level — `requests` is imported inline

## Do NOT

- Make this a hard gate — sasass2 is a Mac desktop, it will be off sometimes
- Send more than 3000 chars of code to the reviewer (context window limit)
- Add retry logic — one shot, pass or skip
- Touch the existing syntax validation or FARA recording logic
- Change the LLM routing in `_call_llm_routed()`
