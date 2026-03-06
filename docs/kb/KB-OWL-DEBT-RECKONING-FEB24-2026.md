# KB: Owl — Debt Reckoning Daemon

**Created:** Feb 24, 2026
**Kanban:** #1891
**Jr Task:** #907 (completed, 1/1 steps succeeded)
**Script:** `/ganuda/scripts/owl_debt_reckoning.py`

---

## What It Does

Owl is the federation's backward-looking eye. It verifies that completed Jr tasks actually shipped working code. Named for the Owl, who sees what others miss in the dark.

**Checks performed per task:**
1. **File existence** — did the Create blocks actually produce files?
2. **Python syntax** — does `ast.parse()` succeed?
3. **Code quality** — duplicate function defs? Multiple `if __name__` blocks? (sign of append-not-replace bug)
4. **Table existence** — did CREATE TABLE instructions produce tables in the DB?
5. **Step success rate** — how many execution steps actually succeeded?

**Scoring:**
- **VERIFIED** — all checks pass, artifacts exist
- **DEGRADED** — some steps failed but core artifacts exist
- **BROKEN** — missing files, syntax errors, or >50% step failures

## First Reckoning Results (Feb 24, 2026)

78 tasks checked over 3 days:
- **41 VERIFIED** (53%)
- **37 BROKEN** (47%)
- **0 DEGRADED**

### Key Failure Patterns Discovered

1. **Backtick path extraction artifact**: regex picks up `` `/ `` prefix from markdown, inflating BROKEN count. Need to strip backticks from extracted paths.
2. **Executor append-not-replace**: Some files have multiple `if __name__` blocks because Create appended instead of replacing.
3. **Gateway timeout during execution**: Council query + summarization steps fail when gateway is under load.
4. **Syntax errors from truncated code blocks**: Jr instruction code blocks occasionally get truncated, producing unterminated strings.
5. **Duplicate Jr tasks**: Same work queued twice (e.g., #869 and #890 both for task vectors). Earlier version works, later re-queue picks up path issues.

### Known False Positives

- Tasks that edit existing files (SEARCH/REPLACE only) won't have Create blocks, so no files to check. These correctly score VERIFIED.
- Tasks like Cloudflare WAF config (#886) produce config, not scripts. Correctly scored VERIFIED because no file creation detected.

## Design Decisions

- **Dry-run mode**: `--dry-run` analyzes without storing to thermal memory.
- **Per-task targeting**: `--task-id 905` checks one specific task.
- **Adjustable lookback**: `--days 7` checks last 7 days.
- **Exit code 1** on any BROKEN — usable in CI/cron.
- **Thermal storage**: Reckoning report stored as memory_type="debt_audit", tagged ["owl", "debt_reckoning"]. Temperature based on severity (80 if BROKEN, 65 if DEGRADED, 50 if clean).
- **JSON report**: `/ganuda/reports/owl_debt_reckoning.json` for structured analysis.

## Origin — Anti-80/20 Principle

From the Chief's Walmart experience: every team sprinted with 80/20 (ship 80%, fix 20% later). After years, those teams were 40% dev / 60% support because nobody looked back. The debt compounded.

**Peace Eagle looks forward.** What should we learn? What's coming?
**Owl looks backward.** Did it actually work? What slipped through?

Both are required. A team that only looks forward drowns in debt. A team that only looks backward stagnates.

## Improvements Needed

1. **Strip backticks from path extraction** — `\`` characters in markdown Create blocks cause false BROKEN scores
2. **Import check** — actually try importing Python modules, not just syntax check
3. **Service verification** — for systemd service files, check if unit is active
4. **Trending** — track VERIFIED/BROKEN ratio over time for federation health
5. **Auto-triage** — for BROKEN tasks, auto-create kanban items or re-queue Jr tasks
6. **Cron/systemd timer** — run daily, store trending data

## Related

- **Peace Eagle (Curiosity):** KB-PEACE-EAGLE-CURIOSITY-DAEMON-FEB24-2026.md
- **Anti-80/20 Principle:** Saved in MEMORY.md
- **Executor known bugs:** KB-EXECUTOR-MIXED-STEP-TYPES-SKIP-BUG-FEB12-2026.md, KB-JR-EXECUTOR-SR-FIRST-EXTRACTION-FIX-FEB11-2026.md
- **Task Reaper:** KB-EXECUTOR-REAPER-IDEMPOTENCY-FEB22-2026.md
