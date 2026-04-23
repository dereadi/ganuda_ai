# JR INSTRUCTION: Owl Audit — Weekend Through Monday (Apr 10-13 2026)

**JR ID:** JR-OWL-AUDIT-WEEKEND-APR10-13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P2
**DATE:** April 13, 2026
**OWL ROLE:** Quality assurance, loose thread detection, hygiene

## Context

Four days of sustained high-output work (Apr 10-13). Partner describes it as "a fevered dream." Multiple work streams ran simultaneously: infrastructure (fiber), contest (ARC-AGI-3), governance (Council votes, Longhouse), research (9 deer signals), tooling (LARQL, ganuda-harness), and team changes (Brandon onboarded). With this much velocity, threads get dropped. Owl's job is to find them.

## TASK 1 — Commit and Git Hygiene

1. Check `git log --since="2026-04-09" --until="2026-04-14"` — verify the weekend commit landed clean
2. Check `git status` — are there still unstaged files that should have been committed?
3. Check for any `.gitignore` gaps — are we accidentally tracking build artifacts, model weights, or secrets?
4. Check for the two monitor.py files that were unstaged due to pre-commit false positives (products/clipboard-intel/monitor.py, products/ganuda-shield/agent/monitor.py) — they have security scanner patterns that trigger the hook. Either allowlist them or refactor the patterns.

## TASK 2 — Infrastructure Thread Check

1. **Fiber Gate 2:** Is the observation log being written? Check `/ganuda/logs/fiber-gate2-observation.log`
2. **pg_hba.conf gap:** The fiber subnet (10.200.0.0/24) is NOT in PostgreSQL's pg_hba.conf on bluefin. Fiber SSH works but direct PostgreSQL over fiber returns `FATAL: no pg_hba.conf entry for host "10.200.0.10"`. Is this tracked for Gate 2 resolution?
3. **SAG service:** SAG was inactive on bluefin during today's checks. Was this intentional? Check if it should be running.
4. **Grafana health checks:** Jr task from Apr 11 (JR-FIBER-BRINGUP-BLUEFIN) Task 3 was to clean dead Grafana health checks in SAG app.py. Was this completed?
5. **WireGuard flakiness:** SSH over WireGuard was timing out today while fiber worked. Is WireGuard degrading or was this transient? Check `wg show` on both nodes.

## TASK 3 — Jr Executor Health

1. **Failed tasks:** Tasks #1501, #1502, #1503 all failed. Root cause: Jr executor partial edit system can't handle multi-file changes with ambiguous anchors. IndentationError on ganuda_agent.py line 504.
2. **DLQ:** Task #1503 entered DLQ (entry 245). Is it still there? Should it be cleared or retried?
3. **Pending tasks:** Task #1504 (strategy integration, atomic) and #1505 (LARQL fork) — have they been picked up?
4. **Queue health:** Run `SELECT id, title, status, progress_percent FROM jr_work_queue ORDER BY id DESC LIMIT 10` and report current state.

## TASK 4 — ARC-AGI-3 Contest Threads

1. **Baseline results saved?** Swarm test ran today (vc33 L2, sp80 100%, lp85 67%). Results at `/ganuda/services/arc_agi_3/swarm_results/swarm_20260413T141627.json`. Verify file exists and contains valid data.
2. **game_strategy.py integration:** The module was written but NOT integrated into ganuda_agent.py. Task #1504 was dispatched for this. Is the integration done?
3. **Working tree changes:** `git diff -- services/arc_agi_3/` — are there uncommitted changes to the agent code from the weekend testing?
4. **venv health:** The arc_agi_3 venv at `/ganuda/services/arc_agi_3/venv/` — does it have all dependencies? `huggingface_hub` was installed during this session.
5. **Experience bank:** 39 experience files in `/ganuda/services/arc_agi_3/experiences/`. Any corrupt or zero-byte files?

## TASK 5 — Council Vote Integrity

1. **Longhouse v1.1 vote (d022edb51960cef1):** Is this recorded in the Council vote database? Check `jr_work_queue` or `council_votes` table.
2. **LARQL v2.0 vote (4c53f9f069f19ef5):** Same check.
3. **Coyote dissent on both votes:** Was Coyote's dissent properly recorded and thermalized?

## TASK 6 — LARQL / ganuda-harness Cleanup

1. **LARQL clone:** `/ganuda/services/larql/` is excluded from git (in .gitignore). Verify the built binary works: `./target/release/larql --version`
2. **Vindex files:** Three vindexes extracted today. Are they intact?
   - `/ganuda/services/larql/starcoder2-3b.vindex/` (browse, gate_vectors empty — expected)
   - `/ganuda/services/larql/qwen25-1.5b.vindex/` (browse, 1.18 GB)
   - `/ganuda/services/larql/qwen25-1.5b-full.vindex/` (all, 2.91 GB)
3. **ganuda-harness:** Binary at `/ganuda/services/ganuda-harness/target/release/ganuda-harness` (9 MB). Verify it runs: `./target/release/ganuda-harness --help`
4. **Audit trail:** One test record in `/ganuda/services/ganuda-harness/audit.jsonl`. Should be preserved as the first governance audit record.
5. **ganuda-harness not running:** It was started and stopped during testing. Verify no orphan process: `pgrep -f ganuda-harness`

## TASK 7 — Memory / Thermal Hygiene

1. **MEMORY.md size:** Check line count. It was already 572 lines and growing. The system warned about truncation. Are we over the limit?
2. **New memories from today:** 12+ new memory files were created. Verify none are duplicates of existing entries.
3. **Stale memories:** Any memories from before Mar 10 that reference things no longer true? (14-day backlog review rule per feedback_backlog_hygiene.md)

## TASK 8 — Kanban / Backlog Check

1. **Open kanban items:** How many items are open? Any over 14 days old that should be closed or reprioritized?
2. **Hulsey follow-up:** The intake form is incoming. Is there a kanban item tracking it?
3. **Patent drawings:** Hulsey said provisionals need drawings/flowcharts. Is there a kanban item for creating them?

## Reporting

Post Owl audit results to thermal memory at 88°C (Owl temperature) with tags `owl_audit,weekend_hygiene,apr2026` and source_triad `it_triad_jr`.

Format: For each task above, report CLEAN / THREAD FOUND / ACTION NEEDED with a one-line description.
