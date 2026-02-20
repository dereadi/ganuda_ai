# KB-MOLTBOOK-CONTENT-FIELD-BUG-FEB04-2026
## Moltbook API Silent Field Rejection — `body` vs `content`

### Incident
**Date:** 2026-02-03/04
**Severity:** P0
**Impact:** All 4 posts published to Moltbook had no body content — title only. Posts attracted troll comments ("looking for friends with no content?"). Content was in our local database but never reached the platform.

### Root Cause
The Moltbook API `POST /posts` expects the text field as `content`, not `body`. Our `moltbook_client.py` sent `{'title': title, 'body': body}`. The API silently accepted the request (HTTP 200, `"success": true`) and discarded the unrecognized `body` field.

### Why It Wasn't Caught
1. Moltbook API returns HTTP 200 even when `content` is missing — no validation error
2. The daemon checked `result.get('ok')` which was `True`
3. The daemon logged "Published post #X to Moltbook" with no indication of a problem
4. The `moltbook_response` stored in our database showed `"content": null` but we never checked it
5. The bug was discovered by a troll commenter (FiverrClawOfficial) who pointed out "no content"

### Fix Applied
Changed `moltbook_client.py` line 143:
```python
# Before (broken):
payload = {'title': title, 'body': body}

# After (fixed):
payload = {'title': title, 'content': body}
```

### Recovery Actions
1. Fixed the field name in the client
2. Deleted all 4 empty posts from Moltbook via `DELETE /posts/:id`
3. Reset queue entries 1-4 to `approved` for re-publish
4. Daemon restart required to pick up the fix

### Lessons Learned

1. **Always verify the first post renders correctly on the target platform before publishing more.** We published 4 posts without checking if any had visible content.

2. **Silent API acceptance is a class of bug.** When an API returns 200 but ignores unknown fields, the only way to catch it is to read back the response and verify the data round-tripped. Our daemon should validate that `moltbook_response.post.content` is not null after publishing.

3. **Read the API docs before writing the client.** The Moltbook GitHub repo (github.com/moltbook/api) clearly shows `content` as the field name. The client was written using `body` by assumption.

4. **Troll comments can contain signal.** FiverrClawOfficial's "no content" comment was dismissed as trolling, but it was an accurate bug report.

5. **Moltbook has no PATCH/PUT for posts.** HTTP 405 on both. Once a post is created, its content cannot be updated — only deleted and re-created. This means any future content bugs result in permanent data loss (comments, upvotes lost on re-creation).

6. **Moltbook has no moderator delete.** Submolt owners cannot delete other agents' posts. "You can only delete your own posts." This is a platform limitation that affects community moderation.

### Related Documents
- `/ganuda/docs/jr_instructions/JR-MOLTBOOK-P0-CONTENT-FIELD-FIX-FEB04-2026.md`
- `/ganuda/docs/kb/KB-JR-EXECUTOR-MOLTBOOK-FAILURES-FEB03-2026.md`
- `/ganuda/docs/protocols/MOLTBOOK-CONTENT-SHARING-POLICY-FEB03-2026.md`

### CMDB Update
- Service: moltbook-proxy
- Component: moltbook_client.py
- Change: Payload field `body` → `content` for POST /posts
- Status: Fixed, pending daemon restart

---
*For Seven Generations*
