# JR Instruction: RLM Thermal Memory Bootstrap (FIXED FORMAT)
## Task ID: RLM-BOOTSTRAP-002
## Priority: P1
## Approved: TPM Direct

---

## Objective

Create Python module and shell script for TPM context persistence across Claude Code sessions. Queries thermal_memory_archive and generates CLAUDE.md bootstrap section.

---

## Implementation

### Step 1: Create the Bootstrap Module

Create `/ganuda/lib/rlm_bootstrap.py`:

```python
#!/usr/bin/env python3
"""
RLM Thermal Memory Bootstrap
Cherokee AI Federation - January 2026

Bootstraps TPM context from thermal_memory_archive for session continuity.
"""

import psycopg2
from datetime import datetime
from typing import List, Dict

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
        SELECT original_content, memory_type, metadata, created_at,
               temperature_score, sacred_pattern
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '%s hours'
        AND (metadata->>'role' = 'tpm'
             OR metadata->>'type' IN ('system_prompt_update', 'council_decision')
             OR sacred_pattern = true)
        ORDER BY sacred_pattern DESC, temperature_score DESC, created_at DESC
        LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (hours, limit))
            cols = ['content', 'type', 'metadata', 'created_at', 'temperature', 'sacred']
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_active_tasks(self) -> List[Dict]:
        """Get pending/in-progress JR tasks."""
        query = """
        SELECT title, status, priority, assigned_jr, created_at::date
        FROM jr_work_queue
        WHERE status IN ('pending', 'in_progress', 'assigned')
        ORDER BY priority, created_at DESC LIMIT 10
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            cols = ['title', 'status', 'priority', 'assigned_jr', 'created']
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_failed_tasks(self) -> List[Dict]:
        """Get failed JR tasks needing attention."""
        query = """
        SELECT title, LEFT(error_message, 80) as error, created_at::date
        FROM jr_work_queue WHERE status = 'failed'
        ORDER BY created_at DESC LIMIT 10
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            cols = ['title', 'error', 'created']
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_stats(self) -> Dict:
        """Get current federation stats."""
        query = """
        SELECT
            (SELECT COUNT(*) FROM thermal_memory_archive) as memories,
            (SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed') as completed,
            (SELECT COUNT(*) FROM jr_work_queue WHERE status = 'failed') as failed,
            (SELECT COUNT(*) FROM duyuktv_tickets WHERE status IN ('open', 'backlog')) as kanban,
            (SELECT COUNT(*) FROM vetassist_cfr_conditions) as cfr
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            return {'memories': row[0], 'jr_completed': row[1], 'jr_failed': row[2],
                    'kanban_open': row[3], 'cfr_conditions': row[4]}

    def generate_bootstrap_context(self) -> str:
        """Generate full bootstrap context for CLAUDE.md."""
        stats = self.get_stats()
        memories = self.get_recent_memories()
        failed = self.get_failed_tasks()

        out = []
        out.append("## RLM Bootstrap Context")
        out.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        out.append("")
        out.append("### Federation Stats")
        out.append(f"- Thermal Memories: {stats['memories']:,}")
        out.append(f"- JR Tasks: {stats['jr_completed']} done, {stats['jr_failed']} failed")
        out.append(f"- Kanban Open: {stats['kanban_open']}")
        out.append(f"- CFR Conditions: {stats['cfr_conditions']}")
        out.append("")

        if failed:
            out.append("### Failed Tasks (Need Attention)")
            for t in failed[:5]:
                out.append(f"- **{t['title']}**: {t['error']}")
            out.append("")

        sacred = [m for m in memories if m.get('sacred')]
        if sacred:
            out.append("### Key Context (Sacred Memories)")
            for m in sacred[:5]:
                content = (m['content'] or '')[:100]
                out.append(f"- {content}...")
            out.append("")

        out.append("## End RLM Bootstrap")
        return "\n".join(out)


def main():
    """Generate and print bootstrap context."""
    bootstrap = ThermalBootstrap()
    try:
        print(bootstrap.generate_bootstrap_context())
    finally:
        bootstrap.close()


if __name__ == "__main__":
    main()
```

### Step 2: Create the CLAUDE.md Updater Script

Create `/ganuda/scripts/update_claude_context.sh`:

```bash
#!/bin/bash
# Update CLAUDE.md with RLM bootstrap context
# Cherokee AI Federation

CLAUDE_MD="$HOME/.claude/CLAUDE.md"
BOOTSTRAP="/ganuda/lib/rlm_bootstrap.py"
VENV="/ganuda/vetassist/backend/venv/bin/python3"
MARKER_START="## RLM Bootstrap Context"
MARKER_END="## End RLM Bootstrap"

# Generate new context
NEW_CONTEXT=$($VENV "$BOOTSTRAP" 2>/dev/null)

if [ -z "$NEW_CONTEXT" ]; then
    echo "Warning: Could not generate bootstrap context"
    exit 1
fi

# Create CLAUDE.md if missing
if [ ! -f "$CLAUDE_MD" ]; then
    mkdir -p "$(dirname "$CLAUDE_MD")"
    echo "$NEW_CONTEXT" > "$CLAUDE_MD"
    exit 0
fi

# Remove old bootstrap section if exists
if grep -q "$MARKER_START" "$CLAUDE_MD"; then
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$CLAUDE_MD"
fi

# Prepend new context
TEMP=$(mktemp)
echo "$NEW_CONTEXT" > "$TEMP"
echo "" >> "$TEMP"
cat "$CLAUDE_MD" >> "$TEMP"
mv "$TEMP" "$CLAUDE_MD"

echo "CLAUDE.md updated with fresh bootstrap context"
```

---

## Verification

```bash
# Test bootstrap module
/ganuda/vetassist/backend/venv/bin/python3 /ganuda/lib/rlm_bootstrap.py

# Make script executable and test
chmod +x /ganuda/scripts/update_claude_context.sh
/ganuda/scripts/update_claude_context.sh

# Verify CLAUDE.md updated
head -30 ~/.claude/CLAUDE.md
```

---

## Acceptance Criteria

1. rlm_bootstrap.py executes without errors
2. Bootstrap context includes stats, failed tasks, sacred memories
3. update_claude_context.sh updates CLAUDE.md correctly
4. Context generation completes in less than 5 seconds

---

*Cherokee AI Federation - For Seven Generations*
