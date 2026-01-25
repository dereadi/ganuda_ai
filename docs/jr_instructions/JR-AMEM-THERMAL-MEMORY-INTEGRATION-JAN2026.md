# JR Instruction: A-MEM Thermal Memory Integration

## Date: January 16, 2026
## Priority: P1 (Council Unanimous HIGH)
## Council Vote: 6700b2d88464ab8b
## Assigned To: IT Triad
## Target: Q2 2026

---

## Overview

Integrate A-MEM (Agentic Memory) principles into the Cherokee AI Federation's thermal memory system. A-MEM uses Zettelkasten-inspired knowledge management with atomic notes, bidirectional links, and progressive summarization.

**Council Concerns:**
- Gecko [PERF CONCERN]: Increased memory usage from bidirectional links and summarization

---

## Background: What is A-MEM?

A-MEM (Agentic Memory) is a memory architecture for AI agents inspired by the Zettelkasten method:

1. **Atomic Notes**: Each memory is a single, self-contained concept
2. **Bidirectional Links**: Memories link to related memories (both directions)
3. **Progressive Summarization**: Frequently accessed memories get condensed summaries
4. **Emergence**: New insights emerge from link patterns

### Research Reference
- Paper: "A-MEM: Agentic Memory for LLM Agents"
- Key insight: Linking memories creates emergent knowledge graphs

---

## Current State: Thermal Memory

Our `thermal_memory_archive` table on bluefin:

```sql
-- Current schema (simplified)
CREATE TABLE thermal_memory_archive (
    memory_id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type VARCHAR(50),
    source_context VARCHAR(100),
    temperature FLOAT DEFAULT 37.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

**Current capabilities:**
- Temperature-based relevance (hotter = more relevant)
- Access counting
- Metadata storage
- ~5,200+ memories archived

**Missing (A-MEM will add):**
- Bidirectional linking between memories
- Progressive summarization
- Atomic note enforcement
- Link-based discovery

---

## Implementation Plan

### Phase 1: Schema Enhancement

Add linking infrastructure to thermal memory:

```sql
-- New table for memory links (bidirectional)
CREATE TABLE thermal_memory_links (
    link_id SERIAL PRIMARY KEY,
    source_memory_id INTEGER REFERENCES thermal_memory_archive(memory_id),
    target_memory_id INTEGER REFERENCES thermal_memory_archive(memory_id),
    link_type VARCHAR(50) DEFAULT 'related',  -- 'related', 'supports', 'contradicts', 'extends'
    link_strength FLOAT DEFAULT 0.5,          -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),                  -- Which agent/process created the link
    UNIQUE(source_memory_id, target_memory_id)
);

-- Index for fast link traversal
CREATE INDEX idx_memory_links_source ON thermal_memory_links(source_memory_id);
CREATE INDEX idx_memory_links_target ON thermal_memory_links(target_memory_id);
CREATE INDEX idx_memory_links_type ON thermal_memory_links(link_type);

-- Add summary field to existing table
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS summary_updated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS atomic_score FLOAT DEFAULT 0.5;  -- How "atomic" (single-concept) the memory is
```

### Phase 2: Link Discovery Service

Create a service that automatically discovers and creates links:

```python
# /ganuda/lib/amem_linker.py

import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np

class AMEMLinker:
    """
    A-MEM Link Discovery Service

    Analyzes memories and creates bidirectional links based on:
    1. Semantic similarity (embedding distance)
    2. Keyword overlap
    3. Temporal proximity
    4. Source context matching
    """

    def __init__(self, db_config: dict, similarity_threshold: float = 0.7):
        self.db_config = db_config
        self.similarity_threshold = similarity_threshold
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality

    def find_related_memories(self, memory_id: int, limit: int = 10) -> list:
        """Find memories related to the given memory"""
        with psycopg2.connect(**self.db_config) as conn:
            cur = conn.cursor()

            # Get source memory
            cur.execute(
                "SELECT content, metadata FROM thermal_memory_archive WHERE memory_id = %s",
                (memory_id,)
            )
            source = cur.fetchone()
            if not source:
                return []

            source_content, source_meta = source
            source_embedding = self.model.encode(source_content)

            # Get candidate memories (exclude self, recently linked)
            cur.execute("""
                SELECT memory_id, content
                FROM thermal_memory_archive
                WHERE memory_id != %s
                AND memory_id NOT IN (
                    SELECT target_memory_id FROM thermal_memory_links
                    WHERE source_memory_id = %s
                )
                ORDER BY temperature DESC, access_count DESC
                LIMIT 100
            """, (memory_id, memory_id))

            candidates = cur.fetchall()

            # Score candidates by similarity
            results = []
            for cand_id, cand_content in candidates:
                cand_embedding = self.model.encode(cand_content)
                similarity = np.dot(source_embedding, cand_embedding) / (
                    np.linalg.norm(source_embedding) * np.linalg.norm(cand_embedding)
                )

                if similarity >= self.similarity_threshold:
                    results.append({
                        'memory_id': cand_id,
                        'similarity': float(similarity),
                        'preview': cand_content[:100]
                    })

            # Sort by similarity, return top matches
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

    def create_link(self, source_id: int, target_id: int,
                    link_type: str = 'related', strength: float = 0.5,
                    created_by: str = 'amem_linker') -> bool:
        """Create bidirectional link between memories"""
        with psycopg2.connect(**self.db_config) as conn:
            cur = conn.cursor()

            # Insert forward link
            cur.execute("""
                INSERT INTO thermal_memory_links
                (source_memory_id, target_memory_id, link_type, link_strength, created_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_memory_id, target_memory_id) DO UPDATE
                SET link_strength = GREATEST(thermal_memory_links.link_strength, EXCLUDED.link_strength)
            """, (source_id, target_id, link_type, strength, created_by))

            # Insert reverse link (bidirectional)
            cur.execute("""
                INSERT INTO thermal_memory_links
                (source_memory_id, target_memory_id, link_type, link_strength, created_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_memory_id, target_memory_id) DO UPDATE
                SET link_strength = GREATEST(thermal_memory_links.link_strength, EXCLUDED.link_strength)
            """, (target_id, source_id, link_type, strength, created_by))

            conn.commit()
            return True

    def get_memory_graph(self, memory_id: int, depth: int = 2) -> dict:
        """Get the knowledge graph around a memory (for visualization)"""
        with psycopg2.connect(**self.db_config) as conn:
            cur = conn.cursor()

            visited = set()
            nodes = []
            edges = []

            def traverse(mid: int, current_depth: int):
                if mid in visited or current_depth > depth:
                    return
                visited.add(mid)

                # Get memory info
                cur.execute(
                    "SELECT content, temperature, memory_type FROM thermal_memory_archive WHERE memory_id = %s",
                    (mid,)
                )
                row = cur.fetchone()
                if row:
                    nodes.append({
                        'id': mid,
                        'label': row[0][:50],
                        'temperature': row[1],
                        'type': row[2]
                    })

                # Get links
                cur.execute("""
                    SELECT target_memory_id, link_type, link_strength
                    FROM thermal_memory_links
                    WHERE source_memory_id = %s
                """, (mid,))

                for target_id, link_type, strength in cur.fetchall():
                    edges.append({
                        'source': mid,
                        'target': target_id,
                        'type': link_type,
                        'strength': strength
                    })
                    traverse(target_id, current_depth + 1)

            traverse(memory_id, 0)
            return {'nodes': nodes, 'edges': edges}
```

### Phase 3: Progressive Summarization

Add automatic summarization for frequently accessed memories:

```python
# /ganuda/lib/amem_summarizer.py

class AMEMSummarizer:
    """
    Progressive Summarization Service

    When a memory is accessed frequently (high temperature + access_count),
    generate a condensed summary for faster retrieval.
    """

    SUMMARY_THRESHOLD_ACCESS = 10    # Summarize after 10 accesses
    SUMMARY_THRESHOLD_TEMP = 50.0    # Or when temperature exceeds 50

    def should_summarize(self, memory: dict) -> bool:
        """Check if memory needs summarization"""
        if memory.get('summary'):
            # Already has summary, check if stale
            return False

        return (
            memory.get('access_count', 0) >= self.SUMMARY_THRESHOLD_ACCESS or
            memory.get('temperature', 37.0) >= self.SUMMARY_THRESHOLD_TEMP
        )

    async def generate_summary(self, content: str, llm_client) -> str:
        """Generate a condensed summary using LLM"""
        prompt = f"""Summarize this knowledge in 1-2 sentences, preserving key facts:

{content}

Summary:"""

        response = await llm_client.complete(prompt, max_tokens=100)
        return response.strip()

    def update_summary(self, memory_id: int, summary: str, db_config: dict):
        """Store the generated summary"""
        with psycopg2.connect(**db_config) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE thermal_memory_archive
                SET summary = %s, summary_updated_at = NOW()
                WHERE memory_id = %s
            """, (summary, memory_id))
            conn.commit()
```

### Phase 4: Daemon Integration

Create a background daemon that continuously links and summarizes:

```python
# /ganuda/daemons/amem_daemon.py

"""
A-MEM Background Daemon

Runs continuously to:
1. Discover and create links between new memories
2. Generate summaries for hot memories
3. Prune weak links over time
"""

import asyncio
import time

async def amem_daemon_loop(config: dict):
    linker = AMEMLinker(config['db'])
    summarizer = AMEMSummarizer()

    while True:
        try:
            # Get recent unlinked memories
            memories = get_unlinked_memories(config['db'], limit=50)

            for memory in memories:
                # Find and create links
                related = linker.find_related_memories(memory['memory_id'])
                for rel in related[:5]:  # Link to top 5 matches
                    linker.create_link(
                        memory['memory_id'],
                        rel['memory_id'],
                        link_type='related',
                        strength=rel['similarity']
                    )

                # Check if needs summarization
                if summarizer.should_summarize(memory):
                    summary = await summarizer.generate_summary(
                        memory['content'],
                        config['llm_client']
                    )
                    summarizer.update_summary(memory['memory_id'], summary, config['db'])

            # Sleep between cycles (5 minutes)
            await asyncio.sleep(300)

        except Exception as e:
            print(f"[AMEM DAEMON ERROR] {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(amem_daemon_loop(load_config()))
```

---

## Performance Considerations (Gecko's Concern)

### Memory Usage Mitigation

1. **Lazy Loading**: Only load links when traversing, not on every query
2. **Link Pruning**: Remove weak links (strength < 0.3) after 30 days
3. **Summary Caching**: Cache summaries in Redis for fast access
4. **Batch Processing**: Process link discovery in batches during off-peak

### Monitoring Metrics

Add to Grafana dashboard:
- `amem_links_total` - Total link count
- `amem_links_created_rate` - Links created per hour
- `amem_summaries_total` - Memories with summaries
- `amem_graph_depth_avg` - Average graph traversal depth
- `amem_memory_usage_mb` - Memory consumed by link index

---

## Validation Checklist

- [ ] `thermal_memory_links` table created
- [ ] `summary` column added to `thermal_memory_archive`
- [ ] AMEMLinker service working
- [ ] AMEMSummarizer service working
- [ ] Background daemon running
- [ ] Performance metrics in Grafana
- [ ] Link pruning cron job configured
- [ ] Council re-review after implementation

---

## Integration Points

### LLM Gateway Enhancement

Update `/v1/council/vote` to include linked memories in context:

```python
# In gateway.py council_vote endpoint
related_memories = amem_linker.get_memory_graph(memory_id, depth=2)
context += format_memory_graph(related_memories)
```

### Thermal Memory Query Enhancement

Update memory retrieval to follow links:

```python
def get_memories_with_links(query: str, limit: int = 10) -> list:
    """Get memories plus their linked context"""
    base_memories = search_thermal_memory(query, limit=limit)

    enhanced = []
    for memory in base_memories:
        memory['linked'] = amem_linker.find_related_memories(
            memory['memory_id'], limit=3
        )
        enhanced.append(memory)

    return enhanced
```

---

## Timeline

| Phase | Target | Deliverable |
|-------|--------|-------------|
| Phase 1 | Week 1 | Schema changes deployed |
| Phase 2 | Week 2-3 | Link discovery service |
| Phase 3 | Week 3-4 | Summarization service |
| Phase 4 | Week 4-5 | Daemon + monitoring |
| Review | Week 6 | Council performance review |

---

## References

- A-MEM Paper: "Agentic Memory for LLM Agents"
- Zettelkasten Method: https://zettelkasten.de/
- Council Vote: `6700b2d88464ab8b` (January 16, 2026)

---

*Cherokee AI Federation - For the Seven Generations*
*"Knowledge linked is wisdom multiplied."*
