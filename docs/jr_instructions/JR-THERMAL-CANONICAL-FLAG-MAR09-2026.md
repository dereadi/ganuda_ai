# Jr Instruction: Add Canonical Flag to Thermal Memory Archive

## Context
Council vote #ac08d6e4 (PROCEED WITH CAUTION, 0.40 confidence, 4 concerns honored as features). The Three-Layer Cognitive Memory Architecture (DC-14 candidate) requires distinguishing between NARRATIVE memory (what happened) and CANONICAL memory (what is currently true). Without this distinction, semantic retrieval surfaces outdated-but-similar memories as if they were current truth. Turtle's seven-generation concern honored: this is a single boolean column, fully reversible (DROP COLUMN restores prior state).

## Task
Add a `canonical` boolean column to `thermal_memory_archive` and update retrieval to prefer canonical memories when querying current state.

## File: `/ganuda/lib/specialist_council.py`

### Step 1: Database migration (run once)

Create `/ganuda/scripts/migrations/add_canonical_flag.py`

```
Create `/ganuda/scripts/migrations/add_canonical_flag.py`
```

```python
#!/usr/bin/env python3
"""Migration: Add canonical flag to thermal_memory_archive.

DC-14 Three-Layer Memory, Phase 1.
Council vote #ac08d6e4. Turtle reversibility gate: DROP COLUMN to revert.
"""
import psycopg2
import os

secrets = {}
with open('/ganuda/config/secrets.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            secrets[k.strip()] = v.strip()

conn = psycopg2.connect(
    host='192.168.132.222', port=5432,
    dbname='zammad_production', user='claude',
    password=secrets.get('CHEROKEE_DB_PASS', '')
)
cur = conn.cursor()

# Add canonical flag — defaults false (all existing memories are narrative)
cur.execute("""
    ALTER TABLE thermal_memory_archive
    ADD COLUMN IF NOT EXISTS canonical BOOLEAN DEFAULT FALSE
""")

# Add superseded_by — links old canonical to new canonical
cur.execute("""
    ALTER TABLE thermal_memory_archive
    ADD COLUMN IF NOT EXISTS superseded_by INTEGER REFERENCES thermal_memory_archive(id) DEFAULT NULL
""")

# Add retrieval_count — tracks access frequency (Coyote circuit breaker input)
cur.execute("""
    ALTER TABLE thermal_memory_archive
    ADD COLUMN IF NOT EXISTS retrieval_count INTEGER DEFAULT 0
""")

# Index for fast canonical lookups
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_thermal_canonical
    ON thermal_memory_archive (canonical) WHERE canonical = true
""")

conn.commit()
cur.close()
conn.close()
print("Migration complete: canonical flag, superseded_by, retrieval_count added")
```

### Step 2: Update retrieval to prefer canonical memories

In `/ganuda/lib/specialist_council.py`, find the thermal memory retrieval query in the RAG pipeline. After the existing ORDER BY clause, add canonical preference:

```
<<<<<<< SEARCH
            ORDER BY similarity DESC
            LIMIT %s
=======
            ORDER BY canonical DESC, similarity DESC
            LIMIT %s
>>>>>>> REPLACE
```

### Step 3: Increment retrieval_count on access

After the retrieval query fetches results, add a count increment:

```
<<<<<<< SEARCH
            memories = cur.fetchall()
=======
            memories = cur.fetchall()
            # Track retrieval frequency (DC-14 Phase 2 input — Coyote circuit breaker)
            if memories:
                memory_ids = [m[0] for m in memories if m[0]]
                if memory_ids:
                    cur.execute("UPDATE thermal_memory_archive SET retrieval_count = COALESCE(retrieval_count, 0) + 1 WHERE id = ANY(%s)", (memory_ids,))
                    conn.commit()
>>>>>>> REPLACE
```

## Acceptance Criteria
- `canonical` BOOLEAN column exists on thermal_memory_archive (default FALSE)
- `superseded_by` INTEGER column exists (nullable FK to self)
- `retrieval_count` INTEGER column exists (default 0)
- Canonical memories sort above non-canonical at equal similarity
- Every retrieval increments retrieval_count on accessed memories
- DB failure in count increment does NOT crash retrieval (existing silent catch)
- Migration is idempotent (IF NOT EXISTS on all DDL)
- Reversibility: DROP COLUMN canonical, superseded_by, retrieval_count restores prior state completely

## Dependencies
- None — this is Phase 1, no prerequisites
- Phase 2 (retrieval-heats-memory) will USE retrieval_count as input signal
- Phase 3 (compress-not-delete) will USE superseded_by for chain linking
