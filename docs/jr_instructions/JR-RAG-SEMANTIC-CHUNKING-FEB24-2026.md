# Jr Instruction: RAG Semantic Chunking + Backfill

**Task ID:** RAG-SEMANTIC-CHUNK
**Kanban:** #1766
**Priority:** 2
**Sacred Fire Priority:** 50
**Story Points:** 13
**Assigned:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Long memories (>1000 chars) lose retrieval precision because embeddings compress everything into a single vector. This task creates a semantic chunking module and a backfill script that splits long memories into overlapping chunks, embeds each chunk independently, and stores them in a new `memory_chunks` table. This gives the RAG pipeline sub-document retrieval granularity.

Two new files:
1. `/ganuda/lib/semantic_chunker.py` — pure-stdlib chunking logic
2. `/ganuda/scripts/rag_chunk_backfill.py` — table creation, chunking, embedding, insertion

---

## Step 1: Create the semantic chunker module

Create `/ganuda/lib/semantic_chunker.py`

```python
"""
Semantic Chunker for Cherokee AI Federation RAG pipeline.

Splits long text at semantic boundaries (paragraphs > lines > sentences)
with configurable overlap. Uses only stdlib.
"""

import re
from typing import List


def chunk_memory(content: str, max_chunk_size: int = 1000, overlap_pct: float = 0.2) -> List[dict]:
    """
    Split content into semantically meaningful chunks with overlap.

    Args:
        content: The text to chunk.
        max_chunk_size: Maximum characters per chunk (default 1000).
        overlap_pct: Fraction of max_chunk_size to overlap with previous chunk (default 0.2).

    Returns:
        List of dicts with keys:
            chunk_index, chunk_content, start_char, end_char, overlap_chars
    """
    if not content or len(content) <= max_chunk_size:
        return [{
            "chunk_index": 0,
            "chunk_content": content or "",
            "start_char": 0,
            "end_char": len(content) if content else 0,
            "overlap_chars": 0,
        }]

    overlap_size = int(max_chunk_size * overlap_pct)

    # Split at semantic boundaries, finest granularity last
    segments = _split_semantic(content)

    chunks = []
    current_chars = []
    current_len = 0
    chunk_index = 0
    content_pos = 0  # tracks position in original content

    for segment in segments:
        seg_len = len(segment)

        # If a single segment exceeds max, force-split it
        if seg_len > max_chunk_size:
            # Flush anything accumulated
            if current_chars:
                chunk_text = "".join(current_chars)
                start = content_pos - len(chunk_text)
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_content": chunk_text,
                    "start_char": start,
                    "end_char": start + len(chunk_text),
                    "overlap_chars": overlap_size if chunk_index > 0 else 0,
                })
                chunk_index += 1
                current_chars = []
                current_len = 0

            # Hard-split the oversized segment
            pos = 0
            while pos < seg_len:
                end = min(pos + max_chunk_size, seg_len)
                piece = segment[pos:end]
                abs_start = content_pos + pos
                ov = 0
                if chunk_index > 0 and pos == 0:
                    ov = overlap_size
                elif pos > 0:
                    ov = overlap_size
                    pos_adj = max(pos - overlap_size, 0)
                    piece = segment[pos_adj:end]
                    abs_start = content_pos + pos_adj
                    ov = pos - pos_adj

                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_content": piece,
                    "start_char": abs_start,
                    "end_char": abs_start + len(piece),
                    "overlap_chars": ov,
                })
                chunk_index += 1
                pos = end
            content_pos += seg_len
            continue

        # Would adding this segment exceed max?
        if current_len + seg_len > max_chunk_size and current_chars:
            chunk_text = "".join(current_chars)
            start = content_pos - len(chunk_text)
            chunks.append({
                "chunk_index": chunk_index,
                "chunk_content": chunk_text,
                "start_char": start,
                "end_char": start + len(chunk_text),
                "overlap_chars": overlap_size if chunk_index > 0 else 0,
            })
            chunk_index += 1

            # Keep overlap from end of current chunk
            overlap_text = chunk_text[-overlap_size:] if len(chunk_text) > overlap_size else chunk_text
            current_chars = [overlap_text]
            current_len = len(overlap_text)

        current_chars.append(segment)
        current_len += seg_len
        content_pos += seg_len

    # Flush remaining
    if current_chars:
        chunk_text = "".join(current_chars)
        start = content_pos - len(chunk_text)
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_content": chunk_text,
            "start_char": start,
            "end_char": start + len(chunk_text),
            "overlap_chars": overlap_size if chunk_index > 0 else 0,
        })

    # Fix first chunk overlap
    if chunks:
        chunks[0]["overlap_chars"] = 0

    return chunks


def _split_semantic(text: str) -> List[str]:
    """
    Split text at semantic boundaries. Tries double-newline (paragraph)
    first, then single newline, then sentence boundaries.
    Returns segments that preserve the original text when joined.
    """
    # Try paragraph splits first
    parts = re.split(r'(\n\n+)', text)
    if len(parts) > 1:
        return parts

    # Try single newline
    parts = re.split(r'(\n)', text)
    if len(parts) > 1:
        return parts

    # Fall back to sentence boundaries: split on ". ", "! ", "? "
    # Keep the delimiter with the preceding segment
    parts = re.split(r'(?<=[.!?]) (?=[A-Z])', text)
    if len(parts) > 1:
        # Re-add spaces between segments (lost in split)
        result = []
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                result.append(part + " ")
            else:
                result.append(part)
        return result

    # No good boundary found, return whole text
    return [text]
```

---

## Step 2: Create the backfill script

Create `/ganuda/scripts/rag_chunk_backfill.py`

```python
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
```

---

## Verification

After both files are created, run these checks on **redfin**:

### 1. Count chunks created

```text
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) AS total_chunks FROM memory_chunks;"
```

Expected: a positive integer (depends on how many memories are >1000 chars).

### 2. Sample query against memory_chunks

```text
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT mc.chunk_id, mc.parent_memory_id, mc.chunk_index,
       LEFT(mc.chunk_content, 80) AS preview,
       mc.overlap_chars
FROM memory_chunks mc
ORDER BY mc.chunk_id
LIMIT 5;
"
```

Expected: 5 rows with chunk_index starting at 0, overlap_chars = 0 for first chunk of each parent.

### 3. Verify embedding dimensions are 1024

```text
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT chunk_id, vector_dims(chunk_embedding) AS dims
FROM memory_chunks
WHERE chunk_embedding IS NOT NULL
LIMIT 3;
"
```

Expected: `dims` = 1024 for all rows.

---

## Notes

- The chunker uses **only stdlib** (re module). No external NLP dependencies.
- Overlap (20% = 200 chars at default 1000 max) ensures context is not lost at chunk boundaries.
- The backfill script is **idempotent** — re-running it skips already-inserted chunks via `ON CONFLICT DO NOTHING`.
- The IVFFlat index with 50 lists is sized for the current memory count (~80K memories, expecting ~200-400K chunks).
- After backfill, downstream RAG queries can search `memory_chunks.chunk_embedding` for sub-document precision and join back to `thermal_memory_archive` via `parent_memory_id`.
