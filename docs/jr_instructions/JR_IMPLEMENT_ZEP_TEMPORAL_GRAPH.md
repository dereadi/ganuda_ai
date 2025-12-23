# JR_IMPLEMENT_ZEP_TEMPORAL_GRAPH.md
## Cherokee AI Federation - Research Paper Implementation

**Paper**: Zep: A Temporal Knowledge Graph Architecture for Agent Memory
**arXiv**: 2501.13956
**Authors**: Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, Daniel Chalef
**Priority**: 2 (LOW-MEDIUM effort - extends existing A-MEM)
**Council Vote**: PROCEED WITH CAUTION (79.3% confidence)

---

## ULTRATHINK ANALYSIS

### What This Paper Teaches Us

Zep introduces **Graphiti** - a temporally-aware knowledge graph engine that:

1. **Synthesizes unstructured + structured data** dynamically
2. **Maintains historical relationships** - knows when things happened
3. **Enables cross-session information synthesis** - connects conversations over time
4. **Achieves 18.5% accuracy improvement** over baselines in temporal reasoning
5. **Reduces latency by 90%** through efficient graph traversal

Key innovation: **Episodes and Entities with Temporal Validity**

```
Entity(name, type, created_at, valid_from, valid_until, facts[])
Episode(content, timestamp, entities[], relationships[])
Relationship(source, target, type, created_at, valid_from, valid_until)
```

### How This Extends A-MEM

| A-MEM Feature | Zep Enhancement | Implementation Path |
|--------------|-----------------|---------------------|
| Keywords/tags extraction | ✅ Already have | No change needed |
| 384-dim embeddings | ✅ Already have | No change needed |
| memory_links (semantic) | ➕ Add temporal validity | Add valid_from/valid_until |
| Static relationships | ➕ Versioned relationships | Track relationship changes |
| No entity extraction | ➕ Named Entity Recognition | Add entity table |
| created_at timestamp | ➕ Temporal reasoning | Add validity windows |
| Single memory recall | ➕ Episode-based recall | Group related memories |

### The Temporal Dimension We're Missing

Current A-MEM links memories by **semantic similarity** (embedding cosine distance).

Zep adds **temporal reasoning**:
- "What was the gateway configuration BEFORE we upgraded?"
- "Show me all decisions about Jr agents from LAST WEEK"
- "What changed BETWEEN the two deployments?"

This is critical for:
- **Debugging regressions** - What changed?
- **Audit trails** - When did we decide X?
- **Knowledge evolution** - How did our understanding grow?

---

## IMPLEMENTATION TASKS

### Task 1: Add Temporal Validity to Memory Links
**Effort**: Low
**Node**: bluefin (database)

```sql
-- Extend memory_links with temporal validity
ALTER TABLE memory_links
ADD COLUMN IF NOT EXISTS valid_from TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS valid_until TIMESTAMP DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS relationship_version INTEGER DEFAULT 1;

-- Create index for temporal queries
CREATE INDEX IF NOT EXISTS idx_memory_links_temporal 
ON memory_links(source_hash, valid_from, valid_until);

CREATE INDEX IF NOT EXISTS idx_memory_links_current 
ON memory_links(source_hash) WHERE is_current = TRUE;

-- Function to version a relationship when it changes
CREATE OR REPLACE FUNCTION version_memory_link()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_current = TRUE AND NEW.is_current = TRUE THEN
        -- Creating new version, close old one
        UPDATE memory_links 
        SET valid_until = NOW(), is_current = FALSE
        WHERE source_hash = NEW.source_hash 
          AND target_hash = NEW.target_hash
          AND is_current = TRUE
          AND link_id != NEW.link_id;
        
        NEW.relationship_version = COALESCE(
            (SELECT MAX(relationship_version) + 1 
             FROM memory_links 
             WHERE source_hash = NEW.source_hash 
               AND target_hash = NEW.target_hash), 
            1
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_version_memory_link ON memory_links;
CREATE TRIGGER trg_version_memory_link
    BEFORE INSERT OR UPDATE ON memory_links
    FOR EACH ROW
    EXECUTE FUNCTION version_memory_link();
```

### Task 2: Create Entity Table (Graphiti-style)
**Effort**: Low
**Node**: bluefin (database)

```sql
-- Zep/Graphiti entity table
CREATE TABLE IF NOT EXISTS memory_entities (
    entity_id SERIAL PRIMARY KEY,
    entity_name VARCHAR(256) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    canonical_name VARCHAR(256),  -- Normalized form
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    mention_count INTEGER DEFAULT 1,
    facts JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding_vector FLOAT8[] DEFAULT NULL,
    UNIQUE(canonical_name, entity_type)
);

CREATE INDEX IF NOT EXISTS idx_entity_name ON memory_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_entity_type ON memory_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_canonical ON memory_entities(canonical_name);

-- Entity-memory junction table
CREATE TABLE IF NOT EXISTS memory_entity_mentions (
    mention_id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(64) NOT NULL,
    entity_id INTEGER REFERENCES memory_entities(entity_id),
    mention_context TEXT,
    mention_offset INTEGER,
    confidence FLOAT DEFAULT 1.0,
    extracted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mention_memory ON memory_entity_mentions(memory_hash);
CREATE INDEX IF NOT EXISTS idx_mention_entity ON memory_entity_mentions(entity_id);

-- Entity relationship table (temporal)
CREATE TABLE IF NOT EXISTS entity_relationships (
    rel_id SERIAL PRIMARY KEY,
    source_entity_id INTEGER REFERENCES memory_entities(entity_id),
    target_entity_id INTEGER REFERENCES memory_entities(entity_id),
    relationship_type VARCHAR(64) NOT NULL,
    properties JSONB DEFAULT '{}'::jsonb,
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP DEFAULT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    evidence_memories TEXT[] DEFAULT ARRAY[]::TEXT[],
    confidence FLOAT DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_entity_rel_source ON entity_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_target ON entity_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_type ON entity_relationships(relationship_type);
```

### Task 3: Create Episode Grouping Table
**Effort**: Low
**Node**: bluefin (database)

```sql
-- Episodes group related memories (conversations, sessions, events)
CREATE TABLE IF NOT EXISTS memory_episodes (
    episode_id SERIAL PRIMARY KEY,
    episode_type VARCHAR(32) NOT NULL,  -- 'conversation', 'deployment', 'debug_session', 'council_vote'
    episode_title VARCHAR(256),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP DEFAULT NULL,
    summary TEXT,
    memory_hashes TEXT[] DEFAULT ARRAY[]::TEXT[],
    entity_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    metadata JSONB DEFAULT '{}'::jsonb,
    is_complete BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_episode_type ON memory_episodes(episode_type);
CREATE INDEX IF NOT EXISTS idx_episode_time ON memory_episodes(started_at, ended_at);

-- Function to auto-group recent memories into episodes
CREATE OR REPLACE FUNCTION detect_episode_boundaries(
    memory_hash_list TEXT[],
    time_gap_minutes INTEGER DEFAULT 30
) RETURNS TABLE(episode_num INTEGER, memory_hash TEXT, started_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY
    WITH memory_times AS (
        SELECT m.memory_hash, m.created_at,
               LAG(m.created_at) OVER (ORDER BY m.created_at) as prev_time
        FROM thermal_memory_archive m
        WHERE m.memory_hash = ANY(memory_hash_list)
    ),
    gaps AS (
        SELECT memory_hash, created_at,
               CASE WHEN prev_time IS NULL 
                    OR EXTRACT(EPOCH FROM (created_at - prev_time))/60 > time_gap_minutes
                    THEN 1 ELSE 0 END as is_new_episode
        FROM memory_times
    ),
    numbered AS (
        SELECT memory_hash, created_at as started_at,
               SUM(is_new_episode) OVER (ORDER BY created_at) as episode_num
        FROM gaps
    )
    SELECT n.episode_num::INTEGER, n.memory_hash, n.started_at
    FROM numbered n
    ORDER BY n.started_at;
END;
$$ LANGUAGE plpgsql;
```

### Task 4: Create Temporal Query Library
**Effort**: Medium
**Node**: redfin (Python)

Create `/ganuda/lib/zep_temporal.py`:

```python
#!/usr/bin/env python3
"""
Zep-inspired Temporal Knowledge Graph for Cherokee AI Federation
Based on arXiv:2501.13956 - Graphiti temporal knowledge engine

Extends A-MEM with:
- Named Entity Recognition and linking
- Temporal validity on relationships
- Episode-based memory grouping
- Cross-session synthesis
"""

import psycopg2
import psycopg2.extras
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Cherokee AI Federation entity types
ENTITY_TYPES = {
    'NODE': ['redfin', 'bluefin', 'greenfin', 'sasass', 'sasass2', 'tpm-macbook', 'bmasass'],
    'SERVICE': ['vllm', 'gateway', 'llm gateway', 'telegram', 'grafana', 'prometheus', 
                'django', 'sag ui', 'kanban'],
    'AGENT': ['jr', 'gecko', 'turtle', 'eagle', 'spider', 'raven', 'crawdad', 'peace chief'],
    'MODEL': ['nemotron', 't5', 'mistral', 'llama', 'claude', 'qwen'],
    'CONCEPT': ['thermal memory', 'pheromone', 'stigmergy', 'council', 'a-mem', 
                's-madrl', 'zettelkasten', 'seven generations'],
    'PERSON': []  # Populated dynamically
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def extract_entities(content: str) -> List[Dict]:
    """
    Extract named entities from memory content.
    Uses pattern matching for Cherokee AI Federation domain entities.
    """
    entities = []
    content_lower = content.lower()
    
    for entity_type, patterns in ENTITY_TYPES.items():
        for pattern in patterns:
            if pattern.lower() in content_lower:
                # Find exact position(s)
                for match in re.finditer(re.escape(pattern), content, re.IGNORECASE):
                    entities.append({
                        'name': match.group(),
                        'type': entity_type,
                        'canonical_name': pattern.lower().replace(' ', '_'),
                        'offset': match.start(),
                        'context': content[max(0, match.start()-50):match.end()+50]
                    })
    
    # Extract IPs as entities
    ip_pattern = r'192\.168\.132\.\d{1,3}'
    for match in re.finditer(ip_pattern, content):
        ip = match.group()
        node_map = {'.222': 'bluefin', '.223': 'redfin', '.224': 'greenfin', 
                    '.241': 'sasass', '.242': 'sasass2'}
        for suffix, node in node_map.items():
            if ip.endswith(suffix):
                entities.append({
                    'name': ip,
                    'type': 'NODE',
                    'canonical_name': node,
                    'offset': match.start(),
                    'context': content[max(0, match.start()-30):match.end()+30]
                })
    
    return entities


def store_entity(entity: Dict) -> int:
    """Store or update entity in database, return entity_id."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_entities (entity_name, entity_type, canonical_name, mention_count)
            VALUES (%s, %s, %s, 1)
            ON CONFLICT (canonical_name, entity_type) DO UPDATE SET
                last_seen_at = NOW(),
                mention_count = memory_entities.mention_count + 1
            RETURNING entity_id
        """, (entity['name'], entity['type'], entity['canonical_name']))
        
        entity_id = cur.fetchone()[0]
        conn.commit()
    
    conn.close()
    return entity_id


def link_entity_to_memory(memory_hash: str, entity_id: int, 
                          context: str, offset: int) -> None:
    """Create mention link between memory and entity."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_entity_mentions 
            (memory_hash, entity_id, mention_context, mention_offset)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (memory_hash, entity_id, context, offset))
        conn.commit()
    
    conn.close()


def enrich_memory_with_entities(memory_hash: str, content: str) -> List[int]:
    """Extract and link entities from a memory."""
    entities = extract_entities(content)
    entity_ids = []
    
    for entity in entities:
        entity_id = store_entity(entity)
        entity_ids.append(entity_id)
        link_entity_to_memory(memory_hash, entity_id, 
                              entity.get('context', ''), entity.get('offset', 0))
    
    return entity_ids


def create_temporal_relationship(source_entity_id: int, target_entity_id: int,
                                  relationship_type: str, evidence_hash: str,
                                  properties: Dict = None) -> int:
    """Create or update temporal relationship between entities."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Close any existing current relationship of same type
        cur.execute("""
            UPDATE entity_relationships
            SET valid_until = NOW(), is_current = FALSE
            WHERE source_entity_id = %s AND target_entity_id = %s
              AND relationship_type = %s AND is_current = TRUE
        """, (source_entity_id, target_entity_id, relationship_type))
        
        # Create new relationship
        cur.execute("""
            INSERT INTO entity_relationships 
            (source_entity_id, target_entity_id, relationship_type, properties, evidence_memories)
            VALUES (%s, %s, %s, %s, ARRAY[%s])
            RETURNING rel_id
        """, (source_entity_id, target_entity_id, relationship_type,
                json.dumps(properties or {}), evidence_hash))
        
        rel_id = cur.fetchone()[0]
        conn.commit()
    
    conn.close()
    return rel_id


def temporal_query(question: str, as_of: datetime = None) -> List[Dict]:
    """
    Query memories with temporal reasoning.
    
    Supports:
    - "before <date>" / "after <date>"
    - "between <date1> and <date2>"
    - "last week" / "yesterday" / "today"
    - "when <entity> was <state>"
    """
    conn = get_connection()
    results = []
    
    # Parse temporal markers
    if as_of is None:
        as_of = datetime.now()
    
    # Extract time references
    time_filters = []
    
    if 'last week' in question.lower():
        time_filters.append(('created_at', '>', as_of - timedelta(days=7)))
    elif 'yesterday' in question.lower():
        time_filters.append(('created_at', '>', as_of - timedelta(days=1)))
        time_filters.append(('created_at', '<', as_of))
    elif 'today' in question.lower():
        time_filters.append(('created_at', '>', as_of.replace(hour=0, minute=0, second=0)))
    
    # Extract entity references
    entities = extract_entities(question)
    entity_filters = [e['canonical_name'] for e in entities]
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Build query
        query = """
            SELECT DISTINCT m.memory_hash, m.original_content, m.created_at,
                   m.temperature_score, m.tags
            FROM thermal_memory_archive m
        """
        
        params = []
        where_clauses = []
        
        # Add entity filters via mentions
        if entity_filters:
            query += """
                JOIN memory_entity_mentions mem ON m.memory_hash = mem.memory_hash
                JOIN memory_entities e ON mem.entity_id = e.entity_id
            """
            where_clauses.append("e.canonical_name = ANY(%s)")
            params.append(entity_filters)
        
        # Add time filters
        for col, op, val in time_filters:
            where_clauses.append(f"m.{col} {op} %s")
            params.append(val)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY m.created_at DESC LIMIT 20"
        
        cur.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return results


def get_entity_timeline(entity_name: str) -> List[Dict]:
    """Get temporal history of an entity - all memories mentioning it over time."""
    conn = get_connection()
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT m.memory_hash, m.original_content, m.created_at,
                   m.temperature_score, mem.mention_context
            FROM memory_entity_mentions mem
            JOIN memory_entities e ON mem.entity_id = e.entity_id
            JOIN thermal_memory_archive m ON mem.memory_hash = m.memory_hash
            WHERE e.canonical_name = %s OR e.entity_name ILIKE %s
            ORDER BY m.created_at ASC
        """, (entity_name.lower().replace(' ', '_'), f'%{entity_name}%'))
        
        results = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return results


def find_relationship_changes(entity1: str, entity2: str) -> List[Dict]:
    """Find how the relationship between two entities changed over time."""
    conn = get_connection()
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT er.relationship_type, er.properties, 
                   er.valid_from, er.valid_until, er.is_current,
                   e1.entity_name as source_name,
                   e2.entity_name as target_name
            FROM entity_relationships er
            JOIN memory_entities e1 ON er.source_entity_id = e1.entity_id
            JOIN memory_entities e2 ON er.target_entity_id = e2.entity_id
            WHERE (e1.canonical_name = %s AND e2.canonical_name = %s)
               OR (e1.canonical_name = %s AND e2.canonical_name = %s)
            ORDER BY er.valid_from ASC
        """, (entity1, entity2, entity2, entity1))
        
        results = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return results


def backfill_entities(batch_size: int = 100) -> Dict:
    """Backfill entity extraction for existing memories."""
    conn = get_connection()
    stats = {'processed': 0, 'entities_found': 0, 'mentions_created': 0}
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Find memories without entity mentions
        cur.execute("""
            SELECT m.memory_hash, m.original_content
            FROM thermal_memory_archive m
            LEFT JOIN memory_entity_mentions mem ON m.memory_hash = mem.memory_hash
            WHERE mem.mention_id IS NULL
            LIMIT %s
        """, (batch_size,))
        
        memories = cur.fetchall()
    
    conn.close()
    
    for memory in memories:
        entity_ids = enrich_memory_with_entities(
            memory['memory_hash'], 
            memory['original_content']
        )
        stats['processed'] += 1
        stats['entities_found'] += len(set(entity_ids))
        stats['mentions_created'] += len(entity_ids)
    
    return stats


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'backfill':
        batch = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        print(f"Backfilling entities for {batch} memories...")
        stats = backfill_entities(batch)
        print(f"Results: {stats}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test entity extraction
        test_content = """
        Deployed vLLM on redfin (192.168.132.223) with Nemotron model.
        Jr agent gecko completed the task. Council voted to proceed.
        """
        entities = extract_entities(test_content)
        print(f"Found {len(entities)} entities:")
        for e in entities:
            print(f"  - {e['name']} ({e['type']})")
    
    else:
        print("Usage: python zep_temporal.py [backfill N | test]")
```

### Task 5: Integrate Temporal Queries into LLM Gateway
**Effort**: Medium
**Node**: redfin

Add temporal memory endpoint to gateway:

```python
# Add to /ganuda/services/llm_gateway/gateway.py

from lib.zep_temporal import temporal_query, get_entity_timeline

@app.post("/v1/memory/temporal")
async def query_temporal_memory(request: Request):
    """
    Temporal memory query endpoint.
    
    POST /v1/memory/temporal
    {
        "question": "What did we do to redfin last week?",
        "as_of": "2025-12-23T00:00:00"  # optional
    }
    """
    data = await request.json()
    question = data.get('question', '')
    as_of_str = data.get('as_of')
    
    as_of = datetime.fromisoformat(as_of_str) if as_of_str else None
    
    results = temporal_query(question, as_of)
    
    return {
        "question": question,
        "as_of": as_of_str or "now",
        "results": results,
        "count": len(results)
    }

@app.get("/v1/entity/{entity_name}/timeline")
async def get_entity_history(entity_name: str):
    """Get full timeline for an entity."""
    timeline = get_entity_timeline(entity_name)
    return {
        "entity": entity_name,
        "timeline": timeline,
        "count": len(timeline)
    }
```

---

## VALIDATION CHECKLIST

After implementation, validate against Zep metrics:

- [ ] Entity extraction identifies nodes, services, agents, models
- [ ] Entity mentions link correctly to memories
- [ ] Temporal queries return time-filtered results
- [ ] Entity timeline shows chronological history
- [ ] Relationship versioning tracks changes over time
- [ ] Episode grouping clusters related memories
- [ ] Cross-session synthesis works ("What did we discuss about X across all sessions?")

---

## SUCCESS METRICS

| Metric | Zep Baseline | Cherokee Target |
|--------|-------------|-----------------|
| Temporal query accuracy | 94.8% (DMR) | >85% |
| Response latency | 90% reduction | >50% reduction |
| Cross-session synthesis | Yes | Observable |
| Entity resolution | High | >80% for domain entities |

---

## SEVEN GENERATIONS CONSIDERATION

Temporal memory serves the Seven Generations principle:
- **Past knowledge accessible** - What ancestors decided and why
- **Context preserved** - Not just facts, but the journey
- **Evolution visible** - How understanding changed over time
- **Wisdom transferable** - Future generations can trace reasoning

"Understanding the past illuminates the path forward."

---

## INTEGRATION WITH SWARMSYS

These two papers synergize:

1. **SwarmSys pheromones** guide agents to successful memory locations
2. **Zep temporal queries** help agents understand WHY those locations succeeded
3. **Entity relationships** track which agents worked on which entities
4. **Episode grouping** identifies successful collaboration patterns

Together: Agents learn not just WHERE to go, but WHEN and WHY.

---

*Created: December 23, 2025*
*Council Vote Audit Hash: aae46bac2393cb44*
