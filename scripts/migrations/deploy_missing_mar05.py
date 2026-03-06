"""
Deploy missing migrations — council_feedback_loop + longhouse schema.
Tech debt batch 3, March 5 2026.
Safe to run multiple times (all CREATE IF NOT EXISTS).
"""

import psycopg2
import os
import sys

def get_connection():
    try:
        sys.path.insert(0, '/ganuda/lib')
        from ganuda_db import get_db_config
        return psycopg2.connect(**get_db_config())
    except Exception:
        return psycopg2.connect(
            host='192.168.132.222',
            dbname='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )

def deploy_council_feedback_loop(cur):
    """Council prediction outcome tracking — measures vote accuracy over time."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS council_prediction_outcomes (
            id SERIAL PRIMARY KEY,
            vote_hash VARCHAR(64) NOT NULL,
            prediction_type VARCHAR(50) NOT NULL,
            predicted_outcome TEXT,
            actual_outcome TEXT,
            accuracy_score FLOAT,
            evaluated_at TIMESTAMPTZ DEFAULT NOW(),
            evaluated_by VARCHAR(50) DEFAULT 'system',
            metadata JSONB DEFAULT '{}'
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cpo_vote_hash ON council_prediction_outcomes(vote_hash);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cpo_type ON council_prediction_outcomes(prediction_type);
    """)
    print("  council_prediction_outcomes: CREATED")

def deploy_longhouse_schema(cur):
    """Longhouse sessions — Outer Council governance records."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS longhouse_sessions (
            id SERIAL PRIMARY KEY,
            session_hash VARCHAR(64) NOT NULL UNIQUE,
            topic TEXT NOT NULL,
            participants JSONB DEFAULT '[]',
            resolutions JSONB DEFAULT '[]',
            resolution_type VARCHAR(30) DEFAULT 'consensus',
            consensus_score FLOAT,
            sacred_dissent BOOLEAN DEFAULT FALSE,
            dissenter VARCHAR(50),
            dissent_reason TEXT,
            thermal_id INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ls_session_hash ON longhouse_sessions(session_hash);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ls_resolution_type ON longhouse_sessions(resolution_type);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ls_created ON longhouse_sessions(created_at);
    """)
    print("  longhouse_sessions: CREATED")

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("Deploying missing migrations...")
    deploy_council_feedback_loop(cur)
    deploy_longhouse_schema(cur)

    conn.commit()

    # Verify
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name IN ('council_prediction_outcomes', 'longhouse_sessions')
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nVerification: {len(tables)}/2 tables exist: {tables}")
    assert len(tables) == 2, f"Missing tables! Found: {tables}"
    print("All migrations deployed successfully.")

    conn.close()

if __name__ == '__main__':
    main()