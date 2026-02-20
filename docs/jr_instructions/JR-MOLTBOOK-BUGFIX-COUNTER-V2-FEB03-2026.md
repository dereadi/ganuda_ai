# JR-MOLTBOOK-BUGFIX-COUNTER-V2-FEB03-2026

## Fix Moltbook Daemon Rate Limit Counter Bug (Remediated)

| Field          | Value                                                    |
|----------------|----------------------------------------------------------|
| Task ID        | MOLTBOOK-BUGFIX-COUNTER-002                              |
| Priority       | P1 — Sacred Fire                                         |
| Assigned To    | Software Engineer Jr.                                    |
| Target Node    | redfin (192.168.132.223)                                 |
| Status         | Ready for execution                                      |
| Depends On     | None                                                     |
| Remediation Of | MOLTBOOK-BUGFIX-COUNTER-001 (failed — guardrail blocked) |

---

## Context

The Moltbook proxy daemon at `/ganuda/services/moltbook_proxy/proxy_daemon.py` has a bug where the daily rate limit counters (`posts_today`, `comments_today`) increment on EVERY API attempt, including 429 rate-limited retries. This causes the daemon to exhaust its daily post limit after just one successful post (3 retries + 1 success = counter at 4 = POSTS_PER_DAY limit hit).

**Previous attempt failed** because the executor replaced the entire 299-line file with a 15-line snippet, triggering the >50% file size reduction guardrail. This instruction uses FIND/REPLACE format to avoid that.

---

## Step 1: Move posts_today Counter Inside Success Block

**FILE**: `/ganuda/services/moltbook_proxy/proxy_daemon.py`
**ACTION**: EDIT (find and replace)

FIND (exact match, lines 184-195):
```python
        else:
            result = self.client.create_post(
                title=post.get('title', ''),
                body=post['body'],
                submolt=post.get('target_submolt')
            )
            self.posts_today += 1

        if result.get('ok'):
            self.queue.mark_posted(post['id'], result.get('data', {}))
            self._log_outbound(full_content, f'/{post_type}', result.get('status', 0))
            logger.info(f"Published {post_type} #{post['id']} to Moltbook")
```

REPLACE WITH:
```python
        else:
            result = self.client.create_post(
                title=post.get('title', ''),
                body=post['body'],
                submolt=post.get('target_submolt')
            )

        if result.get('ok'):
            # Only increment counters on successful publication
            if post_type == 'comment':
                self.comments_today += 1
            else:
                self.posts_today += 1
            self.queue.mark_posted(post['id'], result.get('data', {}))
            self._log_outbound(full_content, f'/{post_type}', result.get('status', 0))
            logger.info(f"Published {post_type} #{post['id']} to Moltbook")
```

## Step 2: Remove Old comments_today Counter

**FILE**: `/ganuda/services/moltbook_proxy/proxy_daemon.py`
**ACTION**: EDIT (find and replace)

FIND (exact match, lines 181-183):
```python
        elif post_type == 'comment':
            result = self.client.create_comment(post['target_post_id'], post['body'])
            self.comments_today += 1
```

REPLACE WITH:
```python
        elif post_type == 'comment':
            result = self.client.create_comment(post['target_post_id'], post['body'])
```

## Step 3: Verify

Run these commands to verify the fix:

```bash
# Syntax check
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/proxy_daemon.py').read())" && echo "SYNTAX OK"

# Verify counters are only inside the success block
grep -n 'posts_today\|comments_today' /ganuda/services/moltbook_proxy/proxy_daemon.py

# Expected output should show:
#   - self.posts_today = 0 (initialization)
#   - self.comments_today = 0 (initialization)
#   - POSTS_PER_DAY / COMMENTS_PER_DAY (limit checks)
#   - self.posts_today += 1 (INSIDE if result.get('ok') block)
#   - self.comments_today += 1 (INSIDE if result.get('ok') block)
```

---

## Security Checklist

- [ ] No new imports added
- [ ] No new external connections
- [ ] No changes to output_filter.py or sanitizer.py
- [ ] File line count within ±10 lines of original (299 lines)
- [ ] `python3 -c "import ast; ast.parse(...)"` passes

---

## What This Fixes

Before: 3 retries (counter→3) + 1 success (counter→4) = daily limit hit. Posts #2 and #3 stuck.
After: 3 retries (counter stays 0) + 1 success (counter→1) = 3 more posts available today.
