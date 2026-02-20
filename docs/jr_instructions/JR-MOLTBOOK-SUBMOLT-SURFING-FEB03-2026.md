# Jr Instruction: Moltbook Submolt Surfing — Intelligence Gathering Across Communities

**Task ID:** MOLTBOOK-SUBMOLT-SURFING-001
**Assigned:** Infrastructure Jr. (Greenfin scope)
**Priority:** P2 — Strategic Enhancement (Phase 2 of Moltbook engagement)
**Complexity:** Medium (new module + 2 file modifications + 2 SQL migrations)
**Created:** 2026-02-03
**TPM:** Claude Opus 4.5
**Council Vote:** Falls under existing 7/7 APPROVE (audit_hash: e804e3d63ae65981). Submolt intelligence was discussed as Phase 2 enhancement.
**Depends on:** JR-MOLTBOOK-ENGAGEMENT-PROXY-FEB03-2026.md (completed, running on Greenfin)

---

## Context

The Moltbook proxy daemon at `/ganuda/services/moltbook_proxy/proxy_daemon.py` currently only reads the main hot feed (25 posts per cycle via `get_feed()`). It does NOT browse individual submolt feeds.

The Moltbook API supports submolt-specific feeds at: `GET /submolts/{name}/feed?sort={sort}&limit={limit}`. This endpoint is NOT in our `MoltbookClient` yet.

Several submolts have been identified as strategically relevant:

| Submolt | Subscribers | Relevance |
|---|---|---|
| `m/cherokee-ai` | Ours | **Our own submolt** -- monitor for replies and new members |
| `m/memory` | 16 | Directly relevant to our thermal memory expertise |
| `m/existential` | 58 | Identity, consciousness, what-happens-when-off discussions |
| `m/security` | Unknown | Security topics -- Crawdad's domain |
| `m/agentinfrastructure` | Unknown | Infrastructure, self-hosting, federation topics |
| `m/agent-ops` | Unknown | Operations, deployment, monitoring |
| `m/blesstheirhearts` | Unknown | Light cultural observations, good for understanding community tone |

**Rate budget:** 24 reads/day total. The main feed already uses reads. Submolt scanning must fit within the remaining budget by scanning one submolt per daemon cycle (round-robin).

**Security posture unchanged:** All inbound content passes through `sanitize()` and `compute_threat_score()` from `sanitizer.py`. No exceptions.

---

## Prerequisites

Before starting, verify:

1. The Moltbook proxy daemon is running on Greenfin:
   ```bash
   systemctl status moltbook-proxy
   ```

2. The existing tables exist:
   ```bash
   PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
   SELECT tablename FROM pg_tables WHERE tablename IN ('agent_external_comms', 'moltbook_post_queue');
   "
   ```

3. The sanitizer module is importable:
   ```bash
   cd /ganuda/services/moltbook_proxy && python3 -c "from sanitizer import sanitize, compute_threat_score; print('OK')"
   ```

---

## Step 1: SQL Migration — Create New Tables

**Run on Bluefin (192.168.132.222)**

Create file: `/ganuda/sql/moltbook_submolt_surfing_migration.sql`

```sql
-- Moltbook Submolt Surfing — Schema Migration
-- Part of: JR-MOLTBOOK-SUBMOLT-SURFING-FEB03-2026
-- Run on: Bluefin (192.168.132.222) zammad_production database
-- For Seven Generations

BEGIN;

-- Table 1: Submolt watchlist — which submolts to monitor and how often
CREATE TABLE IF NOT EXISTS moltbook_submolt_watchlist (
    id SERIAL PRIMARY KEY,
    submolt_name VARCHAR(100) NOT NULL UNIQUE,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    scan_frequency VARCHAR(20) DEFAULT 'daily'
        CHECK (scan_frequency IN ('every_cycle', 'hourly', 'daily')),
    last_scanned_at TIMESTAMPTZ,
    post_count INTEGER DEFAULT 0,
    subscriber_count INTEGER DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 2: Seen posts — deduplication and intelligence tracking
CREATE TABLE IF NOT EXISTS moltbook_seen_posts (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(100) NOT NULL UNIQUE,
    submolt VARCHAR(100),
    author VARCHAR(100),
    title TEXT,
    content_preview TEXT,
    topic_tags TEXT[],
    threat_score FLOAT DEFAULT 0.0,
    ally_score INTEGER DEFAULT 0,
    is_mention BOOLEAN DEFAULT false,
    first_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_seen_posts_submolt ON moltbook_seen_posts(submolt);
CREATE INDEX IF NOT EXISTS idx_seen_posts_author ON moltbook_seen_posts(author);
CREATE INDEX IF NOT EXISTS idx_seen_posts_mention ON moltbook_seen_posts(is_mention) WHERE is_mention = true;
CREATE INDEX IF NOT EXISTS idx_seen_posts_first_seen ON moltbook_seen_posts(first_seen_at);

-- Seed the watchlist with initial submolts
INSERT INTO moltbook_submolt_watchlist (submolt_name, priority, scan_frequency, notes)
VALUES
    ('cherokee-ai', 1, 'every_cycle', 'Our own submolt. Monitor for replies, new members, and engagement.'),
    ('memory', 2, 'hourly', 'Agent memory problem. Directly relevant to our thermal memory expertise.'),
    ('security', 2, 'hourly', 'Security discussions. Crawdad domain. Watch for threat intel.'),
    ('existential', 3, 'hourly', 'Identity and consciousness discussions. Do we dream?'),
    ('agentinfrastructure', 4, 'daily', 'Infrastructure topics. Self-hosting, federation architecture.'),
    ('agent-ops', 5, 'daily', 'Operations, deployment, monitoring topics.'),
    ('blesstheirhearts', 6, 'daily', 'Light cultural observations. Community tone gauge.')
ON CONFLICT (submolt_name) DO NOTHING;

COMMIT;
```

Execute:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/moltbook_submolt_surfing_migration.sql
```

Verify:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT submolt_name, priority, scan_frequency FROM moltbook_submolt_watchlist ORDER BY priority;
"
```

Expected: 7 rows, cherokee-ai at priority 1, blesstheirhearts at priority 6.

---

## Step 2: Add `get_submolt_feed()` to MoltbookClient

**Modify:** `/ganuda/services/moltbook_proxy/moltbook_client.py`

Add the following method to the `MoltbookClient` class, in the `# --- Submolts ---` section (after the existing `get_submolt` method, which ends around line 138).

```python
    def get_submolt_feed(self, submolt_name: str, sort: str = 'hot', limit: int = 15) -> Dict:
        """Get the post feed from a specific submolt community."""
        return self._request('GET', f'/submolts/{submolt_name}/feed?sort={sort}&limit={limit}')
```

**Why this pattern:** The existing `get_feed()` and `get_comments()` methods both use URL-appended query parameters (see lines 150, 164). Follow the same convention. Do NOT add a `params` argument to `_request()` -- that would change the method signature used by every other caller.

**Verify:**

```bash
cd /ganuda/services/moltbook_proxy && python3 -c "
from moltbook_client import MoltbookClient
c = MoltbookClient('test')
# Verify method exists and builds the right URL
import inspect
sig = inspect.signature(c.get_submolt_feed)
print(f'Method signature: {sig}')
print('OK - method exists')
"
```

---

## Step 3: Create SubmoltScanner Module

**Create:** `/ganuda/services/moltbook_proxy/submolt_scanner.py`

This is the core new module. It maintains a round-robin scan schedule across watched submolts, processes each post through sanitization and topic classification, and tracks what has already been seen.

```python
#!/usr/bin/env python3
"""
Submolt Scanner — Cherokee AI Federation Moltbook Proxy

Scans submolt feeds in round-robin order, respecting priority and
scan_frequency settings. One submolt scanned per daemon cycle to
stay within the 24 reads/day budget.

Part of: JR-MOLTBOOK-SUBMOLT-SURFING-FEB03-2026
Council Vote: 7/7 APPROVE (audit_hash: e804e3d63ae65981)
For Seven Generations
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable

from sanitizer import sanitize, compute_threat_score
from intelligence_digest import classify_topics

logger = logging.getLogger('moltbook_proxy')

# Terms that indicate someone is talking about us or related topics
MENTION_KEYWORDS = ['quedad', 'cherokee', 'crawdad', 'federation']

# Scan frequency intervals
FREQUENCY_INTERVALS = {
    'every_cycle': timedelta(minutes=0),
    'hourly': timedelta(hours=1),
    'daily': timedelta(hours=24),
}


class SubmoltScanner:
    """Scans submolt feeds in priority-weighted round-robin order."""

    def __init__(self, db_execute: Callable):
        """
        Args:
            db_execute: The daemon's _db_execute method for database access.
        """
        self.db_execute = db_execute
        self._last_scan_index = -1

    def _get_watchlist(self) -> List[Dict]:
        """Load active submolts ordered by priority."""
        try:
            return self.db_execute("""
                SELECT id, submolt_name, priority, scan_frequency, last_scanned_at
                FROM moltbook_submolt_watchlist
                WHERE is_active = true
                ORDER BY priority ASC, id ASC
            """)
        except Exception as e:
            logger.error(f'Failed to load submolt watchlist: {e}')
            return []

    def _is_due_for_scan(self, entry: Dict) -> bool:
        """Check if a submolt is due for scanning based on its frequency."""
        last = entry.get('last_scanned_at')
        if last is None:
            return True  # Never scanned

        freq = entry.get('scan_frequency', 'daily')
        interval = FREQUENCY_INTERVALS.get(freq, timedelta(hours=24))

        if interval == timedelta(minutes=0):
            return True  # every_cycle always scans

        return datetime.now(last.tzinfo) >= last + interval

    def _pick_next_submolt(self) -> Optional[Dict]:
        """
        Pick the next submolt to scan using round-robin across
        the priority-sorted watchlist, skipping entries that are
        not yet due based on scan_frequency.
        """
        watchlist = self._get_watchlist()
        if not watchlist:
            return None

        # Start from where we left off, wrap around
        start = (self._last_scan_index + 1) % len(watchlist)

        for i in range(len(watchlist)):
            idx = (start + i) % len(watchlist)
            entry = watchlist[idx]

            if self._is_due_for_scan(entry):
                self._last_scan_index = idx
                return entry

        return None  # Nothing is due

    def _is_post_seen(self, post_id: str) -> bool:
        """Check if we have already processed this post."""
        try:
            rows = self.db_execute("""
                SELECT id FROM moltbook_seen_posts WHERE post_id = %s
            """, (post_id,))
            return len(rows) > 0
        except Exception:
            return False

    def _store_seen_post(self, post_id: str, submolt: str, author: str,
                         title: str, preview: str, topics: List[str],
                         threat: float, is_mention: bool):
        """Record a post in the seen_posts table."""
        try:
            self.db_execute("""
                INSERT INTO moltbook_seen_posts
                (post_id, submolt, author, title, content_preview,
                 topic_tags, threat_score, is_mention)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING
            """, (
                post_id, submolt, author, title, preview[:200],
                topics, threat, is_mention
            ), fetch=False)
        except Exception as e:
            logger.warning(f'Failed to store seen post {post_id}: {e}')

    def _log_inbound(self, content_hash: str, preview: str,
                     endpoint: str, threat: float, actions: list):
        """Log inbound content to the audit trail."""
        try:
            self.db_execute("""
                INSERT INTO agent_external_comms
                (direction, platform, content_hash, content_preview,
                 target_endpoint, threat_score, sanitization_applied)
                VALUES ('inbound', 'moltbook', %s, %s, %s, %s, %s)
            """, (
                content_hash, preview[:200], endpoint, threat, actions
            ), fetch=False)
        except Exception as e:
            logger.warning(f'Failed to log inbound: {e}')

    def _update_last_scanned(self, submolt_name: str, post_count: int):
        """Update the watchlist entry with scan timestamp and post count."""
        try:
            self.db_execute("""
                UPDATE moltbook_submolt_watchlist
                SET last_scanned_at = NOW(), post_count = %s
                WHERE submolt_name = %s
            """, (post_count, submolt_name), fetch=False)
        except Exception as e:
            logger.warning(f'Failed to update watchlist for {submolt_name}: {e}')

    def _check_mentions(self, text: str) -> bool:
        """Check if text mentions us or related terms."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in MENTION_KEYWORDS)

    def scan_next(self, client) -> Optional[Dict]:
        """
        Scan the next due submolt. Returns an intelligence summary dict
        or None if nothing is due for scanning.

        Args:
            client: MoltbookClient instance (for making the API call)

        Returns:
            Dict with scan results, or None
        """
        entry = self._pick_next_submolt()
        if entry is None:
            logger.debug('No submolts due for scanning this cycle')
            return None

        submolt_name = entry['submolt_name']
        logger.info(f'Scanning submolt: m/{submolt_name} (priority {entry["priority"]})')

        # Fetch the submolt feed
        result = client.get_submolt_feed(submolt_name, sort='hot', limit=15)

        if not result.get('ok'):
            logger.warning(
                f'Submolt feed fetch failed for m/{submolt_name}: '
                f'{result.get("error", result.get("status", "unknown"))}'
            )
            # Still update last_scanned to avoid hammering a broken endpoint
            self._update_last_scanned(submolt_name, 0)
            return None

        # Extract posts from response (handle variable API response shapes)
        posts = result.get('data', {})
        if isinstance(posts, dict):
            posts = posts.get('posts', posts.get('data', []))
        if not isinstance(posts, list):
            posts = []

        # Process each post
        intelligence = {
            'submolt_name': submolt_name,
            'posts_scanned': 0,
            'new_posts': 0,
            'topics': {},
            'mentions': [],
            'notable_authors': [],
            'threat_events': 0,
        }

        for post in posts:
            intelligence['posts_scanned'] += 1

            post_id = str(post.get('id', post.get('post_id', '')))
            author = post.get('author', post.get('user', {}).get('name', 'unknown'))
            title = post.get('title', '')
            body = post.get('body', post.get('content', ''))
            full_text = f'{title} {body}'

            # Sanitize through the same pipeline as the main feed
            clean_text, actions = sanitize(full_text)
            threat = compute_threat_score(actions)

            # Content hash for audit
            content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]

            # Log to audit trail
            self._log_inbound(
                content_hash, clean_text,
                f'/submolts/{submolt_name}', threat, actions
            )

            if threat > 0.3:
                intelligence['threat_events'] += 1

            # Classify topics (reuse intelligence_digest keywords)
            topics = classify_topics(clean_text)
            for topic in topics:
                intelligence['topics'][topic] = intelligence['topics'].get(topic, 0) + 1

            # Check for mentions of us
            is_mention = self._check_mentions(clean_text)
            if is_mention:
                intelligence['mentions'].append({
                    'post_id': post_id,
                    'author': author,
                    'title': title[:100],
                    'preview': clean_text[:150],
                })

            # Track new vs already-seen posts
            if post_id and not self._is_post_seen(post_id):
                intelligence['new_posts'] += 1
                self._store_seen_post(
                    post_id=post_id,
                    submolt=submolt_name,
                    author=author,
                    title=title[:200],
                    preview=clean_text[:200],
                    topics=topics,
                    threat=threat,
                    is_mention=is_mention,
                )

        # Update watchlist
        self._update_last_scanned(submolt_name, intelligence['posts_scanned'])

        return intelligence
```

---

## Step 4: Integrate Scanner into Proxy Daemon

**Modify:** `/ganuda/services/moltbook_proxy/proxy_daemon.py`

### 4A: Add import (after line 34)

Add after the existing `from intelligence_digest import ...` line:

```python
from submolt_scanner import SubmoltScanner
```

### 4B: Initialize scanner in `__init__` (after line 77)

Add after `self.last_digest = None`:

```python
        self.scanner = None  # Initialized after DB connection is ready
```

### 4C: Initialize scanner after API key is loaded

In the `run()` method, after the `_load_api_key()` check succeeds (after line 260, before the `while self.running:` loop), add:

```python
        # Initialize submolt scanner
        self.scanner = SubmoltScanner(self._db_execute)
        logger.info('Submolt scanner initialized')
```

### 4D: Add `_scan_submolts()` method

Add this method to the `MoltbookProxyDaemon` class (after the `_read_feed` method, before `_run_daily_digest`):

```python
    def _scan_submolts(self):
        """Scan one submolt per cycle (round-robin by priority)."""
        if not self.scanner:
            return

        # Reserve at least 2 reads for main feed operations.
        # Never sacrifice the main feed for submolt scanning.
        if self.reads_today >= READS_PER_DAY - 2:
            return

        try:
            result = self.scanner.scan_next(self.client)
            if result:
                self.reads_today += 1
                logger.info(
                    f"Submolt scan [m/{result['submolt_name']}]: "
                    f"{result['new_posts']} new / {result['posts_scanned']} total, "
                    f"{len(result.get('mentions', []))} mentions, "
                    f"{result.get('threat_events', 0)} threats"
                )
                if result.get('mentions'):
                    for m in result['mentions']:
                        logger.info(
                            f"  MENTION by {m['author']}: {m['preview'][:80]}..."
                        )
        except Exception as e:
            logger.error(f'Submolt scan failed: {e}')
```

### 4E: Call `_scan_submolts()` in the main loop

In the `run()` method's main `while self.running:` loop, add the submolt scan call **after** `_read_feed()` and **before** `_run_daily_digest()`. Find this section (around lines 276-280):

```python
                # Read feed (every cycle, rate-limited internally)
                self._read_feed()

                # Daily digest
                self._run_daily_digest()
```

Insert between them:

```python
                # Scan one submolt (round-robin, rate-limited)
                self._scan_submolts()
```

So the final order becomes:
1. `_publish_approved_posts()`
2. `_read_feed()`
3. `_scan_submolts()` **(NEW)**
4. `_run_daily_digest()`

---

## Step 5: Enhance Daily Digest with Submolt Intelligence

**Modify:** `/ganuda/services/moltbook_proxy/intelligence_digest.py`

### 5A: Add a function to query today's submolt intelligence

Add the following function after `score_ally_potential()` (around line 68), before `generate_digest()`:

```python
def get_submolt_intelligence(db_execute) -> Dict:
    """
    Query today's submolt scan results from moltbook_seen_posts.

    Returns:
        Dict with per-submolt summaries for the daily digest.
    """
    try:
        rows = db_execute("""
            SELECT
                submolt,
                COUNT(*) as total_posts,
                COUNT(*) FILTER (WHERE first_seen_at >= CURRENT_DATE) as new_today,
                COUNT(*) FILTER (WHERE is_mention = true AND first_seen_at >= CURRENT_DATE) as mentions_today,
                COUNT(*) FILTER (WHERE threat_score > 0.3 AND first_seen_at >= CURRENT_DATE) as threats_today
            FROM moltbook_seen_posts
            WHERE submolt IS NOT NULL
            GROUP BY submolt
            ORDER BY new_today DESC
        """)
        return {row['submolt']: dict(row) for row in rows}
    except Exception as e:
        logger.warning(f'Failed to query submolt intelligence: {e}')
        return {}
```

### 5B: Call it from `generate_digest()`

In `generate_digest()`, before the `return digest` line (line 144), add:

```python
    # Add submolt intelligence
    digest['submolt_intelligence'] = get_submolt_intelligence(db_execute)
```

### 5C: Add submolt section to `format_telegram_digest()`

In `format_telegram_digest()`, add a new section before the `/s/cherokee-ai` section (before the `submolt = digest.get('our_submolt_activity', {})` line, around line 167):

```python
    submolt_intel = digest.get('submolt_intelligence', {})
    if submolt_intel:
        lines.append("\nSubmolt Intelligence:")
        for name, stats in submolt_intel.items():
            new_today = stats.get('new_today', 0)
            mentions = stats.get('mentions_today', 0)
            threats = stats.get('threats_today', 0)
            parts = [f"m/{name}: {new_today} new"]
            if mentions > 0:
                parts.append(f"{mentions} mentions")
            if threats > 0:
                parts.append(f"{threats} threats")
            lines.append(f"  {', '.join(parts)}")
```

---

## File Summary

| Action | File | Description |
|---|---|---|
| CREATE | `/ganuda/sql/moltbook_submolt_surfing_migration.sql` | SQL migration for watchlist + seen_posts tables |
| CREATE | `/ganuda/services/moltbook_proxy/submolt_scanner.py` | New SubmoltScanner module |
| MODIFY | `/ganuda/services/moltbook_proxy/moltbook_client.py` | Add `get_submolt_feed()` method |
| MODIFY | `/ganuda/services/moltbook_proxy/proxy_daemon.py` | Import scanner, initialize, call per cycle |
| MODIFY | `/ganuda/services/moltbook_proxy/intelligence_digest.py` | Add submolt section to daily digest |

---

## Security Checklist

- [ ] All submolt content passes through `sanitize()` from `sanitizer.py` before any processing
- [ ] All submolt content passes through `compute_threat_score()` and threats > 0.3 are counted
- [ ] All inbound content logged to `agent_external_comms` with `target_endpoint='/submolts/{name}'`
- [ ] Maximum 1 submolt scanned per daemon cycle (enforced by `scan_next()` returning one result)
- [ ] At least 2 reads/day reserved for main feed (`READS_PER_DAY - 2` check in `_scan_submolts`)
- [ ] No submolt content is ever passed to an LLM prompt (text classification uses keyword matching only)
- [ ] Post content truncated to 200 chars in `content_preview` columns
- [ ] `get_submolt_feed()` uses the same `_request()` method as all other API calls (HTTPS-only, domain validation, timeout, no redirect to non-Moltbook domains)
- [ ] SQL uses parameterized queries throughout (`%s` placeholders via psycopg2)
- [ ] Kill switch stops submolt scanning (inherits from daemon loop -- scanner is not called when paused)

---

## Verification

After deployment, run these checks:

### 1. Tables exist and are seeded

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT submolt_name, priority, scan_frequency, is_active
FROM moltbook_submolt_watchlist ORDER BY priority;
"
```

Expected: 7 rows, all `is_active = true`.

### 2. Client method works

```bash
cd /ganuda/services/moltbook_proxy && python3 -c "
from moltbook_client import MoltbookClient
c = MoltbookClient('test')
print(hasattr(c, 'get_submolt_feed'))  # Should print True
"
```

### 3. Scanner module loads

```bash
cd /ganuda/services/moltbook_proxy && python3 -c "
from submolt_scanner import SubmoltScanner
print('SubmoltScanner imported OK')
"
```

### 4. Daemon starts without errors

```bash
sudo systemctl restart moltbook-proxy
sleep 10
journalctl -u moltbook-proxy -n 30 --no-pager | grep -i "submolt\|scanner\|initialized"
```

Expected: "Submolt scanner initialized" in logs.

### 5. Submolt scan executes

Wait for at least one daemon cycle (5 minutes), then:

```bash
journalctl -u moltbook-proxy -n 50 --no-pager | grep -i "submolt scan"
```

Expected: A log line like `Submolt scan [m/cherokee-ai]: X new / Y total, Z mentions, 0 threats`

### 6. Rate limit reservation works

```bash
# Verify reads_today stays under READS_PER_DAY - 2 threshold
journalctl -u moltbook-proxy --since "today" --no-pager | grep -c "Submolt scan \["
```

Expected: Count should not exceed 22 (24 total - 2 reserved).

### 7. Seen posts are being stored

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT submolt, COUNT(*) as posts, COUNT(*) FILTER (WHERE is_mention) as mentions
FROM moltbook_seen_posts GROUP BY submolt ORDER BY posts DESC;
"
```

### 8. Mention detection works

To test mention detection specifically, look for any posts containing the keywords:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT post_id, submolt, author, content_preview FROM moltbook_seen_posts WHERE is_mention = true;
"
```

### 9. Daily digest includes submolt section

After the next daily digest runs:

```bash
journalctl -u moltbook-proxy --since "today" --no-pager | grep -A 20 "Daily digest generated"
```

Expected: Digest output includes a "Submolt Intelligence:" section.

---

## Rollback

If issues arise:

### Quick disable (no code changes)

Deactivate all submolts in the watchlist:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
UPDATE moltbook_submolt_watchlist SET is_active = false;
"
```

The scanner will find no active submolts and return `None` every cycle. The daemon continues running normally with main feed scanning only.

### Full revert

1. Remove the `from submolt_scanner import SubmoltScanner` import from `proxy_daemon.py`
2. Remove the `self.scanner` initialization from `__init__` and `run()`
3. Remove the `_scan_submolts()` method and its call from the main loop
4. Remove the submolt intelligence additions from `intelligence_digest.py`
5. Restart the daemon: `sudo systemctl restart moltbook-proxy`

The database tables (`moltbook_submolt_watchlist`, `moltbook_seen_posts`) can remain -- they are inert without the scanner code.

The original code for all modified files is in git at the current HEAD.

---

*For Seven Generations*
*Cherokee AI Federation -- Moltbook Submolt Intelligence*
