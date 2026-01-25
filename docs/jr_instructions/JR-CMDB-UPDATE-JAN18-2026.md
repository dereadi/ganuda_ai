# JR Instruction: CMDB Update January 2026

## Metadata
```yaml
task_id: cmdb_update_jan18
priority: 2
assigned_to: it_triad_jr
estimated_effort: low
category: system_maintenance
```

## Overview

Update the software_cmdb table with new services deployed since December 2025.

## BACKEND LOCATION: /ganuda/scripts

## CREATE FILE: cmdb_update_jan2026.sql

## New Services to Add

### Jr Executor Components (redfin)
| Package | Version | Description |
|---------|---------|-------------|
| jr-llm-reasoner | 1.0 | LLM-based task understanding `/ganuda/lib/jr_llm_reasoner.py` |
| jr-plan-parser | 1.0 | Planning response parser `/ganuda/lib/jr_plan_parser.py` |
| jr-planning-prompt | 1.0 | Structured planning prompts `/ganuda/lib/jr_planning_prompt.py` |
| jr-queue-worker | 1.1 | Task queue processor `/ganuda/jr_executor/jr_queue_worker.py` |
| jr-task-executor | 1.1 | Task execution engine `/ganuda/jr_executor/task_executor.py` |

### VetAssist Services (redfin)
| Package | Version | Description |
|---------|---------|-------------|
| vetassist-backend | 0.1 | FastAPI backend `/ganuda/vetassist/backend/` |
| vetassist-document-api | 0.1 | Document upload API with Presidio PII |

### New Infrastructure
| Host | Package | Version | Description |
|------|---------|---------|-------------|
| goldfin | postgresql | 17 | PII Vault database |
| silverfin | freeipa | latest | Identity management |

## SQL to Execute

```sql
-- Jr Executor Components
INSERT INTO software_cmdb (hostname, package_name, version, package_type, source, install_date, last_updated, auto_update, security_critical, notes, discovered_by)
VALUES
('redfin', 'jr-llm-reasoner', '1.0', 'python', 'ganuda', '2026-01-17', NOW(), false, false, 'LLM-based task understanding module', 'cmdb_update'),
('redfin', 'jr-plan-parser', '1.0', 'python', 'ganuda', '2026-01-17', NOW(), false, false, 'Devika-style planning response parser', 'cmdb_update'),
('redfin', 'jr-planning-prompt', '1.0', 'python', 'ganuda', '2026-01-17', NOW(), false, false, 'Structured planning prompt templates', 'cmdb_update'),
('redfin', 'jr-queue-worker', '1.1', 'python', 'ganuda', '2026-01-14', NOW(), false, false, 'Task queue worker with M-GRPO learning', 'cmdb_update'),
('redfin', 'jr-task-executor', '1.1', 'python', 'ganuda', '2026-01-14', NOW(), false, false, 'Task executor with prose-to-code support', 'cmdb_update')
ON CONFLICT (hostname, package_name) DO UPDATE SET
  version = EXCLUDED.version,
  last_updated = NOW(),
  notes = EXCLUDED.notes;

-- VetAssist Services
INSERT INTO software_cmdb (hostname, package_name, version, package_type, source, install_date, last_updated, auto_update, security_critical, notes, discovered_by)
VALUES
('redfin', 'vetassist-backend', '0.1', 'python', 'ganuda', '2026-01-18', NOW(), false, true, 'VetAssist FastAPI backend with Presidio PII detection', 'cmdb_update'),
('redfin', 'vetassist-document-api', '0.1', 'python', 'ganuda', '2026-01-18', NOW(), false, true, 'Document upload API endpoint', 'cmdb_update')
ON CONFLICT (hostname, package_name) DO UPDATE SET
  version = EXCLUDED.version,
  last_updated = NOW(),
  notes = EXCLUDED.notes;

-- New Infrastructure Nodes
INSERT INTO software_cmdb (hostname, package_name, version, package_type, source, install_date, last_updated, auto_update, security_critical, notes, discovered_by)
VALUES
('goldfin', 'postgresql', '17', 'system', 'rocky', '2026-01-16', NOW(), true, true, 'PII Vault database for VetAssist', 'cmdb_update'),
('silverfin', 'freeipa-server', 'latest', 'system', 'rocky', '2026-01-16', NOW(), true, true, 'Cherokee AI Federation identity management', 'cmdb_update')
ON CONFLICT (hostname, package_name) DO UPDATE SET
  version = EXCLUDED.version,
  last_updated = NOW(),
  notes = EXCLUDED.notes;

-- Verify updates
SELECT hostname, package_name, version, last_updated::date
FROM software_cmdb
WHERE discovered_by = 'cmdb_update' OR last_updated > '2026-01-17'
ORDER BY hostname, package_name;
```

## Success Criteria

1. New services added to software_cmdb
2. Existing entries updated with current versions
3. No duplicate entries (ON CONFLICT handles this)

## Testing

Run the SQL file:
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/scripts/cmdb_update_jan2026.sql
```

---
Cherokee AI Federation - For Seven Generations
