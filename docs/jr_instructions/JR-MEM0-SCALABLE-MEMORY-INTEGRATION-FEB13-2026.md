# Jr Instruction: Mem0 Scalable Long-term Memory Integration

**Task**: Integrate Mem0 as memory extraction/consolidation layer atop thermal memory archive
**Council Vote**: #33e50dc466de520e (RC-2026-02C, unanimous 7/7, 61 pts)
**Kanban**: #1706
**Priority**: 2 (P0 — council unanimous)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8

## Context

The federation already has 80K+ thermal memories, pgvector embeddings, and A-MEM linking. What we lack is **automatic memory extraction from conversations**. Currently memories are manually seeded via /seed command or TPM inserts.

Mem0 (https://github.com/mem0ai/mem0) is a production-ready memory layer that automatically:
1. Extracts key facts from conversations
2. Deduplicates against existing memories
3. Updates/merges when facts change
4. Supports per-user scoping

We integrate Mem0 as an EXTRACTION layer that feeds into our existing thermal_memory_archive — NOT as a replacement.

Configuration: Use our local vLLM (Qwen 72B) as the LLM provider and our pgvector on bluefin as the vector store.

## Step 1: Create Mem0 configuration wrapper

Create `/ganuda/lib/mem0_config.py`

```python
"""
Mem0 Configuration for Cherokee AI Federation

Wraps Mem0 to use our local infrastructure:
- LLM: vLLM on redfin:8000 (Qwen2.5-72B via OpenAI-compatible API)
- Embedder: BGE-large on greenfin:8003
- Vector Store: pgvector on bluefin (thermal_memory_archive)

Council Vote #33e50dc466de520e — RC-2026-02C.
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_mem0_config() -> dict:
    """Build Mem0 config using federation infrastructure."""
    db_host = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
    db_user = os.environ.get("CHEROKEE_DB_USER", "claude")
    db_pass = os.environ.get("CHEROKEE_DB_PASS", os.environ.get("PGPASSWORD", ""))
    db_name = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")

    return {
        "llm": {
            "provider": "openai",
            "config": {
                "model": os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ"),
                "api_key": "not-needed",
                "openai_base_url": os.environ.get("VLLM_BASE_URL", "http://192.168.132.223:8000/v1"),
                "temperature": 0.3,
                "max_tokens": 500,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "bge-large-en-v1.5",
                "api_key": "not-needed",
                "openai_base_url": os.environ.get("EMBEDDING_BASE_URL", "http://192.168.132.224:8003"),
                "embedding_dims": 1024,
            },
        },
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": db_host,
                "port": 5432,
                "user": db_user,
                "password": db_pass,
                "dbname": db_name,
                "collection_name": "mem0_memories",
            },
        },
        "version": "v1.1",
    }


def get_memory_instance():
    """Get a configured Mem0 Memory instance."""
    try:
        from mem0 import Memory
        config = get_mem0_config()
        return Memory.from_config(config)
    except ImportError:
        logger.error("mem0 not installed. Run: pip install mem0ai")
        return None
    except Exception as e:
        logger.error("Failed to initialize Mem0: %s", e)
        return None
```

## Step 2: Create bridge to thermal memory archive

Create `/ganuda/lib/mem0_bridge.py`

```python
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
```

## Manual Steps

Install mem0 on redfin:

```text
/home/dereadi/cherokee_venv/bin/pip install mem0ai
```

Verify configuration works:

```text
cd /ganuda && python3 -c "
from lib.mem0_config import get_mem0_config
import json
config = get_mem0_config()
print(json.dumps(config, indent=2, default=str))
"
```

Test extraction with a sample conversation:

```text
cd /ganuda && python3 -c "
from lib.mem0_bridge import extract_and_store
result = extract_and_store([
    {'role': 'user', 'content': 'The Solix 3800 Plus UPS is now monitored via REST API polling every 10 minutes'},
    {'role': 'assistant', 'content': 'Understood. The power monitor daemon on greenfin checks PV STATUS and sends Telegram alerts on discharge.'}
], user_id='darrell')
print(f'Extraction result: {result}')
"
```

## Important Notes

- Mem0 creates its OWN table (`mem0_memories`) for its internal index — this is separate from thermal_memory_archive
- The bridge syncs extracted memories INTO thermal_memory_archive so the council and bots can see them
- Mem0 uses our vLLM to decide what to extract — this costs inference tokens but runs locally
- Start with user_id scoping: "darrell", "joe", "tribe" (shared)
- The embedding API on greenfin:8003 may need to support the OpenAI `/v1/embeddings` format that Mem0 expects — verify compatibility

## Success Criteria

- [ ] `mem0ai` installed in cherokee_venv
- [ ] `mem0_config.py` points to local vLLM + greenfin embeddings + bluefin pgvector
- [ ] `extract_and_store()` extracts facts from conversation and inserts into thermal_memory_archive
- [ ] Deduplication works (same fact → reheat, not duplicate)
- [ ] Per-user scoping functional (darrell vs joe vs tribe)
- [ ] No external API calls (everything runs on federation infrastructure)

---

*For Seven Generations - Cherokee AI Federation*
