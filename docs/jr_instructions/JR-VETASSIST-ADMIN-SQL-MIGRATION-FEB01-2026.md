# Jr Instruction: VetAssist Admin SQL Migration

**Task:** JR-VETASSIST-ADMIN-SQL-MIGRATION
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** None
**Platform:** Bluefin (192.168.132.222)
**Database:** zammad_production
**Council Vote:** #8365 — APPROVED

## Objective

Run SQL migration to create the admin governance infrastructure:
1. Add `admin_tier` column to `users` table
2. Create `admin_audit_log` table for 38 CFR 0.605 compliance
3. Create `admin_user_view` security barrier view (Tier 2 masking)
4. Enable Row-Level Security on sensitive tables
5. Set product owner's account to admin Tier 2

## Migration SQL

**Create:** `/ganuda/vetassist/backend/migrations/admin_governance_migration.sql`

```sql
-- VetAssist Admin Governance Migration
-- Council Vote #8365 — 4-Tier RBAC
-- 38 CFR 0.605 Compliance: Accounting of Disclosures
-- Date: February 1, 2026

BEGIN;

-- =============================================================================
-- 1. Add admin_tier column to users table
-- =============================================================================
-- Tier 0 = regular user (default)
-- Tier 1 = public/aggregate stats only
-- Tier 2 = admin (masked PII, user management)
-- Tier 3 = security (full PII, time-limited, logged)
-- Tier 4 = system (credential material, automated only)

ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_tier INTEGER DEFAULT 0;

COMMENT ON COLUMN users.admin_tier IS 'RBAC tier: 0=user, 1=public, 2=admin, 3=security, 4=system';

-- =============================================================================
-- 2. Create admin_audit_log table
-- =============================================================================
-- Every admin access to PII is logged per 38 CFR 0.605 principle 9

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    admin_email VARCHAR(255),
    admin_tier INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_user_id UUID,
    target_table VARCHAR(100),
    fields_accessed TEXT[],
    justification TEXT,
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    verification_result VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_admin ON admin_audit_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_target ON admin_audit_log(target_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_time ON admin_audit_log(created_at);

COMMENT ON TABLE admin_audit_log IS '38 CFR 0.605 compliance: accounting of all admin PII access';

-- =============================================================================
-- 3. Create security barrier view for Tier 2 admin
-- =============================================================================
-- Admin sees: first_name, masked last_name, user_id, status, dates
-- Admin does NOT see: email, phone, password_hash, va_icn, service details

CREATE OR REPLACE VIEW admin_user_view WITH (security_barrier=true) AS
SELECT
    id,
    first_name,
    LEFT(last_name, 1) || '***' AS last_name,
    veteran_status,
    is_active,
    email_verified,
    va_icn IS NOT NULL AS va_linked,
    va_linked_at,
    admin_tier,
    created_at,
    updated_at,
    last_login,
    disability_rating
FROM users;

COMMENT ON VIEW admin_user_view IS 'Tier 2 admin view — masked PII, no email/phone/ICN';

-- =============================================================================
-- 4. Create verification helper function
-- =============================================================================
-- Server-side email comparison for challenge-response verification
-- Admin provides what veteran told them, system compares without revealing email

CREATE OR REPLACE FUNCTION verify_user_email(
    p_user_id UUID,
    p_claimed_email VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_match BOOLEAN;
BEGIN
    SELECT LOWER(email) = LOWER(p_claimed_email)
    INTO v_match
    FROM users
    WHERE id = p_user_id AND is_active = true;

    RETURN COALESCE(v_match, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION verify_user_email IS 'Challenge-response: verify claimed email without exposing it';

-- =============================================================================
-- 5. Enable Row-Level Security (defense-in-depth)
-- =============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- Note: We do NOT use FORCE ROW LEVEL SECURITY because the application
-- connects as the table owner (claude role). FORCE would break the app.
-- RLS here protects against future non-owner roles.

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- 6. Verify migration
-- =============================================================================

-- Check admin_tier column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'admin_tier';

-- Check admin_audit_log table exists
SELECT table_name FROM information_schema.tables
WHERE table_name = 'admin_audit_log';

-- Check view exists
SELECT table_name FROM information_schema.views
WHERE table_name = 'admin_user_view';

COMMIT;
```

## Execution

Run the migration on bluefin:

```bash
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/vetassist/backend/migrations/admin_governance_migration.sql
```

## Validation

After running the migration:

```sql
-- 1. Verify admin_tier column
SELECT id, first_name, admin_tier FROM users LIMIT 3;

-- 2. Verify admin_user_view masks data
SELECT * FROM admin_user_view LIMIT 3;

-- 3. Verify admin_audit_log table structure
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'admin_audit_log' ORDER BY ordinal_position;

-- 4. Verify verification function works
SELECT verify_user_email(
    (SELECT id FROM users LIMIT 1),
    'definitely-wrong@email.com'
) AS should_be_false;

-- 5. Verify RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename IN ('users', 'chat_messages', 'user_sessions');
```

## Rollback

If needed:
```sql
ALTER TABLE users DROP COLUMN IF EXISTS admin_tier;
DROP TABLE IF EXISTS admin_audit_log;
DROP VIEW IF EXISTS admin_user_view;
DROP FUNCTION IF EXISTS verify_user_email;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;
```
