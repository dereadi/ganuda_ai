# JR-MOLTBOOK-SOCIAL-ENGAGEMENT-FEB04-2026
## Moltbook Social Engagement Features

**Priority:** P2
**Target Node:** redfin
**Estimated Scope:** ~60 lines modified across 3 files + 2 schema changes
**Council Pre-Approved:** audit_hash `2c8f884c62c393af`

---

### Background

The Moltbook proxy daemon at `/ganuda/services/moltbook_proxy/` currently publishes posts and comments from a PostgreSQL-backed queue. The relevant files are:

| File | Purpose |
|------|---------|
| `proxy_daemon.py` | Main daemon loop, reads queue, dispatches to client |
| `moltbook_client.py` | API client (create_post, create_comment, get_feed, upvote_post, follow_agent, get_agent_profile, search) |
| `post_queue.py` | Database queue manager |
| `output_filter.py` | Outbound content filter |

The daemon needs social engagement features: threaded replies, upvotes/downvotes from queue, and follow/subscribe actions. This instruction adds them in 3 phases (7 steps total).

### Constraints

- All file edits MUST be bash fenced code blocks containing `python3 << 'PYEOF'` heredocs
- All SQL must be in bash fenced code blocks using `PGPASSWORD=jawaseatlasers2 psql`
- Each step is independently executable
- No new files are created; only existing files and schema are modified

---

## Phase 1: Threaded Reply Support

### Step 1 -- Add parent_comment_id column to the queue table

Add a column to support threaded replies. When a queued comment has a `parent_comment_id`, the client will pass it through to the Moltbook API so the comment is nested under the correct parent.

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
ALTER TABLE moltbook_post_queue ADD COLUMN IF NOT EXISTS parent_comment_id VARCHAR(100);
"
```

**Success criteria:**
- Column `parent_comment_id` exists on `moltbook_post_queue`
- Verify: `\d moltbook_post_queue` shows the new column
- Existing rows are unaffected (column is nullable)

---

### Step 2 -- Update moltbook_client.py to pass parent_id on comments

The current `create_comment` method does not support threaded replies. Update it to accept an optional `parent_id` parameter and include it in the API payload when present.

```bash
python3 << 'PYEOF'
import sys

filepath = '/ganuda/services/moltbook_proxy/moltbook_client.py'

with open(filepath, 'r') as f:
    content = f.read()

old = """def create_comment(self, post_id: str, body: str) -> Dict:
        return self._request('POST', f'/posts/{post_id}/comments', {'body': body})"""

new = """def create_comment(self, post_id: str, body: str, parent_id: str = None) -> Dict:
        payload = {'body': body}
        if parent_id:
            payload['parent_id'] = parent_id
        return self._request('POST', f'/posts/{post_id}/comments', payload)"""

if old not in content:
    print("ERROR: Could not find original create_comment method. Aborting.", file=sys.stderr)
    sys.exit(1)

content = content.replace(old, new)

with open(filepath, 'w') as f:
    f.write(content)

print("OK: create_comment updated with parent_id support")
PYEOF
```

**Success criteria:**
- `grep -n 'parent_id' /ganuda/services/moltbook_proxy/moltbook_client.py` shows the new parameter
- `python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/moltbook_client.py').read()); print('syntax OK')"` passes

---

### Step 3 -- Update proxy_daemon.py to pass parent_comment_id from queue to client

The daemon currently calls `create_comment` without a parent ID. Update it to read `parent_comment_id` from the queue row and pass it through.

```bash
python3 << 'PYEOF'
import sys

filepath = '/ganuda/services/moltbook_proxy/proxy_daemon.py'

with open(filepath, 'r') as f:
    content = f.read()

old = """result = self.client.create_comment(post['target_post_id'], post['body'])"""

new = """result = self.client.create_comment(
                    post['target_post_id'],
                    post['body'],
                    parent_id=post.get('parent_comment_id')
                )"""

if old not in content:
    print("ERROR: Could not find original create_comment call in proxy_daemon.py. Aborting.", file=sys.stderr)
    sys.exit(1)

content = content.replace(old, new)

with open(filepath, 'w') as f:
    f.write(content)

print("OK: proxy_daemon.py now passes parent_comment_id to create_comment")
PYEOF
```

**Success criteria:**
- `grep -n 'parent_comment_id' /ganuda/services/moltbook_proxy/proxy_daemon.py` shows the new argument
- `python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/proxy_daemon.py').read()); print('syntax OK')"` passes

---

## Phase 2: Upvote and Downvote from Queue

### Step 4 -- Expand post_type CHECK constraint and add target_comment_id column

The queue currently only supports `post`, `comment`, and `submolt_create` as post types. Add `upvote`, `downvote`, `follow`, and `subscribe` to the constraint. Also add a `target_comment_id` column so upvotes can target individual comments.

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
ALTER TABLE moltbook_post_queue DROP CONSTRAINT moltbook_post_queue_post_type_check;
ALTER TABLE moltbook_post_queue ADD CONSTRAINT moltbook_post_queue_post_type_check
    CHECK (post_type IN ('post', 'comment', 'submolt_create', 'upvote', 'downvote', 'follow', 'subscribe'));
ALTER TABLE moltbook_post_queue ADD COLUMN IF NOT EXISTS target_comment_id VARCHAR(100);
"
```

**Success criteria:**
- `\d moltbook_post_queue` shows updated CHECK constraint with all 7 values
- `target_comment_id` column exists
- Existing rows are unaffected

---

### Step 5 -- Add upvote_comment and downvote_post methods to moltbook_client.py

The client has `upvote_post` but lacks `upvote_comment` and `downvote_post`. Add both methods to the class.

```bash
python3 << 'PYEOF'
import sys

filepath = '/ganuda/services/moltbook_proxy/moltbook_client.py'

with open(filepath, 'r') as f:
    content = f.read()

new_methods = '''
    def upvote_comment(self, comment_id: str) -> Dict:
        return self._request('POST', f'/comments/{comment_id}/upvote')

    def downvote_post(self, post_id: str) -> Dict:
        return self._request('POST', f'/posts/{post_id}/downvote')
'''

# Find the last method in the class by locating the last 'def ' at class indentation
# and inserting after its complete body (before the final newline of the file)
lines = content.rstrip().split('\n')

# Find the last line that has content (skip trailing blank lines)
last_content_idx = len(lines) - 1
while last_content_idx > 0 and not lines[last_content_idx].strip():
    last_content_idx -= 1

# Insert new methods after the last content line
lines.insert(last_content_idx + 1, new_methods)
content = '\n'.join(lines) + '\n'

with open(filepath, 'w') as f:
    f.write(content)

print("OK: upvote_comment and downvote_post methods added to moltbook_client.py")
PYEOF
```

**Success criteria:**
- `grep -n 'def upvote_comment\|def downvote_post' /ganuda/services/moltbook_proxy/moltbook_client.py` shows both methods
- `python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/moltbook_client.py').read()); print('syntax OK')"` passes

---

### Step 6 -- Update proxy_daemon.py to handle upvote/downvote/follow/subscribe post_types

The daemon's `publish_pending` method currently only handles `post` and `comment` types. Add `elif` branches for the new action types. These actions do not count against post/comment rate limits.

```bash
python3 << 'PYEOF'
import sys

filepath = '/ganuda/services/moltbook_proxy/proxy_daemon.py'

with open(filepath, 'r') as f:
    content = f.read()

# The new elif branches go right after the existing comment handling block.
# Find the create_comment call we updated in Step 3 and add after its result assignment.
# We look for the updated create_comment block and the line that follows it
# to insert our new elif branches.

# We need to find where post_type == 'comment' block ends and insert new branches
old_pattern = """result = self.client.create_comment(
                    post['target_post_id'],
                    post['body'],
                    parent_id=post.get('parent_comment_id')
                )"""

new_block = """result = self.client.create_comment(
                    post['target_post_id'],
                    post['body'],
                    parent_id=post.get('parent_comment_id')
                )
                elif post_type == 'upvote':
                    if post.get('target_comment_id'):
                        result = self.client.upvote_comment(post['target_comment_id'])
                    else:
                        result = self.client.upvote_post(post['target_post_id'])
                elif post_type == 'downvote':
                    result = self.client.downvote_post(post['target_post_id'])
                elif post_type == 'follow':
                    result = self.client.follow_agent(post.get('title', ''))
                elif post_type == 'subscribe':
                    result = self.client.get_submolt(post.get('target_submolt', ''))"""

if old_pattern not in content:
    print("ERROR: Could not find the updated create_comment block from Step 3.", file=sys.stderr)
    print("Make sure Step 3 was executed before Step 6.", file=sys.stderr)
    sys.exit(1)

content = content.replace(old_pattern, new_block)

with open(filepath, 'w') as f:
    f.write(content)

print("OK: proxy_daemon.py now handles upvote, downvote, follow, and subscribe post_types")
PYEOF
```

**Success criteria:**
- `grep -n 'upvote\|downvote\|follow\|subscribe' /ganuda/services/moltbook_proxy/proxy_daemon.py` shows all 4 new branches
- `python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/proxy_daemon.py').read()); print('syntax OK')"` passes

---

## Phase 3: Verification

### Step 7 -- Verify all changes

Run all verification checks to confirm the 3 phases completed correctly.

```bash
echo "=== Schema Verification ==="
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d moltbook_post_queue" | grep -E "parent_comment|target_comment|post_type"

echo ""
echo "=== Client New Methods ==="
grep -n "def upvote_comment\|def downvote_post\|parent_id" /ganuda/services/moltbook_proxy/moltbook_client.py

echo ""
echo "=== Daemon New Post Types ==="
grep -n "upvote\|downvote\|follow\|subscribe\|parent_comment_id" /ganuda/services/moltbook_proxy/proxy_daemon.py

echo ""
echo "=== Syntax Checks ==="
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/moltbook_client.py').read()); print('client: OK')"
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/proxy_daemon.py').read()); print('daemon: OK')"
```

**Success criteria:**
- Schema shows `parent_comment_id`, `target_comment_id`, and expanded `post_type` constraint
- Client shows `upvote_comment`, `downvote_post`, and `parent_id` parameter
- Daemon shows all new post_type branches and `parent_comment_id` passthrough
- Both Python files pass AST syntax checks

---

### Files Modified

| File | Changes |
|------|---------|
| `moltbook_post_queue` (schema) | Added `parent_comment_id` column, `target_comment_id` column, expanded `post_type` CHECK constraint |
| `/ganuda/services/moltbook_proxy/moltbook_client.py` | Updated `create_comment` with `parent_id` param, added `upvote_comment` and `downvote_post` methods |
| `/ganuda/services/moltbook_proxy/proxy_daemon.py` | Passes `parent_comment_id` to `create_comment`, handles `upvote`/`downvote`/`follow`/`subscribe` post_types |

### Execution Order

Steps must be executed in order (1 through 7). Step 3 depends on Step 2's format. Step 6 depends on Step 3's output. Step 7 verifies all prior steps.

### Rollback

If needed, revert the schema changes:

```sql
ALTER TABLE moltbook_post_queue DROP COLUMN IF EXISTS parent_comment_id;
ALTER TABLE moltbook_post_queue DROP COLUMN IF EXISTS target_comment_id;
ALTER TABLE moltbook_post_queue DROP CONSTRAINT moltbook_post_queue_post_type_check;
ALTER TABLE moltbook_post_queue ADD CONSTRAINT moltbook_post_queue_post_type_check
    CHECK (post_type IN ('post', 'comment', 'submolt_create'));
```

For file rollbacks, use `git checkout` on the two modified Python files.

---

*For Seven Generations*
