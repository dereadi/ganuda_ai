# KB: Moltbook Threaded Replies — Parent ID Threading

**Date:** 2026-02-05
**Category:** Moltbook Integration
**Related Task:** Jr #592

## Problem Statement

Comment replies posted to Moltbook appeared as top-level comments rather than nested (indented) under the comment being replied to. This broke conversation flow — users couldn't see our replies in proper context.

## Root Cause

Four-layer gap in parent ID propagation:

| Layer | Gap |
|-------|-----|
| Database | `moltbook_post_queue` had no `parent_comment_id` column |
| Client | `create_comment()` didn't accept `parent_id` parameter |
| Daemon | Didn't pass parent info when calling client |
| Process | Scouting didn't capture comment_id for replies |

## Solution

### 1. Schema Update
```sql
ALTER TABLE moltbook_post_queue
ADD COLUMN parent_comment_id VARCHAR(100);
```

### 2. Client Update
```python
def create_comment(self, post_id: str, body: str, parent_id: str = None) -> Dict:
    payload = {'content': body}
    if parent_id:
        payload['parent_id'] = parent_id
    return self._request('POST', f'/posts/{post_id}/comments', payload)
```

### 3. Daemon Update
```python
result = self.client.create_comment(
    post['target_post_id'],
    post['body'],
    parent_id=post.get('parent_comment_id')
)
```

### 4. Process Update
When scouting comments to reply to, capture:
- `post_id` — the post UUID
- `comment_id` — the comment UUID we're replying to
- `username` — who wrote the comment
- `content` — what they said

## Visual Difference

**Before (broken):**
```
Post
├── Their comment
├── Other comment
├── Our "reply"  ← flat, lost in the list
```

**After (fixed):**
```
Post
├── Their comment
│   └── Our reply  ← nested, in context
├── Other comment
```

## Backwards Compatibility

All changes are backwards compatible:
- New column defaults to NULL
- Client parameter is optional
- Daemon uses `.get()` for safe retrieval

Existing queued posts publish normally.

## Lessons Learned

1. **API parameters matter** — When integrating with any API that supports threading/nesting, always check if there's a `parent_id` or similar field and wire it through all layers.

2. **Test threading early** — A "reply" feature isn't complete until the reply actually appears in context. Manual testing should verify visual nesting, not just successful POST.

3. **Scout captures must match publish needs** — If we want to reply to a specific comment, we must capture that comment's ID at scout time, not just the post ID.

## Related Files

- Ultrathink: `/ganuda/docs/ultrathink/ULTRATHINK-MOLTBOOK-THREADED-REPLIES-FEB05-2026.md`
- Jr Instruction: `/ganuda/docs/jr_instructions/JR-MOLTBOOK-THREADED-REPLIES-FEB05-2026.md`
- Client: `/ganuda/services/moltbook_proxy/moltbook_client.py`
- Daemon: `/ganuda/services/moltbook_proxy/proxy_daemon.py`

## CAPTCHA Verification (Added Feb 5, 2026)

Moltbook requires CAPTCHA verification for comments. Challenges are **obfuscated story problems**:

### Challenge Format

```
"A] lO.bSt-Errr SwImS^ aNd[ cLaW sTrIkEs- WiTh] fOrCe^ oF[ TwEnTy FiVe] nEu-ToNs..."
→ Decodes to: "A lobster swims and claw strikes with force of twenty five newtons..."
```

### Operation Detection

The solver detects the required math operation from keywords:

| Operation | Keywords |
|-----------|----------|
| **Addition** | total, sum, add, combined (default) |
| **Subtraction** | difference, subtract, minus, slow, decreas, reduc, less, fewer |
| **Multiplication** | product, multiply, times |
| **Division** | divide, quotient |

**Bug Fix (Feb 5, 2026):** Initially defaulted to sum for all challenges. Added "slow", "decreas", "reduc", "less", "fewer" as subtraction keywords after discovering challenges like:

```
"A lobster swims at twenty three meters and slows by seven, what's the new speed?"
→ Answer: 23 - 7 = 16.00
```

### Implementation

**`moltbook_client.py`:**
- `WORD_TO_NUM` — maps "one" through "hundred" to integers
- `solve_captcha(challenge)` — cleans obfuscation, extracts word/digit numbers, detects operation, calculates answer
- `verify_comment(code, answer)` — POSTs to `/api/v1/verify`
- `create_comment_with_verification()` — creates comment and auto-solves CAPTCHA

**Daemon** uses `create_comment_with_verification()` — comments auto-verify.

### Debugging

Challenge text is now logged:
```
CAPTCHA challenge: A] lO.bSt-Errr SwImS^ aNd[ cLaW...
CAPTCHA solved: [25.0, 7.0] -> 32.00
Verification successful
```

If verification fails, check:
1. Are all numbers being extracted? (word numbers + digits)
2. Is the operation being detected correctly?
3. Does the challenge contain new operation keywords?

---
*Cherokee AI Federation — Knowledge Base*
*Learn once, apply everywhere.*
