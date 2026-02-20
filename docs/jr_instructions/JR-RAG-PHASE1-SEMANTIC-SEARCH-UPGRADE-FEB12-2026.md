# Jr Instruction: RAG Phase 1 — Semantic Search Upgrade

**Kanban**: #1760 (Thermal Memory RAG Optimization)
**Sacred Fire Priority**: 21
**Story Points**: 8
**River Cycle**: RC-2026-02A
**Council Vote**: #d7275d4814969bbf — REVIEW REQUIRED (0.888 confidence, 5 concerns addressed)
**Long Man Step**: BUILD (DISCOVER + DELIBERATE + ADAPT complete)

## Context

Our Thermal Memory RAG has 79,406 memories with 98.1% already embedded (BGE-large-en-v1.5, 1024d). The embedding service is healthy on greenfin:8003. Semantic search works in specialist_council.py. BUT:

1. **Jr executors** (both files) still use naive keyword-only ILIKE search — no semantic retrieval
2. **Retrieval truncates too aggressively** — 300-400 chars loses context
3. **No metadata filtering** beyond temperature — can't filter by domain, type, or recency
4. **Backfill script** has API format mismatch with current embedding service
5. **1,490 memories** still unembedded

## Steps

### Step 1: Fix Backfill Script API Format

The backfill script sends `{"text": content}` but the embedding service expects `{"texts": [content]}`.

File: `/ganuda/scripts/backfill_thermal_embeddings.py`

```python
<<<<<<< SEARCH
                resp = requests.post(
                    f"{EMBEDDING_URL}/v1/embeddings",
                    json={"text": content},
                    timeout=30
                )
                if resp.status_code == 200:
                    embedding = resp.json().get("embedding")
=======
                resp = requests.post(
                    f"{EMBEDDING_URL}/v1/embeddings",
                    json={"texts": [content]},
                    timeout=30
                )
                if resp.status_code == 200:
                    embeddings = resp.json().get("embeddings")
                    embedding = embeddings[0] if embeddings else None
>>>>>>> REPLACE
```

### Step 2: Upgrade Jr Task Executor — Add Semantic Search

Add EMBEDDING_SERVICE_URL constant and replace `_query_thermal_memory` with semantic-first approach.

File: `/ganuda/jr_executor/jr_task_executor.py`

```python
<<<<<<< SEARCH
GATEWAY_URL = os.environ.get('CHEROKEE_GATEWAY_URL', 'http://192.168.132.223:8080')
=======
GATEWAY_URL = os.environ.get('CHEROKEE_GATEWAY_URL', 'http://192.168.132.223:8080')
EMBEDDING_SERVICE_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://192.168.132.224:8003')
>>>>>>> REPLACE
```

File: `/ganuda/jr_executor/jr_task_executor.py`

```python
<<<<<<< SEARCH
    def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
        """Query thermal memory for context."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                search_pattern = '%' + '%'.join(query.split()[:5]) + '%'
                cur.execute("""
                    SELECT LEFT(original_content, 300), temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
                rows = cur.fetchall()

                if rows:
                    context = ""
                    for content, temp in rows:
                        context += f"[{temp:.0f}C] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
        return "No relevant memories found."
=======
    def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
        """Query thermal memory using semantic search with keyword fallback."""
        # Try semantic search first via embedding service
        try:
            resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/search",
                json={
                    "query": query[:500],
                    "table": "thermal_memory_archive",
                    "column": "original_content",
                    "embedding_column": "embedding",
                    "limit": limit,
                    "threshold": 0.5
                },
                timeout=10
            )
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    context = ""
                    for r in results:
                        content = r.get("content", "")[:600]
                        sim = r.get("similarity", 0)
                        context += f"[sim={sim:.2f}] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Semantic search failed, using keyword fallback: {e}")

        # Keyword fallback (ILIKE)
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                words = query.split()[:5]
                search_pattern = '%' + '%'.join(words) + '%'
                cur.execute("""
                    SELECT LEFT(original_content, 600), temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
                rows = cur.fetchall()

                if rows:
                    context = ""
                    for content, temp in rows:
                        context += f"[{temp:.0f}C] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Keyword thermal query error: {e}")
        return "No relevant memories found."
>>>>>>> REPLACE
```

### Step 3: Upgrade Jr Task Executor V2 — Same Pattern

File: `/ganuda/lib/jr_task_executor_v2.py`

```python
<<<<<<< SEARCH
GATEWAY_URL = os.environ.get('CHEROKEE_GATEWAY_URL', 'http://192.168.132.223:8080')
=======
GATEWAY_URL = os.environ.get('CHEROKEE_GATEWAY_URL', 'http://192.168.132.223:8080')
EMBEDDING_SERVICE_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://192.168.132.224:8003')
>>>>>>> REPLACE
```

File: `/ganuda/lib/jr_task_executor_v2.py`

```python
<<<<<<< SEARCH
    def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
        """Query thermal memory for context."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                search_pattern = '%' + '%'.join(query.split()[:5]) + '%'
                cur.execute("""
                    SELECT LEFT(original_content, 300), temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
                rows = cur.fetchall()

                if rows:
                    context = ""
                    for content, temp in rows:
                        context += f"[{temp:.0f}C] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
        return "No relevant memories found."
=======
    def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
        """Query thermal memory using semantic search with keyword fallback."""
        # Try semantic search first via embedding service
        try:
            resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/search",
                json={
                    "query": query[:500],
                    "table": "thermal_memory_archive",
                    "column": "original_content",
                    "embedding_column": "embedding",
                    "limit": limit,
                    "threshold": 0.5
                },
                timeout=10
            )
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    context = ""
                    for r in results:
                        content = r.get("content", "")[:600]
                        sim = r.get("similarity", 0)
                        context += f"[sim={sim:.2f}] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Semantic search failed, using keyword fallback: {e}")

        # Keyword fallback (ILIKE)
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                words = query.split()[:5]
                search_pattern = '%' + '%'.join(words) + '%'
                cur.execute("""
                    SELECT LEFT(original_content, 600), temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
                rows = cur.fetchall()

                if rows:
                    context = ""
                    for content, temp in rows:
                        context += f"[{temp:.0f}C] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Keyword thermal query error: {e}")
        return "No relevant memories found."
>>>>>>> REPLACE
```

### Step 4: Increase Retrieval Window in specialist_council.py

Increase from 400 chars to 800 chars for both semantic and keyword paths.

File: `/ganuda/lib/specialist_council.py`

```python
<<<<<<< SEARCH
            SELECT id, LEFT(original_content, 400), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
=======
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
>>>>>>> REPLACE
```

File: `/ganuda/lib/specialist_council.py`

```python
<<<<<<< SEARCH
            SELECT id, LEFT(original_content, 400), temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
              AND temperature_score >= 30
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
=======
            SELECT id, LEFT(original_content, 800), temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
              AND temperature_score >= 30
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
>>>>>>> REPLACE
```

## Verification

After applying changes:

1. Run backfill to embed remaining 1,490 memories:
   ```text
   CHEROKEE_DB_PASS=<password> python3 /ganuda/scripts/backfill_thermal_embeddings.py
   ```

2. Verify Jr semantic search works (check logs after Jr picks up a task):
   ```text
   journalctl -u jr-se -n 50 | grep -i "semantic\|embedding\|sim="
   ```

3. Verify specialist_council.py retrieval shows 800-char memories:
   ```text
   curl -s http://192.168.132.223:8080/v1/council/vote -H "Content-Type: application/json" -H "X-API-Key: <key>" -d '{"question": "test rag retrieval", "context": "verify 800 char window"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('consensus','')[:200])"
   ```

## What This Does NOT Cover (Phase 2)

- Chunking strategy for long memories (separate instruction)
- Cross-encoder re-ranking (separate instruction)
- Evaluation framework / metrics (separate instruction)
- Graph RAG / entity relationship traversal (separate instruction)
- BM25 to replace naive ILIKE keyword search (separate instruction)

## Council Concerns Addressed

| Specialist | Concern | How Addressed |
|------------|---------|---------------|
| Gecko | Performance overhead | `/v1/search` endpoint has 10s timeout, graceful fallback to ILIKE |
| Turtle | Seven-generation impact | Better retrieval = better council reasoning for all future decisions |
| Crawdad | Security | No new endpoints exposed, existing auth model unchanged |
| Raven | Strategy alignment | Phase 1 closes foundation gaps before optimizing |
| Peace Chief | Consensus | All changes are additive — fallback preserved, no breaking changes |
