# JR Instruction: VetAssist CORE Component Audit

## Metadata
```yaml
task_id: vetassist_core_audit
priority: 2
assigned_to: Architecture Jr.
date: 2026-01-16
```

## Audit Results

### TIER 1: EXTRACT TO CORE (High priority)

| File | Lines | Extract As | Rationale |
|------|-------|------------|-----------|
| `pii_service.py` | 40→ | `ganuda-pii` | **DONE** - Already extracted |
| `security.py` | 149 | `ganuda-auth` | JWT, password hashing - universal |
| `database.py` | 45 | `ganuda-db` | SQLAlchemy patterns - universal |
| `config.py` | 76 | `ganuda-config` | Pydantic settings - universal |
| `sanitize.py` | 85 | `ganuda-security` | Input sanitization - universal |
| `health.py` | 95 | `ganuda-api` | Health endpoints - universal |

### TIER 2: PARTIAL EXTRACTION (Council integration)

| File | Lines | Extract | Keep in App |
|------|-------|---------|-------------|
| `council_chat.py` | 241 | Council client, consensus | VA prompts, context |

**Pattern:** Extract generic Council client to `ganuda-council`, keep domain prompts in app.

### TIER 3: APP-SPECIFIC (Stay in VetAssist)

| File | Lines | Reason |
|------|-------|--------|
| `va_calculator.py` | 488 | VA rating math - domain-specific |
| `calculator.py` | 254 | VA calculator endpoint |
| `content.py` | 217 | VetAssist CMS content |
| `chat.py` | 391 | Chat flow (patterns reusable, implementation specific) |
| `auth_service.py` | 286 | FreeIPA integration (generic pattern, specific config) |

---

## Proposed Core Packages

```
/ganuda/lib/
├── ganuda_pii/           # DONE - PII detection/protection
│   ├── service.py
│   ├── tokenizer.py
│   └── recognizers/
│
├── ganuda_auth/          # NEXT - Authentication utilities
│   ├── __init__.py
│   ├── jwt.py            # JWT create/verify
│   ├── password.py       # Hash/verify passwords
│   └── middleware.py     # FastAPI auth middleware
│
├── ganuda_db/            # Database patterns
│   ├── __init__.py
│   ├── connection.py     # Engine, session management
│   ├── base.py           # Declarative base
│   └── deps.py           # FastAPI dependencies (get_db)
│
├── ganuda_config/        # Configuration patterns
│   ├── __init__.py
│   ├── base_settings.py  # Pydantic base
│   └── env.py            # Environment helpers
│
├── ganuda_council/       # Council integration
│   ├── __init__.py
│   ├── client.py         # Council API client
│   └── consensus.py      # Consensus helpers
│
└── ganuda_api/           # API patterns
    ├── __init__.py
    ├── health.py         # Health check router
    ├── middleware/       # Logging, rate limiting
    └── exceptions.py     # Standard error handling
```

---

## Extraction Priority

1. **ganuda-auth** (security.py) - Critical for all apps
2. **ganuda-db** (database.py) - Foundation for data access
3. **ganuda-config** (config.py) - Settings pattern
4. **ganuda-council** (council_chat.py partial) - LLM integration
5. **ganuda-api** (health.py, middleware) - API patterns

---

## Size Reduction Estimate

| Package | Lines Extracted | Apps Benefiting |
|---------|-----------------|-----------------|
| ganuda-pii | ~170 | All with PII |
| ganuda-auth | ~150 | All with auth |
| ganuda-db | ~50 | All with DB |
| ganuda-config | ~80 | All |
| ganuda-council | ~100 | All with LLM |
| ganuda-api | ~100 | All APIs |

**Total extractable:** ~650 lines of reusable code

**Per-app savings:** New apps start with 650+ lines less to write

---

## Next Steps

1. Extract `ganuda-auth` (security.py)
2. Extract `ganuda-db` (database.py)
3. Create `ganuda-config` base
4. Update VetAssist to use extracted packages
5. Document usage patterns

---

*Cherokee AI Federation - For the Seven Generations*
*"Extract once, use forever."*
