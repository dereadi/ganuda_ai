#!/usr/bin/env python3
"""
Observational Memory Schema — Phase 1
Council Votes: #c064bf44b624b56f, #f0ff4f4e44416d6d

Creates:
  - observational_memory_archive: Compressed observations from thermal memories
  - observational_relationships: Links between observations (causal, temporal, thematic)
  - Adds is_observed flag to thermal_memory_archive

CONSTRAINT: thermal_memory_archive is APPEND-ONLY. We only ADD a column, never modify existing data.
"""

import os
import sys
import psycopg2

SECRETS_FILE = "/ganuda/config/secrets.env"


def load_secrets():
    secrets = {}
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    secrets[key] = val
    return secrets


def run_migration():
    secrets = load_secrets()
    conn = psycopg2.connect(
        host=secrets.get("CHEROKEE_DB_HOST", "192.168.132.222"),
        dbname=secrets.get("CHEROKEE_DB_NAME", "zammad_production"),
        user=secrets.get("CHEROKEE_DB_USER", "claude"),
        password=secrets.get("CHEROKEE_DB_PASS", ""),
        port=int(secrets.get("CHEROKEE_DB_PORT", "5432"))
    )
    cur = conn.cursor()

    # 1. Observational Memory Archive
    cur.execute("""
        CREATE TABLE IF NOT EXISTS observational_memory_archive (
            id SERIAL PRIMARY KEY,

            -- Source tracking (which thermal memories were observed)
            source_memory_ids INTEGER[] NOT NULL,
            source_memory_hashes TEXT[] NOT NULL,

            -- Compressed observation
            observation TEXT NOT NULL,
            observation_type VARCHAR(50) NOT NULL DEFAULT 'pattern',
            -- Types: pattern, anomaly, trend, correlation, sacred_echo

            -- Three-date temporal model (Mastra-inspired)
            observed_at TIMESTAMP NOT NULL DEFAULT NOW(),
            first_occurrence TIMESTAMP,
            last_occurrence TIMESTAMP,

            -- Quality and importance
            confidence FLOAT DEFAULT 0.5,
            priority_flag BOOLEAN DEFAULT FALSE,
            sacred_pattern BOOLEAN DEFAULT FALSE,

            -- Embeddings for retrieval
            embedding VECTOR(1024),

            -- Metadata
            observer_model VARCHAR(100),
            observation_hash VARCHAR(64) NOT NULL,
            metadata JSONB DEFAULT '{}',
            tags TEXT[],

            -- Audit
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_obs_mem_type
            ON observational_memory_archive (observation_type);
        CREATE INDEX IF NOT EXISTS idx_obs_mem_priority
            ON observational_memory_archive (priority_flag) WHERE priority_flag = true;
        CREATE INDEX IF NOT EXISTS idx_obs_mem_sacred
            ON observational_memory_archive (sacred_pattern) WHERE sacred_pattern = true;
        CREATE INDEX IF NOT EXISTS idx_obs_mem_hash
            ON observational_memory_archive (observation_hash);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_mem_unique_hash
            ON observational_memory_archive (observation_hash);
    """)
    print("[MIGRATION] Created observational_memory_archive table")

    # 2. Observational Relationships
    cur.execute("""
        CREATE TABLE IF NOT EXISTS observational_relationships (
            id SERIAL PRIMARY KEY,
            source_observation_id INTEGER REFERENCES observational_memory_archive(id),
            target_observation_id INTEGER REFERENCES observational_memory_archive(id),
            relationship_type VARCHAR(50) NOT NULL,
            -- Types: causal, temporal, thematic, contradicts, supersedes
            strength FLOAT DEFAULT 0.5,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(source_observation_id, target_observation_id, relationship_type)
        );

        CREATE INDEX IF NOT EXISTS idx_obs_rel_source
            ON observational_relationships (source_observation_id);
        CREATE INDEX IF NOT EXISTS idx_obs_rel_target
            ON observational_relationships (target_observation_id);
    """)
    print("[MIGRATION] Created observational_relationships table")

    # 3. Add is_observed flag to thermal_memory_archive (APPEND-ONLY — safe column add)
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE thermal_memory_archive ADD COLUMN is_observed BOOLEAN DEFAULT FALSE;
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END $$;
    """)
    print("[MIGRATION] Added is_observed column to thermal_memory_archive")

    # 4. Create pgvector index on observational embeddings
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_obs_mem_embedding
            ON observational_memory_archive
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);
    """)
    print("[MIGRATION] Created pgvector IVFFlat index on observational embeddings")

    conn.commit()
    cur.close()
    conn.close()
    print("[MIGRATION] Observational Memory schema deployed successfully")


if __name__ == "__main__":
    run_migration()