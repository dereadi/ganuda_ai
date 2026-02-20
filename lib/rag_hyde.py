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
VLLM_MODEL = os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq")
EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/v1/embeddings")

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
            timeout=5,
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
            EMBEDDING_URL, json={"texts": [text_to_embed]}, timeout=10
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