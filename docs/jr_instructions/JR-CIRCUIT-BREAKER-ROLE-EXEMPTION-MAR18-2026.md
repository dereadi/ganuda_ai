# JR INSTRUCTION: Circuit Breaker Role Exemption — Structural Dissenters

**Task**: Fix circuit breaker false positives for specialists whose role is to raise concerns. Turtle, Raven, and Coyote are permanently OPEN because their concern patterns ARE their function.
**Priority**: P0 (blocking — degrades council confidence, floods #fire-guard with noise)
**Date**: 2026-03-18
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: drift_detection.py (LIVE), governance_agent.py (LIVE), specialist_health table (LIVE)
**Thermal Context**: 27+ hours of continuous DRIFT ALERT spam, council avg confidence 0.37

## Problem Statement

The circuit breaker threshold is `concern_count >= 7 out of last 10 = OPEN`. Three specialists raise concerns on EVERY vote by design:

| Specialist | Concern Type | Role | Records with Concern |
|---|---|---|---|
| **Turtle** | `7GEN CONCERN` | Seven-generation impact assessment | 10/12 |
| **Raven** | `STRATEGY CONCERN` | Strategic patience, timing analysis | 11/12 |
| **Coyote** | `DISSENT` | Devil's advocate, adversarial testing | 10+/12 |

These specialists can NEVER age out because every new council vote generates a new concern. The circuit breaker is treating role-appropriate behavior as malfunction.

**Consequences**:
- Turtle and Raven OPEN for 27+ hours (Coyote also OPEN)
- Council avg confidence dragged to 0.37-0.52 (below 0.6 threshold)
- #fire-guard flooded with 50+ DRIFT ALERT messages in 27 hours
- Real alerts buried in noise — the boy who cried wolf

## Root Cause

`check_circuit_breaker()` in `/ganuda/lib/drift_detection.py` (line 169) counts `had_concern = True` without distinguishing between:
- **Role concerns**: Specialist raising concerns as part of their defined function (Turtle ALWAYS evaluates 7-gen impact, Raven ALWAYS evaluates strategic timing)
- **Anomaly concerns**: Specialist flagging something genuinely wrong (e.g., Eagle Eye detecting drift, Crawdad flagging a security issue)

The fix must distinguish these two cases.

## Task 1: Add Role-Aware Concern Classification (2 SP)

**File**: `/ganuda/lib/drift_detection.py`

Modify `check_circuit_breaker()` to recognize structural dissenter roles.

**Current code** (line 199):
```python
concern_count = sum(1 for row in rows if row[0] is True)
```

**New logic**:

```python
# Structural dissenters — concern is their role, not a malfunction signal
STRUCTURAL_DISSENTERS = {
    'turtle': '7GEN CONCERN',
    'raven': 'STRATEGY CONCERN',
    'coyote': 'DISSENT',
}

def check_circuit_breaker(specialist_id: str) -> str:
    # ... existing query for last 10 records ...
    # Need to also SELECT concern_type in the query (add to column list)

    rows = cur.fetchall()  # Now: (had_concern, coherence_score, concern_type)

    if not rows:
        return 'CLOSED'

    # For structural dissenters: only count concerns that DON'T match their role type
    # Turtle raising "7GEN CONCERN" is normal. Turtle raising "SECURITY CONCERN" is anomalous.
    expected_concern_type = STRUCTURAL_DISSENTERS.get(specialist_id)

    if expected_concern_type:
        # Only count UNEXPECTED concerns toward the breaker
        concern_count = sum(
            1 for row in rows
            if row[0] is True and row[2] != expected_concern_type
        )
    else:
        # Non-dissenter: all concerns count (existing behavior)
        concern_count = sum(1 for row in rows if row[0] is True)

    # ... rest of threshold logic unchanged ...
```

**Key principle**: A structural dissenter raising their expected concern type is signal, not noise. Only UNEXPECTED concern types (Turtle raising a SECURITY CONCERN, Raven raising a DISSENT) should trigger the breaker.

**Update the SELECT query** to include `concern_type`:
```python
cur.execute("""
    SELECT had_concern, coherence_score, concern_type
    FROM specialist_health
    WHERE specialist_id = %s
    ORDER BY measured_at DESC
    LIMIT 10
""", (specialist_id,))
```

## Task 2: Reduce Alert Noise (1 SP)

**File**: `/ganuda/daemons/governance_agent.py`

The `circuit_breaker_open` alert rule fires every 30 minutes and has been doing so for 27+ hours. Two fixes:

### 2a: Exclude structural dissenters from the alert count

In `collect_circuit_breaker_metrics()` (line 279), add filtering:

```python
STRUCTURAL_DISSENTERS = {'turtle', 'raven', 'coyote'}

for specialist, state in states.items():
    if state == 'OPEN':
        if specialist in STRUCTURAL_DISSENTERS:
            # Track separately — role-appropriate, not alertable
            metrics.setdefault('role_open_specialists', []).append(specialist)
        else:
            metrics['open_breakers'] += 1
            metrics['open_specialists'].append(specialist)
    elif state == 'HALF_OPEN':
        metrics['half_open_breakers'] += 1
    else:
        metrics['closed_breakers'] += 1
```

This way, Turtle/Raven/Coyote being OPEN doesn't trigger the alert. But if Eagle Eye, Crawdad, Spider, Gecko, or Peace Chief goes OPEN — that IS a real problem and SHOULD alert.

### 2b: Log structural dissenter states at INFO, not WARNING

Add an INFO log when structural dissenters are in OPEN state (expected) vs WARNING for non-structural (unexpected):

```python
if metrics.get('role_open_specialists'):
    logger.info(f"Structural dissenters in expected OPEN state: {metrics['role_open_specialists']}")
```

## Task 3: Reset Turtle/Raven/Coyote After Fix (0 SP, P-Day)

After deploying Tasks 1 and 2, the next council vote will recompute breaker states with the new logic. Turtle, Raven, and Coyote should transition to CLOSED (since their role-appropriate concerns no longer count toward the threshold).

**Verify**: Wait for next dawn mist vote (6:15 AM), then check:
```sql
SELECT DISTINCT ON (specialist_id) specialist_id, circuit_breaker_state
FROM specialist_health
ORDER BY specialist_id, measured_at DESC;
```

All specialists should show CLOSED unless there's a genuine anomaly.

## Verification

1. After fix: Next dawn mist vote at 6:15 AM should show Turtle, Raven, Coyote as CLOSED
2. Council avg confidence should recover above 0.6 within 24 hours
3. #fire-guard should stop getting DRIFT ALERT spam for circuit breakers
4. If Turtle raises a SECURITY CONCERN (not 7GEN), the breaker SHOULD still trip — verify this path works
5. Non-structural specialists (Eagle Eye, Crawdad, etc.) should still trip normally on 7/10 concerns

## Design Principle

Per the Circuit Breaker Reform (Mar 2 2026): "States are signals, not silencers." This fix refines the signal — structural dissent is healthy governance, not malfunction. The breaker should detect when a specialist goes OFF-ROLE, not when it stays ON-ROLE.

Partner's BSM heritage: You don't page the ops team because the monitoring system is doing its job. You page when it stops.
