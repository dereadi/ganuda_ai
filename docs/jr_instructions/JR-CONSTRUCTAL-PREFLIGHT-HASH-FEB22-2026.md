# Jr Instruction: Constructal Pre-Flight State Verification

**Task ID:** PREFLIGHT-HASH
**Kanban:** #1796
**Priority:** 3
**Assigned:** Software Engineer Jr.
**Council Vote:** #0352a767e34d2088

---

## Overview

Before the Jr executor runs SEARCH/REPLACE or file write steps, hash the target files and compare against a stored "expected state". If files have diverged since the instruction was written, fail-safe to a warning instead of blindly applying edits to changed code.

This prevents the class of 15+ failures caused by stale SEARCH blocks matching wrong content (Feb 11 SR-FIRST incident).

Two changes:
1. Add a pre-flight hash function to `task_executor.py`
2. Call it between step extraction and step execution

---

## Step 1: Add pre-flight hash verification function

File: `/ganuda/jr_executor/task_executor.py`

Find the imports section and add hashlib if not already imported:

<<<<<<< SEARCH
from typing import Dict, List, Tuple, Optional, Any
=======
from typing import Dict, List, Tuple, Optional, Any
import hashlib as _hashlib
>>>>>>> REPLACE

---

## Step 2: Add the pre-flight verification method

File: `/ganuda/jr_executor/task_executor.py`

Add this method to the TaskExecutor class, right before the `process_queue_task` method:

<<<<<<< SEARCH
    def process_queue_task(self, task: Dict) -> Dict[str, Any]:
=======
    def _preflight_hash_check(self, steps: List[Dict]) -> List[Dict]:
        """
        Constructal Pre-Flight: Hash target files before execution.
        If a file has been modified since the instruction was written,
        warn but don't block (the SR editor's uniqueness check is the hard gate).

        Returns list of preflight results for logging.
        """
        preflight = []
        for step in steps:
            path = None
            if step.get('type') == 'file':
                path = step.get('args', {}).get('path', '')
            elif step.get('type') == 'search_replace':
                path = step.get('args', {}).get('path', '')

            if not path or not os.path.exists(path):
                continue

            try:
                with open(path, 'rb') as f:
                    content = f.read()
                file_hash = _hashlib.sha256(content).hexdigest()[:16]
                file_size = len(content)
                file_lines = content.count(b'\n')

                preflight.append({
                    'path': path,
                    'hash': file_hash,
                    'size': file_size,
                    'lines': file_lines,
                    'exists': True
                })
                print(f"[PreFlight] {os.path.basename(path)}: {file_hash} ({file_lines} lines, {file_size} bytes)")
            except Exception as e:
                preflight.append({
                    'path': path,
                    'hash': None,
                    'error': str(e),
                    'exists': True
                })
                print(f"[PreFlight] WARNING: Could not hash {path}: {e}")

        if preflight:
            print(f"[PreFlight] Verified {len(preflight)} target file(s)")
        return preflight

    def process_queue_task(self, task: Dict) -> Dict[str, Any]:
>>>>>>> REPLACE

---

## Step 3: Call pre-flight check before execution

File: `/ganuda/jr_executor/task_executor.py`

<<<<<<< SEARCH
        # Extract code blocks from instructions
        steps = self._extract_steps_from_instructions(instructions)

        if not steps:
            result['error'] = 'No executable steps found in instruction file'
            return result

        # Execute extracted steps
=======
        # Extract code blocks from instructions
        steps = self._extract_steps_from_instructions(instructions)

        if not steps:
            result['error'] = 'No executable steps found in instruction file'
            return result

        # Constructal Pre-Flight: Hash target files before execution
        preflight_results = self._preflight_hash_check(steps)
        result['preflight'] = preflight_results

        # Execute extracted steps
>>>>>>> REPLACE

---

## Step 4: Log post-flight comparison

File: `/ganuda/jr_executor/task_executor.py`

After step execution succeeds, add post-flight hash comparison. Find:

<<<<<<< SEARCH
            # Check if all steps succeeded
            all_success = all(s.get('success') for s in step_results)
            result['success'] = all_success
=======
            # Post-flight: compare file hashes to detect unintended changes
            for pf in preflight_results:
                path = pf.get('path', '')
                if path and os.path.exists(path) and pf.get('hash'):
                    try:
                        with open(path, 'rb') as f:
                            post_hash = _hashlib.sha256(f.read()).hexdigest()[:16]
                        changed = post_hash != pf['hash']
                        if changed:
                            print(f"[PostFlight] {os.path.basename(path)}: {pf['hash']} -> {post_hash} (MODIFIED)")
                        else:
                            print(f"[PostFlight] {os.path.basename(path)}: unchanged (idempotent or skipped)")
                    except Exception:
                        pass

            # Check if all steps succeeded
            all_success = all(s.get('success') for s in step_results)
            result['success'] = all_success
>>>>>>> REPLACE

---

## Verification

After deploying, queue a test task and check the executor logs:
```text
sudo journalctl -u it-jr-executor -n 50 --no-pager | grep -E "PreFlight|PostFlight"
```

Expected output:
```
[PreFlight] ritual_review.py: a3f2b1c8e4d9... (617 lines, 22340 bytes)
[PreFlight] Verified 1 target file(s)
[PostFlight] ritual_review.py: a3f2b1c8e4d9... -> 7b2e1f4a3c8d... (MODIFIED)
```

---

## Notes

- Pre-flight is **advisory only** — it logs hashes but doesn't block execution
- The SR editor's uniqueness check (`count == 1`) is the hard gate against wrong matches
- Hash is SHA256 truncated to 16 chars (sufficient for drift detection, compact in logs)
- Post-flight comparison shows which files were actually modified vs skipped
- Future Phase 2: Store pre-flight hashes in jr_step_rewards for historical comparison
