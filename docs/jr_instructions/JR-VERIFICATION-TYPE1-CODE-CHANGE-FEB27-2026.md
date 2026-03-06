# Type 1 Verification: Code Change Confirmation

**Council Vote**: #36fd8d2ec0fd0473 (unanimous — verification as first-class operation)
**Coyote**: "We track what we DID but not what HAPPENED"
**Priority**: P1 — Binding condition before next feature sprint
**Assigned**: Software Engineer Jr.

---

## Context

The post-flight hash check in `task_executor.py` already computes pre/post hashes but only PRINTS the result. A task where all SR blocks hit the idempotency skip (file unchanged) completes with `success=True`. This is how TEG #935-N00 was marked completed with no code change.

## Step 1: Make post-flight hash check enforce failure on zero changes

File: `/ganuda/jr_executor/task_executor.py`

Find the post-flight comparison loop that prints "[PostFlight]" messages. After the loop completes, add enforcement logic.

<<<<<<< SEARCH
        # Post-flight comparison
        for pf in preflight_results:
            path = pf.get('path', '')
            if path and os.path.exists(path) and pf.get('hash'):
                with open(path, 'rb') as f:
                    post_hash = _hashlib.sha256(f.read()).hexdigest()[:16]
                changed = post_hash != pf['hash']
                if changed:
                    print(f"[PostFlight] {basename}: {pf['hash']} -> {post_hash} (MODIFIED)")
                else:
                    print(f"[PostFlight] {basename}: unchanged (idempotent or skipped)")
=======
        # Post-flight comparison with verification enforcement
        files_modified = 0
        files_unchanged = 0
        for pf in preflight_results:
            path = pf.get('path', '')
            basename = os.path.basename(path) if path else 'unknown'
            if path and os.path.exists(path) and pf.get('hash'):
                with open(path, 'rb') as f:
                    post_hash = _hashlib.sha256(f.read()).hexdigest()[:16]
                changed = post_hash != pf['hash']
                if changed:
                    print(f"[PostFlight] {basename}: {pf['hash']} -> {post_hash} (MODIFIED)")
                    files_modified += 1
                else:
                    print(f"[PostFlight] {basename}: unchanged (idempotent or skipped)")
                    files_unchanged += 1

        # Type 1 Verification: if we expected to modify files but none changed, flag it
        if preflight_results and files_modified == 0 and files_unchanged > 0:
            print(f"[VERIFY] WARNING: {files_unchanged} target file(s) unchanged after execution")
            if result.get('success'):
                result['success'] = False
                result['error'] = f"TYPE1_VERIFY_FAIL: All {files_unchanged} target files unchanged after SR execution. Likely stale SEARCH strings."
                result['verification_failed'] = True
>>>>>>> REPLACE

## Step 2: Add hash_verified field to SR editor results

File: `/ganuda/jr_executor/search_replace_editor.py`

After the file write succeeds and before returning, add hash verification data to the result dict.

<<<<<<< SEARCH
                result['success'] = True
                result['lines_changed'] = abs(len(replace_text.splitlines()) - len(search_text.splitlines()))
=======
                result['success'] = True
                result['lines_changed'] = abs(len(replace_text.splitlines()) - len(search_text.splitlines()))
                # Type 1 verification: confirm file actually changed
                import hashlib as _ht1
                result['pre_hash'] = _ht1.sha256(content.encode('utf-8')).hexdigest()[:16]
                result['post_hash'] = _ht1.sha256(new_content.encode('utf-8')).hexdigest()[:16]
                result['hash_verified'] = result['pre_hash'] != result['post_hash']
>>>>>>> REPLACE

## Verification

After applying these changes:
1. The executor will fail tasks where SR blocks don't modify any files (stale SEARCH strings)
2. Each SR result includes pre/post hashes for audit
3. Idempotent re-runs are correctly flagged instead of silently succeeding

## What This Prevents

- TEG #935-N00 scenario: SEARCH string doesn't match, task marked completed, code unchanged
- Password migration scenario: rotation script runs but old patterns still present
- Any future SR task that exits 0 but changes nothing
