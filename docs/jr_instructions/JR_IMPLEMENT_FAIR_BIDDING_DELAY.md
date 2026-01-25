# Jr Build Instructions: Fair Bidding with Progressive Delay

**Task ID:** JR-FAIR-BIDDING-001
**Priority:** High (P1)
**Assigned Specialist:** Gecko (Technical Integration)
**Date:** 2025-12-25

---

## Problem Statement

Current bidding is first-come-first-served. jr-redfin-gecko has grabbed **102 tasks** while other Jrs combined have only **24**. This creates:

1. Single point of failure (if Gecko goes down, work stops)
2. Underutilized Jrs on other nodes
3. No load distribution across federation

## Solution: Progressive Delay Penalty

When a Jr wins consecutive bids, add an increasing delay before they can bid again:

| Consecutive Wins | Delay Before Next Bid |
|------------------|----------------------|
| 1 | 0 seconds (normal) |
| 2 | 10 seconds |
| 3 | 20 seconds |
| 4 | 30 seconds |
| 5+ | 45 seconds |

**Reset condition:** When another Jr wins a bid, all delays reset to 0.

---

## Implementation

### 1. Schema Addition

Add tracking columns to jr_task_bids or create a new table:

```sql
-- Add to bluefin
CREATE TABLE IF NOT EXISTS jr_bidding_fairness (
    agent_id VARCHAR(64) PRIMARY KEY,
    consecutive_wins INTEGER DEFAULT 0,
    last_win_at TIMESTAMP,
    current_delay_seconds INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initialize existing agents
INSERT INTO jr_bidding_fairness (agent_id, consecutive_wins, total_wins)
SELECT DISTINCT assigned_to, 0, COUNT(*)
FROM jr_task_announcements
WHERE assigned_to IS NOT NULL
GROUP BY assigned_to
ON CONFLICT (agent_id) DO UPDATE SET total_wins = EXCLUDED.total_wins;
```

### 2. Bidding Daemon Modification

Modify the bidding logic in `/ganuda/services/jr_bidding/bidding_daemon.py` or equivalent:

```python
import time
from datetime import datetime, timedelta

DELAY_SCHEDULE = {
    1: 0,
    2: 10,
    3: 20,
    4: 30,
}
MAX_DELAY = 45  # For 5+ consecutive wins

def get_bidding_delay(agent_id: str) -> int:
    """Get current delay for this agent based on consecutive wins."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT consecutive_wins, current_delay_seconds
        FROM jr_bidding_fairness
        WHERE agent_id = %s
    """, (agent_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return 0

    consecutive_wins = row[0]
    return DELAY_SCHEDULE.get(consecutive_wins, MAX_DELAY)

def record_bid_win(winning_agent: str):
    """Record a win and update delays for all agents."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Increment winner's consecutive wins
    cur.execute("""
        INSERT INTO jr_bidding_fairness (agent_id, consecutive_wins, last_win_at, total_wins)
        VALUES (%s, 1, NOW(), 1)
        ON CONFLICT (agent_id) DO UPDATE SET
            consecutive_wins = jr_bidding_fairness.consecutive_wins + 1,
            last_win_at = NOW(),
            total_wins = jr_bidding_fairness.total_wins + 1,
            current_delay_seconds = CASE
                WHEN jr_bidding_fairness.consecutive_wins >= 4 THEN 45
                WHEN jr_bidding_fairness.consecutive_wins = 3 THEN 30
                WHEN jr_bidding_fairness.consecutive_wins = 2 THEN 20
                WHEN jr_bidding_fairness.consecutive_wins = 1 THEN 10
                ELSE 0
            END,
            updated_at = NOW()
    """, (winning_agent,))

    # Reset OTHER agents' consecutive wins (they get a fresh start)
    cur.execute("""
        UPDATE jr_bidding_fairness
        SET consecutive_wins = 0, current_delay_seconds = 0, updated_at = NOW()
        WHERE agent_id != %s
    """, (winning_agent,))

    conn.commit()
    conn.close()

def submit_bid(agent_id: str, task_id: str, bid_score: float):
    """Submit a bid with fairness delay."""

    # Check if we need to wait
    delay = get_bidding_delay(agent_id)
    if delay > 0:
        print(f"[FAIRNESS] {agent_id} waiting {delay}s before bidding (consecutive wins penalty)")
        time.sleep(delay)

    # Now submit the actual bid
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO jr_task_bids (task_id, agent_id, bid_score, bid_time)
        VALUES (%s, %s, %s, NOW())
    """, (task_id, agent_id, bid_score))

    conn.commit()
    conn.close()

def award_task(task_id: str):
    """Award task to highest bidder and record the win."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get highest bid
    cur.execute("""
        SELECT agent_id, bid_score
        FROM jr_task_bids
        WHERE task_id = %s
        ORDER BY bid_score DESC, bid_time ASC
        LIMIT 1
    """, (task_id,))

    winner = cur.fetchone()
    if winner:
        winning_agent = winner[0]

        # Update task assignment
        cur.execute("""
            UPDATE jr_task_announcements
            SET assigned_to = %s, status = 'assigned'
            WHERE task_id = %s
        """, (winning_agent, task_id))

        conn.commit()
        conn.close()

        # Record the win for fairness tracking
        record_bid_win(winning_agent)

        return winning_agent

    conn.close()
    return None
```

### 3. Alternative: Bidding Window Approach

Instead of delays, use a bidding window where all bids are collected before awarding:

```python
BIDDING_WINDOW_SECONDS = 5  # Collect bids for 5 seconds

def announce_task_with_window(task_id: str, task_content: str):
    """Announce task and wait for bidding window before awarding."""

    # Insert task announcement
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jr_task_announcements (task_id, task_content, status, announced_at)
        VALUES (%s, %s, 'bidding', NOW())
    """, (task_id, task_content))
    conn.commit()
    conn.close()

    # Wait for bidding window
    print(f"[BIDDING] Task {task_id} open for {BIDDING_WINDOW_SECONDS}s...")
    time.sleep(BIDDING_WINDOW_SECONDS)

    # Award to highest bidder, with fairness penalty applied to scores
    conn = get_db_connection()
    cur = conn.cursor()

    # Apply fairness penalty: reduce effective score based on consecutive wins
    cur.execute("""
        SELECT b.agent_id,
               b.bid_score * (1.0 - (COALESCE(f.consecutive_wins, 0) * 0.1)) as adjusted_score
        FROM jr_task_bids b
        LEFT JOIN jr_bidding_fairness f ON b.agent_id = f.agent_id
        WHERE b.task_id = %s
        ORDER BY adjusted_score DESC, b.bid_time ASC
        LIMIT 1
    """, (task_id,))

    winner = cur.fetchone()
    # ... award logic
```

---

## Deployment Steps

### On bluefin:

```bash
# 1. Create fairness tracking table
PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production << 'EOF'
CREATE TABLE IF NOT EXISTS jr_bidding_fairness (
    agent_id VARCHAR(64) PRIMARY KEY,
    consecutive_wins INTEGER DEFAULT 0,
    last_win_at TIMESTAMP,
    current_delay_seconds INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initialize from existing data
INSERT INTO jr_bidding_fairness (agent_id, consecutive_wins, total_wins)
SELECT DISTINCT assigned_to, 0, COUNT(*)
FROM jr_task_announcements
WHERE assigned_to IS NOT NULL
GROUP BY assigned_to
ON CONFLICT (agent_id) DO NOTHING;
EOF
```

### On redfin (and other Jr nodes):

```bash
# 2. Update bidding daemon with fairness logic
# Edit /ganuda/services/jr_bidding/bidding_daemon.py
# Add the functions above

# 3. Restart bidding daemon
sudo systemctl restart jr-bidding
```

---

## Validation

```sql
-- Check fairness distribution after 10 tasks
SELECT agent_id, consecutive_wins, current_delay_seconds, total_wins
FROM jr_bidding_fairness
ORDER BY total_wins DESC;

-- Should see more even distribution:
-- Before: Gecko 102, Turtle 13, Eagle 10
-- After:  Gecko ~40, Turtle ~35, Eagle ~35 (roughly)
```

---

## Acceptance Criteria

1. [ ] `jr_bidding_fairness` table created on bluefin
2. [ ] Bidding daemon updated with delay logic
3. [ ] Consecutive wins tracked correctly
4. [ ] Delays applied (verify with logs)
5. [ ] Task distribution more even after 20+ tasks

---

*For Seven Generations - Cherokee AI Federation*
