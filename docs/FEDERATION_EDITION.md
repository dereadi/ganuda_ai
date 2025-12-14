# Ganuda Federation Edition
## Multi-Node AI Infrastructure

The Federation Edition extends Ganuda Gateway to operate across multiple nodes, enabling distributed AI inference with Cherokee governance principles.

---

## Federation Architecture

```
                    ┌─────────────────────┐
                    │   TPM Orchestrator  │
                    │   (tpm-macbook)     │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    redfin     │    │   bluefin     │    │   greenfin    │
│  GPU Inference│    │   Database    │    │   Daemons     │
│  192.168.132  │    │  192.168.132  │    │  192.168.132  │
│     .223      │    │     .222      │    │     .224      │
└───────────────┘    └───────────────┘    └───────────────┘
        │                                          
        │            ┌───────────────┐    ┌───────────────┐
        │            │    sasass     │    │   sasass2     │
        └───────────▶│  Mac Studio   │    │  Mac Studio   │
                     │  192.168.132  │    │  192.168.132  │
                     │     .241      │    │     .242      │
                     └───────────────┘    └───────────────┘
```

---

## Node Roles

### redfin (192.168.132.223) - GPU Inference
**Primary Services**:
- vLLM inference server (port 8000)
- LLM Gateway v1.2 (port 8080)
- SAG Unified Interface (port 4000)
- Kanban Board (port 3001)

**Hardware**: NVIDIA RTX 5090 (96GB VRAM)

**Key Paths**:
- `/ganuda/services/llm_gateway/` - Gateway code
- `/ganuda/config/ganuda.yaml` - Configuration
- `/ganuda/docs/` - Documentation

### bluefin (192.168.132.222) - Database
**Primary Services**:
- PostgreSQL (port 5432)
- Grafana monitoring (port 3000)

**Database**: `zammad_production`
- `thermal_memory_archive` - 5,200+ memories
- `council_votes` - Decision history
- `breadcrumb_trails` - Audit logs
- `api_keys` - Authentication

**Credentials**: claude / jawaseatlasers2

### greenfin (192.168.132.224) - Daemons
**Primary Services**:
- Promtail log forwarding
- Monitoring agents
- Scheduled tasks

### sasass / sasass2 (Mac Studios) - Edge Development
**Role**: Development workstations, edge deployment testing

---

## Federation Services

### LLM Gateway (redfin:8080)

Core endpoints:
```
GET  /health                    - Health check with module status
GET  /v1/models                 - Available models
POST /v1/chat/completions       - Chat (OpenAI-compatible)
POST /v1/council/vote           - 7-Specialist voting
GET  /v1/council/history        - Vote history
GET  /v1/config/current         - Running configuration
```

Admin key: `ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5`

### vLLM Inference (redfin:8000)

Direct model access:
```bash
curl http://192.168.132.223:8000/v1/models
```

Current model: `nvidia/NVIDIA-Nemotron-Nano-9B-v2`

### SAG Unified Interface (redfin:4000)

ITSM dashboard integrating:
- Event Management
- Kanban Board
- Cherokee AI Monitoring
- IoT Device Management
- Email Intelligence

### Thermal Memory (bluefin)

Query directly:
```sql
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
  SELECT content, pheromone_strength, created_at 
  FROM thermal_memory_archive 
  WHERE pheromone_strength > 0.5 
  ORDER BY created_at DESC 
  LIMIT 10;
"
```

---

## Federation Communication

### Node Discovery
Nodes announce via thermal memory with type `node_heartbeat`.

### Cross-Node Queries
Gateway on redfin routes to bluefin for persistence, greenfin for monitoring.

### Triad Consultation
For architectural decisions, consult all node Triads:

```bash
# Consult each node's perspective
for node in 192.168.132.222 192.168.132.223 192.168.132.224; do
  echo "=== Node $node ==="
  curl -s http://$node:8080/v1/council/vote \
    -H "Authorization: Bearer $API_KEY" \
    -d '{"query": "Your question here"}' | jq '.recommendation'
done
```

---

## Deployment

### Prerequisites
- All nodes on same network (192.168.132.x)
- SSH access configured
- PostgreSQL accessible from gateway

### Starting the Federation

```bash
# On redfin - Start vLLM
cd /home/dereadi/vllm && ./start_vllm.sh

# On redfin - Start Gateway
cd /ganuda/services/llm_gateway
nohup python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 &

# On redfin - Start SAG UI
cd /home/dereadi/sag_unified_interface
nohup python app.py &

# On bluefin - Verify PostgreSQL
systemctl status postgresql

# On greenfin - Start monitoring
systemctl status promtail
```

### Health Check

```bash
# Gateway health
curl http://192.168.132.223:8080/health

# Database connectivity
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1"

# vLLM status
curl http://192.168.132.223:8000/health
```

---

## Maintenance

### Thermal Memory Decay
Runs nightly on bluefin at 3:33 AM:
```bash
/ganuda/scripts/pheromone_decay.sh
```

### Log Rotation
SAG UI logs rotate when exceeding 100MB.

### Backup
Database backups to `/ganuda/backups/` on bluefin.

---

## Security

### Network
- All services on private network (192.168.132.x)
- No public exposure without explicit proxy

### Authentication
- API keys stored hashed in PostgreSQL
- Admin key for federation management
- Per-tenant keys for isolation

### Audit
- All requests logged to `api_audit_log`
- Council votes preserved in `council_votes`
- Breadcrumb trails for decision tracing

---

## Cherokee Principles in Practice

### Seven Generations (Turtle)
Every architectural decision evaluated for 175-year impact.

### Consensus Governance (Peace Chief)
No single specialist can override the Council.

### Thermal Memory
Knowledge persists and evolves, mimicking oral tradition.

### Stigmergic Learning
System learns from usage patterns, not explicit programming.

---

*For Seven Generations*
*Cherokee AI Federation - December 2025*
