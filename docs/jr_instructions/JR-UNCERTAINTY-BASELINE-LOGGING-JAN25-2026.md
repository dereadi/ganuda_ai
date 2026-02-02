# JR Instruction: Uncertainty Baseline Logging

**Task ID:** JR-UNCERTAINTY-BASELINE-001
**Priority:** P0 (Phase 0 - Observe First)
**Type:** enhancement
**Assigned:** Software Engineer Jr.
**Estimated Complexity:** Low

---

## Objective

Add uncertainty/confidence logging to the existing SpecialistCouncil without changing its behavior. This establishes baseline metrics before we implement AUQ enhancements.

**Philosophy:** Observe before changing. Measure what we have.

---

## Context

The Council already makes decisions. We need to understand:
1. How much agreement exists between specialists?
2. How often do we see dissent?
3. What topics generate the most uncertainty?

This data will guide our AUQ integration strategy.

---

## Implementation

### File to Modify

`/ganuda/lib/specialist_council.py`

### Changes Required

1. **Add uncertainty computation method:**

```python
def _compute_implicit_uncertainty(self, votes: list) -> dict:
    """
    Compute implicit uncertainty from vote patterns.
    Does NOT change behavior - logging only.
    """
    if not votes:
        return {"uncertainty": 1.0, "agreement_ratio": 0.0, "dissent_count": 0}

    # Extract positions
    positions = [v.get('position', v.get('vote', 'UNKNOWN')) for v in votes]

    # Count agreement
    if positions:
        most_common = max(set(positions), key=positions.count)
        agreement_count = positions.count(most_common)
        agreement_ratio = agreement_count / len(positions)
    else:
        agreement_ratio = 0.0

    # Count dissent
    dissent_positions = ['DISSENT', 'OPPOSE', 'BLOCK', 'REJECT']
    dissent_count = sum(1 for p in positions if p.upper() in dissent_positions)

    # Uncertainty = 1 - agreement
    uncertainty = 1 - agreement_ratio

    return {
        "uncertainty": round(uncertainty, 3),
        "agreement_ratio": round(agreement_ratio, 3),
        "dissent_count": dissent_count,
        "total_votes": len(positions),
        "positions": positions
    }
```

2. **Add logging to deliberate method:**

Find the `deliberate` method (or equivalent decision method) and add logging:

```python
def deliberate(self, topic: str, context: dict = None) -> dict:
    # ... existing code to collect votes ...

    # NEW: Log uncertainty metrics (doesn't change behavior)
    try:
        uncertainty_metrics = self._compute_implicit_uncertainty(votes)
        self._log_uncertainty_baseline(topic, uncertainty_metrics)
    except Exception as e:
        print(f"[Council] Uncertainty logging failed (non-fatal): {e}")

    # ... existing code to return result ...
```

3. **Add logging method:**

```python
def _log_uncertainty_baseline(self, topic: str, metrics: dict):
    """Log uncertainty metrics to thermal memory for baseline analysis."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
        with conn.cursor() as cur:
            import json
            from datetime import datetime
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, 50.0, %s)
            """, (
                f"council-uncertainty-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                f"Council uncertainty baseline\n"
                f"Topic: {topic[:200]}\n"
                f"Uncertainty: {metrics['uncertainty']:.1%}\n"
                f"Agreement: {metrics['agreement_ratio']:.1%}\n"
                f"Dissent: {metrics['dissent_count']}/{metrics['total_votes']}",
                json.dumps({
                    "type": "council_uncertainty_baseline",
                    "phase": "observability",
                    **metrics
                })
            ))
            conn.commit()
        conn.close()
    except Exception as e:
        # Non-fatal - don't break Council if logging fails
        print(f"[Council] Baseline logging error: {e}")
```

---

## Testing

1. **Manual test:**
```python
from lib.specialist_council import SpecialistCouncil

council = SpecialistCouncil()
result = council.deliberate("Test topic for uncertainty logging", {})
print(result)
```

2. **Verify logging:**
```sql
SELECT memory_hash, original_content, metadata
FROM thermal_memory_archive
WHERE metadata->>'type' = 'council_uncertainty_baseline'
ORDER BY created_at DESC
LIMIT 5;
```

---

## Success Criteria

- [ ] `_compute_implicit_uncertainty` method added
- [ ] Logging integrated into deliberate() without changing behavior
- [ ] Test shows uncertainty metrics in thermal_memory_archive
- [ ] No existing tests broken
- [ ] Council decisions unchanged (behavior preserved)

---

## Rollback

If any issues:
```python
# Simply remove the try/except block that calls _log_uncertainty_baseline
# The method can stay - it's harmless if not called
```

---

## Notes

- This is OBSERVABILITY ONLY - no behavior changes
- Logging failures are non-fatal (catch and continue)
- We need ~1 week of data before Phase 1
- Temperature 50.0 = medium priority for thermal memory

---

## For Seven Generations

Before we change how the Council thinks, we must understand how it thinks today. This logging is our gift to future developers who will inherit this system.
