# JR INSTRUCTION: Backlog Reckoning — Verification and Wiring

**Task ID:** 1260
**Title:** Build backlog_reckoning.py — Weekly Kanban Staleness Scoring
**Priority:** 2
**Status:** CODE COMPLETE — needs verification run
**Original Design:** `/ganuda/docs/jr_instructions/JR-BACKLOG-RECKONING-MAR10-2026.md`
**Council Vote:** #2aaaa11e1715c307 (0.871 confidence, APPROVED WITH CONDITIONS)

## What Was Built

`/ganuda/scripts/backlog_reckoning.py` — fully implemented per the design doc. All six scoring dimensions, three output modes, override tracking, kill switch, Slack integration, and thermal memory writes.

## Script Location

`/ganuda/scripts/backlog_reckoning.py`

## Steps for Jr Verification

### Step 1: Dry-Run Text Output

Run the script in dry-run mode to confirm it connects to the DB, scores items, and produces readable output:

```bash
cd /ganuda && python3 scripts/backlog_reckoning.py --dry-run
```

**Accept if:** Output shows the BACKLOG RECKONING header, lists STALE/REVIEW/SEED sections, shows STATS line with item count, median age, and median score. No traceback.

### Step 2: JSON Output Validation

```bash
cd /ganuda && python3 scripts/backlog_reckoning.py --json --dry-run | python3 -m json.tool > /dev/null && echo "VALID JSON"
```

**Accept if:** Prints "VALID JSON". The output must parse without error.

### Step 3: Scoring Sanity Check

Run JSON mode and inspect a known old ticket (any ticket with `created_at` older than 90 days):

```bash
cd /ganuda && python3 scripts/backlog_reckoning.py --json --dry-run | python3 -c "
import sys, json
data = json.load(sys.stdin)
stale = data.get('stale', [])
if stale:
    top = stale[0]
    print(f'Top stale: #{top[\"id\"]} score={top[\"composite\"]} title={top[\"title\"][:60]}')
    print(f'  Scores: {top[\"scores\"]}')
else:
    print('No stale items found (may be expected if backlog is fresh)')
"
```

**Accept if:** Either shows a stale item with composite >= 0.7, or reports no stale items (both are valid depending on backlog state).

### Step 4: Slack Post (Manual)

Only after Steps 1-3 pass:

```bash
cd /ganuda && python3 scripts/backlog_reckoning.py --slack
```

**Accept if:** Message appears in `#saturday-morning` channel on ganuda.slack.com. If Slack token is not set, script should gracefully fall back to stdout with a warning.

### Step 5: Override File Check

After a non-dry-run execution, verify the overrides file was created:

```bash
cat /ganuda/config/backlog_reckoning_overrides.json | python3 -m json.tool
```

**Accept if:** Valid JSON with a `runs` array containing at least one entry with `date`, `flagged`, `closed`, `kept`, `override_rate` fields.

## Council Conditions (BINDING — verify these)

1. **Override rate threshold 30%** — Check that `OVERRIDE_RATE_LIMIT = 0.30` is defined at module top.
2. **All scoring constants at top of file** — Verify no magic numbers in scoring functions. All thresholds defined as module-level constants.
3. **Kill switch after 4 runs** — Check that `check_kill_switch()` reads from overrides JSON and logs `COYOTE REVIEW REQUIRED` when triggered.

## Files

- `/ganuda/scripts/backlog_reckoning.py` — the script
- `/ganuda/config/backlog_reckoning_overrides.json` — override tracking (created on first run)
- `/ganuda/lib/slack_federation.py` — Slack posting (imported, not modified)
- `/ganuda/lib/ganuda_db.py` — DB connection + thermal writes (imported, not modified)

## DO NOT

- Auto-close any kanban items — this script RECOMMENDS ONLY
- Create a new systemd timer — integrate with existing `owl-debt-reckoning`
- Hardcode DB passwords
- Modify any imported library files
