# Jr Instruction: Executor File-Edit Pipeline Fix

**Task ID:** EXECUTOR-EDIT-FIX-001
**Priority:** P0
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Depends On:** ULTRATHINK-EXECUTOR-FILE-EDIT-PIPELINE-FEB01-2026

## Background

5 consecutive Jr tasks (#514-518) failed because the executor defaults to full-file write mode for code snippets, triggering the 50% reduction guardrail. The `SearchReplaceEditor` (added Jan 31) handles edits correctly, but the mode detection doesn't route to it.

## Changes

### Fix 1: Broaden Mode Detection

**File:** `/ganuda/jr_executor/task_executor.py`

In `_determine_edit_mode()` (around line 361), add broader patterns BEFORE the existing narrow ones.

<<<<<<< SEARCH
        # Pattern: "Add this method after X" or "Add new method"
        add_match = re.search(r'add\s+(?:this\s+)?(?:new\s+)?(?:method|function|class)',
                              text)
=======
        # Pattern: "Add X to the list/array/scopes" or "Add `something`"
        add_to_match = re.search(r'add\s+[`\'"]?[\w._]+[`\'"]?\s+to\s+', text)
        if add_to_match:
            result['mode'] = 'insert_after'
            result['verb'] = 'add_to'
            return result

        # Pattern: "Find X and replace/change/update"
        find_and_match = re.search(r'(?:find|locate|look\s+for)\s+.*?\s+(?:and|then)\s+(?:replace|change|update|add|modify)', text)
        if find_and_match:
            result['mode'] = 'insert_after'
            result['verb'] = 'find_and_modify'
            return result

        # Pattern: "Change X to Y" or "Replace X with Y" or "Update X to Y"
        change_match = re.search(r'(?:change|replace|update|swap|switch)\s+.*?\s+(?:to|with|from)', text)
        if change_match:
            result['mode'] = 'insert_after'
            result['verb'] = 'replace'
            return result

        # Pattern: "Add this method after X" or "Add new method"
        add_match = re.search(r'add\s+(?:this\s+)?(?:new\s+)?(?:method|function|class|endpoint|route|import|scope|button|component)',
                              text)
>>>>>>> REPLACE

### Fix 2: Fix Idempotency Fingerprinting

**File:** `/ganuda/jr_executor/task_executor.py`

In `_apply_partial_edit()` (around line 459), increase fingerprint specificity.

<<<<<<< SEARCH
        # Idempotency check: skip if content already present in file
        # Only for insert/append modes (not replace - the point of replace is to change existing code)
        if mode in ('insert_top', 'append', 'insert_after'):
            # Use a unique multi-line fingerprint (first 3 non-blank non-comment lines)
            fingerprint_lines = [l.strip() for l in new_lines
                                 if l.strip() and not l.strip().startswith('#')][:3]
            existing_stripped = [l.strip() for l in existing_lines]
            if fingerprint_lines and all(fp in existing_stripped for fp in fingerprint_lines):
                print(f"[PartialEdit] SKIP: Content already present ({mode})")
                return {
                    'success': True,
                    'written': len(existing_content),
                    'path': filepath,
                    'mode': f'partial_edit:{mode}:skipped',
                    'old_lines': original_line_count,
                    'new_lines': original_line_count,
                    'note': 'Content already present, skipped'
                }
=======
        # Idempotency check: skip if content already present in file
        # Only for insert/append modes (not replace - the point of replace is to change existing code)
        if mode in ('insert_top', 'append', 'insert_after'):
            # Use a unique multi-line fingerprint — require 5+ significant lines
            # Exclude common boilerplate: imports, loggers, empty lines, comments
            boilerplate_patterns = {'import ', 'from ', 'logger', 'logging', 'return', 'pass', 'def __init__'}
            fingerprint_lines = [
                l.strip() for l in new_lines
                if l.strip()
                and not l.strip().startswith('#')
                and not any(l.strip().startswith(bp) for bp in boilerplate_patterns)
            ][:5]
            existing_stripped = [l.strip() for l in existing_lines]
            # Require ALL 5 lines to match (not just 3) to reduce false positives
            if len(fingerprint_lines) >= 5 and all(fp in existing_stripped for fp in fingerprint_lines):
                print(f"[PartialEdit] SKIP: Content already present ({mode}) — 5-line fingerprint matched")
                return {
                    'success': True,
                    'written': len(existing_content),
                    'path': filepath,
                    'mode': f'partial_edit:{mode}:skipped',
                    'old_lines': original_line_count,
                    'new_lines': original_line_count,
                    'note': 'Content already present, skipped (5-line fingerprint)'
                }
            elif len(fingerprint_lines) < 5:
                print(f"[PartialEdit] Skipping idempotency check — only {len(fingerprint_lines)} significant lines (need 5)")
>>>>>>> REPLACE

### Fix 3: Add Guardrail Bypass for Search-Replace Steps

**File:** `/ganuda/jr_executor/task_executor.py`

The `validate_file_write()` guardrails should not apply when the step type is `search_replace` or `partial_edit`. These operations have their own safety mechanisms.

In `safe_file_write()` (around line 2152), the check already bypasses for `REPLACE` mode. No change needed here — the fix is in routing (Fix 1 ensures snippets route to partial_edit, not write).

### Fix 4: Track Step Completion in Retries

**File:** `/ganuda/jr_executor/task_executor.py`

In `_retry_with_reflection()` (around line 1196), add step tracking to avoid re-executing succeeded steps.

<<<<<<< SEARCH
        augmented_instructions = instructions + reflection_context

        # Re-extract steps with augmented context
        steps = self._extract_steps_from_instructions(augmented_instructions)

        if not steps:
            print(f"[RETRY] No steps extracted from augmented instructions")
            return {
                'success': False,
                'error': f'Retry {attempt}: No executable steps from augmented instructions',
                'steps_executed': [],
                'retry_attempt': attempt
            }

        # Execute retry through same security pipeline
        try:
            step_results = self.execute_steps(steps)
=======
        augmented_instructions = instructions + reflection_context

        # Re-extract steps with augmented context
        steps = self._extract_steps_from_instructions(augmented_instructions)

        if not steps:
            print(f"[RETRY] No steps extracted from augmented instructions")
            return {
                'success': False,
                'error': f'Retry {attempt}: No executable steps from augmented instructions',
                'steps_executed': [],
                'retry_attempt': attempt
            }

        # Filter out already-completed steps (from previous attempt)
        completed_paths = set()
        if previous_result and previous_result.get('steps_executed'):
            for prev_step in previous_result['steps_executed']:
                if prev_step.get('success') and prev_step.get('path'):
                    completed_paths.add(prev_step['path'])
                    print(f"[RETRY] Skipping already-completed: {prev_step['path']}")

        steps_to_run = []
        for s in steps:
            step_path = s.get('args', {}).get('path', '')
            if step_path and step_path in completed_paths:
                continue
            steps_to_run.append(s)

        if not steps_to_run:
            print(f"[RETRY] All steps already completed, nothing to retry")
            return {
                'success': True,
                'steps_executed': previous_result.get('steps_executed', []),
                'retry_attempt': attempt
            }

        print(f"[RETRY] Running {len(steps_to_run)} of {len(steps)} steps (skipping {len(steps) - len(steps_to_run)} completed)")

        # Execute retry through same security pipeline
        try:
            step_results = self.execute_steps(steps_to_run)
>>>>>>> REPLACE

**Note:** This requires passing `previous_result` to `_retry_with_reflection()`. Update the method signature:

<<<<<<< SEARCH
    def _retry_with_reflection(self, task: Dict, instructions: str,
                                result: Dict, reflection: Dict,
                                attempt: int) -> Dict:
=======
    def _retry_with_reflection(self, task: Dict, instructions: str,
                                result: Dict, reflection: Dict,
                                attempt: int, previous_result: Dict = None) -> Dict:
>>>>>>> REPLACE

And update the call site (around line 806):

<<<<<<< SEARCH
                        for attempt in range(1, self.MAX_RETRIES + 1):
                            retry_result = self._retry_with_reflection(
                                task, instructions, current_result,
                                current_reflection, attempt
                            )
=======
                        for attempt in range(1, self.MAX_RETRIES + 1):
                            retry_result = self._retry_with_reflection(
                                task, instructions, current_result,
                                current_reflection, attempt,
                                previous_result=current_result
                            )
>>>>>>> REPLACE

## Verification

1. Re-queue task #515 (PII fix) using SEARCH/REPLACE format — should succeed
2. Check executor logs for `[SmartExtract] Partial edit step:` instead of `[SmartExtract] Write step:`
3. No `BLOCKED:` messages in executor output for legitimate edits
4. Files modified in-place, not replaced wholesale
5. Idempotency check only skips when 5+ significant lines match (not 3 boilerplate lines)

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `jr_executor/task_executor.py` | MODIFY | Broaden mode detection, fix idempotency, track retries |

## Security Notes

- Guardrails remain active for actual full-file write operations
- SearchReplaceEditor's own safety (unique match, backup, syntax validation) protects edit operations
- No changes to path validation, forbidden paths, or file size limits
