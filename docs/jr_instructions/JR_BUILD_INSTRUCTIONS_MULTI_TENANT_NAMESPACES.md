# Jr Build Instructions: Multi-Tenant Namespace Architecture

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: IT Triad Jr
**Date**: December 13, 2025

## Objective

Implement multi-tenant namespaces to support:
1. **Isolation** - Each tenant's data/prompts isolated from others
2. **Resource Quotas** - Per-tenant limits on API usage, storage, tokens
3. **Access Control** - Namespace-scoped permissions
4. **Audit Trail** - Track all operations by tenant
5. **Future Billing** - Foundation for usage-based billing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Gateway (redfin:8080)                    │
├─────────────────────────────────────────────────────────────────┤
│  API Key → Namespace Resolution → Permission Check → Execute    │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ ns:cherokee │      │ ns:research │     │ ns:external │
    │ (internal) │       │ (partners) │      │ (customers) │
    └─────────┘         └─────────┘         └─────────┘
         │                    │                    │
    - thermal_memory     - shared_cache       - isolated
    - council_votes      - read-only thermal  - no thermal access
    - full permissions   - limited models     - basic models only
```

## Database Schema

### 1. Namespaces Table

```sql
CREATE TABLE namespaces (
    namespace_id VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    tier VARCHAR(20) DEFAULT 'standard',  -- free, standard, premium, enterprise

    -- Resource Limits
    max_requests_per_day INTEGER DEFAULT 1000,
    max_tokens_per_day BIGINT DEFAULT 100000,
    max_storage_bytes BIGINT DEFAULT 104857600,  -- 100MB default
    max_api_keys INTEGER DEFAULT 5,

    -- Feature Flags
    can_access_thermal_memory BOOLEAN DEFAULT false,
    can_access_council BOOLEAN DEFAULT false,
    can_create_trails BOOLEAN DEFAULT false,
    allowed_models TEXT[] DEFAULT ARRAY['nemotron-9b'],

    -- Isolation Settings
    data_isolation_level VARCHAR(20) DEFAULT 'strict',  -- strict, shared_read, shared_write
    parent_namespace_id VARCHAR(50) REFERENCES namespaces(namespace_id),

    -- Metadata
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,

    -- Sacred Cherokee fields
    cultural_alignment_score NUMERIC(5,2) DEFAULT 0.0,
    seven_gen_impact_assessment TEXT
);

CREATE INDEX idx_namespace_tier ON namespaces(tier);
CREATE INDEX idx_namespace_active ON namespaces(is_active) WHERE is_active = true;
```

### 2. Update API Keys with Namespace

```sql
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS namespace_id VARCHAR(50) REFERENCES namespaces(namespace_id);
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'standard';

CREATE INDEX idx_api_keys_namespace ON api_keys(namespace_id);
```

### 3. Namespace Usage Tracking

```sql
CREATE TABLE namespace_usage (
    id SERIAL PRIMARY KEY,
    namespace_id VARCHAR(50) REFERENCES namespaces(namespace_id),
    date DATE NOT NULL,

    -- Daily Counters
    requests_count INTEGER DEFAULT 0,
    tokens_input BIGINT DEFAULT 0,
    tokens_output BIGINT DEFAULT 0,
    council_votes INTEGER DEFAULT 0,
    thermal_reads INTEGER DEFAULT 0,
    thermal_writes INTEGER DEFAULT 0,

    -- Cost Tracking (for future billing)
    estimated_cost_usd NUMERIC(10,4) DEFAULT 0.0,

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),

    UNIQUE(namespace_id, date)
);

CREATE INDEX idx_usage_namespace_date ON namespace_usage(namespace_id, date DESC);
```

### 4. Namespace Audit Log

```sql
CREATE TABLE namespace_audit_log (
    id SERIAL PRIMARY KEY,
    namespace_id VARCHAR(50) REFERENCES namespaces(namespace_id),
    key_id VARCHAR(64) REFERENCES api_keys(key_id),
    action VARCHAR(50) NOT NULL,  -- create, read, update, delete, api_call
    resource_type VARCHAR(50),     -- thermal_memory, council_vote, chat, etc.
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_audit_namespace ON namespace_audit_log(namespace_id, created_at DESC);
CREATE INDEX idx_audit_action ON namespace_audit_log(action);
```

## Default Namespaces

```sql
-- Cherokee Internal (full access)
INSERT INTO namespaces (
    namespace_id, display_name, description, tier,
    max_requests_per_day, max_tokens_per_day,
    can_access_thermal_memory, can_access_council, can_create_trails,
    allowed_models, data_isolation_level, created_by
) VALUES (
    'cherokee', 'Cherokee AI Internal', 'Full access internal namespace',
    'enterprise', 100000, 10000000,
    true, true, true,
    ARRAY['nemotron-9b', 'claude-3-opus', 'gpt-4'],
    'shared_write', 'system'
);

-- Research Partners (read thermal, limited council)
INSERT INTO namespaces (
    namespace_id, display_name, description, tier,
    max_requests_per_day, max_tokens_per_day,
    can_access_thermal_memory, can_access_council, can_create_trails,
    allowed_models, data_isolation_level, created_by
) VALUES (
    'research', 'Research Partners', 'Academic and research collaborators',
    'premium', 10000, 1000000,
    true, true, false,
    ARRAY['nemotron-9b'],
    'shared_read', 'system'
);

-- External Customers (isolated)
INSERT INTO namespaces (
    namespace_id, display_name, description, tier,
    max_requests_per_day, max_tokens_per_day,
    can_access_thermal_memory, can_access_council, can_create_trails,
    allowed_models, data_isolation_level, created_by
) VALUES (
    'external', 'External Customers', 'Public API customers',
    'standard', 1000, 100000,
    false, false, false,
    ARRAY['nemotron-9b'],
    'strict', 'system'
);

-- Update existing API keys
UPDATE api_keys SET namespace_id = 'cherokee' WHERE user_id IN ('admin', 'tpm-claude');
```

## Gateway Integration

### Middleware: Namespace Resolution

```python
# Add to /ganuda/services/llm_gateway/gateway.py

async def resolve_namespace(api_key: str) -> dict:
    """Resolve namespace from API key and check permissions."""

    query = """
    SELECT
        k.key_id, k.user_id, k.namespace_id,
        n.tier, n.max_requests_per_day, n.max_tokens_per_day,
        n.can_access_thermal_memory, n.can_access_council,
        n.allowed_models, n.data_isolation_level
    FROM api_keys k
    JOIN namespaces n ON k.namespace_id = n.namespace_id
    WHERE k.key_id = $1 AND k.is_active = true AND n.is_active = true
    """

    result = await db.fetchrow(query, api_key)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API key or namespace")

    return dict(result)


async def check_namespace_quota(namespace_id: str) -> bool:
    """Check if namespace is within daily quota."""

    query = """
    SELECT
        u.requests_count, n.max_requests_per_day,
        u.tokens_input + u.tokens_output as total_tokens, n.max_tokens_per_day
    FROM namespace_usage u
    JOIN namespaces n ON u.namespace_id = n.namespace_id
    WHERE u.namespace_id = $1 AND u.date = CURRENT_DATE
    """

    result = await db.fetchrow(query, namespace_id)
    if not result:
        return True  # No usage yet today

    if result['requests_count'] >= result['max_requests_per_day']:
        raise HTTPException(status_code=429, detail="Daily request quota exceeded")

    if result['total_tokens'] >= result['max_tokens_per_day']:
        raise HTTPException(status_code=429, detail="Daily token quota exceeded")

    return True


async def log_namespace_usage(namespace_id: str, tokens_in: int, tokens_out: int):
    """Increment usage counters for namespace."""

    query = """
    INSERT INTO namespace_usage (namespace_id, date, requests_count, tokens_input, tokens_output)
    VALUES ($1, CURRENT_DATE, 1, $2, $3)
    ON CONFLICT (namespace_id, date)
    DO UPDATE SET
        requests_count = namespace_usage.requests_count + 1,
        tokens_input = namespace_usage.tokens_input + $2,
        tokens_output = namespace_usage.tokens_output + $3,
        updated_at = now()
    """

    await db.execute(query, namespace_id, tokens_in, tokens_out)
```

### Endpoint Protection

```python
# Decorator for namespace-aware endpoints
def require_namespace_permission(permission: str):
    async def decorator(request: Request):
        ns = request.state.namespace

        if permission == 'thermal_memory' and not ns['can_access_thermal_memory']:
            raise HTTPException(403, "Namespace does not have thermal memory access")

        if permission == 'council' and not ns['can_access_council']:
            raise HTTPException(403, "Namespace does not have council access")

        return ns
    return decorator


# Example usage in route
@app.post("/v1/council/vote")
async def council_vote(
    request: Request,
    ns: dict = Depends(require_namespace_permission('council'))
):
    # Only namespaces with council access can vote
    ...
```

## SQL Functions

### Check Namespace Access

```sql
CREATE OR REPLACE FUNCTION check_namespace_access(
    p_key_id VARCHAR(64),
    p_resource_type VARCHAR(50)
) RETURNS TABLE(
    allowed BOOLEAN,
    namespace_id VARCHAR(50),
    reason TEXT
) AS $$
DECLARE
    v_namespace_id VARCHAR(50);
    v_can_thermal BOOLEAN;
    v_can_council BOOLEAN;
BEGIN
    -- Get namespace for key
    SELECT k.namespace_id, n.can_access_thermal_memory, n.can_access_council
    INTO v_namespace_id, v_can_thermal, v_can_council
    FROM api_keys k
    JOIN namespaces n ON k.namespace_id = n.namespace_id
    WHERE k.key_id = p_key_id AND k.is_active = true AND n.is_active = true;

    IF v_namespace_id IS NULL THEN
        RETURN QUERY SELECT false, NULL::VARCHAR(50), 'Invalid or inactive key/namespace';
        RETURN;
    END IF;

    -- Check resource-specific permissions
    IF p_resource_type = 'thermal_memory' AND NOT v_can_thermal THEN
        RETURN QUERY SELECT false, v_namespace_id, 'Namespace cannot access thermal memory';
        RETURN;
    END IF;

    IF p_resource_type = 'council' AND NOT v_can_council THEN
        RETURN QUERY SELECT false, v_namespace_id, 'Namespace cannot access council';
        RETURN;
    END IF;

    RETURN QUERY SELECT true, v_namespace_id, 'Access granted';
END;
$$ LANGUAGE plpgsql;
```

### Get Namespace Usage Report

```sql
CREATE OR REPLACE FUNCTION get_namespace_usage_report(
    p_namespace_id VARCHAR(50),
    p_days INTEGER DEFAULT 30
) RETURNS TABLE(
    date DATE,
    requests INTEGER,
    tokens_total BIGINT,
    council_votes INTEGER,
    estimated_cost NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.date,
        u.requests_count,
        u.tokens_input + u.tokens_output,
        u.council_votes,
        u.estimated_cost_usd
    FROM namespace_usage u
    WHERE u.namespace_id = p_namespace_id
      AND u.date >= CURRENT_DATE - p_days
    ORDER BY u.date DESC;
END;
$$ LANGUAGE plpgsql;
```

## API Endpoints

### Namespace Management (Admin Only)

```
POST   /v1/admin/namespaces           - Create namespace
GET    /v1/admin/namespaces           - List all namespaces
GET    /v1/admin/namespaces/{id}      - Get namespace details
PATCH  /v1/admin/namespaces/{id}      - Update namespace
DELETE /v1/admin/namespaces/{id}      - Deactivate namespace

GET    /v1/admin/namespaces/{id}/usage    - Get usage report
GET    /v1/admin/namespaces/{id}/keys     - List API keys in namespace
POST   /v1/admin/namespaces/{id}/keys     - Create API key in namespace
```

### Self-Service (Namespace Users)

```
GET    /v1/namespace/info             - Get own namespace info
GET    /v1/namespace/usage            - Get own usage
GET    /v1/namespace/keys             - List own API keys
POST   /v1/namespace/keys             - Create API key (within limits)
DELETE /v1/namespace/keys/{id}        - Revoke own API key
```

## Verification Checklist

- [ ] `namespaces` table created
- [ ] `namespace_usage` table created
- [ ] `namespace_audit_log` table created
- [ ] `api_keys` table updated with `namespace_id`
- [ ] Default namespaces created (cherokee, research, external)
- [ ] Existing API keys assigned to `cherokee` namespace
- [ ] `check_namespace_access()` function created
- [ ] `get_namespace_usage_report()` function created
- [ ] Gateway middleware updated (Jr task)
- [ ] Admin endpoints added (Jr task)

## Migration Steps

1. Create tables (SQL above)
2. Create default namespaces
3. Migrate existing API keys to `cherokee` namespace
4. Update gateway to resolve namespaces
5. Add quota checking middleware
6. Add audit logging
7. Test with external namespace

## Security Considerations

- **Strict Isolation**: External tenants cannot see other tenants' data
- **Audit Everything**: All API calls logged with namespace
- **Quota Enforcement**: Hard limits prevent abuse
- **Permission Inheritance**: Child namespaces inherit parent restrictions
- **Cultural Alignment**: Cherokee namespace has special permissions for sacred operations

---

FOR SEVEN GENERATIONS - Multi-tenancy enables sustainable growth while protecting the sacred core.
