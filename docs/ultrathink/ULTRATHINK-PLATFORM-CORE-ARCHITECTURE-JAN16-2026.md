# ULTRATHINK: Platform Core Architecture

## Council Vote Reference: `c4d00e4978e51b67`

---

## The Vision

VetAssist is the **first application** on a platform designed to serve many:
- SSDisabilityAssist
- HealthcareAssist
- HousingAssist
- EducationAssist
- ...and more

Each "Assist" app shares common needs. We must identify and package **CORE** infrastructure.

---

## Component Classification

### TIER 1: CORE PLATFORM (Shared by ALL apps)

| Component | Location | Current State | Package As |
|-----------|----------|---------------|------------|
| **Identity/Auth** | silverfin FreeIPA | OPERATIONAL | `ganuda-identity` |
| **PII Vault** | goldfin PostgreSQL | OPERATIONAL | `ganuda-pii-vault` |
| **LLM Inference** | redfin vLLM | OPERATIONAL | `ganuda-llm` |
| **LLM Gateway** | redfin :8080 | OPERATIONAL | `ganuda-gateway` |
| **Thermal Memory** | bluefin PostgreSQL | OPERATIONAL | `ganuda-memory` |
| **Specialist Council** | lib/specialist_council.py | OPERATIONAL | `ganuda-council` |
| **JR Task System** | jr_executor/* | OPERATIONAL | `ganuda-jrs` |
| **Inter-VLAN Router** | greenfin nftables | OPERATIONAL | `ganuda-network` |

### TIER 2: SHARED LIBRARIES (Reusable code)

| Library | Path | Purpose | Extract To |
|---------|------|---------|------------|
| PIIService | vetassist/backend/app/services/pii_service.py | Presidio + custom recognizers | `ganuda-pii-lib` |
| BaseSettings | vetassist/backend/app/core/config.py | Pydantic config pattern | `ganuda-config` |
| Database Models | vetassist/backend/app/models/* | SQLAlchemy patterns | `ganuda-db-models` |
| API Routers | vetassist/backend/app/api/* | FastAPI patterns | `ganuda-api-base` |

### TIER 3: APP-SPECIFIC (Stays with each app)

| Component | Belongs To | Reason |
|-----------|------------|--------|
| VA claim logic | VetAssist | Domain-specific |
| Rating calculator | VetAssist | VA-specific rules |
| Condition database | VetAssist | VA medical codes |
| Chat prompts | VetAssist | Veteran-focused |
| Frontend UI | VetAssist | App branding/UX |

---

## Hardware Capacity Analysis

### Current Cluster Resources

```
REDFIN (Compute):
├── GPU: 97,887 MiB total (RTX 5090)
│   └── vLLM using: ~85,000 MiB (87%)
│   └── Available: ~12,000 MiB
├── RAM: 123 GB total
│   └── Used: 9.5 GB (8%)
│   └── Available: 113 GB
└── CPU: AMD (cores TBD)

BLUEFIN (Database):
├── PostgreSQL with multiple schemas
├── thermal_memory_archive: 5,200+ entries
└── Can support many more schemas

GREENFIN (Network):
└── Router capacity: effectively unlimited for internal traffic

SILVERFIN (Identity):
└── FreeIPA: Can handle 1000s of users/services

GOLDFIN (PII Vault):
└── PostgreSQL: Can support multiple app schemas
```

### Capacity Estimate Per App

| Resource | Per App Estimate | Current Capacity | Max Apps |
|----------|------------------|------------------|----------|
| GPU VRAM | ~0 (shared vLLM) | Shared model | **10+** |
| System RAM | ~500MB backend | 113 GB free | **200+** |
| Database | 1 schema + tables | Unlimited | **50+** |
| PII Vault | 1 schema | goldfin capacity | **20+** |
| Network | Minimal | Unlimited | **100+** |

### Bottleneck Analysis

1. **GPU (vLLM)**: Single model serves all apps - NOT a per-app bottleneck
2. **LLM Gateway**: May need horizontal scaling at 10+ concurrent apps
3. **Database connections**: PostgreSQL connection pooling needed at scale
4. **PII Vault**: May need sharding at high volume

**Conclusion: Current hardware can support 10-20 Assist apps comfortably**

---

## Core Package Architecture

```
ganuda-platform/
├── ganuda-identity/          # FreeIPA integration
│   ├── client.py             # Kerberos/LDAP client
│   ├── middleware.py         # FastAPI auth middleware
│   └── service_accounts.py   # Service account management
│
├── ganuda-pii/               # PII protection
│   ├── presidio_service.py   # Base Presidio wrapper
│   ├── recognizers/          # Custom recognizers (SSN, VA, etc.)
│   ├── vault_client.py       # goldfin vault integration
│   └── tokenizer.py          # PII tokenization
│
├── ganuda-llm/               # LLM access
│   ├── gateway_client.py     # LLM Gateway client
│   ├── council_client.py     # Specialist Council client
│   └── prompts/              # Shared prompt templates
│
├── ganuda-db/                # Database patterns
│   ├── base_models.py        # SQLAlchemy base classes
│   ├── thermal_memory.py     # Thermal memory integration
│   ├── migrations/           # Alembic patterns
│   └── connection.py         # Connection pooling
│
├── ganuda-api/               # API patterns
│   ├── base_router.py        # Standard CRUD patterns
│   ├── health.py             # Health check endpoints
│   ├── middleware/           # Logging, auth, rate limiting
│   └── exceptions.py         # Standard error handling
│
└── ganuda-config/            # Configuration
    ├── base_settings.py      # Pydantic base settings
    ├── env_loader.py         # Environment management
    └── secrets.py            # silverfin vault integration
```

---

## Implementation Roadmap

### Phase 1: Identify & Mark (Week 1-2)
- [ ] Audit VetAssist codebase for reusable components
- [ ] Add `# CORE: ganuda-xxx` comments to shared code
- [ ] Create dependency map

### Phase 2: Extract & Package (Week 3-4)
- [ ] Create `ganuda-platform` monorepo
- [ ] Extract PIIService → `ganuda-pii`
- [ ] Extract config patterns → `ganuda-config`
- [ ] Extract auth middleware → `ganuda-identity`

### Phase 3: Compile & Distribute (Week 5-6)
- [ ] Create Python packages (wheel/sdist)
- [ ] Set up internal PyPI (or use git+ssh)
- [ ] Document installation for new apps

### Phase 4: Template App (Week 7-8)
- [ ] Create `ganuda-assist-template` cookiecutter
- [ ] New app bootstraps with all CORE packages
- [ ] SSDisabilityAssist as first test case

---

## Database Schema Strategy

### Shared Tables (in `ganuda_core` schema)
```sql
-- thermal_memory_archive (already exists)
-- council_votes (already exists)
-- jr_work_queue (already exists)
-- api_keys (already exists)
```

### Per-App Schemas
```sql
CREATE SCHEMA vetassist;      -- VetAssist tables
CREATE SCHEMA ssdi_assist;    -- Future: SSDI tables
CREATE SCHEMA health_assist;  -- Future: Healthcare tables
```

### PII Vault Schemas (on goldfin)
```sql
CREATE SCHEMA vetassist_pii;  -- VetAssist PII (exists)
CREATE SCHEMA ssdi_pii;       -- Future: SSDI PII
CREATE SCHEMA health_pii;     -- Future: Healthcare PII
```

---

## Decision Points for Council

1. **Monorepo vs Multi-repo?**
   - Monorepo: Easier coordination, atomic changes
   - Multi-repo: Independent versioning, cleaner boundaries

2. **Package distribution?**
   - Internal PyPI server
   - Git submodules
   - pip install from private git

3. **Database isolation?**
   - Schemas within same PostgreSQL
   - Separate databases per app
   - Separate PostgreSQL instances

---

## Seven Generations Impact

This architecture serves not just today's apps but establishes patterns for:
- **Generation 1**: VetAssist (2026)
- **Generation 2**: SSDisabilityAssist, HealthcareAssist (2026-2027)
- **Generation 3**: Expanded assist family (2027-2028)
- **Generation 4-7**: Platform evolution, new domains, federation expansion

**Core packages become tribal knowledge, compiled and passed down.**

---

## Next Actions

1. **JR Task**: Audit VetAssist for CORE candidates
2. **JR Task**: Create `ganuda-platform` repo structure
3. **JR Task**: Extract PIIService as first package
4. **Council Vote**: Monorepo vs multi-repo decision

---

*Cherokee AI Federation - For the Seven Generations*
*"Build once, serve many. The platform is the legacy."*
