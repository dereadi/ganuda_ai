# Jr Instructions: TiMem Foundation Integration (P0)

## Metadata
```yaml
task_id: timem_foundation_p0
priority: P0_EMERGENCY
council_vote: b856f5a9045b6596
tpm_approved: true
assigned_to: it_triad_jr
estimated_duration: 8 days
ultrathink: /ganuda/docs/ultrathink/ULTRATHINK-TIMEM-FOUNDATION-JAN19-2026.md
```

## Context

Council approved Turtle's reordering. Memory foundation must be fixed before layering reasoning systems. Current state: 7,525 memories with 0% consolidation, inconsistent stages, no hierarchy.

## Task 1: Schema Migration

**File**: `/ganuda/sql/timem_schema_migration.sql`

```sql
-- TiMem Schema Migration for thermal_memory_archive
-- Cherokee AI Federation - January 2026

BEGIN;

-- Add Temporal Memory Tree columns
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS parent_memory_id INTEGER REFERENCES thermal_memory_archive(id);

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS tree_level INTEGER DEFAULT 0;
-- 0=leaf, 1=day, 2=week, 3=month, 4=quarter, 5=year, 6=generation

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS children_count INTEGER DEFAULT 0;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS consolidated_from JSONB DEFAULT '[]'::jsonb;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS consolidation_timestamp TIMESTAMP;

-- Create indexes for tree traversal
CREATE INDEX IF NOT EXISTS idx_tma_parent ON thermal_memory_archive(parent_memory_id);
CREATE INDEX IF NOT EXISTS idx_tma_level ON thermal_memory_archive(tree_level);
CREATE INDEX IF NOT EXISTS idx_tma_consolidation ON thermal_memory_archive(consolidation_score)
    WHERE consolidation_score > 0;

-- Consolidation job tracking
CREATE TABLE IF NOT EXISTS memory_consolidation_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    memories_processed INTEGER DEFAULT 0,
    memories_consolidated INTEGER DEFAULT 0,
    tree_nodes_created INTEGER DEFAULT 0,
    source_level INTEGER,
    target_level INTEGER,
    status VARCHAR(50) DEFAULT 'running',
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Backfill: Set all existing memories to leaf level
UPDATE thermal_memory_archive
SET tree_level = 0
WHERE tree_level IS NULL;

COMMIT;

-- Verify
SELECT
    'Schema migration complete' as status,
    COUNT(*) as total_memories,
    COUNT(*) FILTER (WHERE tree_level = 0) as leaf_memories
FROM thermal_memory_archive;
```

**Run with**:
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/timem_schema_migration.sql
```

## Task 2: Consolidation Daemon

**File**: `/ganuda/daemons/timem_consolidator.py`

```python
#!/usr/bin/env python3
"""
TiMem Memory Consolidator Daemon
Cherokee AI Federation - P0 Foundation

Consolidates thermal_memory_archive into hierarchical Temporal Memory Tree.
Based on TiMem paper (arXiv 2601.02845).

Run as: python3 timem_consolidator.py [--once] [--level N]
"""

import os
import sys
import json
import time
import logging
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import requests

# Configuration
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

LLM_GATEWAY = os.environ.get('LLM_GATEWAY', 'http://localhost:8080')
API_KEY = os.environ.get('CHEROKEE_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')

# Consolidation thresholds
CONSOLIDATION_THRESHOLDS = {
    0: {'min_memories': 5, 'age_days': 7},    # Leaf → Daily
    1: {'min_memories': 5, 'age_days': 30},   # Daily → Weekly
    2: {'min_memories': 4, 'age_days': 90},   # Weekly → Monthly
    3: {'min_memories': 3, 'age_days': 365},  # Monthly → Quarterly
    4: {'min_memories': 4, 'age_days': 1825}, # Quarterly → Yearly
    5: {'min_memories': 25, 'age_days': 6388} # Yearly → Generational (175 years / 7)
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('timem_consolidator')


class TiMemConsolidator:
    def __init__(self):
        self.conn = None
        self.job_id = None

    def connect(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def start_job(self, job_type: str, source_level: int, target_level: int):
        """Record consolidation job start."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memory_consolidation_jobs
                (job_type, source_level, target_level)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (job_type, source_level, target_level))
            self.job_id = cur.fetchone()[0]
            self.conn.commit()
        logger.info(f"Started consolidation job {self.job_id}: {job_type}")
        return self.job_id

    def complete_job(self, processed: int, consolidated: int, nodes_created: int, error: str = None):
        """Record consolidation job completion."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE memory_consolidation_jobs
                SET completed_at = NOW(),
                    memories_processed = %s,
                    memories_consolidated = %s,
                    tree_nodes_created = %s,
                    status = %s,
                    error_message = %s
                WHERE id = %s
            """, (
                processed, consolidated, nodes_created,
                'failed' if error else 'completed',
                error, self.job_id
            ))
            self.conn.commit()
        logger.info(f"Job {self.job_id} complete: {consolidated}/{processed} consolidated, {nodes_created} nodes created")

    def get_memories_for_consolidation(self, level: int, time_bucket: str) -> list:
        """Get memories at given level ready for consolidation."""
        threshold = CONSOLIDATION_THRESHOLDS.get(level, {'min_memories': 5, 'age_days': 7})

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, memory_hash, original_content, temperature_score,
                       created_at, current_stage
                FROM thermal_memory_archive
                WHERE tree_level = %s
                  AND consolidation_score = 0
                  AND created_at < NOW() - INTERVAL '%s days'
                  AND DATE_TRUNC(%s, created_at) = DATE_TRUNC(%s, %s::timestamp)
                ORDER BY created_at
            """, (level, threshold['age_days'], time_bucket, time_bucket, time_bucket))
            return cur.fetchall()

    def summarize_memories(self, memories: list) -> str:
        """Use LLM to create consolidated summary."""
        if not memories:
            return ""

        # Create context from memories
        memory_texts = [m['original_content'][:500] for m in memories[:20]]  # Limit context
        prompt = f"""Consolidate these {len(memories)} Cherokee AI Federation memories into a single summary that captures the key patterns, decisions, and wisdom. Preserve cultural significance.

Memories:
{chr(10).join(f"- {t}" for t in memory_texts)}

Create a consolidated summary (2-3 sentences) that captures the essence:"""

        try:
            response = requests.post(
                f"{LLM_GATEWAY}/v1/chat/completions",
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                json={
                    'model': 'cherokee',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 200,
                    'temperature': 0.3
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            # Fallback: simple concatenation
            return f"Consolidated {len(memories)} memories from {memories[0]['created_at'].date()}"

    def create_consolidated_node(self, summary: str, source_memories: list, target_level: int) -> int:
        """Create a new consolidated memory node."""
        source_ids = [m['id'] for m in source_memories]
        avg_temp = sum(m['temperature_score'] for m in source_memories) / len(source_memories)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, original_content, current_stage,
                    temperature_score, tree_level, consolidated_from,
                    consolidation_score, consolidation_timestamp,
                    children_count, created_at
                ) VALUES (
                    md5(%s || NOW()::text),
                    %s,
                    'CONSOLIDATED',
                    %s,
                    %s,
                    %s,
                    1.0,
                    NOW(),
                    %s,
                    %s
                )
                RETURNING id
            """, (
                summary,
                summary,
                avg_temp * 0.9,  # Slightly reduce temperature
                target_level,
                json.dumps(source_ids),
                len(source_ids),
                source_memories[0]['created_at']
            ))
            node_id = cur.fetchone()[0]

            # Update source memories
            cur.execute("""
                UPDATE thermal_memory_archive
                SET parent_memory_id = %s,
                    consolidation_score = 1.0,
                    temperature_score = temperature_score * 0.8
                WHERE id = ANY(%s)
            """, (node_id, source_ids))

            self.conn.commit()
            return node_id

    def consolidate_level(self, source_level: int):
        """Consolidate all memories at source_level to source_level+1."""
        target_level = source_level + 1
        time_buckets = {0: 'day', 1: 'week', 2: 'month', 3: 'quarter', 4: 'year'}
        time_bucket = time_buckets.get(source_level, 'year')

        job_type = f"level_{source_level}_to_{target_level}"
        self.start_job(job_type, source_level, target_level)

        processed = 0
        consolidated = 0
        nodes_created = 0

        try:
            # Get distinct time buckets with enough memories
            threshold = CONSOLIDATION_THRESHOLDS[source_level]
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT DATE_TRUNC('{time_bucket}', created_at) as bucket,
                           COUNT(*) as count
                    FROM thermal_memory_archive
                    WHERE tree_level = %s
                      AND consolidation_score = 0
                      AND created_at < NOW() - INTERVAL '%s days'
                    GROUP BY bucket
                    HAVING COUNT(*) >= %s
                    ORDER BY bucket
                """, (source_level, threshold['age_days'], threshold['min_memories']))
                buckets = cur.fetchall()

            for bucket_row in buckets:
                bucket_date = bucket_row['bucket']

                # Get memories in this bucket
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(f"""
                        SELECT id, memory_hash, original_content, temperature_score,
                               created_at, current_stage
                        FROM thermal_memory_archive
                        WHERE tree_level = %s
                          AND consolidation_score = 0
                          AND DATE_TRUNC('{time_bucket}', created_at) = %s
                        ORDER BY created_at
                    """, (source_level, bucket_date))
                    memories = cur.fetchall()

                if len(memories) >= threshold['min_memories']:
                    processed += len(memories)

                    # Summarize and create consolidated node
                    summary = self.summarize_memories(memories)
                    node_id = self.create_consolidated_node(summary, memories, target_level)

                    consolidated += len(memories)
                    nodes_created += 1
                    logger.info(f"Consolidated {len(memories)} memories into node {node_id}")

            self.complete_job(processed, consolidated, nodes_created)

        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
            self.complete_job(processed, consolidated, nodes_created, str(e))
            raise

        return processed, consolidated, nodes_created

    def run_full_consolidation(self):
        """Run consolidation for all levels."""
        total_processed = 0
        total_consolidated = 0
        total_nodes = 0

        for level in range(6):  # 0 through 5
            try:
                p, c, n = self.consolidate_level(level)
                total_processed += p
                total_consolidated += c
                total_nodes += n
            except Exception as e:
                logger.error(f"Level {level} consolidation failed: {e}")

        logger.info(f"Full consolidation complete: {total_consolidated}/{total_processed} memories, {total_nodes} nodes")
        return total_processed, total_consolidated, total_nodes

    def close(self):
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='TiMem Memory Consolidator')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--level', type=int, help='Consolidate specific level only')
    parser.add_argument('--interval', type=int, default=3600, help='Seconds between runs (default: 3600)')
    args = parser.parse_args()

    consolidator = TiMemConsolidator()

    try:
        consolidator.connect()

        if args.once:
            if args.level is not None:
                consolidator.consolidate_level(args.level)
            else:
                consolidator.run_full_consolidation()
        else:
            logger.info(f"Starting TiMem consolidator daemon (interval: {args.interval}s)")
            while True:
                try:
                    if args.level is not None:
                        consolidator.consolidate_level(args.level)
                    else:
                        consolidator.run_full_consolidation()
                except Exception as e:
                    logger.error(f"Consolidation run failed: {e}")

                time.sleep(args.interval)

    finally:
        consolidator.close()


if __name__ == '__main__':
    main()
```

## Task 3: Systemd Service

**File**: `/etc/systemd/system/timem-consolidator.service`

```ini
[Unit]
Description=TiMem Memory Consolidator - Cherokee AI Federation
After=network-online.target postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/daemons
ExecStart=/home/dereadi/cherokee_venv/bin/python3 timem_consolidator.py --interval 3600
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Deploy**:
```bash
sudo cp /ganuda/daemons/timem-consolidator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable timem-consolidator
sudo systemctl start timem-consolidator
```

## Task 4: Fix Stage/Temperature Consistency

```sql
-- Fix inconsistent stage temperatures
UPDATE thermal_memory_archive
SET current_stage = CASE
    WHEN temperature_score >= 90 THEN 'WHITE_HOT'
    WHEN temperature_score >= 75 THEN 'RED_HOT'
    WHEN temperature_score >= 60 THEN 'HOT'
    WHEN temperature_score >= 45 THEN 'WARM'
    WHEN temperature_score >= 30 THEN 'COOL'
    WHEN temperature_score >= 15 THEN 'COLD'
    ELSE 'CRYSTALLIZED'
END
WHERE consolidation_score = 0;

-- Verify fix
SELECT current_stage, COUNT(*),
       ROUND(AVG(temperature_score)::numeric, 1) as avg_temp
FROM thermal_memory_archive
GROUP BY current_stage
ORDER BY avg_temp DESC;
```

## Task 5: Complexity-Aware Recall

**File**: `/ganuda/lib/timem_recall.py`

```python
"""
TiMem Complexity-Aware Memory Recall
Cherokee AI Federation
"""

def recall_memories(query: str, complexity: str = 'auto', limit: int = 10):
    """
    Recall memories using TiMem hierarchy.

    complexity:
        'simple' - Leaf nodes only (specific memories)
        'moderate' - Daily/weekly consolidated
        'complex' - Monthly/quarterly patterns
        'cultural' - Yearly/generational wisdom
        'auto' - Determine from query
    """
    level_map = {
        'simple': [0],
        'moderate': [0, 1, 2],
        'complex': [2, 3, 4],
        'cultural': [4, 5, 6],
        'auto': None
    }

    if complexity == 'auto':
        # Use query analysis to determine complexity
        cultural_keywords = ['cherokee', 'seven generations', 'wisdom', 'tradition', 'values']
        complex_keywords = ['pattern', 'history', 'trend', 'always', 'usually']

        query_lower = query.lower()
        if any(k in query_lower for k in cultural_keywords):
            levels = [4, 5, 6]
        elif any(k in query_lower for k in complex_keywords):
            levels = [2, 3, 4]
        else:
            levels = [0, 1, 2]
    else:
        levels = level_map.get(complexity, [0, 1, 2])

    # Query with tree level filter
    # ... implementation continues
```

## Success Criteria

- [ ] Schema migration complete (new columns added)
- [ ] consolidation_score > 0 for memories older than 7 days
- [ ] Tree structure with parent-child relationships
- [ ] Consolidation daemon running every hour
- [ ] Stage/temperature consistency fixed
- [ ] Complexity-aware recall functional

## Verification Commands

```bash
# Check schema
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT column_name FROM information_schema.columns
WHERE table_name = 'thermal_memory_archive' AND column_name LIKE '%tree%' OR column_name LIKE '%parent%';"

# Check consolidation progress
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT tree_level, COUNT(*),
       ROUND(AVG(consolidation_score)::numeric, 2) as avg_consolidation
FROM thermal_memory_archive GROUP BY tree_level ORDER BY tree_level;"

# Check consolidation jobs
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT * FROM memory_consolidation_jobs ORDER BY started_at DESC LIMIT 5;"
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Strong foundations last 175 years. Turtle wisdom guides our path."*
