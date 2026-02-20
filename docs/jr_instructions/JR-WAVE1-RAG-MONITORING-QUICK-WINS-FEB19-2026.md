# Jr Instruction: Wave 1 Quick Wins — RAG Performance + Monitoring Wiring

**Task**: Council-approved P0 fixes from Long Man DISCOVER/DELIBERATE phase
**Priority**: 1 (CRITICAL — veterans with real claims incoming, 3/10 monitoring readiness)
**Source**: Council vote #e7084fd90654eb46 (UNANIMOUS on quick wins)
**Assigned Jr**: Software Engineer Jr.

## Context

Council DISCOVER phase found:
- RAG pipeline latency 900-1700ms, can be cut to 400-950ms with two fixes
- Monitoring readiness 3/10 for veteran beta testers
- PostgreSQL on bluefin was DOWN 4+ days with NO alert sent
- VetAssist backend/frontend have ZERO health monitoring
- health_monitor.py writes alerts to DB only — never sends to Telegram

This instruction has 4 fixes. All are surgical, all are council-approved.

---

## Fix 1: RAG — Add memory_hash to primary SELECT (saves 100-150ms)

The ripple retrieval loop (lines 234-241) does 15 individual SELECTs to fetch `memory_hash` because the primary query omits it. Adding one column eliminates 15 round-trips.

File: `/ganuda/lib/specialist_council.py`

```
<<<<<<< SEARCH
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred,
                   metadata
            FROM thermal_memory_archive
=======
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred,
                   metadata,
                   memory_hash
            FROM thermal_memory_archive
>>>>>>> REPLACE
```

Then replace the N+1 loop with a direct read from the already-fetched rows:

```
<<<<<<< SEARCH
            primary_hashes = []
            for r in rows:
                # Look up memory_hash for each retrieved memory
                rcur = ripple_conn.cursor()
                rcur.execute("SELECT memory_hash FROM thermal_memory_archive WHERE id = %s", (r[0],))
                hash_row = rcur.fetchone()
                if hash_row:
                    primary_hashes.append(hash_row[0])
                rcur.close()
=======
            primary_hashes = [r[7] for r in rows if r[7]]  # memory_hash is now column index 7
>>>>>>> REPLACE
```

---

## Fix 2: RAG — HyDE fail-fast timeout (saves 300-600ms)

HyDE generation has a 30s timeout and blocks the entire retrieval path. If vLLM is slow, the user waits 30s before fallback. Fix: 5s timeout + skip HyDE for short queries.

File: `/ganuda/lib/rag_hyde.py`

```
<<<<<<< SEARCH
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
=======
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
>>>>>>> REPLACE
```

File: `/ganuda/lib/specialist_council.py`

Skip HyDE for short queries (greetings, simple lookups):

```
<<<<<<< SEARCH
        # Phase 2c: HyDE — embed hypothetical answer for better retrieval
        query_embedding = None
        try:
            from lib.rag_hyde import get_hyde_embedding
            query_embedding = get_hyde_embedding(question)
=======
        # Phase 2c: HyDE — embed hypothetical answer for better retrieval
        # Skip HyDE for short queries (greetings, simple lookups) — saves 600ms
        query_embedding = None
        try:
            from lib.rag_hyde import get_hyde_embedding
            if len(question) > 30:
                query_embedding = get_hyde_embedding(question)
            else:
                print(f"[RAG] Short query ({len(question)} chars), skipping HyDE")
>>>>>>> REPLACE
```

---

## Fix 3: Monitoring — Wire health_monitor alerts to Telegram

The health_monitor.py `send_alert()` function writes to `tpm_notifications` DB table but never calls `alert_manager`. This is why PostgreSQL was down 4 days with no notification.

File: `/ganuda/services/health_monitor/health_monitor.py`

Add import at top of file:

```
<<<<<<< SEARCH
import os
import socket
import subprocess
import requests
import psycopg2
import json
from datetime import datetime
=======
import os
import sys
import socket
import subprocess
import requests
import psycopg2
import json
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')
try:
    from alert_manager import alert_critical, alert_service_down
    HAS_ALERT_MANAGER = True
except ImportError:
    HAS_ALERT_MANAGER = False
>>>>>>> REPLACE
```

Then add Telegram alerting to the send_alert function:

```
<<<<<<< SEARCH
def send_alert(service_name, node, error, critical):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        priority = "P1" if critical else "P2"
        cur.execute("""
            INSERT INTO tpm_notifications (priority, category, title, message, source_system)
            VALUES (%s, 'health', %s, %s, 'health_monitor')
        """, (priority, f"Service DOWN: {service_name} on {node}", f"Error: {error}\nManual intervention required."))

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 95.0, %s)
        """, (f"health-{node}-{service_name}-{datetime.now().strftime('%Y%m%d%H%M')}",
              f"ALERT: {service_name} on {node} DOWN - {error}",
              json.dumps({"type": "health_alert", "node": node, "service": service_name})))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Alert error: {e}")
=======
def send_alert(service_name, node, error, critical):
    # Send to Telegram via alert_manager (P0 fix — was DB-only before)
    if HAS_ALERT_MANAGER:
        try:
            if critical:
                alert_critical(
                    f"Service DOWN: {service_name} on {node}",
                    f"Error: {error}\nManual intervention required.",
                    source='health-monitor'
                )
            else:
                alert_service_down(service_name, node, str(error))
        except Exception as e:
            print(f"  Telegram alert error: {e}")

    # Also persist to DB (existing behavior)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        priority = "P1" if critical else "P2"
        cur.execute("""
            INSERT INTO tpm_notifications (priority, category, title, message, source_system)
            VALUES (%s, 'health', %s, %s, 'health_monitor')
        """, (priority, f"Service DOWN: {service_name} on {node}", f"Error: {error}\nManual intervention required."))

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 95.0, %s)
        """, (f"health-{node}-{service_name}-{datetime.now().strftime('%Y%m%d%H%M')}",
              f"ALERT: {service_name} on {node} DOWN - {error}",
              json.dumps({"type": "health_alert", "node": node, "service": service_name})))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Alert error: {e}")
>>>>>>> REPLACE
```

---

## Fix 4: Monitoring — Add VetAssist to health checks

File: `/ganuda/services/health_monitor/health_monitor.py`

```
<<<<<<< SEARCH
        {"name": "SAG UI", "check_type": "http", "url": "http://localhost:4000", "restart_cmd": None, "critical": True},
=======
        {"name": "SAG UI", "check_type": "http", "url": "http://localhost:4000", "restart_cmd": None, "critical": True},
        {"name": "VetAssist Backend", "check_type": "http", "url": "http://localhost:8001/api/v1/health", "restart_cmd": None, "critical": True},
        {"name": "VetAssist Frontend", "check_type": "http", "url": "http://localhost:3000", "restart_cmd": None, "critical": True},
>>>>>>> REPLACE
```

---

## Verification

1. **RAG Fix 1**: Run a council vote — check logs for `[RAG] Ripple:` line. Should no longer see 15 individual SELECTs in pg_stat_activity. Latency should drop ~100ms.
2. **RAG Fix 2**: Test with short query ("hello") — should see `[RAG] Short query (5 chars), skipping HyDE`. Test with long query — should timeout in 5s if vLLM slow, not 30s.
3. **Monitoring Fix 3**: Stop a test service temporarily — should receive Telegram alert within 2 minutes (health_monitor cron interval).
4. **Monitoring Fix 4**: Check health_monitor output — should show VetAssist Backend and Frontend in check list with ✓ or ✗ status.
