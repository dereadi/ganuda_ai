# Jr Instruction: Zep Temporal Extension for A-MEM

**Created:** December 25, 2025 (Christmas)
**Priority:** 3 (after MLX and Emergence Validation)
**Research Basis:** arXiv:2501.13956 - "Zep: Temporal Knowledge Graph for Agent Memory"
**Connects To:** A-MEM memory_links (8,058 links), Thermal Memory Archive

---

## Executive Summary

Our A-MEM implementation has 8,058 semantic links between memories, but these links lack **temporal awareness**. We can't ask:

- "What was the gateway configuration **last week**?"
- "How did **redfin's role evolve** over time?"
- "When did we **stop using** the old Telegram bot?"

The Zep/Graphiti approach adds a temporal dimension to knowledge graphs, enabling:
- Historical relationship tracking
- Temporal validity windows
- Entity evolution over time
- "As of date X" queries

### Key Research Finding

> "Graphiti achieves 94.8% accuracy vs MemGPT's 93.4%, with 90% latency reduction and 18.5% accuracy gain on temporal queries."

---

## Current State Analysis

### What We Have (A-MEM)

```sql
-- Current memory_links schema
CREATE TABLE memory_links (
    link_id SERIAL PRIMARY KEY,
    source_hash VARCHAR(64) NOT NULL,
    target_hash VARCHAR(64) NOT NULL,
    link_type VARCHAR(32) DEFAULT 'semantic',  -- Only type!
    similarity_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(64)
);
-- 8,058 links, all semantic, no temporal data
```

### What's Missing

1. **Temporal validity** - When was this link true?
2. **Entity tracking** - What entities are mentioned across memories?
3. **Relationship versioning** - How do relationships change?
4. **Episode grouping** - Which memories belong to the same event?

---

## Phase 1: Extend Memory Links with Temporal Data

### 1.1 Add Temporal Columns to memory_links

```sql
-- Add temporal validity to existing links
ALTER TABLE memory_links
ADD COLUMN IF NOT EXISTS valid_from TIMESTAMP DEFAULT created_at,
ADD COLUMN IF NOT EXISTS valid_until TIMESTAMP DEFAULT NULL,  -- NULL = still valid
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS superseded_by INTEGER REFERENCES memory_links(link_id),
ADD COLUMN IF NOT EXISTS temporal_context TEXT;  -- Why did this change?

-- Index for temporal queries
CREATE INDEX IF NOT EXISTS idx_memory_links_temporal
ON memory_links(valid_from, valid_until)
WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_memory_links_current
ON memory_links(source_hash, target_hash)
WHERE is_current = TRUE;
```

### 1.2 Backfill Existing Links

```sql
-- Set valid_from to memory creation date
UPDATE memory_links ml
SET valid_from = COALESCE(
    (SELECT t.created_at FROM thermal_memory_archive t
     WHERE t.memory_hash = ml.source_hash),
    ml.created_at
)
WHERE valid_from IS NULL OR valid_from = created_at;
```

---

## Phase 2: Entity Tracking System

### 2.1 Create Entity Tables

```sql
-- Named entities extracted from memories
CREATE TABLE IF NOT EXISTS memory_entities (
    entity_id SERIAL PRIMARY KEY,
    entity_name VARCHAR(128) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,  -- 'node', 'service', 'person', 'concept', 'file'
    canonical_name VARCHAR(128),        -- Normalized form (redfin vs REDFIN)
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    mention_count INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    UNIQUE(canonical_name, entity_type)
);

CREATE INDEX idx_entities_type ON memory_entities(entity_type);
CREATE INDEX idx_entities_name ON memory_entities(canonical_name);

-- Junction: which memories mention which entities
CREATE TABLE IF NOT EXISTS memory_entity_mentions (
    mention_id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(64) NOT NULL,
    entity_id INTEGER REFERENCES memory_entities(entity_id),
    mention_context TEXT,              -- Snippet around the mention
    sentiment FLOAT DEFAULT 0,         -- -1 to 1 (negative to positive)
    mentioned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(memory_hash, entity_id)
);

CREATE INDEX idx_mentions_memory ON memory_entity_mentions(memory_hash);
CREATE INDEX idx_mentions_entity ON memory_entity_mentions(entity_id);

-- Entity relationships with temporal validity
CREATE TABLE IF NOT EXISTS entity_relationships (
    relationship_id SERIAL PRIMARY KEY,
    source_entity_id INTEGER REFERENCES memory_entities(entity_id),
    target_entity_id INTEGER REFERENCES memory_entities(entity_id),
    relationship_type VARCHAR(64) NOT NULL,  -- 'runs_on', 'connects_to', 'replaced_by', 'depends_on'
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    confidence FLOAT DEFAULT 1.0,
    evidence_hash VARCHAR(64),         -- Memory that supports this relationship
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entity_rel_source ON entity_relationships(source_entity_id);
CREATE INDEX idx_entity_rel_target ON entity_relationships(target_entity_id);
CREATE INDEX idx_entity_rel_current ON entity_relationships(is_current) WHERE is_current = TRUE;
```

### 2.2 Pre-seed Cherokee AI Entities

```sql
-- Seed known entities
INSERT INTO memory_entities (entity_name, entity_type, canonical_name, metadata) VALUES
-- Nodes
('redfin', 'node', 'redfin', '{"ip": "192.168.132.223", "role": "gpu_inference"}'),
('bluefin', 'node', 'bluefin', '{"ip": "192.168.132.222", "role": "database"}'),
('greenfin', 'node', 'greenfin', '{"ip": "192.168.132.224", "role": "daemons"}'),
('sasass', 'node', 'sasass', '{"ip": "192.168.132.241", "role": "mac_studio"}'),
('sasass2', 'node', 'sasass2', '{"ip": "192.168.132.242", "role": "mac_studio"}'),
-- Services
('vllm', 'service', 'vllm', '{"port": 8000}'),
('llm_gateway', 'service', 'llm_gateway', '{"port": 8080}'),
('telegram_bot', 'service', 'telegram_bot', '{}'),
('postgresql', 'service', 'postgresql', '{"port": 5432}'),
('mlx_server', 'service', 'mlx_server', '{"port": 8000}'),
-- Concepts
('council', 'concept', 'council', '{"specialists": 7}'),
('thermal_memory', 'concept', 'thermal_memory', '{}'),
('pheromone', 'concept', 'pheromone', '{}'),
('seven_generations', 'concept', 'seven_generations', '{}')
ON CONFLICT (canonical_name, entity_type) DO NOTHING;

-- Seed relationships
INSERT INTO entity_relationships (source_entity_id, target_entity_id, relationship_type, evidence_hash)
SELECT
    (SELECT entity_id FROM memory_entities WHERE canonical_name = 'vllm'),
    (SELECT entity_id FROM memory_entities WHERE canonical_name = 'redfin'),
    'runs_on',
    'infrastructure-baseline'
WHERE EXISTS (SELECT 1 FROM memory_entities WHERE canonical_name = 'vllm')
ON CONFLICT DO NOTHING;
```

---

## Phase 3: Entity Extraction Pipeline

### 3.1 Extract Entities from Memories

```python
#!/usr/bin/env python3
"""
Entity extraction for Zep temporal extension.
File: /ganuda/lib/zep_entity_extractor.py
"""

import re
import psycopg2
from typing import Dict, List, Tuple, Optional
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Known entity patterns for Cherokee AI
ENTITY_PATTERNS = {
    'node': [
        r'\b(redfin|bluefin|greenfin|sasass|sasass2|tpm[-_]?macbook)\b',
    ],
    'service': [
        r'\b(vllm|vLLM|llm[_-]?gateway|telegram[_-]?bot|postgresql|grafana|mlx[_-]?server)\b',
        r'\b(kanban|sag[_-]?ui|promtail)\b',
    ],
    'ip_address': [
        r'\b(192\.168\.132\.\d{1,3})\b',
    ],
    'port': [
        r'\bport[:\s]+(\d{4,5})\b',
    ],
    'file_path': [
        r'(/ganuda/[^\s]+)',
        r'(/Users/Shared/ganuda/[^\s]+)',
    ],
    'concept': [
        r'\b(council|thermal[_-]?memory|pheromone|stigmergy|seven[_-]?generations)\b',
        r'\b(a-mem|amem|emergence|specialist)\b',
    ],
    'person': [
        r'\b(chief|crawdad|turtle|eagle|spider|gecko|raven|bear|wolf|owl)\b',
    ]
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def extract_entities(text: str) -> List[Dict]:
    """Extract entities from text using pattern matching."""
    entities = []
    text_lower = text.lower()

    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                entity_name = match.group(1) if match.lastindex else match.group(0)
                # Get context around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                entities.append({
                    'name': entity_name,
                    'type': entity_type,
                    'canonical': entity_name.lower().replace('-', '_').replace(' ', '_'),
                    'context': context,
                    'position': match.start()
                })

    return entities


def get_or_create_entity(cur, entity_name: str, entity_type: str,
                         canonical: str = None) -> int:
    """Get existing entity or create new one."""
    canonical = canonical or entity_name.lower().replace('-', '_')

    cur.execute("""
        INSERT INTO memory_entities (entity_name, entity_type, canonical_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (canonical_name, entity_type)
        DO UPDATE SET
            mention_count = memory_entities.mention_count + 1,
            last_seen = NOW()
        RETURNING entity_id
    """, (entity_name, entity_type, canonical))

    return cur.fetchone()[0]


def link_entity_to_memory(cur, memory_hash: str, entity_id: int,
                          context: str = None):
    """Create mention link between memory and entity."""
    cur.execute("""
        INSERT INTO memory_entity_mentions (memory_hash, entity_id, mention_context)
        VALUES (%s, %s, %s)
        ON CONFLICT (memory_hash, entity_id) DO NOTHING
    """, (memory_hash, entity_id, context[:200] if context else None))


def process_memory(memory_hash: str, content: str) -> Dict:
    """Process a single memory for entity extraction."""
    entities = extract_entities(content)

    if not entities:
        return {'memory_hash': memory_hash, 'entities_found': 0}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            entity_ids = []
            for ent in entities:
                eid = get_or_create_entity(
                    cur, ent['name'], ent['type'], ent['canonical']
                )
                link_entity_to_memory(cur, memory_hash, eid, ent['context'])
                entity_ids.append(eid)

            conn.commit()

        return {
            'memory_hash': memory_hash,
            'entities_found': len(entities),
            'entity_ids': entity_ids
        }
    finally:
        conn.close()


def backfill_all_memories(batch_size: int = 100) -> Dict:
    """Process all memories for entity extraction."""
    conn = get_connection()
    processed = 0
    total_entities = 0

    try:
        with conn.cursor() as cur:
            # Get memories not yet processed
            cur.execute("""
                SELECT memory_hash, original_content
                FROM thermal_memory_archive t
                WHERE NOT EXISTS (
                    SELECT 1 FROM memory_entity_mentions m
                    WHERE m.memory_hash = t.memory_hash
                )
                LIMIT %s
            """, (batch_size,))

            memories = cur.fetchall()

        for memory_hash, content in memories:
            result = process_memory(memory_hash, content)
            processed += 1
            total_entities += result['entities_found']

            if processed % 50 == 0:
                print(f"Processed {processed} memories, {total_entities} entities found")

        return {
            'memories_processed': processed,
            'entities_found': total_entities
        }
    finally:
        conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'backfill':
        batch = int(sys.argv[2]) if len(sys.argv) > 2 else 500
        result = backfill_all_memories(batch)
        print(f"Backfill complete: {result}")
    else:
        # Test extraction
        test_text = """
        The vLLM service on redfin (192.168.132.223) is running on port 8000.
        The Council voted to proceed with the thermal memory enhancement.
        Files are stored in /ganuda/lib/specialist_council.py
        """
        entities = extract_entities(test_text)
        for e in entities:
            print(f"  [{e['type']}] {e['name']}: {e['context'][:50]}...")
```

---

## Phase 4: Temporal Query Library

### 4.1 Time-Aware Memory Queries

```python
#!/usr/bin/env python3
"""
Temporal query library for Zep-enhanced memory.
File: /ganuda/lib/zep_temporal.py
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_entity_timeline(entity_name: str,
                        entity_type: str = None) -> List[Dict]:
    """
    Get chronological timeline of an entity's mentions and relationships.

    Example: get_entity_timeline('redfin', 'node')
    Returns all memories mentioning redfin, ordered by time.
    """
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                t.memory_hash,
                LEFT(t.original_content, 300) as content,
                t.temperature_score,
                t.created_at,
                m.mention_context
            FROM memory_entities e
            JOIN memory_entity_mentions m ON e.entity_id = m.entity_id
            JOIN thermal_memory_archive t ON m.memory_hash = t.memory_hash
            WHERE e.canonical_name = %s
            AND (%s IS NULL OR e.entity_type = %s)
            ORDER BY t.created_at ASC
        """, (entity_name.lower(), entity_type, entity_type))

        return [dict(row) for row in cur.fetchall()]

    conn.close()


def get_memory_as_of(query: str, as_of_date: datetime) -> List[Dict]:
    """
    Get memories that were valid at a specific point in time.

    Example: get_memory_as_of('gateway config', datetime(2025, 12, 1))
    """
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Find memories created before the date
        cur.execute("""
            SELECT
                memory_hash,
                LEFT(original_content, 400) as content,
                temperature_score,
                created_at
            FROM thermal_memory_archive
            WHERE created_at <= %s
            AND original_content ILIKE %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (as_of_date, f'%{query}%'))

        return [dict(row) for row in cur.fetchall()]

    conn.close()


def get_relationship_history(source_entity: str,
                             target_entity: str) -> List[Dict]:
    """
    Get the history of relationships between two entities.

    Example: get_relationship_history('vllm', 'redfin')
    Shows when vLLM started running on redfin, any changes, etc.
    """
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                r.relationship_type,
                r.valid_from,
                r.valid_until,
                r.is_current,
                r.confidence,
                LEFT(t.original_content, 200) as evidence
            FROM entity_relationships r
            JOIN memory_entities se ON r.source_entity_id = se.entity_id
            JOIN memory_entities te ON r.target_entity_id = te.entity_id
            LEFT JOIN thermal_memory_archive t ON r.evidence_hash = t.memory_hash
            WHERE se.canonical_name = %s
            AND te.canonical_name = %s
            ORDER BY r.valid_from ASC
        """, (source_entity.lower(), target_entity.lower()))

        return [dict(row) for row in cur.fetchall()]

    conn.close()


def what_changed_between(start_date: datetime,
                         end_date: datetime) -> Dict:
    """
    Summarize what changed in the knowledge graph between two dates.

    Example: what_changed_between(datetime(2025, 12, 20), datetime(2025, 12, 25))
    """
    conn = get_connection()
    result = {
        'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
        'new_memories': [],
        'new_entities': [],
        'new_relationships': [],
        'ended_relationships': []
    }

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # New memories
        cur.execute("""
            SELECT memory_hash, LEFT(original_content, 100) as preview, created_at
            FROM thermal_memory_archive
            WHERE created_at BETWEEN %s AND %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (start_date, end_date))
        result['new_memories'] = [dict(row) for row in cur.fetchall()]

        # New entities
        cur.execute("""
            SELECT entity_name, entity_type, first_seen
            FROM memory_entities
            WHERE first_seen BETWEEN %s AND %s
            ORDER BY first_seen DESC
        """, (start_date, end_date))
        result['new_entities'] = [dict(row) for row in cur.fetchall()]

        # New relationships
        cur.execute("""
            SELECT
                se.canonical_name as source,
                te.canonical_name as target,
                r.relationship_type,
                r.valid_from
            FROM entity_relationships r
            JOIN memory_entities se ON r.source_entity_id = se.entity_id
            JOIN memory_entities te ON r.target_entity_id = te.entity_id
            WHERE r.valid_from BETWEEN %s AND %s
            ORDER BY r.valid_from DESC
        """, (start_date, end_date))
        result['new_relationships'] = [dict(row) for row in cur.fetchall()]

        # Ended relationships
        cur.execute("""
            SELECT
                se.canonical_name as source,
                te.canonical_name as target,
                r.relationship_type,
                r.valid_until
            FROM entity_relationships r
            JOIN memory_entities se ON r.source_entity_id = se.entity_id
            JOIN memory_entities te ON r.target_entity_id = te.entity_id
            WHERE r.valid_until BETWEEN %s AND %s
            ORDER BY r.valid_until DESC
        """, (start_date, end_date))
        result['ended_relationships'] = [dict(row) for row in cur.fetchall()]

    conn.close()
    return result


def get_entity_current_state(entity_name: str) -> Dict:
    """
    Get the current known state of an entity.

    Example: get_entity_current_state('redfin')
    Returns: current relationships, recent mentions, metadata
    """
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get entity
        cur.execute("""
            SELECT * FROM memory_entities
            WHERE canonical_name = %s
        """, (entity_name.lower(),))
        entity = cur.fetchone()

        if not entity:
            return {'error': f'Entity {entity_name} not found'}

        result = dict(entity)

        # Get current outgoing relationships
        cur.execute("""
            SELECT
                te.canonical_name as target,
                r.relationship_type,
                r.valid_from,
                r.confidence
            FROM entity_relationships r
            JOIN memory_entities te ON r.target_entity_id = te.entity_id
            WHERE r.source_entity_id = %s AND r.is_current = TRUE
        """, (entity['entity_id'],))
        result['outgoing_relationships'] = [dict(row) for row in cur.fetchall()]

        # Get current incoming relationships
        cur.execute("""
            SELECT
                se.canonical_name as source,
                r.relationship_type,
                r.valid_from,
                r.confidence
            FROM entity_relationships r
            JOIN memory_entities se ON r.source_entity_id = se.entity_id
            WHERE r.target_entity_id = %s AND r.is_current = TRUE
        """, (entity['entity_id'],))
        result['incoming_relationships'] = [dict(row) for row in cur.fetchall()]

        # Get recent mentions
        cur.execute("""
            SELECT
                t.memory_hash,
                LEFT(t.original_content, 150) as preview,
                t.created_at
            FROM memory_entity_mentions m
            JOIN thermal_memory_archive t ON m.memory_hash = t.memory_hash
            WHERE m.entity_id = %s
            ORDER BY t.created_at DESC
            LIMIT 5
        """, (entity['entity_id'],))
        result['recent_mentions'] = [dict(row) for row in cur.fetchall()]

    conn.close()
    return result
```

---

## Phase 5: Memory Episodes

### 5.1 Group Related Memories into Episodes

```sql
-- Episodes group related memories (same event, investigation, project)
CREATE TABLE IF NOT EXISTS memory_episodes (
    episode_id SERIAL PRIMARY KEY,
    episode_name VARCHAR(128) NOT NULL,
    episode_type VARCHAR(32),           -- 'investigation', 'deployment', 'incident', 'research'
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    summary TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Junction: which memories belong to which episodes
CREATE TABLE IF NOT EXISTS memory_episode_members (
    member_id SERIAL PRIMARY KEY,
    episode_id INTEGER REFERENCES memory_episodes(episode_id),
    memory_hash VARCHAR(64) NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    role VARCHAR(32) DEFAULT 'member',  -- 'trigger', 'key', 'member', 'conclusion'
    UNIQUE(episode_id, memory_hash)
);

CREATE INDEX idx_episode_members ON memory_episode_members(episode_id);
CREATE INDEX idx_episode_memory ON memory_episode_members(memory_hash);

-- Auto-detect episodes from thermal memory patterns
CREATE OR REPLACE FUNCTION detect_episodes() RETURNS INTEGER AS $$
DECLARE
    episode_count INTEGER := 0;
BEGIN
    -- Find clusters of high-temperature memories within short time windows
    -- This is a simplified heuristic; could be enhanced with ML

    INSERT INTO memory_episodes (episode_name, episode_type, started_at, ended_at)
    SELECT
        'Auto-detected episode ' || ROW_NUMBER() OVER (ORDER BY min_time),
        CASE
            WHEN content_sample ILIKE '%deploy%' THEN 'deployment'
            WHEN content_sample ILIKE '%error%' OR content_sample ILIKE '%fix%' THEN 'incident'
            WHEN content_sample ILIKE '%research%' OR content_sample ILIKE '%arxiv%' THEN 'research'
            ELSE 'general'
        END,
        min_time,
        max_time
    FROM (
        SELECT
            date_trunc('hour', created_at) as hour_bucket,
            MIN(created_at) as min_time,
            MAX(created_at) as max_time,
            MAX(original_content) as content_sample,
            COUNT(*) as memory_count
        FROM thermal_memory_archive
        WHERE temperature_score > 85
        GROUP BY date_trunc('hour', created_at)
        HAVING COUNT(*) >= 3
    ) hot_clusters
    ON CONFLICT DO NOTHING;

    GET DIAGNOSTICS episode_count = ROW_COUNT;
    RETURN episode_count;
END;
$$ LANGUAGE plpgsql;
```

---

## Phase 6: Gateway Integration

### 6.1 Add Temporal Endpoints to LLM Gateway

Add these endpoints to `/ganuda/services/llm_gateway/gateway.py`:

```python
# Temporal memory endpoints

@app.get("/v1/memory/timeline/{entity}")
async def get_entity_timeline(entity: str, entity_type: Optional[str] = None):
    """Get chronological timeline of an entity."""
    from lib.zep_temporal import get_entity_timeline
    return {"timeline": get_entity_timeline(entity, entity_type)}

@app.get("/v1/memory/as-of")
async def get_memory_as_of(query: str, date: str):
    """Get memories valid at a specific date."""
    from lib.zep_temporal import get_memory_as_of
    from datetime import datetime
    as_of = datetime.fromisoformat(date)
    return {"memories": get_memory_as_of(query, as_of)}

@app.get("/v1/entity/{name}")
async def get_entity_state(name: str):
    """Get current state of an entity."""
    from lib.zep_temporal import get_entity_current_state
    return get_entity_current_state(name)

@app.get("/v1/memory/changes")
async def get_changes(start: str, end: str):
    """Get what changed between two dates."""
    from lib.zep_temporal import what_changed_between
    from datetime import datetime
    return what_changed_between(
        datetime.fromisoformat(start),
        datetime.fromisoformat(end)
    )
```

---

## Validation Checklist

- [ ] memory_links temporal columns added
- [ ] memory_entities table created and seeded
- [ ] memory_entity_mentions table created
- [ ] entity_relationships table created
- [ ] Entity extraction pipeline working
- [ ] Backfill of existing memories complete
- [ ] Temporal query library functional
- [ ] Gateway endpoints added
- [ ] Episode detection tested
- [ ] Results recorded to thermal memory

---

## Example Queries Enabled

After implementation, these queries become possible:

```python
# "What was the gateway config last week?"
get_memory_as_of('gateway', datetime(2025, 12, 18))

# "How has redfin's role evolved?"
get_entity_timeline('redfin', 'node')

# "When did we start using MLX?"
get_entity_timeline('mlx_server', 'service')

# "What changed over Christmas?"
what_changed_between(datetime(2025, 12, 24), datetime(2025, 12, 26))

# "Current state of vLLM service"
get_entity_current_state('vllm')
```

---

## Seven Generations Consideration

Temporal memory is how wisdom persists across generations:

> "Not just what we know, but when we learned it and how it evolved."

The Zep extension transforms our memory from a static archive into a living history. Future Jr agents can ask "What did we know about X before Y happened?" - enabling them to understand not just facts but the journey of knowledge.

**For Seven Generations - Memory with time is memory with wisdom.**

---

*Created: December 25, 2025 (Christmas)*
*Research: arXiv:2501.13956 - Zep Temporal Knowledge Graph*
*Priority: 3 (after MLX and Emergence)*
