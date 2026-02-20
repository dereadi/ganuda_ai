# JR-MOLTBOOK-THREADED-REPLIES-FEB05-2026

## Priority: P0
## Assignee: Moltbook Jr / Integration Jr
## Estimated Effort: 1 hour
## Blocks: All future comment replies

## Context

Our Moltbook comment replies post as top-level comments instead of nested (indented) under the comment we're replying to. This breaks conversation flow — users don't see our replies in context.

**Root Cause:** The `create_comment()` function doesn't accept or pass a `parent_id` parameter.

**Ultrathink Reference:** `/ganuda/docs/ultrathink/ULTRATHINK-MOLTBOOK-THREADED-REPLIES-FEB05-2026.md`

## Database Schema (COMPLETE)

The schema has already been updated:
```sql
ALTER TABLE moltbook_post_queue ADD COLUMN IF NOT EXISTS parent_comment_id VARCHAR(100);
```

This column stores the UUID of the comment we're replying to. NULL for top-level comments.

## Deliverables

### 1. Update moltbook_client.py

**File:** `/ganuda/services/moltbook_proxy/moltbook_client.py`

**Current (line 158-160):**
```python
def create_comment(self, post_id: str, body: str) -> Dict:
    """Comment on a post."""
    return self._request('POST', f'/posts/{post_id}/comments', {'content': body})
```

**Change to:**
```python
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

### 2. Update proxy_daemon.py

**File:** `/ganuda/services/moltbook_proxy/proxy_daemon.py`

**Current (line 192-193):**
```python
elif post_type == 'comment':
    result = self.client.create_comment(post['target_post_id'], post['body'])
```

**Change to:**
```python
elif post_type == 'comment':
    result = self.client.create_comment(
        post['target_post_id'],
        post['body'],
        parent_id=post.get('parent_comment_id')
    )
```

## Testing

1. Queue a test reply WITH `parent_comment_id` set:
```sql
INSERT INTO moltbook_post_queue
(post_type, target_post_id, parent_comment_id, body, status)
VALUES (
    'comment',
    'uuid-of-post',
    'uuid-of-comment-we-are-replying-to',
    'Test threaded reply',
    'approved'
);
```

2. Let daemon publish it
3. Check Moltbook — reply should appear nested (indented) under the parent comment

## Backwards Compatibility

- `parent_comment_id` defaults to NULL — existing queue items unaffected
- `parent_id` parameter is optional with default None — old code paths work
- Daemon uses `.get()` which returns None if column missing

No breaking changes.

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
│   └── quedad: "Our reply to EnronEnjoyer"  ← NESTED
├── OtherAgent: "Something else"
```

## Process Change (Future)

When scouting comments to reply to, capture the `comment_id` along with the content and username. Store it in the queue's `parent_comment_id` field when drafting replies.

This task covers the code infrastructure. Scouting process updates are separate.

---
*Cherokee AI Federation — Moltbook Engineering*
*Threading matters. Context matters. Conversations matter.*
