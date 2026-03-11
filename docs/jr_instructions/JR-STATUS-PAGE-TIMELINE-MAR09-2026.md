# Jr Instruction: Status Page — Unified Organism Activity Timeline

**Task #1208**
**Date:** 2026-03-09
**Priority:** 2 (Visible to external users — ganuda.us/status.html)
**TPM:** Claude Opus

## Context

The current status page at ganuda.us/status.html shows "Recently Completed" Jr tasks. When no tasks complete recently, the page looks hung — like the organism is dead. In reality, the federation is constantly active: thermal memories being written, council votes being cast, fire guard running every 2 minutes, dawn mist generating daily. We need a unified activity timeline that shows the organism is alive and breathing, even when no Jr tasks are completing.

## CRITICAL: Database Schema Reference

Use these EXACT column/table names (do NOT guess):
- **council_votes**: vote_id (PK), audit_hash, question, recommendation, confidence, voted_at
- **jr_work_queue**: id, title, status, created_at, updated_at, completed_at
- **thermal_memory_archive**: id, original_content (NOT "content"), temperature_score (NOT "temperature"), created_at, memory_hash, sacred_pattern, domain_tag
- **web_content**: site, path, content, content_type, content_hash, published, updated_at, created_by
- There is NO table called "longhouse_votes" — use council_votes
- For fire guard/dawn mist events: query thermal_memory_archive WHERE original_content ILIKE '%fire guard%' or '%dawn mist%'

## Task

Create a script at `/ganuda/scripts/status_page_activity.py` that queries multiple tables from the bluefin DB, generates a unified chronological activity timeline as HTML, and publishes it via the web_content pipeline. Use `/ganuda/scripts/publish_web_content.py` as the reference pattern for DB connection and publishing.

## Steps

### Step 1: Create the activity timeline script

Create `/ganuda/scripts/status_page_activity.py` with the following content:

```python
#!/usr/bin/env python3
"""Status Page Activity Timeline — Cherokee AI Federation

Generates a unified organism activity timeline for ganuda.us/status.html.
Queries thermal memories, council votes, fire guard checks, dawn mist reports,
and Jr task status changes. Publishes via web_content pipeline.

Task #1208. Run from redfin via systemd timer or cron.

Usage:
    python3 /ganuda/scripts/status_page_activity.py
    python3 /ganuda/scripts/status_page_activity.py --dry-run   # print HTML, don't publish
"""

import os
import sys
import hashlib
from datetime import datetime

import psycopg2
import psycopg2.extras


# --- DB Config ---
def load_secrets():
    secrets = {}
    secrets_path = '/ganuda/config/secrets.env'
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    secrets[k.strip()] = v.strip()
    return secrets


secrets = load_secrets()

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": secrets.get("CHEROKEE_DB_PASS", ""),
}

SITE = "ganuda.us"
TIMELINE_PATH = "/status-activity.html"
MAX_EVENTS = 50


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_recent_thermals(cur, limit=10):
    """Fetch recent thermal memory writes (excluding PII/SACRED content)."""
    cur.execute("""
        SELECT id, created_at, temperature,
               LEFT(content, 120) as summary
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '48 hours'
          AND temperature < 95
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    events = []
    for row in cur.fetchall():
        events.append({
            "time": row[1],
            "type": "thermal",
            "icon": "&#x1f321;",
            "label": "Thermal Memory",
            "detail": f"#{row[0]} (temp {row[2]}) — {row[3]}..." if row[3] else f"#{row[0]} (temp {row[2]})",
        })
    return events


def fetch_recent_votes(cur, limit=10):
    """Fetch recent Longhouse council votes."""
    cur.execute("""
        SELECT id, created_at, audit_hash, confidence, result
        FROM longhouse_votes
        WHERE created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    events = []
    for row in cur.fetchall():
        hash_short = row[2][:12] if row[2] else "unknown"
        result_str = row[4] if row[4] else "pending"
        events.append({
            "time": row[1],
            "type": "vote",
            "icon": "&#x1f3db;",
            "label": "Council Vote",
            "detail": f"{hash_short} — {result_str} (conf {row[3]:.2f})" if row[3] else f"{hash_short} — {result_str}",
        })
    return events


def fetch_recent_jr_tasks(cur, limit=10):
    """Fetch recent Jr task status changes."""
    cur.execute("""
        SELECT id, updated_at, title, status
        FROM jr_work_queue
        WHERE updated_at > NOW() - INTERVAL '7 days'
        ORDER BY updated_at DESC
        LIMIT %s
    """, (limit,))
    events = []
    status_icons = {
        "completed": "&#x2705;",
        "failed": "&#x274c;",
        "in_progress": "&#x1f504;",
        "pending": "&#x23f3;",
    }
    for row in cur.fetchall():
        status = row[3] if row[3] else "unknown"
        icon = status_icons.get(status, "&#x2022;")
        title = row[2][:80] if row[2] else f"Task #{row[0]}"
        events.append({
            "time": row[1],
            "type": "jr_task",
            "icon": icon,
            "label": f"Jr Task ({status})",
            "detail": title,
        })
    return events


def fetch_fire_guard_events(cur, limit=5):
    """Fetch recent fire guard activity from thermal memory."""
    cur.execute("""
        SELECT id, created_at, LEFT(content, 120) as summary
        FROM thermal_memory_archive
        WHERE content ILIKE '%%fire guard%%'
          AND created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    events = []
    for row in cur.fetchall():
        events.append({
            "time": row[1],
            "type": "fire_guard",
            "icon": "&#x1f525;",
            "label": "Fire Guard",
            "detail": row[2] if row[2] else "Health check completed",
        })
    return events


def fetch_dawn_mist_events(cur, limit=3):
    """Fetch recent dawn mist reports from thermal memory."""
    cur.execute("""
        SELECT id, created_at, LEFT(content, 120) as summary
        FROM thermal_memory_archive
        WHERE content ILIKE '%%dawn mist%%'
          AND created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    events = []
    for row in cur.fetchall():
        events.append({
            "time": row[1],
            "type": "dawn_mist",
            "icon": "&#x1f305;",
            "label": "Dawn Mist",
            "detail": row[2] if row[2] else "Daily standup generated",
        })
    return events


def sanitize_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def generate_timeline_html(events):
    """Generate HTML fragment for the activity timeline."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M CT")

    # Sort all events by time, most recent first
    events.sort(key=lambda e: e["time"] if e["time"] else datetime.min, reverse=True)
    events = events[:MAX_EVENTS]

    rows = []
    for evt in events:
        time_str = evt["time"].strftime("%b %d %H:%M") if evt["time"] else "Unknown"
        detail = sanitize_html(evt.get("detail", ""))
        type_class = evt.get("type", "unknown")
        rows.append(
            f'<tr class="activity-{type_class}">'
            f'<td class="activity-time">{time_str}</td>'
            f'<td class="activity-icon">{evt["icon"]}</td>'
            f'<td class="activity-label">{sanitize_html(evt["label"])}</td>'
            f'<td class="activity-detail">{detail}</td>'
            f'</tr>'
        )

    if not rows:
        rows.append(
            '<tr><td colspan="4" style="text-align:center;color:#888;">'
            'No recent activity found.</td></tr>'
        )

    table_rows = "\n    ".join(rows)

    html = f"""<div class="activity-timeline">
  <h3>Federation Activity <span class="activity-updated">Updated: {now}</span></h3>
  <table class="activity-table">
    <thead>
      <tr>
        <th>Time</th>
        <th></th>
        <th>Source</th>
        <th>Detail</th>
      </tr>
    </thead>
    <tbody>
    {table_rows}
    </tbody>
  </table>
  <style>
    .activity-timeline {{ margin: 1.5em 0; }}
    .activity-timeline h3 {{ font-size: 1.1em; margin-bottom: 0.5em; }}
    .activity-updated {{ font-size: 0.75em; color: #888; font-weight: normal; }}
    .activity-table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
    .activity-table th {{ text-align: left; border-bottom: 2px solid #ddd; padding: 0.4em 0.6em; }}
    .activity-table td {{ padding: 0.3em 0.6em; border-bottom: 1px solid #eee; }}
    .activity-time {{ white-space: nowrap; color: #666; font-family: monospace; }}
    .activity-icon {{ text-align: center; }}
    .activity-detail {{ max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .activity-thermal td {{ background: #fffbf0; }}
    .activity-vote td {{ background: #f0f4ff; }}
    .activity-fire_guard td {{ background: #fff0f0; }}
    .activity-dawn_mist td {{ background: #f0fff4; }}
  </style>
</div>"""
    return html


def publish_timeline(html_content):
    """Publish timeline HTML to web_content table."""
    conn = get_connection()
    cur = conn.cursor()
    content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
    try:
        cur.execute("""
            INSERT INTO web_content (site, path, content_type, content, content_hash, created_by)
            VALUES (%s, %s, 'text/html', %s, %s, 'status-activity')
            ON CONFLICT (site, path) DO UPDATE SET
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                updated_at = NOW()
        """, (SITE, TIMELINE_PATH, html_content, content_hash))
        conn.commit()
        print(f"Published timeline to {SITE}{TIMELINE_PATH} ({len(html_content)} bytes)")
    finally:
        cur.close()
        conn.close()


def main():
    dry_run = '--dry-run' in sys.argv

    conn = get_connection()
    cur = conn.cursor()

    try:
        all_events = []
        all_events.extend(fetch_recent_thermals(cur))
        all_events.extend(fetch_recent_votes(cur))
        all_events.extend(fetch_recent_jr_tasks(cur))
        all_events.extend(fetch_fire_guard_events(cur))
        all_events.extend(fetch_dawn_mist_events(cur))
    finally:
        cur.close()
        conn.close()

    html = generate_timeline_html(all_events)

    if dry_run:
        print(html)
        print(f"\n--- DRY RUN: {len(all_events)} events, {len(html)} bytes HTML ---")
    else:
        publish_timeline(html)


if __name__ == "__main__":
    main()
```

### Step 2: Make the script executable

```bash
chmod +x /ganuda/scripts/status_page_activity.py
```

### Step 3: Test with dry run

```bash
python3 /ganuda/scripts/status_page_activity.py --dry-run
```

Verify that HTML output contains events from multiple sources (thermals, votes, tasks, fire guard, dawn mist) merged into one chronological timeline.

### Step 4: Publish the timeline

```bash
python3 /ganuda/scripts/status_page_activity.py
```

### Step 5: Wire into status page

The existing status page at ganuda.us/status.html needs to include this timeline fragment. Either:
- Option A: Modify the status page generator to fetch and embed the `/status-activity.html` content
- Option B: Use JavaScript `fetch('/status-activity.html')` to load the timeline dynamically
- Option C: Have the materializer on owlfin/eaglefin compose the final page from fragments

Choose the approach that fits the existing materializer pattern. The timeline publishes as a separate web_content entry at `/status-activity.html` so it can be updated independently (every 15 minutes via timer) without rebuilding the full status page.

### Step 6: Create a systemd timer (optional but recommended)

Create a timer to refresh the timeline every 15 minutes:

Timer unit: `status-activity.timer`
Service unit: `status-activity.service`
ExecStart: `/usr/bin/python3 /ganuda/scripts/status_page_activity.py`
OnCalendar: `*:0/15` (every 15 minutes)

Deploy via FreeIPA sudo pattern on redfin.

## Acceptance Criteria

- Script exists at `/ganuda/scripts/status_page_activity.py` and is executable
- Script queries 5 data sources: thermal memories, council votes, Jr tasks, fire guard, dawn mist
- All events are merged into one chronological timeline (most recent first)
- Output is valid HTML with inline CSS (no external dependencies)
- `--dry-run` flag prints HTML to stdout without publishing
- Normal run publishes to web_content table at path `/status-activity.html`
- HTML sanitization prevents XSS from thermal memory content
- Script handles empty result sets gracefully (shows "No recent activity" message)
- SACRED thermals (temperature >= 95) are excluded from the timeline
- Script uses credentials from `/ganuda/config/secrets.env`

## Constraints

- Read DB credentials from `/ganuda/config/secrets.env` — do NOT hardcode passwords
- Do NOT expose SACRED thermal content (temperature >= 95) on the public status page
- Do NOT include PII or full thermal content — truncate to 120 chars max
- Do NOT modify the existing status page generator — publish as a separate web_content entry
- Use the same DB connection pattern as `/ganuda/scripts/publish_web_content.py`
- HTML must be self-contained (inline CSS, no external JS/CSS dependencies)
- Timeline should show max 50 events to keep page load reasonable
- No dependencies beyond psycopg2 (already installed on redfin)
