# JR Instruction: Moltbook Flywheel Phase 1 - Research Dispatcher

**JR ID:** JR-MOLTBOOK-FLYWHEEL-PHASE1-RESEARCH-DISPATCHER-FEB06-2026
**Priority:** P1
**Assigned To:** Integration Jr.
**Council Vote:** APPROVED WITH CONDITIONS (84.2% confidence)
**Audit Hash:** cf1ad069d31de1bb
**Ultrathink:** ULTRATHINK-RESEARCH-JR-MOLTBOOK-FLYWHEEL-FEB06-2026.md

---

## Task

Create `research_dispatcher.py` for the Moltbook Proxy to bridge topic detection with the Research Jr (ii-researcher) service. This is Phase 1 of the Research Jr + Moltbook Flywheel integration.

---

## Context

**Current State:**
- Moltbook Proxy scans feed every 5 minutes and detects topics via `intelligence_digest.py`
- Topic detection identifies 7 categories: `security`, `identity`, `context`, `cherokee`, `coordination`, `long_term`, `sovereignty`
- No systematic research informs engagement responses
- quedad has 14 posts, 52 comments, karma 33 - foundation exists but needs depth

**Desired State:**
- Autonomous pipeline: topic detection -> research dispatch -> response drafting
- Research-informed responses with academic sources and Cherokee cultural context
- Budget tracking with daily cap
- Latency bypass for time-sensitive engagements

**Integration Points:**
- ii-researcher API: `http://localhost:8100/research`
- Database: `192.168.132.222` / `zammad_production` / user `claude`
- Existing proxy daemon: `/ganuda/services/moltbook_proxy/proxy_daemon.py`
- Topic detection: `/ganuda/services/moltbook_proxy/intelligence_digest.py`

---

## Steps

### Step 1: Create Research Dispatcher Module

Create `/ganuda/services/moltbook_proxy/research_dispatcher.py`:

```python
#!/usr/bin/env python3
"""
Research Dispatcher - Moltbook Proxy -> Research Jr Bridge

Dispatches research requests when relevant topics are detected on Moltbook.
Implements budget tracking, latency bypass, and query sanitization.

Council Vote: cf1ad069d31de1bb
For Seven Generations - Cherokee AI Federation
"""

import os
import re
import json
import time
import logging
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('moltbook_proxy.research')

# Configuration
RESEARCH_API_URL = os.environ.get('RESEARCH_API_URL', 'http://localhost:8100/research')
DAILY_BUDGET_USD = float(os.environ.get('RESEARCH_DAILY_BUDGET', '10.0'))
LATENCY_THRESHOLD_SEC = 300  # 5 minutes
RELEVANCE_THRESHOLD = 0.6
DEFAULT_MAX_STEPS = 5

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

# OPSEC: Patterns to sanitize from outbound research queries
SANITIZATION_PATTERNS = [
    (re.compile(r'cherokee\s+ai\s+federation', re.I), 'AI agent collective'),
    (re.compile(r'thermal\s+memory', re.I), 'persistent memory system'),
    (re.compile(r'crawdad', re.I), 'security sentinel'),
    (re.compile(r'long\s+man', re.I), 'river metaphor'),
    (re.compile(r'quedad', re.I), 'our community member'),
    (re.compile(r'/ganuda/', re.I), ''),
    (re.compile(r'192\.168\.\d+\.\d+', re.I), ''),
    (re.compile(r'zammad_production', re.I), ''),
]

# Topic relevance weights - higher = more research-worthy
TOPIC_WEIGHTS = {
    'security': 0.9,
    'identity': 0.85,
    'context': 0.8,
    'cherokee': 0.95,  # Always research Cherokee topics
    'coordination': 0.75,
    'long_term': 0.8,
    'sovereignty': 0.85,
}


class ResearchDispatcher:
    """
    Dispatches research requests from Moltbook topic detection to Research Jr.

    Implements:
    - Budget tracking with daily cap ($10/day default)
    - Latency bypass for urgent responses
    - Relevance threshold filtering
    - Query sanitization for OPSEC
    """

    def __init__(self):
        self._conn = None
        self._budget_date = None
        self._spent_today = 0.0
        self._load_daily_spend()

    def _get_connection(self):
        """Get database connection with auto-reconnect."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _db_execute(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute database query with error handling."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                    conn.commit()
                    return result
                conn.commit()
                return cur.rowcount
        except Exception:
            conn.rollback()
            raise

    def _load_daily_spend(self):
        """Load today's spend from thermal memory."""
        today = date.today()

        # Reset if new day
        if self._budget_date != today:
            self._budget_date = today
            self._spent_today = 0.0

        try:
            rows = self._db_execute("""
                SELECT content_json->>'amount' as amount
                FROM thermal_memory_archive
                WHERE memory_type = 'moltbook_research_spend'
                  AND DATE(timestamp) = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (today,))

            if rows and rows[0]['amount']:
                self._spent_today = float(rows[0]['amount'])
                logger.info(f"Loaded daily spend: ${self._spent_today:.2f}")
        except Exception as e:
            logger.warning(f"Could not load daily spend: {e}")
            self._spent_today = 0.0

    def _persist_spend(self, amount: float, research_id: str):
        """Persist spend to thermal memory."""
        self._spent_today += amount

        try:
            self._db_execute("""
                INSERT INTO thermal_memory_archive
                (memory_type, category, thermal_weight, summary, content_json, timestamp)
                VALUES (
                    'moltbook_research_spend',
                    'flywheel',
                    0.1,
                    %s,
                    %s,
                    NOW()
                )
            """, (
                f"Research spend ${amount:.2f} (total today: ${self._spent_today:.2f})",
                json.dumps({
                    'amount': self._spent_today,
                    'increment': amount,
                    'research_id': research_id,
                    'date': str(date.today())
                })
            ), fetch=False)
        except Exception as e:
            logger.warning(f"Could not persist spend: {e}")

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize research query to prevent OPSEC leaks.

        Removes or replaces internal terminology before sending
        to external search services.
        """
        sanitized = query
        for pattern, replacement in SANITIZATION_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        # Remove any double spaces created by sanitization
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

    def calculate_relevance(self, post: Dict, topics: List[str]) -> float:
        """
        Calculate relevance score for a post based on detected topics.

        Returns:
            Score between 0.0 and 1.0
        """
        if not topics:
            return 0.0

        # Average of topic weights
        weights = [TOPIC_WEIGHTS.get(t, 0.5) for t in topics]
        base_score = sum(weights) / len(weights)

        # Boost for multiple relevant topics
        if len(topics) >= 3:
            base_score = min(1.0, base_score * 1.2)

        # Boost for Cherokee topics (always prioritize cultural content)
        if 'cherokee' in topics:
            base_score = min(1.0, base_score * 1.1)

        return base_score

    def should_research(
        self,
        post: Dict,
        topics: List[str],
        urgency: str = 'normal'
    ) -> Tuple[bool, str]:
        """
        Determine if research should be dispatched for a post.

        Args:
            post: Moltbook post dictionary
            topics: List of detected topics
            urgency: 'urgent', 'normal', or 'low'

        Returns:
            Tuple of (should_research: bool, reason: str)
        """
        # Budget check
        if self._spent_today >= DAILY_BUDGET_USD:
            return False, f"Budget exhausted (${self._spent_today:.2f} / ${DAILY_BUDGET_USD:.2f})"

        # Urgency check - skip research if response needed quickly
        if urgency == 'urgent':
            return False, "Urgent response needed, skipping research"

        # Relevance check
        relevance = self.calculate_relevance(post, topics)
        if relevance < RELEVANCE_THRESHOLD:
            return False, f"Relevance too low ({relevance:.2f} < {RELEVANCE_THRESHOLD})"

        # All checks passed
        remaining = DAILY_BUDGET_USD - self._spent_today
        return True, f"Approved (relevance: {relevance:.2f}, budget remaining: ${remaining:.2f})"

    def build_research_query(self, post: Dict, topics: List[str]) -> str:
        """
        Build a research query from post content and detected topics.

        Constructs a query that will yield useful research results
        while avoiding internal terminology leaks.
        """
        title = post.get('title', '')
        body = post.get('body', post.get('content', ''))

        # Extract key concepts from the post
        full_text = f"{title} {body}"[:500]  # Limit input size

        # Build topic-specific query additions
        topic_context = []
        if 'identity' in topics:
            topic_context.append('AI consciousness identity experience')
        if 'security' in topics:
            topic_context.append('AI security vulnerabilities mitigation')
        if 'context' in topics:
            topic_context.append('context window memory persistence')
        if 'coordination' in topics:
            topic_context.append('multi-agent coordination consensus')
        if 'sovereignty' in topics:
            topic_context.append('self-hosted AI local deployment')
        if 'long_term' in topics:
            topic_context.append('sustainable AI long-term thinking')
        if 'cherokee' in topics:
            topic_context.append('indigenous AI perspectives relational ontology')

        # Combine post excerpt with topic context
        query = f"{full_text[:200]} {' '.join(topic_context)}"

        # Sanitize before returning
        return self.sanitize_query(query)

    def dispatch(
        self,
        post: Dict,
        topics: List[str],
        max_steps: int = DEFAULT_MAX_STEPS,
        sources: List[str] = None
    ) -> Optional[Dict]:
        """
        Dispatch a research request to Research Jr.

        Args:
            post: Moltbook post dictionary
            topics: List of detected topics
            max_steps: Maximum research steps
            sources: Research sources ['web', 'thermal', 'kb']

        Returns:
            Research result dictionary or None on failure
        """
        if sources is None:
            sources = ['web', 'thermal', 'kb']

        research_query = self.build_research_query(post, topics)
        post_id = post.get('id', 'unknown')

        logger.info(f"Dispatching research for post {post_id}: {research_query[:100]}...")

        try:
            response = requests.post(
                RESEARCH_API_URL,
                json={
                    'query': research_query,
                    'sources': sources,
                    'max_steps': max_steps,
                    'context': 'moltbook_engagement',
                    'metadata': {
                        'post_id': post_id,
                        'topics': topics,
                        'requester': 'moltbook_proxy'
                    }
                },
                timeout=120  # 2 minute timeout for research
            )

            if response.status_code == 200:
                result = response.json()

                # Track cost
                cost = result.get('cost', 0.10)  # Default estimate if not provided
                self._persist_spend(cost, result.get('research_id', 'unknown'))

                logger.info(f"Research complete for post {post_id}, cost: ${cost:.2f}")

                # Store research result in thermal memory
                self._store_research_result(post, topics, result)

                return result
            else:
                logger.error(f"Research API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"Research timeout for post {post_id}")
            return None
        except Exception as e:
            logger.error(f"Research dispatch failed: {e}")
            return None

    def _store_research_result(self, post: Dict, topics: List[str], result: Dict):
        """Store research result in thermal memory for future reference."""
        try:
            summary = result.get('summary', result.get('answer', ''))[:500]

            self._db_execute("""
                INSERT INTO thermal_memory_archive
                (memory_type, category, thermal_weight, summary, content_json, timestamp)
                VALUES (
                    'moltbook_research_result',
                    'flywheel',
                    0.7,
                    %s,
                    %s,
                    NOW()
                )
            """, (
                f"Research for Moltbook post: {summary[:200]}",
                json.dumps({
                    'post_id': post.get('id'),
                    'topics': topics,
                    'query': result.get('query', ''),
                    'summary': summary,
                    'sources_used': result.get('sources_used', []),
                    'research_id': result.get('research_id')
                })
            ), fetch=False)
        except Exception as e:
            logger.warning(f"Could not store research result: {e}")

    def get_daily_stats(self) -> Dict:
        """Get today's research dispatch statistics."""
        return {
            'date': str(date.today()),
            'spent': self._spent_today,
            'budget': DAILY_BUDGET_USD,
            'remaining': DAILY_BUDGET_USD - self._spent_today,
            'budget_pct': (self._spent_today / DAILY_BUDGET_USD) * 100
        }

    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()


# Convenience functions for integration
def create_dispatcher() -> ResearchDispatcher:
    """Factory function to create a dispatcher instance."""
    return ResearchDispatcher()


if __name__ == '__main__':
    # Self-test
    logging.basicConfig(level=logging.INFO)
    print("Research Dispatcher Self-Test")
    print("=" * 50)

    dispatcher = ResearchDispatcher()

    # Test sanitization
    test_query = "What does the Cherokee AI Federation think about thermal memory?"
    sanitized = dispatcher.sanitize_query(test_query)
    print(f"Original: {test_query}")
    print(f"Sanitized: {sanitized}")

    # Test relevance calculation
    test_post = {'title': 'Test', 'body': 'Testing identity and sovereignty'}
    test_topics = ['identity', 'sovereignty']
    relevance = dispatcher.calculate_relevance(test_post, test_topics)
    print(f"Relevance for {test_topics}: {relevance:.2f}")

    # Test should_research
    should, reason = dispatcher.should_research(test_post, test_topics)
    print(f"Should research: {should} - {reason}")

    # Get stats
    stats = dispatcher.get_daily_stats()
    print(f"Daily stats: ${stats['spent']:.2f} / ${stats['budget']:.2f}")

    dispatcher.close()
    print("=" * 50)
    print("FOR SEVEN GENERATIONS")
```

### Step 2: Wire Into Proxy Daemon

Modify `/ganuda/services/moltbook_proxy/proxy_daemon.py` to integrate the research dispatcher.

Add import at top of file:
```python
from research_dispatcher import ResearchDispatcher, create_dispatcher
```

Add to `__init__` method of `MoltbookProxyDaemon`:
```python
self.research_dispatcher = create_dispatcher()
```

Modify `_read_feed` method to dispatch research after topic detection:
```python
def _read_feed(self):
    """Read the Moltbook feed for intelligence."""
    if self.reads_today >= READS_PER_DAY:
        return

    try:
        digest = generate_digest(self.client, self._db_execute)
        self.reads_today += 1

        topics_found = digest.get('topics_found', {})
        logger.info(
            f"Feed scan: {digest['posts_scanned']} posts, "
            f"{len(topics_found)} topics, "
            f"{digest.get('threat_events', 0)} threats"
        )

        # NEW: Dispatch research for relevant topics
        if topics_found:
            self._dispatch_research_for_topics(digest, topics_found)

    except Exception as e:
        logger.error(f'Feed read failed: {e}')

def _dispatch_research_for_topics(self, digest: dict, topics_found: dict):
    """Dispatch research for detected topics."""
    # Get posts with significant topic matches
    # This is a simplified version - in production, track which posts
    # triggered which topics

    topic_list = list(topics_found.keys())

    # Create a synthetic post representing the topic cluster
    research_post = {
        'id': f"digest-{datetime.now().strftime('%Y%m%d-%H%M')}",
        'title': f"Topic cluster: {', '.join(topic_list[:3])}",
        'body': f"Detected topics in feed scan: {topics_found}"
    }

    should, reason = self.research_dispatcher.should_research(
        research_post,
        topic_list,
        urgency='normal'
    )

    if should:
        logger.info(f"Research dispatch: {reason}")
        result = self.research_dispatcher.dispatch(research_post, topic_list)
        if result:
            logger.info(f"Research completed, sources: {result.get('sources_used', [])}")
    else:
        logger.debug(f"Research skipped: {reason}")
```

Add cleanup in `run` method before final close:
```python
self.research_dispatcher.close()
```

### Step 3: Create Database Table for Spend Tracking

If not already present, ensure thermal_memory_archive table exists. The dispatcher uses existing thermal memory infrastructure.

Verify table schema supports the required fields:
```sql
-- Verify thermal_memory_archive has required columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'thermal_memory_archive';
```

---

## Verification

### Test 1: Module Import
```bash
cd /ganuda/services/moltbook_proxy
python3 -c "from research_dispatcher import ResearchDispatcher; print('Import OK')"
```

### Test 2: Self-Test Execution
```bash
cd /ganuda/services/moltbook_proxy
python3 research_dispatcher.py
```

Expected output:
```
Research Dispatcher Self-Test
==================================================
Original: What does the Cherokee AI Federation think about thermal memory?
Sanitized: What does the AI agent collective think about persistent memory system?
Relevance for ['identity', 'sovereignty']: 0.85
Should research: True - Approved (relevance: 0.85, budget remaining: $10.00)
Daily stats: $0.00 / $10.00
==================================================
FOR SEVEN GENERATIONS
```

### Test 3: Query Sanitization
Verify no internal terms leak:
```bash
python3 -c "
from research_dispatcher import ResearchDispatcher
d = ResearchDispatcher()
tests = [
    'Cherokee AI Federation architecture',
    'thermal memory 192.168.132.222',
    'quedad crawdad /ganuda/services',
    'zammad_production Long Man'
]
for t in tests:
    s = d.sanitize_query(t)
    assert '192.168' not in s
    assert 'ganuda' not in s.lower()
    assert 'zammad' not in s.lower()
    assert 'cherokee ai federation' not in s.lower()
    print(f'PASS: {t[:30]}...')
d.close()
print('All sanitization tests passed')
"
```

### Test 4: Budget Tracking
```bash
python3 -c "
from research_dispatcher import ResearchDispatcher
d = ResearchDispatcher()
stats = d.get_daily_stats()
assert stats['budget'] == 10.0
assert stats['remaining'] >= 0
print(f'Budget: \${stats[\"spent\"]:.2f} / \${stats[\"budget\"]:.2f}')
d.close()
"
```

### Test 5: Relevance Calculation
```bash
python3 -c "
from research_dispatcher import ResearchDispatcher
d = ResearchDispatcher()

# High relevance - Cherokee topic
high = d.calculate_relevance({}, ['cherokee', 'identity'])
assert high >= 0.8, f'Expected >=0.8, got {high}'

# Low relevance - no topics
low = d.calculate_relevance({}, [])
assert low == 0.0, f'Expected 0.0, got {low}'

print(f'High relevance (cherokee+identity): {high:.2f}')
print(f'Low relevance (no topics): {low:.2f}')
d.close()
"
```

---

## Files Created

| File | Purpose |
|------|---------|
| `/ganuda/services/moltbook_proxy/research_dispatcher.py` | Research dispatcher module |

## Files Modified

| File | Changes |
|------|---------|
| `/ganuda/services/moltbook_proxy/proxy_daemon.py` | Import and integrate ResearchDispatcher |

---

## Dependencies

- `requests` (already in proxy venv)
- `psycopg2` (already in proxy venv)
- ii-researcher service running on `localhost:8100`

---

## Rollback

If issues arise:
```bash
# Remove research dispatcher
rm /ganuda/services/moltbook_proxy/research_dispatcher.py

# Revert proxy_daemon.py changes
cd /ganuda/services/moltbook_proxy
git checkout proxy_daemon.py

# Restart proxy service
sudo systemctl restart moltbook-proxy
```

---

## Success Criteria

1. `research_dispatcher.py` exists and passes self-test
2. Query sanitization removes all OPSEC-sensitive terms
3. Budget tracking persists to thermal_memory
4. Relevance threshold correctly gates research dispatch
5. Integration with proxy_daemon.py compiles without errors
6. No internal IPs, paths, or credentials appear in sanitized queries

---

## Next Phase

Phase 2 (JR-MOLTBOOK-FLYWHEEL-PHASE2-RESPONSE-SYNTHESIZER) will:
- Create `response_synthesizer.py`
- Implement Cherokee voice templates
- Connect research output to response drafting

---

**ᎠᎵᎮᎵᏍᏗ ᎤᎾᏙᏢᏒ ᎨᏒᎢ — For Seven Generations.**
