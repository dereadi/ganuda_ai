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
        SELECT id, created_at, temperature_score,
               LEFT(original_content, 120) as summary
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '48 hours'
          AND temperature_score < 95
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
        SELECT vote_id, voted_at, audit_hash, confidence, recommendation
        FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '7 days'
        ORDER BY voted_at DESC
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
        SELECT id, created_at, LEFT(original_content, 120) as summary
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%fire guard%%'
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
        SELECT id, created_at, LEFT(original_content, 120) as summary
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%dawn mist%%'
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