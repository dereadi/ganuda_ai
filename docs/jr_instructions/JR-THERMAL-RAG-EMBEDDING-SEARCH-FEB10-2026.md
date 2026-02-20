# Jr Instruction: Thermal Memory RAG — Embedding Search Integration

**Kanban**: #1760
**Priority**: HIGH (sacred_fire_priority 5)
**Target Node**: redfin (specialist_council.py) + bluefin (schema)
**Ref**: ULTRATHINK-LORA-SHIFT-RAG-PROMPT-OPTIMIZATION-FEB10-2026.md
**Council Vote**: audit_hash `8073845bd4abffc6`

## Context

The council determined that thermal memory RAG optimization is the highest-value alternative to LoRA fine-tuning. Currently, thermal_memory_archive is searched via ILIKE keyword matching only. An embedding service (BAAI/bge-large-en-v1.5, 1024 dimensions) is already running and has pgvector support. This task wires semantic search into the council voting flow.

## Step 1: Add embedding column and index to thermal_memory_archive

This is a SQL migration. Create a new migration file.

Create `/ganuda/jr_assignments/database_migrations/002_thermal_memory_embeddings.sql`

```sql
-- Thermal Memory RAG: Add embedding column for semantic search
-- Migration 002 — February 10, 2026
-- Ref: Kanban #1760, Council audit 8073845b

-- Requires pgvector extension (already installed for VetAssist RAG)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column (BGE-large-en-v1.5 produces 1024-dim vectors)
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- IVFFlat index for cosine similarity search
-- lists = sqrt(19800) ≈ 141, rounded to 150
CREATE INDEX IF NOT EXISTS idx_thermal_embedding_cosine
ON thermal_memory_archive
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 150);

-- Index for filtering by temperature + embedding availability
CREATE INDEX IF NOT EXISTS idx_thermal_embedding_temp
ON thermal_memory_archive (temperature_score DESC)
WHERE embedding IS NOT NULL;
```

## Step 2: Add semantic search method to specialist_council.py

File: `/ganuda/lib/specialist_council.py`

Add after the existing imports (after line 26):

```python
<<<<<<< SEARCH
from concurrent.futures import ThreadPoolExecutor, as_completed
=======
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
>>>>>>> REPLACE
```

Add a new function after the `INFRASTRUCTURE_CONTEXT` definition (after line 126, before `SPECIALISTS`). Insert between the closing `"""` of INFRASTRUCTURE_CONTEXT and the `SPECIALISTS = {` line:

```python
<<<<<<< SEARCH
"""

# Specialist definitions with infrastructure context
SPECIALISTS = {
=======
"""

# Embedding service for semantic search (BGE-large-en-v1.5, 1024 dims)
EMBEDDING_SERVICE_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://localhost:8003')

def query_thermal_memory_semantic(question: str, limit: int = 5, min_temperature: float = 30.0) -> str:
    """Retrieve semantically relevant thermal memories for council context.

    Uses the embedding service to find similar memories via pgvector cosine search.
    Falls back to keyword ILIKE if embedding service is unavailable.
    """
    try:
        # Get embedding for the question
        embed_resp = requests.post(
            f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
            json={"text": question},
            timeout=10
        )
        if embed_resp.status_code != 200:
            raise Exception(f"Embedding service returned {embed_resp.status_code}")

        query_embedding = embed_resp.json().get("embedding")
        if not query_embedding:
            raise Exception("No embedding returned")

        # Semantic search via pgvector
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 400), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))

        rows = cur.fetchall()
        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)

        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval):"]
        for row in rows:
            mem_id, content, temp, sim = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f} | similarity={sim:.2f}]")
            context_parts.append(content)

        return "\n".join(context_parts)

    except Exception as e:
        print(f"[RAG] Semantic search failed, falling back to keyword: {e}")
        return _keyword_fallback(question, limit)


def _keyword_fallback(question: str, limit: int = 5) -> str:
    """Fallback keyword search when embedding service is unavailable."""
    try:
        words = question.split()[:5]
        pattern = '%' + '%'.join(words) + '%'
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 400), temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
              AND temperature_score >= 30
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (pattern, limit))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return ""

        context_parts = ["RELEVANT THERMAL MEMORIES (keyword retrieval):"]
        for row in rows:
            mem_id, content, temp = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f}]")
            context_parts.append(content)

        return "\n".join(context_parts)
    except Exception:
        return ""


# Specialist definitions with infrastructure context
SPECIALISTS = {
>>>>>>> REPLACE
```

## Step 3: Wire RAG into the council vote flow

Inject retrieved thermal memories into the question context before querying specialists.

File: `/ganuda/lib/specialist_council.py`

In the `vote()` method, add RAG retrieval at the start (right after the method signature):

```python
<<<<<<< SEARCH
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Health check deep backend before routing
        deepseek_healthy = check_backend_health(DEEPSEEK_BACKEND)
=======
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Phase: Thermal Memory RAG — enrich question with relevant memories
        thermal_context = ""
        try:
            thermal_context = query_thermal_memory_semantic(question, limit=5)
            if thermal_context:
                print(f"[RAG] Injected {thermal_context.count('Memory #')} thermal memories into council context")
        except Exception as e:
            print(f"[RAG] Memory retrieval failed (non-fatal): {e}")

        # Build enriched question with thermal context
        enriched_question = question
        if thermal_context:
            enriched_question = f"{question}\n\n---\n{thermal_context}"

        # Health check deep backend before routing
        deepseek_healthy = check_backend_health(DEEPSEEK_BACKEND)
>>>>>>> REPLACE
```

Then update the specialist query calls to use enriched_question instead of question. In the parallel query section:

```python
<<<<<<< SEARCH
                futures[executor.submit(self._query_specialist, sid, question, backend)] = sid
=======
                futures[executor.submit(self._query_specialist, sid, enriched_question, backend)] = sid
>>>>>>> REPLACE
```

And in the consensus synthesis, pass the original question (not enriched) to keep synthesis clean:

```python
<<<<<<< SEARCH
        # Synthesize consensus
        consensus = self._synthesize_consensus(responses, question)
=======
        # Synthesize consensus (use original question, not enriched)
        consensus = self._synthesize_consensus(responses, question)
>>>>>>> REPLACE
```

(This line stays the same — just confirming the original `question` is used, not `enriched_question`.)

## Step 4: Backfill existing memories

Create a backfill script. This calls the existing embedding service to generate embeddings for all thermal memories.

Create `/ganuda/scripts/backfill_thermal_embeddings.py`

```python
#!/usr/bin/env python3
"""Backfill thermal_memory_archive with embeddings from the embedding service.

Usage: python3 /ganuda/scripts/backfill_thermal_embeddings.py
"""
import os
import sys
import time
import requests
import psycopg2

EMBEDDING_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://localhost:8003')
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

BATCH_SIZE = 50

def backfill():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Count unembedded memories
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE embedding IS NULL")
    total = cur.fetchone()[0]
    print(f"Memories to embed: {total}")

    if total == 0:
        print("All memories already embedded.")
        return

    processed = 0
    errors = 0

    while True:
        cur.execute("""
            SELECT id, LEFT(original_content, 2000)
            FROM thermal_memory_archive
            WHERE embedding IS NULL
            ORDER BY temperature_score DESC, id
            LIMIT %s
        """, (BATCH_SIZE,))
        rows = cur.fetchall()

        if not rows:
            break

        for mem_id, content in rows:
            try:
                resp = requests.post(
                    f"{EMBEDDING_URL}/v1/embeddings",
                    json={"text": content},
                    timeout=30
                )
                if resp.status_code == 200:
                    embedding = resp.json().get("embedding")
                    if embedding:
                        cur.execute(
                            "UPDATE thermal_memory_archive SET embedding = %s::vector WHERE id = %s",
                            (str(embedding), mem_id)
                        )
                        processed += 1
                    else:
                        errors += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors < 5:
                    print(f"  Error on #{mem_id}: {e}")

            if processed % 100 == 0 and processed > 0:
                conn.commit()
                print(f"  Progress: {processed}/{total} embedded, {errors} errors")

        conn.commit()

    conn.close()
    print(f"\nBackfill complete: {processed} embedded, {errors} errors out of {total} total")


if __name__ == "__main__":
    backfill()
```

## Verification

After all steps:

1. Run the SQL migration on bluefin
2. Run the backfill script: `python3 /ganuda/scripts/backfill_thermal_embeddings.py`
3. Test semantic search: Query the council with a question and check logs for `[RAG] Injected N thermal memories`
4. Verify fallback: Stop embedding service, query council — should see `[RAG] Semantic search failed, falling back to keyword`

## Notes

- The embedding service must be running on redfin port 8003
- Backfill will take ~10-20 minutes for 19,800 memories at 50/batch
- IVFFlat index needs at least 150 rows to build properly (we have 19,800+ — no issue)
- The `traceback` import is added for future error reporting but not used yet — no harm
