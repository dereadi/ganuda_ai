# KB: Jr SEV1 Disarm-and-Verify Playbook — Captured From May 16-17 2026 Incident

**Filed:** 2026-05-17 ~21:15 CDT
**Author:** Stoneclad (TPM) under Partner directive
**Trigger event:** May 16 22:36 — secrets.env corrupted by Jr-stub deliverable during 8h unattended window. May 17 evening — Partner returned, saw redfin GPU busy, escalated to SEV1. Full disarm took ~3 hours; verification ~1 hour.
**Severity:** P0 playbook — covers active production-file damage by hallucinating Jr deliverables.
**Lifetime expectation:** Until FWPL Phase 1 (#2563) ships, this playbook is the operator-procedure for any recurrence.

## Why this KB exists

A SEV1 incident touched 7 production files (secrets.env twice, specialist_council.py, task_executor.py, STEM-CELL doc 40% truncated, plus ~20 Jr-stub-spam files). We solved it ad-hoc, then verified end-to-end. Capturing the playbook so the next recurrence is a 30-minute drill not a 4-hour archaeology dig.

## Incident shape (so you recognize it next time)

Symptoms in any combination:
- File on disk that you didn't write contains the literal string `# ... (rest of the code)` or similar stub placeholder
- `git status` shows modifications to config/secrets/sacred files you haven't touched in this session
- `md5sum` of secrets.env doesn't match the value documented in last-known-good audit
- Untracked files with hallucinated names (substantive content with names that don't match any task you dispatched)
- `python -c 'import lib.specialist_council'` raises `IndentationError` despite no recent code review
- `jr-executor` was running unattended for >hours with no operator oversight
- DLQ retry poller was enabled
- GPU shows utilization but no operator-initiated job is running

## Root cause (one sentence)

**DLQ retry poller resurrects damage-prone tasks → Jr produces stub deliverable that passes claim_verifier when content-mode + over-eager-code rules collide → stub gets written over production file → no FWPL pre-write hook to reject it.** The damage-prone tasks were originally created weeks ago for legitimate work that has since been done, but they live indefinitely in the DLQ and re-fire on poll.

## Disarm protocol (in order, every time)

### Step 1 — STOP all Jr surfaces immediately (do not investigate first)

```bash
ssh redfin "sudo systemctl stop jr-executor jr-orchestrator jr-queue-worker jr-dlq-retry-poller"
ssh bluefin "sudo systemctl stop jr-executor"  # if running there
```

Kill any zombie processes (the May 17 incident had a 33-day-uptime `jr-executor` outside systemd that survived `systemctl stop`):

```bash
ssh redfin "ps -ef | grep -E 'jr_|python.*executor' | grep -v grep"
# For any zombies: ssh redfin "sudo kill <PID>"
```

**Do NOT investigate first.** Every minute of investigation while Jr keeps running risks another file corrupted. Disarm is reversible; corrupted production files are not (without backups).

### Step 2 — Verify damage is stopped (5-minute MD5 watch)

```bash
# Take MD5 of every file Jr could have touched
md5sum /ganuda/config/secrets.env /ganuda/lib/specialist_council.py \
       /ganuda/jr_executor/task_executor.py /ganuda/lib/jr_plan_parser.py \
       /ganuda/jr_executor/dlq_manager.py
# Wait 5 minutes, re-take. If any MD5 changed, you missed a process.
```

### Step 3 — Identify the offender(s)

Three pattern-matches to find what Jr was doing:

```bash
# Pattern 1: recent file writes outside expected paths
find /ganuda -type f -newer /tmp/disarm-marker -not -path '*/.git/*' 2>/dev/null

# Pattern 2: DLQ entries that fired during damage window
PGPASSWORD=... psql -h 10.100.0.2 -U claude -d zammad_production -c \
  "SELECT id, original_task_id, last_retry_timestamp FROM jr_failed_tasks_dlq
   WHERE last_retry_timestamp > NOW() - INTERVAL '4 hours'
   ORDER BY last_retry_timestamp DESC LIMIT 20;"

# Pattern 3: tasks marked started during damage window
PGPASSWORD=... psql -h 10.100.0.2 -U claude -d zammad_production -c \
  "SELECT id, status, assigned_jr, started_at, LEFT(title,60) FROM jr_work_queue
   WHERE started_at > NOW() - INTERVAL '4 hours'
   ORDER BY started_at DESC LIMIT 20;"
```

### Step 4 — Cancel offenders + abandon their DLQ entries

```bash
# Cancel the offending tasks (do NOT delete — preserve for forensics)
PGPASSWORD=... psql -h 10.100.0.2 -U claude -d zammad_production -c \
  "UPDATE jr_work_queue SET status='cancelled',
     error_message='SEV1 disarm: damage-prone task, cancelled on $(date +%F)'
   WHERE id IN (1278, 1264, 1294, ...);"

# Abandon their DLQ entries
PGPASSWORD=... psql -h 10.100.0.2 -U claude -d zammad_production -c \
  "UPDATE jr_failed_tasks_dlq SET resolution_status='abandoned',
     resolution_notes='SEV1 disarm: parent task cancelled, see KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026'
   WHERE original_task_id IN (1278, 1264, 1294, ...);"
```

### Step 5 — Restore corrupted files from backups

Look for `*.backup_<timestamp>` siblings in the same directory:

```bash
ls -la /ganuda/config/*.backup* /ganuda/lib/*.backup* /ganuda/docs/architecture/*.backup*
```

Surgical restore (preferred over copy-overwrite — preserves any clean changes that arrived between corruption and restore):

```bash
# Example for secrets.env — restore only the broken section
sed -n '/^# section_start/,/^# section_end/p' \
    /ganuda/config/secrets.env.backup_20260516_222728 > /tmp/clean-section
# Then manually splice into current file
```

Preserve corrupted versions as forensics:

```bash
cp /ganuda/lib/specialist_council.py /ganuda/lib/specialist_council.py.broken-$(date +%Y%m%d-%H%M)
```

For Python files that may have transient corruption Jr would re-corrupt on restart, **stash via git** rather than rewriting in place:

```bash
git stash push -m "Jr-stub-corruption of <file> — <description> — stashed YYYY-MM-DD for TPM-inline review" <file>
```

This preserves the corruption diff in `git stash list` for forensic review without leaving the file in a broken state.

### Step 6 — Quarantine Jr-stub clutter

Don't delete — quarantine. Pattern-detect by recency + name shape:

```bash
mkdir -p /ganuda/jr_stub_quarantine_$(date +%Y%m%d)
# Move any file with stub-pattern names (truncated, partial, hallucinated)
mv /ganuda/path/to/stub-file /ganuda/jr_stub_quarantine_$(date +%Y%m%d)/
```

The May 17 incident had **81 JR-RECURSIVE-*-MD files** created by `recursive_decomposer` auto-decomposing failed tasks. Quarantine all of them — they're RAG pollution.

## Verification protocol (run BEFORE authorizing restart)

### Check 1 — Code integrity

All these MD5s should be stable for ≥10 min before restart:

| File | Expected behavior |
|---|---|
| `/ganuda/config/secrets.env` | matches last-known-good; **do not commit MD5 to KB** |
| `/ganuda/lib/specialist_council.py` | DC-15/16/17 framework present; `python -c 'import lib.specialist_council'` succeeds |
| `/ganuda/jr_executor/task_executor.py` | `python -m py_compile jr_executor/task_executor.py` succeeds |
| `/ganuda/lib/jr_plan_parser.py` | grep `Strategy [1-5]` finds all 5 strategies |
| `/ganuda/jr_executor/dlq_manager.py` | grep `_mark_queue_row_failed` finds 2+ call sites |
| `/ganuda/jr_executor/dlq_retry_poller.py` | grep `MAX_AGE_DAYS` finds env-var default |

### Check 2 — Damage-prone tasks confirmed cancelled

```sql
SELECT id, status FROM jr_work_queue WHERE id IN (<offender list>);
-- ALL must be 'cancelled'
```

### Check 3 — Pending tasks are all curated

```sql
SELECT id, assigned_jr, LEFT(title,60) FROM jr_work_queue WHERE status='pending';
```

- All `pending` rows should have `assigned_jr IS NULL` (so dispatcher won't auto-pick them), OR
- The `assigned_jr` set on them is intentional (Partner explicitly authorized)
- If you see `pending` rows with unexpected `assigned_jr` set, **investigate before restart**

### Check 4 — DLQ would-fire count

```sql
SELECT COUNT(*) FROM jr_failed_tasks_dlq
WHERE resolution_status='retrying'
  AND EXTRACT(EPOCH FROM (NOW() - created_at))/86400 <= 3;
```

If >0, **DO NOT restart `jr-dlq-retry-poller`** until either (a) each within-3d entry has a triage decision, or (b) Council ratifies bulk-abandon-on-restart policy.

### Check 5 — Failure-mode → root-cause coverage

Run the histogram (last 24h):

```sql
SELECT CASE
  WHEN error_message ILIKE '%HALLUCINATION%' THEN 'A: hallucination'
  WHEN error_message ILIKE '%instruction file not found%' THEN 'B: instruction missing'
  WHEN error_message ILIKE '%No executable steps%' THEN 'C: plan parser empty'
  WHEN error_message ILIKE '%research%' THEN 'D: research pipeline'
  WHEN error_message ILIKE '%1 step(s) failed%' THEN 'F: generic step fail'
  ELSE 'Z: other'
END AS mode, COUNT(*)
FROM jr_work_queue WHERE status='failed' AND updated_at > NOW() - INTERVAL '24 hours'
GROUP BY 1 ORDER BY 2 DESC;
```

For each non-historical mode with count >0, **a KB must exist** mapping the mode → root cause. If not, file the KB before restart OR restart only the surfaces unaffected by that mode.

## Go/no-go decision matrix

| Surface | Restart-safe when |
|---|---|
| `jr-executor` | Check 1+2+5 pass; restart-safe even with DLQ unresolved (manual dispatch only) |
| `jr-orchestrator` | Check 1+2+3 pass; restart-safe but watch for `recursive_decomposer` re-firing |
| `jr-queue-worker` | Check 1+3 pass; uses pre-assigned_jr only |
| `jr-dlq-retry-poller` | Check 4 = 0 OR all within-3d entries have KB coverage; **strongly recommend gating on FWPL Phase 1 ship** |

## Reusable cancellation list (May 17 2026 SEV1)

Tasks confirmed damage-prone, cancelled, **DO NOT re-dispatch without explicit operator review**:

| ID | Title (truncated) | Why damage-prone |
|---|---|---|
| 1264 | Cert Shepherd — Sync TLS Certs Between DMZ Nodes | TLS-cert writing → can overwrite real certs |
| 1278 | CRAWDAD P0: Mac Fleet Credential Sweep | credential rotation → can overwrite secrets.env |
| 1294 | Greenfin Sentinel — Sub-Claude Watchdog | systemd-unit writing → can break boot |
| 1296 | Small Model Sub-Agent Dispatch Harness | code-gen into reasoner path |
| 1313 | Peace Chief Curiosity Engine — Stub Pipeline | named "Stub Pipeline" — produces stubs |
| 1325 | SLA Baseline Metrics — Governance Response Time | metric-writing into governance files |
| 1486 | Meeting Notes Extractor: Deploy Demo + Substack + LinkedIn | publishes to external surfaces |
| 1529 | Cert Shepherd — sync TLS certs between DMZ nodes | duplicate of #1264 |
| 1584 | Owl Pass: Apr 22 2026 end-of-day federation sweep | sweep tasks can touch many files |
| 1646 | EAI-DEER-SEARCH-TERMS — Deer pipeline | search-term injection into deer pipeline |
| 1649 | INFRA-TRUENAS-NETWORK-HARDENING-MAY10 | network config writing |
| 1662 | FA-GAP5-001 — Fine-Tune on Sacred Thermals | could touch thermal memory |

Pattern: **anything that writes credentials, certs, systemd units, network configs, sacred memory, or external-publishing surfaces is damage-prone**. Add to this list as new ones are identified.

## Lineage links

- **Parent KBs** (failure modes this playbook responds to):
  - `KB-JR-STUB-PASSES-VERIFIER-MAY16-2026.md` — claim_verifier covers Mode A
  - `KB-JR-CAPABILITY-GAPS-EXECUTION-MODE-PLAN-PARSER-MAY15-2026.md` — Mode C
  - `KB-JR-EXECUTOR-DLQ-ZOMBIE-ROW-MAY15-2026.md` — zombie-row pattern
  - `KB-JR-CONTENT-GENERATION-OVER-EAGER-CODE-MAY16-2026.md` — Mode A substrate
  - `KB-JR-DISPATCH-PRE-ASSIGNED-JR-MAY16-2026.md` — Mode B
- **Sibling audits:**
  - `/ganuda/docs/audit/JR-READINESS-VERIFICATION-MAY17-2026.md` — applies this playbook to current state
  - `/ganuda/docs/audit/EXECUTION-MODE-ROUTER-AUDIT-MAY17-2026.md`
  - `/ganuda/docs/audit/BOOT-ORDER-AUDIT-MAY17-2026.md`
- **Structural answer (in flight):**
  - Kanban #2563 — FWPL Phase 1 (File-Write-Protection Layer). When this ships, pre-write hook rejects stub-shaped writes BEFORE they hit disk. Playbook becomes a fallback rather than a routine procedure.
- **Architectural frame:**
  - `memory/project_duplo_jr_layer_extension_may17_2026.md` — DUPLO/White-DUPLO applied to Jr-execution layer; FWPL Phase 1 is White-DUPLO-at-file-write
  - Council vote `b19336ffe8067670` (Concerns-as-Features synthesis)

## Open follow-ups (not blocking restart, but ticket-worthy)

1. **Mode D (research pipeline) needs its own KB** — 5 failures in last 24h, no root-cause documented yet
2. **#1497 Substack instruction file** — failed 6+ times "No executable steps"; triage cancel-vs-rewrite
3. **#1670 parser-fix task re-fail** — verify the fix actually took effect for its own dispatch
4. **Bluefin tailscale daemon down 9 days** — LAN works, tailscale dead, separate infra ticket
5. **`recursive_decomposer` review** — auto-decomposes failed tasks into STEP files (81 created at SEV1) → RAG pollution. Add to FWPL Phase 1 scope OR file separately.

## When to re-run the verification protocol

- After ANY Jr-service restart following a halt of >1 hour
- After ANY production-file restore from backup
- After ANY DLQ poller config change
- Weekly even in steady state, until FWPL Phase 1 ships
- When Partner returns from a >4-hour away window and Jr was running
