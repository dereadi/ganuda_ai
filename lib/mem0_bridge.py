"""
Mem0 ↔ Thermal Memory Bridge — Cherokee AI Federation

Syncs Mem0 extracted memories into the tribe's thermal_memory_archive.
Mem0 handles extraction/dedup, thermal archive handles temperature/sacred patterns.

Council Vote #33e50dc466de520e — RC-2026-02C.
"""

import hashlib
import logging
import os
from typing import List, Dict, Optional

import psycopg2
from psycopg2.extras import Json

from lib.secrets_loader import get_db_config

logger = logging.getLogger(__name__)
DB_CONFIG = get_db_config()


def extract_and_store(messages: List[Dict], user_id: str = "tribe",
                      agent_id: str = "mem0_bridge",
                      initial_temperature: float = 75.0) -> Dict:
    """Extract memories from conversation and store in thermal archive.

    Args:
        messages: List of {"role": "user"/"assistant", "content": "..."} dicts
        user_id: Mem0 user scope (e.g., "darrell", "joe", "tribe")
        agent_id: Who triggered the extraction
        initial_temperature: Starting temp for new memories (75 = warm)

    Returns:
        Dict with counts: extracted, new, updated, errors
    """
    from lib.mem0_config import get_memory_instance

    mem = get_memory_instance()
    if mem is None:
        return {"error": "Mem0 not available"}

    # Let Mem0 extract memories from the conversation
    result = mem.add(messages, user_id=user_id)
    extracted = result.get("results", []) if isinstance(result, dict) else []

    new_count = 0
    updated_count = 0
    errors = 0

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        for memory_entry in extracted:
            memory_text = memory_entry.get("memory", "")
            if not memory_text or len(memory_text) < 10:
                continue

            memory_hash = hashlib.sha256(memory_text.encode()).hexdigest()

            try:
                with conn.cursor() as cur:
                    # Check if this memory already exists (dedup)
                    cur.execute(
                        "SELECT id, temperature_score FROM thermal_memory_archive WHERE memory_hash = %s",
                        (memory_hash,)
                    )
                    existing = cur.fetchone()

                    if existing:
                        # Reheat existing memory (it was mentioned again)
                        cur.execute("""
                            UPDATE thermal_memory_archive
                            SET temperature_score = LEAST(temperature_score + 5, 100),
                                last_access = NOW(),
                                access_count = access_count + 1
                            WHERE memory_hash = %s
                        """, (memory_hash,))
                        updated_count += 1
                    else:
                        # Insert new thermal memory
                        cur.execute("""
                            INSERT INTO thermal_memory_archive
                                (memory_hash, original_content, temperature_score,
                                 memory_type, metadata, tags)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            memory_hash,
                            memory_text,
                            initial_temperature,
                            "episodic",
                            Json({
                                "source": "mem0_extraction",
                                "user_id": user_id,
                                "agent_id": agent_id,
                                "mem0_event": memory_entry.get("event", "ADD"),
                            }),
                            ["mem0", "auto_extracted", user_id],
                        ))
                        new_count += 1

                conn.commit()
            except Exception as e:
                logger.error("Failed to store memory: %s", e)
                conn.rollback()
                errors += 1
    finally:
        conn.close()

    return {
        "extracted": len(extracted),
        "new": new_count,
        "updated": updated_count,
        "errors": errors,
    }


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
        vllm_model = os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq")

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
    """Search memories scoped to a specific user via Mem0."""
    from lib.mem0_config import get_memory_instance

    mem = get_memory_instance()
    if mem is None:
        return []

    try:
        results = mem.search(query=query, user_id=user_id, limit=limit)
        return results.get("results", []) if isinstance(results, dict) else results
    except Exception as e:
        logger.error("Mem0 search failed: %s", e)
        return []