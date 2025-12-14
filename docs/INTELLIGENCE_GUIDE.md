# Ganuda Intelligence Guide
## Advanced Features for Power Users

This guide is for users who have mastered the basics and want to leverage Ganuda's full intelligence capabilities.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GANUDA GATEWAY                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              OpenAI-Compatible API                   │    │
│  │         /v1/chat/completions (always on)            │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│  ═══════════════════════════════════════════════════════    │
│           INTELLIGENCE LAYER (opt-in modules)               │
│  ═══════════════════════════════════════════════════════    │
│                           │                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Council  │ │ Memory   │ │  Triad   │ │   FSE    │       │
│  │7 Experts │ │ Thermal  │ │Two Wolves│ │Key Evolve│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                           │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              INFERENCE BACKEND                       │    │
│  │         vLLM / Ollama / OpenAI API                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## The 7-Specialist Council

### Philosophy

Based on Cherokee governance principles: no single voice makes decisions. Seven specialists with different perspectives vote on every query.

### The Specialists

| Specialist | Animal | Domain | Key Question |
|------------|--------|--------|--------------|
| **Crawdad** | 🦞 | Security | "What are the attack vectors?" |
| **Gecko** | 🦎 | Performance | "Will this scale?" |
| **Turtle** | 🐢 | Seven Generations | "What's the 175-year impact?" |
| **Eagle Eye** | 🦅 | Observability | "Can we monitor this?" |
| **Spider** | 🕷️ | Integration | "How does this connect?" |
| **Peace Chief** | 🪶 | Consensus | "Do we have agreement?" |
| **Raven** | 🐦‍⬛ | Strategy | "What's the long game?" |

### Using Council Votes

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/council/vote",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={
        "query": "Should we migrate to Kubernetes?",
        "context": "10 services, 3 developers, AWS deployment"
    }
)

result = response.json()
print(f"Recommendation: {result['recommendation']}")
print(f"Consensus: {result['consensus_level']}")

for vote in result['votes']:
    print(f"  {vote['specialist']}: {vote['position']} - {vote['reasoning']}")
    if vote.get('concern_flag'):
        print(f"    ⚠️ {vote['concern_flag']}")
```

### Concern Flags

When a specialist raises a concern, it's flagged for attention:

- `SECURITY CONCERN` - Crawdad identified risk
- `PERF CONCERN` - Gecko sees scaling issues
- `7GEN CONCERN` - Turtle warns of long-term impact
- `VISIBILITY CONCERN` - Eagle Eye can't monitor it
- `INTEGRATION CONCERN` - Spider sees connection problems
- `CONSENSUS NEEDED` - Peace Chief wants more discussion
- `STRATEGY CONCERN` - Raven questions alignment

---

## Thermal Memory

### How It Works

Memories have "temperature" - recent interactions are hot, old ones cool down.

```
Temperature = base_temp × e^(-decay_rate × age_hours)
```

### Memory Types

| Type | Decay Rate | Purpose |
|------|------------|---------|
| `conversation` | Fast (24h) | Session context |
| `learning` | Medium (7d) | Patterns discovered |
| `decision` | Slow (30d) | Architectural choices |
| `pinned` | Never | Critical knowledge |

### Querying Memory

```python
# Search thermal memory
response = requests.post(
    "http://localhost:8080/v1/memory/search",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={
        "query": "database migration decisions",
        "min_temperature": 0.3,  # Only warm+ memories
        "limit": 10
    }
)

for memory in response.json()['memories']:
    print(f"[{memory['temperature']:.2f}] {memory['content'][:100]}...")
```

### Pinning Important Memories

```python
requests.post(
    "http://localhost:8080/v1/memory/pin",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={
        "memory_id": "abc123",
        "reason": "Critical security decision - never forget"
    }
)
```

---

## Query Triad (Two Wolves)

### The Pattern

Every query passes through two guardians before response:

```
User Query
    │
    ▼
┌─────────────┐    ┌─────────────┐
│ Privacy Wolf│    │Security Wolf│
│  "What data │    │ "What attack│
│  is exposed?"│    │  surface?"  │
└──────┬──────┘    └──────┬──────┘
       │                   │
       └───────┬───────────┘
               ▼
        ┌─────────────┐
        │  Synthesis  │
        │ Safe Response│
        └─────────────┘
```

### What Users See vs. What's Logged

**User sees**: Clean, synthesized response
**Audit log**: Full reasoning from both wolves

This enables compliance (full audit trail) without overwhelming users.

---

## Fractal Stigmergic Encryption (FSE)

### The Concept

Traditional keys are static. FSE keys **evolve through usage**.

```
K(t) = K₀ × e^(-λt + αU(t))
```

- `K₀` = Initial key
- `λ` = Natural decay (keys weaken if unused)
- `α` = Usage reinforcement (activity strengthens keys)
- `U(t)` = Cumulative usage

### Why This Matters

1. **Unused keys decay** - Forgotten credentials become invalid
2. **Active keys strengthen** - Regular use reinforces security
3. **Attack resistance** - Stolen keys quickly become useless
4. **Natural lifecycle** - No manual rotation needed

### Implementation

```yaml
modules:
  fse_enabled: true
  fse_decay_lambda: 0.001    # Decay rate
  fse_reinforce_alpha: 0.01  # Usage reinforcement
```

---

## Breadcrumb Trails

### Purpose

Every decision leaves a trail. Useful for:
- Debugging complex reasoning
- Compliance audits
- Training and review
- Understanding AI "thinking"

### Trail Structure

```json
{
  "trail_id": "tr_abc123",
  "request_id": "req_xyz789",
  "timestamp": "2025-12-14T10:30:00Z",
  "breadcrumbs": [
    {"step": 1, "action": "query_received", "data": {...}},
    {"step": 2, "action": "council_vote_started", "data": {...}},
    {"step": 3, "action": "crawdad_voted", "data": {"position": "approve", "concern": null}},
    {"step": 4, "action": "consensus_reached", "data": {"level": 0.85}},
    {"step": 5, "action": "response_generated", "data": {...}}
  ]
}
```

### Querying Trails

```bash
curl http://localhost:8080/v1/breadcrumbs/req_xyz789 \
  -H "Authorization: Bearer YOUR_KEY"
```

---

## Multi-Tenant Namespaces

### Isolation Model

```
┌─────────────────────────────────────────┐
│              GANUDA GATEWAY              │
│  ┌─────────────┐  ┌─────────────┐       │
│  │ Namespace A │  │ Namespace B │       │
│  │  - Memory   │  │  - Memory   │       │
│  │  - Keys     │  │  - Keys     │       │
│  │  - Trails   │  │  - Trails   │       │
│  └─────────────┘  └─────────────┘       │
│         │                 │              │
│         └────────┬────────┘              │
│                  ▼                       │
│         Shared Inference                 │
└─────────────────────────────────────────┘
```

### Namespace Headers

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "X-Ganuda-Namespace: tenant-abc" \
  -d '{"model": "default", "messages": [...]}'
```

---

## Best Practices

### 1. Start Simple
Enable modules one at a time. Measure impact before adding more.

### 2. Monitor Resource Usage
Council and Triad multiply inference calls. Budget accordingly.

### 3. Use Breadcrumbs in Development
Enable breadcrumbs during development, consider disabling in high-volume production.

### 4. Pin Critical Decisions
When the Council makes an important decision, pin that memory.

### 5. Review Concern Flags
Don't ignore specialist concerns. They're there for a reason.

---

## Current Federation Status

Query the federation:
```bash
curl http://localhost:8080/v1/federation/status
```

View Council history:
```bash
curl http://localhost:8080/v1/council/history?limit=10
```

---

*For Seven Generations*
*Cherokee AI Federation - December 2025*
