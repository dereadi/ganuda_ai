# JR Instruction: Council Feedback Loop — Prediction Outcomes Table

**Task ID**: FEEDBACK-LOOP-001
**Priority**: 3 (of 10)
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

Council Vote Round 2 (Mar 1 2026, confidence 0.70) approved Proposal C: Closed Feedback Loops.
Wire Jr task outcomes back to the authorizing council vote so the council learns from its own decisions.

This is the simplest of three active inference proposals. Minimal cost, maximum learning.
Coyote's dissent on Proposal A is honored — this is NOT mandatory prediction tracking.
This is outcome recording after the fact.

## Acceptance Criteria

1. New table `council_prediction_outcomes` exists on bluefin PostgreSQL
2. Table links a council vote (`audit_hash`) to a Jr task (`task_id`) and records predicted vs actual outcome
3. A helper function in `specialist_council.py` can record an outcome
4. A helper function can query outcomes for a given vote or specialist
5. No changes to existing council voting flow — this is additive only

## Step 1: Create Migration Script

Create `/ganuda/scripts/migrations/council_feedback_loop.py`

```python
#!/usr/bin/env python3
"""
Council Feedback Loop — Prediction Outcomes Table
Council Vote: Round 2 Mar 1 2026 (Proposal C: ADOPT)

Creates the prediction_outcomes table that wires Jr task results
back to the council votes that authorized them.
"""
import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

from ganuda_db import get_connection, get_dict_cursor

DDL = """
CREATE TABLE IF NOT EXISTS council_prediction_outcomes (
    id              SERIAL PRIMARY KEY,
    audit_hash      VARCHAR(64) NOT NULL,
    task_id         VARCHAR(64),
    predicted_outcome TEXT,
    actual_outcome    TEXT,
    delta_notes       TEXT,
    outcome_score     DOUBLE PRECISION,
    specialist_accuracy JSONB DEFAULT '{}',
    recorded_by     VARCHAR(64) NOT NULL DEFAULT 'system',
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed        BOOLEAN NOT NULL DEFAULT FALSE,
    review_notes    TEXT
);

CREATE INDEX IF NOT EXISTS idx_cpo_audit_hash ON council_prediction_outcomes(audit_hash);
CREATE INDEX IF NOT EXISTS idx_cpo_task_id ON council_prediction_outcomes(task_id);
CREATE INDEX IF NOT EXISTS idx_cpo_recorded_at ON council_prediction_outcomes(recorded_at);

COMMENT ON TABLE council_prediction_outcomes IS 'Closed feedback loop: links council votes to Jr task outcomes. Council Vote Mar 1 2026 Proposal C.';
COMMENT ON COLUMN council_prediction_outcomes.audit_hash IS 'FK to council_votes.audit_hash — which vote authorized this work';
COMMENT ON COLUMN council_prediction_outcomes.task_id IS 'FK to jr_work_queue.task_id — which task was the outcome of';
COMMENT ON COLUMN council_prediction_outcomes.predicted_outcome IS 'What the council expected would happen (extracted from consensus/recommendation)';
COMMENT ON COLUMN council_prediction_outcomes.actual_outcome IS 'What actually happened (extracted from jr_work_queue.result)';
COMMENT ON COLUMN council_prediction_outcomes.delta_notes IS 'Human or TPM notes on the gap between prediction and reality';
COMMENT ON COLUMN council_prediction_outcomes.outcome_score IS '0.0 = completely wrong, 1.0 = exactly right, NULL = not yet scored';
COMMENT ON COLUMN council_prediction_outcomes.specialist_accuracy IS 'Per-specialist accuracy for this prediction: {"raven": 0.8, "turtle": 0.9, ...}';
"""

def main():
    conn = None
    try:
        conn = get_connection()
        cur = get_dict_cursor(conn)
        cur.execute(DDL)
        conn.commit()
        print("[OK] council_prediction_outcomes table created")

        # Verify
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'council_prediction_outcomes'
            ORDER BY ordinal_position
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"  {row['column_name']}: {row['data_type']}")
        print(f"\n[OK] {len(rows)} columns verified")
    except Exception as e:
        print(f"[ERROR] {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
```

## Step 2: Add Helper Functions to specialist_council.py

File: `/ganuda/lib/specialist_council.py`

Add these two functions ABOVE the `if __name__ == "__main__":` block at the bottom of the file:

<<<<<<< SEARCH
if __name__ == "__main__":
    # Test
    print("Testing council vote with trails...")
=======
# ── Council Feedback Loop (Council Vote Mar 1 2026, Proposal C) ──

def record_prediction_outcome(
    audit_hash: str,
    task_id: str = None,
    predicted_outcome: str = None,
    actual_outcome: str = None,
    delta_notes: str = None,
    outcome_score: float = None,
    specialist_accuracy: dict = None,
    recorded_by: str = "tpm"
) -> int:
    """Record the outcome of a council-authorized action.

    Links a council vote to what actually happened, closing the feedback loop.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO council_prediction_outcomes
                (audit_hash, task_id, predicted_outcome, actual_outcome,
                 delta_notes, outcome_score, specialist_accuracy, recorded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (audit_hash, task_id, predicted_outcome, actual_outcome,
              delta_notes, outcome_score,
              json.dumps(specialist_accuracy or {}), recorded_by))
        row = cur.fetchone()
        conn.commit()
        return row[0]
    finally:
        if conn:
            conn.close()


def query_prediction_outcomes(audit_hash: str = None, limit: int = 20) -> list:
    """Query prediction outcomes for a vote or recent history.

    Returns list of dicts with outcome data for feedback analysis.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        if audit_hash:
            cur.execute("""
                SELECT id, audit_hash, task_id, predicted_outcome,
                       actual_outcome, delta_notes, outcome_score,
                       specialist_accuracy, recorded_at, reviewed
                FROM council_prediction_outcomes
                WHERE audit_hash = %s
                ORDER BY recorded_at DESC
            """, (audit_hash,))
        else:
            cur.execute("""
                SELECT id, audit_hash, task_id, predicted_outcome,
                       actual_outcome, delta_notes, outcome_score,
                       specialist_accuracy, recorded_at, reviewed
                FROM council_prediction_outcomes
                ORDER BY recorded_at DESC
                LIMIT %s
            """, (limit,))
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Test
    print("Testing council vote with trails...")
>>>>>>> REPLACE

## Notes for Jr

- The migration script is Python, NOT SQL. Run with `python3 /ganuda/scripts/migrations/council_feedback_loop.py`.
- Do NOT modify any existing council voting logic. This is purely additive.
- The `specialist_accuracy` JSONB field is for future use — when we implement Proposal A (opt-in prediction tracking), individual specialist predictions can be scored here.
- The `reviewed` boolean supports a future Owl audit pass.
- No service restart required for the migration. The specialist_council.py changes require gateway restart only if imported there (currently it is not — the helpers are called manually by TPM).
