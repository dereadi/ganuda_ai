# Jr Instruction: Constructal Law — Structured Memory Extraction via Mem0

**Task ID**: CONSTRUCTAL-MEM0-001
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false
**Council Vote**: #0352a767e34d2088 (Constructal Law Trio, RC-2026-02F)
**Kanban**: #1795

## Context

The council's thermal memory pipeline (HyDE → pgvector → Cross-encoder → Sufficiency → CRAG) retrieves relevant memories as raw prose — 800 chars each. This wastes token budget on verbose context. A 5-memory injection costs ~4000 tokens but delivers only ~20 facts.

**Goal**: Extract structured key-value facts from council deliberation prose, store them compactly in thermal_memory_archive metadata, and inject 3-5x more context per token when retrieved.

**Constraints** (Gecko): Must use existing vLLM calls, zero additional compute beyond one extraction call per vote.

## Step 1: Add structured fact extraction to mem0_bridge.py

File: `/ganuda/lib/mem0_bridge.py`

<<<<<<< SEARCH
def search_user_memories(query: str, user_id: str = "tribe",
                         limit: int = 5) -> List[Dict]:
=======
def extract_structured_facts(prose: str, source_hash: str,
                              vllm_url: str = "http://192.168.132.223:8000/v1/chat/completions",
                              vllm_model: str = None) -> List[Dict]:
    """Extract structured key-value facts from council deliberation prose.

    Uses a single vLLM call to compress verbose prose into compact fact triples.
    Each fact is: {subject, predicate, object} — e.g., {"s": "redfin", "p": "runs", "o": "vLLM Qwen2.5-72B on port 8000"}

    Returns list of fact dicts. Stores nothing — caller decides storage.
    Council Vote #0352a767e34d2088 (Constructal Law).
    """
    import requests as _req

    if not vllm_model:
        vllm_model = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")

    extraction_prompt = (
        "Extract structured facts from the following text as JSON. "
        "Return ONLY a JSON array of objects, each with keys: s (subject), p (predicate), o (object). "
        "Each fact should be a single atomic statement. "
        "Compress verbose descriptions into concise key-value form. "
        "Example: [{\"s\": \"greenfin\", \"p\": \"hosts\", \"o\": \"OpenObserve on port 5601\"}, "
        "{\"s\": \"council\", \"p\": \"voted\", \"o\": \"PROCEED WITH CAUTION 0.858\"}]\n\n"
        f"Text:\n{prose[:2000]}"
    )

    try:
        resp = _req.post(vllm_url, json={
            "model": vllm_model,
            "messages": [
                {"role": "system", "content": "You extract structured facts from text. Return only valid JSON arrays."},
                {"role": "user", "content": extraction_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON from response — handle markdown code fences
        import json as _json
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            cleaned = cleaned.rsplit("```", 1)[0]
        facts = _json.loads(cleaned.strip())
        if not isinstance(facts, list):
            facts = [facts]
        return [f for f in facts if isinstance(f, dict) and "s" in f and "p" in f and "o" in f]
    except Exception as e:
        logger.error("Structured fact extraction failed: %s", e)
        return []


def store_structured_facts(facts: List[Dict], source_hash: str,
                            source_type: str = "council_vote") -> int:
    """Store extracted facts as structured metadata on the source thermal memory.

    Updates the source memory's metadata.structured_facts field.
    Also creates a compact TEXT representation for embedding search.

    Returns count of facts stored.
    """
    if not facts:
        return 0

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Compact text representation for search
        compact_lines = [f"{f['s']} {f['p']} {f['o']}" for f in facts]
        compact_text = "; ".join(compact_lines)

        # Update source memory's metadata with structured facts
        cur.execute("""
            UPDATE thermal_memory_archive
            SET metadata = COALESCE(metadata, '{}'::jsonb) ||
                jsonb_build_object(
                    'structured_facts', %s::jsonb,
                    'fact_count', %s,
                    'compact_text', %s
                )
            WHERE memory_hash = %s
        """, (Json(facts), len(facts), compact_text, source_hash))

        rows_updated = cur.rowcount
        conn.commit()
        conn.close()

        if rows_updated > 0:
            logger.info("Stored %d structured facts for memory %s", len(facts), source_hash[:8])
        return len(facts)
    except Exception as e:
        logger.error("Failed to store structured facts: %s", e)
        return 0


def search_user_memories(query: str, user_id: str = "tribe",
                         limit: int = 5) -> List[Dict]:
>>>>>>> REPLACE

## Step 2: Add post-vote fact extraction hook in specialist_council.py

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Log to database with routing manifest + rubric data
        self._log_vote(vote, routing_manifest=routing_manifest, rubric_data=rubric_data)

        return vote
=======
        # Log to database with routing manifest + rubric data
        self._log_vote(vote, routing_manifest=routing_manifest, rubric_data=rubric_data)

        # Constructal Law: Extract structured facts from deliberation (Council Vote #0352a767)
        # One vLLM call per vote — compresses prose into searchable fact triples.
        try:
            from lib.mem0_bridge import extract_structured_facts, store_structured_facts
            deliberation_prose = f"QUESTION: {question}\nCONSENSUS: {consensus}\nRECOMMENDATION: {recommendation}"
            facts = extract_structured_facts(deliberation_prose, vote.audit_hash)
            if facts:
                stored = store_structured_facts(facts, vote.audit_hash, source_type="council_vote")
                print(f"[CONSTRUCTAL] Extracted {len(facts)} facts, stored {stored} for vote {vote.audit_hash}")
        except Exception as e:
            print(f"[CONSTRUCTAL] Fact extraction skipped (non-fatal): {e}")

        return vote
>>>>>>> REPLACE

## Step 3: Add compact context retrieval function in specialist_council.py

This adds a helper that retrieves structured facts when available, falling back to raw prose. Called from the thermal memory injection in `vote()`.

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
def _ripple_retrieve(primary_hashes: list, conn, max_hops: int = 2, decay: float = 0.7, threshold: float = 0.1) -> list:
=======
def _format_memory_compact(mem_id: int, content: str, temp: float, score: float, metadata_json: str = None) -> str:
    """Format a memory for council context, preferring compact structured facts.

    If the memory has structured_facts in metadata, render as compact fact list.
    Otherwise fall back to raw prose (truncated to 800 chars as before).
    Constructal Law: reduce resistance in information flow.
    """
    if metadata_json:
        try:
            import json as _json
            meta = _json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            compact = meta.get("compact_text")
            if compact:
                return f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f} | STRUCTURED]\n{compact}"
        except Exception:
            pass
    return f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]\n{content}"


def _ripple_retrieve(primary_hashes: list, conn, max_hops: int = 2, decay: float = 0.7, threshold: float = 0.1) -> list:
>>>>>>> REPLACE

## Step 4: Use compact format in memory retrieval

Update the retrieval loop to fetch metadata and use compact formatting when available.

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Semantic search via pgvector
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
=======
        # Semantic search via pgvector (with metadata for Constructal structured facts)
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred,
                   metadata
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
>>>>>>> REPLACE

## Step 5: Update row unpacking to include metadata

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        adjusted_rows = []
        for row in rows:
            mem_id, content, temp, sim = row[0], row[1], row[2], row[3]
            acc_count = row[4] if len(row) > 4 else 0
            is_sacred = row[5] if len(row) > 5 else False
            if is_sacred or acc_count <= 2:
                adjusted_rows.append((mem_id, content, temp, sim))
            else:
                penalty = min((acc_count - 2) * 0.02, 0.30)
                adjusted_sim = sim * (1.0 - penalty)
                adjusted_rows.append((mem_id, content, temp, adjusted_sim))
        rows = adjusted_rows
=======
        adjusted_rows = []
        for row in rows:
            mem_id, content, temp, sim = row[0], row[1], row[2], row[3]
            acc_count = row[4] if len(row) > 4 else 0
            is_sacred = row[5] if len(row) > 5 else False
            meta = row[6] if len(row) > 6 else None
            if is_sacred or acc_count <= 2:
                adjusted_rows.append((mem_id, content, temp, sim, meta))
            else:
                penalty = min((acc_count - 2) * 0.02, 0.30)
                adjusted_sim = sim * (1.0 - penalty)
                adjusted_rows.append((mem_id, content, temp, adjusted_sim, meta))
        rows = adjusted_rows
>>>>>>> REPLACE

## Step 6: Use compact format in context building

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if crag_note:
            context_parts.append(crag_note)
        if sufficiency_note:
            context_parts.append(sufficiency_note)
        for row in rows:
            mem_id, content, temp, score = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]")
            context_parts.append(content)
=======
        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if crag_note:
            context_parts.append(crag_note)
        if sufficiency_note:
            context_parts.append(sufficiency_note)
        structured_count = 0
        for row in rows:
            mem_id, content, temp, score = row[0], row[1], row[2], row[3]
            meta = row[4] if len(row) > 4 else None
            formatted = _format_memory_compact(mem_id, content, temp, score, meta)
            if "STRUCTURED" in formatted:
                structured_count += 1
            context_parts.append(formatted)
        if structured_count > 0:
            print(f"[CONSTRUCTAL] {structured_count}/{len(rows)} memories served as compact structured facts")
>>>>>>> REPLACE

## Verification

After deployment, test with:

```text
curl -s http://localhost:8080/council/vote -X POST -H "Content-Type: application/json" -d '{"question": "What is the current state of our monitoring stack?"}' | python3 -m json.tool
```

Look for in gateway logs:
- `[CONSTRUCTAL] Extracted N facts, stored N for vote XXXX`
- `[CONSTRUCTAL] N/M memories served as compact structured facts`

Query DB to verify fact storage:
```text
SELECT id, memory_hash, metadata->'structured_facts' as facts, metadata->'fact_count' as n
FROM thermal_memory_archive
WHERE metadata->>'structured_facts' IS NOT NULL
ORDER BY id DESC LIMIT 5;
```

## Manual Steps (TPM on redfin)

1. After Jr applies changes: `sudo -n ganuda-service-ctl restart llm-gateway`
2. Clear pycache: `rm -rf /ganuda/scripts/__pycache__ /ganuda/lib/__pycache__`
3. Run a test council vote and verify structured facts appear in DB
