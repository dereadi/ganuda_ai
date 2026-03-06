# QW-4: Resilient Thermal Writes (3x retry + disk fallback)

**Kanban**: #1909
**Priority**: P2 — Reliability Quick Win (Legion adoption)
**Assigned**: Software Engineer Jr.

---

## Context

Thermal memory writes currently have no retry logic. If the DB is unreachable during vLLM heavy load, observations are silently lost. Legion's `lib/resilience.py` wraps writes with 3x retry + exponential backoff + local disk fallback. We adopt this pattern by adding `safe_thermal_write()` to `ganuda_db/__init__.py`.

## Step 1: Add safe_thermal_write to ganuda_db

File: `/ganuda/lib/ganuda_db/__init__.py`

````text
<<<<<<< SEARCH
def execute_query(sql: str, params=None) -> list:
=======
def safe_thermal_write(content: str, temperature: float = 60.0,
                       source: str = "unknown", sacred: bool = False,
                       metadata: dict = None) -> bool:
    """
    Resilient thermal memory write with 3x retry + disk fallback.
    Legion adoption (QW-4, kanban #1909).

    Returns True if written to DB, False if fell back to disk.
    """
    import hashlib
    import json
    import time
    from datetime import datetime

    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    meta = metadata or {}
    meta.update({"source": source, "timestamp": datetime.now().isoformat()})

    for attempt in range(3):
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                    (original_content, temperature_score, memory_hash,
                     sacred_pattern, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (memory_hash) DO NOTHING
                """, (content, temperature, memory_hash, sacred,
                      json.dumps(meta)))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception:
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))

    # All retries failed — disk fallback
    try:
        import os
        fallback_dir = "/ganuda/logs"
        os.makedirs(fallback_dir, exist_ok=True)
        fallback_path = os.path.join(fallback_dir, "thermal_fallback.jsonl")
        with open(fallback_path, "a") as f:
            f.write(json.dumps({
                "content": content[:2000],
                "temperature": temperature,
                "memory_hash": memory_hash,
                "sacred": sacred,
                "metadata": meta,
            }) + "\n")
    except Exception:
        pass
    return False


def execute_query(sql: str, params=None) -> list:
>>>>>>> REPLACE
````

## Verification

After applying:
1. `python3 -c "import sys; sys.path.insert(0,'/ganuda/lib'); from ganuda_db import safe_thermal_write; print('imported ok')"` works
2. `grep 'safe_thermal_write' /ganuda/lib/ganuda_db/__init__.py` shows the function
3. Function has 3x retry with exponential backoff (0.5s, 1s, 2s)
4. Falls back to `/ganuda/logs/thermal_fallback.jsonl` if all retries fail
5. Returns bool indicating DB success vs disk fallback
