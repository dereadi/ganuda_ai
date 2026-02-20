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
