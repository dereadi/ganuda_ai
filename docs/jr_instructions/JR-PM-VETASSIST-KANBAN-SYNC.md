# Jr Instructions: VetAssist Kanban Board Sync

**Task ID**: PM-KANBAN-SYNC-001
**Priority**: HIGH
**Target**: bluefin (PostgreSQL) + redfin (SAG UI)
**Assigned To**: PM Jr (or Executive Jr if PM Jr not available)
**Frequency**: Daily at 06:00 CST
**Council Approval**: Part of VetAssist project governance

---

## Executive Summary

Maintain the kanban board at http://192.168.132.223:3001 with current VetAssist project status. Sync thermal_memory entries with kanban tickets to ensure visibility.

**Problem Solved**: 8 Jr instructions exist but are not tracked. Blockers not visible. No project tracking.

---

## Step 1: Create VetAssist Epic in Kanban

### Database Insert (zammad_production on bluefin)

```sql
-- Connect to bluefin PostgreSQL
-- Database: zammad_production

-- Create VetAssist epic ticket
INSERT INTO kanban_ticket_log (
    ticket_id,
    title,
    description,
    status,
    priority,
    specialist,
    sacred_fire_priority,
    temperature_zone,
    epic,
    tags
) VALUES (
    'VETASSIST-EPIC-001',
    'VetAssist MVP - Veteran Disability Claims Assistant',
    'AI-powered claims assistance tool enabling veterans to file disability claims independently. Council approved 5-0-2 on 2025-12-28.',
    'in_progress',
    9,
    'TPM',
    9,
    'HOT',
    'VetAssist MVP',
    ARRAY['vetassist', 'mvp', 'veteran', 'claims']
);
```

---

## Step 2: Create Cards for Each Jr Instruction

### Generate Kanban Cards from Jr Instructions

```python
#!/usr/bin/env python3
"""
PM Jr: Sync Jr instructions to kanban board
Run on bluefin or any node with psql access
"""

import subprocess
import json
from datetime import datetime

JR_INSTRUCTIONS = [
    {
        "id": "VETASSIST-COND-001",
        "title": "Condition Database (400+ conditions)",
        "file": "JR-VetAssist-Condition-Database.md",
        "target": "bluefin/redfin",
        "status": "ready",
        "priority": 8,
        "depends_on": None
    },
    {
        "id": "VETASSIST-CALC-001",
        "title": "Combined Rating Calculator (38 CFR 4.25)",
        "file": "JR-VetAssist-Rating-Calculator.md",
        "target": "redfin",
        "status": "ready",
        "priority": 8,
        "depends_on": None
    },
    {
        "id": "VETASSIST-EVID-001",
        "title": "Evidence Checklist System",
        "file": "JR-VetAssist-Evidence-Checklist.md",
        "target": "bluefin/redfin",
        "status": "ready",
        "priority": 8,
        "depends_on": "VETASSIST-COND-001"
    },
    {
        "id": "VETASSIST-API-001",
        "title": "VetAssist API Integration",
        "file": "JR-VETASSIST-API-INTEGRATION-JAN9-2026.md",
        "target": "redfin",
        "status": "blocked",
        "priority": 7,
        "depends_on": "VETASSIST-EVID-001"
    },
    {
        "id": "VETASSIST-PII-001",
        "title": "PII Database on goldfin",
        "file": "vetassist_pii_database_jr.md",
        "target": "goldfin",
        "status": "blocked",
        "priority": 9,
        "depends_on": "FreeIPA domain join"
    },
    {
        "id": "VETASSIST-SEC-001",
        "title": "Goldfin Security Architecture",
        "file": "JR-Goldfin-Security-Architecture.md",
        "target": "goldfin",
        "status": "ready",
        "priority": 9,
        "depends_on": None
    },
    {
        "id": "VETASSIST-UI-001",
        "title": "VetAssist Web UI",
        "file": "Not created yet",
        "target": "redfin",
        "status": "not_started",
        "priority": 6,
        "depends_on": "VETASSIST-API-001"
    },
    {
        "id": "VETASSIST-STMT-001",
        "title": "Personal Statement Builder",
        "file": "Not created yet",
        "target": "redfin/goldfin",
        "status": "not_started",
        "priority": 7,
        "depends_on": "VETASSIST-PII-001"
    }
]

def generate_insert_sql(task):
    """Generate SQL INSERT for kanban_ticket_log"""
    return f"""
INSERT INTO kanban_ticket_log (
    ticket_id, title, description, status, priority,
    specialist, sacred_fire_priority, temperature_zone,
    epic, tags
) VALUES (
    '{task["id"]}',
    '{task["title"]}',
    'Jr Instructions: {task["file"]}. Target: {task["target"]}. Depends on: {task["depends_on"] or "None"}',
    '{task["status"]}',
    {task["priority"]},
    'IT_Jr',
    {task["priority"]},
    'HOT',
    'VetAssist MVP',
    ARRAY['vetassist', 'jr-instruction', '{task["target"].split("/")[0]}']
) ON CONFLICT (ticket_id) DO UPDATE SET
    status = EXCLUDED.status,
    updated_at = NOW();
"""

# Generate all SQL
for task in JR_INSTRUCTIONS:
    print(generate_insert_sql(task))
```

---

## Step 3: Sync Blocker Status

### Check for Blockers and Update Kanban

```sql
-- Mark tasks as blocked if dependencies not complete
UPDATE kanban_ticket_log
SET status = 'blocked',
    description = description || E'\n\nBLOCKER: vLLM service down on redfin'
WHERE epic = 'VetAssist MVP'
  AND status = 'ready'
  AND title LIKE '%API%';

-- Mark PII tasks blocked by FreeIPA
UPDATE kanban_ticket_log
SET status = 'blocked',
    description = description || E'\n\nBLOCKER: FreeIPA domain join required'
WHERE epic = 'VetAssist MVP'
  AND ticket_id = 'VETASSIST-PII-001';
```

---

## Step 4: Report Status to Thermal Memory

### Write Daily Status to thermal_memory

```sql
INSERT INTO triad_shared_memories (
    content, temperature, source_triad, tags, access_level
) VALUES (
    'PM Jr Daily Status Report - ' || TO_CHAR(NOW(), 'YYYY-MM-DD') || E'\n\n' ||
    'VetAssist Project:\n' ||
    '- Total Jr Instructions: 8\n' ||
    '- Ready: ' || (SELECT COUNT(*) FROM kanban_ticket_log WHERE epic = 'VetAssist MVP' AND status = 'ready') || E'\n' ||
    '- Blocked: ' || (SELECT COUNT(*) FROM kanban_ticket_log WHERE epic = 'VetAssist MVP' AND status = 'blocked') || E'\n' ||
    '- Completed: ' || (SELECT COUNT(*) FROM kanban_ticket_log WHERE epic = 'VetAssist MVP' AND status = 'completed') || E'\n\n' ||
    'Blockers: vLLM down, FreeIPA domain join pending\n\n' ||
    'For Seven Generations.',
    85,
    'pm_jr',
    ARRAY['status', 'vetassist', 'daily-report'],
    'federation'
);
```

---

## Step 5: Escalate Blockers

### If Blocker Persists > 24 Hours

Write to thermal_memory with temperature 95+ and tag 'escalation':

```sql
INSERT INTO triad_shared_memories (
    content, temperature, source_triad, tags, access_level
) VALUES (
    'ESCALATION: vLLM Down > 24 Hours - VetAssist Blocked',
    95,
    'pm_jr',
    ARRAY['escalation', 'blocker', 'vllm', 'vetassist'],
    'federation'
);
```

Optionally send Telegram alert if telegram_bot configured.

---

## Execution Schedule

| Time | Action |
|------|--------|
| 06:00 | Run kanban sync |
| 06:05 | Check blocker status |
| 06:10 | Write daily report to thermal_memory |
| 12:00 | Mid-day blocker check |
| 18:00 | Evening status update |

---

## Success Criteria

- [ ] VetAssist epic exists in kanban
- [ ] All 8 Jr instructions have kanban cards
- [ ] Blocked status correctly reflects blockers
- [ ] Daily status in thermal_memory
- [ ] Escalations sent for blockers > 24 hours

---

*For Seven Generations*
