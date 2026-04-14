-- Migration: Add edge embeddings for GNN compatibility (S-PATH-RAG)
-- Council Vote: S-PATH-RAG adoption APPROVED 12-1-0, Mar 30 2026
-- Jr Task: #1447 — S-PATH-RAG P-3: KG Schema Upgrade
-- Date: 2026-03-30

BEGIN;

-- Add embedding column to thermal_relationships (1024d BGE-large compatible)
ALTER TABLE thermal_relationships
ADD COLUMN IF NOT EXISTS edge_embedding vector(1024);

-- Add relationship type embedding (384d for type classification)
ALTER TABLE thermal_relationships
ADD COLUMN IF NOT EXISTS type_embedding vector(384);

-- Index for edge embedding similarity search
-- Using ivfflat with 50 lists (appropriate for <100K edges initially)
CREATE INDEX IF NOT EXISTS idx_thermal_rel_edge_embedding
ON thermal_relationships USING ivfflat (edge_embedding vector_cosine_ops)
WITH (lists = 50);

-- Composite index for path search: source → type → target (filter valid_until at query time)
CREATE INDEX IF NOT EXISTS idx_thermal_rel_path_search
ON thermal_relationships (source_memory_id, relationship_type, target_memory_id)
WHERE valid_until IS NULL;

-- Reverse path search index (target → source for bidirectional traversal)
CREATE INDEX IF NOT EXISTS idx_thermal_rel_reverse_path
ON thermal_relationships (target_memory_id, relationship_type, source_memory_id)
WHERE valid_until IS NULL;

-- Confidence-weighted path search (for Dijkstra with semantic weights)
CREATE INDEX IF NOT EXISTS idx_thermal_rel_confidence
ON thermal_relationships (confidence DESC)
WHERE valid_until IS NULL;

COMMIT;
