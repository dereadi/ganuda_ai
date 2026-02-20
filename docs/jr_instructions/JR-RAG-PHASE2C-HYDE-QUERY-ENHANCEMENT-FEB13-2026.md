# Jr Instruction: RAG Phase 2c — HyDE Query Enhancement

**Task**: Add Hypothetical Document Embedding (HyDE) to improve retrieval quality
**Council Vote**: #33e50dc466de520e (RC-2026-02C, 28 pts, 4/7)
**Kanban**: #1768
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**Depends on**: JR-RAG-PHASE2B-CROSS-ENCODER-RERANKING-FEB13-2026.md (rag_reranker.py must exist)

## Context

HyDE (Hypothetical Document Embeddings) improves retrieval by generating a hypothetical answer to the query, then embedding THAT instead of the raw query. The hypothesis is closer in embedding space to real answers than the question is.

Pipeline becomes: Query → LLM generates hypothetical answer → Embed hypothesis → pgvector search → Cross-encoder rerank → Return top results.

The LLM generation uses our local vLLM on redfin:8000.

## Step 1: Create HyDE module

Create `/ganuda/lib/rag_hyde.py`

```python
"""
RAG HyDE — Hypothetical Document Embedding for Cherokee AI Federation

Generates a hypothetical answer using local vLLM, then embeds it for
better semantic retrieval. Falls back to raw query embedding if LLM unavailable.

Council Vote #33e50dc466de520e — Phase 2c of RAG pipeline.
"""

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

VLLM_URL = os.environ.get("VLLM_URL", "http://192.168.132.223:8000/v1/chat/completions")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")
EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/embed")

HYDE_PROMPT = """Write a short paragraph (3-5 sentences) that would be a good answer to the following question. Write it as if it were a factual document excerpt, not a conversational answer. Be specific and use technical terms where appropriate.

Question: {query}

Document excerpt:"""


def generate_hypothesis(query: str, max_tokens: int = 200) -> Optional[str]:
    """Generate a hypothetical answer using local vLLM."""
    try:
        resp = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "user", "content": HYDE_PROMPT.format(query=query)}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("HyDE generation failed: %s", e)
        return None


def get_hyde_embedding(query: str) -> list:
    """Get embedding for a HyDE-enhanced query.

    Generates a hypothetical answer, then embeds it.
    Falls back to embedding the raw query if generation fails.
    """
    hypothesis = generate_hypothesis(query)
    text_to_embed = hypothesis if hypothesis else query

    try:
        resp = requests.post(
            EMBEDDING_URL, json={"text": text_to_embed}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return data["embedding"]
        elif "embeddings" in data:
            return data["embeddings"][0] if data["embeddings"] else []
        return []
    except Exception as e:
        logger.warning("HyDE embedding failed: %s", e)
        return []
```

## Step 2: Wire HyDE into specialist_council.py retrieval

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Get embedding for the question
        embed_resp = requests.post(
            f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
            json={"texts": [question]},
            timeout=10
        )
        if embed_resp.status_code != 200:
            raise Exception(f"Embedding service returned {embed_resp.status_code}")

        embeddings = embed_resp.json().get("embeddings")
        query_embedding = embeddings[0] if embeddings else None
        if not query_embedding:
            raise Exception("No embedding returned")
=======
        # Phase 2c: HyDE — embed hypothetical answer for better retrieval
        query_embedding = None
        try:
            from lib.rag_hyde import get_hyde_embedding
            query_embedding = get_hyde_embedding(question)
            if query_embedding:
                print(f"[RAG] Using HyDE-enhanced embedding ({len(query_embedding)}d)")
        except Exception as e:
            print(f"[RAG] HyDE unavailable, using raw embedding: {e}")

        if not query_embedding:
            embed_resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
                json={"texts": [question]},
                timeout=10
            )
            if embed_resp.status_code != 200:
                raise Exception(f"Embedding service returned {embed_resp.status_code}")

            embeddings = embed_resp.json().get("embeddings")
            query_embedding = embeddings[0] if embeddings else None
            if not query_embedding:
                raise Exception("No embedding returned")
>>>>>>> REPLACE

## Manual Steps

Verify HyDE generates hypothetical answers:

```text
cd /ganuda && python3 -c "
from lib.rag_hyde import generate_hypothesis, get_hyde_embedding
hyp = generate_hypothesis('How do we handle power outages?')
print(f'Hypothesis: {hyp[:200]}...')
emb = get_hyde_embedding('How do we handle power outages?')
print(f'HyDE embedding dims: {len(emb)}')
"
```

After patching specialist_council.py:

```text
sudo rm -rf /ganuda/lib/__pycache__
sudo systemctl restart llm-gateway.service
```

## Success Criteria

- [ ] `generate_hypothesis()` returns a 3-5 sentence hypothetical answer via vLLM
- [ ] `get_hyde_embedding()` embeds the hypothesis (1024d from BGE-large)
- [ ] Falls back to raw query embedding if vLLM or hypothesis fails
- [ ] Council retrieval uses HyDE when available
- [ ] Added latency < 3s (vLLM generation)

---

*For Seven Generations - Cherokee AI Federation*
