# Jr Instruction: Langfuse — Self-Hosted LLM Observability on Greenfin

**Epic**: LANGFUSE-EPIC (Cognitive Gaps Mar 15 2026)
**Council Vote**: Approved as Priority #3 in cognitive gap analysis
**Estimated SP**: 8
**Target Node**: greenfin (192.168.132.224)
**Status**: DEPLOYMENT COMPLETE (Mar 16 2026) — Langfuse v2.30.0 running via Podman, host networking, nftables port 3100 open to LAN. See JR-LANGFUSE-GATEWAY-WIRING-MAR16-2026.md for instrumentation.

---

## Objective

Deploy Langfuse (self-hosted, MIT license) on greenfin for LLM observability. We need to answer three concrete questions (Coyote gate):

1. **What does each council vote cost in tokens?** — Currently unknown.
2. **Which Jr tasks are the most expensive?** — No per-task token tracking.
3. **Are we wasting tokens on low-value queries?** — No query-level cost visibility.

## What Is Langfuse

Open-source LLM engineering platform. Provides:
- Trace visualization (see the full chain of LLM calls per request)
- Token cost tracking (per model, per request, per user)
- Prompt versioning and management
- Latency breakdown
- Quality scoring

GitHub: 19k+ stars, MIT license, self-hostable with PostgreSQL + Docker.

## Design — Council Concerns as Features

### Crawdad (Security)
- Langfuse stores prompts and completions. MUST be on greenfin LAN only — no external exposure.
- Bind to `127.0.0.1` or `192.168.132.224` only. No 0.0.0.0 binding.
- PII scrub on stored traces: integrate DomainTokenizer before traces are persisted.
- No Langfuse cloud — self-hosted only. Never send trace data externally.

### Turtle (Coexistence)
- Deploy alongside OpenObserve, not replacing it. Different concerns:
  - OpenObserve = system logs, metrics, infrastructure
  - Langfuse = LLM traces, token costs, prompt quality
- Separate PostgreSQL instance on greenfin (NOT bluefin). Use greenfin's local PG or SQLite.

### Spider (Dependencies)
- Langfuse requires: PostgreSQL (or SQLite for dev), Node.js runtime, Docker (preferred).
- Use Docker Compose for isolation. Do NOT install Node.js system-wide on greenfin.
- Pin Langfuse version — no auto-updates.

### Gecko (Resource Budget)
- Greenfin has 128 CPU cores and 124GB RAM. Langfuse is lightweight.
- AllowedCPUs: assign Langfuse its own CPU budget (e.g., CPUs 8-11, separate from BitNet's 0-7).
- Memory limit: 2GB max via Docker `--memory` flag.

### Coyote (Three Questions Gate)
- Langfuse MUST answer the three questions above within 1 week of deployment.
- If it cannot answer them, it's not earning its resource slot. Review and potentially remove.
- Do NOT add features beyond the three questions in Phase 1.

### DC-9 (Waste Heat)
- Langfuse itself must be lightweight. If it adds >5% CPU load to greenfin, it's too heavy.
- The whole point is making waste VISIBLE, not adding more of it.

## Implementation

### Step 1: Install Langfuse on greenfin via Docker Compose

```yaml
# /ganuda/services/langfuse/docker-compose.yml
version: '3.8'
services:
  langfuse:
    image: langfuse/langfuse:latest  # Pin to specific version after first deploy
    ports:
      - "192.168.132.224:3100:3000"  # LAN only, not 0.0.0.0
    environment:
      - DATABASE_URL=postgresql://langfuse:GENERATED_PASSWORD@langfuse-db:5432/langfuse
      - NEXTAUTH_SECRET=GENERATED_SECRET
      - NEXTAUTH_URL=http://192.168.132.224:3100
      - TELEMETRY_ENABLED=false  # No phone home
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 2G
    depends_on:
      - langfuse-db

  langfuse-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=langfuse
      - POSTGRES_PASSWORD=GENERATED_PASSWORD
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G

volumes:
  langfuse-data:
```

### Step 2: Instrument the gateway

In `/ganuda/services/llm_gateway/gateway.py`, add Langfuse tracing to LLM calls:

```python
from langfuse import Langfuse

langfuse = Langfuse(
    host="http://192.168.132.224:3100",
    public_key="pk-...",
    secret_key="sk-...",
)

# Wrap each LLM call with a trace
trace = langfuse.trace(name="council_vote", metadata={"vote_hash": audit_hash})
generation = trace.generation(
    name="specialist_query",
    model=model_name,
    input=messages,
    output=response,
    usage={"prompt_tokens": ..., "completion_tokens": ...},
)
```

### Step 3: Instrument Jr executor

Same pattern — wrap each Jr task execution with a Langfuse trace. Include task_id, step count, and total tokens.

### Step 4: Add Fire Guard health check

Add `http://192.168.132.224:3100/api/public/health` to Fire Guard's check list for greenfin.

### Step 5: Dashboard — Three Questions

Create Langfuse dashboard views for:
1. Token cost per council vote (grouped by vote_hash)
2. Token cost per Jr task (grouped by task_id)
3. Token cost per gateway query (sorted by cost descending, identify waste)

## Acceptance Criteria

1. Langfuse running on greenfin, accessible from LAN only
2. Gateway LLM calls traced with token counts
3. Jr executor calls traced with token counts
4. Dashboard answers the Three Questions
5. Fire Guard health check active
6. CPU load <5% on greenfin
7. No external data transmission (telemetry disabled, self-hosted only)

## What NOT To Do

- Do NOT expose Langfuse to the internet or DMZ
- Do NOT use Langfuse Cloud — self-hosted only
- Do NOT store traces on bluefin — greenfin local PG only
- Do NOT instrument consultation ring traces (external model responses contain tokenized data — security boundary)
- Do NOT auto-update Langfuse — pin the version
