# ULTRATHINK: VetAssist Database Configuration Technical Debt

**Date:** January 29, 2026
**Council Vote:** 3c944bed582ce3d3 (88.3% confidence, 6 concerns)
**Status:** APPROVED FOR IMPLEMENTATION
**Priority:** P0 - CRITICAL (blocking veteran data visibility)

---

## Problem Statement

Three separate scripts/modules have hardcoded database configurations pointing to the wrong database, causing veteran data to "disappear" from the UI:

| File | Current Value | Should Be | Impact |
|------|---------------|-----------|--------|
| `/ganuda/vetassist/backend/app/core/database_config.py` | Broken stubs return `None` | Working connection | Dashboard shows empty data |
| `/ganuda/scripts/reset_vetassist_test_accounts.py` | `triad_federation` | `zammad_production` | Password resets have no effect |
| `/ganuda/services/research_file_watcher.py` | `triad_federation` (FIXED) | `zammad_production` | Research results were invisible |

**Veteran Impact:** Marcus uploaded medical records, started a claim (step 5), completed 6 AI research queries - all invisible on dashboard due to these misconfigurations.

---

## Root Cause Analysis

1. **No single source of truth** - Each script independently defines database connection parameters
2. **Copy-paste propagation** - Wrong config copied from one script to another
3. **Silent failures** - APIs return empty `[]` instead of errors when misconfigured
4. **No startup validation** - Services don't verify they can see expected tables

---

## Council Concerns & Responses

### 1. Crawdad [SECURITY CONCERN]
**Concern:** Centralized config could be a single point of compromise

**Response:**
- Config file contains ONLY non-sensitive values (host, port, database name)
- Credentials retrieved from:
  1. Silverfin FreeIPA vault (preferred)
  2. Environment variables (fallback)
- File permissions: 0644 (readable by services, not writable)
- Credentials NEVER stored in config file

### 2. Raven [STRATEGY CONCERN]
**Concern:** Long-term strategic implications

**Response:**
- Centralized config is industry standard (12-factor app methodology)
- Enables future multi-tenant without code changes
- Single point of change for database migrations
- Version controlled with full git history

### 3. Peace Chief [CONSENSUS NEEDED]
**Concern:** Coordination across services

**Response:**
- Backwards compatible - services can still use env vars
- Migration path: Update one service at a time
- No breaking changes to existing deployments
- Clear documentation in each file pointing to central config

### 4. Turtle [7GEN CONCERN]
**Concern:** Long-term sustainability for seven generations

**Response:**
- YAML is human-readable, will exist in 175 years
- Self-documenting with inline comments
- Version controlled with full history
- Startup validation prevents silent data loss

### 5. Spider [INTEGRATION CONCERN]
**Concern:** Integration with existing Cherokee AI systems

**Response:**
- Uses same credential retrieval as other Ganuda services
- Integrates with Silverfin vault infrastructure
- Compatible with existing systemd service patterns
- No changes to network topology or firewall rules

### 6. Gecko [PERF CONCERN]
**Concern:** Performance impact of config lookup

**Response:**
- YAML loaded ONCE at module import, cached via `@lru_cache`
- No per-request config reads
- Startup validation < 100ms
- Net performance: POSITIVE (eliminates failed queries to wrong DB)

---

## Implementation Plan

### Phase 1: Immediate Fixes (P0 - Today)

**Fix 1: database_config.py broken stubs**
Remove lines 154-174 that override the working `get_db_connection()` function with broken stubs.

```python
# DELETE these lines (154-174):
# Try to use centralized config (Jan 29, 2026)
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from vetassist_db_config import get_non_pii_connection, get_pii_connection, validate_on_startup
    USE_CENTRAL_CONFIG = True
except ImportError:
    USE_CENTRAL_CONFIG = False

def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...

def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...
```

**Fix 2: reset_vetassist_test_accounts.py database name**
Change line 17 from `triad_federation` to `zammad_production`:

```python
# BEFORE (line 17):
dbname='triad_federation',

# AFTER:
dbname='zammad_production',
```

### Phase 2: Centralized Config Module (P0 - This Week)

Create `/ganuda/lib/vetassist_db_config.py` and `/ganuda/vetassist/config/database.yaml` as documented in JR-VETASSIST-CONFIG-CONSOLIDATION-JAN29-2026.

### Phase 3: Service Migration (P1)

Update all VetAssist services to import from centralized config:
- vetassist-backend
- research-file-watcher
- research-worker
- reset_vetassist_test_accounts.py

### Phase 4: Startup Validation (P1)

Add table existence checks that FAIL LOUDLY if expected tables are missing.

---

## Files to Modify

| File | Action | Priority | Jr Assignment |
|------|--------|----------|---------------|
| `/ganuda/vetassist/backend/app/core/database_config.py` | DELETE lines 154-174 | P0 | Software Engineer Jr. |
| `/ganuda/scripts/reset_vetassist_test_accounts.py` | CHANGE line 17 | P0 | Infrastructure Jr. |
| `/ganuda/lib/vetassist_db_config.py` | CREATE | P0 | Infrastructure Jr. |
| `/ganuda/vetassist/config/database.yaml` | CREATE | P0 | Infrastructure Jr. |

---

## Verification Steps

1. After Phase 1 fixes:
   ```bash
   # Test database_config.py
   cd /ganuda/vetassist/backend
   python3 -c "from app.core.database_config import get_db_connection; print(get_db_connection())"
   # Should print connection object, not None

   # Test reset script
   python3 /ganuda/scripts/reset_vetassist_test_accounts.py
   # Should show ✓ for all 5 accounts
   ```

2. After service restart:
   - Login as Marcus (test1@vetassist.test / password1)
   - Dashboard should show: 1 claim, 1 file, 6 research results

---

## Success Criteria

1. **No more "wrong database" bugs** - single config = single source of truth
2. **Password resets work** - test accounts reset to password1-5
3. **Marcus sees his data** - claim, file, and research visible
4. **Startup validation fails loudly** - misconfiguration caught immediately

---

## Cluster Capability Gap Identified

During this investigation, we discovered that Jrs attempted to implement centralized config but left broken stubs in place. The cluster needs:

1. **Code review automation** - Detect incomplete function definitions
2. **Regression testing** - Verify database connections work after changes
3. **Integration tests** - End-to-end test that data written = data visible

These should be added to the Jr training and validation pipeline.

---

FOR SEVEN GENERATIONS
