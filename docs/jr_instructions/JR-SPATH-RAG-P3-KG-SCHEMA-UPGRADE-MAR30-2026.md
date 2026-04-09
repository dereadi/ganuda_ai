# JR INSTRUCTION: S-PATH-RAG P-3 — Knowledge Graph Schema Upgrade for GNN Compatibility

**Task**: Add edge/relationship embeddings and GNN-compatible indexes to thermal_relationships. Foundation for S-PATH-RAG.
**Priority**: P1 (blocks all subsequent S-PATH-RAG work)
**Date**: 2026-03-30
**TPM**: Claude Opus
**Council Vote**: S-PATH-RAG adoption APPROVED 12-1-0
**Story Points**: 2
**Depends On**: thermal_relationships table (EXISTS, 3 edges), thermal_memory_archive embeddings (EXISTS, 88% coverage)

## Problem Statement

The `thermal_relationships` table has the right relational schema (source, target, type, confidence, provenance, temporal validity) but no vector embeddings on edges. S-PATH-RAG requires GNN processing of graph structure, which needs dense vector representations for both nodes AND edges.

Nodes already have embeddings (thermal_memory_archive.embedding, 1024d BGE-large). Edges have nothing.

## Task 1: Add Edge Embedding Column (0.5 SP)

**File**: New migration SQL

```sql
-- Migration: Add edge embeddings for GNN compatibility
-- S-PATH-RAG adoption, Council vote Mar 30 2026

BEGIN;

-- Add embedding column to thermal_relationships
ALTER TABLE thermal_relationships
ADD COLUMN IF NOT EXISTS edge_embedding vector(1024);

-- Add relationship type embedding (smaller, for type classification)
ALTER TABLE thermal_relationships
ADD COLUMN IF NOT EXISTS type_embedding vector(384);

-- Index for edge embedding similarity search
CREATE INDEX IF NOT EXISTS idx_thermal_rel_edge_embedding
ON thermal_relationships USING ivfflat (edge_embedding vector_cosine_ops)
WITH (lists = 50);

-- Composite index for path search: source → type → target with confidence
CREATE INDEX IF NOT EXISTS idx_thermal_rel_path_search
ON thermal_relationships (source_memory_id, relationship_type, target_memory_id)
WHERE valid_until IS NULL OR valid_until > NOW();

COMMIT;
```

Save as: `/ganuda/sql/migration_thermal_relationships_v2_gnn.sql`

Run on bluefin:
```bash
PGPASSWORD=$CHEROKEE_DB_PASS psql -h 10.100.0.2 -U claude -d triad_federation -f /ganuda/sql/migration_thermal_relationships_v2_gnn.sql
```

## Task 2: Edge Embedding Generator (1 SP)

**Create**: `/ganuda/lib/kg_edge_embedder.py`

When a relationship is created, generate an edge embedding by combining:
1. Source node embedding (from thermal_memory_archive)
2. Target node embedding (from thermal_memory_archive)
3. Relationship type text (embedded via BGE-large on greenfin:8003)

Combination method: concatenate source + target + type embeddings, then project down to 1024d via mean pooling or a learned projection.

```python
def embed_edge(source_embedding, target_embedding, relationship_type: str) -> list:
    """Generate edge embedding from source, target, and relationship type.

    Uses the formula: edge = mean(source, target, type_embed)
    This preserves directionality (source→target order matters in concat)
    while keeping dimensionality at 1024d.
    """
    # Get type embedding from greenfin embedding service
    type_embed = get_embedding(relationship_type)  # 1024d from BGE-large

    # Mean pool the three vectors
    edge = np.mean([source_embedding, target_embedding, type_embed], axis=0)
    return edge.tolist()
```

**Integration point**: Hook into `create_thermal_relationship()` function or call after edge creation in `kg_auto_relate.py`.

## Task 3: Update Auto-Relate Task (#1445) (0.5 SP)

The existing pending task `#1445 — SkillRL KG Phase 0: Auto-Relate Thermal Edges` creates edges based on embedding similarity. Update the instruction to also:

1. Generate edge embeddings for every new relationship using the edge embedder
2. Store edge_embedding in the thermal_relationships row
3. Use relationship_type-specific thresholds (not one global threshold)

This is a modification to the existing Jr instruction, not a new task.

## Verification

1. Migration runs cleanly: `\d thermal_relationships` shows `edge_embedding vector(1024)` column
2. Edge embedder produces valid 1024d vectors: test with 2 known thermals and a relationship type
3. IVFFlat index created: `\di idx_thermal_rel_edge_embedding`
4. Auto-relate task updated to include edge embedding generation

## Success Criteria

- [ ] `edge_embedding` column exists on thermal_relationships
- [ ] `type_embedding` column exists on thermal_relationships
- [ ] IVFFlat index on edge_embedding is created
- [ ] Path search composite index is created
- [ ] Edge embedder function works end-to-end (source + target + type → 1024d vector)
- [ ] Auto-relate task (#1445) instruction updated to include edge embedding

---

FOR SEVEN GENERATIONS
