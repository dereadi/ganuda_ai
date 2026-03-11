# [RECURSIVE] Measure: SLA Baseline Metrics (Governance Response Time) - Step 4

**Parent Task**: #1206
**Auto-decomposed**: 2026-03-10T11:25:18.257497
**Original Step Title**: Generate the report file

---

### Step 4: Generate the report file

```bash
mkdir -p /ganuda/docs/business
python3 /ganuda/scripts/sla_baseline_metrics.py --write-report
```

## Acceptance Criteria

- Script exists at `/ganuda/scripts/sla_baseline_metrics.py` and is executable
- Script measures all 5 metrics: council vote time, Jr task completion, thermal write rate, gateway response, dawn mist generation
- Script outputs a formatted table to stdout
- `--write-report` flag writes a markdown summary to `/ganuda/docs/business/SLA-BASELINE-METRICS-MAR09-2026.md`
- Script handles missing data gracefully (N/A, not crash)
- Script uses credentials from `/ganuda/config/secrets.env` (never hardcoded)
- Script completes in under 30 seconds
- No dependencies beyond psycopg2 and requests (both already installed on redfin)

## Constraints

- Read DB credentials from `/ganuda/config/secrets.env` — do NOT hardcode passwords
- Do NOT write to the database — read-only queries only
- Do NOT import from federation libraries (ganuda_db, specialist_council) — this script is standalone
- Gateway health check should timeout after 10 seconds per request
- Handle connection failures gracefully with clear error messages
