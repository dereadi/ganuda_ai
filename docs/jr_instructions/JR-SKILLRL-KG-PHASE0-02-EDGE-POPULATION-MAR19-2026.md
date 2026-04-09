# Jr Instruction: SkillRL KG Phase 0 — Auto-Relate Thermal Edges

**Epic**: SKILLRL-EPIC (Phase 0: KG Formalization)
**Council Vote**: #8984 (0.87, APPROVED 7-1)
**Estimated SP**: 2
**Depends On**: `thermal_relationships` table (migration_thermal_relationships_v1.sql — already deployed Jan 22 2026)
**Academic Basis**: Princeton "Alternative Trajectory for Generative AI" — KG structure requires edges, not just nodes. Thermalized as #129586.
**Kanban**: task_id 383d4e33

---

## Objective

The knowledge graph has **92,867 nodes** (thermals) but only **3 edges** (thermal_relationships). A graph with no edges is a point cloud. This task creates a post-thermalization hook that automatically populates edges when new thermals are created, turning the point cloud into a traversable knowledge graph.

Phase 0 scope: automatic edge creation on NEW thermals only. Backfill of existing 92K thermals is Phase 1 (separate Jr instruction, separate SP budget — Coyote cap).

## Design

### File: `/ganuda/lib/kg_auto_relate.py`

```python
class KGAutoRelate:
    """Create thermal_relationships edges on new thermals."""

    def relate_new_thermal(self, thermal_id: int, db_conn) -> list[int]:
        """
        Find related thermals and create edges.
        Returns list of created relationship IDs.
        """
```

### Edge Creation Rules

**Rule 1: Embedding Similarity (relationship_type = 'semantically_related')**
- Query greenfin embedding service (port 8003) for top-3 similar thermals
- Cosine similarity threshold: **>0.82** (stricter than experience bank's 0.7 — Coyote: edges should be strong connections, not weak associations)
- Use the new thermal's embedding vector, search against `thermal_memory_archive.embedding` via pgvector
- Create bidirectional edges (A→B and B→A) with confidence = cosine_score
- Provenance: `'kg_auto_relate'`

**Rule 2: Tag Co-occurrence (relationship_type = 'shares_topic')**
- If new thermal shares 2+ tags with an existing thermal → create edge
- Only consider thermals from last 30 days (temporal locality — old tag matches are noise)
- Confidence: `shared_tag_count / max(total_tags_a, total_tags_b)`
- Max 5 edges per rule per thermal (Coyote: don't explode edge count)

**Rule 3: Source Triad Chains (relationship_type = 'same_session')**
- If new thermal has same `source_session` as existing thermals → create `same_session` edge
- These are thermals born in the same conversation — inherently related
- Confidence: 0.9 (high — same session is strong signal)
- Max 10 edges (sessions can be long)

### What This Task Does NOT Do

- **No backfill** of existing 92K thermals. That's Phase 1, separate budget.
- **No council vote edges** — those require parsing `council_votes.question` text. Separate task.
- **No Jr task dependency edges** — those require `jr_task_queue.parent_task_id`. Separate task.
- **No traversal queries** — this task creates edges. Traversal is downstream (experience bank augmentation).

### Integration Point

This should be called as a **post-thermalization hook** wherever thermals are created. The primary thermalization paths are:

1. `lib/thermalize.py` (or equivalent thermal creation function)
2. `lib/governance_agent.py` (council vote thermalization)
3. Manual thermalization via API

Add a function call after successful INSERT into `thermal_memory_archive`:
```python
from lib.kg_auto_relate import KGAutoRelate
kg = KGAutoRelate()
kg.relate_new_thermal(new_thermal_id, db_conn)
```

Fire-and-forget. If it fails, the thermal still exists — edges are supplementary.

### Performance Budget

- Embedding similarity query: use pgvector `<=>` operator (cosine distance), IVFFlat index already exists
- Tag co-occurrence: SQL query with `tags && %s` (array overlap operator)
- Source session: simple WHERE clause
- Total budget: **< 200ms per thermalization** (Spider condition)
- If over budget, log warning and skip remaining rules

## Steps

1. Create `/ganuda/lib/kg_auto_relate.py` with `KGAutoRelate` class
2. Implement three edge creation rules: embedding similarity, tag co-occurrence, source session chains
3. Use `create_thermal_relationship()` PostgreSQL function (already exists from migration_thermal_relationships_v1.sql)
4. Add 200ms total timeout across all rules
5. Wire into thermalization path(s) as post-hook — identify where thermals are INSERTed and add the call
6. Write tests in `/ganuda/tests/test_kg_auto_relate.py`:
   - Test each rule independently with known thermals
   - Test timeout behavior (mock slow query)
   - Test edge deduplication (don't create duplicate edges)
   - Test threshold enforcement (similarity < 0.82 creates no edge)

## Verification

1. Thermalize a test memory, check `thermal_relationships` for new edges
2. Verify edge count grows proportionally (not explosively) — target 3-8 edges per new thermal
3. Verify `active_thermal_relationships` view works (create the view if migration didn't deploy it — Query 3 showed it doesn't exist)
4. Check edges have correct provenance (`kg_auto_relate`) and confidence scores

## Council Concerns Applied

- **Coyote**: 0.82 cosine threshold (high bar). Max edges per rule (5/5/10). No backfill in Phase 0.
- **Spider**: 200ms total budget. Fire-and-forget. Thermal exists regardless.
- **Eagle Eye**: Provenance tracking on all edges for audit.
- **Turtle**: Edges use soft-delete (`invalidate_thermal_relationship()` sets `valid_until`). Reversible.
- **Crawdad**: No PII in edges — only thermal IDs, relationship types, and confidence scores.

## Migration Note

The `active_thermal_relationships` VIEW from the migration SQL may not have been deployed (Query 3 returned "table does not exist"). If missing, create it:

```sql
CREATE OR REPLACE VIEW active_thermal_relationships AS
SELECT * FROM thermal_relationships
WHERE valid_until IS NULL OR valid_until > NOW();
```
