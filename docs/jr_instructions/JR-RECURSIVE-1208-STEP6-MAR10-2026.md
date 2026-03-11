# [RECURSIVE] Status Page: Unified Organism Activity Timeline - Step 6

**Parent Task**: #1208
**Auto-decomposed**: 2026-03-10T07:20:17.122581
**Original Step Title**: Create a systemd timer (optional but recommended)

---

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
