# Ganuda Intelligence Modules

Ganuda includes optional intelligence modules that enhance the basic gateway. All modules are **disabled by default** for simplicity.

## Module Overview

| Module | Purpose | Config Flag | Resource Impact |
|--------|---------|-------------|-----------------|
| Council | Multi-perspective AI decisions | `council_enabled` | +3 API calls/request |
| Memory | Persistent context across sessions | `memory_enabled` | +PostgreSQL storage |
| Breadcrumbs | Decision trail logging | `breadcrumbs_enabled` | +Disk I/O |
| FSE | Fractal Stigmergic Encryption | `fse_enabled` | +CPU for key evolution |
| Triad | Privacy/Security dual review | `triad_enabled` | +2 API calls/request |
| Multi-Tenant | Namespace isolation | `multi_tenant_enabled` | +Auth overhead |

---

## Enabling Modules

Edit `/ganuda/config/ganuda.yaml` and set the module flag to `true`:

```yaml
modules:
  council_enabled: true    # Enable 7-Specialist Council
  memory_enabled: true     # Enable Thermal Memory
  # ... other modules
```

Then restart the gateway:

```bash
# Manual restart
pkill -f 'uvicorn gateway:app'
cd /ganuda/services/llm_gateway
nohup python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 &

# Or with Docker
docker-compose restart gateway
```

Verify module status: `curl http://localhost:8080/health`

---

## Module Details

### 1. Council (7-Specialist Voting)

**What it does**: Routes queries through 7 specialist perspectives before responding.

The 7 Specialists:
| Specialist | Role | Concern Flag |
|------------|------|--------------|
| Crawdad | Security | SECURITY CONCERN |
| Gecko | Technical Integration | PERF CONCERN |
| Turtle | Seven Generations Wisdom | 7GEN CONCERN |
| Eagle Eye | Monitoring | VISIBILITY CONCERN |
| Spider | Cultural Integration | INTEGRATION CONCERN |
| Peace Chief | Democratic Coordination | CONSENSUS NEEDED |
| Raven | Strategic Planning | STRATEGY CONCERN |

**When to enable**:
- Making architectural decisions
- Need diverse viewpoints on complex problems
- Want transparent reasoning trails

**Configuration**:
```yaml
modules:
  council_enabled: true
  council_specialists: 7
```

**API Endpoint**: `POST /v1/council/vote`

```bash
curl http://localhost:8080/v1/council/vote \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should we adopt microservices architecture?",
    "context": "Current monolith, 50k LOC, 3 developers"
  }'
```

---

### 2. Memory (Thermal Memory)

**What it does**: Persists context across sessions with time-based decay.

**When to enable**:
- Long-running projects
- Need continuity between conversations
- Building institutional knowledge

**Configuration**:
```yaml
modules:
  memory_enabled: true
  memory_thermal_decay: true
```

**How it works**:
- Recent interactions have high "temperature" (priority)
- Older memories decay over time (pheromone_strength decreases)
- Critical items can be "pinned" to prevent decay
- Stored in `thermal_memory_archive` table (5,200+ memories)

---

### 3. Breadcrumbs (Decision Trails)

**What it does**: Logs decision paths for audit and debugging.

**When to enable**:
- Compliance requirements
- Debugging complex reasoning
- Training and review

**Configuration**:
```yaml
modules:
  breadcrumbs_enabled: true
```

**Stored in**: `breadcrumb_trails` table

---

### 4. FSE (Fractal Stigmergic Encryption)

**What it does**: Keys evolve through usage patterns. More use = more secure.

**When to enable**:
- High-security environments
- Long-running deployments
- When key rotation alone isn't sufficient

**Configuration**:
```yaml
modules:
  fse_enabled: true
```

**Key Evolution Formula**: `K(t) = K₀ × e^(-λt + αU(t))`
- λ = natural decay rate
- α = usage reinforcement factor
- U(t) = cumulative usage at time t

---

### 5. Triad (Query Triad Interface)

**What it does**: Every query reviewed by Privacy Wolf and Security Wolf before response.

**When to enable**:
- Handling sensitive data
- Compliance requirements (HIPAA, GDPR)
- Defense-in-depth security

**Configuration**:
```yaml
modules:
  triad_enabled: true
```

**Two Wolves Pattern**:
- Privacy Wolf: Evaluates data exposure risk
- Security Wolf: Evaluates attack surface
- User sees synthesized response; full reasoning logged

---

### 6. Multi-Tenant (Namespace Isolation)

**What it does**: Isolates data and context between tenants/organizations.

**When to enable**:
- SaaS deployments
- Multiple teams sharing infrastructure
- Data isolation requirements

**Configuration**:
```yaml
modules:
  multi_tenant_enabled: true
```

---

## Recommended Configurations

### Development (Minimal)
```yaml
modules:
  council_enabled: false
  memory_enabled: false
  breadcrumbs_enabled: false
  fse_enabled: false
  triad_enabled: false
  multi_tenant_enabled: false
```

### Production (Standard)
```yaml
modules:
  council_enabled: true
  memory_enabled: true
  breadcrumbs_enabled: true
  fse_enabled: false
  triad_enabled: false
  multi_tenant_enabled: false
```

### Enterprise (Full Security)
```yaml
modules:
  council_enabled: true
  memory_enabled: true
  breadcrumbs_enabled: true
  fse_enabled: true
  triad_enabled: true
  multi_tenant_enabled: true
```

---

## Checking Module Status

```bash
# Health endpoint shows module status
curl -s http://localhost:8080/health | jq '.components'

# Full config (passwords redacted)
curl -s http://localhost:8080/v1/config/current | jq '.config.modules'
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Endpoint returns 503 "Module disabled" | Enable module in ganuda.yaml, restart gateway |
| High latency after enabling Council | Expected: Council adds ~3 inference calls |
| Memory not persisting | Check database connection in config |
| FSE key errors | Ensure fse_enabled was true at startup |

---

*For Seven Generations*
