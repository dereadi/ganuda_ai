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