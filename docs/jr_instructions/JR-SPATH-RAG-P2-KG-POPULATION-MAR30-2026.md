# JR INSTRUCTION: S-PATH-RAG P-2 — Knowledge Graph Population Sprint

**Task**: Populate thermal_relationships from 3 edges to meaningful coverage. Build the graph that S-PATH-RAG will traverse.
**Priority**: P1 (blocks path search and GNN encoding)
**Date**: 2026-03-30
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: JR-SPATH-RAG-P3-KG-SCHEMA-UPGRADE (edge embeddings available)

## Problem Statement

We have 95,672 thermal memories and 3 relationships. That's not a knowledge graph, it's three lines on a whiteboard. S-PATH-RAG needs a connected graph with meaningful paths to search. The auto-relate task (#1445) was designed for this but hasn't run and needs augmentation.

## Target State

- **Nodes**: 95K+ thermal memories (already exist)
- **Edges**: Target 50K-100K relationships across 8-10 relationship types
- **Coverage**: Every thermal with an embedding should have at least 2 relationships
- **Edge embeddings**: Every relationship has a 1024d edge_embedding

## Task 1: Batch Auto-Relate — Embedding Similarity (3 SP)

**Create**: `/ganuda/scripts/kg_batch_relate.py`

Process all thermal memories with embeddings and create relationships based on:

### Relationship Type 1: `semantically_near` (cosine similarity > 0.75)
```sql
-- For each thermal, find the top-5 most similar thermals
-- Use pgvector cosine distance
SELECT t2.id, 1 - (t1.embedding <=> t2.embedding) as similarity
FROM thermal_memory_archive t1, thermal_memory_archive t2
WHERE t1.id = $1 AND t2.id != t1.id
  AND t1.embedding IS NOT NULL AND t2.embedding IS NOT NULL
ORDER BY t1.embedding <=> t2.embedding
LIMIT 5;
```

Create `semantically_near` edges for pairs with similarity > 0.75. Store similarity as confidence.

**IMPORTANT**: Process in batches of 500 to avoid memory issues. Use cursor-based pagination. Checkpoint progress in a state file so the script can resume.

### Relationship Type 2: `temporal_sequence` (created within 1 hour of each other, same domain_tag)
```sql
SELECT t2.id
FROM thermal_memory_archive t1, thermal_memory_archive t2
WHERE t1.id = $1 AND t2.id != t1.id
  AND t1.domain_tag = t2.domain_tag
  AND ABS(EXTRACT(EPOCH FROM (t1.created_at - t2.created_at))) < 3600
ORDER BY t2.created_at
LIMIT 3;
```

### Relationship Type 3: `same_domain` (same domain_tag, different content)
Group by domain_tag, create edges between thermals sharing the same tag.

### Relationship Type 4: `sacred_cluster` (sacred thermals linked to each other)
All sacred=true thermals form a fully connected subgraph. These are the highest-value nodes.

### Relationship Type 5: `council_voted` (thermals with council vote audit hashes in metadata)
Link thermals to the council votes that referenced them.

### Relationship Type 6: `jr_task_chain` (thermals created during Jr task execution)
Link thermals by Jr task ID from metadata, preserving the task execution chain.

## Task 2: Edge Embedding Backfill (1 SP)

After batch auto-relate runs, backfill edge embeddings for all new relationships:

```python
# For each relationship without an edge_embedding
for rel in relationships_without_embeddings:
    source_emb = get_node_embedding(rel.source_memory_id)
    target_emb = get_node_embedding(rel.target_memory_id)
    edge_emb = embed_edge(source_emb, target_emb, rel.relationship_type)
    update_edge_embedding(rel.id, edge_emb)
```

Process in batches. This is I/O bound (reading embeddings from DB), not compute bound.

## Task 3: Relationship Statistics and Validation (1 SP)

After population, generate a report:

```python
# Report includes:
# - Total edges by type
# - Average confidence by type
# - Node degree distribution (min, max, median, p95)
# - Connected components count (should be small — ideally 1 giant component)
# - Isolated nodes (nodes with 0 edges)
# - Edge embedding coverage (should be 100%)
```

Save to `/ganuda/state/kg_population_report.json` and thermal memory.

**Critical check**: If more than 20% of embedded thermals are isolated (0 edges), the similarity threshold is too high. Lower to 0.70 and re-run.

## Execution Notes

- Run on redfin (has the DB connection and enough RAM for batch processing)
- Use WireGuard IP for DB: `10.100.0.2:5432`
- Use greenfin embedding service for type embeddings: `192.168.132.224:8003`
- Estimated runtime: 2-4 hours for 95K thermals (pgvector cosine search is fast with IVFFlat)
- Checkpoint every 1000 thermals processed so the script can resume on crash

## Verification

```sql
-- Quick health check after population
SELECT relationship_type, COUNT(*), AVG(confidence)::numeric(4,2)
FROM thermal_relationships
WHERE valid_until IS NULL OR valid_until > NOW()
GROUP BY relationship_type
ORDER BY count DESC;

-- Edge embedding coverage
SELECT
    COUNT(*) as total,
    COUNT(edge_embedding) as with_embedding,
    ROUND(COUNT(edge_embedding)::numeric / COUNT(*)::numeric * 100, 1) as pct
FROM thermal_relationships;

-- Isolated nodes
SELECT COUNT(*) FROM thermal_memory_archive t
WHERE t.embedding IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM thermal_relationships r
    WHERE r.source_memory_id = t.id OR r.target_memory_id = t.id
  );
```

---

FOR SEVEN GENERATIONS
