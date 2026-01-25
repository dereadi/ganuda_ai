# Jr Task: Context Graph Enhancement to Thermal Memory

**Date**: January 5, 2026
**Priority**: MEDIUM
**Target Node**: bluefin (192.168.132.222)
**Database**: zammad_production
**Council Vote**: APPROVED (88% confidence)
**Research Basis**: arXiv:2406.11160 (Context Graphs)

## Background

The Council approved enhancing thermal_memory_archive from flat storage to a Context Graph structure. This enables:

- **Provenance tracking** - Which Triad/Jr created each memory, from which node
- **Temporal validity** - When is this knowledge valid (not just when created)
- **Relationship graphs** - Links between memories for multi-hop reasoning
- **CGR³ paradigm** - Retrieve → Rank → Reason over structured knowledge

## Architecture Overview

```
BEFORE (Flat Storage):
┌─────────────────────────────────────────┐
│ thermal_memory_archive                  │
│ - content, temperature, created_at      │
│ - No relationships, no provenance       │
└─────────────────────────────────────────┘

AFTER (Context Graph):
┌─────────────────────────────────────────────────────────────┐
│ thermal_memory_archive                                      │
│ + source_triad (IT/Data/Ops/Jr)                            │
│ + source_node (redfin/bluefin/greenfin)                    │
│ + source_session (conversation ID)                          │
│ + valid_from / valid_until (temporal window)               │
│ + relationships (JSONB graph edges)                         │
│                                                             │
│    ┌─────┐  supersedes  ┌─────┐  references  ┌─────┐      │
│    │ M1  │─────────────▶│ M2  │─────────────▶│ M3  │      │
│    └─────┘              └─────┘              └─────┘      │
│       │                    │                               │
│       │ extends            │ contradicts                   │
│       ▼                    ▼                               │
│    ┌─────┐              ┌─────┐                           │
│    │ M4  │              │ M5  │                           │
│    └─────┘              └─────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Schema Enhancement (Non-Breaking)

**Objective**: Add new columns as nullable, preserve existing functionality

```sql
-- Connect to zammad_production on bluefin
-- All changes are additive - existing queries continue to work

-- 1. Add provenance columns
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS source_triad VARCHAR(50);

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS source_node VARCHAR(50);

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS source_session VARCHAR(100);

-- 2. Add temporal validity columns
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS valid_until TIMESTAMPTZ;

-- 3. Add relationships graph column
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS relationships JSONB DEFAULT '{}';

-- 4. Add schema version for compatibility tracking
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS context_version INTEGER DEFAULT 1;

-- 5. Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_thermal_source_triad
ON thermal_memory_archive (source_triad);

CREATE INDEX IF NOT EXISTS idx_thermal_source_node
ON thermal_memory_archive (source_node);

CREATE INDEX IF NOT EXISTS idx_thermal_source_session
ON thermal_memory_archive (source_session);

CREATE INDEX IF NOT EXISTS idx_thermal_valid_range
ON thermal_memory_archive (valid_from, valid_until);

-- GIN index for JSONB relationship queries
CREATE INDEX IF NOT EXISTS idx_thermal_relationships
ON thermal_memory_archive USING GIN (relationships);

-- 6. Create compatibility view for legacy consumers
CREATE OR REPLACE VIEW thermal_memory_archive_v1 AS
SELECT
    id, memory_hash, original_content, compressed_content,
    temperature_score, memory_type, sacred_pattern, created_at
FROM thermal_memory_archive;

COMMENT ON VIEW thermal_memory_archive_v1 IS
'Legacy compatibility view - use thermal_memory_archive directly for context graph features';
```

## Phase 2: Backfill Existing Memories

**Objective**: Populate new columns for 6700+ existing memories

```sql
-- Set defaults for existing memories
UPDATE thermal_memory_archive
SET
    source_triad = 'legacy',
    source_node = 'unknown',
    source_session = 'pre-context-graph',
    valid_from = created_at,
    valid_until = CASE
        WHEN sacred_pattern = true THEN NULL  -- Sacred = eternal validity
        WHEN memory_type = 'operations' THEN created_at + INTERVAL '90 days'
        WHEN memory_type = 'research' THEN created_at + INTERVAL '365 days'
        ELSE NULL  -- Default to no expiration
    END,
    relationships = '{}',
    context_version = 1
WHERE source_triad IS NULL;

-- Verify backfill
SELECT
    source_triad,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM thermal_memory_archive
GROUP BY source_triad;
```

## Phase 3: Relationship Structure

**Objective**: Define the graph edge format for memory relationships

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `supersedes` | This memory replaces an older one | New API docs supersede old |
| `references` | This memory cites another | Research cites prior work |
| `contradicts` | This memory conflicts with another | Conflicting config advice |
| `extends` | This memory adds to another | Additional details |
| `part_of` | This memory belongs to a collection | Chapter in a guide |
| `derived_from` | This was generated from source | Summary of long doc |

### JSONB Structure

```json
{
  "related_to": [
    {
      "memory_id": 123,
      "relationship": "supersedes",
      "weight": 0.9,
      "created_at": "2026-01-05T12:00:00Z",
      "created_by": "IT Chief"
    },
    {
      "memory_id": 456,
      "relationship": "references",
      "weight": 0.7,
      "created_at": "2026-01-05T12:00:00Z",
      "created_by": "Data Chief"
    }
  ],
  "part_of": [
    {
      "memory_id": 789,
      "relationship": "collection",
      "collection_name": "VetAssist Architecture"
    }
  ]
}
```

### Helper Functions for Relationships

```sql
-- Add a relationship between two memories
CREATE OR REPLACE FUNCTION add_memory_relationship(
    from_memory_id INTEGER,
    to_memory_id INTEGER,
    rel_type TEXT,
    weight FLOAT DEFAULT 0.8,
    created_by TEXT DEFAULT 'system'
) RETURNS BOOLEAN AS $$
DECLARE
    new_rel JSONB;
    existing_rels JSONB;
BEGIN
    -- Build new relationship object
    new_rel := jsonb_build_object(
        'memory_id', to_memory_id,
        'relationship', rel_type,
        'weight', weight,
        'created_at', NOW(),
        'created_by', created_by
    );

    -- Get existing relationships
    SELECT COALESCE(relationships->'related_to', '[]'::JSONB)
    INTO existing_rels
    FROM thermal_memory_archive
    WHERE id = from_memory_id;

    -- Append new relationship
    UPDATE thermal_memory_archive
    SET relationships = jsonb_set(
        COALESCE(relationships, '{}'::JSONB),
        '{related_to}',
        existing_rels || new_rel
    )
    WHERE id = from_memory_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Find memories related to a given memory
CREATE OR REPLACE FUNCTION get_related_memories(
    start_memory_id INTEGER,
    max_depth INTEGER DEFAULT 2,
    min_weight FLOAT DEFAULT 0.5
) RETURNS TABLE (
    memory_id INTEGER,
    depth INTEGER,
    path INTEGER[],
    relationship_type TEXT,
    cumulative_weight FLOAT,
    title TEXT,
    temperature_score FLOAT
) AS $$
WITH RECURSIVE memory_graph AS (
    -- Base case: starting memory
    SELECT
        tma.id as memory_id,
        0 as depth,
        ARRAY[tma.id] as path,
        'root'::TEXT as relationship_type,
        1.0::FLOAT as cumulative_weight
    FROM thermal_memory_archive tma
    WHERE tma.id = start_memory_id

    UNION ALL

    -- Recursive case: follow relationships
    SELECT
        (rel->>'memory_id')::INTEGER as memory_id,
        mg.depth + 1 as depth,
        mg.path || (rel->>'memory_id')::INTEGER as path,
        (rel->>'relationship')::TEXT as relationship_type,
        mg.cumulative_weight * COALESCE((rel->>'weight')::FLOAT, 0.5) as cumulative_weight
    FROM memory_graph mg
    JOIN thermal_memory_archive tma ON tma.id = mg.memory_id
    CROSS JOIN LATERAL jsonb_array_elements(
        COALESCE(tma.relationships->'related_to', '[]'::JSONB)
    ) AS rel
    WHERE mg.depth < max_depth
      AND mg.cumulative_weight * COALESCE((rel->>'weight')::FLOAT, 0.5) >= min_weight
      AND NOT (rel->>'memory_id')::INTEGER = ANY(mg.path)  -- Prevent cycles
)
SELECT
    mg.memory_id,
    mg.depth,
    mg.path,
    mg.relationship_type,
    mg.cumulative_weight,
    LEFT(tma.original_content, 100) as title,
    tma.temperature_score
FROM memory_graph mg
JOIN thermal_memory_archive tma ON tma.id = mg.memory_id
WHERE mg.depth > 0
ORDER BY mg.cumulative_weight DESC, mg.depth ASC;
$$ LANGUAGE SQL;
```

## Phase 4: CGR³ Query Functions

**Objective**: Implement Retrieve-Rank-Reason paradigm

```sql
-- CGR³ Retrieve: Get candidate memories with context filters
CREATE OR REPLACE FUNCTION cgr3_retrieve(
    search_query TEXT,
    filter_triad TEXT DEFAULT NULL,
    filter_node TEXT DEFAULT NULL,
    filter_after TIMESTAMPTZ DEFAULT NULL,
    filter_before TIMESTAMPTZ DEFAULT NULL,
    include_expired BOOLEAN DEFAULT FALSE,
    max_results INTEGER DEFAULT 20
) RETURNS TABLE (
    id INTEGER,
    content TEXT,
    temperature_score FLOAT,
    source_triad VARCHAR,
    source_node VARCHAR,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    relevance_score FLOAT
) AS $$
SELECT
    tma.id,
    tma.original_content as content,
    tma.temperature_score,
    tma.source_triad,
    tma.source_node,
    tma.valid_from,
    tma.valid_until,
    -- Simple relevance: temperature * recency factor
    tma.temperature_score * (
        1.0 - EXTRACT(EPOCH FROM (NOW() - tma.created_at)) /
              (86400.0 * 365)  -- Decay over 1 year
    ) as relevance_score
FROM thermal_memory_archive tma
WHERE
    -- Text search
    (tma.original_content ILIKE '%' || search_query || '%'
     OR tma.compressed_content ILIKE '%' || search_query || '%')
    -- Triad filter
    AND (filter_triad IS NULL OR tma.source_triad = filter_triad)
    -- Node filter
    AND (filter_node IS NULL OR tma.source_node = filter_node)
    -- Time range filter
    AND (filter_after IS NULL OR tma.created_at >= filter_after)
    AND (filter_before IS NULL OR tma.created_at <= filter_before)
    -- Validity filter
    AND (include_expired OR tma.valid_until IS NULL OR tma.valid_until > NOW())
ORDER BY relevance_score DESC, tma.temperature_score DESC
LIMIT max_results;
$$ LANGUAGE SQL;

-- CGR³ Rank: Re-rank results with relationship context
CREATE OR REPLACE FUNCTION cgr3_rank(
    memory_ids INTEGER[],
    boost_sacred BOOLEAN DEFAULT TRUE,
    boost_recent BOOLEAN DEFAULT TRUE
) RETURNS TABLE (
    id INTEGER,
    base_score FLOAT,
    relationship_boost FLOAT,
    sacred_boost FLOAT,
    recency_boost FLOAT,
    final_score FLOAT
) AS $$
SELECT
    tma.id,
    tma.temperature_score as base_score,
    -- Boost if memory has many relationships
    COALESCE(jsonb_array_length(tma.relationships->'related_to'), 0) * 0.1 as relationship_boost,
    -- Boost sacred memories
    CASE WHEN boost_sacred AND tma.sacred_pattern THEN 0.2 ELSE 0 END as sacred_boost,
    -- Boost recent memories
    CASE WHEN boost_recent THEN
        GREATEST(0, 0.3 - EXTRACT(EPOCH FROM (NOW() - tma.created_at)) / (86400.0 * 30))
    ELSE 0 END as recency_boost,
    -- Final combined score
    tma.temperature_score
        + COALESCE(jsonb_array_length(tma.relationships->'related_to'), 0) * 0.1
        + CASE WHEN boost_sacred AND tma.sacred_pattern THEN 0.2 ELSE 0 END
        + CASE WHEN boost_recent THEN
            GREATEST(0, 0.3 - EXTRACT(EPOCH FROM (NOW() - tma.created_at)) / (86400.0 * 30))
          ELSE 0 END
    as final_score
FROM thermal_memory_archive tma
WHERE tma.id = ANY(memory_ids)
ORDER BY final_score DESC;
$$ LANGUAGE SQL;
```

## Phase 5: Memory Linking Service

**Objective**: Daemon to automatically discover and create relationships

Create `/ganuda/daemons/memory_linker.py` on greenfin:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Memory Linker Daemon
Automatically discovers and creates relationships between thermal memories.
"""

import psycopg2
import schedule
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import re

DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

class MemoryLinker:
    """Discovers relationships between thermal memories."""

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True

    def find_supersedes_relationships(self) -> List[Tuple[int, int]]:
        """Find memories that update/supersede older ones on same topic."""
        query = """
        SELECT
            newer.id as new_id,
            older.id as old_id,
            similarity(newer.compressed_content, older.compressed_content) as sim
        FROM thermal_memory_archive newer
        JOIN thermal_memory_archive older ON older.id < newer.id
        WHERE
            newer.created_at > older.created_at
            AND newer.memory_type = older.memory_type
            AND similarity(newer.compressed_content, older.compressed_content) > 0.6
            AND newer.id NOT IN (
                SELECT (rel->>'memory_id')::INTEGER
                FROM thermal_memory_archive t,
                     jsonb_array_elements(t.relationships->'related_to') rel
                WHERE t.id = newer.id
            )
        ORDER BY sim DESC
        LIMIT 50;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [(row[0], row[1]) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error finding supersedes: {e}")
            return []

    def find_reference_relationships(self) -> List[Tuple[int, int]]:
        """Find memories that reference others by hash or keywords."""
        query = """
        SELECT
            m1.id as referencer_id,
            m2.id as referenced_id
        FROM thermal_memory_archive m1
        JOIN thermal_memory_archive m2 ON m2.id != m1.id
        WHERE
            m1.original_content ILIKE '%' || m2.memory_hash || '%'
            OR m1.original_content ILIKE '%memory ' || m2.id::TEXT || '%'
        LIMIT 50;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return [(row[0], row[1]) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error finding references: {e}")
            return []

    def add_relationship(self, from_id: int, to_id: int,
                         rel_type: str, weight: float = 0.7):
        """Add a relationship between two memories."""
        query = """
        SELECT add_memory_relationship(%s, %s, %s, %s, %s);
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (from_id, to_id, rel_type, weight, 'memory_linker'))
                print(f"  Added {rel_type}: {from_id} -> {to_id}")
        except Exception as e:
            print(f"Error adding relationship: {e}")

    def run_linking_pass(self):
        """Run one pass of relationship discovery."""
        print(f"\n[{datetime.now()}] Running memory linking pass...")

        # Find supersedes relationships
        supersedes = self.find_supersedes_relationships()
        print(f"  Found {len(supersedes)} potential supersedes relationships")
        for new_id, old_id in supersedes[:10]:  # Limit per pass
            self.add_relationship(new_id, old_id, 'supersedes', 0.8)

        # Find reference relationships
        references = self.find_reference_relationships()
        print(f"  Found {len(references)} potential reference relationships")
        for ref_id, target_id in references[:10]:
            self.add_relationship(ref_id, target_id, 'references', 0.7)

        print(f"  Linking pass complete")


def main():
    print("Cherokee AI Federation - Memory Linker Daemon")
    print("=" * 50)

    linker = MemoryLinker()

    # Run immediately on start
    linker.run_linking_pass()

    # Schedule periodic runs
    schedule.every(1).hour.do(linker.run_linking_pass)

    print("\nDaemon running. Linking pass every hour.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
```

## Phase 6: Update Memory Writers

**Objective**: Ensure new memories include context graph fields

Update all code that inserts into thermal_memory_archive to include:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash,
    original_content,
    compressed_content,
    temperature_score,
    memory_type,
    sacred_pattern,
    created_at,
    -- NEW: Context graph fields
    source_triad,
    source_node,
    source_session,
    valid_from,
    valid_until,
    relationships,
    context_version
) VALUES (
    md5($content),
    $content,
    $compressed,
    $temperature,
    $type,
    $sacred,
    NOW(),
    -- NEW: Context values
    'IT Chief',           -- or 'Data Chief', 'Ops Chief', 'Jr-xyz'
    'redfin',             -- or 'bluefin', 'greenfin', etc.
    $session_id,          -- conversation or task ID
    NOW(),                -- valid from now
    NULL,                 -- NULL = no expiration, or specific date
    '{}',                 -- relationships added later
    2                     -- context_version = 2 for new format
);
```

## Testing & Verification

### Test 1: Schema Changes Applied
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'thermal_memory_archive'
ORDER BY ordinal_position;
-- Should show new columns: source_triad, source_node, etc.
```

### Test 2: Backfill Completed
```sql
SELECT
    source_triad,
    COUNT(*) as count
FROM thermal_memory_archive
GROUP BY source_triad;
-- Should show 'legacy' for old memories, specific triads for new
```

### Test 3: Relationships Work
```sql
-- Add test relationship
SELECT add_memory_relationship(1, 2, 'references', 0.8, 'test');

-- Query relationships
SELECT * FROM get_related_memories(1, 2, 0.5);
```

### Test 4: CGR³ Retrieval Works
```sql
SELECT * FROM cgr3_retrieve(
    'database',           -- search query
    'IT Chief',           -- filter by triad
    NULL,                 -- any node
    '2026-01-01'::TIMESTAMPTZ,  -- after date
    NULL,                 -- before date
    FALSE,                -- exclude expired
    10                    -- max results
);
```

### Test 5: Legacy Compatibility
```sql
-- Old queries should still work
SELECT * FROM thermal_memory_archive_v1 LIMIT 5;
```

## Rollback Plan

If issues arise, the enhancement is fully reversible:

```sql
-- Remove new columns (data loss - use with caution)
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS source_triad;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS source_node;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS source_session;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS valid_from;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS valid_until;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS relationships;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS context_version;

-- Drop functions
DROP FUNCTION IF EXISTS add_memory_relationship;
DROP FUNCTION IF EXISTS get_related_memories;
DROP FUNCTION IF EXISTS cgr3_retrieve;
DROP FUNCTION IF EXISTS cgr3_rank;

-- Drop view
DROP VIEW IF EXISTS thermal_memory_archive_v1;
```

## Acceptance Criteria

- [ ] Phase 1: New columns added, indexes created, compatibility view exists
- [ ] Phase 2: Existing 6700+ memories backfilled with defaults
- [ ] Phase 3: Relationship helper functions working
- [ ] Phase 4: CGR³ query functions returning results
- [ ] Phase 5: Memory linker daemon deployed on greenfin
- [ ] Phase 6: New memory inserts include context fields
- [ ] All existing thermal memory consumers still work via v1 view

## Security Notes

- **Provenance is audit trail** - source_triad/node/session tracks who created what
- **Temporal validity** - respects sacred_pattern (175-year protection)
- **Relationships are append-only** - historical links preserved
- **Memory linker** runs with read-heavy, write-light pattern

## For Seven Generations

This enhancement transforms thermal memory from flat storage into a knowledge graph, enabling the Federation to reason across 175 years of accumulated wisdom.
