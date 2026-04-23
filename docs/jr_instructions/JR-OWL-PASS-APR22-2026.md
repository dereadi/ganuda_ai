# JR INSTRUCTION: Owl Pass — Apr 22 2026 End-of-Day Sweep

**JR ID:** JR-OWL-PASS-APR22-2026
**FROM:** TPM (Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P2
**DATE:** 2026-04-22
**OWL ROLE:** Quality assurance, loose-thread detection, tech-debt regression, "look-back pays 10x"

## Context

Today produced an unusually high volume of architectural changes + operational findings. Owl's job: walk through each work stream, verify nothing got dropped, surface loose threads, flag anything that needs follow-up tracking.

**Today's shipped architecture:**
- Persona-attention fix in specialist_council.vote_first (memory context moved from system prompt → user message) + matching fix in `_run_deliberation_first`
- Greenfin backend wired as fallback node in Council routing (bmasass→greenfin→redfin chain)
- Council persona-attention fix verified via real votes post-patch (flag rate 100% → 38%)
- Medicine Woman alert dedup (signature-based, 4h re-escalation)
- Reroute-observability OTel metric added (`ganuda.council.specialist.reroute`)
- TPM Claude Code memory hooks LIVE (`/ganuda/scripts/tpm_hooks/`): UserPromptSubmit, SessionStart, PreCompact
- 5 atomic replacement tickets filed + closed (#1579 indexes, #1580 rollback-logging, #1581 linux-creds, #1582 goldfin-verify, #1583 role-audit)
- DLQ cleanup: 8 old failures closed with verified disposition
- Deer Braided Stream lead drafted + placed on sasass + feedback-memory filed

**Today's real findings needing tracking:**
- Goldfin offline 70 days (Tailscale last-seen Feb 2026) — `/ganuda/docs/kb/KB-GOLDFIN-PII-VERIFY-APR22-2026.md`
- `cherokee_helpdesk` role has SUPERUSER (high-severity privilege-excess finding) — `/ganuda/docs/kb/KB-DB-ROLE-PRIVILEGE-AUDIT-APR22-2026.md`
- `claude` role blast-radius concentration (medium severity)
- `claude_user` has unnecessary CREATEDB (low severity)

## TASK 1 — Git Hygiene

1. Check `git status` — what was modified today? Likely heavy touches to `/ganuda/lib/specialist_council.py`, `/ganuda/daemons/*.py`, `/ganuda/scripts/tpm_hooks/*`.
2. Verify no uncommitted sensitive content. Scan for hardcoded credentials in any newly-modified file.
3. `git diff --stat HEAD` summary — report lines-added/lines-removed by file.
4. Any .backup files left behind from today's edits? Clean them.

## TASK 2 — Specialist Council Patches Verification

1. Verify `/ganuda/lib/specialist_council.py` imports cleanly — `python3 -c "from lib.specialist_council import council_vote_first, GREENFIN_BACKEND, BACKEND_FALLBACK_CHAIN; print('ok')"`.
2. Run a smoke-test Council vote (low-stakes, simple question). Report: did all 13 specialists respond, and what was the first-pass flag rate? Baseline to compare future sessions against.
3. Probe the greenfin fallback by simulating bmasass unreachable. Expected: `coyote`, `crane`, `blue_jay`, `turtle` reroute to greenfin, NOT to redfin. Return the reroute-flag results.
4. Verify OTel metric `ganuda.council.specialist.reroute` is emitted when reroute occurs (grep service logs or metric export).

## TASK 3 — TPM Memory Hooks Health

1. Check `/ganuda/logs/tpm_hooks/*.log` — are prompt_inject / session_start / compact_guard firing? Row count per log for today.
2. Sample three log entries per hook. Verify thermal_hits + crawdad_hits are both non-zero in typical entries.
3. Confirm `~/.claude/settings.json` still has all 3 hook entries registered.
4. Embedding service (`http://192.168.132.224:8003/v1/search`) reachable from redfin? If greenfin goes down, hooks will silently fail. Worth monitoring.

## TASK 4 — Medicine Woman Alert Dedup Check

1. Check `journalctl -u medicine-woman.service --since "2026-04-22 14:00" | grep 'Alert sent\\|Alert dedup'`. Verify the dedup is actually suppressing repeated alerts.
2. Verify DLQ depth via `jr_work_queue` — confirm < 10 (threshold). Should be 8 after today's cleanup.
3. Confirm alert signature-tracking globals are active in the running process.

## TASK 5 — DB Health Post-Migration

1. Query `pg_stat_user_indexes` for the 4 new indexes shipped in #1579. Report `idx_scan` counts — are they getting used? (May still be 0 if data volume is low, that's fine.)
2. `grep -c "ROLLBACK:" /ganuda/logs/*.log` or equivalent across daemon log destinations — count rollback instrumentation events since deploy. Report the first few samples to verify instrumentation is emitting cleanly.
3. Verify all 7 daemons that got rollback-instrumentation are still running: `systemctl status {medicine-woman,governance-agent,memory-jr,meta-jr-phase1,memory-consolidation,staleness-scorer,meta-jr}.service` (names vary — check which are actual service units vs ad-hoc).

## TASK 6 — Goldfin Investigation (REAL FINDING)

**This is the highest-priority follow-up task.**

1. Verify goldfin is STILL offline (Tailscale status + ping). If it came back online today, update KB.
2. Grep federation service configs for hardcoded references to goldfin / `192.168.20.10` / `vetassist_pii`:
   ```
   grep -rE "192\.168\.20\.10|vetassist_pii|goldfin" /ganuda/ --include="*.py" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env*"
   ```
3. If any config expects goldfin — is it silently failing? Check recent error logs from vetassist services.
4. Check backup system — when was goldfin last backed up? Is there a backup that could be restored to another node if goldfin hardware is dead?
5. Report findings to TPM for Partner escalation.

## TASK 7 — Cherokee_helpdesk Privilege Audit (REAL FINDING)

1. Check `pg_stat_activity` + pg_log (if accessible) for any recent connection by `cherokee_helpdesk` role. When was it last used?
2. If unused in 30+ days, recommend DROP. If actively used, recommend NOSUPERUSER + specific grants per KB-DB-ROLE-PRIVILEGE-AUDIT-APR22-2026.md.
3. Do NOT execute the ALTER / DROP without Partner sign-off — this is a real credential change that could break something. Surface recommendation, not action.

## TASK 8 — Deer Publication Queue Integrity

1. `/ganuda/docs/deer_braided_stream_lead_draft_apr22_2026.md` — exists and accessible?
2. `/Users/Shared/ganuda/docs/deer_braided_stream_lead_draft_apr22_2026.md` on sasass — reach out via SSH and verify.
3. Kanban #1452 (Deer: Three-Paper Convergence — LinkedIn + Substack) — what's its status? Is it reconciled with the Braided Stream lead draft or should the scope be refreshed?

## TASK 9 — Fresh Memory File Sanity

Today ~13 new memory files landed in `/home/dereadi/.claude/projects/-ganuda/memory/`. Owl should:
1. Verify each has the expected frontmatter (`name`, `description`, `type`).
2. Spot-check MEMORY.md — does it index every new file? Any duplicates?
3. Flag any memory file > 2000 lines (too big, should be split).

## TASK 10 — Summary Report

Produce `/ganuda/docs/kb/KB-OWL-PASS-APR22-2026.md` with:
- Findings section (new issues Owl discovered beyond what TPM already knew)
- Confirmation section (what TPM did today that Owl verified as working)
- Follow-up section (what still needs action — prioritized)
- One-line Council-ready summary of the whole day's posture

## Done criteria

- `/ganuda/docs/kb/KB-OWL-PASS-APR22-2026.md` exists and is > 1KB
- All 10 tasks have findings / confirmations recorded
- If any new blocker discovered, kanban ticket filed with `owl-finding-apr22` tag

## Apr 22 2026 TPM
