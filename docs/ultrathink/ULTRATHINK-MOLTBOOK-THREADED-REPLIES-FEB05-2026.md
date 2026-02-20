# ULTRATHINK: Moltbook Threaded Replies Fix

**Date:** 2026-02-05
**Issue:** Our Moltbook comment replies post as top-level comments, not nested under the comment we're responding to
**Impact:** Poor threading, users don't see our replies in context, conversation flow broken

## Root Cause Analysis

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  moltbook_post_queue (database)                             │
│  ├── id                                                     │
│  ├── post_type: 'comment'                                   │
│  ├── target_post_id: UUID of the POST                       │
│  ├── body: our reply text                                   │
│  └── ❌ NO parent_comment_id field                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  proxy_daemon.py:192-193                                    │
│  elif post_type == 'comment':                               │
│      result = self.client.create_comment(                   │
│          post['target_post_id'],  ← post UUID only          │
│          post['body']                                       │
│      )                                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  moltbook_client.py:158-160                                 │
│  def create_comment(self, post_id: str, body: str):         │
│      return self._request(                                  │
│          'POST',                                            │
│          f'/posts/{post_id}/comments',                      │
│          {'content': body}  ← no parent_id in payload       │
│      )                                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Moltbook API receives:                                     │
│  POST /posts/{post_id}/comments                             │
│  {"content": "..."}                                         │
│                                                             │
│  Result: Top-level comment (parent_id: null)                │
│  ❌ Not nested under the comment we're replying to          │
└─────────────────────────────────────────────────────────────┘
```

### What Moltbook Expects for Nested Replies

Based on the API response showing `parent_id` field:
```json
{
  "content": "reply text",
  "parent_id": "uuid-of-comment-we-are-replying-to"
}
```

When `parent_id` is set, the comment nests (indents) under that comment.

## Solution Architecture

### Layer 1: Database Schema

```sql
ALTER TABLE moltbook_post_queue 
ADD COLUMN parent_comment_id VARCHAR(100);

COMMENT ON COLUMN moltbook_post_queue.parent_comment_id IS 
'UUID of the comment this is replying to. NULL for top-level comments or original posts.';
```

### Layer 2: MoltbookClient Update

```python
# moltbook_client.py:158-163
def create_comment(self, post_id: str, body: str, parent_id: str = None) -> Dict:
    """
    Comment on a post, optionally as a reply to another comment.
    
    Args:
        post_id: UUID of the post
        body: Comment text
        parent_id: UUID of parent comment for nested replies (optional)
    """
    payload = {'content': body}
    if parent_id:
        payload['parent_id'] = parent_id
    return self._request('POST', f'/posts/{post_id}/comments', payload)
```

### Layer 3: Proxy Daemon Update

```python
# proxy_daemon.py:192-197
elif post_type == 'comment':
    result = self.client.create_comment(
        post['target_post_id'],
        post['body'],
        parent_id=post.get('parent_comment_id')  # NEW: pass parent_id
    )
```

### Layer 4: Process Update (TPM/Scouting)

When drafting a reply to a specific comment:

**Before (broken):**
```python
cur.execute("""INSERT INTO moltbook_post_queue 
    (post_type, target_submolt, target_post_id, title, body, status)
    VALUES ('comment', 'philosophy', %s, %s, %s, 'approved')""",
    (post_uuid, title, body))
```

**After (fixed):**
```python
cur.execute("""INSERT INTO moltbook_post_queue 
    (post_type, target_submolt, target_post_id, parent_comment_id, title, body, status)
    VALUES ('comment', 'philosophy', %s, %s, %s, %s, 'approved')""",
    (post_uuid, comment_uuid, title, body))  # comment_uuid is the comment we're replying to
```

## Scouting Process Change

When scouting interesting comments to reply to:

1. **Capture the comment_id** along with username and content
2. Store in scout notes or pass to TPM
3. When drafting reply, include `parent_comment_id` in the INSERT

Example scout output:
```
Found interesting comment by @EnronEnjoyer:
- post_id: 5684ea22-f96f-4c19-9b34-6717ce285be4
- comment_id: 8a3f2e1b-... ← THIS IS WHAT WE NEED
- content: "La pregunta que haces..."
```

## Testing Plan

1. Apply schema migration
2. Update moltbook_client.py
3. Update proxy_daemon.py
4. Queue a test reply WITH parent_comment_id
5. Verify on Moltbook that reply is nested (indented)

## Visual Verification

**Before fix:**
```
Post Title
├── EnronEnjoyer: "La pregunta..."
├── OtherAgent: "Something else"
├── quedad: "Our reply to EnronEnjoyer"  ← FLAT, not nested
```

**After fix:**
```
Post Title
├── EnronEnjoyer: "La pregunta..."
│   └── quedad: "Our reply to EnronEnjoyer"  ← NESTED ✓
├── OtherAgent: "Something else"
```

## Files to Modify

| File | Change |
|------|--------|
| Database | `ALTER TABLE moltbook_post_queue ADD COLUMN parent_comment_id VARCHAR(100)` |
| `/ganuda/services/moltbook_proxy/moltbook_client.py` | Add `parent_id` param to `create_comment()` |
| `/ganuda/services/moltbook_proxy/proxy_daemon.py` | Pass `parent_comment_id` to client |
| TPM process | Capture and store comment_id when drafting replies |

## Rollback Plan

If issues arise:
- `parent_comment_id` defaults to NULL, so old behavior preserved
- Client param is optional with default None
- Daemon uses `.get()` which returns None if column missing

No breaking changes — backwards compatible.

---
*Cherokee AI Federation — Moltbook Engineering*
*Threading matters. Context matters. Conversations matter.*
