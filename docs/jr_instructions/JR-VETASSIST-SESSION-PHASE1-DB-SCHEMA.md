# Jr Instruction: VetAssist VA Session Management - Phase 1: Database Schema

## Priority: HIGH
## Estimated Effort: Medium
## Dependencies: None

---

## Objective

Create the database schema for VetAssist VA session management. This includes tables for users, encrypted VA tokens, sessions, and audit logging.

---

## Context

VetAssist successfully authenticates veterans through VA.gov OAuth but lacks session persistence. We need database tables to store:
1. User accounts linked to VA identity (ICN)
2. Encrypted VA tokens (access_token, refresh_token)
3. VetAssist sessions for JWT tracking
4. Audit logs for security compliance

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/backend/app/db/migrations/003_va_session_tables.sql`

```sql
-- VetAssist VA Session Management Schema
-- Cherokee AI Federation - For Seven Generations
-- Phase 1: Database Tables

-- VA-linked user accounts
CREATE TABLE IF NOT EXISTS vetassist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- VA Identity (from token claims)
    va_icn VARCHAR(50) UNIQUE,           -- VA Integration Control Number
    va_veteran_status VARCHAR(20),        -- confirmed, not_confirmed, etc.

    -- Profile (from VA or user-entered)
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Account status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- VA OAuth tokens (encrypted at rest)
CREATE TABLE IF NOT EXISTS vetassist_va_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES vetassist_users(id) ON DELETE CASCADE,

    -- Encrypted tokens (AES-256-GCM)
    access_token_encrypted BYTEA NOT NULL,
    refresh_token_encrypted BYTEA,

    -- Token metadata (not sensitive)
    token_type VARCHAR(20) DEFAULT 'Bearer',
    scope VARCHAR(500),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    refreshed_at TIMESTAMPTZ,

    UNIQUE(user_id)  -- One active token set per user
);

-- VetAssist sessions (for JWT tracking and revocation)
CREATE TABLE IF NOT EXISTS vetassist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES vetassist_users(id) ON DELETE CASCADE,

    -- Session data
    jwt_id VARCHAR(64) UNIQUE NOT NULL,  -- jti claim for revocation
    device_info JSONB,                    -- User agent, IP (hashed)

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_vetassist_sessions_user ON vetassist_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_vetassist_sessions_jwt ON vetassist_sessions(jwt_id);
CREATE INDEX IF NOT EXISTS idx_vetassist_sessions_expires ON vetassist_sessions(expires_at) WHERE revoked_at IS NULL;

-- Audit log for security compliance
CREATE TABLE IF NOT EXISTS vetassist_auth_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES vetassist_users(id),
    event_type VARCHAR(50) NOT NULL,     -- login, logout, token_refresh, failed_login, etc.
    event_data JSONB,                     -- Non-sensitive metadata
    ip_hash VARCHAR(64),                  -- SHA-256 of IP for privacy
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_vetassist_audit_user ON vetassist_auth_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_vetassist_audit_type ON vetassist_auth_audit(event_type);
CREATE INDEX IF NOT EXISTS idx_vetassist_audit_created ON vetassist_auth_audit(created_at);

-- Comments for documentation
COMMENT ON TABLE vetassist_users IS 'VetAssist user accounts linked to VA identity';
COMMENT ON TABLE vetassist_va_tokens IS 'Encrypted VA OAuth tokens - access and refresh';
COMMENT ON TABLE vetassist_sessions IS 'Active VetAssist sessions for JWT management';
COMMENT ON TABLE vetassist_auth_audit IS 'Security audit log for authentication events';
COMMENT ON COLUMN vetassist_va_tokens.access_token_encrypted IS 'AES-256-GCM encrypted, nonce prepended';
COMMENT ON COLUMN vetassist_sessions.jwt_id IS 'Maps to JWT jti claim for revocation';
```

---

## Verification

1. Connect to database and run migration:
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d triad_federation -f /ganuda/vetassist/backend/app/db/migrations/003_va_session_tables.sql
```

2. Verify tables exist:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'vetassist_%'
ORDER BY table_name;
```

3. Verify indexes:
```sql
SELECT indexname FROM pg_indexes
WHERE tablename LIKE 'vetassist_%';
```

---

## Success Criteria

- [ ] All 4 tables created successfully
- [ ] All indexes created
- [ ] Foreign key constraints working
- [ ] No errors on migration run

---

*Cherokee AI Federation - For Seven Generations*
