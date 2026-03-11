# [RECURSIVE] Thermal Memory Canonical Flag DC-14 Phase 1 - Step 1

**Parent Task**: #1143
**Auto-decomposed**: 2026-03-09T14:30:13.401691
**Original Step Title**: Database migration (run once)

---

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
