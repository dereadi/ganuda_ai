# JR INSTRUCTION: Governance Alert Noise Floor — Complete Structural Dissenter Exemption

**Task**: Extend structural dissenter exemptions to the two remaining noisy alert rules in governance_agent.py
**Priority**: P1 (completes the circuit breaker role exemption work from Mar 18)
**Date**: 2026-03-29
**TPM**: Claude Opus
**Story Points**: 2
**Depends On**: drift_detection.py structural dissenter fix (LIVE), governance_agent.py circuit_breaker_open fix (LIVE)

## Problem Statement

The circuit breaker role exemption (JR-CIRCUIT-BREAKER-ROLE-EXEMPTION-MAR18) fixed one of three noise sources. Two remain:

### Noise Source 1: `specialist_concern_spike` (line 67-73)

```python
'condition': lambda m: any(c > 5 for c in m.get('concerns_by_specialist', {}).values()),
```

This fires when ANY specialist raises >5 concerns in 24h. Turtle, Raven, and Coyote raise concerns on EVERY vote by design. With dawn mist + any ad-hoc votes, they easily exceed 5 concerns/day. This rule is permanently firing for them.

### Noise Source 2: `council_confidence_drop` (line 59-65)

```python
'condition': lambda m: m.get('avg_confidence_24h', 1.0) < 0.6,
```

`avg_confidence_24h` is computed as an unweighted AVG across ALL council votes (line 172-178). Structural dissenters vote with lower confidence by design (dissent and concern carry lower confidence scores). They drag the average below 0.6 even when non-dissenter specialists are healthy.

## Task 1: Filter `concerns_by_specialist` (1 SP)

**File**: `/ganuda/daemons/governance_agent.py`

In the `collect_metrics()` function (around line 181-194), the concerns query returns all specialists. The alert condition checks all of them.

**Fix**: Filter structural dissenters from the alert condition, but keep them in the metrics for observability.

**Current** (line 67-68):
```python
'specialist_concern_spike': {
    'condition': lambda m: any(c > 5 for c in m.get('concerns_by_specialist', {}).values()),
```

**New**:
```python
STRUCTURAL_DISSENTERS = {'turtle', 'raven', 'coyote'}

'specialist_concern_spike': {
    'condition': lambda m: any(
        c > 5 for spec, c in m.get('concerns_by_specialist', {}).items()
        if spec not in STRUCTURAL_DISSENTERS
    ),
```

**Do NOT remove structural dissenters from `concerns_by_specialist` itself** — the data is still useful for observability and dawn mist reports. Only filter them from the alert trigger.

## Task 2: Weight confidence excluding structural dissenters (1 SP)

**File**: `/ganuda/daemons/governance_agent.py`

Add a second confidence metric that excludes structural dissenters.

**Current** (lines 172-178):
```python
cur.execute("""
    SELECT AVG(confidence), COUNT(*)
    FROM council_votes
    WHERE created_at > NOW() - INTERVAL '24 hours'
""")
row = cur.fetchone()
metrics['avg_confidence_24h'] = float(row[0]) if row[0] is not None else 1.0
```

**New** — add a filtered query:
```python
# Overall confidence (keep for observability)
cur.execute("""
    SELECT AVG(confidence), COUNT(*)
    FROM council_votes
    WHERE created_at > NOW() - INTERVAL '24 hours'
""")
row = cur.fetchone()
metrics['avg_confidence_24h_all'] = float(row[0]) if row[0] is not None else 1.0
metrics['total_votes_24h'] = int(row[1]) if row[1] else 0

# Non-dissenter confidence (used for alert threshold)
cur.execute("""
    SELECT AVG(confidence), COUNT(*)
    FROM council_votes
    WHERE created_at > NOW() - INTERVAL '24 hours'
      AND specialist_id NOT IN ('turtle', 'raven', 'coyote')
""")
row = cur.fetchone()
metrics['avg_confidence_24h'] = float(row[0]) if row[0] is not None else 1.0
```

The alert rule at line 59 already uses `avg_confidence_24h`, so it will now evaluate against the non-dissenter average. The full average is preserved as `avg_confidence_24h_all` for dawn mist reporting.

## Verification

1. After deploy, wait for next governance cycle (30 min)
2. Check that `specialist_concern_spike` no longer fires for Turtle/Raven/Coyote:
   - Trigger: run a council vote with Coyote dissenting (normal)
   - Verify no Slack alert in #fire-guard
3. Check that `avg_confidence_24h` excludes dissenter drag:
   - If non-dissenter confidence is above 0.6, the alert should stop
4. Verify non-dissenter alerts STILL work:
   - If Eagle Eye or Crawdad spikes >5 concerns, alert SHOULD fire
5. Dawn mist should still report full confidence including dissenters (use `avg_confidence_24h_all`)

## Design Principle

Same as the circuit breaker fix: "States are signals, not silencers." Structural dissent is healthy governance. The alert system should detect when non-dissenter specialists go off-pattern, not when dissenters do their job.

---

FOR SEVEN GENERATIONS
