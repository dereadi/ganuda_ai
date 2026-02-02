# JR Instruction: Summary Augmented Chunking for CFR RAG

**JR ID:** JR-AI-006
**Priority:** P2
**Sprint:** VetAssist AI Enhancements Phase 2
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Assigned To:** software_jr
**Effort:** Medium

## Problem Statement

Current RAG retrieval for CFR (Code of Federal Regulations) sometimes returns wrong regulatory sections. Veterans receive incorrect citations, potentially leading to denied claims due to wrong legal basis.

Research on legal AI shows Summary Augmented Chunking (SAC) significantly improves retrieval precision for regulatory documents.

## Background

Standard chunking embeds raw text, which can miss semantic context. SAC generates a summary for each chunk and embeds both, enabling:
1. Better semantic matching via summary
2. Preserved detail via original content
3. Re-ranking based on summary relevance

## Required Implementation

### 1. Database Schema Update

ADD migration: `/ganuda/vetassist/backend/migrations/sac_rag_schema.sql`

```sql
-- Summary Augmented Chunking for CFR RAG
-- Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)

-- Add summary columns to existing RAG chunks table
ALTER TABLE vetassist_rag_chunks
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS summary_embedding VECTOR(384),
ADD COLUMN IF NOT EXISTS summary_generated_at TIMESTAMP;

-- Index for summary embedding similarity search
CREATE INDEX IF NOT EXISTS idx_rag_summary_embedding
ON vetassist_rag_chunks
USING ivfflat (summary_embedding vector_cosine_ops)
WITH (lists = 100);

-- Track SAC generation status
ALTER TABLE vetassist_rag_chunks
ADD COLUMN IF NOT EXISTS sac_status VARCHAR(20) DEFAULT 'pending';

COMMENT ON COLUMN vetassist_rag_chunks.summary IS 'AI-generated summary of chunk content for SAC retrieval';
COMMENT ON COLUMN vetassist_rag_chunks.summary_embedding IS 'Embedding vector of summary for similarity search';
COMMENT ON COLUMN vetassist_rag_chunks.sac_status IS 'pending, processing, complete, error';
```

### 2. SAC Generator Service

CREATE: `/ganuda/vetassist/backend/app/services/sac_generator.py`

```python
"""
Summary Augmented Chunking Generator for VetAssist RAG.
Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)

Generates summaries for RAG chunks to improve retrieval precision.
"""

import logging
import httpx
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkSummary:
    """Generated summary for a RAG chunk."""
    chunk_id: int
    summary: str
    original_length: int
    summary_length: int


class SACGenerator:
    """
    Generates summaries for CFR chunks using local LLM.
    """

    SUMMARY_PROMPT = '''Summarize this Code of Federal Regulations section in 2-3 sentences.
Focus on:
1. What disability/condition this applies to
2. Key eligibility criteria
3. Rating percentages if mentioned

CFR Section:
{content}

Summary:'''

    def __init__(self):
        self.api_url = os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        self.model = os.getenv("VLLM_MODEL", "/ganuda/models/qwen2.5-coder-32b-awq")

    async def generate_summary(self, chunk_content: str) -> str:
        """Generate a summary for a single chunk."""
        prompt = self.SUMMARY_PROMPT.format(content=chunk_content[:3000])  # Limit input

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"].strip()

    async def process_batch(
        self,
        chunks: List[Dict],
        batch_size: int = 10
    ) -> List[ChunkSummary]:
        """Process a batch of chunks and generate summaries."""
        summaries = []

        for chunk in chunks:
            try:
                summary = await self.generate_summary(chunk["content"])
                summaries.append(ChunkSummary(
                    chunk_id=chunk["id"],
                    summary=summary,
                    original_length=len(chunk["content"]),
                    summary_length=len(summary)
                ))
                logger.info(f"[SAC] Generated summary for chunk {chunk['id']}")
            except Exception as e:
                logger.error(f"[SAC] Error generating summary for chunk {chunk['id']}: {e}")

        return summaries


class SACIngestion:
    """
    Handles SAC ingestion for RAG chunks.
    """

    def __init__(self):
        from app.core.database_config import get_db_connection
        self.get_connection = get_db_connection
        self.generator = SACGenerator()
        self.embedding_model = self._load_embedding_model()

    def _load_embedding_model(self):
        """Load sentence transformer for embedding."""
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

    def get_pending_chunks(self, limit: int = 100) -> List[Dict]:
        """Get chunks that need SAC processing."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, content, cfr_section
                    FROM vetassist_rag_chunks
                    WHERE sac_status = 'pending' OR sac_status IS NULL
                    ORDER BY id
                    LIMIT %s
                """, (limit,))

                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    def update_chunk_summary(
        self,
        chunk_id: int,
        summary: str,
        summary_embedding: List[float]
    ):
        """Update chunk with generated summary and embedding."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE vetassist_rag_chunks
                    SET summary = %s,
                        summary_embedding = %s,
                        summary_generated_at = NOW(),
                        sac_status = 'complete'
                    WHERE id = %s
                """, (summary, summary_embedding, chunk_id))
                conn.commit()
        finally:
            conn.close()

    async def process_pending(self, batch_size: int = 50):
        """Process all pending chunks."""
        chunks = self.get_pending_chunks(batch_size)
        logger.info(f"[SAC] Processing {len(chunks)} pending chunks")

        if not chunks:
            logger.info("[SAC] No pending chunks to process")
            return

        # Generate summaries
        summaries = await self.generator.process_batch(chunks)

        # Generate embeddings and update database
        for summary in summaries:
            embedding = self.embedding_model.encode(summary.summary).tolist()
            self.update_chunk_summary(summary.chunk_id, summary.summary, embedding)

        logger.info(f"[SAC] Completed processing {len(summaries)} chunks")


# Background task runner
async def run_sac_backfill():
    """Run SAC backfill for existing chunks."""
    ingestion = SACIngestion()
    while True:
        chunks = ingestion.get_pending_chunks(100)
        if not chunks:
            break
        await ingestion.process_pending(100)
```

### 3. Enhanced RAG Query Service

MODIFY: `/ganuda/vetassist/backend/app/services/rag_query.py`

Update query method to use hybrid SAC retrieval:

```python
from sentence_transformers import SentenceTransformer

class RAGQueryService:

    def __init__(self):
        from app.core.database_config import get_db_connection
        self.get_connection = get_db_connection
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def query_with_sac(
        self,
        query: str,
        top_k: int = 5,
        summary_weight: float = 0.4
    ) -> List[Dict]:
        """
        Hybrid query using both content and summary embeddings.

        Args:
            query: User query
            top_k: Number of results to return
            summary_weight: Weight for summary similarity (0-1)

        Returns:
            List of matching chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Hybrid query: combine content and summary similarity
                cur.execute("""
                    WITH content_match AS (
                        SELECT id, content, cfr_section, summary,
                               1 - (embedding <=> %s::vector) as content_score
                        FROM vetassist_rag_chunks
                        WHERE embedding IS NOT NULL
                    ),
                    summary_match AS (
                        SELECT id,
                               1 - (summary_embedding <=> %s::vector) as summary_score
                        FROM vetassist_rag_chunks
                        WHERE summary_embedding IS NOT NULL
                    )
                    SELECT
                        c.id,
                        c.content,
                        c.cfr_section,
                        c.summary,
                        c.content_score,
                        COALESCE(s.summary_score, 0) as summary_score,
                        (c.content_score * %s + COALESCE(s.summary_score, 0) * %s) as combined_score
                    FROM content_match c
                    LEFT JOIN summary_match s ON c.id = s.id
                    ORDER BY combined_score DESC
                    LIMIT %s
                """, (
                    query_embedding,
                    query_embedding,
                    1 - summary_weight,
                    summary_weight,
                    top_k
                ))

                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]

                logger.info(f"[RAG-SAC] Found {len(results)} matches for query")
                return results

        finally:
            conn.close()

    def query_with_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_sac: bool = True,
        **kwargs
    ):
        """Enhanced query_with_context with SAC support."""
        if use_sac:
            results = self.query_with_sac(query, **kwargs)
        else:
            results = self._legacy_query(query, **kwargs)

        # ... rest of existing method ...
        return results
```

### 4. SAC Background Task

CREATE: `/ganuda/vetassist/backend/scripts/sac_backfill.py`

```python
#!/usr/bin/env python3
"""
SAC Backfill Script - Generate summaries for existing RAG chunks.
Run as background task or cron job.
"""

import asyncio
import sys
sys.path.insert(0, '/ganuda/vetassist/backend')

from app.services.sac_generator import SACIngestion, run_sac_backfill

async def main():
    print("[SAC Backfill] Starting...")
    await run_sac_backfill()
    print("[SAC Backfill] Complete")

if __name__ == "__main__":
    asyncio.run(main())
```

## Verification

```bash
# 1. Apply database migration
cd /ganuda/vetassist/backend
psql -h 192.168.132.222 -U claude -d zammad_production -f migrations/sac_rag_schema.sql

# 2. Test SAC generator
python3 -c "
from app.services.sac_generator import SACGenerator, SACIngestion
print('✓ SAC Generator imported')

ingestion = SACIngestion()
pending = ingestion.get_pending_chunks(10)
print(f'✓ Found {len(pending)} pending chunks')
"

# 3. Run backfill (small batch for testing)
python3 scripts/sac_backfill.py

# 4. Test hybrid query
python3 -c "
from app.services.rag_query import RAGQueryService
service = RAGQueryService()
results = service.query_with_sac('PTSD rating criteria', top_k=3)
print(f'✓ SAC query returned {len(results)} results')
for r in results:
    print(f'  - {r[\"cfr_section\"]}: content={r[\"content_score\"]:.2f}, summary={r[\"summary_score\"]:.2f}')
"
```

## Performance Targets (Eagle Eye)

| Metric | Baseline | Target |
|--------|----------|--------|
| CFR retrieval precision@5 | ~0.75 | >0.90 |
| Query latency | ~200ms | <300ms |
| SAC backfill throughput | N/A | >100 chunks/min |

---

FOR SEVEN GENERATIONS
