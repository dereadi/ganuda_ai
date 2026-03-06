# Jr Instruction: RAG Wave 1 — Performance + Monitoring Wiring

**Task ID:** RAG-WAVE1
**Kanban:** #1849
**Priority:** 2
**Assigned:** Software Engineer Jr.
**Council Vote:** #e7084fd9 (UNANIMOUS)

---

## Overview

Four fixes to improve RAG latency (900-1700ms → 400-950ms) and monitoring readiness (3/10 → 5/10):

1. Add `memory_hash` to pgvector SELECT (eliminates N+1 dedup queries)
2. HyDE fail-fast 5s timeout (already partially done — add explicit timeout)
3. Wire health_monitor.py Telegram alerts for VetAssist
4. Add VetAssist backend + frontend to health checks

---

## Step 1: Add memory_hash to pgvector SELECT

The semantic search query fetches `memory_hash` via a SEPARATE follow-up query for dedup. Adding it to the main SELECT eliminates 15 N+1 queries per RAG call.

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred,
                   metadata,
                   memory_hash
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
=======
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred,
                   metadata,
                   memory_hash,
                   tags,
                   memory_type
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
>>>>>>> REPLACE

---

## Step 2: Add HyDE explicit timeout

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        try:
            from lib.rag_hyde import get_hyde_embedding
            if len(question) > 30:
                query_embedding = get_hyde_embedding(question)
            else:
                print(f"[RAG] Short query ({len(question)} chars), skipping HyDE")
            if query_embedding:
                print(f"[RAG] Using HyDE-enhanced embedding ({len(query_embedding)}d)")
        except Exception as e:
            print(f"[RAG] HyDE unavailable, using raw embedding: {e}")
=======
        try:
            from lib.rag_hyde import get_hyde_embedding
            import signal

            def _hyde_timeout_handler(signum, frame):
                raise TimeoutError("HyDE exceeded 5s timeout")

            if len(question) > 30:
                old_handler = signal.signal(signal.SIGALRM, _hyde_timeout_handler)
                signal.alarm(5)
                try:
                    query_embedding = get_hyde_embedding(question)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                print(f"[RAG] Short query ({len(question)} chars), skipping HyDE")
            if query_embedding:
                print(f"[RAG] Using HyDE-enhanced embedding ({len(query_embedding)}d)")
        except TimeoutError:
            print("[RAG] HyDE timeout (5s) — falling back to raw embedding")
        except Exception as e:
            print(f"[RAG] HyDE unavailable, using raw embedding: {e}")
>>>>>>> REPLACE

---

## Step 3: Add VetAssist endpoints to health monitor

File: `/ganuda/services/health_monitor.py`

<<<<<<< SEARCH
SERVICES = [
    ('vLLM', 'http://localhost:8000/health', 5000),
    ('Gateway', 'http://localhost:8080/health', 2000),
    ('ii-researcher', 'http://localhost:8090/health', 3000),
]
=======
SERVICES = [
    ('vLLM', 'http://localhost:8000/health', 5000),
    ('Gateway', 'http://localhost:8080/health', 2000),
    ('ii-researcher', 'http://localhost:8090/health', 3000),
    ('VetAssist-Backend', 'http://localhost:8001/health', 3000),
    ('VetAssist-Frontend', 'http://localhost:3000/', 5000),
]
>>>>>>> REPLACE

---

## Step 4: Add DLQ depth check to health monitor

File: `/ganuda/services/health_monitor.py`

<<<<<<< SEARCH
def check_jr_queue_depth() -> bool:
    """Check for Jr work queue backup."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.close()
        conn.close()

        if pending > 20:
            alert_medium(
                "Jr Work Queue Backup",
                f"{pending} Jr tasks pending",
                source='eagle-eye',
                context={'pending_tasks': pending}
            )
            return False

        logging.debug(f"Jr queue: {pending} pending")
        return True

    except Exception as e:
        logging.error(f"Jr queue check failed: {e}")
        return True
=======
def check_jr_queue_depth() -> bool:
    """Check for Jr work queue backup."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'pending'")
        pending = cur.fetchone()[0]

        # Also check DLQ depth (failed tasks in last 7 days)
        cur.execute("""
            SELECT COUNT(*) FROM jr_work_queue
            WHERE status IN ('failed', 'error')
              AND updated_at > NOW() - INTERVAL '7 days'
        """)
        dlq_depth = cur.fetchone()[0]
        cur.close()
        conn.close()

        if pending > 20:
            alert_medium(
                "Jr Work Queue Backup",
                f"{pending} Jr tasks pending",
                source='eagle-eye',
                context={'pending_tasks': pending}
            )
            return False

        if dlq_depth > 5:
            alert_medium(
                "Jr DLQ Depth High",
                f"{dlq_depth} failed tasks in last 7 days",
                source='eagle-eye',
                context={'dlq_depth': dlq_depth}
            )

        logging.debug(f"Jr queue: {pending} pending, DLQ: {dlq_depth}")
        return True

    except Exception as e:
        logging.error(f"Jr queue check failed: {e}")
        return True
>>>>>>> REPLACE

---

## Verification

1. Restart the gateway to pick up specialist_council.py changes:
```text
sudo systemctl restart llm-gateway
```

2. Test RAG query latency (should be faster with memory_hash in SELECT):
```text
curl -s http://localhost:8080/v1/council/vote -X POST \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is the thermal memory architecture?"}' | python3 -m json.tool | head -20
```

3. Verify health monitor picks up VetAssist:
```text
python3 /ganuda/services/health_monitor.py
```

---

## What This Does NOT Do

- Does NOT deploy health_monitor as a systemd service (TPM-direct)
- Does NOT modify the embedding service
- Does NOT change the pgvector index type (IVFFlat is fine for 80K memories)
