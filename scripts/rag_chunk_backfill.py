"""
RAG Chunk Backfill Script — Cherokee AI Federation

Creates memory_chunks table and populates it by:
1. Querying thermal_memory_archive for long memories (>1000 chars)
2. Chunking each via semantic_chunker.chunk_memory()
3. Embedding each chunk via greenfin:8003
4. Inserting into memory_chunks with ON CONFLICT DO NOTHING

Usage:
    python3 /ganuda/scripts/rag_chunk_backfill.py
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error

import psycopg2
import psycopg2.extras

# Add lib to path
sys.path.insert(0, "/ganuda/lib")
from semantic_chunker import chunk_memory

EMBEDDING_URL = "http://192.168.132.224:8003/embed"
BATCH_SIZE = 50


def get_db_connection():
    """Connect to federation database."""
    return psycopg2.connect(
        host="192.168.132.222",
        dbname="zammad_production",
        user="claude",
        password=os.environ["CHEROKEE_DB_PASS"],
    )


def create_table(conn):
    """Create memory_chunks table if it does not exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_chunks (
                chunk_id SERIAL PRIMARY KEY,
                parent_memory_id INTEGER NOT NULL REFERENCES thermal_memory_archive(id),
                chunk_index INTEGER NOT NULL,
                chunk_content TEXT NOT NULL,
                chunk_hash VARCHAR(64) NOT NULL,
                chunk_embedding vector(1024),
                overlap_chars INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(parent_memory_id, chunk_index)
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_parent
            ON memory_chunks(parent_memory_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON memory_chunks USING ivfflat (chunk_embedding vector_cosine_ops)
            WITH (lists = 50);
        """)
    conn.commit()
    print("[OK] memory_chunks table ready")


def embed_text(text: str) -> list:
    """Get embedding from greenfin embedding service."""
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        EMBEDDING_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["embedding"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as e:
        print(f"  [WARN] Embedding failed: {e}")
        return None


def fetch_long_memories(conn):
    """Fetch memories with original_content longer than 1000 chars."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, original_content
            FROM thermal_memory_archive
            WHERE LENGTH(original_content) > 1000
            ORDER BY id
        """)
        return cur.fetchall()


def process_memory(conn, memory_id: int, content: str, stats: dict):
    """Chunk, embed, and insert chunks for a single memory."""
    chunks = chunk_memory(content, max_chunk_size=1000, overlap_pct=0.2)

    for chunk in chunks:
        chunk_hash = hashlib.sha256(chunk["chunk_content"].encode()).hexdigest()
        embedding = embed_text(chunk["chunk_content"])

        embedding_str = str(embedding) if embedding else None

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memory_chunks
                    (parent_memory_id, chunk_index, chunk_content, chunk_hash,
                     chunk_embedding, overlap_chars)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (parent_memory_id, chunk_index) DO NOTHING
            """, (
                memory_id,
                chunk["chunk_index"],
                chunk["chunk_content"],
                chunk_hash,
                embedding_str,
                chunk["overlap_chars"],
            ))

        if cur.rowcount > 0:
            stats["chunks_inserted"] += 1
        else:
            stats["chunks_skipped"] += 1

    conn.commit()
    stats["memories_processed"] += 1


def main():
    print("=" * 60)
    print("RAG Semantic Chunking Backfill")
    print("=" * 60)

    conn = get_db_connection()
    print("[OK] Database connected")

    create_table(conn)

    memories = fetch_long_memories(conn)
    total = len(memories)
    print(f"[INFO] Found {total} memories with >1000 chars to chunk")

    if total == 0:
        print("[DONE] Nothing to process")
        conn.close()
        return

    stats = {
        "memories_processed": 0,
        "chunks_inserted": 0,
        "chunks_skipped": 0,
    }

    start_time = time.time()

    for i, mem in enumerate(memories):
        memory_id = mem["id"]
        content = mem["original_content"]

        process_memory(conn, memory_id, content, stats)

        if (i + 1) % BATCH_SIZE == 0 or (i + 1) == total:
            elapsed = time.time() - start_time
            rate = stats["memories_processed"] / elapsed if elapsed > 0 else 0
            print(
                f"  [{i + 1}/{total}] "
                f"processed={stats['memories_processed']}, "
                f"chunks_inserted={stats['chunks_inserted']}, "
                f"skipped={stats['chunks_skipped']}, "
                f"rate={rate:.1f} mem/s"
            )

    elapsed = time.time() - start_time
    conn.close()

    print()
    print("=" * 60)
    print("BACKFILL COMPLETE")
    print(f"  Memories processed: {stats['memories_processed']}")
    print(f"  Chunks inserted:    {stats['chunks_inserted']}")
    print(f"  Chunks skipped:     {stats['chunks_skipped']}")
    print(f"  Elapsed:            {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()