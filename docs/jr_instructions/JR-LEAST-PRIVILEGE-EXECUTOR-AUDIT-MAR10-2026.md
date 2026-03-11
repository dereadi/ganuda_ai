# JR INSTRUCTION: Least-Privilege Jr Executor Security Audit

**Task**: Audit the Jr executor system for privilege escalation risks — report only, no changes
**Priority**: P1 — security
**Date**: 2026-03-10
**TPM**: Claude Opus
**Kanban**: #2079
**Story Points**: 5

## Problem Statement

The Jr executor is the system that picks up tasks from `jr_work_queue` and executes them autonomously. It runs code, writes files, and interacts with the database. We need to understand exactly what privileges it has, where the boundaries are (or aren't), and what an adversarial or buggy task could do.

This is an audit. You are NOT making changes. You are documenting the current state and recommending fixes.

## Audit Scope

### 1. Filesystem Access

Investigate what filesystem paths the Jr executor can write to.

Questions to answer:
- What user does the Jr executor process run as? (Check systemd service file, `ps aux`, `whoami` in executor context)
- What is the working directory?
- Are there any path restrictions (chroot, apparmor, seccomp)?
- Can a Jr task write to `/etc/`, `/ganuda/config/`, `/ganuda/lib/`, or other sensitive paths?
- Can a Jr task write to other users' home directories?
- Can a Jr task overwrite its own executor code (`jr_executor/task_executor.py`)?

### 2. Database Permissions

Investigate the DB privileges of the user the executor connects as.

Questions to answer:
- What PostgreSQL user does the executor use? (Check connection string in `jr_queue_client.py`)
- What tables can that user SELECT from?
- What tables can that user INSERT/UPDATE/DELETE on?
- Can that user CREATE or DROP tables?
- Can that user access `thermal_memory_archive`, `council_votes`, `web_content`, or other sensitive tables?
- Is there any row-level security?

To check, connect to PostgreSQL on 192.168.132.222:5432 (db: zammad_production) and run:
```sql
-- Check grants for the executor's DB user
SELECT grantee, table_name, privilege_type
FROM information_schema.table_privileges
WHERE grantee = '<executor_db_user>';

-- Check if the user has superuser or createdb
SELECT usename, usesuper, usecreatedb FROM pg_user WHERE usename = '<executor_db_user>';
```

### 3. Shell Command Execution

Investigate whether Jr tasks can execute arbitrary shell commands.

Questions to answer:
- Does `task_executor.py` use `subprocess`, `os.system`, `exec()`, `eval()`, or similar?
- If yes, what inputs control the command? (Task description? Step content? External data?)
- Is there any sandboxing, allowlisting, or input validation?
- Can a Jr task install Python packages (`pip install`)?
- Can a Jr task make network requests to arbitrary hosts?

### 4. Process Privileges

Questions to answer:
- Does the executor run as root?
- Does the executor have sudo access? (Check FreeIPA rules for the executor's user)
- Is there a systemd `DynamicUser`, `ProtectSystem`, `PrivateTmp`, or other hardening?
- What capabilities does the process have? (`getpcaps`, `/proc/PID/status`)

### 5. Credential Exposure

Questions to answer:
- Are there hardcoded credentials in `task_executor.py`, `jr_queue_client.py`, or related files?
- Does the executor have access to `secrets.env`?
- Can a Jr task read other services' credentials?
- Are API keys (Telegram, Slack, etc.) accessible from the executor context?

## Target Files to Audit

- `/ganuda/jr_executor/task_executor.py` — main executor logic
- `/ganuda/jr_executor/jr_queue_client.py` — DB client for task queue
- `/ganuda/jr_executor/telegram_notify.py` — notification integration
- `/etc/systemd/system/jr-se.service` (or similar) — systemd unit file
- `/ganuda/config/secrets.env` — credential file (check permissions, not contents)
- Any other files imported by the executor

## Output Format

Write findings to: `/ganuda/docs/security/AUDIT-JR-EXECUTOR-PRIVILEGES-MAR2026.md`

Structure the report as:

```markdown
# Jr Executor Security Audit — March 2026

## Executive Summary
[2-3 sentences: overall risk level, biggest finding]

## Findings

### 1. Filesystem Access
**Risk**: [HIGH/MEDIUM/LOW]
[Details, evidence, file paths]

### 2. Database Permissions
**Risk**: [HIGH/MEDIUM/LOW]
[Details, SQL query results]

### 3. Shell Command Execution
**Risk**: [HIGH/MEDIUM/LOW]
[Details, code references]

### 4. Process Privileges
**Risk**: [HIGH/MEDIUM/LOW]
[Details, systemd config]

### 5. Credential Exposure
**Risk**: [HIGH/MEDIUM/LOW]
[Details, file permissions]

## Recommendations
[Numbered list of specific, actionable changes with file paths and code snippets]

## Appendix
[Raw query output, ps output, file permission listings]
```

## Constraints

- **AUDIT ONLY — DO NOT MAKE CHANGES.** No code modifications, no config changes, no DB alterations.
- Do NOT print or log actual credential values — report their existence and accessibility only
- Do NOT attempt to exploit any vulnerability — report and document only
- Do NOT connect to external services as part of the audit
- Run read-only queries only against PostgreSQL

## Files to Read Before Starting

- `/ganuda/jr_executor/task_executor.py` — the main executor
- `/ganuda/jr_executor/jr_queue_client.py` — DB connection and query logic
- `/ganuda/jr_executor/telegram_notify.py` — notification subsystem
- `/ganuda/docs/jr_instructions/JR-DB-CONNECTION-HYGIENE-MAR09-2026.md` — related DB connection work

## Acceptance Criteria

- Written report exists at `/ganuda/docs/security/AUDIT-JR-EXECUTOR-PRIVILEGES-MAR2026.md`
- Report covers all 5 audit areas with risk ratings
- Report includes specific evidence (code line numbers, query results, file permissions)
- Report includes actionable recommendations
- No code or config changes were made
- Report does not contain actual credential values

## DO NOT

- Make any changes to code, config, or database
- Print, log, or include actual passwords/keys/tokens in the report
- Attempt exploitation of any finding
- Skip any of the 5 audit areas — all must be covered
- Recommend changes without specific file paths and code references
