# JR Instruction: Retrieval Beyond RAG — Phase 1 Entity Resolution Tables

**Task**: Create cross-domain entity resolution linking tables for thermal memory
**Priority**: 9 (strategic architecture — Council vote #807e89fe8b772db0)
**Sacred Fire**: No
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**TEG Plan**: true

## Context

Council deliberated on retrieval architecture beyond RAG (Thermal #119251, #119258). Current state: 119K+ thermals with pgvector embeddings but NO explicit foreign keys between thermals, council_votes, jr_work_queue, or duyuktv_tickets. Cross-references exist only as informal text in JSONB metadata. This makes causal/relational queries impossible.

Phase 1 creates the entity resolution bridge table and a temporal state column on thermals. We already have `thermal_relationships` (causal edges between thermals) and `observational_memory_archive` (compressed observations) — this Phase wires them to the rest of the federation's data.

## Changes

### Step 1: Create migration SQL

Create `scripts/migrations/entity_resolution_phase1.sql`

```python
"""
Entity Resolution Phase 1 — Cross-Domain Linking Tables
Council Vote: #807e89fe8b772db0 (PROCEED WITH CAUTION, 0.85)
Thermal refs: #119251 (Nate B. Jones thesis), #119258 (council deliberation)
Kanban EPIC: #1971
"""

import psycopg2
import os
import sys

def get_connection():
    """Connect using secrets_loader or env fallback."""
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

def run_migration():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Entity link bridge table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS thermal_entity_links (
            id SERIAL PRIMARY KEY,
            thermal_id INTEGER NOT NULL REFERENCES thermal_memory_archive(id) ON DELETE CASCADE,
            entity_type VARCHAR(30) NOT NULL,
            entity_id VARCHAR(64) NOT NULL,
            link_type VARCHAR(30) NOT NULL DEFAULT 'references',
            confidence FLOAT DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT NOW(),
            created_by VARCHAR(50) DEFAULT 'system',
            CONSTRAINT valid_entity_type CHECK (
                entity_type IN ('council_vote', 'jr_task', 'kanban_ticket', 'specification', 'code_commit', 'thermal', 'observation')
            ),
            CONSTRAINT valid_link_type CHECK (
                link_type IN ('references', 'caused_by', 'produced', 'resolved', 'blocked_by', 'supersedes', 'validates')
            )
        );
    """)

    # 2. Indexes for graph traversal
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tel_thermal_id ON thermal_entity_links(thermal_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tel_entity ON thermal_entity_links(entity_type, entity_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tel_link_type ON thermal_entity_links(link_type);
    """)

    # 3. Temporal state column on thermal_memory_archive
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'thermal_memory_archive' AND column_name = 'temporal_state'
            ) THEN
                ALTER TABLE thermal_memory_archive
                ADD COLUMN temporal_state VARCHAR(20) DEFAULT 'current'
                CHECK (temporal_state IN ('current', 'superseded', 'historical', 'retracted'));
            END IF;
        END $$;
    """)

    # 4. Index on temporal_state for filtered retrieval
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tma_temporal_state ON thermal_memory_archive(temporal_state);
    """)

    # 5. Reverse lookup view: given any entity, find all linked thermals
    cur.execute("""
        CREATE OR REPLACE VIEW entity_thermal_graph AS
        SELECT
            tel.entity_type,
            tel.entity_id,
            tel.link_type,
            tel.confidence,
            tma.id AS thermal_id,
            LEFT(tma.original_content, 200) AS thermal_preview,
            tma.temperature_score,
            tma.sacred_pattern,
            tma.temporal_state,
            tma.created_at AS thermal_created_at
        FROM thermal_entity_links tel
        JOIN thermal_memory_archive tma ON tma.id = tel.thermal_id
        ORDER BY tma.temperature_score DESC;
    """)

    conn.commit()
    print(f"Phase 1 migration complete.")
    print(f"  - thermal_entity_links table created")
    print(f"  - temporal_state column added to thermal_memory_archive")
    print(f"  - entity_thermal_graph view created")
    print(f"  - 4 indexes created")

    # Verify
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'thermal_entity_links'")
    assert cur.fetchone()[0] == 1, "thermal_entity_links table not found"
    cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'thermal_memory_archive' AND column_name = 'temporal_state'")
    assert cur.fetchone()[0] == 1, "temporal_state column not found"
    print("Verification PASSED.")

    conn.close()

if __name__ == '__main__':
    run_migration()
```

### Step 2: Create backfill script to link existing thermals

Create `scripts/backfill_entity_links.py`

```python
"""
Backfill entity links from existing thermal metadata JSONB.
Scans thermal_memory_archive.metadata for known entity references
and creates corresponding thermal_entity_links rows.

Safe to run multiple times (idempotent — checks for existing links).
"""

import psycopg2
import psycopg2.extras
import json
import re
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

def backfill():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    insert_cur = conn.cursor()

    linked = 0
    skipped = 0

    # Pattern: metadata contains council_vote hash
    cur.execute("""
        SELECT id, metadata FROM thermal_memory_archive
        WHERE metadata IS NOT NULL
        AND (metadata::text LIKE '%council_vote%' OR metadata::text LIKE '%audit_hash%'
             OR metadata::text LIKE '%task_id%' OR metadata::text LIKE '%kanban%'
             OR metadata::text LIKE '%parent_thermal%')
        ORDER BY id
    """)

    for row in cur:
        meta = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
        thermal_id = row['id']

        links_to_insert = []

        # Council vote references
        for key in ('council_vote', 'audit_hash', 'vote_hash'):
            if key in meta and meta[key]:
                links_to_insert.append(('council_vote', str(meta[key]), 'references'))

        # Jr task references
        for key in ('task_id', 'jr_task_id', 'jr_task'):
            if key in meta and meta[key]:
                links_to_insert.append(('jr_task', str(meta[key]), 'references'))

        # Kanban references
        for key in ('kanban_id', 'kanban', 'ticket_id'):
            if key in meta and meta[key]:
                links_to_insert.append(('kanban_ticket', str(meta[key]), 'references'))

        # Parent thermal references
        if 'parent_thermal' in meta and meta['parent_thermal']:
            links_to_insert.append(('thermal', str(meta['parent_thermal']), 'caused_by'))

        for entity_type, entity_id, link_type in links_to_insert:
            # Idempotent: skip if link already exists
            insert_cur.execute("""
                INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
                SELECT %s, %s, %s, %s, 'backfill'
                WHERE NOT EXISTS (
                    SELECT 1 FROM thermal_entity_links
                    WHERE thermal_id = %s AND entity_type = %s AND entity_id = %s
                )
            """, (thermal_id, entity_type, entity_id, link_type,
                  thermal_id, entity_type, entity_id))
            if insert_cur.rowcount > 0:
                linked += 1
            else:
                skipped += 1

    # Also scan original_content for council vote hash patterns
    cur.execute("""
        SELECT id, original_content FROM thermal_memory_archive
        WHERE original_content LIKE '%COUNCIL VOTE%'
        AND original_content ~ '[0-9a-f]{16}'
        ORDER BY id
    """)

    vote_hash_pattern = re.compile(r'#([0-9a-f]{16})')
    for row in cur:
        thermal_id = row['id']
        for match in vote_hash_pattern.finditer(row['original_content']):
            vote_hash = match.group(1)
            insert_cur.execute("""
                INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
                SELECT %s, 'council_vote', %s, 'references', 'backfill_content_scan'
                WHERE NOT EXISTS (
                    SELECT 1 FROM thermal_entity_links
                    WHERE thermal_id = %s AND entity_type = 'council_vote' AND entity_id = %s
                )
            """, (thermal_id, vote_hash, thermal_id, vote_hash))
            if insert_cur.rowcount > 0:
                linked += 1

    conn.commit()
    print(f"Backfill complete: {linked} links created, {skipped} duplicates skipped")

    # Stats
    stats_cur = conn.cursor()
    stats_cur.execute("SELECT entity_type, COUNT(*) FROM thermal_entity_links GROUP BY entity_type ORDER BY COUNT(*) DESC")
    print("\nEntity link distribution:")
    for row in stats_cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == '__main__':
    backfill()
```

### Step 3: Add entity linking helper to ganuda_db

File: `lib/ganuda_db/__init__.py`

<<<<<<< SEARCH
__version__ = "1.2.0"
=======
__version__ = "1.3.0"
>>>>>>> REPLACE

Then append to end of file (before any `if __name__` block, or at module level):

<<<<<<< SEARCH
def get_connection(retries: int = 3):
=======
def link_thermal_entity(thermal_id: int, entity_type: str, entity_id: str,
                        link_type: str = "references", created_by: str = "system") -> bool:
    """
    Create a cross-domain link between a thermal memory and another entity.
    Idempotent — skips if link already exists.
    Returns True if link was created, False if it already existed.

    Entity types: council_vote, jr_task, kanban_ticket, specification, code_commit, thermal, observation
    Link types: references, caused_by, produced, resolved, blocked_by, supersedes, validates
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
            SELECT %s, %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM thermal_entity_links
                WHERE thermal_id = %s AND entity_type = %s AND entity_id = %s
            )
        """, (thermal_id, entity_type, entity_id, link_type, created_by,
              thermal_id, entity_type, entity_id))
        created = cur.rowcount > 0
        conn.commit()
        conn.close()
        return created
    except Exception as e:
        logger.error(f"link_thermal_entity failed: {e}")
        return False


def get_connection(retries: int = 3):
>>>>>>> REPLACE

## Verification

After migration + backfill:

```text
-- Check table exists
SELECT COUNT(*) FROM thermal_entity_links;

-- Check temporal_state column
SELECT temporal_state, COUNT(*) FROM thermal_memory_archive GROUP BY temporal_state;

-- Check entity distribution
SELECT entity_type, COUNT(*) FROM thermal_entity_links GROUP BY entity_type;

-- Test graph traversal: find all thermals linked to a council vote
SELECT * FROM entity_thermal_graph WHERE entity_type = 'council_vote' AND entity_id = '807e89fe8b772db0';
```

## Notes

- This is Phase 1 of 4. Phase 2 adds causal edge queries. Phase 3 adds temporal state tracking logic. Phase 4 builds the hybrid retrieval pipeline.
- The backfill script is idempotent and safe to re-run.
- The `link_thermal_entity()` helper should be called from `_log_vote()` in specialist_council.py and from the Jr executor on task completion — but that wiring is Phase 2 work.
- EPIC kanban: #1971. Phase 1 kanban: #1972.
