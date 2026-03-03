#!/usr/bin/env python3
"""Create elisi_state table for Phase 2 valence signal persistence."""

import os
import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}


def migrate():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS elisi_state (
            key         VARCHAR(64) PRIMARY KEY,
            value       NUMERIC(10,6),
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Seed initial values (idempotent)
    cur.execute("""
        INSERT INTO elisi_state (key, value) VALUES
            ('expected_utility', 0.500000),
            ('last_valence', 0.000000),
            ('last_observation_at', 0.000000)
        ON CONFLICT (key) DO NOTHING;
    """)

    conn.commit()

    # Verify
    cur.execute("SELECT key, value FROM elisi_state ORDER BY key;")
    rows = cur.fetchall()
    for k, v in rows:
        print(f"  {k} = {v}")
    print(f"elisi_state table ready ({len(rows)} rows)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    migrate()