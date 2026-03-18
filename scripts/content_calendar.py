#!/usr/bin/env python3
"""
Content Calendar Query Tool — Deer's Substack Pipeline
Cherokee AI Federation | Jr Task #1437

Reads /ganuda/config/content_calendar.json and reports on upcoming content.
Called from dawn mist to remind Deer about publishing deadlines.

Usage:
    python3 scripts/content_calendar.py [next|all|overdue]

    next     - Show the next item to publish (default)
    all      - Show all calendar entries
    overdue  - Show items past their target date that aren't published
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path

CALENDAR_PATH = Path("/ganuda/config/content_calendar.json")


def load_calendar():
    """Load the content calendar JSON."""
    if not CALENDAR_PATH.exists():
        print(f"ERROR: Calendar not found at {CALENDAR_PATH}")
        sys.exit(1)
    with open(CALENDAR_PATH) as f:
        return json.load(f)


def get_target_date(entry):
    """Extract the relevant date from a calendar entry."""
    date_str = entry.get("target_date") or entry.get("published_date")
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    return None


def days_until(target):
    """Return days until target date. Negative means overdue."""
    if target is None:
        return None
    return (target - date.today()).days


def format_entry(entry, verbose=False):
    """Format a single calendar entry for display."""
    title = entry["title"]
    status = entry["status"].upper()
    target = get_target_date(entry)
    delta = days_until(target)

    lines = [f"  Title:  {title}"]
    lines.append(f"  Status: {status}")

    if entry.get("published_date"):
        lines.append(f"  Published: {entry['published_date']}")
    if entry.get("target_date"):
        if delta is not None:
            if delta < 0:
                lines.append(f"  Target: {entry['target_date']}  ({abs(delta)} days OVERDUE)")
            elif delta == 0:
                lines.append(f"  Target: {entry['target_date']}  (TODAY)")
            else:
                lines.append(f"  Target: {entry['target_date']}  ({delta} days away)")
        else:
            lines.append(f"  Target: {entry['target_date']}")

    if entry.get("source_url"):
        lines.append(f"  Source: {entry['source_url']}")
    if entry.get("substack_url"):
        lines.append(f"  Substack: {entry['substack_url']}")
    if entry.get("notes"):
        lines.append(f"  Notes: {entry['notes']}")

    return "\n".join(lines)


def cmd_next(calendar):
    """Show the next item to publish."""
    entries = calendar["calendar"]
    upcoming = [e for e in entries if e["status"] != "published"]

    if not upcoming:
        print("All content is published. Time to add more to the calendar.")
        return

    # Sort by target date, entries without dates go last
    upcoming.sort(key=lambda e: get_target_date(e) or date.max)
    nxt = upcoming[0]
    target = get_target_date(nxt)
    delta = days_until(target)

    print(f"NEXT UP for {calendar['publication']}:")
    print(format_entry(nxt))
    print()

    if delta is not None and delta <= 2:
        print("  ** DEADLINE APPROACHING — time to finalize and publish **")
    if delta is not None and delta < 0:
        print("  ** OVERDUE — publish or reschedule **")

    # Show pipeline depth
    scheduled = len([e for e in entries if e["status"] == "scheduled"])
    planned = len([e for e in entries if e["status"] == "planned"])
    print(f"\n  Pipeline: {scheduled} scheduled, {planned} planned")


def cmd_all(calendar):
    """Show all calendar entries."""
    entries = calendar["calendar"]
    pub = calendar["publication"]
    cadence = calendar["cadence"]

    published = [e for e in entries if e["status"] == "published"]
    upcoming = [e for e in entries if e["status"] != "published"]
    upcoming.sort(key=lambda e: get_target_date(e) or date.max)

    print(f"CONTENT CALENDAR: {pub} ({cadence})")
    print(f"{'=' * 60}")

    if published:
        print(f"\nPUBLISHED ({len(published)}):")
        for e in published:
            print(format_entry(e))
            print()

    if upcoming:
        print(f"UPCOMING ({len(upcoming)}):")
        for e in upcoming:
            print(format_entry(e))
            print()


def cmd_overdue(calendar):
    """Show items past their target date that aren't published."""
    entries = calendar["calendar"]
    today = date.today()

    overdue = []
    for e in entries:
        if e["status"] == "published":
            continue
        target = get_target_date(e)
        if target and target < today:
            overdue.append(e)

    if not overdue:
        print("No overdue items. Deer is on schedule.")
        return

    print(f"OVERDUE ITEMS ({len(overdue)}):")
    print(f"{'=' * 60}")
    for e in overdue:
        print(format_entry(e))
        print()


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "next"
    calendar = load_calendar()

    commands = {
        "next": cmd_next,
        "all": cmd_all,
        "overdue": cmd_overdue,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Usage: {sys.argv[0]} [next|all|overdue]")
        sys.exit(1)

    commands[command](calendar)


if __name__ == "__main__":
    main()
