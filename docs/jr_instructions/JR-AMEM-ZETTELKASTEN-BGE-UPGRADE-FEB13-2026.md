# Jr Instruction: A-MEM Zettelkasten — Upgrade to BGE-large Embeddings

**Task**: Fix amem_memory.py to use BGE-large (1024d) via greenfin API instead of local MiniLM (384d)
**Council Vote**: #33e50dc466de520e (RC-2026-02C, unanimous 7/7)
**Kanban**: #1704
**Priority**: 1 (P0 — council unanimous pick, 70 points)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 13

## Context

`amem_memory.py` currently loads `all-MiniLM-L6-v2` locally (384 dimensions) for embeddings and does a FULL TABLE SCAN in Python to find similar memories. This is wrong because:

1. Production uses BGE-large-en-v1.5 (1024d) on greenfin:8003 — the embedding service that backed Phase 1 RAG
2. The `embedding` column (vector(1024)) has 79,472 entries indexed with IVFFlat — fast pgvector search
3. The `embedding_vector` column (ARRAY, MiniLM 384d) has 80,855 entries but is NOT indexed for vector search
4. `find_similar_memories()` fetches ALL rows and computes cosine in numpy — O(n) scan on 80K+ rows

Fix: Use greenfin:8003 API for embeddings, pgvector `<=>` operator for similarity, drop the local model dependency.

## Step 1: Switch embedding to greenfin BGE-large API

File: `/ganuda/lib/amem_memory.py`

<<<<<<< SEARCH
import psycopg2
import psycopg2.extras
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

# Initialize embedding model (lightweight, runs on CPU)
EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load embedding model."""
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return EMBEDDING_MODEL
=======
import logging
import os
import psycopg2
import psycopg2.extras
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import requests

from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

logger = logging.getLogger(__name__)

EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/embed")
>>>>>>> REPLACE

## Step 2: Replace local compute_embedding with API call

File: `/ganuda/lib/amem_memory.py`

<<<<<<< SEARCH
def compute_embedding(text: str) -> List[float]:
    """Compute embedding vector for text."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
=======
def compute_embedding(text: str) -> List[float]:
    """Get BGE-large 1024d embedding from greenfin embedding service."""
    try:
        resp = requests.post(EMBEDDING_URL, json={"text": text}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return data["embedding"]
        elif "embeddings" in data:
            return data["embeddings"][0] if data["embeddings"] else []
        return []
    except Exception as e:
        logger.warning("Embedding service error: %s", e)
        return []
>>>>>>> REPLACE

## Step 3: Replace full-table-scan similarity with pgvector

File: `/ganuda/lib/amem_memory.py`

<<<<<<< SEARCH
def find_similar_memories(embedding: List[float], limit: int = 5, exclude_hash: str = None) -> List[Tuple[str, float]]:
    """Find memories with similar embeddings using cosine similarity."""
    import numpy as np
    conn = get_connection()

    with conn.cursor() as cur:
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

    query_vec = np.array(embedding)
    similarities = []
    for mem_hash, mem_embedding in candidates:
        if mem_embedding:
            candidate_vec = np.array(mem_embedding)
            sim = np.dot(query_vec, candidate_vec)
            if sim > 0.5:
                similarities.append((mem_hash, float(sim)))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:limit]
=======
def find_similar_memories(embedding: List[float], limit: int = 5, exclude_hash: str = None) -> List[Tuple[str, float]]:
    """Find similar memories using pgvector cosine distance on BGE-large embeddings."""
    if not embedding:
        return []

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash,
                       1 - (embedding <=> %s::vector) as similarity
                FROM thermal_memory_archive
                WHERE embedding IS NOT NULL
                AND memory_hash != COALESCE(%s, '')
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding, exclude_hash, embedding, limit))
            results = [(row[0], float(row[1])) for row in cur.fetchall() if row[1] > 0.5]
        return results
    except Exception as e:
        logger.error("pgvector similarity search failed: %s", e)
        return []
    finally:
        conn.close()
>>>>>>> REPLACE

## Step 4: Fix enrich_memory to write to `embedding` column (not embedding_vector)

File: `/ganuda/lib/amem_memory.py`

<<<<<<< SEARCH
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE thermal_memory_archive
            SET keywords = %s, tags = %s, contextual_description = %s, embedding_vector = %s
            WHERE memory_hash = %s
        """, (keywords, tags, context_desc, embedding, memory_hash))
        conn.commit()
    conn.close()
=======
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE thermal_memory_archive
            SET keywords = %s, tags = %s, contextual_description = %s,
                embedding = %s::vector
            WHERE memory_hash = %s
        """, (keywords, tags, context_desc, embedding, memory_hash))
        conn.commit()
    conn.close()
>>>>>>> REPLACE

## Step 5: Fix backfill to target memories without contextual_description

File: `/ganuda/lib/amem_memory.py`

<<<<<<< SEARCH
    with conn.cursor() as cur:
        cur.execute("""
            SELECT memory_hash, original_content
            FROM thermal_memory_archive
            WHERE embedding_vector IS NULL OR array_length(embedding_vector, 1) IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """, (batch_size,))
        memories = cur.fetchall()
=======
    with conn.cursor() as cur:
        cur.execute("""
            SELECT memory_hash, original_content
            FROM thermal_memory_archive
            WHERE contextual_description IS NULL
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (batch_size,))
        memories = cur.fetchall()
>>>>>>> REPLACE

## Manual Steps

After patching, verify on redfin:

```text
cd /ganuda && python3 -c "
from lib.amem_memory import compute_embedding, find_similar_memories
emb = compute_embedding('power outage recovery')
print(f'Embedding dims: {len(emb)}')
similar = find_similar_memories(emb, limit=3)
print(f'Similar memories: {similar}')
"
```

Expected: Embedding dims = 1024, and similar memories returned in <100ms (pgvector indexed).

Then run backfill for contextual descriptions (batches of 500, hottest memories first):

```text
cd /ganuda && python3 -c "from lib.amem_memory import backfill_existing_memories; print(backfill_existing_memories(500))"
```

## Success Criteria

- [ ] `compute_embedding()` returns 1024d vector from greenfin:8003
- [ ] `find_similar_memories()` uses pgvector `<=>` operator (no full table scan)
- [ ] `enrich_memory()` writes to `embedding` column (vector(1024)), not `embedding_vector`
- [ ] Backfill targets memories without `contextual_description` (80,126 remaining)
- [ ] No `sentence-transformers` import anywhere in amem_memory.py

---

*For Seven Generations - Cherokee AI Federation*
