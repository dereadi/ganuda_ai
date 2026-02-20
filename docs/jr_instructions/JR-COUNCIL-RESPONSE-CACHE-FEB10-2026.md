# Jr Instruction: Council Response Cache — Semantic Similarity Reuse

**Kanban**: #1762
**Priority**: LOW (sacred_fire_priority 3)
**Target Node**: redfin (specialist_council.py) + bluefin (council_votes schema)
**Ref**: ULTRATHINK-LORA-SHIFT-RAG-PROMPT-OPTIMIZATION-FEB10-2026.md
**Council Vote**: audit_hash `8073845bd4abffc6`
**Dependency**: Soft dependency on Kanban #1760 (uses same embedding service)

## Context

Every council query triggers a full 7-specialist parallel deliberation (~18 seconds, 7 vLLM calls). Many queries are semantically similar to previous ones. This task adds a cache layer: before running full deliberation, check if a semantically similar query was recently answered with high confidence. If so, return the cached response.

## Step 1: Add question embedding column to council_votes

SQL migration on bluefin.

Create `/ganuda/jr_assignments/database_migrations/003_council_vote_embeddings.sql`

```sql
-- Council Response Cache: Add question embedding for similarity search
-- Migration 003 — February 10, 2026
-- Ref: Kanban #1762, Council audit 8073845b

CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column for council vote questions
ALTER TABLE council_votes
ADD COLUMN IF NOT EXISTS question_embedding vector(1024);

-- IVFFlat index for cosine similarity on question embeddings
-- Fewer rows than thermal memory, so lists = 50 is sufficient
CREATE INDEX IF NOT EXISTS idx_council_question_embedding
ON council_votes
USING ivfflat (question_embedding vector_cosine_ops)
WITH (lists = 50);
```

## Step 2: Add cache check to council voting flow

File: `/ganuda/lib/specialist_council.py`

Add a cache lookup method to the `SpecialistCouncil` class. Insert after the `_synthesize_consensus` method (after line 376, before `vote`):

```python
<<<<<<< SEARCH
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
=======
    def _check_response_cache(self, question: str, similarity_threshold: float = 0.92,
                               max_age_hours: int = 24, min_confidence: float = 0.85) -> Optional[CouncilVote]:
        """Check if a semantically similar question was recently answered with high confidence."""
        try:
            # Embed the incoming question
            embed_resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
                json={"text": question},
                timeout=10
            )
            if embed_resp.status_code != 200:
                return None

            query_embedding = embed_resp.json().get("embedding")
            if not query_embedding:
                return None

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT audit_hash, question, recommendation, confidence, consensus,
                       responses::text, concerns::text,
                       1 - (question_embedding <=> %s::vector) as similarity
                FROM council_votes
                WHERE question_embedding IS NOT NULL
                  AND confidence >= %s
                  AND voted_at > NOW() - INTERVAL '%s hours'
                ORDER BY question_embedding <=> %s::vector
                LIMIT 1
            """, (str(query_embedding), min_confidence, max_age_hours, str(query_embedding)))

            row = cur.fetchone()
            conn.close()

            if row and row[7] >= similarity_threshold:
                print(f"[CACHE HIT] Similar question found (similarity={row[7]:.3f}, audit={row[0]})")
                import json as _json
                cached_responses = _json.loads(row[5]) if row[5] else {}
                cached_concerns = _json.loads(row[6]) if row[6] else []

                return CouncilVote(
                    question=question,
                    responses=[],
                    consensus=f"[CACHED from {row[0]}] {row[4]}",
                    recommendation=row[3] if isinstance(row[3], str) else "PROCEED",
                    confidence=row[3] if isinstance(row[3], float) else 0.85,
                    concerns=cached_concerns if isinstance(cached_concerns, list) else [],
                    audit_hash=f"cache-{row[0]}"
                )
            return None

        except Exception as e:
            print(f"[CACHE] Lookup failed (non-fatal): {e}")
            return None

    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
>>>>>>> REPLACE
```

## Step 3: Wire cache check into vote flow

File: `/ganuda/lib/specialist_council.py`

At the start of the `vote()` method, add cache check before anything else. Insert right after the docstring:

```python
<<<<<<< SEARCH
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Phase: Thermal Memory RAG — enrich question with relevant memories
=======
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Phase: Response Cache — check for similar recent high-confidence answers
        if not high_stakes:  # Never serve cache for high_stakes deliberations
            cached = self._check_response_cache(question)
            if cached:
                self._log_vote(cached, routing_manifest={"vote_type": "cached", "source_audit": cached.audit_hash})
                return cached

        # Phase: Thermal Memory RAG — enrich question with relevant memories
>>>>>>> REPLACE
```

Note: The RAG phase reference assumes Kanban #1760 has been applied. If not yet applied, the SEARCH block should match the current code at that location.

## Step 4: Embed question on every new vote

File: `/ganuda/lib/specialist_council.py`

In the `_log_vote` method, add question embedding storage. Find where votes are logged to database and add the embedding. If `_log_vote` stores to council_votes, add this after the INSERT:

Add a new method to the class for embedding questions on vote storage:

```python
<<<<<<< SEARCH
        # Log to database with routing manifest
        self._log_vote(vote, routing_manifest=routing_manifest)

        return vote
=======
        # Log to database with routing manifest
        self._log_vote(vote, routing_manifest=routing_manifest)

        # Embed and store question for future cache lookups
        self._embed_vote_question(vote)

        return vote
>>>>>>> REPLACE
```

Then add the embedding method to the class (before `_log_vote` or after it):

```python
<<<<<<< SEARCH
    def _query_specialist_with_prompt(self, specialist_id: str, question: str,
=======
    def _embed_vote_question(self, vote: CouncilVote):
        """Embed the vote question for future cache similarity lookups."""
        try:
            embed_resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
                json={"text": vote.question},
                timeout=10
            )
            if embed_resp.status_code == 200:
                embedding = embed_resp.json().get("embedding")
                if embedding:
                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE council_votes
                        SET question_embedding = %s::vector
                        WHERE audit_hash = %s
                    """, (str(embedding), vote.audit_hash))
                    conn.commit()
                    conn.close()
        except Exception as e:
            print(f"[CACHE] Failed to embed vote question (non-fatal): {e}")

    def _query_specialist_with_prompt(self, specialist_id: str, question: str,
>>>>>>> REPLACE
```

## Verification

After all steps:

1. Run SQL migration on bluefin
2. Clear pycache: `rm -rf /ganuda/lib/__pycache__/`
3. Submit a council vote — check logs for `[CACHE] Lookup failed` or similar (no embeddings yet, so cache miss is expected)
4. Submit the SAME question again — should see `[CACHE HIT]` in logs
5. Submit a `high_stakes` query — should NEVER use cache (always full deliberation)

## Notes

- Cache is NEVER used for `high_stakes` queries — those always get full 7-specialist deliberation
- Similarity threshold 0.92 is intentionally high — only near-duplicate questions hit cache
- 24-hour TTL prevents stale cached answers from persisting
- Minimum confidence 0.85 ensures only high-quality responses are cached
- Cache entries are tagged with `cache-{original_audit_hash}` for audit trail
- The embedding service must be running for cache to function; if down, falls through to full deliberation
