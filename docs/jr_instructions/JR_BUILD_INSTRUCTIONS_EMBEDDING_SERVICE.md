# Jr Build Instructions: Embedding Service

## Priority: HIGH - Enables Semantic Search & RAG

---

## Overview

Deploy an embedding service for Cherokee AI to enable:
1. **Semantic search** in thermal memory
2. **RAG** (Retrieval Augmented Generation) for Council
3. **Similar issue detection** in SAG
4. **Knowledge base search**

---

## Current State

| Component | Status |
|-----------|--------|
| Embedding models | Cached (BGE-large, MiniLM) |
| pgvector extension | NOT installed |
| Vector columns | NOT created |
| Embedding API | NOT implemented |

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   LLM Gateway   │────▶│ Embedding Service│────▶│   PostgreSQL    │
│   (port 8080)   │     │   (port 8003)    │     │   + pgvector    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  BGE-large-en   │
                        │  (1024 dims)    │
                        └─────────────────┘
```

---

## Phase 1: PostgreSQL pgvector Extension

### On bluefin (192.168.132.222):

```bash
# Install pgvector
sudo apt-get update
sudo apt-get install postgresql-16-pgvector

# Or compile from source if package not available
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Enable Extension:

```sql
-- Connect to zammad_production
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## Phase 2: Database Schema

### Add Vector Column to Thermal Memory:

```sql
-- Add embedding column to thermal_memory_archive
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Create index for similarity search
CREATE INDEX IF NOT EXISTS idx_thermal_embedding
ON thermal_memory_archive
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add embedding column to decision_reflections (for metacognition)
ALTER TABLE decision_reflections
ADD COLUMN IF NOT EXISTS query_embedding vector(1024);
```

### Create Embedding Cache Table:

```sql
CREATE TABLE IF NOT EXISTS embedding_cache (
    id SERIAL PRIMARY KEY,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    content_preview VARCHAR(500),
    embedding vector(1024) NOT NULL,
    model_name VARCHAR(100) DEFAULT 'BAAI/bge-large-en-v1.5',
    created_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embedding_cache_hash ON embedding_cache(content_hash);
CREATE INDEX idx_embedding_cache_vector ON embedding_cache
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## Phase 3: Embedding Service

### Create `/ganuda/services/embedding_service/embedding_server.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Embedding Service
Provides vector embeddings for semantic search and RAG
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from sentence_transformers import SentenceTransformer
import time

app = FastAPI(title="Cherokee AI Embedding Service", version="1.0.0")

# Load model at startup
MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM = 1024

print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print(f"Model loaded. Dimension: {EMBEDDING_DIM}")

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


class EmbedRequest(BaseModel):
    texts: List[str]
    cache: bool = True


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimensions: int
    cached_count: int
    computed_count: int
    latency_ms: int


class SearchRequest(BaseModel):
    query: str
    table: str = "thermal_memory_archive"
    column: str = "original_content"
    embedding_column: str = "embedding"
    limit: int = 10
    threshold: float = 0.7


class SearchResult(BaseModel):
    id: int
    content: str
    similarity: float
    metadata: Optional[dict] = None


def get_db():
    return psycopg2.connect(**DB_CONFIG)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_cached_embedding(conn, hash_val: str) -> Optional[List[float]]:
    """Check cache for existing embedding"""
    cur = conn.cursor()
    cur.execute("""
        SELECT embedding FROM embedding_cache
        WHERE content_hash = %s
    """, (hash_val,))
    result = cur.fetchone()
    if result:
        # Update access stats
        cur.execute("""
            UPDATE embedding_cache
            SET access_count = access_count + 1, last_accessed = NOW()
            WHERE content_hash = %s
        """, (hash_val,))
        conn.commit()
        return list(result[0])
    return None


def cache_embedding(conn, hash_val: str, text: str, embedding: List[float]):
    """Store embedding in cache"""
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO embedding_cache (content_hash, content_preview, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (content_hash) DO NOTHING
        """, (hash_val, text[:500], embedding))
        conn.commit()
    except Exception as e:
        print(f"Cache insert error: {e}")
        conn.rollback()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "dimensions": EMBEDDING_DIM
    }


@app.post("/v1/embeddings", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest):
    """Generate embeddings for texts"""
    start = time.time()

    embeddings = []
    cached_count = 0
    computed_count = 0

    conn = get_db() if request.cache else None

    try:
        for text in request.texts:
            hash_val = content_hash(text)

            # Check cache
            if request.cache and conn:
                cached = get_cached_embedding(conn, hash_val)
                if cached:
                    embeddings.append(cached)
                    cached_count += 1
                    continue

            # Compute embedding
            embedding = model.encode(text, normalize_embeddings=True).tolist()
            embeddings.append(embedding)
            computed_count += 1

            # Cache result
            if request.cache and conn:
                cache_embedding(conn, hash_val, text, embedding)

    finally:
        if conn:
            conn.close()

    return EmbedResponse(
        embeddings=embeddings,
        model=MODEL_NAME,
        dimensions=EMBEDDING_DIM,
        cached_count=cached_count,
        computed_count=computed_count,
        latency_ms=int((time.time() - start) * 1000)
    )


@app.post("/v1/search", response_model=List[SearchResult])
async def semantic_search(request: SearchRequest):
    """Semantic search using vector similarity"""

    # Get query embedding
    query_embedding = model.encode(request.query, normalize_embeddings=True).tolist()

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Semantic search query
        cur.execute(f"""
            SELECT
                id,
                {request.column} as content,
                1 - ({request.embedding_column} <=> %s::vector) as similarity,
                metadata
            FROM {request.table}
            WHERE {request.embedding_column} IS NOT NULL
            AND 1 - ({request.embedding_column} <=> %s::vector) > %s
            ORDER BY {request.embedding_column} <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, request.threshold, query_embedding, request.limit))

        results = cur.fetchall()

        return [
            SearchResult(
                id=r['id'],
                content=r['content'][:1000] if r['content'] else '',
                similarity=float(r['similarity']),
                metadata=r.get('metadata')
            )
            for r in results
        ]

    finally:
        cur.close()
        conn.close()


@app.post("/v1/index")
async def index_table(table: str = "thermal_memory_archive",
                      content_column: str = "original_content",
                      embedding_column: str = "embedding",
                      batch_size: int = 100):
    """Backfill embeddings for existing records"""

    conn = get_db()
    cur = conn.cursor()

    # Count records needing embedding
    cur.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE {embedding_column} IS NULL
    """)
    total = cur.fetchone()[0]

    if total == 0:
        return {"message": "All records already have embeddings", "indexed": 0}

    indexed = 0

    while indexed < total:
        # Get batch
        cur.execute(f"""
            SELECT id, {content_column} FROM {table}
            WHERE {embedding_column} IS NULL
            LIMIT %s
        """, (batch_size,))

        batch = cur.fetchall()
        if not batch:
            break

        # Generate embeddings
        texts = [row[1] or '' for row in batch]
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        # Update records
        for (record_id, _), embedding in zip(batch, embeddings):
            cur.execute(f"""
                UPDATE {table}
                SET {embedding_column} = %s
                WHERE id = %s
            """, (embedding.tolist(), record_id))

        conn.commit()
        indexed += len(batch)
        print(f"Indexed {indexed}/{total} records")

    cur.close()
    conn.close()

    return {"message": f"Indexed {indexed} records", "indexed": indexed}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Cherokee AI Embedding Service")
    print(f"Model: {MODEL_NAME}")
    print(f"Dimensions: {EMBEDDING_DIM}")
    print("Endpoints: /health, /v1/embeddings, /v1/search, /v1/index")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

---

## Phase 4: Systemd Service

### Create `/etc/systemd/system/embedding.service`:

```ini
[Unit]
Description=Cherokee AI Embedding Service
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/embedding_service
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
ExecStart=/home/dereadi/cherokee_venv/bin/python embedding_server.py
Restart=always
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

---

## Phase 5: Gateway Integration

### Add to LLM Gateway `/v1/embeddings` proxy:

```python
# In gateway.py

EMBEDDING_BACKEND = "http://localhost:8002"

@app.post("/v1/embeddings")
async def proxy_embeddings(request: Request, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Proxy to embedding service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMBEDDING_BACKEND}/v1/embeddings",
            json=body,
            timeout=60.0
        )
        return response.json()
```

---

## Phase 6: Thermal Memory Enhancement

### Update thermal memory to use embeddings:

```python
# In thermal memory archival code

async def archive_memory(content: str, metadata: dict):
    """Archive memory with embedding"""

    # Get embedding
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8002/v1/embeddings",
            json={"texts": [content]}
        )
        embedding = resp.json()["embeddings"][0]

    # Store with embedding
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, embedding, metadata, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """, (
        hashlib.sha256(content.encode()).hexdigest(),
        content,
        embedding,
        json.dumps(metadata)
    ))
    conn.commit()


async def search_memories(query: str, limit: int = 10):
    """Semantic search in thermal memory"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8002/v1/search",
            json={
                "query": query,
                "table": "thermal_memory_archive",
                "limit": limit,
                "threshold": 0.6
            }
        )
        return resp.json()
```

---

## Phase 7: Backfill Existing Data

After service is running:

```bash
# Backfill thermal memory embeddings
curl -X POST "http://localhost:8002/v1/index?table=thermal_memory_archive&content_column=original_content&embedding_column=embedding"
```

Expected: ~5,200 memories to embed at ~100/batch = ~52 batches.

---

## API Reference

### POST /v1/embeddings

```json
Request:
{
  "texts": ["Hello world", "Cherokee AI"],
  "cache": true
}

Response:
{
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
  "model": "BAAI/bge-large-en-v1.5",
  "dimensions": 1024,
  "cached_count": 1,
  "computed_count": 1,
  "latency_ms": 45
}
```

### POST /v1/search

```json
Request:
{
  "query": "authentication security",
  "table": "thermal_memory_archive",
  "limit": 5,
  "threshold": 0.7
}

Response:
[
  {
    "id": 123,
    "content": "Security review of authentication...",
    "similarity": 0.89,
    "metadata": {"type": "kb_article"}
  }
]
```

---

## Model Selection

| Model | Dimensions | Size | Speed | Quality |
|-------|------------|------|-------|---------|
| **BAAI/bge-large-en-v1.5** | 1024 | 1.3GB | Medium | Excellent |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | 90MB | Fast | Good |
| BAAI/bge-small-en-v1.5 | 384 | 130MB | Fast | Good |

**Recommendation**: Start with **BGE-large** for quality. Switch to smaller if latency is an issue.

---

## Success Criteria

- [ ] pgvector extension installed on bluefin
- [ ] Vector columns added to thermal_memory_archive
- [ ] Embedding service running on port 8002
- [ ] `/v1/embeddings` returns valid vectors
- [ ] `/v1/search` finds semantically similar content
- [ ] Existing thermal memories backfilled with embeddings
- [ ] Gateway proxies embedding requests

---

## Files to Create

1. `/ganuda/services/embedding_service/embedding_server.py`
2. `/etc/systemd/system/embedding.service`
3. Database migrations for pgvector

---

*For Seven Generations*
