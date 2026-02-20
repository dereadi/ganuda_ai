# Jr Instruction: Kanban Board Lifecycle Automation & Cleanup

**Task ID:** KANBAN-LIFECYCLE-001
**Priority:** P2
**Date:** February 8, 2026
**Node:** redfin (192.168.132.223) — API/frontend, bluefin (192.168.132.222) — database
**Assigned:** Software Engineer Jr.
**Council Vote:** Strategic review #753ecd19 (Feb 8, 2026) identified kanban hygiene as critical gap

## Overview

The visual kanban board (`/ganuda/pathfinder/qdad-apps/visual-kanban/`) has served us well for task visualization, but tickets aren't progressing through full lifecycles. We have 40 "In Progress" tickets stuck since October, 21 inconsistent status values, no GitHub sync, and no epic-level tracking. This instruction addresses all of these.

## Current Architecture

```
SAG Unified Interface (port 4000)
  └── kanban_integration.py → KanbanClient
        └── dual-write: duyuktv_tickets (bluefin) + kanban_tasks (redfin spoke)

Visual Kanban Board
  ├── Backend API (port 5000) — /ganuda/pathfinder/qdad-apps/visual-kanban/backend/api.py
  ├── WebSocket (port 8765) — /ganuda/pathfinder/qdad-apps/visual-kanban/backend/websocket.py
  └── Frontend (port 8002) — /ganuda/pathfinder/qdad-apps/visual-kanban/frontend/
```

Database: `zammad_production` on bluefin, table `duyuktv_tickets` (primary), `kanban_tasks` on redfin spoke (federation copy).

## Phase 1: Status Normalization

### Problem
21 different status values across the system: `backlog`, `planning`, `in_progress`, `active`, `in_review`, `completed`, `done`, `closed`, `resolved`, `blocked`, `open`, `new`, `To Do`, `In Progress`, `Backlog`, `Planning`, etc. The frontend already normalizes some of these in `kanban.js`, but the backend doesn't — so database queries return inconsistent data.

### Step 1.1: Define canonical statuses

| Canonical Status | Maps From | Kanban Column |
|-----------------|-----------|---------------|
| `backlog` | backlog, Backlog | Backlog |
| `todo` | open, new, planning, Planning, To Do | Todo |
| `in_progress` | in_progress, In Progress, active | In Progress |
| `in_review` | in_review, In Review | In Progress (tagged) |
| `completed` | completed, done, closed, resolved, Completed | Completed |
| `blocked` | blocked, Blocked | Blocked (new column) |

### Step 1.2: Migration script

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/migrations/001_normalize_statuses.sql`

```sql
-- Normalize statuses in duyuktv_tickets
BEGIN;

-- Map all variants to canonical values
UPDATE duyuktv_tickets SET status = 'backlog' WHERE status IN ('Backlog');
UPDATE duyuktv_tickets SET status = 'todo' WHERE status IN ('open', 'new', 'planning', 'Planning', 'To Do');
UPDATE duyuktv_tickets SET status = 'in_progress' WHERE status IN ('In Progress', 'active');
UPDATE duyuktv_tickets SET status = 'in_review' WHERE status IN ('In Review');
UPDATE duyuktv_tickets SET status = 'completed' WHERE status IN ('done', 'closed', 'resolved', 'Completed');
UPDATE duyuktv_tickets SET status = 'blocked' WHERE status IN ('Blocked');

-- Add constraint to prevent future inconsistency
ALTER TABLE duyuktv_tickets ADD CONSTRAINT chk_valid_status
    CHECK (status IN ('backlog', 'todo', 'in_progress', 'in_review', 'completed', 'blocked'));

COMMIT;
```

Run on bluefin:
```bash
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h localhost -U claude -d zammad_production -f /ganuda/pathfinder/qdad-apps/visual-kanban/migrations/001_normalize_statuses.sql
```

### Step 1.3: Update backend API

In `/ganuda/pathfinder/qdad-apps/visual-kanban/backend/api.py`, add status validation to the `PUT /tickets/<id>` endpoint:

```python
VALID_STATUSES = {'backlog', 'todo', 'in_progress', 'in_review', 'completed', 'blocked'}

@app.route('/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    data = request.json
    new_status = data.get('status', '').lower().strip()
    if new_status not in VALID_STATUSES:
        return jsonify({'error': f'Invalid status: {new_status}. Valid: {VALID_STATUSES}'}), 400
    # ... existing update logic
```

## Phase 2: Stale Ticket Automation

### Problem
40 tickets in "In Progress" since October 2025. No automated detection or escalation.

### Step 2.1: Add staleness detection to API

Add new endpoint to `api.py`:

```python
@app.route('/tickets/stale', methods=['GET'])
def get_stale_tickets():
    """Return tickets in_progress for more than 14 days without updates."""
    threshold_days = request.args.get('days', 14, type=int)
    # Query tickets where status = 'in_progress' AND updated_at < now() - threshold_days
    # Return list with age_days, title, tribal_agent
```

### Step 2.2: Create automation script

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/scripts/kanban_hygiene.py`

This script runs daily (via cron or systemd timer) and:

1. **Identifies stale tickets** — `in_progress` for >14 days with no updates
2. **Moves ancient tickets** — `in_progress` for >60 days → `blocked` with note "Auto-blocked: no updates for 60+ days"
3. **Identifies orphaned tickets** — `todo` with no `tribal_agent` assigned for >30 days → flag for council review
4. **Reports** — Writes daily hygiene report to thermal_memory_archive

```python
#!/usr/bin/env python3
"""Kanban board hygiene automation.
Runs daily to detect stale tickets, auto-block ancient ones, and report.
"""
import psycopg2
import datetime
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'dbname': 'zammad_production',
    'user': 'claude',
    # Read password from secrets.env or environment
}

STALE_THRESHOLD_DAYS = 14
AUTO_BLOCK_THRESHOLD_DAYS = 60
ORPHAN_THRESHOLD_DAYS = 30

def get_password():
    """Read DB password from /ganuda/config/secrets.env"""
    import os
    # Try environment first
    pw = os.environ.get('GANUDA_DB_PASSWORD')
    if pw:
        return pw
    # Fall back to secrets.env
    try:
        with open('/ganuda/config/secrets.env') as f:
            for line in f:
                if line.startswith('GANUDA_DB_PASSWORD='):
                    return line.strip().split('=', 1)[1]
    except FileNotFoundError:
        pass
    raise RuntimeError("No database password found")

def run_hygiene():
    DB_CONFIG['password'] = get_password()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    now = datetime.datetime.now()

    # 1. Find stale tickets
    cur.execute("""
        SELECT id, title, tribal_agent, updated_at,
               EXTRACT(DAY FROM now() - updated_at) as age_days
        FROM duyuktv_tickets
        WHERE status = 'in_progress'
          AND updated_at < now() - interval '%s days'
        ORDER BY updated_at ASC
    """, (STALE_THRESHOLD_DAYS,))
    stale = cur.fetchall()

    # 2. Auto-block ancient tickets
    cur.execute("""
        UPDATE duyuktv_tickets
        SET status = 'blocked',
            description = description || E'\n\n[AUTO-BLOCKED ' || now()::date || ': No updates for 60+ days]'
        WHERE status = 'in_progress'
          AND updated_at < now() - interval '%s days'
        RETURNING id, title
    """, (AUTO_BLOCK_THRESHOLD_DAYS,))
    auto_blocked = cur.fetchall()

    # 3. Find orphaned tickets
    cur.execute("""
        SELECT id, title, created_at,
               EXTRACT(DAY FROM now() - created_at) as age_days
        FROM duyuktv_tickets
        WHERE status = 'todo'
          AND (tribal_agent IS NULL OR tribal_agent = '')
          AND created_at < now() - interval '%s days'
        ORDER BY created_at ASC
    """, (ORPHAN_THRESHOLD_DAYS,))
    orphans = cur.fetchall()

    conn.commit()

    # 4. Report
    report = {
        'date': now.isoformat(),
        'stale_count': len(stale),
        'auto_blocked_count': len(auto_blocked),
        'orphan_count': len(orphans),
        'auto_blocked_ids': [r[0] for r in auto_blocked],
    }
    print(json.dumps(report, indent=2))

    conn.close()
    return report

if __name__ == '__main__':
    run_hygiene()
```

### Step 2.3: Systemd timer

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/scripts/kanban-hygiene.timer`

```ini
[Unit]
Description=Daily kanban hygiene check

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/scripts/kanban-hygiene.service`

```ini
[Unit]
Description=Kanban board hygiene automation

[Service]
Type=oneshot
ExecStart=/ganuda/pathfinder/qdad-apps/visual-kanban/venv/bin/python3 /ganuda/pathfinder/qdad-apps/visual-kanban/scripts/kanban_hygiene.py
EnvironmentFile=/ganuda/config/secrets.env
WorkingDirectory=/ganuda/pathfinder/qdad-apps/visual-kanban
```

Deploy on redfin:
```bash
sudo cp kanban-hygiene.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kanban-hygiene.timer
```

## Phase 3: Epic Lifecycle Tracking

### Problem
Stories are logged individually but never grouped into epics. Epics never show as "completed" even when all child stories are done.

### Step 3.1: Add epic support to database

```sql
-- Add epic tracking columns to duyuktv_tickets
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS epic_id VARCHAR(50);
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS ticket_type VARCHAR(20) DEFAULT 'story';
-- ticket_type: 'epic', 'story', 'task', 'bug'

-- Create index for epic grouping
CREATE INDEX IF NOT EXISTS idx_duyuktv_epic ON duyuktv_tickets(epic_id) WHERE epic_id IS NOT NULL;

-- Add constraint
ALTER TABLE duyuktv_tickets ADD CONSTRAINT chk_ticket_type
    CHECK (ticket_type IN ('epic', 'story', 'task', 'bug'));
```

### Step 3.2: Add epic endpoints to API

In `api.py`, add:

```python
@app.route('/epics', methods=['GET'])
def get_epics():
    """Return all epics with child story counts and completion percentage."""
    # Query all tickets where ticket_type = 'epic'
    # For each, count children (WHERE epic_id = epic.id)
    # Calculate: total, completed, percentage

@app.route('/epics/<epic_id>/complete', methods=['POST'])
def auto_complete_epic(epic_id):
    """Auto-complete an epic if all child stories are completed."""
    # Count children not in 'completed' status
    # If 0 remaining, move epic to 'completed'
```

### Step 3.3: Add epic view to frontend

In `kanban.js`, add an epic grouping toggle:

- Default view: flat ticket list (current behavior)
- Epic view: grouped by epic_id, with progress bar showing % complete
- Epic cards show: title, child count, completion percentage, Sacred Fire total

In `index.html`, add toggle button:
```html
<button id="epicToggle" onclick="kanban.toggleEpicView()">View: Stories | Epics</button>
```

## Phase 4: GitHub Sync

### Problem
We track work in the kanban board AND in GitHub Projects, but there's no sync between them. Work gets logged in one but not the other.

### Step 4.1: GitHub webhook receiver

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/backend/github_sync.py`

```python
"""GitHub ↔ Kanban sync via webhooks and API."""
import hmac
import hashlib
from flask import Blueprint, request, jsonify

github_bp = Blueprint('github', __name__)

# GitHub status → Kanban status mapping
GH_STATUS_MAP = {
    'open': 'todo',
    'in_progress': 'in_progress',
    'closed': 'completed',
}

@github_bp.route('/webhook/github', methods=['POST'])
def github_webhook():
    """Receive GitHub issue/project webhooks and sync to kanban."""
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    # ... verify with HMAC

    payload = request.json
    action = payload.get('action')

    if 'issue' in payload:
        issue = payload['issue']
        # Upsert into duyuktv_tickets with github_issue_id
        # Map labels to tribal_agent
        # Map milestone to epic_id

    return jsonify({'ok': True})
```

### Step 4.2: Add GitHub columns to database

```sql
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS github_issue_id INTEGER;
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS github_repo VARCHAR(100);
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS github_url TEXT;
ALTER TABLE duyuktv_tickets ADD COLUMN IF NOT EXISTS github_synced_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_duyuktv_github ON duyuktv_tickets(github_issue_id) WHERE github_issue_id IS NOT NULL;
```

### Step 4.3: Push-to-GitHub script

**File:** `/ganuda/pathfinder/qdad-apps/visual-kanban/scripts/sync_to_github.py`

Runs on-demand or via cron to push kanban ticket updates to GitHub Issues:

```python
"""Sync kanban tickets to GitHub Issues using gh CLI."""
import subprocess
import json

def sync_ticket_to_github(ticket):
    """Create or update a GitHub issue for a kanban ticket."""
    if ticket['github_issue_id']:
        # Update existing issue
        subprocess.run(['gh', 'issue', 'edit', str(ticket['github_issue_id']),
                       '--title', ticket['title'],
                       '--repo', 'dereadi/qdad-apps'])
    else:
        # Create new issue
        result = subprocess.run(['gh', 'issue', 'create',
                               '--title', ticket['title'],
                               '--body', ticket['description'] or '',
                               '--repo', 'dereadi/qdad-apps'],
                              capture_output=True, text=True)
        # Parse issue number from output
        # Update ticket with github_issue_id
```

### Step 4.4: Configure GitHub webhook

```bash
# On the repo, set webhook to point to redfin
gh api repos/dereadi/qdad-apps/hooks --method POST \
    -f url="http://redfin-public-url/webhook/github" \
    -f content_type="json" \
    -f secret="WEBHOOK_SECRET_FROM_SECRETS_ENV"
```

**Note:** This requires either a public URL for redfin or a Tailscale Funnel. If neither is available, use polling mode instead (cron script that runs `gh issue list` periodically).

## Phase 5: Fix Operational Issues

### Step 5.1: Move logs out of /tmp

The launch script currently logs to `/tmp/visual_kanban_*.log`. These get deleted on reboot.

In `launch_visual_kanban.sh`, change:
```bash
# OLD:
# ... > /tmp/visual_kanban_api.log 2>&1 &
# NEW:
LOG_DIR="/ganuda/pathfinder/qdad-apps/visual-kanban/logs"
mkdir -p "$LOG_DIR"
# ... > "$LOG_DIR/api.log" 2>&1 &
# ... > "$LOG_DIR/websocket.log" 2>&1 &
# ... > "$LOG_DIR/frontend.log" 2>&1 &
```

### Step 5.2: Fix hardcoded DB password

In `/ganuda/home/dereadi/kanban_federation_writer.py`, the old password `jawaseatlasers2` is hardcoded. Update to read from secrets:

```python
import os

def get_db_password():
    pw = os.environ.get('GANUDA_DB_PASSWORD')
    if pw:
        return pw
    try:
        with open('/ganuda/config/secrets.env') as f:
            for line in f:
                if line.startswith('GANUDA_DB_PASSWORD='):
                    return line.strip().split('=', 1)[1]
    except FileNotFoundError:
        pass
    raise RuntimeError("No database password found")
```

Also check and update `api.py` and `websocket.py` if they have hardcoded passwords.

### Step 5.3: Add "Blocked" column to frontend

Currently the frontend only has 4 columns (Backlog, Todo, In Progress, Completed). Add a 5th "Blocked" column:

In `index.html`:
```html
<div class="kanban-column" data-status="blocked">
    <h2>Blocked</h2>
    <div class="ticket-list" id="blocked-tickets"></div>
</div>
```

Update `kanban.js` to route `blocked` tickets to this column and style them with a red-orange border.

## Phase 6: Log Recent Sprint Work

### Step 6.1: Backfill Feb 7-8 completed work

Run this SQL on bluefin to capture the sprint work we've done but haven't logged:

```sql
-- Feb 7-8 Sprint Backfill
INSERT INTO duyuktv_tickets (title, description, status, sacred_fire_priority, tribal_agent, ticket_type, created_at, updated_at) VALUES
('Persist greenfin firewall rules', 'Save nftables ruleset to /etc/nftables.conf for reboot persistence. Council concern: nftables vs iptables-nft evaluation order.', 'completed', 70, 'TPM', 'task', '2026-02-07', '2026-02-07'),
('Restart optic-nerve on bluefin', 'Restart optic-nerve service pointing to VLM adapter :8092. Verified healthy.', 'completed', 60, 'TPM', 'task', '2026-02-08', '2026-02-08'),
('Council Vote #8475: MLX vs Exo', 'Evaluate distributed Exo vs single-node MLX for 70B inference. Council approved MLX. KB: KB-MLX-VS-EXO-DISTRIBUTED-INFERENCE-FEB07-2026.md', 'completed', 80, 'Peace Chief', 'story', '2026-02-07', '2026-02-07'),
('Council Vote #8481: Hybrid 32B+70B', 'Revise MLX deployment from single 70B to hybrid: DeepSeek-R1-32B always-on + Qwen2.5-72B on-demand. Approved.', 'completed', 80, 'Peace Chief', 'story', '2026-02-08', '2026-02-08'),
('Council Vote #8476: SAG Secrets Tab', 'Custom secrets management tab in SAG with Flask-Login, bcrypt, Fernet encryption, 4-tier RBAC. Approved.', 'completed', 80, 'Peace Chief', 'story', '2026-02-08', '2026-02-08'),
('Write Jr Instruction: MLX Hybrid Deployment', 'JR-MAC-MLX-70B-INFERENCE-FEB07-2026.md (MLX-M4MAX-001). DeepSeek-R1-32B on port 8800, Qwen2.5-72B on port 8801, launchd plist.', 'completed', 70, 'TPM', 'task', '2026-02-07', '2026-02-08'),
('Write Jr Instruction: Camera Password Rotation', 'JR-CAMERA-FLEET-PASSWORD-ROTATION-FEB08-2026.md (CAM-ROTATE-001). 3 cameras, unique passwords, secrets.env + FreeIPA vault.', 'completed', 80, 'TPM', 'task', '2026-02-08', '2026-02-08'),
('Write Jr Instruction: SAG Secrets Tab', 'JR-SAG-SECRETS-MANAGEMENT-TAB-FEB08-2026.md (SAG-SECRETS-001). Database schema, auth module, secrets blueprint, seed script.', 'completed', 80, 'TPM', 'task', '2026-02-08', '2026-02-08'),
('Research: Shared LoRA Subspaces paper', 'arXiv 2602.06043 (Johns Hopkins). Evaluate for federation fine-tuning. Queued as RESEARCH-LORA-001.', 'completed', 50, 'TPM', 'story', '2026-02-08', '2026-02-08');

-- Create the Feb 7-8 sprint epic
INSERT INTO duyuktv_tickets (title, description, status, sacred_fire_priority, tribal_agent, ticket_type, created_at, updated_at) VALUES
('EPIC: Feb 7-8 Infrastructure & Security Sprint', 'Reactive sprint covering: MLX deployment pivot (single→hybrid), camera credential rotation, SAG secrets management, kanban automation, greenfin firewall persistence, optic-nerve restart. Council votes: #8475, #8476, #8481. Strategic review confirmed pattern: reactive sprint → proactive hardening.', 'in_progress', 85, 'TPM', 'epic', '2026-02-07', '2026-02-08');
```

**Note:** After epic tracking is implemented (Phase 3), link these stories to the epic via `epic_id`.

## Verification

After all phases:

1. `curl http://192.168.132.223:5000/tickets | python3 -m json.tool` — all tickets have canonical statuses
2. Frontend shows 5 columns (Backlog, Todo, In Progress, Blocked, Completed)
3. `curl http://192.168.132.223:5000/tickets/stale` — returns stale ticket report
4. `curl http://192.168.132.223:5000/epics` — returns epic list with completion percentages
5. Logs persist in `/ganuda/pathfinder/qdad-apps/visual-kanban/logs/`, not `/tmp/`
6. No hardcoded passwords in any Python file — all read from secrets.env or environment

## Rollback

Each phase has its own migration. To rollback:
- Phase 1: `ALTER TABLE duyuktv_tickets DROP CONSTRAINT chk_valid_status;`
- Phase 3: `ALTER TABLE duyuktv_tickets DROP COLUMN epic_id, DROP COLUMN ticket_type;`
- Phase 4: `ALTER TABLE duyuktv_tickets DROP COLUMN github_issue_id, github_repo, github_url, github_synced_at;`

## Priority Order

1. Phase 5 (operational fixes) — immediate, prevents data loss
2. Phase 1 (status normalization) — enables everything else
3. Phase 6 (backfill sprint work) — capture before we forget
4. Phase 2 (stale ticket automation) — daily hygiene
5. Phase 3 (epic tracking) — organizational improvement
6. Phase 4 (GitHub sync) — nice to have, implement when redfin has public endpoint or use polling

---
**FOR SEVEN GENERATIONS** — Track the work so future minds don't wonder what we did.
