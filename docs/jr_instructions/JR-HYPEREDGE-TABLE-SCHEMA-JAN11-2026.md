# Jr Instruction: Hyperedge Table Schema for Thermal Memory

**Date**: January 11, 2026
**Priority**: MEDIUM
**Target Node**: bluefin (PostgreSQL)
**TPM**: Flying Squirrel (dereadi)
**Council Vote**: 24462bd0faef976d (84.4% confidence, PROCEED WITH CAUTION)

## Background

The Council approved prototyping hypergraph structures starting with thermal_memory. Hyperedges allow modeling higher-order relationships (3+ nodes connected simultaneously) rather than just pairwise links.

**Source**: MIT paper by Stewart & Buehler - "Higher-Order Knowledge Representations for Agentic Scientific Reasoning"
**GitHub**: https://github.com/lamm-mit/HyperGraph

## Use Cases

1. **Research Trail**: Link research paper → implementation → validation → council vote as ONE relationship
2. **Topic Continuity**: Connect memories that discuss the same topic across sessions
3. **Deployment Chain**: Link Jr instruction → code changes → deployment → verification
4. **Knowledge Synthesis**: Connect multiple memories that together form a complete concept

## Schema Design

### New Table: `thermal_hyperedges`

```sql
CREATE TABLE thermal_hyperedges (
    hyperedge_id SERIAL PRIMARY KEY,

    -- Hyperedge metadata
    edge_type VARCHAR(50) NOT NULL,  -- 'research_trail', 'topic_thread', 'deployment_chain', 'synthesis'
    label VARCHAR(255),               -- Human-readable description

    -- Connected memories (array of memory_hash values)
    member_hashes TEXT[] NOT NULL,    -- Array of memory_hash from thermal_memory_archive
    member_count INTEGER GENERATED ALWAYS AS (array_length(member_hashes, 1)) STORED,

    -- Relationship semantics
    relationship_type VARCHAR(50),    -- 'sequential', 'parallel', 'hierarchical', 'associative'
    directionality VARCHAR(20) DEFAULT 'undirected',  -- 'directed', 'undirected'

    -- Strength and decay (aligned with thermal memory)
    strength FLOAT DEFAULT 1.0,       -- Hyperedge strength (decays like pheromones)
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,

    -- Provenance
    created_by VARCHAR(100),          -- 'tpm', 'jr', 'council', 'auto'
    source_session VARCHAR(100),

    -- Optional: ordered members for sequential relationships
    member_order JSONB,               -- {"memory_hash_1": 1, "memory_hash_2": 2, ...}

    -- Metadata
    tags TEXT[],
    metadata JSONB
);

-- Indexes for efficient querying
CREATE INDEX idx_hyperedge_type ON thermal_hyperedges(edge_type);
CREATE INDEX idx_hyperedge_members ON thermal_hyperedges USING GIN(member_hashes);
CREATE INDEX idx_hyperedge_tags ON thermal_hyperedges USING GIN(tags);
CREATE INDEX idx_hyperedge_strength ON thermal_hyperedges(strength DESC);

-- Constraint: minimum 2 members (though hyperedges typically have 3+)
ALTER TABLE thermal_hyperedges ADD CONSTRAINT min_members CHECK (array_length(member_hashes, 1) >= 2);
```

### Junction Table: `hyperedge_members` (Alternative Design)

For more complex queries, a junction table may be useful:

```sql
CREATE TABLE hyperedge_members (
    id SERIAL PRIMARY KEY,
    hyperedge_id INTEGER REFERENCES thermal_hyperedges(hyperedge_id) ON DELETE CASCADE,
    memory_hash VARCHAR(32) NOT NULL,
    role VARCHAR(50),                 -- 'source', 'implementation', 'validation', etc.
    position INTEGER,                 -- Order in sequence (if applicable)
    added_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(hyperedge_id, memory_hash)
);

CREATE INDEX idx_hm_hyperedge ON hyperedge_members(hyperedge_id);
CREATE INDEX idx_hm_memory ON hyperedge_members(memory_hash);
```

## Query Patterns

### Find all hyperedges containing a memory

```sql
SELECT h.*
FROM thermal_hyperedges h
WHERE 'abc123def456' = ANY(h.member_hashes);
```

### Find related memories through hyperedges (spreading activation)

```sql
-- Given a memory hash, find all memories connected via hyperedges
WITH connected AS (
    SELECT UNNEST(member_hashes) as related_hash
    FROM thermal_hyperedges
    WHERE 'abc123def456' = ANY(member_hashes)
)
SELECT DISTINCT t.*
FROM thermal_memory_archive t
JOIN connected c ON t.memory_hash = c.related_hash
WHERE t.memory_hash != 'abc123def456';
```

### Find research trails

```sql
SELECT h.label, h.member_hashes, h.member_order
FROM thermal_hyperedges h
WHERE h.edge_type = 'research_trail'
ORDER BY h.created_at DESC;
```

## Decay Function

Align with existing pheromone decay:

```sql
-- Decay hyperedge strength (run with pheromone_decay.sh)
UPDATE thermal_hyperedges
SET strength = strength * 0.95
WHERE last_accessed < NOW() - INTERVAL '7 days';

-- Boost strength on access
UPDATE thermal_hyperedges
SET strength = LEAST(strength * 1.1, 1.0),
    last_accessed = NOW(),
    access_count = access_count + 1
WHERE hyperedge_id = $1;
```

## Security Requirements (per Crawdad)

1. **Audit Logging**: Log all hyperedge creation/modification
2. **No PII in hyperedges**: Only reference memory_hash, not content
3. **Access Control**: Same permissions as thermal_memory_archive

```sql
-- Audit trigger
CREATE OR REPLACE FUNCTION log_hyperedge_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO thermal_memory_archive (
        memory_hash, original_content, temperature_score, tags,
        source_triad, source_node, memory_type
    ) VALUES (
        md5('hyperedge_audit_' || NEW.hyperedge_id || '_' || NOW()),
        'HYPEREDGE ' || TG_OP || ': ' || NEW.label || ' (ID: ' || NEW.hyperedge_id || ')',
        50.0,
        ARRAY['audit', 'hyperedge', NEW.edge_type],
        'system', 'bluefin', 'audit'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hyperedge_audit_trigger
AFTER INSERT OR UPDATE ON thermal_hyperedges
FOR EACH ROW EXECUTE FUNCTION log_hyperedge_changes();
```

## Integration Points

### 1. Thermal Memory Insert Hook

When creating high-temperature memories, check for related memories and suggest hyperedge creation:

```python
async def suggest_hyperedges(new_memory_hash: str, tags: list, content: str):
    """Find potential hyperedge candidates based on tags and content similarity"""
    # Query for memories with overlapping tags
    # Return suggestions for TPM review
    pass
```

### 2. Council Vote Integration

After council votes, automatically create research trail hyperedge:

```python
async def create_research_trail(audit_hash: str, related_memories: list):
    """Create hyperedge linking council vote to related research"""
    pass
```

### 3. Spreading Activation (Synapse alignment)

Use hyperedges for spreading activation in memory retrieval:

```python
async def spread_activation(seed_hash: str, depth: int = 2):
    """Retrieve memories connected via hyperedges up to N hops"""
    pass
```

## Verification

After implementation:

```sql
-- Verify table exists
\d thermal_hyperedges

-- Create test hyperedge
INSERT INTO thermal_hyperedges (edge_type, label, member_hashes, created_by)
VALUES (
    'research_trail',
    'Hypergraph Research Trail',
    ARRAY['abc123', 'def456', 'ghi789'],
    'test'
);

-- Verify query works
SELECT * FROM thermal_hyperedges WHERE 'abc123' = ANY(member_hashes);
```

## Related Documentation

- Council Vote: 24462bd0faef976d
- MIT Paper: https://github.com/lamm-mit/HyperGraph
- Synapse Paper: arXiv:2601.02744 (spreading activation)
- Mem0 Paper: arXiv:2504.19413 (graph-based memory)

---

For Seven Generations.
