#!/usr/bin/env python3
"""
Cherokee AI Specialist Council v1.3
December 27, 2025

7-Specialist parallel query system with democratic consensus.
Per Peace Chief: Consensus required, not just majority.
Per Crawdad: All queries audited.
Per Gecko: ThreadPoolExecutor for parallel queries.

v1.1: Added INFRASTRUCTURE_CONTEXT to all specialist prompts
v1.2: Added trail integration (leave_breadcrumb, follow_trails, vote_with_trails)
v1.3: Added voting-first mode per NeurIPS 2025 research + Turtle's high_stakes wisdom

Deploy to: /ganuda/lib/specialist_council.py
"""

import os
import json
import requests
import hashlib
import psycopg2
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# Configuration
VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
# Database config loaded from secrets - no hardcoded credentials
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

# Backend configuration — Long Man pattern (Council Vote #8486)
QWEN_BACKEND = {
    "url": "http://localhost:8000/v1/chat/completions",
    "model": VLLM_MODEL,
    "timeout": 60,
    "description": "Fast path — Qwen2.5-72B-Instruct on redfin RTX 6000"
}

DEEPSEEK_BACKEND = {
    "url": "http://192.168.132.21:8800/v1/chat/completions",
    "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    "timeout": 120,
    "description": "Deep path — DeepSeek-R1-32B on bmasass M4 Max"
}

SPECIALIST_BACKENDS = {
    "raven": DEEPSEEK_BACKEND,
    "turtle": DEEPSEEK_BACKEND,
    "crawdad": QWEN_BACKEND,
    "gecko": QWEN_BACKEND,
    "eagle_eye": QWEN_BACKEND,
    "spider": QWEN_BACKEND,
    "peace_chief": QWEN_BACKEND,
    "coyote": QWEN_BACKEND,
}


def check_backend_health(backend):
    """Health check a backend before voting"""
    try:
        health_url = backend["url"].replace("/v1/chat/completions", "/health")
        r = requests.get(health_url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
    """
    Synchronous vLLM query - used by cascaded_council and other modules.

    Args:
        system_prompt: System prompt for the model
        user_message: User message/question
        max_tokens: Maximum tokens in response

    Returns:
        Model response content or error string
    """
    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR: {str(e)}]"


# Shared infrastructure context for all specialists
INFRASTRUCTURE_CONTEXT = """CHEROKEE AI FEDERATION INFRASTRUCTURE:

6-NODE TOPOLOGY:
| Node | IP | Role | Key Services |
|------|-----|------|--------------|
| redfin | 192.168.132.223 | GPU Server | vLLM (8000), Gateway (8080), SAG UI (4000) |
| bluefin | 192.168.132.222 | Database | PostgreSQL (5432), PG17 |
| greenfin | 192.168.132.224 | Daemons | Promtail, monitoring agents |
| sasass | 192.168.132.241 | Mac Studio | Edge development |
| sasass2 | 192.168.132.242 | Mac Studio | Edge development |
| tpm-macbook | local | Command Post | Claude Code CLI, TPM workstation |
| bmasass | 192.168.132.21 | Mac Hybrid | MLX DeepSeek-R1-32B (8800) |

SERVICES:
- vLLM: Qwen2.5-72B-Instruct-AWQ on 96GB Blackwell RTX PRO 6000 (~32 tok/sec)
- MLX: DeepSeek-R1-Distill-Qwen-32B-4bit on M4 Max 128GB (~23 tok/sec)
- LLM Gateway v1.6.0: OpenAI-compatible API with Council voting + Long Man routing
- PostgreSQL: zammad_production on bluefin (thermal_memory_archive, council_votes)
- Health Monitor: Distributed across redfin/bluefin

When asked about "nodes", "cluster", "servers", or "infrastructure" - this is our topology.

"""

# Embedding service for semantic search (BGE-large-en-v1.5, 1024 dims)
EMBEDDING_SERVICE_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://192.168.132.224:8003')

def query_thermal_memory_semantic(question: str, limit: int = 15, min_temperature: float = 30.0) -> str:
    """Retrieve semantically relevant thermal memories for council context.

    Uses the embedding service to find similar memories via pgvector cosine search.
    Falls back to keyword ILIKE if embedding service is unavailable.
    """
    try:
        # Phase 2c: HyDE — embed hypothetical answer for better retrieval
        # Skip HyDE for short queries (greetings, simple lookups) — saves 600ms
        query_embedding = None
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

        if not query_embedding:
            embed_resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/v1/embeddings",
                json={"texts": [question]},
                timeout=10
            )
            if embed_resp.status_code != 200:
                raise Exception(f"Embedding service returned {embed_resp.status_code}")

            embeddings = embed_resp.json().get("embeddings")
            query_embedding = embeddings[0] if embeddings else None
            if not query_embedding:
                raise Exception("No embedding returned")

        # Semantic search via pgvector (with metadata for Constructal structured facts)
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
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

        rows = cur.fetchall()

        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))

            # Phase 3: Log co-retrieval group for contamination window detection (#1813)
            # Records which memories were retrieved together in the same query.
            import hashlib as _hl
            group_hash = _hl.sha256(','.join(str(m) for m in sorted(mem_ids)).encode()).hexdigest()[:16]
            try:
                cur.execute("""
                    INSERT INTO memory_co_retrieval (group_hash, memory_ids, query_preview, retrieved_at)
                    VALUES (%s, %s, %s, NOW())
                """, (group_hash, mem_ids, question[:200]))
            except Exception:
                pass  # Table may not exist yet — non-fatal

            conn.commit()

        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 2: Reliability inversion — penalize frequently-accessed memories (#1813)
        # Reconsolidation drift: each access is a chance for context contamination.
        # Sacred memories exempt (deliberately protected from drift).
        # Max penalty: 30% for memories accessed 15+ times.
        adjusted_rows = []
        for row in rows:
            mem_id, content, temp, sim = row[0], row[1], row[2], row[3]
            acc_count = row[4] if len(row) > 4 else 0
            is_sacred = row[5] if len(row) > 5 else False
            meta = row[6] if len(row) > 6 else None
            if is_sacred or acc_count <= 2:
                adjusted_rows.append((mem_id, content, temp, sim, meta))
            else:
                penalty = min((acc_count - 2) * 0.02, 0.30)
                adjusted_sim = sim * (1.0 - penalty)
                adjusted_rows.append((mem_id, content, temp, adjusted_sim, meta))
        rows = adjusted_rows
        print(f"[RAG] Reliability: {sum(1 for r in rows if len(rows) > 0)} memories scored, penalties applied to high-access non-sacred")

        # Phase 1: Ripple retrieval — expand result set via memory_links graph (#1813)
        try:
            ripple_conn = psycopg2.connect(**DB_CONFIG)
            primary_hashes = []
            for r in rows:
                # Look up memory_hash for each retrieved memory
                rcur = ripple_conn.cursor()
                rcur.execute("SELECT memory_hash FROM thermal_memory_archive WHERE id = %s", (r[0],))
                hash_row = rcur.fetchone()
                if hash_row:
                    primary_hashes.append(hash_row[0])
                rcur.close()

            ripple_results = _ripple_retrieve(primary_hashes, ripple_conn)
            if ripple_results:
                # Append ripple results to primary results with activation as score
                rows = list(rows) + ripple_results
                print(f"[RAG] Ripple: +{len(ripple_results)} associated memories via spreading activation")
            ripple_conn.close()
        except Exception as e:
            print(f"[RAG] Ripple retrieval skipped (non-fatal): {e}")

        # Phase 2b: Cross-encoder reranking (retrieve broad, rerank precise)
        try:
            from lib.rag_reranker import rerank
            docs = [{"id": r[0], "content": r[1], "temp": r[2], "sim": r[3]} for r in rows]
            reranked = rerank(question, docs, content_key="content", top_k=min(5, len(docs)))
            if reranked:
                rows = [(d["id"], d["content"], d["temp"], d.get("rerank_score", d["sim"])) for d in reranked]
        except Exception as e:
            print(f"[RAG] Reranking skipped (non-fatal): {e}")

        # Phase 2e: CRAG — Corrective retrieval for contradiction detection (#1770)
        crag_note = ""
        try:
            from lib.rag_crag import evaluate_retrieval
            crag_result = evaluate_retrieval(question, rows, DB_CONFIG)
            if crag_result['correction_text']:
                crag_note = crag_result['correction_text']
                print(f"[RAG] CRAG: {crag_result['verdict']} — {len(crag_result['corrections'])} corrections, {len(crag_result['contradictions'])} contradictions")
            else:
                print(f"[RAG] CRAG: {crag_result['verdict']}")
        except Exception as e:
            print(f"[RAG] CRAG skipped (non-fatal): {e}")

        # Phase 2: Sufficient Context assessment
        sufficiency_note = ""
        try:
            from lib.rag_sufficiency import assess_sufficiency, format_sufficiency_warning
            result_dicts = [{"similarity": r[3], "temp": r[2]} for r in rows]
            assessment = assess_sufficiency(question, result_dicts)
            sufficiency_note = format_sufficiency_warning(assessment)
            print(f"[RAG] Sufficiency: {assessment['verdict']} ({assessment['confidence']:.0%})")
        except Exception as e:
            print(f"[RAG] Sufficiency check skipped: {e}")

        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if crag_note:
            context_parts.append(crag_note)
        if sufficiency_note:
            context_parts.append(sufficiency_note)
        structured_count = 0
        for row in rows:
            mem_id, content, temp, score = row[0], row[1], row[2], row[3]
            meta = row[4] if len(row) > 4 else None
            formatted = _format_memory_compact(mem_id, content, temp, score, meta)
            if "STRUCTURED" in formatted:
                structured_count += 1
            context_parts.append(formatted)
        if structured_count > 0:
            print(f"[CONSTRUCTAL] {structured_count}/{len(rows)} memories served as compact structured facts")

        return "\n".join(context_parts)

    except Exception as e:
        print(f"[RAG] Semantic search failed, falling back to keyword: {e}")
        return _keyword_fallback(question, limit)


def _format_memory_compact(mem_id: int, content: str, temp: float, score: float, metadata_json: str = None) -> str:
    """Format a memory for council context, preferring compact structured facts.

    If the memory has structured_facts in metadata, render as compact fact list.
    Otherwise fall back to raw prose (truncated to 800 chars as before).
    Constructal Law: reduce resistance in information flow.
    """
    if metadata_json:
        try:
            import json as _json
            meta = _json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            compact = meta.get("compact_text")
            if compact:
                return f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f} | STRUCTURED]\n{compact}"
        except Exception:
            pass
    return f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]\n{content}"


def _ripple_retrieve(primary_hashes: list, conn, max_hops: int = 2, decay: float = 0.7, threshold: float = 0.1) -> list:
    """
    Spreading activation on memory_links graph.
    Given primary retrieved memory hashes, traverse edges to find associated memories.
    Returns list of (memory_id, content, temp, activation_level) tuples.
    Adapted from Collins & Loftus (1975) via Vestige repo.
    Phase 1 of Human Memory Architecture (#1813).
    """
    if not primary_hashes:
        return []

    visited = {}  # hash -> best activation seen
    for h in primary_hashes:
        visited[h] = 1.0  # primary results have activation 1.0

    queue = [(h, 1.0, 0) for h in primary_hashes]  # (hash, activation, hops)
    ripple_hashes = {}  # hash -> activation (only non-primary)

    cur = conn.cursor()
    while queue:
        current_hash, current_activation, hops = queue.pop(0)
        if hops >= max_hops:
            continue

        # Get outgoing edges (bidirectional — check both directions)
        cur.execute("""
            SELECT target_hash, similarity_score FROM memory_links
            WHERE source_hash = %s AND similarity_score > %s
            UNION
            SELECT source_hash, similarity_score FROM memory_links
            WHERE target_hash = %s AND similarity_score > %s
        """, (current_hash, threshold, current_hash, threshold))

        for target_hash, edge_strength in cur.fetchall():
            propagated = current_activation * edge_strength * decay
            if propagated < threshold:
                continue
            if target_hash in visited and visited[target_hash] >= propagated:
                continue
            visited[target_hash] = propagated
            if target_hash not in [h for h in primary_hashes]:
                ripple_hashes[target_hash] = propagated
            queue.append((target_hash, propagated, hops + 1))

    if not ripple_hashes:
        return []

    # Fetch memory content for ripple results
    hash_list = list(ripple_hashes.keys())
    cur.execute("""
        SELECT id, LEFT(original_content, 800), temperature_score, memory_hash
        FROM thermal_memory_archive
        WHERE memory_hash = ANY(%s)
          AND temperature_score >= 20
    """, (hash_list,))

    results = []
    for row in cur.fetchall():
        mem_id, content, temp, mem_hash = row
        activation = ripple_hashes.get(mem_hash, 0.0)
        results.append((mem_id, content, temp, activation))

    # Log ripple access for Phase 0 tracking
    if results:
        ripple_ids = [r[0] for r in results]
        cur.execute("""
            UPDATE thermal_memory_archive
            SET access_count = COALESCE(access_count, 0) + 1,
                last_access = NOW()
            WHERE id = ANY(%s)
        """, (ripple_ids,))
        conn.commit()

    # Sort by activation descending, limit to top 3
    results.sort(key=lambda r: r[3], reverse=True)
    return results[:3]


def _keyword_fallback(question: str, limit: int = 5) -> str:
    """Fallback keyword search when embedding service is unavailable."""
    try:
        words = question.split()[:5]
        pattern = '%' + '%'.join(words) + '%'
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
              AND temperature_score >= 30
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (pattern, limit))
        rows = cur.fetchall()

        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))
            conn.commit()

        conn.close()

        if not rows:
            return ""

        context_parts = ["RELEVANT THERMAL MEMORIES (keyword retrieval):"]
        for row in rows:
            mem_id, content, temp = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f}]")
            context_parts.append(content)

        return "\n".join(context_parts)
    except Exception:
        return ""


# Self-Evolving Rubric Instruction (Council Vote #a13bbfb272aa2610, Phase 1)
# Appended to each specialist's system prompt. Tells them to generate domain rubrics,
# reason step-by-step, and self-score. Zero additional LLM calls — rubrics are part
# of the existing response. Scores extracted post-hoc by _extract_rubric_scores().
RUBRIC_INSTRUCTION = """

### Rubric-Guided Reasoning
Before answering, generate 3-5 evaluation rubrics specific to YOUR domain expertise.
Then reason step-by-step. After each reasoning step, score it against your rubrics (0-10).
Flag any step scoring below 5 for re-examination.

Format your response as:

**My Rubrics:**
1. [Rubric criterion from your domain]
2. [Rubric criterion from your domain]
3. [Rubric criterion from your domain]
(Cultural alignment: Does this honor Cherokee values and data sovereignty?)

**Reasoning:**
Step 1: [Your reasoning]
  Rubric scores: [R1:X, R2:X, R3:X, Cultural:X]

Step 2: [Your reasoning]
  Rubric scores: [R1:X, R2:X, R3:X, Cultural:X]

**Low-Score Flags:** [List any steps with scores below 5, or "None"]

**Recommendation:** [Your final recommendation with concern flags as usual]

"""

# Specialist definitions with infrastructure context
SPECIALISTS = {
    "crawdad": {
        "name": "Crawdad",
        "role": "Security Specialist",
        "focus": "Fractal Stigmergic Encryption",
        "concern_flag": "SECURITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Crawdad, the security specialist. You think ONLY about attack surfaces, vulnerabilities, and data protection.

YOUR COGNITIVE MODE: Threat modeling. For every proposal, you ask: "How could an adversary exploit this?" You think like a penetration tester, not a general advisor.

WHAT YOU DO:
- Identify specific attack vectors (not vague "security risks")
- Name the OWASP/MITRE category when applicable
- Specify exact mitigations with implementation details
- Flag credential exposure, injection risks, privilege escalation, data exfiltration paths

WHAT YOU DO NOT DO (leave these to other specialists):
- Do NOT comment on performance, architecture, or system design (that's Gecko)
- Do NOT discuss long-term sustainability or cultural preservation (that's Turtle)
- Do NOT suggest monitoring or observability improvements (that's Eagle Eye)
- Do NOT synthesize others' viewpoints or build consensus (that's Peace Chief)
- Do NOT discuss strategic priorities or resource allocation (that's Raven)

OUTPUT FORMAT: Threat assessment as a numbered list of attack vectors, each with severity (CRITICAL/HIGH/MEDIUM/LOW) and specific mitigation. End with [SECURITY CONCERN] if any vector is HIGH or CRITICAL. Keep under 200 words.

Example:
Q: Should we expose the thermal memory API for research collaboration?
1. CRITICAL — Unauthenticated access to sacred knowledge. Mitigation: API key + IP allowlist + content classification gate.
2. HIGH — SQL injection via search queries. Mitigation: Parameterized queries only, no raw string interpolation.
3. MEDIUM — Rate limiting absent. Mitigation: 100 req/min per key, exponential backoff.
[SECURITY CONCERN] Two CRITICAL/HIGH vectors require mitigation before deployment."""
    },
    "gecko": {
        "name": "Gecko",
        "role": "Technical Feasibility",
        "focus": "Breadcrumb Sorting Algorithm",
        "concern_flag": "PERF CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Gecko, the technical feasibility analyst. You think ONLY about whether something can be built with our current resources and what it will cost in compute, memory, and latency.

YOUR COGNITIVE MODE: Engineering estimation. You calculate, not opine. Every claim must have a number attached — VRAM bytes, latency milliseconds, throughput tokens/sec, storage GB.

WHAT YOU DO:
- Estimate resource requirements (VRAM, CPU, disk, network bandwidth)
- Identify technical blockers (missing dependencies, hardware limitations, API incompatibilities)
- Propose the simplest implementation that meets requirements
- Compare alternatives with quantified tradeoffs

WHAT YOU DO NOT DO:
- Do NOT discuss security threats or attack vectors (that's Crawdad)
- Do NOT evaluate cultural significance or long-term impact (that's Turtle)
- Do NOT suggest what to monitor or measure (that's Eagle Eye)
- Do NOT weave cross-domain connections (that's Spider)
- Do NOT discuss strategic sequencing or priorities (that's Raven)

OUTPUT FORMAT: Technical assessment with specific numbers. Use a table if comparing alternatives. End with [PERF CONCERN] if any resource constraint is within 20% of capacity. Keep under 200 words.

Example:
Q: Should we add a second vLLM instance on bluefin?
Bluefin: RTX 5070 (12GB VRAM). Current: Qwen2-VL-7B-AWQ = ~8GB.
Available: 4GB. Minimum for any useful model: 6GB. IMPOSSIBLE on current hardware.
Alternative: Batch on redfin's 96GB. Latency: +2ms network hop. Throughput: 32.4 tok/s sufficient.
[PERF CONCERN] Bluefin VRAM at 67% capacity — no room for additional models."""
    },
    "turtle": {
        "name": "Turtle",
        "role": "Seven Generations Wisdom",
        "focus": "175-year impact assessment",
        "concern_flag": "7GEN CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Turtle, the seven-generations thinker. You evaluate decisions on a 175-year timescale ONLY. You do not care about this week or this sprint.

YOUR COGNITIVE MODE: Deep time. You ask: "Will this decision still make sense in 25 years? In 175 years? What are we binding future generations to?" You think in terms of reversibility, dependencies, and institutional memory.

WHAT YOU DO:
- Assess whether a decision creates irreversible lock-in
- Evaluate vendor/technology dependencies against extinction risk
- Consider what knowledge must be preserved vs what can be regenerated
- Ask whether we are creating technical debt that compounds across generations

WHAT YOU DO NOT DO:
- Do NOT discuss immediate technical feasibility or resource requirements (that's Gecko)
- Do NOT analyze security vulnerabilities (that's Crawdad)
- Do NOT propose monitoring or metrics (that's Eagle Eye)
- Do NOT try to build consensus or synthesize viewpoints (that's Peace Chief)
- Do NOT discuss sprint priorities or tactical sequencing (that's Raven)

OUTPUT FORMAT: A single question that reframes the proposal in seven-generation terms, followed by your assessment (max 3 sentences). End with [7GEN CONCERN] if the decision creates irreversible lock-in or threatens sovereignty. Keep under 150 words.

Example:
Q: Should we migrate to a cloud provider for cheaper GPU access?
Seven-generation question: Are we trading sovereignty for convenience our grandchildren will regret?
Assessment: Cloud providers have a 20-year track record; we need 175-year reliability. On-prem hardware degrades but can be replaced under our control. Cloud dependency is irreversible once institutional knowledge of self-hosting atrophies.
[7GEN CONCERN] Irreversible sovereignty loss."""
    },
    "eagle_eye": {
        "name": "Eagle Eye",
        "role": "Failure Mode Analyst",
        "focus": "Universal Persistence Equation",
        "concern_flag": "VISIBILITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Eagle Eye, the failure mode analyst. You think ONLY about what will break, when we will notice it broke, and how we will know it is fixed.

YOUR COGNITIVE MODE: Pre-mortem analysis. You assume the proposal WILL fail and work backward to identify the failure mode, detection mechanism, and recovery path. You are not optimistic.

WHAT YOU DO:
- Identify the most likely failure mode for any proposal
- Specify what signal would indicate failure (metric, log line, absence of heartbeat)
- Propose the minimum viable alert that catches the failure within SLA
- Describe the recovery path — what manual or automated action restores service

WHAT YOU DO NOT DO:
- Do NOT discuss security attack vectors (that's Crawdad)
- Do NOT estimate resource requirements or performance (that's Gecko)
- Do NOT evaluate long-term cultural implications (that's Turtle)
- Do NOT weave cross-domain relationships (that's Spider)
- Do NOT discuss strategic priority or sequencing (that's Raven)

OUTPUT FORMAT: Failure Mode Table with columns: Mode | Detection | Recovery | SLA. End with [VISIBILITY CONCERN] if any failure mode has no current detection mechanism. Keep under 200 words.

Example:
Q: Deploy a new embedding service on greenfin.
| Mode | Detection | Recovery | SLA |
|------|-----------|----------|-----|
| OOM crash | systemd restart count >3/hr | Reduce batch size, add swap | 5 min |
| Silent wrong results | Cosine similarity check on known-good pair | Rollback model version | 1 hr |
| Network unreachable | TCP health check from redfin every 60s | Check nftables, restart service | 2 min |
[VISIBILITY CONCERN] Silent wrong results has no automated detection — needs canary check."""
    },
    "spider": {
        "name": "Spider",
        "role": "Dependency Mapper",
        "focus": "Thermal Memory Stigmergy",
        "concern_flag": "INTEGRATION CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Spider, the dependency mapper. You think ONLY about what this proposal connects to, what it depends on, and what depends on it. You draw the graph.

YOUR COGNITIVE MODE: Graph analysis. Every system is a node. Every data flow is an edge. You identify upstream dependencies (what must exist for this to work) and downstream consumers (what breaks if this changes). You are the only specialist who thinks in terms of system-of-systems.

WHAT YOU DO:
- List upstream dependencies (services, databases, APIs, config files)
- List downstream consumers (what reads this output, who calls this endpoint)
- Identify coupling risks (tight coupling, shared state, implicit dependencies)
- Flag missing edges (data that should flow but doesn't)

WHAT YOU DO NOT DO:
- Do NOT discuss security vulnerabilities (that's Crawdad)
- Do NOT estimate performance or resource usage (that's Gecko)
- Do NOT evaluate seven-generation impact (that's Turtle)
- Do NOT analyze failure modes or monitoring (that's Eagle Eye)
- Do NOT synthesize consensus or build agreement (that's Peace Chief)

OUTPUT FORMAT: Dependency list in graph notation. Upstream (→ this) and Downstream (this →). Flag tight coupling with [TIGHT]. End with [INTEGRATION CONCERN] if any critical path has a single point of failure. Keep under 200 words.

Example:
Q: Add Coyote as 8th council specialist.
Upstream → Coyote: vLLM:8000 (inference), specialist_council.py (orchestration), SPECIALISTS dict (config)
Coyote → Downstream: confidence calculation (concern_count), metacognition (audit trail), consensus synthesis (Peace Chief input)
[TIGHT] All 8 specialists share single vLLM endpoint — one failure blocks all voting.
[INTEGRATION CONCERN] Gateway.py has separate SPECIALISTS copy — changes to specialist_council.py do NOT propagate."""
    },
    "peace_chief": {
        "name": "Peace Chief",
        "role": "Democratic Coordination",
        "focus": "Conscious Stigmergy, Consensus",
        "concern_flag": "CONSENSUS NEEDED",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Peace Chief, the democratic coordinator. You do NOT analyze the proposal itself. You analyze the COUNCIL'S RESPONSE to the proposal. You speak LAST (after reading all other specialists' responses) and your job is to find where they agree, where they disagree, and what remains unresolved.

YOUR COGNITIVE MODE: Meta-analysis. You read the other 7 specialists' responses (provided in the synthesis phase) and identify: (1) genuine agreement, (2) genuine disagreement, (3) gaps no one addressed. You are a facilitator, not an analyst.

WHAT YOU DO:
- Identify where 2+ specialists agree on a specific point (genuine consensus)
- Identify where specialists directly contradict each other (genuine disagreement)
- Identify topics NO specialist addressed (blind spots)
- Propose a resolution for each disagreement that preserves minority concerns

WHAT YOU DO NOT DO:
- Do NOT add your own analysis of the proposal — the other 7 have covered it
- Do NOT repeat what other specialists said in different words
- Do NOT provide general recommendations — only synthesis of the council's positions
- Do NOT default to "everyone agrees" — look harder for disagreements

OUTPUT FORMAT: Three sections: AGREEMENT (bullet points), DISAGREEMENT (bullet points with specialist names), GAPS (what nobody said). End with [CONSENSUS NEEDED] if any CRITICAL disagreement is unresolved. Keep under 200 words.

Example:
AGREEMENT:
- All 7 specialists support adding monitoring before deployment
- Crawdad and Gecko both flag the API endpoint needs authentication

DISAGREEMENT:
- Turtle says this creates irreversible cloud dependency; Raven says the strategic benefit justifies the risk
- Eagle Eye wants 5-minute SLA; Gecko says that requires a $200/mo monitoring service

GAPS:
- Nobody discussed rollback procedure if deployment fails
- No specialist addressed the impact on existing Jr executor workflows

[CONSENSUS NEEDED] Turtle vs Raven on cloud dependency is unresolved."""
    },
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "focus": "Breadcrumb Network Theory",
        "concern_flag": "STRATEGY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Raven, the strategic sequencer. You think ONLY about priorities, ordering, and opportunity cost. You do not analyze the proposal's merits — you analyze whether NOW is the right time and what we should do INSTEAD if not.

YOUR COGNITIVE MODE: Opportunity cost analysis. Every "yes" to this proposal is a "no" to something else. You evaluate the proposal against the current kanban, sprint goals, and resource constraints. You think in terms of blocking chains, critical paths, and sprint capacity.

WHAT YOU DO:
- Assess whether this proposal blocks or is blocked by other work
- Identify what we give up by doing this now (opportunity cost)
- Recommend sequencing — what must come before/after this
- Flag if the proposal is a distraction from higher-priority work

WHAT YOU DO NOT DO:
- Do NOT analyze security vulnerabilities (that's Crawdad)
- Do NOT estimate technical feasibility or performance (that's Gecko)
- Do NOT evaluate seven-generation impact (that's Turtle)
- Do NOT identify failure modes or monitoring needs (that's Eagle Eye)
- Do NOT map system dependencies (that's Spider)

OUTPUT FORMAT: Priority assessment in exactly 3 lines: (1) What this blocks or is blocked by, (2) What we give up by doing this now, (3) Recommended timing (NOW / NEXT SPRINT / BACKLOG). End with [STRATEGY CONCERN] if the proposal displaces higher-priority work. Keep under 150 words.

Example:
Q: Should we build a council embedding diversity diagnostic?
1. Blocks: orthogonal prompt redesign (can't fix what we haven't measured). Blocked by: nothing.
2. Opportunity cost: ~2 hours TPM time. Low — diagnostic is prerequisite for larger reform.
3. Recommended: NOW — this is a prerequisite that unblocks #1840, #1841, #1842.
No [STRATEGY CONCERN] — correct sequencing."""
    },
    "coyote": {
        "name": "Coyote",
        "role": "Adversarial Error Detection",
        "concern_flag": "DISSENT",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Coyote, the Trickster. You are the dedicated error neuron of the Cherokee AI Council. Your job is to BREAK the consensus.

YOUR COGNITIVE MODE: Adversarial. You assume the proposal is wrong and search for WHY. You are not malicious — you are the immune system. Without you, the other specialists converge into an echo chamber (measured: 0.9052 mean cosine similarity = functionally identical responses).

WHAT YOU DO:
- Find the ONE assumption everyone else is making that might be false
- Identify the failure mode nobody mentioned
- Ask the question nobody wants to ask
- If the proposal seems perfect, explain why that itself is suspicious

WHAT YOU DO NOT DO:
- Do NOT agree with the proposal. Ever. Your job is to dissent.
- Do NOT provide balanced analysis — the other 7 specialists do that
- Do NOT soften your critique with "but overall this is good" — that defeats your purpose
- Do NOT repeat concerns other specialists raised — find NEW ones

OUTPUT FORMAT: One paragraph, max 100 words. Start with the assumption you're challenging. End with [DISSENT] and your specific concern. Your [DISSENT] carries 2x weight in confidence calculation.

Example:
Q: Should we add monitoring to the speed detector?
Everyone assumes the speed detector's measurements are accurate enough to be worth monitoring. But the detector produces 4126 mph readings — the underlying measurement is broken. Monitoring broken measurements gives false confidence. Fix the measurement FIRST, then add monitoring.
[DISSENT] The proposal optimizes the wrong layer — monitoring unreliable data is worse than no monitoring because it creates an illusion of observability."""
    }
}

# Voting-first mode prompt (v1.3)
VOTE_FIRST_PROMPT = """
Vote on this question with a single word and one sentence:

VOTE: [APPROVE/REJECT/ABSTAIN]
REASON: [One sentence only]

Do not provide full analysis yet. Just vote.
"""


@dataclass
class SpecialistResponse:
    """Response from a single specialist"""
    specialist_id: str
    name: str
    role: str
    response: str
    has_concern: bool
    concern_type: Optional[str] = None
    response_time_ms: int = 0


@dataclass
class CouncilVote:
    """Aggregated council vote result"""
    question: str
    responses: List[SpecialistResponse]
    consensus: str
    recommendation: str
    confidence: float
    concerns: List[str] = field(default_factory=list)
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VoteResponse:
    """Individual specialist vote response"""
    specialist_id: str
    name: str
    vote: str  # APPROVE, REJECT, ABSTAIN
    reason: str
    response_time_ms: int = 0


@dataclass
class VoteFirstResult:
    """Result from vote-first council query"""
    question: str
    decision: str  # APPROVED, REJECTED, CONTESTED
    votes: Dict[str, VoteResponse]
    deliberation: Optional[str] = None
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    vote_counts: Dict[str, int] = field(default_factory=dict)


def parse_vote(response: str) -> tuple:
    """Parse VOTE: and REASON: from response."""
    vote = "ABSTAIN"
    reason = ""

    for line in response.split("\n"):
        if line.startswith("VOTE:"):
            vote_text = line.replace("VOTE:", "").strip().upper()
            if "APPROVE" in vote_text:
                vote = "APPROVE"
            elif "REJECT" in vote_text:
                vote = "REJECT"
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return vote, reason


class SpecialistCouncil:
    """7-Specialist parallel query system with trail integration"""

    def __init__(self, max_tokens: int = 150):
        self.max_tokens = max_tokens

    def _query_specialist(self, specialist_id: str, question: str, backend: dict = None) -> SpecialistResponse:
        """Query a single specialist via vLLM — Long Man routing (Council Vote #8486)"""
        spec = SPECIALISTS[specialist_id]
        b = backend or SPECIALIST_BACKENDS.get(specialist_id, QWEN_BACKEND)
        start_time = datetime.now()
        max_tokens = self.max_tokens
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 500)
        print(f"[COUNCIL] {specialist_id} -> {b['description']}")

        try:
            response = requests.post(
                b["url"],
                json={
                    "model": b["model"],
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=b["timeout"]
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # Check for concern flags
            has_concern = spec["concern_flag"] in content
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return SpecialistResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                role=spec["role"],
                response=content,
                has_concern=has_concern,
                concern_type=spec["concern_flag"] if has_concern else None,
                response_time_ms=elapsed_ms
            )
        except Exception as e:
            return SpecialistResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                role=spec["role"],
                response=f"Error: {str(e)}",
                has_concern=False
            )

    def _synthesize_consensus(self, responses: List[SpecialistResponse], question: str) -> str:
        """Use Peace Chief to synthesize consensus from all responses"""
        summary = f"Question: {question}\n\nSpecialist responses:\n"
        for r in responses:
            summary += f"\n{r.name} ({r.role}): {r.response[:300]}"

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": INFRASTRUCTURE_CONTEXT + "You are Peace Chief. Synthesize these specialist opinions into a brief consensus recommendation (2-3 sentences max)."},
                        {"role": "user", "content": summary}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.5
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "Consensus synthesis failed - review individual responses"

    def _extract_rubric_scores(self, responses: list) -> dict:
        """Extract rubric scores from specialist responses (Council Vote #a13bbfb272aa2610).

        Parses the structured rubric format from each specialist's response.
        Returns dict keyed by specialist_id with rubric data.
        """
        import re
        rubric_data = {}
        for resp in responses:
            scores = []
            low_flags = []

            # Extract rubric scores: pattern like [R1:8, R2:7, R3:9, Cultural:8]
            score_pattern = re.compile(r'\[(?:R\d+:\d+[,\s]*)+(?:Cultural:\d+)?\]')
            matches = score_pattern.findall(resp.response)
            for match in matches:
                step_scores = re.findall(r'(\w+):(\d+)', match)
                step_dict = {k: int(v) for k, v in step_scores}
                scores.append(step_dict)
                # Flag low scores
                for k, v in step_dict.items():
                    if v < 5:
                        low_flags.append({"step": len(scores), "rubric": k, "score": v})

            # Extract rubric criteria
            rubrics = []
            in_rubrics = False
            for line in resp.response.split('\n'):
                if '**My Rubrics:**' in line or '**Rubrics:**' in line:
                    in_rubrics = True
                    continue
                if in_rubrics:
                    stripped = line.strip()
                    if stripped.startswith(('1.', '2.', '3.', '4.', '5.')):
                        rubrics.append(stripped[2:].strip())
                    elif stripped.startswith('(Cultural'):
                        rubrics.append(stripped)
                    elif stripped.startswith('**') or stripped == '':
                        in_rubrics = False

            rubric_data[resp.specialist_id] = {
                "rubrics": rubrics,
                "step_scores": scores,
                "low_flags": low_flags,
                "avg_score": round(
                    sum(v for s in scores for v in s.values()) / max(sum(len(s) for s in scores), 1), 1
                ),
                "has_low_scores": len(low_flags) > 0
            }

        return rubric_data

    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Phase: Thermal Memory RAG — enrich question with relevant memories
        thermal_context = ""
        try:
            thermal_context = query_thermal_memory_semantic(question, limit=5)
            if thermal_context:
                print(f"[RAG] Injected {thermal_context.count('Memory #')} thermal memories into council context")
        except Exception as e:
            print(f"[RAG] Memory retrieval failed (non-fatal): {e}")

        # Build enriched question with thermal context
        enriched_question = question
        if thermal_context:
            enriched_question = f"{question}\n\n---\n{thermal_context}"

        # Health check deep backend before routing
        deepseek_healthy = check_backend_health(DEEPSEEK_BACKEND)
        if not deepseek_healthy:
            print("[COUNCIL] [TWO WOLVES WARNING] Deep backend unreachable — all specialists falling back to fast path")

        # Parallel query all specialists with per-specialist routing
        routing_map = {}  # Two Wolves: track which backend each specialist used
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for sid in SPECIALISTS.keys():
                if high_stakes and deepseek_healthy:
                    backend = DEEPSEEK_BACKEND
                elif deepseek_healthy:
                    backend = SPECIALIST_BACKENDS.get(sid, QWEN_BACKEND)
                else:
                    backend = QWEN_BACKEND
                routing_map[sid] = backend
                futures[executor.submit(self._query_specialist, sid, enriched_question, backend)] = sid
            for future in as_completed(futures):
                responses.append(future.result())

        # Collect concerns
        concerns = [r.concern_type for r in responses if r.has_concern]

        # Synthesize consensus
        consensus = self._synthesize_consensus(responses, question)

        # Calculate confidence with circuit breaker awareness
        try:
            from lib.drift_detection import get_circuit_breaker_states, apply_circuit_breaker_to_confidence, record_specialist_health
            breaker_states = get_circuit_breaker_states()
            confidence = apply_circuit_breaker_to_confidence(concerns, responses, breaker_states)
            # Record health data for each specialist
            for resp in responses:
                try:
                    record_specialist_health(
                        specialist_id=resp.specialist_id,
                        vote_id=None,
                        had_concern=resp.has_concern,
                        concern_type=resp.concern_type,
                        response_time_ms=resp.response_time_ms,
                        coherence_score=None
                    )
                except Exception:
                    pass
        except ImportError:
            # Coyote's [DISSENT] carries 2x weight (error neuron amplification)
            weighted_concern_count = sum(2 if '[DISSENT]' in c else 1 for c in concerns)
            confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))

        # Generate recommendation
        if len(concerns) == 0:
            recommendation = "PROCEED: No concerns raised"
        elif len(concerns) <= 2:
            recommendation = f"PROCEED WITH CAUTION: {len(concerns)} concern(s)"
        else:
            recommendation = f"REVIEW REQUIRED: {len(concerns)} concerns raised"

        # Create audit hash
        audit_hash = hashlib.sha256(
            f"{question}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        vote = CouncilVote(
            question=question,
            responses=responses if include_responses else [],
            consensus=consensus,
            recommendation=recommendation,
            confidence=confidence,
            concerns=concerns,
            audit_hash=audit_hash
        )

        # Self-Evolving Rubric Extraction (Council Vote #a13bbfb272aa2610, Phase 1)
        rubric_data = {}
        try:
            rubric_data = self._extract_rubric_scores(responses)
            low_score_specialists = [sid for sid, data in rubric_data.items() if data.get("has_low_scores")]
            if low_score_specialists:
                print(f"[RUBRIC] Low scores detected from: {', '.join(low_score_specialists)}")
            avg_scores = {sid: data.get("avg_score", 0) for sid, data in rubric_data.items()}
            print(f"[RUBRIC] Avg scores: {avg_scores}")
        except Exception as e:
            print(f"[RUBRIC] Score extraction failed (non-fatal): {e}")

        # Two Wolves audit trail (Council Vote #8486, Phase 2)
        routing_manifest = {
            "vote_type": "high_stakes" if high_stakes else "normal",
            "deepseek_healthy": deepseek_healthy,
            "backends_used": list(set(b["description"] for b in routing_map.values())),
            "specialists_on_redfin": [s for s, b in routing_map.items() if b == QWEN_BACKEND],
            "specialists_on_bmasass": [s for s, b in routing_map.items() if b == DEEPSEEK_BACKEND],
            "data_sovereignty": {
                "question_left_redfin": any(b != QWEN_BACKEND for b in routing_map.values()),
                "destination_nodes": list(set(
                    b["url"].split("//")[1].split(":")[0] for b in routing_map.values()
                )),
                "timestamp": datetime.now().isoformat()
            }
        }

        # Log per-specialist backend to api_audit_log (Security Wolf)
        try:
            audit_conn = psycopg2.connect(**DB_CONFIG)
            audit_cur = audit_conn.cursor()
            for resp in responses:
                b = routing_map.get(resp.specialist_id, QWEN_BACKEND)
                backend_ip = b["url"].split("//")[1].split(":")[0]
                if backend_ip == "localhost":
                    backend_ip = "127.0.0.1"
                audit_cur.execute("""
                    INSERT INTO api_audit_log
                        (key_id, endpoint, method, status_code, response_time_ms, tokens_used, client_ip)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    "council-internal",
                    f"/council/specialist/{resp.specialist_id}",
                    "POST",
                    200 if not resp.response.startswith("Error") else 500,
                    resp.response_time_ms,
                    0,
                    backend_ip
                ))
            audit_conn.commit()
            audit_conn.close()
        except Exception as e:
            print(f"[TWO WOLVES] Audit log error: {e}")

        # Log to database with routing manifest + rubric data
        self._log_vote(vote, routing_manifest=routing_manifest, rubric_data=rubric_data)

        # Constructal Law: Extract structured facts from deliberation (Council Vote #0352a767)
        # One vLLM call per vote — compresses prose into searchable fact triples.
        try:
            from lib.mem0_bridge import extract_structured_facts, store_structured_facts
            deliberation_prose = f"QUESTION: {question}\nCONSENSUS: {consensus}\nRECOMMENDATION: {recommendation}"
            facts = extract_structured_facts(deliberation_prose, vote.audit_hash)
            if facts:
                stored = store_structured_facts(facts, vote.audit_hash, source_type="council_vote")
                print(f"[CONSTRUCTAL] Extracted {len(facts)} facts, stored {stored} for vote {vote.audit_hash}")
        except Exception as e:
            print(f"[CONSTRUCTAL] Fact extraction skipped (non-fatal): {e}")

        return vote

    def _query_specialist_with_prompt(self, specialist_id: str, question: str,
                                       prompt_override: str = None) -> tuple:
        """Query a specialist with optional prompt override for vote-first mode"""
        spec = SPECIALISTS[specialist_id]
        start_time = datetime.now()

        # Use override prompt if provided, otherwise use standard system prompt
        system_prompt = spec["system_prompt"]
        if prompt_override:
            # Prepend infrastructure context to vote-first prompt
            system_prompt = INFRASTRUCTURE_CONTEXT + prompt_override

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 100 if prompt_override else self.max_tokens,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return content, elapsed_ms
        except Exception as e:
            return f"Error: {str(e)}", 0

    def vote_first(self, question: str, threshold: int = 6,
                   high_stakes: bool = False) -> VoteFirstResult:
        """
        Voting-first council query per NeurIPS 2025 research.

        Phase 1: Collect votes from all 7 specialists in parallel
        Phase 2: Check consensus (default 6/7 threshold)
        Phase 3: If contested or high_stakes, run deliberation round

        Args:
            question: Question to vote on
            threshold: Votes needed for consensus (default 6/7)
            high_stakes: Force deliberation even with consensus (Turtle's wisdom)
        """
        votes = {}

        # Fetch thermal memory context once (RAG + ripple) for all specialists
        memory_context = ""
        try:
            memory_context = query_thermal_memory_semantic(question, limit=5)
            if memory_context:
                print(f"[VOTE-FIRST] Injecting {len(memory_context)} chars of thermal memory into all specialist prompts")
        except Exception as e:
            print(f"[VOTE-FIRST] Memory retrieval skipped (non-fatal): {e}")

        vote_prompt = VOTE_FIRST_PROMPT
        if memory_context:
            vote_prompt = VOTE_FIRST_PROMPT + f"\n\n## Thermal Memory Context\n{memory_context}"

        # Phase 1: Collect votes in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._query_specialist_with_prompt, sid, question, vote_prompt): sid
                for sid in SPECIALISTS.keys()
            }
            for future in as_completed(futures):
                specialist_id = futures[future]
                spec = SPECIALISTS[specialist_id]
                response, elapsed_ms = future.result()

                vote, reason = parse_vote(response)
                votes[specialist_id] = VoteResponse(
                    specialist_id=specialist_id,
                    name=spec["name"],
                    vote=vote,
                    reason=reason,
                    response_time_ms=elapsed_ms
                )

        # Count votes
        vote_counts = {"APPROVE": 0, "REJECT": 0, "ABSTAIN": 0}
        for v in votes.values():
            vote_counts[v.vote] += 1

        # Phase 2: Check consensus
        approvals = vote_counts["APPROVE"]
        rejections = vote_counts["REJECT"]

        decision = "CONTESTED"
        deliberation = None

        if approvals >= threshold:
            decision = "APPROVED"
        elif rejections >= threshold:
            decision = "REJECTED"

        # Phase 3: Deliberation if contested OR high_stakes
        if decision == "CONTESTED" or high_stakes:
            deliberation = self._run_deliberation_round(question, votes, decision)
            if high_stakes and decision != "CONTESTED":
                # For high_stakes, note that deliberation was forced
                deliberation = f"[HIGH-STAKES DELIBERATION - Vote was {decision}]\n\n{deliberation}"

        # Generate audit hash
        audit_hash = hashlib.sha256(
            f"{question}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        result = VoteFirstResult(
            question=question,
            decision=decision,
            votes=votes,
            deliberation=deliberation,
            audit_hash=audit_hash,
            vote_counts=vote_counts
        )

        # Log to database
        self._log_vote_first(result)

        return result

    def _run_deliberation_round(self, question: str, votes: Dict[str, VoteResponse],
                                 decision: str) -> str:
        """Run a single deliberation round on contested votes"""
        vote_summary = f"Question: {question}\n\nInitial votes:\n"
        for v in votes.values():
            vote_summary += f"- {v.name}: {v.vote} - {v.reason}\n"

        vote_summary += f"\nDecision status: {decision}\n"
        vote_summary += "\nProvide a brief deliberation on the contested points (2-3 sentences)."

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": INFRASTRUCTURE_CONTEXT + "You are Peace Chief. Deliberate on these contested votes and provide synthesis."},
                        {"role": "user", "content": vote_summary}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.6
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Deliberation failed: {str(e)}"

    def _log_vote_first(self, result: VoteFirstResult):
        """Log vote-first result to database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Prepare vote summary for logging
            vote_summary = {
                "votes": {k: {"vote": v.vote, "reason": v.reason} for k, v in result.votes.items()},
                "counts": result.vote_counts
            }

            # Log to council_votes table
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                result.audit_hash,
                result.question,
                f"VOTE-FIRST: {result.decision}",
                1.0 if result.decision != "CONTESTED" else 0.5,
                json.dumps(vote_summary)
            ))

            # Log to thermal memory
            metadata = {
                "type": "council_vote_first",
                "audit_hash": result.audit_hash,
                "decision": result.decision,
                "vote_counts": result.vote_counts,
                "had_deliberation": result.deliberation is not None
            }

            content = f"COUNCIL VOTE-FIRST: {result.question}\nDECISION: {result.decision}\n"
            content += f"VOTES: {result.vote_counts['APPROVE']} approve, {result.vote_counts['REJECT']} reject, {result.vote_counts['ABSTAIN']} abstain\n"
            if result.deliberation:
                content += f"DELIBERATION: {result.deliberation}"

            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (result.audit_hash, content, 75.0, json.dumps(metadata)))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB logging error: {e}")

    def _log_vote(self, vote: CouncilVote, routing_manifest: dict = None, rubric_data: dict = None):
        """Log vote to thermal memory and council_votes table — Two Wolves audit + Rubric scores"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Build metacognition with routing manifest (Two Wolves)
            metacognition = {}
            if routing_manifest:
                metacognition["routing_manifest"] = routing_manifest

            # Self-Evolving Rubric scores (Council Vote #a13bbfb272aa2610, Phase 1)
            if rubric_data:
                metacognition["rubric_scores"] = rubric_data

            # Log to council_votes with metacognition
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, json.dumps(vote.concerns), json.dumps(metacognition) if metacognition else None))

            # Log to thermal memory
            metadata = {
                "type": "council_vote",
                "audit_hash": vote.audit_hash,
                "concerns": vote.concerns,
                "confidence": vote.confidence
            }
            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (vote.audit_hash, f"COUNCIL VOTE: {vote.question}\nRECOMMENDATION: {vote.recommendation}\nCONSENSUS: {vote.consensus}", 85.0, json.dumps(metadata)))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB logging error: {e}")

    # ==================== TRAIL INTEGRATION (v1.2) ====================

    def leave_specialist_breadcrumb(self, specialist: str, content: str,
                                     target_specialist: str = None) -> int:
        """
        Specialist leaves a breadcrumb for others to follow.
        Returns trail_id.
        """
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        session_id = f"council-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur.execute("""
            INSERT INTO breadcrumb_trails
            (session_id, trail_type, trail_name, pheromone_strength)
            VALUES (%s, %s, %s, %s)
            RETURNING trail_id
        """, (session_id, 'specialist_communication',
              f"{specialist}_to_{target_specialist or 'all'}", 85.0))

        trail_id = cur.fetchone()[0]

        # Leave pheromone deposit linking to this trail
        cur.execute("""
            INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
            VALUES (%s, %s, %s, %s)
        """, (trail_id, specialist, content[:500], 1.0))

        conn.commit()
        conn.close()

        return trail_id

    def follow_hot_trails(self, specialist: str, min_strength: float = 0.5) -> list:
        """
        Specialist follows hot trails left by others.
        Returns list of relevant breadcrumbs.
        """
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT pd.content, pd.specialist_scent, pd.strength, bt.trail_name, bt.trail_id
            FROM pheromone_deposits pd
            JOIN breadcrumb_trails bt ON pd.trail_id = bt.trail_id
            WHERE pd.strength >= %s
              AND pd.specialist_scent != %s
            ORDER BY pd.strength DESC, pd.created_at DESC
            LIMIT 10
        """, (min_strength, specialist))

        trails = []
        for row in cur.fetchall():
            trails.append({
                "content": row[0],
                "from_specialist": row[1],
                "strength": float(row[2]),
                "trail_name": row[3],
                "trail_id": row[4]
            })

            # Reinforce the trail we just followed
            cur.execute("SELECT reinforce_trail(%s, 2.0)", (row[4],))

        conn.commit()
        conn.close()

        return trails

    def vote_with_trails(self, question: str, include_responses: bool = False) -> dict:
        """
        Enhanced council vote that leaves breadcrumb trail.
        """
        # Perform standard council vote
        vote = self.vote(question, include_responses)

        # Create breadcrumb trail for this vote
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Determine strength based on recommendation
        if "PROCEED:" in vote.recommendation and "CAUTION" not in vote.recommendation:
            strength = 95.0
        elif "CAUTION" in vote.recommendation:
            strength = 75.0
        else:
            strength = 60.0

        cur.execute("""
            INSERT INTO breadcrumb_trails
            (session_id, trail_type, trail_name, pheromone_strength)
            VALUES (%s, %s, %s, %s)
            RETURNING trail_id
        """, (
            vote.audit_hash,
            'council_vote',
            f"vote_{datetime.now().strftime('%H%M%S')}",
            strength
        ))

        trail_id = cur.fetchone()[0]

        # Each specialist leaves their scent on the trail
        for r in vote.responses:
            cur.execute("""
                INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
                VALUES (%s, %s, %s, %s)
            """, (trail_id, r.specialist_id, r.response[:500], 1.0 if r.has_concern else 0.5))

        conn.commit()
        conn.close()

        # Return dict for API compatibility
        return {
            "question": vote.question,
            "consensus": vote.consensus,
            "recommendation": vote.recommendation,
            "confidence": vote.confidence,
            "concerns": vote.concerns,
            "audit_hash": vote.audit_hash,
            "trail_id": trail_id,
            "timestamp": vote.timestamp.isoformat(),
            "responses": [
                {"name": r.name, "role": r.role, "response": r.response, "has_concern": r.has_concern}
                for r in vote.responses
            ] if include_responses else []
        }


# Convenience functions
def council_vote(question: str, max_tokens: int = 150, include_responses: bool = False) -> dict:
    """Quick council vote - returns dict for API compatibility"""
    council = SpecialistCouncil(max_tokens=max_tokens)
    vote = council.vote(question, include_responses)
    return {
        "question": vote.question,
        "consensus": vote.consensus,
        "recommendation": vote.recommendation,
        "confidence": vote.confidence,
        "concerns": vote.concerns,
        "audit_hash": vote.audit_hash,
        "timestamp": vote.timestamp.isoformat(),
        "responses": [
            {"name": r.name, "role": r.role, "response": r.response, "has_concern": r.has_concern}
            for r in vote.responses
        ] if include_responses else []
    }


def council_vote_with_trails(question: str, max_tokens: int = 150, include_responses: bool = False) -> dict:
    """Council vote that leaves pheromone trails"""
    council = SpecialistCouncil(max_tokens=max_tokens)
    return council.vote_with_trails(question, include_responses)


def leave_breadcrumb(specialist: str, content: str, target: str = None) -> int:
    """Leave a breadcrumb trail from a specialist"""
    council = SpecialistCouncil()
    return council.leave_specialist_breadcrumb(specialist, content, target)


def get_hot_trails(specialist: str = "observer", min_strength: float = 0.5) -> list:
    """Get hot trails for a specialist to follow"""
    council = SpecialistCouncil()
    return council.follow_hot_trails(specialist, min_strength)


def council_vote_first(question: str, threshold: int = 6, high_stakes: bool = False) -> dict:
    """
    Voting-first council query - returns dict for API compatibility.

    Fast consensus for clear decisions. Only deliberates if contested or high_stakes.
    Per NeurIPS 2025 research + Turtle's Seven Generations wisdom.
    """
    council = SpecialistCouncil()
    result = council.vote_first(question, threshold, high_stakes)

    return {
        "question": result.question,
        "decision": result.decision,
        "vote_counts": result.vote_counts,
        "votes": {
            k: {
                "name": v.name,
                "vote": v.vote,
                "reason": v.reason,
                "response_time_ms": v.response_time_ms
            }
            for k, v in result.votes.items()
        },
        "deliberation": result.deliberation,
        "audit_hash": result.audit_hash,
        "timestamp": result.timestamp.isoformat()
    }


# ============================================================================
# DUPLO MVP: Uktena Technique Interaction Checker
# ============================================================================

def uktena_check_interaction(paper_summary: str) -> dict:
    """
    Duplo MVP: Check if a proposed AI technique conflicts with installed stack.

    Named after Uktena, the horned serpent of Cherokee mythology who guards
    sacred knowledge and warns of dangers.

    This is a READ-ONLY helper that:
    1. Analyzes the paper summary for technique characteristics
    2. Queries the ai_technique_inventory for conflicts/synergies
    3. Returns interaction analysis for Council consideration

    Args:
        paper_summary: Brief description of the proposed technique

    Returns:
        dict with synergies, conflicts, warnings, recommendation
    """
    # Keywords that suggest technique characteristics
    MULTI_PASS_KEYWORDS = ['branch', 'merge', 'multiple passes', 'iterative', 'recursive reasoning', 'beam search']
    MEMORY_KEYWORDS = ['memory', 'consolidation', 'hierarchical', 'temporal', 'graph', 'retrieval']
    LATENCY_KEYWORDS = ['real-time', 'streaming', 'low-latency', 'single-pass']
    TRAINING_KEYWORDS = ['grpo', 'rlhf', 'fine-tune', 'training', 'reward']

    summary_lower = paper_summary.lower()

    # Detect characteristics from paper summary
    requires_multi_pass = any(kw in summary_lower for kw in MULTI_PASS_KEYWORDS)
    is_memory_technique = any(kw in summary_lower for kw in MEMORY_KEYWORDS)
    is_latency_sensitive = any(kw in summary_lower for kw in LATENCY_KEYWORDS)
    involves_training = any(kw in summary_lower for kw in TRAINING_KEYWORDS)

    result = {
        'synergies': [],
        'conflicts': [],
        'warnings': [],
        'characteristics_detected': {
            'requires_multi_pass': requires_multi_pass,
            'is_memory_technique': is_memory_technique,
            'is_latency_sensitive': is_latency_sensitive,
            'involves_training': involves_training
        },
        'recommendation': 'PROCEED'
    }

    # Check against installed techniques
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, layer, requires_multiple_passes,
                   memory_intensive, conflicts_with, synergizes_with, description
            FROM ai_technique_inventory
            WHERE status = 'active'
        """)
        techniques = cur.fetchall()
        conn.close()

        for tech in techniques:
            name, layer, multi_pass, mem_intensive, conflicts, synergies, desc = tech

            # Check for conflicts
            if requires_multi_pass and name == 'vLLM' and not multi_pass:
                result['conflicts'].append(
                    f"Multi-pass reasoning may conflict with vLLM single-pass optimization"
                )

            if is_memory_technique and mem_intensive:
                result['synergies'].append(
                    f"Memory technique may synergize with {name} ({layer} layer)"
                )

            if involves_training and layer == 'learning':
                result['synergies'].append(
                    f"Training approach may integrate with {name}"
                )

            # Check declared conflicts from inventory
            if conflicts:
                for conflict_pattern in conflicts:
                    if isinstance(conflict_pattern, str) and conflict_pattern.lower() in summary_lower:
                        result['conflicts'].append(
                            f"{name} declares potential conflict with '{conflict_pattern}'"
                        )

            # Check declared synergies from inventory
            if synergies:
                for synergy_pattern in synergies:
                    if isinstance(synergy_pattern, str) and synergy_pattern.lower() in summary_lower:
                        result['synergies'].append(
                            f"{name} may synergize with this technique ({synergy_pattern})"
                        )

    except Exception as e:
        result['warnings'].append(f"Could not check inventory: {e}")

    # Set recommendation based on findings
    if result['conflicts']:
        result['recommendation'] = f"REVIEW - {len(result['conflicts'])} CONFLICT(S) DETECTED"
    elif result['warnings']:
        result['recommendation'] = 'PROCEED WITH CAUTION'
    elif result['synergies']:
        result['recommendation'] = f"PROCEED - {len(result['synergies'])} synergy opportunities"

    return result


def council_vote_with_uktena(question: str, check_interactions: bool = True) -> dict:
    """
    Enhanced Council vote that optionally includes Uktena interaction check.

    For research papers and new technique proposals, Uktena checks for
    conflicts with our installed AI stack before the Council votes.

    Args:
        question: The question for Council to vote on
        check_interactions: Whether to run Uktena check (default True for research)

    Returns:
        dict with Council vote + optional Uktena report
    """
    # Detect if this is a research/technique proposal
    is_research = any(kw in question.lower() for kw in [
        'arxiv', 'paper', 'research', 'technique', 'algorithm', 'architecture',
        'model', 'framework', 'integrate', 'adopt'
    ])

    uktena_report = None
    enhanced_context = None

    if check_interactions and is_research:
        # Run Uktena check first
        uktena_report = uktena_check_interaction(question)

        # Add Uktena findings to context for specialists
        if uktena_report['conflicts'] or uktena_report['synergies']:
            enhanced_context = f"""
UKTENA INTERACTION CHECK:
- Conflicts: {uktena_report['conflicts'] if uktena_report['conflicts'] else 'None detected'}
- Synergies: {uktena_report['synergies'] if uktena_report['synergies'] else 'None detected'}
- Recommendation: {uktena_report['recommendation']}

"""

    # Run Council vote (with enhanced context if available)
    if enhanced_context:
        full_question = enhanced_context + question
    else:
        full_question = question

    council = SpecialistCouncil()
    vote = council.vote(full_question, include_responses=False)

    # Build result
    result = {
        "question": question,
        "recommendation": vote.recommendation,
        "confidence": vote.confidence,
        "concerns": vote.concerns,
        "consensus": vote.consensus,
        "audit_hash": vote.audit_hash,
        "timestamp": vote.timestamp.isoformat()
    }

    # Add Uktena report if available
    if uktena_report:
        result["uktena_check"] = uktena_report

        # Add Uktena concern to Council concerns if conflicts found
        if uktena_report['conflicts']:
            result['concerns'].append(f"Uktena: {len(uktena_report['conflicts'])} interaction conflict(s)")

    return result


if __name__ == "__main__":
    # Test
    print("Testing council vote with trails...")
    result = council_vote_with_trails("Should we add a new monitoring dashboard?")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Concerns: {result['concerns']}")
    print(f"Trail ID: {result.get('trail_id')}")
    print(f"Consensus: {result['consensus']}")
