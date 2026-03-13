# [RECURSIVE] SLA Baseline Metrics — Governance Response Time (retry) - Step 4

**Parent Task**: #1325
**Auto-decomposed**: 2026-03-12T17:53:45.717626
**Original Step Title**: Generate the report file

---

### Step 4: Generate the report file

```bash
mkdir -p /ganuda/docs/business && python3 /ganuda/scripts/sla_baseline_metrics.py --write-report
```

## Acceptance Criteria

- Script exists at `/ganuda/scripts/sla_baseline_metrics.py` and is executable
- Script measures all 5 metrics: council vote time, Jr task completion, thermal write rate, gateway response, dawn mist generation
- Script outputs a formatted table to stdout
- `--write-report` flag writes markdown summary to `/ganuda/docs/business/SLA-BASELINE-METRICS-MAR12-2026.md`
- Script handles missing data gracefully (N/A, not crash)
- Script uses credentials from `/ganuda/config/secrets.env` (never hardcoded)
- Script completes in under 30 seconds
