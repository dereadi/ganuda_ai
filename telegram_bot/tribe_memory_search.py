"""
Tribe Memory Search — Semantic search for Cherokee AI thermal memories.

Uses BGE-large-en-v1.5 embedding service on greenfin:8003 and
pgvector cosine similarity on thermal_memory_archive.

Council Vote #7ab07bfbd92c70b4 — Full memory access, no filtering.
TPM directive: 2 trusted users, physical security handles opsec.
"""

import json
import logging
import os
from datetime import datetime

import psycopg2
import psycopg2.extras
import requests

logger = logging.getLogger(__name__)

EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/embed")
DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", os.environ.get("PGPASSWORD", ""))
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")


def get_db():
    """Get PostgreSQL connection to bluefin."""
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )


def get_embedding(text: str) -> list:
    """Get BGE-large 1024d embedding from greenfin embedding service."""
    try:
        resp = requests.post(
            EMBEDDING_URL,
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Handle both {"embedding": [...]} and {"embeddings": [[...]]}
        if "embedding" in data:
            return data["embedding"]
        elif "embeddings" in data:
            return data["embeddings"][0] if data["embeddings"] else []
        return []
    except Exception as e:
        logger.warning("Embedding service error: %s", e)
        return []


def semantic_search(query: str, limit: int = 5, min_score: float = 0.3) -> list:
    """Search thermal memories by semantic similarity.

    Args:
        query: Natural language search query
        limit: Max results to return
        min_score: Minimum cosine similarity threshold

    Returns:
        List of dicts with keys: id, content, score, temperature,
        created_at, tags, memory_type
    """
    embedding = get_embedding(query)
    if not embedding:
        logger.warning("No embedding returned, falling back to ILIKE search")
        return text_search(query, limit)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, original_content, temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   created_at, tags, memory_type,
                   contextual_description
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (embedding, embedding, limit))

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
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if results:
            mem_ids = [r["id"] for r in results]
            with conn.cursor() as ucur:
                ucur.execute("""
                    UPDATE thermal_memory_archive
                    SET access_count = COALESCE(access_count, 0) + 1,
                        last_access = NOW()
                    WHERE id = ANY(%s)
                """, (mem_ids,))
            conn.commit()

        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Semantic search failed: %s", e)
        return text_search(query, limit)


def text_search(query: str, limit: int = 5) -> list:
    """Fallback ILIKE text search when embedding service is unavailable."""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, original_content, temperature_score,
                   created_at, tags, memory_type, contextual_description
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (f"%{query}%", limit))

        results = []
        for row in cur.fetchall():
            results.append({
                "id": row["id"],
                "content": row["original_content"],
                "score": 0.5,  # placeholder for text match
                "temperature": row["temperature_score"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "tags": row["tags"] or [],
                "memory_type": row["memory_type"],
                "description": row["contextual_description"],
            })
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if results:
            mem_ids = [r["id"] for r in results]
            with conn.cursor() as ucur:
                ucur.execute("""
                    UPDATE thermal_memory_archive
                    SET access_count = COALESCE(access_count, 0) + 1,
                        last_access = NOW()
                    WHERE id = ANY(%s)
                """, (mem_ids,))
            conn.commit()

        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Text search failed: %s", e)
        return []


def format_for_telegram(results: list, max_chars: int = 3000) -> str:
    """Format search results for Telegram message."""
    if not results:
        return "No matching memories found."

    lines = [f"Found {len(results)} memories:\n"]
    total = 0
    for r in results:
        snippet = r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
        temp = f"{r['temperature']:.0f}" if r["temperature"] else "?"
        line = f"#{r['id']} ({r['score']:.0%} match, {temp} deg)\n{snippet}\n"
        if total + len(line) > max_chars:
            lines.append(f"... and {len(results) - len(lines) + 1} more")
            break
        lines.append(line)
        total += len(line)

    return "\n".join(lines)


def format_for_llm(results: list, max_chars: int = 4000) -> str:
    """Format search results as context injection for LLM conversations."""
    if not results:
        return ""

    parts = ["[Tribe Memory Context]"]
    total = 0
    for r in results:
        snippet = r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"]
        entry = f"Memory #{r['id']} (relevance: {r['score']:.0%}, temp: {r['temperature']:.0f}):\n{snippet}"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)

    return "\n\n".join(parts)