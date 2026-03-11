# JR INSTRUCTION: Backlog Reckoning Script

**Task:** Build `/ganuda/scripts/backlog_reckoning.py`
**Priority:** 2
**Council Vote:** #2aaaa11e1715c307 (0.871 confidence, APPROVED WITH CONDITIONS)
**Design Doc:** `/ganuda/docs/design/DC-BACKLOG-RECKONING-MAR10-2026.md`

## What You're Building

A weekly script that scores kanban backlog items for staleness and produces an advisory report. It does NOT auto-close anything. It recommends.

## Database Connection

Use `ganuda_db` or manual fallback pattern (see `coherence_scan.py` for the pattern):
- Host: `192.168.132.222`
- DB: `zammad_production`
- User: `claude`
- Password: from `CHEROKEE_DB_PASS` env var or `/ganuda/config/secrets.env`

The fallback pattern loads secrets.env when the env var is missing — see `generate_status_page.py` lines 261-271 for reference. Prefer the `ganuda_db.get_connection()` / `ganuda_db.get_dict_cursor()` pattern used in `council_dawn_mist.py` (lines 23, 215-216) with a manual psycopg2 fallback if ganuda_db is not importable.

## Steps

### 1. Query All Open Kanban Items

```sql
SELECT id, title, status, created_at, updated_at
FROM duyuktv_tickets
WHERE status IN ('open', 'backlog')
ORDER BY created_at ASC
```

### 2. Score Each Item (Composite Staleness Score)

Six dimensions, each 0.0 to 1.0:

**age_score:**
- <30 days: 0.0
- 30-60 days: 0.3
- 60-90 days: 0.6
- >90 days: 0.9

**inactivity_score:**
- updated_at within 14 days: 0.0
- 14-30 days: 0.3
- 30-60 days: 0.6
- >60 days: 0.9

**dc_drift_score:**
- Query `thermal_memory_archive` for sacred thermals with "DC-" in `original_content` created AFTER the ticket's `created_at`
- 0 new DCs: 0.0
- 1-2 new DCs: 0.3
- 3-5 new DCs: 0.6
- >5 new DCs: 0.9

Note: the column is `sacred_pattern` (boolean), not `sacred`. The content column is `original_content`. See `council_dawn_mist.py` line 118 for the correct column name usage.

**decomposition_score** (EPICs only):
- Check if title starts with "EPIC"
- If EPIC and no linked Jr tasks completed in 30 days: 0.9
- If EPIC with recent activity: 0.3
- If not EPIC: 0.0

To check for linked Jr tasks, search `jr_work_queue` for tasks whose `title` or `description` references the EPIC ticket ID or keywords from the EPIC title. Simple substring match is fine for Phase 1.

**tech_supersession_score:**
- Simple keyword check against a deprecated tech list:
  ```python
  DEPRECATED_TECH = [
      'ChromaDB', 'DeepSeek-R1-Distill', 'telegram_bot_daemon',
      'cherokee-council-gateway', 'sag-unified', 'vllm-redfin'
  ]
  ```
- Match found in title: 0.9
- No match: 0.0

**market_freshness_score:**
- If title contains market-related keywords (`'LinkedIn', 'partnership', 'pricing', 'customer', 'onboarding', 'sales'`):
  - Check if Deer thermals (`domain_tag='market'` or tags contain `'deer'`) exist from last 30 days referencing similar topics
  - Recent signal: 0.0
  - No recent signal: 0.6
- If not market-related: 0.0

**Composite score:** weighted average
- age: 0.20
- inactivity: 0.25
- dc_drift: 0.20
- decomposition: 0.10
- tech_supersession: 0.15
- market_freshness: 0.10

All weights and thresholds MUST be defined as constants at the top of the file (Council condition #2).

### 3. Classify

- Score >= 0.7: **STALE** — recommend close or rewrite
- Score 0.4-0.7: **REVIEW** — ambiguous, may need LLM assessment (Phase 2)
- Score < 0.4: **KEEP**
- If item has "seed" or "dormant" tag: exempt from weekly, flag for quarterly review

### 4. Cap Output

- Max 7 STALE recommendations per run
- Max 5 REVIEW items per run
- Include all SEED/DORMANT items for quarterly tracking

Sort STALE and REVIEW by composite score descending so the worst offenders surface first.

### 5. Output Formats

The script must support three output modes via CLI flags:

**`--text`** (default): Human-readable report for dawn mist
**`--json`**: Machine-readable for integration
**`--slack`**: Format for Slack `#saturday-morning` channel

Use `argparse` for CLI handling. Also support `--dry-run` which scores but does not post to Slack or write overrides.

Text format example:
```
BACKLOG RECKONING — Wed Mar 12, 2026 05:00 CT
================================================================

STALE (recommend close/rewrite): 3 items
  #1908 [0.82] Clone and evaluate Claude-Flow swarm orchestration
    → Age: 0.9 | Inactivity: 0.9 | DC drift: 0.6 | Tech: 0.0
    → 4 DCs ratified since creation. Pre-DC-10 assumptions.
  ...

REVIEW (needs human eye): 2 items
  ...

SEEDS (quarterly review): 1 item
  ...

STATS: 69 open items scored. Median age: 42 days. Median score: 0.38.
Override rate (last 4 weeks): N/A (first run)
================================================================
```

For `--slack` mode, use `slack_federation.send("saturday-morning", text)`. Follow the import pattern from `council_dawn_mist.py` lines 26-29:
```python
try:
    from slack_federation import send as slack_send
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
```

Slack channel map is in `/ganuda/lib/slack_federation.py` — the target channel is `saturday-morning` (channel ID `C0AKAV1Q9RS`). Respect silent hours unless `urgent=True`.

### 6. Timer Integration

Do NOT create a new systemd timer. Add to the existing `owl-debt-reckoning` workflow. The script should be callable standalone:
```bash
python3 /ganuda/scripts/backlog_reckoning.py           # text output to stdout
python3 /ganuda/scripts/backlog_reckoning.py --json     # JSON to stdout
python3 /ganuda/scripts/backlog_reckoning.py --slack     # post to Slack #saturday-morning
python3 /ganuda/scripts/backlog_reckoning.py --dry-run   # score but don't post
```

### 7. Override Tracking

Create a simple JSON file at `/ganuda/config/backlog_reckoning_overrides.json` to track Chief's decisions over time:
```json
{
  "runs": [
    {
      "date": "2026-03-12",
      "flagged": [1908, 1939, 530],
      "closed": [1908],
      "kept": [1939, 530],
      "override_rate": 0.67
    }
  ]
}
```

Use atomic writes (`tempfile` + `os.replace`) like `thread_bookmarks.py`. Write to a temp file first, then atomically move it into place to avoid corruption on crash.

### 8. Thermal Memory

After each run, write a summary thermal to `thermal_memory_archive` using `ganuda_db.safe_thermal_write()` (imported in `council_dawn_mist.py` line 23). Temperature 50 for normal runs, 70 if override rate exceeds threshold.

## Council Conditions (BINDING)

These are binding conditions from the council vote. Violating them invalidates the approval.

1. **Override rate threshold: 30%.** Track from first run. If >30% after 4 runs, log warning to stderr and thermal memory.
2. **Staleness thresholds MUST be configurable** — all scoring constants defined at the top of the file as module-level variables, not buried in scoring logic.
3. **4-week kill switch:** After 4 runs, if override rate >30% OR no tickets closed, script logs `COYOTE REVIEW REQUIRED` and stops recommending closures until recalibrated. The kill switch state should be checked from the overrides JSON at startup.

## Testing

- `--dry-run` must work without Slack/dawn mist integration
- Score a known stale item (e.g., #530 from early days) — should score high
- Score a recent item — should score low
- Check that EPIC detection works
- Verify DC drift detection finds recent DCs
- Verify that `--json` output is valid JSON parseable by `json.loads()`
- Verify that seed/dormant items are excluded from STALE/REVIEW lists

## Files to Read Before Starting

- `/ganuda/scripts/council_dawn_mist.py` — dawn mist delivery pattern, `ganuda_db` imports, Slack integration
- `/ganuda/lib/slack_federation.py` — Slack posting API (`send()`, `send_blocks()`), channel map, silent hours
- `/ganuda/scripts/coherence_scan.py` — DB connection pattern with `ganuda_db` fallback
- `/ganuda/scripts/generate_status_page.py` — direct psycopg2 DB pattern, secrets.env loading, kanban queries
- `/ganuda/docs/design/DC-BACKLOG-RECKONING-MAR10-2026.md` — full design doc
- `/ganuda/docs/kb/KB-DC14-WATERSHED-LAYER.md` — column name gotchas for `thermal_memory_archive`

## DO NOT

- Auto-close any kanban items — this script RECOMMENDS ONLY
- Create a new systemd timer
- Hardcode DB passwords — use env var with secrets.env fallback
- Query the LLM for every item (Phase 2 — rule-based only for now)
- Import modules not available in the standard ganuda Python environment
