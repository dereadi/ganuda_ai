# JR-VETASSIST-VA-LINK-MIGRATION-JAN30-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Database / DevOps
- **Target Node:** bluefin (192.168.132.222)
- **Database:** zammad_production
- **Depends On:** None (Phase 1 — no code dependencies)
- **Blocks:** JR-VETASSIST-VA-LINK-ENDPOINT-JAN30-2026

## Context

VetAssist has two disconnected identity systems:

| System | Table | Key Field | JWT Secret |
|--------|-------|-----------|------------|
| Email/Password | `users` (SQLAlchemy) | `users.id` (UUID) | `SECRET_KEY` |
| VA OAuth | `vetassist_users` (psycopg2) | `vetassist_users.va_icn` | `VETASSIST_JWT_SECRET` |

A user who registers with email and later logs in via VA.gov gets two unlinked accounts. We need to add columns to the `users` table so a local account can reference a VA ICN.

## Migration SQL

Run the following on `zammad_production` on bluefin:

```sql
-- VetAssist Account Linking: Add VA ICN reference to users table
-- Phase 1 of VA Account Linking feature
-- Date: 2026-01-30
-- Safe: Additive only, nullable columns, no data modification

BEGIN;

-- Add VA Integration Control Number column
-- UNIQUE constraint prevents one ICN from linking to multiple local accounts
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_icn VARCHAR(50) UNIQUE;

-- Track when the VA account was linked (for audit and display)
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_linked_at TIMESTAMPTZ;

-- Add index for ICN lookups during linked-login flow
-- (The UNIQUE constraint creates an implicit index, but being explicit)
CREATE INDEX IF NOT EXISTS idx_users_va_icn ON users(va_icn) WHERE va_icn IS NOT NULL;

COMMIT;
```

## Implementation Steps

1. SSH into bluefin:
   ```bash
   ssh bluefin
   ```

2. Run the migration:
   ```bash
   psql -U zammad -d zammad_production -f /ganuda/sql/vetassist_va_link_migration.sql
   ```

   Or inline:
   ```bash
   psql -U zammad -d zammad_production <<'EOF'
   BEGIN;
   ALTER TABLE users ADD COLUMN IF NOT EXISTS va_icn VARCHAR(50) UNIQUE;
   ALTER TABLE users ADD COLUMN IF NOT EXISTS va_linked_at TIMESTAMPTZ;
   CREATE INDEX IF NOT EXISTS idx_users_va_icn ON users(va_icn) WHERE va_icn IS NOT NULL;
   COMMIT;
   EOF
   ```

3. Save the migration file for version control:
   ```bash
   cat > /ganuda/sql/vetassist_va_link_migration.sql <<'EOF'
   -- VetAssist Account Linking: Add VA ICN reference to users table
   -- Phase 1 of VA Account Linking feature
   -- Date: 2026-01-30

   BEGIN;
   ALTER TABLE users ADD COLUMN IF NOT EXISTS va_icn VARCHAR(50) UNIQUE;
   ALTER TABLE users ADD COLUMN IF NOT EXISTS va_linked_at TIMESTAMPTZ;
   CREATE INDEX IF NOT EXISTS idx_users_va_icn ON users(va_icn) WHERE va_icn IS NOT NULL;
   COMMIT;
   EOF
   ```

## Verification

```bash
# Confirm columns exist
psql -U zammad -d zammad_production -c "\d users" | grep -E "va_icn|va_linked_at"

# Expected output:
# va_icn          | character varying(50) |           |          |
# va_linked_at    | timestamp with time zone |           |          |

# Confirm unique constraint
psql -U zammad -d zammad_production -c "\di" | grep va_icn

# Confirm no existing data was modified
psql -U zammad -d zammad_production -c "SELECT COUNT(*) FROM users WHERE va_icn IS NOT NULL;"
# Expected: 0
```

## Rollback (if needed)

```sql
BEGIN;
DROP INDEX IF EXISTS idx_users_va_icn;
ALTER TABLE users DROP COLUMN IF EXISTS va_linked_at;
ALTER TABLE users DROP COLUMN IF EXISTS va_icn;
COMMIT;
```

## Security Notes

- `va_icn` is PII — it is the VA Integration Control Number
- It is stored in the `users` table which already contains PII (email, name, phone)
- The ICN must NEVER appear in API responses (handled in Phase 2)
- Crawdad review applies to any endpoint that touches this column
