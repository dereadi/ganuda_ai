# Jr Instruction: Ritual Calendar Phase 1 — Table Creation + Seed Data

**Kanban:** #1838
**Council Vote:** #a061155542ea3374
**KB:** KB-RITUAL-CALENDAR-ARCHITECTURE-FEB18-2026.md
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.

---

## Overview

Create the `federation_calendar` table to store commemorative dates and milestone events for the ritual reinforcement engine. Seed with 9 founding events discovered from thermal memory archaeology.

---

## Step 1: Create the federation_calendar table

File: `/ganuda/scripts/migrations/create_federation_calendar.sql`

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
CREATE INDEX idx_federation_calendar_month_day
ON federation_calendar (EXTRACT(MONTH FROM event_date), EXTRACT(DAY FROM event_date));

-- Index for type filtering
CREATE INDEX idx_federation_calendar_type ON federation_calendar (event_type);

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
('2026-02-15', 'Breakthrough Day', 'achievement', 'Jane Street Track 2 — trace pairing solver achieved MSE 0.004576, 3.2x better than public solver.');
```

---

## Step 2: Add commemorative scanning to ritual_review.py

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
def run_ritual(mode="weekly"):
    """Main ritual orchestration: GATHER → PROCESS → REVIEW → REINFORCE → DIGEST → SEED"""
    logging.info(f"=== RITUAL REVIEW ({mode.upper()}) BEGINNING ===")
=======
def check_commemorative_dates(conn, days_ahead=7):
    """Check for federation anniversary dates within the next N days.
    Returns list of commemorative events whose month/day falls within the window."""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT event_name, event_type, event_date, description,
                   EXTRACT(YEAR FROM AGE(CURRENT_DATE, event_date))::int AS years_ago
            FROM federation_calendar
            WHERE recurring = true
            AND (
                -- Check if anniversary falls within next N days
                (EXTRACT(MONTH FROM event_date) = EXTRACT(MONTH FROM CURRENT_DATE)
                 AND EXTRACT(DAY FROM event_date) BETWEEN EXTRACT(DAY FROM CURRENT_DATE)
                 AND EXTRACT(DAY FROM CURRENT_DATE) + %s)
                OR
                -- Handle month boundary (e.g., Jan 29 looking 7 days ahead into Feb)
                (EXTRACT(MONTH FROM event_date) = EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '%s days')
                 AND EXTRACT(DAY FROM event_date) <= EXTRACT(DAY FROM CURRENT_DATE + INTERVAL '%s days'))
            )
            ORDER BY EXTRACT(MONTH FROM event_date), EXTRACT(DAY FROM event_date)
        """, (days_ahead, days_ahead, days_ahead))
        events = cur.fetchall()
        cur.close()
        if events:
            logging.info(f"Found {len(events)} commemorative event(s) in next {days_ahead} days")
        return events
    except Exception as e:
        logging.warning(f"Commemorative date check failed (table may not exist yet): {e}")
        return []


def run_ritual(mode="weekly"):
    """Main ritual orchestration: GATHER → PROCESS → REVIEW → REINFORCE → DIGEST → SEED"""
    logging.info(f"=== RITUAL REVIEW ({mode.upper()}) BEGINNING ===")
>>>>>>> REPLACE

---

## Step 3: Wire commemorative dates into the digest

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
    # === DIGEST ===
    digest = generate_digest(patterns, reviews, mode, failure_results, new_corrective)
=======
    # === COMMEMORATIVE CHECK ===
    upcoming_events = check_commemorative_dates(conn, days_ahead=7 if mode == "weekly" else 30)

    # === DIGEST ===
    digest = generate_digest(patterns, reviews, mode, failure_results, new_corrective, upcoming_events)
>>>>>>> REPLACE

---

## Step 4: Update generate_digest to include commemorative section

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
def generate_digest(patterns, reviews, mode, failure_results=None, new_corrective=None):
=======
def generate_digest(patterns, reviews, mode, failure_results=None, new_corrective=None, upcoming_events=None):
>>>>>>> REPLACE

---

## Step 5: Add commemorative section to digest output

File: `/ganuda/scripts/ritual_review.py`

Find the line near the end of `generate_digest` that writes the neuroscience citation footer, and add the commemorative section before it:

<<<<<<< SEARCH
    lines.append("---")
    lines.append("*Generated by ritual_review.py ({} mode)*".format(mode))
    lines.append("*Neuroscience basis: Hobson et al. (2017) — Rituals decrease neural response to failure (PMC5452956)*")
=======
    # === Commemorative Calendar ===
    if upcoming_events:
        lines.append("")
        lines.append("### This Week in Federation History")
        lines.append("")
        for event in upcoming_events:
            name = event.get("event_name", event[0]) if isinstance(event, dict) else event[0]
            etype = event.get("event_type", event[1]) if isinstance(event, dict) else event[1]
            edate = event.get("event_date", event[2]) if isinstance(event, dict) else event[2]
            desc = event.get("description", event[3]) if isinstance(event, dict) else event[3]
            years = event.get("years_ago", event[4]) if isinstance(event, dict) else event[4]
            marker = {"sacred": "🔥", "remembrance": "⚡", "achievement": "🌟", "milestone": "📊"}.get(etype, "📅")
            if years == 0:
                ago_text = "(this year)"
            elif years == 1:
                ago_text = "(1 year ago)"
            else:
                ago_text = f"({years} years ago)"
            lines.append(f"- {marker} **{name}** — {edate} {ago_text}")
            if desc:
                lines.append(f"  {desc}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by ritual_review.py ({} mode)*".format(mode))
    lines.append("*Neuroscience basis: Hobson et al. (2017) — Rituals decrease neural response to failure (PMC5452956)*")
>>>>>>> REPLACE

---

## Manual Steps (TPM)

After Jr completes the code changes:

1. Run the migration on bluefin PostgreSQL:
```text
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/scripts/migrations/create_federation_calendar.sql
```

2. Test the ritual with commemorative scanning:
```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/ritual_review.py --mode weekly
```

3. Verify the cultural digest has a "This Week in Federation History" section.

---

## Acceptance Criteria

- [ ] `federation_calendar` table exists with 9 seeded events
- [ ] `check_commemorative_dates()` function added to ritual_review.py
- [ ] `generate_digest()` accepts and renders upcoming_events
- [ ] Weekly ritual run includes commemorative section when events match
- [ ] No breaking changes to existing ritual modes
