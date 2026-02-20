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
from sentence_transformers import SentenceTransformer
import time
import os

app = FastAPI(title="Cherokee AI Embedding Service", version="1.0.0")

MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM = 1024

print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print(f"Model loaded. Dimension: {EMBEDDING_DIM}")

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', '')
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


@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME, "dimensions": EMBEDDING_DIM}


@app.post("/v1/embeddings", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest):
    """Generate embeddings for texts"""
    start = time.time()
    embeddings = []
    cached_count = 0
    computed_count = 0

    for text in request.texts:
        embedding = model.encode(text, normalize_embeddings=True).tolist()
        embeddings.append(embedding)
        computed_count += 1

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
    query_embedding = model.encode(request.query, normalize_embeddings=True).tolist()

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(f"""
            SELECT id, {request.column} as content,
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
                id=r["id"],
                content=r["content"][:1000] if r["content"] else "",
                similarity=float(r["similarity"]),
                metadata=r.get("metadata")
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
                      batch_size: int = 50):
    """Backfill embeddings for existing records"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {embedding_column} IS NULL")
    total = cur.fetchone()[0]

    if total == 0:
        return {"message": "All records have embeddings", "indexed": 0}

    indexed = 0
    while indexed < total:
        cur.execute(f"""
            SELECT id, {content_column} FROM {table}
            WHERE {embedding_column} IS NULL LIMIT %s
        """, (batch_size,))
        batch = cur.fetchall()
        if not batch:
            break

        texts = [row[1] or "" for row in batch]
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        for (record_id, _), embedding in zip(batch, embeddings):
            cur.execute(f"UPDATE {table} SET {embedding_column} = %s WHERE id = %s",
                       (embedding.tolist(), record_id))

        conn.commit()
        indexed += len(batch)
        print(f"Indexed {indexed}/{total}")

    cur.close()
    conn.close()
    return {"message": f"Indexed {indexed} records", "indexed": indexed}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Cherokee AI Embedding Service")
    print(f"Model: {MODEL_NAME}")
    print("Endpoints: /health, /v1/embeddings, /v1/search, /v1/index")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8003)
