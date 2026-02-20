# KB: Kanban Board Lifecycle Gaps & Remediation Plan

**Created:** 2026-02-08
**Author:** TPM (Claude Opus 4.6)
**Category:** Process Improvement / ITSM

## Problem Statement

The Cherokee AI Federation kanban board has significant lifecycle management gaps discovered during strategic review on Feb 8, 2026.

## Findings

### By the Numbers
- **21 different status values** across duyuktv_tickets (should be 6)
- **40 tickets stuck in "In Progress"** since October 2025 (4+ months)
- **324 completed tickets** — none with epic grouping
- **114 open tickets** — unclear how many are still relevant
- **0 epics** have gone through full lifecycle (planned → completed)
- **0 GitHub issues** synced to kanban board

### Root Causes
1. **No status validation** — backend accepts any string as status
2. **No staleness detection** — tickets rot in "in_progress" indefinitely
3. **No epic model** — stories never roll up into tracked initiatives
4. **Manual only** — no automation for ticket lifecycle transitions
5. **Logs in /tmp** — kanban service logs deleted on every reboot
6. **Hardcoded credentials** — `jawaseatlasers2` (old, rotated password) in kanban_federation_writer.py

### Architecture (Current)
```
/ganuda/pathfinder/qdad-apps/visual-kanban/
├── backend/api.py         — Flask REST API (port 5000)
├── backend/websocket.py   — Real-time updates (port 8765)
├── frontend/              — HTML/JS/CSS (port 8002)
└── launch_visual_kanban.sh — Launcher (logs to /tmp!)

/ganuda/home/dereadi/
├── kanban_federation_writer.py — Dual-write (hardcoded old password!)
├── kanban_integration.py       — SAG ↔ Kanban integration
└── consult_triad_kanban.py     — Triad consultation
```

## Remediation

Jr Instruction: `JR-KANBAN-LIFECYCLE-AUTOMATION-FEB08-2026.md` (KANBAN-LIFECYCLE-001)

6 phases in priority order:
1. **Operational fixes** — move logs from /tmp, fix hardcoded passwords
2. **Status normalization** — 21 → 6 canonical statuses with DB constraint
3. **Backfill sprint work** — log Feb 7-8 sprint (9 completed tasks, 1 epic)
4. **Stale ticket automation** — daily hygiene script via systemd timer
5. **Epic lifecycle tracking** — epic_id column, completion percentage endpoints
6. **GitHub sync** — webhook receiver + polling fallback

## Key Learnings

1. **Never log to /tmp on production services** — use /ganuda/logs/ or service-specific log dir
2. **Validate status values at the database level** — CHECK constraint prevents drift
3. **Stale tickets = invisible waste** — automate detection, don't rely on human review
4. **Epic tracking is organizational memory** — without it, we don't know what initiatives we've completed
5. **Dual-write patterns need password rotation awareness** — when secrets rotate, ALL consumers must update

## Avoid These Mistakes

- Don't add new status values without updating the CHECK constraint
- Don't hardcode DB passwords in Python files — always use secrets_loader or environment
- Don't rely on frontend normalization alone — backend must enforce canonical values
- Don't skip logging completed work — if it's not in the kanban, it didn't happen (for process purposes)

---
**FOR SEVEN GENERATIONS** — Track the work. Document the patterns. Automate the hygiene.
