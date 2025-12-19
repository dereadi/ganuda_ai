# Jr Build Instructions: Federated Embedding Service

## Priority: HIGH - Enables Tribal Resonance

---

## Vision

> "Shared resonance, different personalities"

The federation shares a common semantic understanding while each node maintains its own context and personality. Like a tribe - shared culture, individual voices.

---

## Architecture

```
                         ┌─────────────────────────┐
                         │   Shared Thermal Memory │
                         │   (bluefin - pgvector)  │
                         └───────────┬─────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │     redfin      │    │     sasass      │    │     sasass2     │
    │   (GPU - BGE)   │    │  (MPS - BGE)    │    │  (MPS - BGE)    │
    │   Port 8003     │    │   Port 8003     │    │   Port 8003     │
    │                 │    │                 │    │                 │
    │ + Local Context │    │ + Local Context │    │ + Local Context │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Federated API  │
                         │  /v1/federated/ │
                         └─────────────────┘
```

---

## Components

### 1. Central Embedding Service (redfin - EXISTS)
- **Role**: Primary embedding generation (GPU accelerated)
- **Model**: BAAI/bge-large-en-v1.5
- **Port**: 8003
- **Storage**: Writes to bluefin pgvector

### 2. Edge Embedding Services (Mac Studios)
- **Role**: Local embedding + federated queries
- **Model**: BAAI/bge-large-en-v1.5 (MPS accelerated)
- **Port**: 8003
- **Storage**: Local SQLite + query central

### 3. Federated Query Router
- **Role**: Aggregate searches across nodes
- **Endpoint**: `/v1/federated/search`

---

## Mac Studio Deployment

### Prerequisites

```bash
# On sasass and sasass2
pip3 install sentence-transformers fastapi uvicorn psycopg2-binary
```

### Create Embedding Service

Create `/Users/Shared/ganuda/services/embedding_service/embedding_server.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federated Embedding Service - Mac Studio Edition
Uses MPS (Metal Performance Shaders) for GPU acceleration on Apple Silicon
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import time
import socket
import os

app = FastAPI(title="Cherokee AI Embedding Service", version="1.1.0")

# Configuration
MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM = 1024
NODE_NAME = socket.gethostname()
LOCAL_DB = f"/Users/Shared/ganuda/data/{NODE_NAME}_embeddings.db"

# Central database (bluefin)
CENTRAL_DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

# Load model with MPS (Apple Silicon GPU)
print(f"Loading embedding model on {NODE_NAME}...")
device = "mps" if os.uname().sysname == "Darwin" else "cuda"
model = SentenceTransformer(MODEL_NAME, device=device)
print(f"Model loaded on {device}. Dimension: {EMBEDDING_DIM}")


class EmbedRequest(BaseModel):
    texts: List[str]
    store_local: bool = False


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    node: str
    dimensions: int
    latency_ms: int


class SearchRequest(BaseModel):
    query: str
    scope: str = "central"  # "local", "central", "federated"
    limit: int = 10
    threshold: float = 0.6


class SearchResult(BaseModel):
    id: int
    content: str
    similarity: float
    source: str  # node name
    metadata: Optional[dict] = None


def init_local_db():
    """Initialize local SQLite database"""
    os.makedirs(os.path.dirname(LOCAL_DB), exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS local_embeddings (
            id INTEGER PRIMARY KEY,
            content_hash TEXT UNIQUE,
            content TEXT,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_central_db():
    return psycopg2.connect(**CENTRAL_DB_CONFIG)


@app.on_event("startup")
async def startup():
    init_local_db()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "node": NODE_NAME,
        "model": MODEL_NAME,
        "device": device,
        "dimensions": EMBEDDING_DIM
    }


@app.post("/v1/embeddings", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest):
    """Generate embeddings locally"""
    start = time.time()

    embeddings = model.encode(request.texts, normalize_embeddings=True).tolist()

    # Optionally store locally
    if request.store_local:
        conn = sqlite3.connect(LOCAL_DB)
        for text, emb in zip(request.texts, embeddings):
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            conn.execute(
                "INSERT OR IGNORE INTO local_embeddings (content_hash, content, embedding) VALUES (?, ?, ?)",
                (content_hash, text, str(emb))
            )
        conn.commit()
        conn.close()

    return EmbedResponse(
        embeddings=embeddings,
        model=MODEL_NAME,
        node=NODE_NAME,
        dimensions=EMBEDDING_DIM,
        latency_ms=int((time.time() - start) * 1000)
    )


@app.post("/v1/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """Search embeddings - local, central, or federated"""

    query_embedding = model.encode(request.query, normalize_embeddings=True).tolist()
    results = []

    if request.scope in ["central", "federated"]:
        # Search central thermal memory
        try:
            conn = get_central_db()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, original_content as content,
                       1 - (embedding <=> %s::vector) as similarity,
                       metadata
                FROM thermal_memory_archive
                WHERE embedding IS NOT NULL
                AND 1 - (embedding <=> %s::vector) > %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, request.threshold, query_embedding, request.limit))

            for r in cur.fetchall():
                results.append(SearchResult(
                    id=r["id"],
                    content=r["content"][:500] if r["content"] else "",
                    similarity=float(r["similarity"]),
                    source="central",
                    metadata=r.get("metadata")
                ))
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Central search error: {e}")

    if request.scope in ["local", "federated"]:
        # Search local embeddings
        try:
            conn = sqlite3.connect(LOCAL_DB)
            cur = conn.cursor()
            cur.execute("SELECT id, content, embedding FROM local_embeddings")

            import json
            import numpy as np
            query_vec = np.array(query_embedding)

            for row in cur.fetchall():
                local_emb = np.array(json.loads(row[2]))
                similarity = float(np.dot(query_vec, local_emb))
                if similarity > request.threshold:
                    results.append(SearchResult(
                        id=row[0],
                        content=row[1][:500],
                        similarity=similarity,
                        source=NODE_NAME
                    ))
            conn.close()
        except Exception as e:
            print(f"Local search error: {e}")

    # Sort by similarity and limit
    results.sort(key=lambda x: x.similarity, reverse=True)
    return results[:request.limit]


@app.post("/v1/store")
async def store_to_central(texts: List[str]):
    """Store embeddings in central thermal memory"""
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    conn = get_central_db()
    cur = conn.cursor()

    stored = 0
    for text, emb in zip(texts, embeddings):
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        try:
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, embedding, current_stage, temperature_score)
                VALUES (%s, %s, %s, 'FRESH', 90.0)
                ON CONFLICT (memory_hash) DO UPDATE SET embedding = EXCLUDED.embedding
            """, (content_hash, text, emb))
            stored += 1
        except Exception as e:
            print(f"Store error: {e}")

    conn.commit()
    cur.close()
    conn.close()

    return {"stored": stored, "source_node": NODE_NAME}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(f"Cherokee AI Federated Embedding Service")
    print(f"Node: {NODE_NAME}")
    print(f"Device: {device}")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

---

## Deployment Steps

### On sasass (192.168.132.241):

```bash
# Create directories
mkdir -p /Users/Shared/ganuda/services/embedding_service
mkdir -p /Users/Shared/ganuda/data

# Copy embedding server (or create from above)
# ...

# Install dependencies
pip3 install sentence-transformers fastapi uvicorn psycopg2-binary

# Test run
cd /Users/Shared/ganuda/services/embedding_service
python3 embedding_server.py
```

### On sasass2 (192.168.132.242):

Same steps as sasass.

---

## LaunchAgent for macOS

Create `~/Library/LaunchAgents/com.cherokee.embedding.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.embedding</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/Shared/ganuda/services/embedding_service/embedding_server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda/services/embedding_service</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/embedding.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/embedding.error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.cherokee.embedding.plist
```

---

## Federated Search Example

```python
# Query across all nodes
import httpx

NODES = [
    "http://192.168.132.223:8003",  # redfin
    "http://192.168.132.241:8003",  # sasass
    "http://192.168.132.242:8003",  # sasass2
]

async def federated_search(query: str, limit: int = 10):
    """Search across all tribe nodes"""
    all_results = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for node in NODES:
            try:
                resp = await client.post(
                    f"{node}/v1/search",
                    json={"query": query, "scope": "local", "limit": limit}
                )
                all_results.extend(resp.json())
            except:
                continue

    # Also search central
    resp = await client.post(
        f"{NODES[0]}/v1/search",
        json={"query": query, "scope": "central", "limit": limit}
    )
    all_results.extend(resp.json())

    # Dedupe and sort
    seen = set()
    unique = []
    for r in sorted(all_results, key=lambda x: x["similarity"], reverse=True):
        if r["content"][:100] not in seen:
            seen.add(r["content"][:100])
            unique.append(r)

    return unique[:limit]
```

---

## Tribal Resonance Model

Each of our 6 nodes contributes to shared understanding:

| Node | IP | Role | Local Personality |
|------|-----|------|-------------------|
| **redfin** | 192.168.132.223 | GPU Inference | Council deliberations, vLLM, decisions |
| **bluefin** | 192.168.132.222 | Database | Shared thermal memory (pgvector), Grafana |
| **greenfin** | 192.168.132.224 | Daemons | Monitoring, Promtail, background tasks |
| **sasass** | 192.168.132.241 | Mac Studio | Edge development, local AI experiments |
| **sasass2** | 192.168.132.242 | Mac Studio | Edge development, research |
| **tpm-macbook** | local | Orchestration | TPM CLI, Claude Code, coordination |

### How Resonance Works:

1. **Local observations** stored in node's local DB
2. **Important insights** promoted to central thermal memory
3. **Queries** search local first, then central
4. **Federated queries** aggregate across all nodes
5. **Semantic similarity** finds related thoughts across the tribe

---

## Success Criteria

- [ ] Embedding service running on all Mac Studios
- [ ] MPS acceleration working (not CPU)
- [ ] Local SQLite storing node-specific context
- [ ] Central search returning thermal memories
- [ ] Federated search aggregating across nodes

---

*For Seven Generations*
