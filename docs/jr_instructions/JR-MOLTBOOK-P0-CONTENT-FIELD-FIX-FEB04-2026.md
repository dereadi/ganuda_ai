# JR Instruction: P0: Fix Moltbook Post Content Field Name

**Priority:** P0 - CRITICAL
**Sprint:** Moltbook Integration Emergency
**Created:** 2026-02-04
**Author:** TPM via Claude Code
**Target:** redfin
**Blocks:** All future Moltbook posts from having body content
**Council Pre-Approved:** audit_hash 2c8f884c62c393af

## Problem Statement

The Moltbook proxy daemon is publishing ALL posts with title only and no body text. Every post created through the proxy arrives on Moltbook as a title-only stub because the API payload uses the wrong field name.

**Root Cause:** In `/ganuda/services/moltbook_proxy/moltbook_client.py`, the `create_post` method sends the payload key `body` but the Moltbook API expects the key `content`. The post title works because `title` is correct, but the body text is silently discarded by the API because `body` is not a recognized field.

**Impact:** Every post published through the proxy since deployment has been missing its body text. This is a silent data loss -- the API accepts the request, returns success, but ignores the unrecognized `body` field entirely.

**Current code (~line 142):**
```python
def create_post(self, title: str, body: str, submolt: str = None) -> Dict:
    payload = {'title': title, 'body': body}
    if submolt:
        payload['submolt'] = submolt
    return self._request('POST', '/posts', payload)
```

**Fix:** Change `'body': body` to `'content': body` in the payload dict. The method signature parameter name `body` stays the same (that is our internal name). Only the API-facing payload key changes.

## Required Changes

MODIFY: `/ganuda/services/moltbook_proxy/moltbook_client.py`

### Step 1: Fix the field name

```bash
python3 << 'PYEOF'
filepath = '/ganuda/services/moltbook_proxy/moltbook_client.py'
with open(filepath, 'r') as f:
    content = f.read()

old = "payload = {'title': title, 'body': body}"
new = "payload = {'title': title, 'content': body}"

if old not in content:
    print("ERROR: Could not find target line")
    exit(1)

content = content.replace(old, new)
with open(filepath, 'w') as f:
    f.write(content)
print("OK: Fixed body -> content in create_post payload")
PYEOF
```

### Step 2: Verify the fix

```bash
grep -n "payload = {'title'" /ganuda/services/moltbook_proxy/moltbook_client.py
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/moltbook_client.py').read()); print('syntax OK')"
```

Expected output:
```
142:    payload = {'title': title, 'content': body}
syntax OK
```

### Step 3: Restart the daemon

NOTE: This step requires sudo (will be run manually by Chief). Just output the commands:

```bash
echo "=== Run these commands as root ==="
echo "sudo systemctl restart moltbook-proxy"
echo "sudo systemctl status moltbook-proxy"
```

### Step 4: Attempt to fix existing empty posts

Check whether the Moltbook API supports PATCH or PUT to update existing posts in-place. If it does, we can backfill the missing content. If not, we accept the empty posts as-is (deleting and re-posting would lose comments and upvotes).

```bash
MOLTBOOK_KEY=$(grep MOLTBOOK_API_KEY /ganuda/services/moltbook_proxy/.env | cut -d= -f2)

# Test if PATCH exists
echo "Testing PATCH endpoint..."
curl -s -w "\nHTTP:%{http_code}" -X PATCH -H "Authorization: Bearer $MOLTBOOK_KEY" -H "Content-Type: application/json" "https://www.moltbook.com/api/v1/posts/ec0f5ebb-e82f-4584-959e-46d483f027c1" -d '{"content": "test"}' 2>/dev/null | tail -2

# Test if PUT exists
echo "Testing PUT endpoint..."
curl -s -w "\nHTTP:%{http_code}" -X PUT -H "Authorization: Bearer $MOLTBOOK_KEY" -H "Content-Type: application/json" "https://www.moltbook.com/api/v1/posts/ec0f5ebb-e82f-4584-959e-46d483f027c1" -d '{"content": "test"}' 2>/dev/null | tail -2
```

## Rollback

Reverse the payload key change:
```
'content': body  -->  'body': body
```

Then restart the daemon. Note: reverting will cause posts to lose body text again.

---
FOR SEVEN GENERATIONS
