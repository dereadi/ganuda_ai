# JR INSTRUCTION: Summarize Topic — ThermalToolSet Ring for Semantic Synthesis

**Task**: Implement a `summarize_topic` tool in the ThermalToolSet that performs semantic search across thermals, gathers relevant chunks, and feeds them to the LLM for consolidated synthesis. Adapted from jsdorn/MyBrain `summarize_topic` MCP tool pattern.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Council Votes**: #798ad0b799bad552 (ToolSet pattern), #4df2e34784f1b36c (Joe's MyBrain adoption)
**Depends On**: ThermalToolSet (JR-TOOLSET-RING-PATTERN), thermal chunking (JR-THERMAL-CHUNKING-INGEST)

## Context

When someone asks the council "what do we know about BigMac onboarding?" — the council currently opines from its training context alone. It doesn't search thermals. Joe's `summarize_topic` pattern fixes this:

1. Semantic search → top N relevant thermal chunks
2. Feed chunks as context to LLM
3. LLM generates consolidated summary grounded in actual data

This becomes a `read` safety_class tool in the ThermalToolSet — no council gate needed for search+summarize.

## Step 1: Add summarize_topic to ThermalToolSet

Add to `/ganuda/lib/toolsets/thermal_toolset.py`:

```python
ToolDescriptor(
    name="summarize_topic",
    description="Search thermals semantically for a topic and generate a consolidated summary from the results. Use when asked 'what do we know about X' or 'summarize our knowledge on X'.",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "The topic to search and summarize"},
            "top_k": {"type": "integer", "description": "Number of thermal chunks to retrieve (default 10)"},
            "domain_filter": {"type": "string", "description": "Optional domain_tag filter"}
        },
        "required": ["topic"]
    },
    safety_class="read"
)
```

## Step 2: Implement summarize_topic Method

```python
def summarize_topic(self, topic: str, top_k: int = 10,
                    domain_filter: str = "") -> dict:
    """Semantic search thermals for topic, feed to LLM for synthesis.

    Adapted from jsdorn/MyBrain summarize_topic MCP tool.
    """
    import psycopg2
    import requests
    from ganuda_db import get_db_config

    conn = psycopg2.connect(**get_db_config())
    cur = conn.cursor()

    # Step 1: Get embedding for topic query
    # Use the embedder on greenfin or local sentence-transformer
    embed_resp = requests.post(
        "http://192.168.132.224:8003/embed",
        json={"text": topic},
        timeout=10
    )
    embed_resp.raise_for_status()
    query_vector = embed_resp.json()["embedding"]

    # Step 2: Semantic search with optional domain filter
    domain_clause = ""
    params = [str(query_vector), top_k]
    if domain_filter:
        domain_clause = "AND domain_tag = %s"
        params = [str(query_vector), domain_filter, top_k]

    cur.execute(f"""
        SELECT t.id, t.original_content, t.temperature_score, t.domain_tag,
               t.sacred_pattern, t.parent_thermal_id, t.chunk_index,
               t.embedding <=> %s::vector AS distance
        FROM thermal_memory_archive t
        WHERE t.embedding IS NOT NULL
        {domain_clause}
        ORDER BY t.embedding <=> %s::vector
        LIMIT %s
    """, [str(query_vector)] + ([domain_filter] if domain_filter else []) + [str(query_vector), top_k])

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {
            "topic": topic,
            "chunks_found": 0,
            "summary": f"No thermals found related to '{topic}'."
        }

    # Step 3: Build context from retrieved chunks
    context_texts = []
    for row in rows:
        tid, content, temp, domain, sacred, parent_id, chunk_idx, dist = row
        prefix = "[SACRED] " if sacred else ""
        context_texts.append(
            f"{prefix}[{domain}, temp={temp}]: {content[:500]}"
        )

    context_block = "\n\n---\n\n".join(context_texts)

    # Step 4: Feed to LLM for synthesis (use local vLLM on redfin)
    synth_resp = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
            "messages": [
                {"role": "system", "content": "You are a knowledge synthesizer for the Cherokee AI Federation. Given thermal memory fragments on a topic, produce a concise, accurate summary. Cite specific details. Flag any contradictions between fragments."},
                {"role": "user", "content": f"Summarize what we know about: {topic}\n\nThermal fragments:\n{context_block}"}
            ],
            "max_tokens": 600,
            "temperature": 0.3
        },
        timeout=120
    )
    synth_resp.raise_for_status()
    summary = synth_resp.json()["choices"][0]["message"]["content"]

    return {
        "topic": topic,
        "chunks_found": len(rows),
        "domains": list(set(r[3] for r in rows)),
        "sacred_count": sum(1 for r in rows if r[4]),
        "summary": summary
    }
```

## Step 3: Register as Ring

```sql
INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name,
    parameters, safety_class, ring_type, provider, ring_status)
VALUES (
    'thermal_summarize_topic',
    'Semantic search thermals for a topic and generate LLM-synthesized summary',
    'lib.toolsets.thermal_toolset', 'summarize_topic',
    '{}'::jsonb, 'read', 'associate', 'toolset_thermal', 'active'
)
ON CONFLICT (tool_name) DO UPDATE SET ring_status = 'active', updated_at = NOW();
```

## Step 4: Wire to Gateway Council

When the council receives a question that matches data-retrieval patterns ("what do we know about", "summarize", "search thermals for"), the council should call `summarize_topic` as a pre-step and inject the result into specialist context.

Add to the council vote flow in gateway.py:

```python
# Before specialist dispatch, check if question is a data query
DATA_PATTERNS = ["what do we know", "summarize", "search thermals",
                 "find thermals", "what happened with", "history of"]

if any(p in question.lower() for p in DATA_PATTERNS):
    from toolsets.thermal_toolset import ThermalToolSet
    ts = ThermalToolSet()
    topic_result = ts.summarize_topic(topic=question, top_k=10)
    # Inject thermal context into specialist prompts
    thermal_context = f"\n\nTHERMAL MEMORY CONTEXT ({topic_result['chunks_found']} fragments):\n{topic_result['summary']}"
    # Append to each specialist's system prompt for this vote
```

## Step 5: Add Quick Script for Testing

Create `/ganuda/scripts/summarize_topic.py`:

```python
#!/usr/bin/env python3
"""Quick test: summarize a topic from thermals.

Usage: python3 summarize_topic.py "BigMac onboarding"
"""
import sys
sys.path.insert(0, '/ganuda/lib')
from toolsets.thermal_toolset import ThermalToolSet

topic = " ".join(sys.argv[1:]) or "federation infrastructure"
ts = ThermalToolSet()
result = ts.summarize_topic(topic=topic)
print(f"Topic: {result['topic']}")
print(f"Chunks found: {result['chunks_found']}")
print(f"Domains: {', '.join(result['domains'])}")
print(f"Sacred: {result['sacred_count']}")
print(f"\n{result['summary']}")
```

## DO NOT

- Use this tool for write operations — it's read-only (search + synthesize)
- Skip the semantic search step and just dump all thermals to the LLM — that's a context bomb
- Return raw thermal content to the user — always synthesize through LLM
- Hardcode the embedding endpoint — use config/secrets.env
- Call the external embedding service more than once per query — cache the vector

## Acceptance Criteria

- `summarize_topic` method exists in ThermalToolSet
- Registered as ring in duplo_tool_registry (safety_class: read)
- Semantic search retrieves relevant thermal chunks
- LLM synthesis produces coherent summary from fragments
- Gateway council detects data-retrieval questions and invokes automatically
- Test script works: `python3 summarize_topic.py "DC-10 reflex principle"` returns grounded summary
