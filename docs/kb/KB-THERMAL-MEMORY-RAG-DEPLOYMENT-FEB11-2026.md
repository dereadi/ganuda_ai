# KB: Thermal Memory RAG — Semantic Search Deployment

**Date**: February 11, 2026
**Severity**: Enhancement — HIGH priority (#1760)
**Related**: Kanban #1760, Jr Task #699 (partial), Council Vote #8526
**Supersedes**: Text LoRA approach (DEPRIORITIZED per KB-LORA-COUNCIL-DELIBERATION)

---

## Summary

Deployed semantic search over 78K thermal memories using pgvector embeddings. Every council vote now automatically retrieves relevant thermal memories and injects them as context into specialist prompts. This replaces the text LoRA approach — cheaper, faster, no fine-tuning needed.

## Architecture

```
Council Vote Request
    |
specialist_council.py vote()
    |
query_thermal_memory_semantic(question)
    | (primary)                    | (fallback)
Embedding Server                Keyword ILIKE search
greenfin:8003                   bluefin PostgreSQL
BGE-large-en-v1.5               top 5 by temperature_score
1024-dim cosine similarity
    |
enriched_question = question + thermal_context
    |
7 specialists get enriched prompt
```

## Components

### 1. Schema Migration (Jr #699 Step 1 — SUCCEEDED)
```sql
ALTER TABLE thermal_memory_archive ADD COLUMN embedding vector(1024);
CREATE INDEX idx_thermal_memory_embedding ON thermal_memory_archive
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_thermal_memory_sacred ON thermal_memory_archive (sacred_pattern)
  WHERE sacred_pattern = true;
```

### 2. Embedding Server (greenfin:8003)
- **Model**: BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Framework**: FastAPI + SentenceTransformers
- **Endpoints**: /health, /v1/embeddings, /v1/search, /v1/index
- **Memory**: ~1.5GB at rest, 4GB max
- **File**: /ganuda/services/embedding_service/embedding_server.py
- **Systemd**: cherokee-embedding-server.service (STAGED, needs sudo deploy)

### 3. Semantic Search Function (specialist_council.py)
- `query_thermal_memory_semantic(question, limit=5)` — sends question to embedding server, gets top-N similar memories by cosine distance
- `_keyword_fallback(question, limit=5)` — ILIKE search on original_content, ordered by temperature_score DESC
- Graceful degradation: if embedding server unavailable (timeout, backfill busy), falls back to keyword search automatically

### 4. Vote Flow Integration (specialist_council.py)
- Before specialist queries, retrieves thermal context
- Constructs enriched_question with separator and memory citations
- All 7 specialists receive the enriched context
- Non-fatal: RAG failure does not block the vote

### 5. Backfill (78K memories)
- Via /v1/index endpoint on embedding server
- Progress: started Feb 11, processing ~200 memories/min
- Batches of 100, commits after each batch
- During backfill, semantic search falls back to keyword (server busy)

## API Contract

Embedding Server expects:
```
POST /v1/embeddings
Body: {"texts": ["list of strings"]}

Response: {"embeddings": [[1024 floats], ...], "model": "BAAI/bge-large-en-v1.5"}
```

**Important**: Server expects `texts` (list), NOT `text` (string). This caused an initial mismatch that was fixed in specialist_council.py.

## Firewall

- redfin (192.168.132.223) to greenfin (192.168.132.224):8003
- Rule: `sudo nft add rule inet filter input ip saddr 192.168.132.223 tcp dport 8003 accept`
- **Must persist**: `sudo nft list ruleset | sudo tee /etc/nftables.conf`

## Failure Modes

| Failure | Behavior | Fix |
|---------|----------|-----|
| Embedding server down | Keyword fallback | Restart service on greenfin |
| Embedding server busy (backfill) | Keyword fallback | Wait for backfill |
| No matching memories | Empty context, vote proceeds | Expected for novel topics |
| Database connection failure | RAG skipped, vote proceeds | Check connectivity |
| API mismatch (text vs texts) | 422 error | Use texts list format |

## Jr Task #699 Lessons

- Step 1 (SQL migration): Jr executed perfectly
- Step 2 (specialist_council.py edit): Jr FAILED — 50% guardrail blocked it
- Resolution: TPM applied Step 2 edits directly as partner work
- Pattern: See KB-JR-EXECUTOR-SR-LARGE-FILE-FAILURE-PATTERN-FEB11-2026.md

## Monitoring

Check embedding coverage:
```
SELECT COUNT(*) AS total, COUNT(embedding) AS with_embedding,
       ROUND(COUNT(embedding)::numeric / COUNT(*)::numeric * 100, 1) AS pct
FROM thermal_memory_archive;
```

Check RAG in council votes: look for "[RAG] Injected N thermal memories" in gateway logs.

## Related

- KB-LORA-COUNCIL-DELIBERATION-FEB10-2026.md (LoRA deprioritized in favor of RAG)
- KB-JR-EXECUTOR-SR-LARGE-FILE-FAILURE-PATTERN-FEB11-2026.md (Jr task failure)
- KB-JR-DUAL-PIPELINE-ARCHITECTURE-FEB11-2026.md (Pipeline A vs B)
