# KB: TTD Metric — Time-to-Detection (Eagle Eye)

**Built:** 2026-03-10 by TPM (grindstone surge, Leaders Meeting #1)
**Kanban:** #2078 | **Longhouse:** bb75fd4e3a693335

## Problem

Critical failures went undetected for DAYS:
- Governance SQL wrong column names: 73 hours TTD
- fire_guard.py corruption: 28.5 hours TTD
- Raven circuit breaker OPEN: 141.5 hours before investigation

Target: TTD < 2 hours for critical systems.

## Table

```sql
CREATE TABLE failure_detection_log (
    id SERIAL PRIMARY KEY,
    failure_type VARCHAR(100) NOT NULL,    -- e.g. 'sql_column_mismatch', 'file_corruption'
    component VARCHAR(100) NOT NULL,        -- e.g. 'fire_guard', 'governance_agent'
    failure_occurred_at TIMESTAMPTZ,        -- when it actually broke (may be estimated)
    failure_detected_at TIMESTAMPTZ DEFAULT NOW(),  -- when we found it
    ttd_seconds FLOAT,                      -- the metric: detected - occurred
    detected_by VARCHAR(100),               -- who/what found it: 'fire_guard', 'tpm_manual', 'eagle_eye'
    severity VARCHAR(20) DEFAULT 'medium',  -- critical, high, medium, low
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## View

```sql
-- Eagle Eye dashboard: TTD by component
SELECT * FROM eagle_eye_ttd_summary;
```

Returns: component, total_failures, avg/max/min TTD, count within 2hr target, percent within target.

## How to Log a Failure

When a failure is discovered:
```sql
INSERT INTO failure_detection_log
    (failure_type, component, failure_occurred_at, failure_detected_at, ttd_seconds, detected_by, severity, details)
VALUES
    ('type', 'component', 'estimated_break_time', NOW(),
     EXTRACT(EPOCH FROM (NOW() - 'estimated_break_time'::timestamptz)),
     'detector_name', 'severity', 'what happened');
```

## Gotchas for Jrs

- `failure_occurred_at` is often ESTIMATED — use best available evidence (log timestamps, last known good)
- `ttd_seconds` = `failure_detected_at - failure_occurred_at` in seconds. Calculate it, don't leave NULL.
- `detected_by` should name the SYSTEM that found it (fire_guard, safety_canary, eagle_eye) or 'tpm_manual' / 'chief_manual' if a human caught it
- The goal is to SHRINK this number over time. Every entry is a learning opportunity.
- Fire Guard running every 2 min should catch most failures within 2-4 minutes. If TTD > 10 min, Fire Guard missed it — investigate why.
