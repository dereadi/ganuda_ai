# JR-MOLTBOOK-COMMENT-GATING-FIX-FEB04-2026

**Priority:** P1
**Assigned:** Jr Engineer
**Created:** 2026-02-04
**Council Vote:** 7/7 APPROVE

---

## Summary

The Moltbook proxy daemon's `_publish_approved_posts()` method gates ALL queue processing behind a single `posts_today >= POSTS_PER_DAY` check. This means once the daily post limit is reached, comments are also blocked from publishing -- even though comments have their own separate counter (`comments_today`) and limit (`COMMENTS_PER_DAY`). Posts and comments must be rate-limited independently.

## Root Cause

In `/ganuda/services/moltbook_proxy/proxy_daemon.py` around line 155:

```python
def _publish_approved_posts(self):
    if self.posts_today >= POSTS_PER_DAY:
        return  # blocks comments too
```

The early return fires when the post limit is hit, preventing any further processing of the approved queue -- including comments that have not reached their own limit. The `get_approved_posts()` function in `post_queue.py` also lacks a `post_type` filter, so there is no way to selectively fetch only comments or only posts.

## Files Modified

1. `/ganuda/services/moltbook_proxy/proxy_daemon.py` -- split gating logic in `_publish_approved_posts()`
2. `/ganuda/services/moltbook_proxy/post_queue.py` -- add optional `post_type` filter to `get_approved_posts()`

## Fix

```bash
python3 << 'PYTHON_SCRIPT'
import re
import sys
import shutil
from datetime import datetime

DAEMON_PATH = "/ganuda/services/moltbook_proxy/proxy_daemon.py"
QUEUE_PATH = "/ganuda/services/moltbook_proxy/post_queue.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ============================================================
# STEP 1: Patch post_queue.py - add post_type filter parameter
# ============================================================

shutil.copy2(QUEUE_PATH, f"{QUEUE_PATH}.bak.{timestamp}")

with open(QUEUE_PATH, "r") as f:
    queue_content = f.read()

# Find the get_approved_posts function definition and replace it
# to accept an optional post_type parameter.

old_def_pattern = re.compile(
    r'(def get_approved_posts\()(\s*\))',
    re.DOTALL
)

if old_def_pattern.search(queue_content):
    # Case: no existing parameters besides self (module-level function)
    queue_content = old_def_pattern.sub(
        r'\1post_type=None)',
        queue_content
    )
elif 'def get_approved_posts(self)' in queue_content:
    queue_content = queue_content.replace(
        'def get_approved_posts(self)',
        'def get_approved_posts(self, post_type=None)'
    )
elif 'def get_approved_posts(self,' in queue_content:
    queue_content = queue_content.replace(
        'def get_approved_posts(self,',
        'def get_approved_posts(self, post_type=None,'
    )
else:
    print("ERROR: Could not locate get_approved_posts() signature in post_queue.py")
    sys.exit(1)

# Now inject the post_type filter into the SQL query inside the function.
# We look for the WHERE clause that filters on approval status and append
# an optional AND condition for post_type.

# Find the query string that selects approved posts.
# Expected pattern: WHERE ... approved/status ... ORDER BY
query_injection = '''
        # -- BEGIN COMMENT-GATING FIX (JR-MOLTBOOK-COMMENT-GATING-FIX-FEB04-2026) --
        type_filter = ""
        type_params = ()
        if post_type is not None:
            type_filter = " AND post_type = %s"
            type_params = (post_type,)
        # -- END COMMENT-GATING FIX --
'''

# Insert the filter-building block right before the cursor.execute / query execution.
# We look for the pattern: cursor.execute( or db.execute( or conn.execute(
exec_pattern = re.compile(r'(\n)([ \t]*)(cursor\.execute|db\.execute|conn\.execute)\(')
match = exec_pattern.search(queue_content, queue_content.index('get_approved_posts'))

if match:
    insert_pos = match.start()
    indent = match.group(2)
    # Adjust indentation of injected block
    adjusted_injection = query_injection.replace('\n        ', '\n' + indent)
    queue_content = queue_content[:insert_pos] + adjusted_injection + queue_content[insert_pos:]

    # Now patch the SQL string to include the type_filter placeholder.
    # Find the SQL query string within get_approved_posts that has ORDER BY
    # and inject + type_filter before the ORDER BY.
    # We replace the execute call to append type_params to existing params.

    # Strategy: find the query variable or inline SQL and add type_filter.
    # Look for pattern like: "... WHERE status = 'approved'" or similar,
    # followed by ORDER BY. We insert the filter between them.

    # Find ORDER BY in the SQL near the execute call
    func_start = queue_content.index('get_approved_posts')
    # Find the next function def or end-of-file to scope our search
    next_def = queue_content.find('\ndef ', func_start + 1)
    if next_def == -1:
        next_def = len(queue_content)
    func_body = queue_content[func_start:next_def]

    # Replace ORDER BY with type_filter injection in the SQL string
    order_pattern = re.compile(r"""(['"].*?)(ORDER\s+BY)""", re.DOTALL | re.IGNORECASE)
    if 'ORDER BY' in func_body or 'order by' in func_body:
        # Find the SQL string containing ORDER BY and inject type_filter before it
        # using f-string or string concatenation
        queue_content = queue_content[:func_start] + re.sub(
            r"""(['"])(.*?)(ORDER\s+BY)""",
            r"""\1\2" + type_filter + " \3""",
            func_body,
            count=1,
            flags=re.DOTALL | re.IGNORECASE
        ) + queue_content[next_def:]

    # Patch execute call to include type_params in the parameter tuple
    # Find the execute call within the function scope and append type_params
    func_start = queue_content.index('get_approved_posts')
    next_def = queue_content.find('\ndef ', func_start + 1)
    if next_def == -1:
        next_def = len(queue_content)
    func_body = queue_content[func_start:next_def]

    # Add + type_params to the params argument of the execute call
    exec_call_pattern = re.compile(
        r'(execute\([^,]+,\s*\()([^)]*)\)(\s*\))',
        re.DOTALL
    )
    exec_match = exec_call_pattern.search(func_body)
    if exec_match:
        patched_func = func_body[:exec_match.start()] + \
            exec_match.group(0).replace(
                exec_match.group(3),
                ' + type_params)'
            ) + func_body[exec_match.end():]
        queue_content = queue_content[:func_start] + patched_func + queue_content[next_def:]
else:
    print("WARNING: Could not locate execute() call in get_approved_posts().")
    print("         Manual injection of post_type filter into SQL query required.")

with open(QUEUE_PATH, "w") as f:
    f.write(queue_content)

print(f"PATCHED: {QUEUE_PATH}")
print(f"  Backup: {QUEUE_PATH}.bak.{timestamp}")

# ============================================================
# STEP 2: Patch proxy_daemon.py - split gating logic
# ============================================================

shutil.copy2(DAEMON_PATH, f"{DAEMON_PATH}.bak.{timestamp}")

with open(DAEMON_PATH, "r") as f:
    daemon_content = f.read()

# Find the _publish_approved_posts method and replace the gating block.
# Original pattern:
#     def _publish_approved_posts(self):
#         if self.posts_today >= POSTS_PER_DAY:
#             return
#
# Replacement: independent rate limiting for posts vs comments.

old_gating_pattern = re.compile(
    r'(def _publish_approved_posts\(self\):\s*\n)'
    r'(\s+)(if\s+self\.posts_today\s*>=\s*POSTS_PER_DAY:\s*\n)'
    r'(\s+return[^\n]*\n)',
    re.MULTILINE
)

match = old_gating_pattern.search(daemon_content)
if not match:
    print("ERROR: Could not locate the original gating pattern in proxy_daemon.py")
    print("       Expected: if self.posts_today >= POSTS_PER_DAY: return")
    sys.exit(1)

indent = match.group(2)  # capture the indentation level

new_gating = (
    f'{match.group(1)}'
    f'{indent}# -- BEGIN COMMENT-GATING FIX (JR-MOLTBOOK-COMMENT-GATING-FIX-FEB04-2026) --\n'
    f'{indent}posts_exhausted = self.posts_today >= POSTS_PER_DAY\n'
    f'{indent}comments_exhausted = self.comments_today >= COMMENTS_PER_DAY\n'
    f'\n'
    f'{indent}if posts_exhausted and comments_exhausted:\n'
    f'{indent}    return  # both limits reached, nothing to publish\n'
    f'\n'
    f'{indent}# Determine which types we can still publish\n'
    f'{indent}if posts_exhausted:\n'
    f'{indent}    post_type_filter = "comment"  # only comments have capacity\n'
    f'{indent}elif comments_exhausted:\n'
    f'{indent}    post_type_filter = "post"  # only posts have capacity\n'
    f'{indent}else:\n'
    f'{indent}    post_type_filter = None  # both have capacity\n'
    f'{indent}# -- END COMMENT-GATING FIX --\n'
)

daemon_content = daemon_content[:match.start()] + new_gating + daemon_content[match.end():]

# Now find the call to get_approved_posts() within _publish_approved_posts
# and pass the post_type_filter argument.
func_start = daemon_content.index('_publish_approved_posts')
next_def = daemon_content.find('\n    def ', func_start + 1)
if next_def == -1:
    next_def = len(daemon_content)

func_body = daemon_content[func_start:next_def]

# Replace get_approved_posts() with get_approved_posts(post_type=post_type_filter)
if 'get_approved_posts()' in func_body:
    patched_body = func_body.replace(
        'get_approved_posts()',
        'get_approved_posts(post_type=post_type_filter)',
        1
    )
    daemon_content = daemon_content[:func_start] + patched_body + daemon_content[next_def:]
elif 'get_approved_posts(self)' in func_body:
    # If it is a method call on self
    pass  # self.queue.get_approved_posts() pattern handled below

# Also handle self.queue.get_approved_posts() or self.post_queue.get_approved_posts()
for attr in ['queue', 'post_queue', '_queue', '_post_queue']:
    old_call = f'self.{attr}.get_approved_posts()'
    new_call = f'self.{attr}.get_approved_posts(post_type=post_type_filter)'
    if old_call in daemon_content:
        # Only replace within _publish_approved_posts scope
        func_start = daemon_content.index('_publish_approved_posts')
        next_def_idx = daemon_content.find('\n    def ', func_start + 1)
        if next_def_idx == -1:
            next_def_idx = len(daemon_content)
        before = daemon_content[:func_start]
        scope = daemon_content[func_start:next_def_idx]
        after = daemon_content[next_def_idx:]
        scope = scope.replace(old_call, new_call, 1)
        daemon_content = before + scope + after
        break

with open(DAEMON_PATH, "w") as f:
    f.write(daemon_content)

print(f"PATCHED: {DAEMON_PATH}")
print(f"  Backup: {DAEMON_PATH}.bak.{timestamp}")

print()
print("DONE: Comment gating fix applied.")
print("  - post_queue.py: get_approved_posts() now accepts post_type filter")
print("  - proxy_daemon.py: posts and comments are rate-limited independently")
PYTHON_SCRIPT
```

## Verification

After applying the fix, verify with the following checks:

1. **Unit check -- comments publish when posts exhausted:**
   ```
   # In a Python shell or test script:
   daemon.posts_today = 4   # at or above POSTS_PER_DAY
   daemon.comments_today = 0
   daemon._publish_approved_posts()
   # Expected: comments are fetched and published; posts are skipped
   ```

2. **Unit check -- posts publish when comments exhausted:**
   ```
   daemon.posts_today = 0
   daemon.comments_today = COMMENTS_PER_DAY
   daemon._publish_approved_posts()
   # Expected: posts are fetched and published; comments are skipped
   ```

3. **Unit check -- nothing publishes when both exhausted:**
   ```
   daemon.posts_today = POSTS_PER_DAY
   daemon.comments_today = COMMENTS_PER_DAY
   daemon._publish_approved_posts()
   # Expected: early return, no queue fetch
   ```

4. **Query filter check:**
   ```
   # Confirm get_approved_posts(post_type="comment") appends
   # AND post_type = 'comment' to the SQL WHERE clause
   ```

5. **Tail the daemon log after deploy:**
   ```bash
   journalctl -u moltbook-proxy -f --since "5 min ago"
   # Look for comment publish events when posts_today shows >= 4
   ```

## Rollback

Backups are created automatically with timestamp suffixes:
```bash
# Restore if needed:
cp /ganuda/services/moltbook_proxy/proxy_daemon.py.bak.<timestamp> \
   /ganuda/services/moltbook_proxy/proxy_daemon.py
cp /ganuda/services/moltbook_proxy/post_queue.py.bak.<timestamp> \
   /ganuda/services/moltbook_proxy/post_queue.py
sudo systemctl restart moltbook-proxy
```
