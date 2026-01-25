# Jr Task: Implement A-MEM Zettelkasten Linking for Thermal Memory

**Task ID:** task-impl-amem-001
**Priority:** P1 (Phase 3.1 - Parallel Track A)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** arXiv:2502.12110 - A-MEM: Agentic Memory for LLM Agents

---

## Overview

Enhance the thermal_memory_archive with Zettelkasten-style interconnected knowledge networks. This transforms our flat memory store into a graph-based system where memories link to related memories, enabling richer context retrieval and memory evolution.

**Seven Generations Alignment:** Knowledge preservation across generations through interconnected memory networks.

---

## Research Paper Summary

A-MEM creates "agentic memory" that dynamically organizes memories following the Zettelkasten method:
- Each memory note contains structured attributes (keywords, tags, contextual description)
- Memories automatically link to semantically related memories
- New memories trigger updates to existing memory representations
- Linear space complexity O(N) with fast retrieval (0.31μs to 3.70μs from 1K to 1M)

---

## Implementation Tasks

### Task 1: Extend thermal_memory_archive Schema

Add new columns for A-MEM attributes:

```sql
-- Add A-MEM columns to thermal_memory_archive
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS keywords TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS contextual_description TEXT,
ADD COLUMN IF NOT EXISTS embedding_vector FLOAT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS linked_memories TEXT[] DEFAULT '{}';

-- Create index for keyword/tag searching
CREATE INDEX IF NOT EXISTS idx_thermal_keywords ON thermal_memory_archive USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_thermal_tags ON thermal_memory_archive USING GIN(tags);

-- Create memory_links table for bidirectional relationships
CREATE TABLE IF NOT EXISTS memory_links (
    link_id SERIAL PRIMARY KEY,
    source_hash VARCHAR(64) NOT NULL,
    target_hash VARCHAR(64) NOT NULL,
    link_type VARCHAR(32) DEFAULT 'semantic',  -- 'semantic', 'causal', 'temporal', 'conceptual'
    similarity_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(64),  -- agent that created the link
    UNIQUE(source_hash, target_hash)
);

CREATE INDEX IF NOT EXISTS idx_memory_links_source ON memory_links(source_hash);
CREATE INDEX IF NOT EXISTS idx_memory_links_target ON memory_links(target_hash);
```

### Task 2: Create Memory Note Constructor

**File:** `/ganuda/lib/amem_memory.py`

```python
#!/usr/bin/env python3
"""
A-MEM Memory System for Cherokee AI Federation
Based on arXiv:2502.12110 - Agentic Memory for LLM Agents

Implements Zettelkasten-style memory linking for thermal_memory_archive.
"""

import psycopg2
import psycopg2.extras
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Initialize embedding model (lightweight, runs on CPU)
# all-MiniLM-L6-v2: 384 dimensions, fast inference
EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load embedding model."""
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return EMBEDDING_MODEL

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from content using simple TF-based extraction.

    For production, could use LLM-based extraction via gateway.
    """
    import re
    from collections import Counter

    # Simple keyword extraction (stopword removal + frequency)
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'between', 'under', 'again', 'further',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                 'because', 'until', 'while', 'this', 'that', 'these', 'those'}

    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content.lower())
    words = [w for w in words if w not in stopwords and len(w) > 2]

    # Get most common
    counter = Counter(words)
    return [word for word, _ in counter.most_common(max_keywords)]


def extract_tags(content: str) -> List[str]:
    """
    Extract category tags based on content patterns.

    Cherokee AI specific categories.
    """
    tags = []
    content_lower = content.lower()

    # Node tags
    if any(node in content_lower for node in ['redfin', 'bluefin', 'greenfin', 'sasass', 'bmasass']):
        tags.append('infrastructure')

    # Service tags
    if 'telegram' in content_lower:
        tags.append('telegram')
    if 'gateway' in content_lower or 'llm' in content_lower:
        tags.append('llm_gateway')
    if 'thermal' in content_lower or 'memory' in content_lower:
        tags.append('thermal_memory')
    if 'jr' in content_lower or 'agent' in content_lower:
        tags.append('jr_agents')
    if 'council' in content_lower:
        tags.append('council')

    # Event tags
    if 'error' in content_lower or 'fail' in content_lower:
        tags.append('error')
    if 'success' in content_lower or 'complete' in content_lower:
        tags.append('success')
    if 'deploy' in content_lower:
        tags.append('deployment')
    if 'task' in content_lower:
        tags.append('task')

    # Knowledge tags
    if 'research' in content_lower or 'arxiv' in content_lower:
        tags.append('research')
    if 'plan' in content_lower or 'roadmap' in content_lower:
        tags.append('planning')

    return list(set(tags)) or ['general']


def generate_contextual_description(content: str, keywords: List[str]) -> str:
    """
    Generate a contextual description summarizing the memory.

    Simple extraction for now - could use LLM for richer descriptions.
    """
    # Take first 200 chars as summary
    summary = content[:200].strip()
    if len(content) > 200:
        summary += "..."

    keyword_str = ", ".join(keywords[:5]) if keywords else "general"

    return f"Memory about {keyword_str}. {summary}"


def compute_embedding(text: str) -> List[float]:
    """Compute embedding vector for text."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def find_similar_memories(embedding: List[float],
                          limit: int = 5,
                          exclude_hash: str = None) -> List[Tuple[str, float]]:
    """
    Find memories with similar embeddings using cosine similarity.

    Returns list of (memory_hash, similarity_score) tuples.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        # Get all memories with embeddings
        cur.execute("""
            SELECT memory_hash, embedding_vector
            FROM thermal_memory_archive
            WHERE embedding_vector IS NOT NULL
            AND array_length(embedding_vector, 1) > 0
            AND memory_hash != COALESCE(%s, '')
        """, (exclude_hash,))

        candidates = cur.fetchall()

    conn.close()

    if not candidates:
        return []

    # Compute cosine similarities
    import numpy as np
    query_vec = np.array(embedding)

    similarities = []
    for mem_hash, mem_embedding in candidates:
        if mem_embedding:
            candidate_vec = np.array(mem_embedding)
            # Cosine similarity (vectors are normalized)
            sim = np.dot(query_vec, candidate_vec)
            if sim > 0.5:  # Threshold for relevance
                similarities.append((mem_hash, float(sim)))

    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:limit]


def create_memory_links(source_hash: str,
                        similar_memories: List[Tuple[str, float]],
                        agent_id: str = 'amem_system') -> int:
    """
    Create bidirectional links between memories.

    Returns number of links created.
    """
    if not similar_memories:
        return 0

    conn = get_connection()
    links_created = 0

    with conn.cursor() as cur:
        for target_hash, similarity in similar_memories:
            # Create link in both directions
            try:
                cur.execute("""
                    INSERT INTO memory_links (source_hash, target_hash, similarity_score, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_hash, target_hash) DO UPDATE
                    SET similarity_score = EXCLUDED.similarity_score
                """, (source_hash, target_hash, similarity, agent_id))

                cur.execute("""
                    INSERT INTO memory_links (source_hash, target_hash, similarity_score, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_hash, target_hash) DO NOTHING
                """, (target_hash, source_hash, similarity, agent_id))

                links_created += 1
            except Exception as e:
                print(f"Link creation error: {e}")

        # Update linked_memories arrays
        cur.execute("""
            UPDATE thermal_memory_archive
            SET linked_memories = (
                SELECT ARRAY_AGG(target_hash)
                FROM memory_links
                WHERE source_hash = %s
            )
            WHERE memory_hash = %s
        """, (source_hash, source_hash))

        conn.commit()

    conn.close()
    return links_created


def enrich_memory(memory_hash: str, content: str, agent_id: str = 'amem_system') -> Dict:
    """
    Enrich an existing memory with A-MEM attributes.

    Main function to call for processing memories.
    """
    # Extract attributes
    keywords = extract_keywords(content)
    tags = extract_tags(content)
    context_desc = generate_contextual_description(content, keywords)
    embedding = compute_embedding(content)

    # Find similar memories and create links
    similar = find_similar_memories(embedding, limit=5, exclude_hash=memory_hash)

    conn = get_connection()

    with conn.cursor() as cur:
        # Update memory with A-MEM attributes
        cur.execute("""
            UPDATE thermal_memory_archive
            SET keywords = %s,
                tags = %s,
                contextual_description = %s,
                embedding_vector = %s
            WHERE memory_hash = %s
        """, (keywords, tags, context_desc, embedding, memory_hash))

        conn.commit()

    conn.close()

    # Create links
    links_created = create_memory_links(memory_hash, similar, agent_id)

    return {
        'memory_hash': memory_hash,
        'keywords': keywords,
        'tags': tags,
        'contextual_description': context_desc,
        'similar_memories': len(similar),
        'links_created': links_created
    }


def get_linked_context(memory_hash: str, depth: int = 1) -> List[Dict]:
    """
    Get linked memories for context enrichment.

    depth: How many hops to follow (1 = direct links, 2 = links of links)
    """
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if depth == 1:
            cur.execute("""
                SELECT t.memory_hash, t.original_content, t.temperature_score,
                       t.keywords, t.tags, l.similarity_score
                FROM thermal_memory_archive t
                JOIN memory_links l ON t.memory_hash = l.target_hash
                WHERE l.source_hash = %s
                ORDER BY l.similarity_score DESC
                LIMIT 5
            """, (memory_hash,))
        else:
            # Two-hop query for deeper context
            cur.execute("""
                WITH RECURSIVE linked AS (
                    SELECT target_hash, 1 as depth, similarity_score
                    FROM memory_links WHERE source_hash = %s
                    UNION
                    SELECT l.target_hash, linked.depth + 1, l.similarity_score
                    FROM memory_links l
                    JOIN linked ON l.source_hash = linked.target_hash
                    WHERE linked.depth < %s
                )
                SELECT DISTINCT t.memory_hash, t.original_content, t.temperature_score,
                       t.keywords, t.tags, linked.similarity_score, linked.depth
                FROM thermal_memory_archive t
                JOIN linked ON t.memory_hash = linked.target_hash
                ORDER BY linked.depth, linked.similarity_score DESC
                LIMIT 10
            """, (memory_hash, depth))

        results = cur.fetchall()

    conn.close()
    return [dict(r) for r in results]


def backfill_existing_memories(batch_size: int = 100, agent_id: str = 'amem_backfill') -> Dict:
    """
    Backfill A-MEM attributes for existing memories.

    Run as batch job to process historical memories.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        # Find memories without embeddings
        cur.execute("""
            SELECT memory_hash, original_content
            FROM thermal_memory_archive
            WHERE embedding_vector IS NULL OR array_length(embedding_vector, 1) IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """, (batch_size,))

        memories = cur.fetchall()

    conn.close()

    processed = 0
    errors = 0

    for memory_hash, content in memories:
        try:
            enrich_memory(memory_hash, content, agent_id)
            processed += 1
        except Exception as e:
            print(f"Error processing {memory_hash}: {e}")
            errors += 1

    return {
        'processed': processed,
        'errors': errors,
        'remaining': len(memories) == batch_size  # More to process if we hit limit
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'backfill':
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        result = backfill_existing_memories(batch_size)
        print(f"Backfill result: {result}")
    else:
        print("A-MEM Memory System")
        print("Usage: python amem_memory.py backfill [batch_size]")
```

### Task 3: Integrate with Memory Creation

Update thermal memory insertion to auto-enrich:

```python
# Add to existing thermal memory creation code
from lib.amem_memory import enrich_memory

def store_thermal_memory(content: str, temperature: float, metadata: dict = None):
    """Store memory with A-MEM enrichment."""

    # Existing storage logic...
    memory_hash = create_memory_hash(content)

    # Insert base memory
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (memory_hash) DO UPDATE
            SET temperature_score = EXCLUDED.temperature_score
            RETURNING memory_hash
        """, (memory_hash, content, temperature, Json(metadata or {})))
        conn.commit()
    conn.close()

    # Enrich with A-MEM attributes (async if needed)
    try:
        enrich_result = enrich_memory(memory_hash, content)
        return {'hash': memory_hash, 'enrichment': enrich_result}
    except Exception as e:
        # Don't fail if enrichment fails
        return {'hash': memory_hash, 'enrichment_error': str(e)}
```

---

## Deployment Steps

1. Run SQL schema changes on bluefin
2. Install sentence-transformers: `pip install sentence-transformers`
3. Create `/ganuda/lib/amem_memory.py`
4. Run backfill for existing memories: `python amem_memory.py backfill 500`
5. Integrate with thermal memory creation pipeline
6. Monitor link creation and retrieval performance

---

## Dependencies

```
sentence-transformers>=2.2.0
numpy>=1.21.0
psycopg2-binary>=2.9.0
```

---

## Success Criteria

- [ ] thermal_memory_archive has keywords, tags, embedding_vector columns
- [ ] memory_links table created with bidirectional relationships
- [ ] enrich_memory() creates 3-5 links per new memory
- [ ] get_linked_context() returns related memories for retrieval
- [ ] Backfill processes 1000+ existing memories
- [ ] Retrieval latency < 10ms for linked context

---

## Seven Generations Impact

This enhancement preserves knowledge relationships across time. When future agents query thermal memory, they receive not just the direct match but the interconnected knowledge network - context that would otherwise be lost. The Zettelkasten method has preserved human knowledge for centuries; we adapt it for AI memory.

---

*For Seven Generations - Cherokee AI Federation*
