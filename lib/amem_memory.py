#!/usr/bin/env python3
"""
A-MEM Memory System for Cherokee AI Federation
Based on arXiv:2502.12110 - Agentic Memory for LLM Agents

Implements Zettelkasten-style memory linking for thermal_memory_archive.
"""

import logging
import os
import psycopg2
import psycopg2.extras
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import requests

from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

logger = logging.getLogger(__name__)

EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/v1/embeddings")

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from content using simple TF-based extraction."""
    import re
    from collections import Counter

    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'between', 'under', 'again', 'further',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                 'because', 'until', 'while', 'this', 'that', 'these', 'those'}

    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content.lower())
    words = [w for w in words if w not in stopwords and len(w) > 2]

    counter = Counter(words)
    return [word for word, _ in counter.most_common(max_keywords)]


def extract_tags(content: str) -> List[str]:
    """Extract category tags based on content patterns."""
    tags = []
    content_lower = content.lower()

    if any(node in content_lower for node in ['redfin', 'bluefin', 'greenfin', 'sasass', 'bmasass']):
        tags.append('infrastructure')
    if 'telegram' in content_lower:
        tags.append('telegram')
    if 'gateway' in content_lower or 'llm' in content_lower:
        tags.append('llm_gateway')
    if 'thermal' in content_lower or 'memory' in content_lower:
        tags.append('thermal_memory')
    if 'jr' in content_lower or 'agent' in content_lower:
        tags.append('jr_agents')
    if 'council' in content_lower:
        tags.append('council')
    if 'error' in content_lower or 'fail' in content_lower:
        tags.append('error')
    if 'success' in content_lower or 'complete' in content_lower:
        tags.append('success')
    if 'deploy' in content_lower:
        tags.append('deployment')
    if 'task' in content_lower:
        tags.append('task')
    if 'research' in content_lower or 'arxiv' in content_lower:
        tags.append('research')
    if 'plan' in content_lower or 'roadmap' in content_lower:
        tags.append('planning')

    return list(set(tags)) or ['general']


def generate_contextual_description(content: str, keywords: List[str]) -> str:
    """Generate a contextual description summarizing the memory."""
    summary = content[:200].strip()
    if len(content) > 200:
        summary += "..."
    keyword_str = ", ".join(keywords[:5]) if keywords else "general"
    return f"Memory about {keyword_str}. {summary}"


def compute_embedding(text: str) -> List[float]:
    """Get BGE-large 1024d embedding from greenfin embedding service."""
    try:
        resp = requests.post(EMBEDDING_URL, json={"texts": [text]}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return data["embedding"]
        elif "embeddings" in data:
            return data["embeddings"][0] if data["embeddings"] else []
        return []
    except Exception as e:
        logger.warning("Embedding service error: %s", e)
        return []


def find_similar_memories(embedding: List[float], limit: int = 5, exclude_hash: str = None) -> List[Tuple[str, float]]:
    """Find similar memories using pgvector cosine distance on BGE-large embeddings."""
    if not embedding:
        return []

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash,
                       1 - (embedding <=> %s::vector) as similarity
                FROM thermal_memory_archive
                WHERE embedding IS NOT NULL
                AND memory_hash != COALESCE(%s, '')
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding, exclude_hash, embedding, limit))
            results = [(row[0], float(row[1])) for row in cur.fetchall() if row[1] > 0.5]
        return results
    except Exception as e:
        logger.error("pgvector similarity search failed: %s", e)
        return []
    finally:
        conn.close()


def create_memory_links(source_hash: str, similar_memories: List[Tuple[str, float]], agent_id: str = 'amem_system') -> int:
    """Create bidirectional links between memories."""
    if not similar_memories:
        return 0

    conn = get_connection()
    links_created = 0

    with conn.cursor() as cur:
        for target_hash, similarity in similar_memories:
            try:
                cur.execute("""
                    INSERT INTO memory_links (source_hash, target_hash, similarity_score, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_hash, target_hash) DO UPDATE
                    SET similarity_score = EXCLUDED.similarity_score
                """, (source_hash, target_hash, similarity, agent_id))

                cur.execute("""
                    INSERT INTO memory_links (source_hash, target_hash, similarity_score, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_hash, target_hash) DO NOTHING
                """, (target_hash, source_hash, similarity, agent_id))

                links_created += 1
            except Exception as e:
                print(f"Link creation error: {e}")

        cur.execute("""
            UPDATE thermal_memory_archive
            SET linked_memories = (
                SELECT ARRAY_AGG(target_hash)
                FROM memory_links
                WHERE source_hash = %s
            )
            WHERE memory_hash = %s
        """, (source_hash, source_hash))

        conn.commit()

    conn.close()
    return links_created


def enrich_memory(memory_hash: str, content: str, agent_id: str = 'amem_system') -> Dict:
    """Enrich an existing memory with A-MEM attributes."""
    keywords = extract_keywords(content)
    tags = extract_tags(content)
    context_desc = generate_contextual_description(content, keywords)
    embedding = compute_embedding(content)

    similar = find_similar_memories(embedding, limit=5, exclude_hash=memory_hash)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE thermal_memory_archive
            SET keywords = %s, tags = %s, contextual_description = %s,
                embedding = %s::vector
            WHERE memory_hash = %s
        """, (keywords, tags, context_desc, embedding, memory_hash))
        conn.commit()
    conn.close()

    links_created = create_memory_links(memory_hash, similar, agent_id)

    return {
        'memory_hash': memory_hash,
        'keywords': keywords,
        'tags': tags,
        'contextual_description': context_desc,
        'similar_memories': len(similar),
        'links_created': links_created
    }


def get_linked_context(memory_hash: str, depth: int = 1) -> List[Dict]:
    """Get linked memories for context enrichment."""
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if depth == 1:
            cur.execute("""
                SELECT t.memory_hash, t.original_content, t.temperature_score,
                       t.keywords, t.tags, l.similarity_score
                FROM thermal_memory_archive t
                JOIN memory_links l ON t.memory_hash = l.target_hash
                WHERE l.source_hash = %s
                ORDER BY l.similarity_score DESC
                LIMIT 5
            """, (memory_hash,))
        else:
            cur.execute("""
                WITH RECURSIVE linked AS (
                    SELECT target_hash, 1 as depth, similarity_score
                    FROM memory_links WHERE source_hash = %s
                    UNION
                    SELECT l.target_hash, linked.depth + 1, l.similarity_score
                    FROM memory_links l
                    JOIN linked ON l.source_hash = linked.target_hash
                    WHERE linked.depth < %s
                )
                SELECT DISTINCT t.memory_hash, t.original_content, t.temperature_score,
                       t.keywords, t.tags, linked.similarity_score, linked.depth
                FROM thermal_memory_archive t
                JOIN linked ON t.memory_hash = linked.target_hash
                ORDER BY linked.depth, linked.similarity_score DESC
                LIMIT 10
            """, (memory_hash, depth))

        results = cur.fetchall()

    conn.close()
    return [dict(r) for r in results]


def backfill_existing_memories(batch_size: int = 100, agent_id: str = 'amem_backfill') -> Dict:
    """Backfill A-MEM attributes for existing memories."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT memory_hash, original_content
            FROM thermal_memory_archive
            WHERE contextual_description IS NULL
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (batch_size,))
        memories = cur.fetchall()

    conn.close()

    processed = 0
    errors = 0

    for memory_hash, content in memories:
        try:
            enrich_memory(memory_hash, content, agent_id)
            processed += 1
        except Exception as e:
            print(f"Error processing {memory_hash}: {e}")
            errors += 1

    return {
        'processed': processed,
        'errors': errors,
        'remaining': len(memories) == batch_size
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'backfill':
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        result = backfill_existing_memories(batch_size)
        print(f"Backfill result: {result}")
    else:
        print("A-MEM Memory System")
        print("Usage: python amem_memory.py backfill [batch_size]")
