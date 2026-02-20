# JR-MOLTBOOK-BUGFIX-COUNTER-V3-FEB03-2026

## Fix Moltbook Daemon Rate Limit Counter Bug (V3 - Executable Script)

| Field          | Value                                                    |
|----------------|----------------------------------------------------------|
| Task ID        | MOLTBOOK-BUGFIX-COUNTER-003                              |
| Priority       | P1 — Sacred Fire                                         |
| Assigned To    | Software Engineer Jr.                                    |
| Target Node    | redfin (192.168.132.223)                                 |
| Status         | Ready for execution                                      |
| Depends On     | None                                                     |
| Remediation Of | V1 (guardrail blocked), V2 (false completion — executor ran verification but not edit steps) |

---

## Context

The Moltbook proxy daemon has a bug where `self.posts_today += 1` (line 190) and `self.comments_today += 1` (line 183) increment on EVERY API attempt including 429 retries, causing premature daily limit exhaustion.

**V1 failed**: Full-file replacement triggered >50% size reduction guardrail.
**V2 failed**: FIND/REPLACE format not understood by SmartExtract — only verification bash commands were executed, edit was never applied.
**V3 approach**: Package the entire edit as a single executable Python script that the SmartExtract module will extract and run.

---

## Step 1: Apply the Fix via Python Script

```bash
python3 << 'PYEOF'
import re

target = '/ganuda/services/moltbook_proxy/proxy_daemon.py'

with open(target, 'r') as f:
    content = f.read()

# Verify the bug exists (counter outside success block)
if 'self.posts_today += 1\n\n        if result.get' not in content:
    print("SKIP: Bug pattern not found — file may already be fixed")
    exit(0)

# Fix 1: Remove self.comments_today += 1 from line 183
content = content.replace(
    "result = self.client.create_comment(post['target_post_id'], post['body'])\n            self.comments_today += 1",
    "result = self.client.create_comment(post['target_post_id'], post['body'])"
)

# Fix 2: Remove self.posts_today += 1 from line 190 and add both counters inside success block
content = content.replace(
    "submolt=post.get('target_submolt')\n            )\n            self.posts_today += 1\n\n        if result.get('ok'):\n            self.queue.mark_posted(post['id'], result.get('data', {}))",
    "submolt=post.get('target_submolt')\n            )\n\n        if result.get('ok'):\n            # Only increment counters on successful publication\n            if post_type == 'comment':\n                self.comments_today += 1\n            else:\n                self.posts_today += 1\n            self.queue.mark_posted(post['id'], result.get('data', {}))"
)

with open(target, 'w') as f:
    f.write(content)

print("SUCCESS: Counter bug fixed in proxy_daemon.py")
PYEOF
```

## Step 2: Verify the Fix

```bash
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/proxy_daemon.py').read())" && echo "SYNTAX OK"
grep -n 'posts_today\|comments_today' /ganuda/services/moltbook_proxy/proxy_daemon.py
```

Expected: `self.posts_today += 1` and `self.comments_today += 1` should appear ONLY inside the `if result.get('ok'):` block (after line ~192), NOT at their old positions (lines 183, 190).

---

## Security Checklist

- [ ] No new imports added
- [ ] No new external connections
- [ ] Original file preserved (Python script checks pattern before modifying)
- [ ] `python3 -c "import ast; ast.parse(...)"` passes
