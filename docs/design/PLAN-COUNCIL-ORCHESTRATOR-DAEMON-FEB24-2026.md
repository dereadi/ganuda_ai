# Council Orchestrator Daemon — Design Plan

**Date:** 2026-02-24
**Author:** TPM
**Kanban:** #1835 (Level 5: Council Orchestrator Daemon, 21 SP)
**Council Vote Required:** Yes
**Status:** DESIGN — awaiting Council review

---

## 1. Objective

Extract the council voting lifecycle out of the gateway's synchronous request path and into a dedicated daemon that orchestrates specialist voting, manages TPM vote integration, and handles timeouts gracefully. The existing Jr instruction (JR-COUNCIL-ORCHESTRATOR-DAEMON-FEB23-2026) covers only TPM auto-triage of completed votes. This plan addresses the full lifecycle: request intake, parallel specialist queries, consensus synthesis, TPM integration, and thermal memory persistence.

---

## 2. Current Architecture — How Council Votes Flow Today

### 2.1 Entry Points

Three council vote endpoints live in `gateway.py` (redfin:8080):

| Endpoint | Mode | Description |
|----------|------|-------------|
| `POST /v1/council/vote` | parallel (default) or cascaded | Full 7-specialist deliberation + consensus synthesis |
| `POST /v1/council/vote-first` | vote-first | Fast consensus: specialists vote first, deliberate only if contested |
| `POST /v1/council/halo` | HALO | Task decomposition into specialist subtasks (experimental) |

### 2.2 Request Flow — `/v1/council/vote` (Primary Path)

The current flow executes entirely within a single FastAPI async handler (~250 lines in `gateway.py` lines 1115-1410):

```
Client POST /v1/council/vote
  |
  v
1. Temporal query detection + context retrieval
2. YAML constraint trigger analysis (per-specialist)
3. RAG thermal memory retrieval (HyDE -> pgvector -> reranker -> CRAG -> sufficiency) — ONCE for all specialists
4. Initialize MetacognitiveCouncil tracer
5. ThreadPoolExecutor(max_workers=8) — 7 specialists queried in PARALLEL
   |-- Each specialist query:
   |   a. Build enhanced prompt: system_prompt + memory_context + temporal_context + RAG + constraints + rubric instruction
   |   b. POST to vLLM (Qwen 72B on redfin:8000, timeout=60s)
   |   c. Extract concerns from response
   |   d. Update specialist memory state
   |   e. Record in metacognition tracer
6. Consensus synthesis: Peace Chief synthesizes all 7 responses via separate vLLM call
7. Self-Refine loop (RL2F Phase 0) — up to 3 rounds of critique/refine on consensus
8. Confidence calculation: weighted concerns (Coyote DISSENT = 2x)
9. Recommendation: PROCEED / PROCEED WITH CAUTION / REVIEW REQUIRED
10. Build routing manifest (Two Wolves audit trail)
11. INSERT into council_votes (tpm_vote='pending', 5-min window)
12. Per-specialist audit log entries
13. Create TPM notification (for Telegram/dashboard)
14. Return response to client (synchronous)
```

### 2.3 Parallel Pipeline in `specialist_council.py`

A **second, independent** implementation exists in `/ganuda/lib/specialist_council.py` (class `SpecialistCouncil`). This has its own specialist definitions, backend routing (SPECIALIST_BACKENDS dict with Raven/Turtle on DeepSeek, others on Qwen), and voting logic. The `council_vote_first()` function wraps this class.

**Critical observation:** Gateway SPECIALISTS and specialist_council.py SPECIALISTS are maintained in parallel. Prompt changes in one do not propagate to the other. The gateway copy has diverged (simpler prompts, no "focus" field, no examples). This is a known dual-pipeline problem.

### 2.4 Performance Characteristics

| Phase | Typical Latency | Bottleneck |
|-------|----------------|------------|
| RAG retrieval (HyDE + pgvector + reranker) | 2-5s | greenfin embedding service, redfin vLLM for HyDE |
| 7 specialist queries (parallel, vLLM) | 8-15s | vLLM KV cache contention — 7 concurrent prompts compete for 96GB |
| Consensus synthesis (1 vLLM call) | 2-4s | Sequential after all specialists complete |
| Self-Refine loop (0-3 rounds) | 0-12s | Each round = 2 vLLM calls (critique + refine) |
| DB writes + audit | <100ms | Negligible |
| **Total** | **12-36s** | Dominated by vLLM inference |

The specialists already run in parallel via ThreadPoolExecutor. The real bottleneck is vLLM: 7 concurrent requests to a single GPU sharing the same KV cache. This is not a parallelism problem — it is a resource contention problem. A daemon does not change this.

---

## 3. Proposed Architecture

### 3.1 Decision: Extract to Daemon vs. Keep in Gateway

**Recommendation: Keep voting orchestration in gateway, add daemon for TPM lifecycle only.**

Rationale:
- The specialist voting is already parallel (ThreadPoolExecutor, 8 workers). Moving it to a daemon adds IPC latency without reducing vLLM contention.
- The gateway's synchronous response is expected by callers (Telegram bots, SAG UI, Claude Code). An async daemon would require callers to poll for results — a breaking API change.
- The TPM vote lifecycle (auto-approve, timeout handling, escalation) is genuinely decoupled and benefits from daemon treatment.

### 3.2 Proposed Architecture — Two Components

```
                         +-----------------------+
                         |  gateway.py (redfin)  |
                         |  /v1/council/vote     |
                         +-----------+-----------+
                                     |
                     (existing flow, no change)
                                     |
                                     v
                         +-----------+-----------+
                         |   council_votes (DB)  |
                         |   tpm_vote='pending'  |
                         +-----------+-----------+
                                     |
                  +------------------+------------------+
                  |                                     |
                  v                                     v
    +-------------+-------------+        +--------------+--------------+
    | council_orchestrator.py   |        |  /v1/council/vote/{hash}/tpm |
    | (daemon on redfin)        |        |  (manual TPM vote endpoint)  |
    |                           |        |  (stays in gateway)          |
    | - Polls pending votes     |        +-----------------------------+
    | - Auto-approves high-conf |
    | - Flags low-conf for Chief|
    | - Handles timeouts        |
    | - Telegram notifications  |
    | - Thermal memory logging  |
    +---------------------------+
```

### 3.3 Daemon Responsibilities (council_orchestrator.py)

1. **TPM Auto-Triage**: Poll `council_votes WHERE tpm_vote = 'pending' AND vote_window_expires < NOW()`. Auto-approve if confidence >= 0.85 and concern_count <= 1. Flag for Chief review if confidence < 0.60.

2. **Timeout Handling**: Votes that expire without TPM action get a `tpm_vote = 'timeout_approved'` or `tpm_vote = 'timeout_escalated'` depending on confidence. Currently, expired votes just sit forever.

3. **Escalation via Telegram**: Low-confidence votes that remain pending get escalated to Chief via `@derpatobot`. Include the question, confidence, concern summary, and a direct link to vote.

4. **Vote Analytics**: Track auto-approve rate, average TPM response time, timeout frequency. Persist to thermal memory for the council to learn from.

5. **Stale Vote Cleanup**: Votes older than 24 hours with `tpm_vote = 'pending'` get auto-closed with a summary reason.

### 3.4 What Does NOT Go in the Daemon

- **Specialist query orchestration**: Stays in gateway (already parallel, callers expect synchronous responses).
- **Consensus synthesis**: Stays in gateway (depends on specialist responses in same request context).
- **RAG retrieval**: Stays in gateway (same reason).
- **Self-Refine loop**: Stays in gateway.

---

## 4. Key Design Decisions

### 4.1 Async vs. Sync Specialist Queries

**Decision: Keep synchronous (status quo).**

The gateway is a FastAPI app with async handlers, but the specialist queries use `requests.post()` (synchronous) inside a `ThreadPoolExecutor`. This is the correct pattern: vLLM calls are CPU-bound from the client perspective (waiting for GPU inference), and ThreadPoolExecutor properly parallelizes them without blocking the event loop.

Switching to `httpx.AsyncClient` or `aiohttp` would reduce thread overhead but would not reduce wall-clock time — the bottleneck is vLLM serving 7 concurrent requests, not Python threading.

### 4.2 Specialist Parallelism: Already Solved

The gateway already uses `ThreadPoolExecutor(max_workers=8)` to fan out all 7 specialists in parallel. The latency profile confirms this: total time is roughly max(specialist_times) + synthesis_time, not sum(specialist_times).

The real optimization opportunity is **vLLM request scheduling**: with 7 concurrent prompts hitting the same 72B model, KV cache pressure causes mutual slowdown. Potential improvements (not in scope for this ticket):
- Batch specialist prompts into fewer vLLM requests (if vLLM supports multi-prompt batching)
- Reduce specialist max_tokens from 300 to 200 (already documented in prompts but not enforced)
- Hard cap rubric instruction injection for shorter prompts
- Use prefix caching (all 7 share INFRASTRUCTURE_CONTEXT + RAG context)

### 4.3 Dual Pipeline Consolidation

The gateway and `specialist_council.py` maintain separate SPECIALISTS dictionaries, separate backend routing, and separate prompt definitions. This is a known architectural debt. This design does NOT attempt to consolidate them. Consolidation should be its own kanban item because:
- Changing the gateway's SPECIALISTS dict risks breaking the production API
- The specialist_council.py version is used by vote-first mode, self-audit, and Jr executors
- Unifying requires careful testing across all consumers

### 4.4 Database Polling vs. Event-Driven

**Decision: Database polling (60s interval).**

PostgreSQL LISTEN/NOTIFY would reduce latency from up to 60s to near-instant. However:
- TPM vote latency is not time-critical (5-minute window)
- Polling is simpler to implement, debug, and recover from
- No new infrastructure dependencies
- Connection pool management with LISTEN requires dedicated connections

If vote volume increases beyond 100/day, revisit with LISTEN/NOTIFY.

---

## 5. Risk Analysis

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Auto-approve misfire**: Daemon approves a vote that should have been reviewed | HIGH | Conservative threshold (0.85 confidence + <=1 concern). Log all auto-decisions to thermal memory. Coyote DISSENT always forces manual review. |
| **Double-vote race condition**: TPM manually votes at the same moment daemon auto-votes | MEDIUM | Use `WHERE tpm_vote = 'pending'` as optimistic lock. Only process expired votes (`vote_window_expires < NOW()`). |
| **Daemon crash during poll**: Leaves votes in inconsistent state | LOW | All operations are idempotent. Daemon restart picks up where it left off. No in-memory state. |
| **Telegram spam**: Too many notifications for Chief | MEDIUM | Rate limit to max 5 notifications per hour. Batch low-priority votes into digest. |
| **Gateway dual-pipeline drift**: Changes to gateway SPECIALISTS not reflected in specialist_council.py | HIGH (existing) | Out of scope for this ticket. Flag for future consolidation. |
| **vLLM contention from 7 concurrent queries**: Slows all specialist responses | MEDIUM (existing) | Not addressed by daemon. Potential future optimization: prefix caching, reduced max_tokens. |

---

## 6. Recommended Phasing

### Phase 1: TPM Auto-Triage Daemon (8 SP) — Ships First

**Scope:** The existing Jr instruction (JR-COUNCIL-ORCHESTRATOR-DAEMON-FEB23-2026) covers most of this.

Additions beyond the existing Jr instruction:
- Timeout handling: `tpm_vote = 'timeout_approved'` for high-confidence expired votes
- Coyote DISSENT guard: never auto-approve if any concern contains `[DISSENT]`
- Use `lib/secrets_loader` for DB credentials instead of hardcoded config
- Systemd service file for daemon lifecycle
- Graceful shutdown with connection pool cleanup (already in Jr instruction)

**Deliverables:**
- `/ganuda/daemons/council_orchestrator.py`
- `/ganuda/scripts/systemd/council-orchestrator.service`
- Thermal memory logging for all auto-decisions

### Phase 2: Telegram Escalation (5 SP)

**Scope:** Integrate with `@derpatobot` for Chief notifications.

- Low-confidence votes (< 0.60) generate Telegram message to Chief
- Message includes: question (truncated), confidence, top concerns, link to vote endpoint
- Rate-limited: max 5 per hour, batch if exceeding
- Depends on: `telegram_notify.py` (already exists)

**Deliverables:**
- Telegram integration in `council_orchestrator.py`
- Rate limiter with sliding window

### Phase 3: Vote Analytics + Observability (5 SP)

**Scope:** Track voting patterns over time.

- Auto-approve rate (daily/weekly)
- Average TPM response time
- Timeout frequency
- Confidence distribution of auto-approved vs. manually reviewed votes
- Expose metrics via `/v1/council/analytics` endpoint in gateway
- Persist summary to thermal memory (weekly)

### Phase 4: Future Considerations (3 SP — backlog)

- **Dual pipeline consolidation**: Unify SPECIALISTS between gateway and specialist_council.py
- **LISTEN/NOTIFY**: Replace polling if vote volume exceeds 100/day
- **vLLM prefix caching**: Shared INFRASTRUCTURE_CONTEXT + RAG context across all 7 specialists
- **Graduated auto-approve**: Train threshold from historical TPM decisions (RL2F crossover)

---

## 7. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `council_votes` table | LIVE | 8,674+ rows, schema includes `tpm_vote`, `vote_window_expires`, `metacognition` |
| `thermal_memory_archive` | LIVE | Target for vote decision logging |
| `lib/secrets_loader.py` | LIVE | DB credentials, replaces hardcoded config |
| `telegram_notify.py` | LIVE | For Phase 2 escalation |
| `@derpatobot` / `derpatobot.service` | LIVE | Telegram bot for Chief notifications |
| `psycopg2.pool` | Available | Already used by `tpm_autonomic_v2.py` as pattern |

---

## 8. What This Is NOT

- This is **not** a rewrite of council voting. The gateway's specialist orchestration stays intact.
- This is **not** a solution for vLLM contention. That requires inference-layer changes.
- This is **not** a dual-pipeline consolidation. That is separate technical debt.
- This is **not** an async voting API. Callers still get synchronous responses from the gateway.

The daemon's purpose is narrow and specific: automate the TPM vote lifecycle that currently requires manual intervention or silently expires.
