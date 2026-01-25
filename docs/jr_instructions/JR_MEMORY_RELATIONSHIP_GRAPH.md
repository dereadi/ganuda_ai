# Jr Task: Implement Memory Relationship Graph

**Ticket:** #1698
**Priority:** P2
**Node:** bluefin (database)
**Created:** December 21, 2025
**Specialist:** Turtle (Seven Generations Wisdom)

---

## Research Basis

**Sources:**
- [Stigmergy: The Future of Decentralized AI](https://www.numberanalytics.com/blog/stigmergy-future-decentralized-ai)
- [Automatic Design of Stigmergy-Based Behaviors](https://www.nature.com/articles/s44172-024-00175-7)

**Key Concepts:**
- Stigmergy = coordination through environment modification
- "Pheromone trails" connect related information
- Positive/negative feedback loops enhance/suppress paths
- No central control - emergent organization

**Current Gap:** Thermal memories are isolated entries. No relationships between them. Cannot traverse "related knowledge."

---

## Proposed Architecture

### Graph Schema

```sql
-- Memory relationship edges
CREATE TABLE memory_relationships (
    id SERIAL PRIMARY KEY,
    source_hash VARCHAR(128) NOT NULL,
    target_hash VARCHAR(128) NOT NULL,
    relationship_type VARCHAR(32) NOT NULL,
    strength FLOAT DEFAULT 1.0,        -- Pheromone strength (decays over time)
    created_at TIMESTAMP DEFAULT NOW(),
    last_traversed TIMESTAMP,
    traversal_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',

    -- Constraints
    UNIQUE(source_hash, target_hash, relationship_type),
    FOREIGN KEY (source_hash) REFERENCES thermal_memory_archive(memory_hash),
    FOREIGN KEY (target_hash) REFERENCES thermal_memory_archive(memory_hash)
);

-- Indexes for graph traversal
CREATE INDEX idx_memory_rel_source ON memory_relationships(source_hash);
CREATE INDEX idx_memory_rel_target ON memory_relationships(target_hash);
CREATE INDEX idx_memory_rel_type ON memory_relationships(relationship_type);
CREATE INDEX idx_memory_rel_strength ON memory_relationships(strength DESC);
```

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `references` | One memory cites another | Bug fix references original error |
| `supersedes` | Newer info replaces older | Updated config supersedes old |
| `relates_to` | Topically related | All T5-Gemma 2 research |
| `causes` | Causal relationship | Error caused by config change |
| `requires` | Dependency | Feature requires other feature |
| `contradicts` | Conflicting information | Flag for resolution |

---

## Implementation

### Phase 1: Schema Creation

```sql
-- Run on bluefin
CREATE TABLE IF NOT EXISTS memory_relationships (
    id SERIAL PRIMARY KEY,
    source_hash VARCHAR(128) NOT NULL,
    target_hash VARCHAR(128) NOT NULL,
    relationship_type VARCHAR(32) NOT NULL,
    strength FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_traversed TIMESTAMP,
    traversal_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    UNIQUE(source_hash, target_hash, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_memory_rel_source ON memory_relationships(source_hash);
CREATE INDEX IF NOT EXISTS idx_memory_rel_target ON memory_relationships(target_hash);
CREATE INDEX IF NOT EXISTS idx_memory_rel_strength ON memory_relationships(strength DESC);
```

### Phase 2: Relationship Detection

```python
# /ganuda/lib/memory_graph.py

import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np

class MemoryGraph:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="192.168.132.222",
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

    def add_relationship(self, source_hash, target_hash, rel_type, strength=1.0, metadata=None):
        """Add edge between memories"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memory_relationships
                    (source_hash, target_hash, relationship_type, strength, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_hash, target_hash, relationship_type)
                DO UPDATE SET strength = memory_relationships.strength + %s
            """, (source_hash, target_hash, rel_type, strength,
                  json.dumps(metadata or {}), strength * 0.5))
            self.conn.commit()

    def find_related(self, memory_hash, rel_type=None, min_strength=0.5, limit=10):
        """Find related memories"""
        with self.conn.cursor() as cur:
            query = """
                SELECT m.memory_hash, m.original_content, m.temperature_score,
                       r.relationship_type, r.strength
                FROM memory_relationships r
                JOIN thermal_memory_archive m ON r.target_hash = m.memory_hash
                WHERE r.source_hash = %s AND r.strength >= %s
            """
            params = [memory_hash, min_strength]

            if rel_type:
                query += " AND r.relationship_type = %s"
                params.append(rel_type)

            query += " ORDER BY r.strength DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            return cur.fetchall()

    def traverse_path(self, start_hash, end_hash, max_depth=5):
        """Find path between memories (BFS)"""
        visited = set()
        queue = [(start_hash, [start_hash])]

        while queue and len(visited) < 1000:
            current, path = queue.pop(0)

            if current == end_hash:
                return path

            if current in visited:
                continue
            visited.add(current)

            if len(path) >= max_depth:
                continue

            for related in self.find_related(current, limit=20):
                next_hash = related[0]
                if next_hash not in visited:
                    queue.append((next_hash, path + [next_hash]))

        return None  # No path found

    def strengthen_path(self, path):
        """Reinforce traversed path (positive feedback)"""
        for i in range(len(path) - 1):
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE memory_relationships
                    SET strength = strength * 1.1,
                        last_traversed = NOW(),
                        traversal_count = traversal_count + 1
                    WHERE source_hash = %s AND target_hash = %s
                """, (path[i], path[i+1]))
            self.conn.commit()

    def auto_detect_relationships(self, memory_hash, content, threshold=0.7):
        """Automatically find related memories via embedding similarity"""
        # Get embedding for new memory
        new_embedding = self.encoder.encode(content)

        # Find candidates (recent memories with embeddings)
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash, original_content, embedding
                FROM thermal_memory_archive
                WHERE memory_hash != %s
                AND embedding IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 500
            """, (memory_hash,))
            candidates = cur.fetchall()

        # Calculate similarities
        for cand_hash, cand_content, cand_embedding in candidates:
            if cand_embedding:
                similarity = np.dot(new_embedding, np.array(cand_embedding))
                if similarity >= threshold:
                    self.add_relationship(
                        memory_hash, cand_hash,
                        'relates_to',
                        strength=similarity
                    )
```

### Phase 3: Pheromone Decay

Add to existing `/ganuda/scripts/pheromone_decay.sh`:

```bash
# Decay relationship strengths (relationships that aren't used weaken)
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production << 'EOF'

-- Decay unused relationships (not traversed in 30 days)
UPDATE memory_relationships
SET strength = strength * 0.95
WHERE last_traversed IS NULL
   OR last_traversed < NOW() - INTERVAL '30 days';

-- Remove very weak relationships
DELETE FROM memory_relationships
WHERE strength < 0.1;

-- Log decay stats
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
SELECT
    'pheromone-decay-' || TO_CHAR(NOW(), 'YYYYMMDD'),
    'Pheromone decay cycle: ' || COUNT(*) || ' relationships decayed, ' ||
    (SELECT COUNT(*) FROM memory_relationships WHERE strength < 0.1) || ' pruned',
    50.0,
    '{"type": "maintenance"}'::jsonb
FROM memory_relationships
WHERE last_traversed IS NULL OR last_traversed < NOW() - INTERVAL '30 days';

EOF
```

### Phase 4: Integration with Thermal Memory Writes

When writing to thermal memory, auto-detect relationships:

```python
def write_thermal_memory(content, metadata):
    # Write memory
    memory_hash = generate_hash(content)
    insert_memory(memory_hash, content, metadata)

    # Auto-detect relationships
    graph = MemoryGraph()
    graph.auto_detect_relationships(memory_hash, content)

    # If metadata specifies explicit relationships, add those
    if 'references' in metadata:
        for ref_hash in metadata['references']:
            graph.add_relationship(memory_hash, ref_hash, 'references')

    if 'supersedes' in metadata:
        graph.add_relationship(memory_hash, metadata['supersedes'], 'supersedes')
```

---

## Usage Examples

### Find Related Knowledge

```python
graph = MemoryGraph()

# What's related to the T5-Gemma 2 research?
related = graph.find_related('t5-gemma2-research-20251221')
for mem in related:
    print(f"{mem[0]}: {mem[1][:100]}... (strength: {mem[4]})")
```

### Traverse Knowledge Path

```python
# How does the Telegram bot fix relate to the health monitor?
path = graph.traverse_path(
    'fix-telegram-alert-20251221',
    'health-monitor-setup-20251212'
)
if path:
    print("Knowledge path:", " -> ".join(path))
    graph.strengthen_path(path)  # Reinforce this connection
```

### Query with Graph Context

```python
def query_with_context(question, seed_memories):
    """Enhanced query that includes graph-related memories"""
    all_context = []
    graph = MemoryGraph()

    for seed in seed_memories:
        all_context.append(get_memory(seed))
        # Add related memories
        for related in graph.find_related(seed, limit=3):
            all_context.append(related)

    return query_llm(question, context=all_context)
```

---

## Success Criteria

1. Memories form clusters around topics (visible in graph)
2. Frequently used paths strengthen over time
3. Stale/unused relationships decay and get pruned
4. Query quality improves with graph context
5. Can answer "how does X relate to Y?" questions

---

## Visualization (Optional)

Export graph for visualization:

```sql
-- Export for Gephi/Neo4j visualization
COPY (
    SELECT source_hash, target_hash, relationship_type, strength
    FROM memory_relationships
    WHERE strength > 0.3
) TO '/tmp/memory_graph.csv' WITH CSV HEADER;
```

---

*For Seven Generations - Cherokee AI Federation*
