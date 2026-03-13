#!/usr/bin/env python3
"""
Stats Keeper — Auto-refresh ganuda.us landing page numbers.

Queries live counts from PostgreSQL, updates ONLY the numeric values
in the landing page HTML, writes the result back to web_content.

Jr Task #1263 — Council vote #bc1de267de3dc86d.

WRITE CONSTRAINT (Coyote binding): This script writes ONLY to the
web_content table. All other tables are READ-ONLY.
"""

import os
import re
import sys
import hashlib
import psycopg2

# --- Constants ---
FEDERATION_NODE_COUNT = 8  # redfin, bluefin, greenfin, bmasass, owlfin, eaglefin, sasass, sasass2

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def load_secrets():
    """Load DB password from secrets.env if not already in environment."""
    global DB_PASS
    if DB_PASS:
        return
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ[m.group(1)] = m.group(2)
        DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
    except FileNotFoundError:
        pass


def get_connection():
    """Get a psycopg2 connection to the federation database."""
    return psycopg2.connect(
        host=DB_HOST, port=5432, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def query_stats(conn):
    """Query live stats from database. READ-ONLY."""
    cur = conn.cursor()
    stats = {}

    # Thermal memory count
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    stats["thermal_count"] = cur.fetchone()[0]

    # Council vote count
    cur.execute("SELECT COUNT(*) FROM council_votes")
    stats["vote_count"] = cur.fetchone()[0]

    # Completed Jr tasks
    cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed'")
    stats["task_count"] = cur.fetchone()[0]

    cur.close()
    return stats


def format_thermal(count):
    """Format thermal count as 'XXK+' (e.g., 93412 -> '93K+')."""
    return f"{count // 1000}K+"


def format_number(count):
    """Format number with commas (e.g., 8860 -> '8,860')."""
    return f"{count:,}"


def read_landing_page(conn):
    """Read current /index.html from web_content. READ-ONLY."""
    cur = conn.cursor()
    cur.execute("SELECT content FROM web_content WHERE path = '/index.html' AND site = 'ganuda.us'")
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return row[0]


def update_stats_in_html(html, stats):
    """
    Replace stat numbers in the landing page HTML.

    Targets the 'By the Numbers' stat grid:
      <div class="num">92K+</div><div class="label">Thermal Memories</div>
      <div class="num">8,860</div><div class="label">Council Votes</div>
      <div class="num">917</div><div class="label">Tasks Shipped</div>

    Also updates the prose paragraph references to keep them consistent.

    Returns (updated_html, changes_made) or (None, []) if patterns not found.
    """
    thermal_fmt = format_thermal(stats["thermal_count"])
    vote_fmt = format_number(stats["vote_count"])
    task_fmt = format_number(stats["task_count"])

    changes = []
    updated = html

    # --- Stat grid replacements (precise patterns with label context) ---

    # Thermal Memories stat
    pattern = r'(<div class="num">)[^<]+(</div><div class="label">Thermal Memories</div>)'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, rf'\g<1>{thermal_fmt}\2', updated)
        changes.append(f"thermal stat: {match.group(0).split('</div>')[0].split('>')[1]} -> {thermal_fmt}")
    else:
        print("WARNING: Could not find Thermal Memories stat pattern", file=sys.stderr)

    # Council Votes stat
    pattern = r'(<div class="num">)[^<]+(</div><div class="label">Council Votes</div>)'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, rf'\g<1>{vote_fmt}\2', updated)
        changes.append(f"vote stat: {match.group(0).split('</div>')[0].split('>')[1]} -> {vote_fmt}")
    else:
        print("WARNING: Could not find Council Votes stat pattern", file=sys.stderr)

    # Tasks Shipped stat
    pattern = r'(<div class="num">)[^<]+(</div><div class="label">Tasks Shipped</div>)'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, rf'\g<1>{task_fmt}\2', updated)
        changes.append(f"task stat: {match.group(0).split('</div>')[0].split('>')[1]} -> {task_fmt}")
    else:
        print("WARNING: Could not find Tasks Shipped stat pattern", file=sys.stderr)

    # --- Prose paragraph updates ---
    # "shipped over 900 tasks" -> "shipped over X tasks"
    task_round = (stats["task_count"] // 100) * 100  # round down to nearest hundred
    pattern = r'shipped over [\d,]+ tasks'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, f'shipped over {task_round:,} tasks', updated)
        changes.append(f"prose tasks: {match.group(0)} -> shipped over {task_round:,} tasks")

    # "held 8,800+ governance votes" -> "held X+ governance votes"
    vote_round = (stats["vote_count"] // 100) * 100
    pattern = r'held [\d,]+\+ governance votes'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, f'held {vote_round:,}+ governance votes', updated)
        changes.append(f"prose votes: {match.group(0)} -> held {vote_round:,}+ governance votes")

    # "accumulated 92,000+ persistent memories" -> "accumulated X+ persistent memories"
    thermal_round = (stats["thermal_count"] // 1000) * 1000
    pattern = r'accumulated [\d,]+\+ persistent memories'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, f'accumulated {thermal_round:,}+ persistent memories', updated)
        changes.append(f"prose thermals: {match.group(0)} -> accumulated {thermal_round:,}+ persistent memories")

    # "92,000+ memories" in the Thermal Memory pillar description
    pattern = r'[\d,]+\+ memories with temperature-based'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, f'{thermal_round:,}+ memories with temperature-based', updated)
        changes.append(f"pillar thermals: updated to {thermal_round:,}+")

    # "over 900 tasks autonomously" in the Autonomous Task pillar
    pattern = r'shipped over [\d,]+ tasks autonomously'
    match = re.search(pattern, updated)
    if match:
        updated = re.sub(pattern, f'shipped over {task_round:,} tasks autonomously', updated)
        changes.append(f"pillar tasks: updated to over {task_round:,}")

    if not changes:
        print("ERROR: No stat patterns matched in the HTML. Aborting update.", file=sys.stderr)
        return None, []

    return updated, changes


def write_landing_page(conn, html):
    """Write updated HTML back to web_content. ONLY table we write to."""
    content_hash = hashlib.sha256(html.encode()).hexdigest()
    cur = conn.cursor()
    cur.execute(
        "UPDATE web_content SET content = %s, content_hash = %s, updated_at = NOW() "
        "WHERE path = '/index.html' AND site = 'ganuda.us'",
        (html, content_hash)
    )
    rows = cur.rowcount
    conn.commit()
    cur.close()
    return rows


def main():
    load_secrets()

    if not DB_PASS:
        print("ERROR: No database password available (set CHEROKEE_DB_PASS or provide secrets.env)", file=sys.stderr)
        sys.exit(1)

    try:
        conn = get_connection()
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Query live stats
        stats = query_stats(conn)

        # Step 2: Read current landing page
        html = read_landing_page(conn)
        if not html:
            print("ERROR: No /index.html found in web_content table", file=sys.stderr)
            sys.exit(1)

        # Step 3-4: Update stats in HTML
        updated_html, changes = update_stats_in_html(html, stats)
        if updated_html is None:
            sys.exit(1)

        # Check if anything actually changed
        if updated_html == html:
            print(f"Stats unchanged: {stats['thermal_count']} thermals, "
                  f"{stats['vote_count']} votes, {stats['task_count']} tasks — no update needed")
            sys.exit(0)

        # Step 5: Write back
        rows = write_landing_page(conn, updated_html)
        if rows == 0:
            print("ERROR: UPDATE affected 0 rows — web_content row may be missing", file=sys.stderr)
            sys.exit(1)

        # Step 6: Summary
        print(f"Stats updated: {stats['thermal_count']} thermals, "
              f"{stats['vote_count']} votes, {stats['task_count']} tasks")
        for change in changes:
            print(f"  {change}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
