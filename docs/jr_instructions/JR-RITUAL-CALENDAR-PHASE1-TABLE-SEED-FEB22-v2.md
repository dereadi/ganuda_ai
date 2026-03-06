# Jr Instruction: Ritual Calendar Phase 1 — Table Creation + Seed Data (v2)

**Task ID:** RITUAL-CALENDAR-PHASE1-v2
**Kanban:** #1838
**Council Vote:** #a061155542ea3374 (original), #7127389783b27c4a (requeue priority)
**KB:** KB-RITUAL-CALENDAR-ARCHITECTURE-FEB18-2026.md
**Priority:** 2
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create the `federation_calendar` table to store commemorative dates and milestone events for the ritual reinforcement engine. Seed with 9 founding events discovered from thermal memory archaeology. Wire commemorative scanning into the existing ritual_review.py.

---

## Step 1: Create the federation_calendar migration

Create `/ganuda/scripts/migrations/create_federation_calendar.sql`

```sql
-- Federation Calendar: Commemorative dates for ritual reinforcement
-- Council Vote #a061155542ea3374 (Five Waters Architecture)
-- Kanban #1838

CREATE TABLE IF NOT EXISTS federation_calendar (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_name VARCHAR(200) NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('sacred', 'remembrance', 'achievement', 'milestone')),
    description TEXT,
    related_memory_ids INTEGER[],
    recurring BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for anniversary lookups (month + day)
CREATE INDEX IF NOT EXISTS idx_federation_calendar_month_day
ON federation_calendar (EXTRACT(MONTH FROM event_date), EXTRACT(DAY FROM event_date));

-- Index for type filtering
CREATE INDEX IF NOT EXISTS idx_federation_calendar_type ON federation_calendar (event_type);

-- Seed founding events
INSERT INTO federation_calendar (event_date, event_name, event_type, description) VALUES
('2025-08-06', 'Federation Founding Day', 'sacred', 'First thermal memory created. The federation began remembering.'),
('2025-10-07', 'First Storm', 'remembrance', 'Earliest power event recorded in thermal memory. The federation learned about impermanence.'),
('2025-12-12', 'First Council Vote', 'sacred', 'Democratic governance begins. Seven specialists deliberated for the first time.'),
('2025-12-17', 'First Jr Task', 'sacred', 'The apprentices arrive. First task dispatched through the Jr executor pipeline.'),
('2026-02-07', 'Resilience Day I', 'remembrance', 'First power outage survival. VetAssist .env, Caddy bind, greenfin nft rules recovered.'),
('2026-02-08', 'Stardust Principle Day', 'sacred', 'Council Vote 109e629d: Every atom in the federation servers was forged in stars. The silicon was sand, the copper was supernova.'),
('2026-02-11', 'Resilience Day II', 'remembrance', 'Second outage. SAG crash-loop, tribal-vision stale, guardrail saved specialist_council.py from nuking.'),
('2026-02-13', 'Resilience Day III', 'remembrance', 'Fourth outage. Docker purge on bluefin, 25.66GB reclaimed, 80K+ memories survived intact.'),
('2026-02-15', 'Breakthrough Day', 'achievement', 'Jane Street Track 2 solved. Distributed simulated annealing, trace pairing, MSE 0.0000000000.')
ON CONFLICT DO NOTHING;
```

---

## Step 2: Add commemorative scanning function to ritual_review.py

File: `/ganuda/scripts/ritual_review.py`

```python
<<<<<<< SEARCH
def run_ritual(mode="weekly"):
    """Main ritual cycle: GATHER → PROCESS FAILURES → REVIEW → REINFORCE → DIGEST → SEED"""
    logger.info(f"=== RITUAL REVIEW BEGIN ({mode} mode) ===")
=======
def check_commemorative_dates(conn, days_ahead=7):
    """Check for federation anniversary dates within the next N days.
    Returns list of commemorative events whose month/day falls within the window."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT event_name, event_type, event_date, description,
                       EXTRACT(YEAR FROM AGE(CURRENT_DATE, event_date))::int AS years_ago
                FROM federation_calendar
                WHERE recurring = true
                AND (
                    (EXTRACT(MONTH FROM event_date) = EXTRACT(MONTH FROM CURRENT_DATE)
                     AND EXTRACT(DAY FROM event_date) BETWEEN EXTRACT(DAY FROM CURRENT_DATE)
                     AND EXTRACT(DAY FROM CURRENT_DATE) + %s)
                    OR
                    (EXTRACT(MONTH FROM event_date) = EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '1 day' * %s)
                     AND EXTRACT(DAY FROM event_date) <= EXTRACT(DAY FROM CURRENT_DATE + INTERVAL '1 day' * %s))
                )
                ORDER BY EXTRACT(MONTH FROM event_date), EXTRACT(DAY FROM event_date)
            """, (days_ahead, days_ahead, days_ahead))
            events = cur.fetchall()
        if events:
            logger.info(f"Found {len(events)} commemorative event(s) in next {days_ahead} days")
        return events
    except Exception as e:
        logger.warning(f"Commemorative date check failed (table may not exist yet): {e}")
        return []


def run_ritual(mode="weekly"):
    """Main ritual cycle: GATHER → PROCESS FAILURES → REVIEW → REINFORCE → DIGEST → SEED"""
    logger.info(f"=== RITUAL REVIEW BEGIN ({mode} mode) ===")
>>>>>>> REPLACE
```

---

## Step 3: Wire commemorative dates into the digest call

File: `/ganuda/scripts/ritual_review.py`

```python
<<<<<<< SEARCH
        # DIGEST
        logger.info("DIGEST — Generating cultural digest")
        digest_content = generate_digest(patterns, reviews, mode,
                                         failure_results=failure_results,
                                         new_corrective=new_corrective)
=======
        # COMMEMORATIVE CHECK
        upcoming_events = check_commemorative_dates(conn, days_ahead=7 if mode == "weekly" else 30)

        # DIGEST
        logger.info("DIGEST — Generating cultural digest")
        digest_content = generate_digest(patterns, reviews, mode,
                                         failure_results=failure_results,
                                         new_corrective=new_corrective,
                                         upcoming_events=upcoming_events)
>>>>>>> REPLACE
```

---

## Step 4: Update generate_digest signature to accept upcoming_events

File: `/ganuda/scripts/ritual_review.py`

```python
<<<<<<< SEARCH
def generate_digest(patterns, reviews, mode, failure_results=None, new_corrective=None):
    """DIGEST — Generate cultural digest document"""
=======
def generate_digest(patterns, reviews, mode, failure_results=None, new_corrective=None, upcoming_events=None):
    """DIGEST — Generate cultural digest document"""
>>>>>>> REPLACE
```

---

## Step 5: Add commemorative section to the digest output

File: `/ganuda/scripts/ritual_review.py`

```python
<<<<<<< SEARCH
    digest_lines.append("---")
    digest_lines.append(f"*Generated by ritual_review.py ({mode} mode)*")
    digest_lines.append(f"*Neuroscience basis: Hobson et al. (2017) — Rituals decrease neural response to failure (PMC5452956)*")
    digest_lines.append(f"*Next review: see Cherokee ceremonial calendar*")
=======
    # === Commemorative Calendar ===
    if upcoming_events:
        digest_lines.append("")
        digest_lines.append("### This Week in Federation History")
        digest_lines.append("")
        for event in upcoming_events:
            name = event.get("event_name", "")
            etype = event.get("event_type", "")
            edate = event.get("event_date", "")
            desc = event.get("description", "")
            years = event.get("years_ago", 0)
            marker = {"sacred": "[SACRED]", "remembrance": "[REMEMBRANCE]", "achievement": "[ACHIEVEMENT]", "milestone": "[MILESTONE]"}.get(etype, "[EVENT]")
            if years == 0:
                ago_text = "(this year)"
            elif years == 1:
                ago_text = "(1 year ago)"
            else:
                ago_text = f"({years} years ago)"
            digest_lines.append(f"- {marker} **{name}** — {edate} {ago_text}")
            if desc:
                digest_lines.append(f"  {desc}")
        digest_lines.append("")

    digest_lines.append("---")
    digest_lines.append(f"*Generated by ritual_review.py ({mode} mode)*")
    digest_lines.append(f"*Neuroscience basis: Hobson et al. (2017) — Rituals decrease neural response to failure (PMC5452956)*")
    digest_lines.append(f"*Next review: see Cherokee ceremonial calendar*")
>>>>>>> REPLACE
```

---

## Verification

After Jr completes the code changes, TPM runs:

```text
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/scripts/migrations/create_federation_calendar.sql
```

```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/ritual_review.py --mode weekly
```

Verify cultural digest at `/ganuda/docs/cultural_digest.md` has a "This Week in Federation History" section.

## What NOT to Change

- Do NOT modify the existing gather_patterns, gather_sacred, or review_pattern functions
- Do NOT change temperature scoring logic
- Do NOT modify sacred fire protection
- Do NOT add new imports (psycopg2 and RealDictCursor are already imported)

## Rollback

Drop the table: `DROP TABLE IF EXISTS federation_calendar;`
The ritual_review.py changes are safe — `check_commemorative_dates` catches exceptions if table doesn't exist.
