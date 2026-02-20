# Jr Instruction: RAG Phase 2b — Cross-Encoder Reranking

**Task**: Add cross-encoder reranking to semantic retrieval (retrieve 10, rerank to top 3)
**Council Vote**: #33e50dc466de520e (RC-2026-02C, 39 pts, 6/7)
**Kanban**: #1767
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8

## Context

Currently `query_thermal_memory_semantic()` in specialist_council.py retrieves the top-5 memories by pgvector cosine distance and passes them directly to the council. Bi-encoder (embedding) retrieval is fast but imprecise — it can miss nuance.

Cross-encoder reranking is the standard RAG improvement: retrieve a broader set (top 10-20), then use a cross-encoder model to precisely score each (query, document) pair and return only the best 3-5.

The reranking module should be a shared service that both `specialist_council.py` and `tribe_memory_search.py` can call.

## Step 1: Create the reranker module

Create `/ganuda/lib/rag_reranker.py`

```python
"""
RAG Cross-Encoder Reranker — Cherokee AI Federation

Two-stage retrieval: bi-encoder (fast, broad) → cross-encoder (precise, narrow).
Uses ms-marco-MiniLM-L-6-v2 for reranking (runs on CPU, ~80MB).

Council Vote #33e50dc466de520e — Phase 2b of RAG pipeline.
"""

import logging
import os
from typing import List, Tuple

logger = logging.getLogger(__name__)

RERANKER_MODEL = None
RERANKER_MODEL_NAME = os.environ.get(
    "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def get_reranker():
    """Lazy-load cross-encoder model (CPU, ~80MB RAM)."""
    global RERANKER_MODEL
    if RERANKER_MODEL is None:
        try:
            from sentence_transformers import CrossEncoder
            RERANKER_MODEL = CrossEncoder(RERANKER_MODEL_NAME)
            logger.info("Cross-encoder loaded: %s", RERANKER_MODEL_NAME)
        except Exception as e:
            logger.error("Failed to load cross-encoder: %s", e)
            return None
    return RERANKER_MODEL


def rerank(query: str, documents: List[dict], content_key: str = "content",
           top_k: int = 3) -> List[dict]:
    """Rerank documents using cross-encoder relevance scoring.

    Args:
        query: The user's search query
        documents: List of dicts, each must have content_key field
        content_key: Key in each dict containing the text to score
        top_k: Number of top results to return after reranking

    Returns:
        Top-k documents sorted by cross-encoder score, with 'rerank_score' added.
        Falls back to original order if reranker unavailable.
    """
    if not documents:
        return []

    model = get_reranker()
    if model is None:
        logger.warning("Reranker unavailable, returning original order")
        return documents[:top_k]

    try:
        pairs = [(query, doc.get(content_key, "")[:1000]) for doc in documents]
        scores = model.predict(pairs)

        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        ranked = sorted(documents, key=lambda d: d["rerank_score"], reverse=True)
        return ranked[:top_k]
    except Exception as e:
        logger.error("Reranking failed: %s", e)
        return documents[:top_k]
```

## Step 2: Wire reranker into specialist_council.py semantic retrieval

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
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
=======
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 2b: Cross-encoder reranking (retrieve broad, rerank precise)
        try:
            from lib.rag_reranker import rerank
            docs = [{"id": r[0], "content": r[1], "temp": r[2], "sim": r[3]} for r in rows]
            reranked = rerank(question, docs, content_key="content", top_k=min(5, len(docs)))
            if reranked:
                rows = [(d["id"], d["content"], d["temp"], d.get("rerank_score", d["sim"])) for d in reranked]
        except Exception as e:
            print(f"[RAG] Reranking skipped (non-fatal): {e}")

        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        for row in rows:
            mem_id, content, temp, score = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]")
            context_parts.append(content)

        return "\n".join(context_parts)
>>>>>>> REPLACE

## Step 3: Increase initial retrieval to 15 (broader pool for reranking)

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
def query_thermal_memory_semantic(question: str, limit: int = 5, min_temperature: float = 30.0) -> str:
=======
def query_thermal_memory_semantic(question: str, limit: int = 15, min_temperature: float = 30.0) -> str:
>>>>>>> REPLACE

## Step 4: Wire reranker into tribe_memory_search.py

File: `/ganuda/telegram_bot/tribe_memory_search.py`

<<<<<<< SEARCH
        results = []
        for row in cur.fetchall():
            score = float(row["similarity"]) if row["similarity"] else 0
            if score >= min_score:
                results.append({
                    "id": row["id"],
                    "content": row["original_content"],
                    "score": round(score, 3),
                    "temperature": row["temperature_score"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "tags": row["tags"] or [],
                    "memory_type": row["memory_type"],
                    "description": row["contextual_description"],
                })
        cur.close()
        conn.close()
        return results
=======
        results = []
        for row in cur.fetchall():
            score = float(row["similarity"]) if row["similarity"] else 0
            if score >= min_score:
                results.append({
                    "id": row["id"],
                    "content": row["original_content"],
                    "score": round(score, 3),
                    "temperature": row["temperature_score"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "tags": row["tags"] or [],
                    "memory_type": row["memory_type"],
                    "description": row["contextual_description"],
                })
        cur.close()
        conn.close()

        # Phase 2b: Cross-encoder reranking if available
        if results and len(results) > 3:
            try:
                import sys
                sys.path.insert(0, "/ganuda")
                from lib.rag_reranker import rerank
                reranked = rerank(query, results, content_key="content", top_k=limit)
                if reranked:
                    for r in reranked:
                        if "rerank_score" in r:
                            r["score"] = round(r.pop("rerank_score"), 3)
                    results = reranked
            except Exception as e:
                logger.debug("Reranking skipped: %s", e)

        return results
>>>>>>> REPLACE

## Manual Steps

Install cross-encoder model on redfin (one time):

```text
/home/dereadi/cherokee_venv/bin/pip install sentence-transformers
```

Verify reranker loads:

```text
cd /ganuda && python3 -c "
from lib.rag_reranker import rerank
docs = [
    {'content': 'Power outage recovery procedure for Cherokee AI'},
    {'content': 'VetAssist frontend build configuration'},
    {'content': 'UPS battery monitoring and Telegram alerts'},
]
result = rerank('power failure', docs, top_k=2)
for r in result:
    print(f'{r[\"rerank_score\"]:.3f} — {r[\"content\"][:60]}')
"
```

After patching specialist_council.py, clear pycache and restart gateway:

```text
sudo rm -rf /ganuda/scripts/__pycache__ /ganuda/lib/__pycache__
sudo systemctl restart llm-gateway.service
```

## Success Criteria

- [ ] `rag_reranker.py` loads cross-encoder model on first call (~2s cold start)
- [ ] `rerank()` returns top-k docs sorted by cross-encoder score
- [ ] Council retrieval fetches 15 candidates, reranks to top 5
- [ ] Telegram search reranks results when >3 candidates
- [ ] Graceful fallback: if reranker fails, original order preserved
- [ ] Gateway restart after pycache clear

---

*For Seven Generations - Cherokee AI Federation*
