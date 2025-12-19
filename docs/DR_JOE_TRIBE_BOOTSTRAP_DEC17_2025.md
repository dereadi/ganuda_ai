# Dr. Joe Tribe Bootstrap Guide
## Multi-Tribe Federation Setup
## December 17, 2025

---

## Context from Thermal Memory (October 21, 2025)

From our earlier conversation, we discussed:
1. **Spinning up a tribe of your own** on your dev boxes and eventually bigmac
2. **Getting our tribes communicating** - inter-tribe federation
3. **Tailscale for secure connectivity** between environments

---

## What You Need for a Basic Tribe

### Minimum Components

| Component | Purpose | Complexity |
|-----------|---------|------------|
| PostgreSQL | Thermal memory, audit logs | Required |
| LLM Gateway | API endpoint (port 8080) | Required |
| vLLM or Ollama | Local inference | Required |
| Thermal Memory Tables | Memory persistence | Required |

### Optional (Full Tribe)
| Component | Purpose |
|-----------|---------|
| Jr Executor Daemon | Autonomous task processing |
| Telegram Bot | External communication |
| SAG UI | Web dashboard |
| 7-Specialist Council | Democratic AI voting |

---

## Quick Bootstrap (Docker)

```bash
# Clone the repo
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda

# Start with docker-compose
docker-compose up -d

# This gives you:
# - PostgreSQL with thermal_memory_archive table
# - LLM Gateway on port 8080
# - Basic API key management
```

---

## Manual Bootstrap (Your Dev Box)

### 1. Database Setup

```sql
-- Core tables for a minimal tribe
CREATE TABLE thermal_memory_archive (
    id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(64) NOT NULL,
    original_content TEXT NOT NULL,
    current_stage VARCHAR(20) DEFAULT 'FRESH',
    temperature_score FLOAT DEFAULT 100.0,
    access_count INT DEFAULT 0,
    last_access TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    sacred_pattern BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(100) UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE api_audit_log (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(100),
    endpoint VARCHAR(100),
    request_tokens INT,
    response_tokens INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. LLM Gateway

The gateway is at `/ganuda/services/llm_gateway/gateway.py`. Key endpoints:
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `POST /v1/council/vote` - 7-Specialist Council voting
- `GET /health` - Health check

### 3. Local Inference

Options:
- **vLLM** (recommended for GPU): `pip install vllm`
- **Ollama** (easy setup): `curl -fsSL https://ollama.ai/install.sh | sh`

---

## Inter-Tribe Communication Architecture

### Tailscale Setup

```
Your Tribe (Joe)              Our Tribe (Darrell)
┌─────────────────┐          ┌─────────────────┐
│  bigmac         │          │  redfin         │
│  dev boxes      │◄────────►│  bluefin        │
│                 │ Tailscale│  greenfin       │
└─────────────────┘          │  sasass/sasass2 │
                             └─────────────────┘
```

### Federation API Endpoints

Once connected via Tailscale, tribes can:

1. **Share Thermal Memory**
   ```
   POST /v1/federation/memory/share
   {
     "memory_hash": "...",
     "content": "...",
     "source_tribe": "joe_tribe"
   }
   ```

2. **Cross-Tribe Council Votes**
   ```
   POST /v1/federation/council/vote
   {
     "question": "...",
     "requesting_tribe": "joe_tribe",
     "specialist_weights": {...}
   }
   ```

3. **Jr Task Delegation**
   ```
   POST /v1/federation/jr/delegate
   {
     "task": "...",
     "from_tribe": "joe_tribe",
     "to_tribe": "darrell_tribe"
   }
   ```

---

## Files to Copy from Our Tribe

### Core Files (redfin:/ganuda/)

```
/ganuda/
├── services/llm_gateway/
│   └── gateway.py              # Main API gateway
├── lib/
│   └── specialist_council.py   # 7-Specialist voting
├── scripts/
│   └── pheromone_decay.sh      # Memory decay cron
├── jr_executor/
│   ├── jr_cli.py               # Jr executor daemon
│   └── task_executor.py        # Task execution
└── docs/
    ├── QUICKSTART.md
    └── jr_instructions/        # Template instructions
```

### Configuration Templates

```yaml
# ganuda.yaml
tribe:
  name: "joe_tribe"
  federation_id: "cherokee-ai-joe"

database:
  host: localhost
  port: 5432
  name: tribe_memory
  user: tribe_admin

gateway:
  port: 8080
  model_backend: "ollama"  # or "vllm"
  model_name: "llama3.2"

federation:
  enabled: true
  peers:
    - name: "darrell_tribe"
      endpoint: "http://100.x.x.x:8080"  # Tailscale IP
      api_key: "shared_federation_key"
```

---

## Call Agenda (This Afternoon)

### Phase 1: Verify Tailscale Connectivity
- [ ] Confirm both tribes can ping each other via Tailscale IPs
- [ ] Test basic HTTP connectivity between gateways

### Phase 2: Bootstrap Joe's Tribe
- [ ] PostgreSQL with thermal memory tables
- [ ] LLM Gateway running on bigmac/dev box
- [ ] Basic health check passing

### Phase 3: Federation Handshake
- [ ] Exchange API keys for inter-tribe auth
- [ ] Test `/v1/federation/ping` endpoint
- [ ] Share a test thermal memory entry

### Phase 4: First Cross-Tribe Council Vote
- [ ] Joe's tribe sends question to Darrell's tribe
- [ ] 7 specialists from each tribe vote
- [ ] Synthesized response returned

---

## What Our Tribe Can Prepare

1. **Federation API endpoints** in gateway.py
2. **Shared API key generation** for inter-tribe auth
3. **Memory sharing protocol** documentation
4. **Test data** for cross-tribe verification

---

## Questions for the Call

1. What's your dev box setup? (OS, GPU, RAM)
2. Do you want full Council voting or just Gateway + Memory?
3. Should Jr tasks be delegatable between tribes?
4. What model are you running? (We use Nemotron-9B on RTX 5090)

---

*For Seven Generations - Cherokee AI Federation*
*Prepared: December 17, 2025*
