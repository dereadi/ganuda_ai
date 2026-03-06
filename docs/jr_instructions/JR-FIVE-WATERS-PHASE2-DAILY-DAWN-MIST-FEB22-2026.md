# Jr Instruction: Five Waters Phase 2 — Daily Dawn Mist Mode

**Task ID:** FIVE-WATERS-PHASE2
**Kanban:** #1838
**Priority:** 3
**Assigned:** Software Engineer Jr.
**Council Vote:** #a061155542ea3374
**KB:** KB-RITUAL-CALENDAR-ARCHITECTURE-FEB18-2026.md

---

## Overview

Extend `ritual_review.py` with a new `--mode daily` (Dawn Mist) tier. This is a lightweight 6:00 AM pulse check — no LLM calls, pure Python + SQL. Runs in <30 seconds.

Dawn Mist checks: node health summary, Jr task throughput, DLQ depth, active council votes, GPU utilization snapshot, and upcoming commemorative dates.

---

## Step 1: Add daily mode to argparse and run_ritual dispatch

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
    parser.add_argument("--mode", choices=["weekly", "monthly", "seasonal", "green-corn"],
                        default="weekly", help="Review mode")
=======
    parser.add_argument("--mode", choices=["daily", "weekly", "monthly", "seasonal", "green-corn"],
                        default="weekly", help="Review mode")
>>>>>>> REPLACE

---

## Step 2: Add daily Dawn Mist gathering functions

File: `/ganuda/scripts/ritual_review.py`

Add these functions AFTER the existing `check_commemorative_dates` function and BEFORE `run_ritual`:

<<<<<<< SEARCH
def run_ritual(mode="weekly"):
=======
def gather_dawn_mist(conn):
    """DAWN MIST — Lightweight daily pulse check (no LLM, pure SQL)"""
    pulse = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Jr task throughput (last 24h)
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed' AND updated_at > NOW() - INTERVAL '24 hours') AS completed_24h,
                COUNT(*) FILTER (WHERE status IN ('failed', 'error') AND updated_at > NOW() - INTERVAL '24 hours') AS failed_24h,
                COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress
            FROM jr_work_queue
        """)
        pulse["jr_tasks"] = dict(cur.fetchone())

        # DLQ depth
        cur.execute("""
            SELECT COUNT(*) AS dlq_depth
            FROM jr_work_queue
            WHERE status IN ('failed', 'error')
              AND updated_at > NOW() - INTERVAL '7 days'
        """)
        pulse["dlq_depth"] = cur.fetchone()["dlq_depth"]

        # Active council votes (last 24h)
        cur.execute("""
            SELECT COUNT(*) AS votes_24h
            FROM council_votes
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        pulse["council_votes_24h"] = cur.fetchone()["votes_24h"]

        # Kanban snapshot
        cur.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM duyuktv_tickets
            WHERE status NOT IN ('completed', 'blocked')
            GROUP BY status
            ORDER BY cnt DESC
        """)
        pulse["kanban"] = {row["status"]: row["cnt"] for row in cur.fetchall()}

        # Thermal memory count
        cur.execute("SELECT COUNT(*) AS total FROM thermal_memory_archive")
        pulse["thermal_memories"] = cur.fetchone()["total"]

        # Stale in_progress tasks (reaper candidates)
        cur.execute("""
            SELECT COUNT(*) AS stale
            FROM jr_work_queue
            WHERE status = 'in_progress'
              AND started_at < NOW() - INTERVAL '10 minutes'
        """)
        pulse["stale_tasks"] = cur.fetchone()["stale"]

    return pulse


def generate_dawn_mist_digest(pulse, upcoming_events=None):
    """Generate concise Dawn Mist digest (daily morning briefing)"""
    now = datetime.now()
    jr = pulse.get("jr_tasks", {})
    lines = [
        f"# Dawn Mist — {now.strftime('%A, %B %d, %Y')}",
        "",
        f"**Generated:** {now.strftime('%H:%M:%S')}",
        "",
        "## Jr Executor (24h)",
        f"- Completed: {jr.get('completed_24h', 0)}",
        f"- Failed: {jr.get('failed_24h', 0)}",
        f"- Pending: {jr.get('pending', 0)}",
        f"- In-progress: {jr.get('in_progress', 0)}",
        f"- Stale (reaper candidates): {pulse.get('stale_tasks', 0)}",
        "",
        f"## DLQ Depth: {pulse.get('dlq_depth', 0)}",
        "",
        f"## Council Votes (24h): {pulse.get('council_votes_24h', 0)}",
        "",
        "## Kanban",
    ]
    for status, cnt in pulse.get("kanban", {}).items():
        lines.append(f"- {status}: {cnt}")

    lines.extend([
        "",
        f"## Thermal Memories: {pulse.get('thermal_memories', 0):,}",
    ])

    if upcoming_events:
        lines.append("")
        lines.append("## Commemorative Calendar")
        for event in upcoming_events:
            name = event.get("event_name", "")
            years = event.get("years_ago", 0)
            ago = f"({years} year{'s' if years != 1 else ''} ago)" if years > 0 else "(this year)"
            lines.append(f"- **{name}** {ago}")

    lines.extend([
        "",
        "---",
        f"*Dawn Mist — Five Waters Tier 1 — {now.strftime('%Y-%m-%d')}*",
    ])
    return "\n".join(lines)


def run_ritual(mode="weekly"):
>>>>>>> REPLACE

---

## Step 3: Add daily mode handling in run_ritual

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
    conn = get_db_connection()
    try:
        # GATHER
        logger.info("GATHER — Reading behavioral patterns")
=======
    conn = get_db_connection()
    try:
        # === DAILY DAWN MIST (fast path — no pattern review) ===
        if mode == "daily":
            logger.info("DAWN MIST — Lightweight pulse check")
            pulse = gather_dawn_mist(conn)
            upcoming_events = check_commemorative_dates(conn, days_ahead=3)
            digest_content = generate_dawn_mist_digest(pulse, upcoming_events)

            dawn_mist_path = "/ganuda/docs/dawn_mist.md"
            os.makedirs(os.path.dirname(dawn_mist_path), exist_ok=True)
            with open(dawn_mist_path, "w") as f:
                f.write(digest_content)

            logger.info(f"Dawn Mist digest written to {dawn_mist_path}")
            logger.info(f"  Jr 24h: {pulse['jr_tasks'].get('completed_24h', 0)} completed, "
                         f"{pulse['jr_tasks'].get('failed_24h', 0)} failed")
            logger.info(f"  DLQ depth: {pulse['dlq_depth']}")
            logger.info(f"  Stale tasks: {pulse['stale_tasks']}")

            return {
                "mode": "daily",
                "pulse": pulse,
                "digest_path": dawn_mist_path
            }

        # GATHER
        logger.info("GATHER — Reading behavioral patterns")
>>>>>>> REPLACE

---

## Step 4: Update lookback days to include daily

File: `/ganuda/scripts/ritual_review.py`

<<<<<<< SEARCH
        days_lookback = {"weekly": 7, "monthly": 30, "seasonal": 90, "green-corn": 365}
=======
        days_lookback = {"daily": 1, "weekly": 7, "monthly": 30, "seasonal": 90, "green-corn": 365}
>>>>>>> REPLACE

---

## Verification

Run the daily mode manually:
```text
cd /ganuda/scripts && python3 ritual_review.py --mode daily
```

Expected: Dawn Mist digest written to `/ganuda/docs/dawn_mist.md` with Jr stats, DLQ depth, kanban snapshot, and any upcoming commemorative events.

---

## What This Does NOT Do

- Does NOT deploy systemd timers (Phase 3, TPM-direct)
- Does NOT add Telegram integration (Phase 4)
- Does NOT modify weekly/monthly/seasonal modes (already working)
- Does NOT call any LLM endpoints
