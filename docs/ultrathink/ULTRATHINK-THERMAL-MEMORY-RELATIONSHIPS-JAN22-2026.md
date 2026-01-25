# Ultrathink: Evolving Thermal Memory for Relationships-as-Things

**Date:** January 22, 2026
**Context:** Charles Simon's UKS insights applied to Cherokee AI

## Current State

Thermal memory stores flat facts:
```sql
thermal_memory_archive (
  id, memory_hash, original_content, metadata, temperature_score...
)
```

## Problem

Can't represent:
- Relationships between memories
- Conditional knowledge
- Provenance chains
- Temporal state vs history

## Proposed Evolution

### Option 1: PostgreSQL Graph Extension (Minimal Change)

Add relationship table:
```sql
CREATE TABLE thermal_relationships (
  id SERIAL PRIMARY KEY,
  source_memory_id INT REFERENCES thermal_memory_archive(id),
  relationship_type VARCHAR(50),  -- 'near', 'caused_by', 'if_then', 'learned_from'
  target_memory_id INT REFERENCES thermal_memory_archive(id),
  confidence FLOAT DEFAULT 1.0,
  valid_from TIMESTAMP,
  valid_until TIMESTAMP,  -- NULL = still valid
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Relationships can reference other relationships (the breakthrough!)
ALTER TABLE thermal_relationships 
ADD COLUMN source_relationship_id INT REFERENCES thermal_relationships(id),
ADD COLUMN target_relationship_id INT REFERENCES thermal_relationships(id);
```

### Option 2: Clause Table for Conditionals

```sql
CREATE TABLE thermal_clauses (
  id SERIAL PRIMARY KEY,
  clause_type VARCHAR(20),  -- 'if_then', 'and', 'or', 'not'
  relationship_ids INT[],   -- Array of relationship IDs in this clause
  evaluation_result BOOLEAN,
  last_evaluated TIMESTAMP,
  metadata JSONB
);
```

### Option 3: Full Graph Database (Apache AGE)

PostgreSQL extension for native graph queries:
```sql
-- Install Apache AGE
CREATE EXTENSION age;

-- Create graph
SELECT create_graph('thermal_graph');

-- Store as vertices and edges
SELECT * FROM cypher('thermal_graph', $$
  CREATE (p:Person {detected_at: 'front_door', confidence: 0.92})
  CREATE (d:Door {name: 'front_door'})
  CREATE (p)-[r:NEAR {distance: '2m', provenance: 'vlm'}]->(d)
  RETURN p, r, d
$$) as (p agtype, r agtype, d agtype);
```

## Recommended Approach: Hybrid

1. **Phase 1**: Add `thermal_relationships` table (minimal change)
2. **Phase 2**: Add `thermal_clauses` for conditionals
3. **Phase 3**: Evaluate Apache AGE for complex queries
4. **Phase 4**: Consider UKS for vision-specific graph

## VLM Integration Example

```python
# VLM returns description
vlm_result = {
    "description": "Person standing near front door, appears to be waiting",
    "entities": ["person", "door"],
    "relationships": [{"type": "near", "source": "person", "target": "door"}],
    "confidence": 0.89
}

# Store as thermal memories + relationships
person_id = store_thermal_memory("Entity: Person detected at front_door")
door_id = store_thermal_memory("Entity: Door (front_door)")
rel_id = store_thermal_relationship(
    source=person_id, 
    type="near", 
    target=door_id,
    confidence=0.89,
    metadata={"provenance": "vlm", "frame": "frame_001.jpg"}
)

# Create conditional clause
clause_id = store_thermal_clause(
    type="if_then",
    condition_relationships=[rel_id],
    action="alert_if_after_hours"
)
```

## Council Implications

Each specialist can query relationships:
- **Crawdad**: "Show all unauthorized access relationships"
- **Eagle Eye**: "What changed between frame N and N+1?"
- **Turtle**: "What relationship patterns persist across 7 generations?"

## Migration Path

1. Current memories remain unchanged
2. New relationships reference existing memories
3. Gradual enrichment as VLM extracts entities
4. No breaking changes to existing code

## For Seven Generations

This architecture supports:
- Historical relationship tracking (valid_from/valid_until)
- Provenance chains (learned_from relationships)
- Conditional wisdom (clauses)
- Pattern recognition across time
