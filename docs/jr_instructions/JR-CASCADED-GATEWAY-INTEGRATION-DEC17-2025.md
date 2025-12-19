# JR INSTRUCTIONS: Cascaded Council Gateway Integration
## December 17, 2025

### OBJECTIVE
Integrate cascaded voting mode into the LLM Gateway API endpoint.

---

## TASK 1: Create Gateway Patch File

Create `/ganuda/services/llm_gateway/cascaded_patch.py`:

```python
#!/usr/bin/env python3
"""
Cascaded Council Gateway Patch
Apply this patch to gateway.py to add cascaded voting mode.

Run: python3 cascaded_patch.py
"""

import re

GATEWAY_FILE = '/ganuda/services/llm_gateway/gateway.py'

# Patch 1: Update CouncilVoteRequest model to add mode parameter
PATCH_MODEL_OLD = '''class CouncilVoteRequest(BaseModel):
    question: str
    max_tokens: int = 300
    include_responses: bool = False'''

PATCH_MODEL_NEW = '''class CouncilVoteRequest(BaseModel):
    question: str
    max_tokens: int = 300
    include_responses: bool = False
    mode: str = "parallel"  # "parallel" or "cascaded"
    include_grpo: bool = False  # Include GRPO rankings'''

# Patch 2: Add import for cascaded_council at top of file (after existing imports)
PATCH_IMPORT = '''
# Cascaded Council Support
sys.path.insert(0, '/ganuda/lib')
try:
    from cascaded_council import cascaded_vote, rank_votes_grpo
    HAS_CASCADED = True
except ImportError:
    HAS_CASCADED = False
    print("[WARNING] cascaded_council not available")
'''

# Patch 3: Add cascaded mode check at start of council_vote function
PATCH_CASCADED_CHECK = '''
    # Check for cascaded mode
    if getattr(request, 'mode', 'parallel') == 'cascaded':
        if not HAS_CASCADED:
            raise HTTPException(status_code=501, detail="Cascaded mode not available")

        result = cascaded_vote(request.question, request.max_tokens)

        # Add GRPO rankings if requested
        if getattr(request, 'include_grpo', False):
            result['grpo_rankings'] = rank_votes_grpo(result.get('votes', []))

        # Log to audit
        elapsed = (time.time() - start) * 1000
        log_audit(api_key.key_id, "/v1/council/vote", "POST", 200, int(elapsed), 0, client_ip)

        # Save to database with cascaded mode flag
        audit_hash = hashlib.sha256(f"{time.time()}|{request.question}".encode()).hexdigest()[:16]
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO council_votes
                    (audit_hash, question, consensus, confidence, concerns, vote_mode, stages_completed, blocked_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    audit_hash,
                    request.question,
                    result.get('consensus', ''),
                    result.get('confidence', 0),
                    result.get('votes', []),
                    'cascaded',
                    result.get('stages_completed'),
                    result.get('blocked_by')
                ))
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to save cascaded vote: {e}")

        result['audit_hash'] = audit_hash
        result['response_time_ms'] = int(elapsed)
        return result
'''


def apply_patches():
    """Apply all patches to gateway.py"""
    print("Reading gateway.py...")
    with open(GATEWAY_FILE, 'r') as f:
        content = f.read()

    modified = False

    # Patch 1: Update model
    if 'mode: str = "parallel"' not in content:
        if PATCH_MODEL_OLD in content:
            content = content.replace(PATCH_MODEL_OLD, PATCH_MODEL_NEW)
            print("  [OK] Added mode parameter to CouncilVoteRequest")
            modified = True
        else:
            print("  [SKIP] CouncilVoteRequest not found or already modified")
    else:
        print("  [SKIP] Mode parameter already exists")

    # Patch 2: Add import
    if 'from cascaded_council import' not in content:
        # Find a good place to insert - after the existing imports
        import_marker = 'from concurrent.futures import ThreadPoolExecutor, as_completed'
        if import_marker in content:
            content = content.replace(import_marker, import_marker + PATCH_IMPORT)
            print("  [OK] Added cascaded_council import")
            modified = True
        else:
            print("  [WARN] Could not find import marker")
    else:
        print("  [SKIP] Cascaded import already exists")

    # Patch 3: Add cascaded check to council_vote
    if "mode', 'parallel') == 'cascaded'" not in content:
        # Find the council_vote function and add check after quota check
        quota_check = 'raise HTTPException(status_code=429, detail="Insufficient quota for council vote")'
        if quota_check in content:
            content = content.replace(quota_check, quota_check + PATCH_CASCADED_CHECK)
            print("  [OK] Added cascaded mode check to council_vote")
            modified = True
        else:
            print("  [WARN] Could not find quota check marker")
    else:
        print("  [SKIP] Cascaded check already exists")

    if modified:
        # Backup original
        backup_file = GATEWAY_FILE + '.backup'
        with open(backup_file, 'w') as f:
            with open(GATEWAY_FILE, 'r') as orig:
                f.write(orig.read())
        print(f"  [OK] Backup saved to {backup_file}")

        # Write patched file
        with open(GATEWAY_FILE, 'w') as f:
            f.write(content)
        print(f"  [OK] Patched gateway.py saved")
        print("\n*** RESTART GATEWAY TO APPLY CHANGES ***")
        print("Run: pkill -f 'uvicorn gateway' && cd /ganuda/services/llm_gateway && nohup uvicorn gateway:app --host 0.0.0.0 --port 8080 > /ganuda/logs/gateway.log 2>&1 &")
    else:
        print("\nNo changes needed - all patches already applied")

    return modified


if __name__ == "__main__":
    print("=" * 50)
    print("Cascaded Council Gateway Patch")
    print("=" * 50)
    apply_patches()
    print("=" * 50)
```

---

## Verification

```bash
cd /ganuda/services/llm_gateway && /home/dereadi/cherokee_venv/bin/python3 cascaded_patch.py
```

---

## SUCCESS CRITERIA

1. Patch script runs without errors
2. gateway.py backed up
3. CouncilVoteRequest has mode parameter
4. Cascaded import added
5. Cascaded mode check added to council_vote

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
