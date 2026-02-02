# Ultrathink: ii-researcher Federation Integration

**Date:** January 28, 2026
**Council Vote:** 166956a7959c2232 (79.4% confidence)
**Priority:** P1 - Platform capability
**TPM:** Claude Opus

---

## Executive Summary

Integrate ii-researcher as the federation-wide deep search capability, enabling web research for Telegram Chief, VetAssist, and all Jr workers via our existing vLLM infrastructure.

---

## Council Concerns & Mitigations

| Concern | Specialist | Mitigation |
|---------|------------|------------|
| Security | Crawdad | Sandbox external requests, no PII in queries, audit logging |
| Performance | Gecko | Cache results, rate limiting, async processing |
| Strategy | Raven | Phased rollout, validate accuracy on our use cases |
| 7GEN | Turtle | Data sovereignty, no vendor lock-in (local LLMs) |
| Visibility | Eagle Eye | Metrics dashboard, search logging |
| Consensus | Peace Chief | Document integration points, team review |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CHEROKEE AI FEDERATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Telegram     │  │  VetAssist   │  │  Jr Workers  │       │
│  │ Chief        │  │  Dashboard   │  │  (SE, IT,    │       │
│  │              │  │              │  │   Research)  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│                    ┌──────▼──────┐                          │
│                    │ ii-researcher│                          │
│                    │ (FastAPI)    │                          │
│                    │ Port: 8090   │                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐        │
│  │  LiteLLM    │  │   Tavily    │  │  SerpAPI    │        │
│  │  Proxy      │  │   Search    │  │  (backup)   │        │
│  │  Port: 8081 │  │             │  │             │        │
│  └──────┬──────┘  └─────────────┘  └─────────────┘        │
│         │                                                   │
│  ┌──────▼──────┐                                           │
│  │    vLLM     │                                           │
│  │ Nemotron-9B │                                           │
│  │  Port: 8000 │                                           │
│  └─────────────┘                                           │
│                                                              │
│  redfin (192.168.132.223)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Installation (Infrastructure Jr.)

1. Clone ii-researcher to `/ganuda/services/ii-researcher`
2. Create Python venv with dependencies
3. Configure LiteLLM proxy for vLLM backend
4. Set up Tavily API key (free tier: 1000 searches/month)
5. Create systemd service

### Phase 2: API Integration (Software Engineer Jr.)

1. Create `/ganuda/lib/research_client.py` - unified research interface
2. Add research endpoint to LLM Gateway (`/v1/research`)
3. Integrate with Telegram Chief commands (`/research <query>`)
4. Add VetAssist research panel

### Phase 3: Security Hardening (IT Triad Jr.)

1. Audit logging for all searches
2. PII detection before query submission
3. Rate limiting (10 searches/minute per user)
4. Sandboxed execution environment

---

## Files to Create

| File | Description |
|------|-------------|
| `/ganuda/services/ii-researcher/` | Cloned repository |
| `/ganuda/services/ii-researcher/.env` | API keys and config |
| `/ganuda/scripts/systemd/ii-researcher.service` | Systemd service |
| `/ganuda/lib/research_client.py` | Python client library |
| `/ganuda/services/llm_gateway/routes/research.py` | Gateway endpoint |

---

## Configuration

### Environment Variables

```bash
# /ganuda/services/ii-researcher/.env
OPENAI_API_BASE=http://localhost:8081/v1  # LiteLLM proxy
OPENAI_API_KEY=not-needed-for-local
TAVILY_API_KEY=tvly-xxxxx
DEFAULT_MODEL=nemotron-9b
SEARCH_PROVIDER=tavily
MAX_SOURCES=10
```

### LiteLLM Proxy Config

```yaml
# /ganuda/config/litellm_config.yaml
model_list:
  - model_name: nemotron-9b
    litellm_params:
      model: openai/nvidia/NVIDIA-Nemotron-Nano-9B-v2
      api_base: http://localhost:8000/v1
      api_key: not-needed
  - model_name: qwen-32b
    litellm_params:
      model: openai/Qwen/QwQ-32B
      api_base: http://localhost:8000/v1
      api_key: not-needed
```

---

## API Design

### Research Endpoint

```python
# POST /v1/research
{
    "query": "VA disability rating for tinnitus",
    "max_sources": 5,
    "depth": "standard",  # or "deep"
    "output_format": "summary"  # or "report"
}

# Response
{
    "answer": "Tinnitus is rated at 10% under diagnostic code 6260...",
    "sources": [
        {"url": "...", "title": "...", "snippet": "..."}
    ],
    "confidence": 0.87,
    "search_time_ms": 2340
}
```

### Telegram Integration

```
User: /research VA sleep apnea secondary to PTSD
Bot: 🔍 Researching...

📊 Research Results:
Sleep apnea can be service-connected secondary to PTSD...

Sources:
1. VA.gov - Secondary Conditions
2. BVA Decision 2024-12345
3. 38 CFR 3.310

Confidence: 87%
```

---

## Success Criteria

1. ii-researcher running as systemd service
2. LiteLLM proxy routing to vLLM
3. `/research` command working in Telegram
4. VetAssist research panel functional
5. All searches logged to audit table
6. < 5 second response time for standard queries

---

## Rollback Plan

```bash
sudo systemctl stop ii-researcher
sudo systemctl disable ii-researcher
# Gateway continues without research endpoint
```

---

## Cost Analysis

| Component | Cost |
|-----------|------|
| Tavily API | Free tier: 1000/month, then $0.01/search |
| vLLM | Already running (sunk cost) |
| LiteLLM | Open source, self-hosted |
| ii-researcher | Open source |

**Estimated monthly:** $0-50 depending on search volume

---

FOR SEVEN GENERATIONS
