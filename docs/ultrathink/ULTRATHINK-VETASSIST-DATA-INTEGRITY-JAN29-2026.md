# ULTRATHINK: VetAssist Data Integrity Architecture

**Date:** January 29, 2026
**Council Vote:** d91695f5c391dc71 (83.3% confidence, 6 concerns)
**Status:** REVIEW REQUIRED - All specialists raised concerns

---

## Problem Statement

Veterans using VetAssist experience data "disappearing" - claims, medical records, and research results become invisible due to database configuration mismatches across services.

**Impact on Veterans:**
- Marcus uploaded medical records → vanished from dashboard
- Started claim wizard (step 5) → claim not visible
- Completed 6 AI research queries → results missing (fixed)
- Trust erosion in a population already skeptical of bureaucratic systems

**Root Cause:** No single source of truth for database configuration
- `research_file_watcher.py` → hardcoded `triad_federation`
- `vetassist backend .env` → hardcoded `triad_federation`
- Other services → mixed configurations
- Silent failures return empty `[]` instead of errors

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      VetAssist Services                          │
├─────────────────────────────────────────────────────────────────┤
│  Backend API        │  File Watcher     │  Research Worker      │
│  (.env → DB_NAME)   │  (hardcoded)      │  (hardcoded)          │
│       ↓                    ↓                    ↓                │
│  triad_federation?   triad_federation?   zammad_production?     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Databases                                 │
├──────────────────────┬──────────────────────────────────────────┤
│  bluefin (222)       │  goldfin (VLAN 20 Sanctum)               │
│  zammad_production   │  vetassist_pii                           │
│  - wizard_sessions   │  - encrypted_records                     │
│  - wizard_files      │  - pii_tokens                            │
│  - research_results  │  - audit_log                             │
│  - claims            │                                          │
│  - scratchpads       │                                          │
└──────────────────────┴──────────────────────────────────────────┘
```

---

## Council Concerns & Responses

### 1. Raven [STRATEGY CONCERN]
**Concern:** Long-term strategic implications of centralized config

**Response:**
- Centralized config is standard practice (12-factor app methodology)
- Single point of change when database migrations occur
- Enables future multi-tenant architecture without code changes
- Strategy: Config lives in version control, secrets in vault

### 2. Gecko [PERF CONCERN]
**Concern:** Performance impact of config lookup

**Response:**
- YAML config loaded once at startup, cached in memory
- No per-request config reads
- Validation runs once at startup (< 100ms)
- Net performance: NEUTRAL (eliminates failed queries to wrong DB)

### 3. Eagle Eye [VISIBILITY CONCERN]
**Concern:** Monitoring and observability of config state

**Response:**
- Add `/health/db` endpoint showing which database is connected
- Log database name on every service startup
- Prometheus metric: `vetassist_db_connection{database="zammad_production"}`
- Alert if any service connects to unexpected database

### 4. Crawdad [SECURITY CONCERN]
**Concern:** Security of centralized config containing credentials

**Response:**
- Config file contains ONLY non-sensitive values (host, port, database name)
- Credentials retrieved from:
  1. Silverfin FreeIPA vault (preferred)
  2. Environment variables (fallback)
- File permissions: 0644 (readable, not writable by services)
- Secrets NEVER in config file

### 5. Spider [INTEGRATION CONCERN]
**Concern:** Integration with existing systems

**Response:**
- Backwards compatible: Services can still use env vars
- Config file is optional override, not mandatory
- Migration path: Update services one at a time
- No breaking changes to existing deployments

### 6. Turtle [7GEN CONCERN]
**Concern:** Long-term sustainability for seven generations

**Response:**
- YAML is human-readable, will exist in 175 years
- Self-documenting with comments
- Version controlled with full history
- Data integrity monitoring prevents silent data loss
- Veterans' records preserved across infrastructure changes

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              /ganuda/vetassist/config/database.yaml              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  non_pii:                                                │    │
│  │    host: 192.168.132.222  # bluefin                     │    │
│  │    database: zammad_production                          │    │
│  │    port: 5432                                           │    │
│  │                                                         │    │
│  │  pii:                                                   │    │
│  │    host: 192.168.20.10    # goldfin (VLAN 20)          │    │
│  │    database: vetassist_pii                              │    │
│  │    port: 5432                                           │    │
│  │                                                         │    │
│  │  # Credentials from vault or env vars - NEVER here     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              /ganuda/lib/vetassist_db_config.py                  │
│  - Loads database.yaml                                          │
│  - Retrieves credentials from vault/env                         │
│  - Validates tables exist on startup                            │
│  - Exports: get_non_pii_connection(), get_pii_connection()      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      VetAssist Services                          │
│  All services import from vetassist_db_config                   │
│  Startup validation FAILS if tables missing                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Integrity Monitoring

### Startup Validation
```python
REQUIRED_TABLES = {
    'non_pii': [
        'vetassist_wizard_sessions',
        'vetassist_wizard_files',
        'vetassist_research_results',
        'vetassist_claims',
        'vetassist_scratchpads'
    ],
    'pii': [
        'vetassist_encrypted_records',
        'vetassist_pii_tokens'
    ]
}

def validate_on_startup():
    """FAIL LOUDLY if expected tables are missing."""
    for table in REQUIRED_TABLES['non_pii']:
        if not table_exists(table):
            raise StartupError(f"FATAL: Table {table} not found in {database}")
```

### User Data Integrity Daemon
```python
def check_user_data_integrity():
    """Alert if user's visible data count drops unexpectedly."""
    for user in get_active_users():
        current = get_data_counts(user.id)
        previous = get_yesterday_counts(user.id)

        if current.files < previous.files:
            alert(f"User {user.id} files dropped: {previous.files} → {current.files}")
        if current.claims < previous.claims:
            alert(f"User {user.id} claims dropped: {previous.claims} → {current.claims}")
```

---

## Implementation Plan

### Phase 1: Config Consolidation (P0)
1. Create `/ganuda/vetassist/config/database.yaml`
2. Create `/ganuda/lib/vetassist_db_config.py`
3. Update `vetassist-backend` to use new config
4. Update `research-file-watcher` to use new config
5. Update `research-worker` VetAssist sync to use new config

### Phase 2: Startup Validation (P0)
1. Add table existence checks to config module
2. Services fail to start if tables missing
3. Clear error messages in logs and systemd status

### Phase 3: Integrity Monitoring (P1)
1. Create `vetassist_data_integrity_daemon.py`
2. Track per-user data counts daily
3. Alert to Telegram on unexpected drops
4. Dashboard shows data health status

### Phase 4: Health Endpoints (P1)
1. Add `/health/db` to backend showing connection status
2. Add Prometheus metrics for database state
3. Grafana dashboard for VetAssist data integrity

---

## Files to Create/Modify

| File | Action | Priority |
|------|--------|----------|
| `/ganuda/vetassist/config/database.yaml` | CREATE | P0 |
| `/ganuda/lib/vetassist_db_config.py` | CREATE | P0 |
| `/ganuda/vetassist/backend/app/core/database_config.py` | MODIFY - use new config | P0 |
| `/ganuda/services/research_file_watcher.py` | MODIFY - use new config | P0 |
| `/ganuda/services/research_worker.py` | MODIFY - use new config | P0 |
| `/ganuda/services/vetassist_integrity_daemon.py` | CREATE | P1 |

---

## Success Criteria

1. **No more "wrong database" bugs** - single config means single point of truth
2. **Startup fails visibly** - misconfiguration caught immediately, not silently
3. **Data drops trigger alerts** - TPM notified before user reports missing data
4. **Veteran trust maintained** - data appears consistently, every time

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Config file deleted | Low | High | Version control + backup |
| Migration breaks existing | Medium | Medium | Gradual rollout, backwards compatible |
| Vault unavailable | Low | Medium | Env var fallback |

---

## Conclusion

The Council's concerns are valid and addressed. The centralized config approach:
- Eliminates the class of bugs we've been fixing all day
- Fails loudly rather than silently
- Monitors for data integrity issues
- Maintains security (no credentials in config)
- Scales for seven generations

**Recommendation:** APPROVE with Phase 1 + Phase 2 as P0

---

FOR SEVEN GENERATIONS
