# JR Instruction: RLM Thermal Memory Bootstrap (Option A)
## Task ID: RLM-BOOTSTRAP-001
## Priority: P1
## Estimated Complexity: Medium
## Approved: TPM Direct

---

## Objective

Implement Option A: Thermal Memory Bootstrap for TPM context persistence. Create a Python module that queries thermal_memory_archive on session start and generates a context summary for CLAUDE.md.

---

## Implementation

### Step 1: Create the Bootstrap Module

Create file `/ganuda/lib/rlm_bootstrap.py`:

```python
#!/usr/bin/env python3
"""
RLM Thermal Memory Bootstrap
Cherokee AI Federation - January 2026

Bootstraps TPM context from thermal_memory_archive for session continuity.
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

class ThermalBootstrap:
    """Bootstrap TPM context from thermal memory."""

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)

    def close(self):
        if self.conn:
            self.conn.close()

    def get_recent_memories(self, hours: int = 24, limit: int = 30) -> List[Dict]:
        """Get recent TPM-relevant memories."""
        query = """
        SELECT
            original_content,
            memory_type,
            metadata,
            created_at,
            temperature_score,
            sacred_pattern
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '%s hours'
        AND (
            metadata->>'role' = 'tpm'
            OR metadata->>'type' IN ('system_prompt_update', 'council_decision', 'jr_task', 'deployment')
            OR sacred_pattern = true
        )
        ORDER BY
            sacred_pattern DESC,
            temperature_score DESC,
            created_at DESC
        LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (hours, limit))
            columns = ['content', 'type', 'metadata', 'created_at', 'temperature', 'sacred']
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_active_tasks(self) -> List[Dict]:
        """Get pending/in-progress JR tasks."""
        query = """
        SELECT title, status, priority, assigned_jr, created_at::date
        FROM jr_work_queue
        WHERE status IN ('pending', 'in_progress', 'assigned')
        ORDER BY priority, created_at DESC
        LIMIT 10
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            columns = ['title', 'status', 'priority', 'assigned_jr', 'created']
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_recent_council_votes(self, limit: int = 5) -> List[Dict]:
        """Get recent council decisions."""
        query = """
        SELECT
            LEFT(question, 100) as question,
            recommendation,
            confidence,
            concern_count,
            tpm_vote,
            voted_at::date
        FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '7 days'
        ORDER BY voted_at DESC
        LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (limit,))
            columns = ['question', 'recommendation', 'confidence', 'concerns', 'tpm_vote', 'date']
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_failed_tasks(self) -> List[Dict]:
        """Get failed JR tasks needing attention."""
        query = """
        SELECT title, LEFT(error_message, 80) as error, created_at::date
        FROM jr_work_queue
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 10
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            columns = ['title', 'error', 'created']
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_stats(self) -> Dict:
        """Get current federation stats."""
        query = """
        SELECT
            (SELECT COUNT(*) FROM thermal_memory_archive) as memories,
            (SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed') as jr_completed,
            (SELECT COUNT(*) FROM jr_work_queue WHERE status = 'failed') as jr_failed,
            (SELECT COUNT(*) FROM jr_work_queue WHERE status IN ('pending', 'in_progress')) as jr_active,
            (SELECT COUNT(*) FROM duyuktv_tickets WHERE status IN ('open', 'backlog', 'in_progress')) as kanban_open,
            (SELECT COUNT(*) FROM vetassist_cfr_conditions) as cfr_conditions
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            return {
                'memories': row[0],
                'jr_completed': row[1],
                'jr_failed': row[2],
                'jr_active': row[3],
                'kanban_open': row[4],
                'cfr_conditions': row[5]
            }

    def generate_bootstrap_context(self) -> str:
        """Generate full bootstrap context for CLAUDE.md."""
        stats = self.get_stats()
        memories = self.get_recent_memories()
        tasks = self.get_active_tasks()
        failed = self.get_failed_tasks()
        votes = self.get_recent_council_votes()

        output = []
        output.append("## RLM Bootstrap Context")
        output.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        output.append("")

        # Stats summary
        output.append("### Federation Stats")
        output.append(f"- Thermal Memories: {stats['memories']:,}")
        output.append(f"- JR Tasks: {stats['jr_completed']} completed, {stats['jr_failed']} failed, {stats['jr_active']} active")
        output.append(f"- Kanban Open: {stats['kanban_open']}")
        output.append(f"- CFR Conditions: {stats['cfr_conditions']}")
        output.append("")

        # Failed tasks (priority)
        if failed:
            output.append("### Failed Tasks (Need Attention)")
            for t in failed[:5]:
                output.append(f"- **{t['title']}**: {t['error']}")
            output.append("")

        # Active tasks
        if tasks:
            output.append("### Active JR Tasks")
            for t in tasks[:5]:
                output.append(f"- [{t['status']}] P{t['priority']}: {t['title']}")
            output.append("")

        # Recent council votes
        if votes:
            output.append("### Recent Council Decisions")
            for v in votes[:3]:
                output.append(f"- {v['question'][:60]}... → {v['recommendation']} ({v['tpm_vote']})")
            output.append("")

        # Sacred memories
        sacred = [m for m in memories if m.get('sacred')]
        if sacred:
            output.append("### Key Context (Sacred Memories)")
            for m in sacred[:5]:
                content = m['content'][:150] if m['content'] else ''
                output.append(f"- {content}...")
            output.append("")

        return "\n".join(output)


def main():
    """Generate and print bootstrap context."""
    bootstrap = ThermalBootstrap()
    try:
        context = bootstrap.generate_bootstrap_context()
        print(context)
    finally:
        bootstrap.close()


if __name__ == "__main__":
    main()
```

### Step 2: Create the CLAUDE.md Updater Script

Create file `/ganuda/scripts/update_claude_context.sh`:

```bash
#!/bin/bash
# Update CLAUDE.md with RLM bootstrap context
# Cherokee AI Federation

CLAUDE_MD="$HOME/.claude/CLAUDE.md"
BOOTSTRAP_SCRIPT="/ganuda/lib/rlm_bootstrap.py"
MARKER_START="## RLM Bootstrap Context"
MARKER_END="## End RLM Bootstrap"

# Generate new context
NEW_CONTEXT=$(/ganuda/vetassist/backend/venv/bin/python3 "$BOOTSTRAP_SCRIPT" 2>/dev/null)

if [ -z "$NEW_CONTEXT" ]; then
    echo "Warning: Could not generate bootstrap context"
    exit 1
fi

# Check if CLAUDE.md exists
if [ ! -f "$CLAUDE_MD" ]; then
    echo "Creating new CLAUDE.md"
    echo "$NEW_CONTEXT" > "$CLAUDE_MD"
    echo "" >> "$CLAUDE_MD"
    echo "$MARKER_END" >> "$CLAUDE_MD"
    exit 0
fi

# Remove old bootstrap section if exists
if grep -q "$MARKER_START" "$CLAUDE_MD"; then
    # Remove from marker to end marker (or end of file)
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$CLAUDE_MD"
fi

# Prepend new context
TEMP_FILE=$(mktemp)
echo "$NEW_CONTEXT" > "$TEMP_FILE"
echo "" >> "$TEMP_FILE"
echo "$MARKER_END" >> "$TEMP_FILE"
echo "" >> "$TEMP_FILE"
cat "$CLAUDE_MD" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$CLAUDE_MD"

echo "CLAUDE.md updated with fresh bootstrap context"
```

### Step 3: Create Systemd Timer for Auto-Refresh

Create file `/ganuda/scripts/systemd/rlm-bootstrap.service`:

```ini
[Unit]
Description=RLM Bootstrap Context Generator
After=network.target

[Service]
Type=oneshot
User=dereadi
ExecStart=/ganuda/scripts/update_claude_context.sh
StandardOutput=journal
StandardError=journal
```

Create file `/ganuda/scripts/systemd/rlm-bootstrap.timer`:

```ini
[Unit]
Description=Run RLM Bootstrap every 30 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

### Step 4: Test the Bootstrap

```bash
# Test the Python module directly
cd /ganuda
python3 lib/rlm_bootstrap.py

# Expected output: Markdown formatted context summary
```

---

## Verification Commands

```bash
# 1. Test bootstrap module
/ganuda/vetassist/backend/venv/bin/python3 /ganuda/lib/rlm_bootstrap.py

# 2. Test CLAUDE.md updater
chmod +x /ganuda/scripts/update_claude_context.sh
/ganuda/scripts/update_claude_context.sh

# 3. Check CLAUDE.md was updated
head -50 ~/.claude/CLAUDE.md

# 4. Verify database connectivity
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) FROM thermal_memory_archive;"
```

---

## Acceptance Criteria

1. [ ] `rlm_bootstrap.py` executes without errors
2. [ ] Bootstrap context includes: stats, failed tasks, active tasks, council votes
3. [ ] `update_claude_context.sh` updates CLAUDE.md correctly
4. [ ] Context generation completes in <5 seconds
5. [ ] No PII exposed in bootstrap output

---

## Fallback Plan

If Option A fails, implement Option C (simple shell-based):

```bash
# Fallback: Direct psql to CLAUDE.md
echo "## Recent TPM Context" >> ~/.claude/CLAUDE.md
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -t -c "
SELECT '- ' || LEFT(original_content, 100)
FROM thermal_memory_archive
WHERE metadata->>'role' = 'tpm'
ORDER BY created_at DESC
LIMIT 10;
" >> ~/.claude/CLAUDE.md
```

---

*Cherokee AI Federation - For Seven Generations*
