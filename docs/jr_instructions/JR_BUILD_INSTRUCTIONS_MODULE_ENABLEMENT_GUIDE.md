# Jr Build Instructions: Module Enablement Guide
## Priority: HIGH - Week 3 Deliverable

---

## Objective

Create user-facing documentation that explains how to enable each intelligence module in Ganuda Gateway. Users start with a "boring" gateway and progressively enable advanced features.

---

## Target Audience

- Users who have completed the Quickstart
- Developers wanting advanced AI capabilities
- Teams ready to move beyond basic inference

---

## Document Structure

### Location: `/ganuda/docs/MODULES.md`

```markdown
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

Edit `ganuda.yaml` and set the module flag to `true`:

```yaml
modules:
  council_enabled: true    # Enable 7-Specialist Council
  memory_enabled: true     # Enable Thermal Memory
  # ... other modules
```

Then restart the gateway:

```bash
# Docker
docker-compose restart gateway

# Systemd
sudo systemctl restart llm-gateway
```

Verify at: `http://localhost:8080/health`

---

## Module Details

### 1. Council (7-Specialist Voting)

**What it does**: Routes queries through 7 specialist perspectives before responding.

**When to enable**:
- Making architectural decisions
- Need diverse viewpoints on complex problems
- Want transparent reasoning trails

**Configuration**:
```yaml
modules:
  council_enabled: true
  council_specialists: 7  # Number of specialists (default: 7)
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

**Response includes**:
- Individual specialist votes with reasoning
- Consensus recommendation
- Concern flags (SECURITY, PERF, 7GEN, etc.)

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
  memory_thermal_decay: true  # Older memories fade (recommended)
```

**How it works**:
- Recent interactions have high "temperature" (priority)
- Older memories decay over time
- Critical items can be "pinned" to prevent decay

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

---

### 4. FSE (Fractal Stigmergic Encryption)

**What it does**: Keys evolve through usage patterns. More use = more secure.

**When to enable**:
- High-security environments
- Long-running deployments
- When key rotation isn't sufficient

**Configuration**:
```yaml
modules:
  fse_enabled: true
```

**Key Evolution Formula**: `K(t) = K₀ × e^(-λt + αU(t))`

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

**User experience**: Users see synthesized response. Full reasoning logged for audit.

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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Module endpoint returns 503 | Module not enabled in config |
| High latency after enabling Council | Expected: +3 inference calls |
| Memory not persisting | Check database connection |
| FSE key errors | Ensure proper initialization |

---

## Next Steps

- [API Reference](/docs/API.md)
- [Configuration Reference](/docs/CONFIGURATION.md)
- [Threat Model](/docs/THREAT_MODEL.md)
```

---

## Success Criteria

- [ ] Each module has clear enable/disable instructions
- [ ] Resource impact documented
- [ ] Use cases explained
- [ ] Copy-paste configuration examples
- [ ] Troubleshooting section

---

*For Seven Generations*
