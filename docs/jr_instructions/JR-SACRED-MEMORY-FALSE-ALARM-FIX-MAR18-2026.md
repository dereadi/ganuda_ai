# JR INSTRUCTION: Sacred Memory Count — False Alarm Fix

**Task**: Fix false CRITICAL alerts when DB connection fails during sacred memory count check. Missing data is not the same as decreased data.
**Priority**: P0 (blocking — CRITICAL alerts every ~3 hours are noise)
**Date**: 2026-03-18
**TPM**: Claude Opus
**Story Points**: 1
**Depends On**: governance_agent.py (LIVE)
**Thermal Context**: "Sacred memory count DECREASED: expected 1349, got ?" firing 6+ times in 27 hours

## Problem Statement

The governance agent's `sacred_memory_count_change` alert fires CRITICAL when `sacred_count < expected_sacred_count`. But when `collect_memory_metrics()` throws a DB connection exception, `sacred_count` is never set in the metrics dict. The condition lambda defaults missing keys to 0:

```python
'condition': lambda m: (
    m.get('sacred_count', 0) < m.get('expected_sacred_count', 0)
)
```

This evaluates as `0 < 1349 = True`, triggering a CRITICAL alert. The alert message formats `actual` as `'?'` (the default in the format dict). Sacred memories are fine — the monitoring query intermittently fails due to bluefin connection flakiness.

## Root Cause

**File**: `/ganuda/daemons/governance_agent.py`

Lines 338-341 catch the exception but don't prevent the alert:
```python
try:
    metrics.update(collect_memory_metrics(cur, run_integrity_check=run_integrity))
except Exception as e:
    logger.error(f"Memory metric collection failed: {e}")
    # sacred_count never gets set → defaults to 0 → triggers false CRITICAL
```

## Fix (1 SP)

### Option A: Guard the condition lambda (simplest)

Change the `sacred_memory_count_change` alert rule condition to require `sacred_count` to actually exist in the metrics:

```python
'sacred_memory_count_change': {
    'condition': lambda m: (
        'sacred_count' in m
        and m.get('sacred_count', 0) < m.get('expected_sacred_count', 0)
    ),
    'severity': 'CRITICAL',
    'message': 'Sacred memory count DECREASED: expected {expected}, got {actual}',
    'value_key': 'sacred_count',
    'cooldown_hours': 1,
    'escalate_after': 1,
},
```

One line added: `'sacred_count' in m and`. If the metric wasn't collected, the alert doesn't fire. If the metric WAS collected and shows a decrease, the alert fires correctly.

### Option B: Add a separate alert for metric collection failure (belt + suspenders)

Add a new alert rule that fires when memory metrics couldn't be collected — this IS worth knowing, but as a WARNING, not CRITICAL:

```python
'memory_metrics_unavailable': {
    'condition': lambda m: 'sacred_count' not in m and 'expected_sacred_count' in m,
    'severity': 'WARNING',
    'message': 'Memory metrics collection failed — sacred count not available this cycle',
    'cooldown_hours': 4,
    'escalate_after': 6,
},
```

This way:
- DB connection failure → WARNING (appropriate — monitoring is degraded)
- Actual sacred memory decrease → CRITICAL (appropriate — data integrity issue)
- Missing data is never treated as zero

### Recommended: Both Options A and B

Apply the guard clause (Option A) AND add the degraded monitoring alert (Option B). Total change: ~10 lines.

## Verification

1. Simulate a DB connection failure (temporarily use wrong host in DB_CONFIG). Verify: WARNING fires for unavailable metrics, NOT a CRITICAL for sacred memory decrease.
2. With correct DB connection, verify sacred count still reports correctly and CRITICAL would fire if count actually decreased.
3. Monitor #fire-guard for 24 hours after deploy — should see zero false "Sacred memory count DECREASED" alerts.

## Design Principle

Missing data ≠ bad data. A monitoring system that can't distinguish between "I couldn't check" and "I checked and something is wrong" will train operators to ignore CRITICAL alerts. That's how real incidents get missed.
