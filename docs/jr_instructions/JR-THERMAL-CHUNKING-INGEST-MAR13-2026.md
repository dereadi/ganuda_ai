# JR INSTRUCTION: Thermal Chunking — Smart Ingest for Semantic Search

**Task**: Add chunking to thermal memory ingest so long thermals are split into searchable chunks with parent linkage. Adapted from jsdorn/MyBrain chunking pattern (parent_id + chunk_index). Dramatically improves vector search quality on our 92K+ thermals.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Council Vote**: #4df2e34784f1b36c (0.874, APPROVED)
**Depends On**: thermal_memory_archive table, embedding pipeline

## Context

Our thermals are stored as unstructured blobs. Average length is 340 chars (fine), but the 95th percentile is 540 chars and the max is 652K chars. Long thermals get one embedding vector covering the whole blob — semantic search misses specific details buried inside.

Joe Dorn's MyBrain splits notes into chunks with `parent_id` + `chunk_index`. When searching, chunks are returned individually (high precision) and can be reassembled by parent (full context). We adopt this pattern for thermals.

## Step 1: Add Chunk Columns to thermal_memory_archive

```sql
-- Add chunking support columns
ALTER TABLE thermal_memory_archive
  ADD COLUMN IF NOT EXISTS parent_thermal_id INTEGER REFERENCES thermal_memory_archive(id),
  ADD COLUMN IF NOT EXISTS chunk_index INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS chunk_total INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS is_chunk BOOLEAN DEFAULT FALSE;

-- Index for reassembly
CREATE INDEX IF NOT EXISTS idx_thermal_parent_chunk
  ON thermal_memory_archive(parent_thermal_id, chunk_index)
  WHERE parent_thermal_id IS NOT NULL;

-- Existing thermals are chunk_index=0, chunk_total=1, is_chunk=false (already defaults)
```

## Step 2: Create Chunking Function

Create `/ganuda/lib/thermal_chunker.py`:

```python
"""Thermal memory chunker — splits long thermals into semantic chunks.

Adapted from jsdorn/MyBrain chunking pattern.
Council vote #4df2e34784f1b36c.

Strategy:
- Thermals <= 512 chars: no chunking (one embedding covers it)
- Thermals > 512 chars: split on sentence boundaries, ~400 char target per chunk
- Each chunk gets its own embedding vector
- Chunks link back to parent via parent_thermal_id + chunk_index
"""

import re

CHUNK_TARGET = 400   # Target chars per chunk
CHUNK_MAX = 512      # Max chars before chunking kicks in
CHUNK_OVERLAP = 50   # Overlap between chunks for context continuity

# Split on sentence boundaries
SENTENCE_RE = re.compile(r'(?<=[.!?])\s+|(?<=\n)\s*')


def should_chunk(content: str) -> bool:
    """Return True if content exceeds chunk threshold."""
    return len(content) > CHUNK_MAX


def chunk_thermal(content: str) -> list[str]:
    """Split thermal content into chunks on sentence boundaries.

    Returns list of chunk strings. Single-element list if no chunking needed.
    """
    if not should_chunk(content):
        return [content]

    sentences = SENTENCE_RE.split(content)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If adding this sentence would exceed target AND we have content, start new chunk
        if len(current_chunk) + len(sentence) > CHUNK_TARGET and current_chunk:
            chunks.append(current_chunk.strip())
            # Overlap: keep last CHUNK_OVERLAP chars as context bridge
            if len(current_chunk) > CHUNK_OVERLAP:
                current_chunk = current_chunk[-CHUNK_OVERLAP:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [content]


def ingest_thermal_chunked(conn, content: str, temperature: int,
                           domain_tag: str, sacred: bool = False,
                           source_node: str = None, source_triad: str = None) -> dict:
    """Ingest a thermal with automatic chunking.

    For short thermals: behaves exactly like current ingest (one row).
    For long thermals: creates parent row + chunk rows, each with own embedding.

    Returns: {"parent_id": int, "chunks": int}
    """
    cur = conn.cursor()

    # Always insert the parent thermal (full content)
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, domain_tag, sacred_pattern,
         memory_hash, chunk_index, chunk_total, is_chunk, source_node, source_triad)
        VALUES (%s, %s, %s, %s,
                encode(sha256((%s || NOW()::text)::bytea), 'hex'),
                0, 1, FALSE, %s, %s)
        RETURNING id
    """, (content, temperature, domain_tag, sacred,
          f"thermal-{domain_tag}-", source_node, source_triad))

    parent_id = cur.fetchone()[0]
    chunks = chunk_thermal(content)

    if len(chunks) <= 1:
        # No chunking needed — parent row is the only row
        conn.commit()
        return {"parent_id": parent_id, "chunks": 1}

    # Update parent with chunk_total
    cur.execute("""
        UPDATE thermal_memory_archive
        SET chunk_total = %s
        WHERE id = %s
    """, (len(chunks), parent_id))

    # Insert chunk rows
    for i, chunk_text in enumerate(chunks):
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, domain_tag, sacred_pattern,
             memory_hash, parent_thermal_id, chunk_index, chunk_total, is_chunk,
             source_node, source_triad)
            VALUES (%s, %s, %s, %s,
                    encode(sha256((%s || NOW()::text)::bytea), 'hex'),
                    %s, %s, %s, TRUE, %s, %s)
        """, (chunk_text, temperature, domain_tag, sacred,
              f"chunk-{parent_id}-{i}-",
              parent_id, i, len(chunks), source_node, source_triad))

    conn.commit()
    return {"parent_id": parent_id, "chunks": len(chunks)}
```

## Step 3: Backfill Existing Long Thermals

Create `/ganuda/scripts/backfill_thermal_chunks.py`:

```python
"""One-time backfill: chunk existing long thermals.

Run once after deploying chunking schema.
Only processes thermals > 512 chars that aren't already chunked.
"""

import psycopg2
from thermal_chunker import chunk_thermal

# DB config from secrets.env
import sys
sys.path.insert(0, '/ganuda/lib')

def backfill():
    conn = psycopg2.connect(
        host='192.168.132.222', port=5432,
        dbname='zammad_production', user='claude',
        password=open('/ganuda/config/secrets.env').read().split('DB_PASS=')[1].split('\n')[0]
    )
    cur = conn.cursor()

    # Find long thermals that aren't already chunked
    cur.execute("""
        SELECT id, original_content, temperature_score, domain_tag,
               sacred_pattern, source_node, source_triad
        FROM thermal_memory_archive
        WHERE LENGTH(original_content) > 512
        AND is_chunk = FALSE
        AND parent_thermal_id IS NULL
        AND chunk_total = 1
        ORDER BY id
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} thermals to chunk")

    chunked = 0
    total_chunks = 0

    for row in rows:
        tid, content, temp, domain, sacred, src_node, src_triad = row
        chunks = chunk_thermal(content)

        if len(chunks) <= 1:
            continue

        # Update parent
        cur.execute("UPDATE thermal_memory_archive SET chunk_total = %s WHERE id = %s",
                    (len(chunks), tid))

        # Insert chunks
        for i, chunk_text in enumerate(chunks):
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (original_content, temperature_score, domain_tag, sacred_pattern,
                 memory_hash, parent_thermal_id, chunk_index, chunk_total, is_chunk,
                 source_node, source_triad)
                VALUES (%s, %s, %s, %s,
                        encode(sha256((%s || NOW()::text)::bytea), 'hex'),
                        %s, %s, %s, TRUE, %s, %s)
            """, (chunk_text, temp, domain, sacred,
                  f"backfill-chunk-{tid}-{i}-",
                  tid, i, len(chunks), src_node, src_triad))

        chunked += 1
        total_chunks += len(chunks)

        if chunked % 100 == 0:
            conn.commit()
            print(f"  Chunked {chunked} thermals ({total_chunks} chunks)")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done: {chunked} thermals → {total_chunks} chunks")

if __name__ == "__main__":
    backfill()
```

## Step 4: Update Embedding Pipeline

The existing embedding pipeline should:
1. For chunk rows (is_chunk=TRUE): generate embedding from chunk content (shorter, more precise)
2. For parent rows (is_chunk=FALSE, chunk_total > 1): skip embedding (chunks carry the vectors)
3. For standalone rows (is_chunk=FALSE, chunk_total = 1): embed as before

## Step 5: Update Search to Reassemble

When vector search returns a chunk, include the parent_thermal_id so the caller can fetch full context:

```sql
-- Search returns chunks; caller can fetch parent for full context
SELECT t.id, t.original_content, t.temperature_score, t.domain_tag,
       t.parent_thermal_id, t.chunk_index,
       p.original_content AS parent_content
FROM thermal_memory_archive t
LEFT JOIN thermal_memory_archive p ON p.id = t.parent_thermal_id
WHERE t.embedding <=> query_vector < 0.3
ORDER BY t.embedding <=> query_vector
LIMIT 10;
```

## DO NOT

- Chunk thermals under 512 chars — the overhead isn't worth it for short content
- Delete parent thermals when chunking — parent holds the canonical full text
- Skip the backfill — existing long thermals won't benefit from chunking otherwise
- Generate embeddings for parent rows that have chunks — waste of compute
- Hardcode DB credentials — use secrets.env

## Acceptance Criteria

- Schema migration applied (parent_thermal_id, chunk_index, chunk_total, is_chunk columns)
- `thermal_chunker.py` splits on sentence boundaries with 50-char overlap
- Backfill script processes existing long thermals
- New thermal ingest uses `ingest_thermal_chunked()` by default
- Vector search returns chunk + parent context
- No regression on short thermals (identical behavior)
