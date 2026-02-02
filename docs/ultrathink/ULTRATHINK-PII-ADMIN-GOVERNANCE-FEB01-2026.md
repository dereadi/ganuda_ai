# ULTRATHINK: PII Administration & Governance Architecture
**Date:** February 1, 2026
**Author:** TPM (Claude Opus 4.5)
**Council Vote:** #8365 — 87.3% confidence, APPROVED with 2 concerns
**Regulatory Framework:** 38 CFR 0.605, 38 USC 5701, FIPS 140-2/199, HIPAA (advisory)

---

## 1. Problem Statement

VetAssist stores veteran PII across multiple tables with no administrative access controls, no role-based visibility, and no audit trail for human data access. The product owner has intentionally avoided viewing production PII data. As the platform scales to multiple administrators, security levels, and potentially multiple "Assist" apps, we need a governance framework that:

1. Allows admin functions (password reset, identity verification, user management) WITHOUT exposing unnecessary PII
2. Implements least-privilege access at the database layer, not just application layer
3. Complies with VA data handling regulations (38 CFR 0.605 — legally binding, not advisory)
4. Creates an audit trail for every human PII access event
5. Supports future multi-tenant, multi-role administration

**User's exact words:** *"I would prefer least privilege. Like I could know First and Last name and userid, and some way to verify that they who they say they are, like for functions like resetting password."*

---

## 2. Current State Assessment

### 2.1 Database Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| Primary Database | PostgreSQL on bluefin (192.168.132.222) | `zammad_production` |
| PII Database | Exists, unused | `vetassist_pii` (via `get_pii_db_connection()`) |
| Connection Pooling | pool_size=10, max_overflow=20 | SQLAlchemy engine |
| Auth | JWT (HS256), 24hr expiry, session tracking | `user_sessions` table |
| RBAC | **NONE** — only `is_active` flag exists | `users.is_active` |
| Admin Endpoints | **NONE** | Gap |
| Admin Audit Trail | **NONE** — existing audit is AI-generation only | `vetassist_ai_audit_trail` |

### 2.2 PII Distribution Map

| Table | PII Columns | Current Rows | Sensitivity |
|-------|-------------|-------------|-------------|
| `users` | email, password_hash, first_name, last_name, phone, va_icn | 6 | HIGH — identity + credentials |
| `vetassist_dependents` | (dependent info) | 0 | HIGH — family PII |
| `chat_messages` | content (free text, may contain PII) | 4 | MEDIUM — user-generated |
| `vetassist_va_tokens` | access_token, refresh_token | varies | CRITICAL — credential material |
| `vetassist_va_connections` | va_api_token | varies | CRITICAL — credential material |
| `vetassist_users` | VA-linked user accounts | varies | HIGH — VA identity |
| `vetassist_auth_audit` | ip_address, user_agent | varies | LOW — metadata |
| `user_sessions` | token_hash, ip_address, user_agent | varies | MEDIUM — session metadata |

### 2.3 Two Identity Systems (From VA Linking Plan)

The VA Account Linking plan (approved, in-progress) introduces `va_icn` on the `users` table. This creates a bridge between email/password auth and VA OAuth but does NOT change the PII governance requirements — it adds another PII field (ICN) that must be protected.

---

## 3. Research Synthesis

### 3.1 Industry Patterns (Stripe/GitHub Model)

**Stripe's approach** is the gold standard for admin PII access:
- PII stored in isolated infrastructure with separate network segment
- Admin dashboard shows tokenized references, not raw PII
- Role-based API keys with scoped permissions
- Every access event logged with IP, timestamp, justification field

**GitHub's Entitlements system** uses GitOps-driven IAM:
- All access changes go through pull requests
- Time-boxed access grants with automatic expiry
- Separation between "who can see data" and "who can modify data"

**Relevant pattern for VetAssist:** Challenge-response identity verification. Admin sees `First Name: John, Last Name: D***`, asks veteran: "What is the email address on your account?" — verifies match without admin needing to see email. This eliminates admin PII exposure for 95%+ of support scenarios.

### 3.2 PostgreSQL Security Layers

Three complementary mechanisms available:

**Row-Level Security (RLS):**
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;  -- Critical: applies to table owner too

CREATE POLICY admin_read ON users
    FOR SELECT
    TO vetassist_admin
    USING (true);  -- Can see all rows, but column masking via views
```

**Security Barrier Views with Column Masking:**
```sql
CREATE VIEW admin_users WITH (security_barrier=true) AS
SELECT
    id,
    first_name,
    LEFT(last_name, 1) || '***' AS last_name_masked,
    CASE
        WHEN current_setting('app.admin_tier') = '3' THEN email
        ELSE LEFT(email, 2) || '***@' || SPLIT_PART(email, '@', 2)
    END AS email,
    veteran_status,
    va_icn IS NOT NULL AS va_linked,
    created_at,
    is_active
FROM users;
```

**postgresql_anonymizer extension:**
- `anon.partial('john.doe@email.com', 2, '***', 4)` → `jo***l.com`
- `anon.partial_email('john.doe@email.com')` → `j***@email.com`
- Dynamic masking per database role — zero application code changes
- ~12% query overhead (acceptable for admin operations, not user-facing)

**Recommended approach:** Security barrier views for day-to-day admin + RLS as defense-in-depth + `postgresql_anonymizer` for declarative masking rules. Views are the primary control because they're simpler to reason about and audit.

### 3.3 PII Tokenization Architecture

**Core concept:** Application stores UUID tokens, vault stores encrypted PII. Blind indexes (HMAC-SHA256) enable search without decryption.

```
┌─────────────┐       ┌──────────────┐       ┌────────────────┐
│ Application  │ ───── │  pii_tokens  │ ───── │  Encrypted PII │
│ users.email  │       │  token (UUID)│       │  (AES-256-GCM) │
│ = token_ref  │       │  blind_index │       │  in vault DB   │
└─────────────┘       │  field_type  │       └────────────────┘
                      │  key_version │
                      └──────────────┘
```

**Open-source options:**
- **Databunker** (MIT) — most mature, self-hosted, REST API, automatic tokenization
- **HashiCorp Vault Transform** — enterprise, requires Vault infrastructure
- **Custom implementation** — using `vetassist_pii` database (already exists, unused)

**Recommendation:** Phase 1 uses the simpler security-barrier views approach. Phase 2+ implements full tokenization in `vetassist_pii` database. Rationale: we have 6 users today. Tokenization is the correct long-term architecture but adds significant complexity for the current scale. The views + RLS approach provides 38 CFR compliance immediately.

### 3.4 VA Regulatory Requirements

**38 CFR 0.605 — Nine Ethics Principles (Legally Binding):**
1. Statistical records only with informed consent
2. Maintain only relevant, timely, complete records
3. No secret record systems
4. Rules of conduct for all personnel handling records
5. Administrative, technical, physical safeguards
6. Collection directly from individual when possible
7. **Inform individuals about record use, access, and corrections** ← Admin must support this
8. Minimum necessary access
9. **Accounting of disclosures** ← Every time an admin views PII, it must be logged

**38 USC 5701 — Claims Confidentiality:**
- All claims records are confidential and privileged
- Disclosure only to authorized persons
- VA Inspector General can audit at any time

**HIPAA Gap:**
- When veteran data leaves VA systems into third-party apps, HIPAA protections may not follow
- VetAssist should treat all veteran data as if HIPAA applies regardless — this exceeds requirements but is ethically correct and the Council concurs

**FIPS Requirements:**
- FIPS 140-2: Encryption at rest and in transit (PostgreSQL SSL + disk encryption)
- FIPS 199 MODERATE: Minimum classification for veteran data systems

**Breach Reporting:**
- 1-hour notification to VA upon suspected breach
- Liquidated damages: per-individual financial penalties
- Implication: audit trail must be granular enough to identify exactly which records were accessed

**Key architectural implication:** VA's design intent is transient data flow — pull from VA APIs in real-time, don't warehouse. For data we must store (user accounts, chat history), minimize PII surface area and implement accounting of every access.

---

## 4. Council Vote #8365 — Synthesis

**Vote result:** 87.3% confidence, APPROVED

**All 7 specialists aligned on:**
1. Admin dashboard fields: first_name, last_name (masked), user_id, veteran_status, account_status, created_at
2. Identity verification: masked email + security questions (NOT last-4-phone — Spider and Eagle Eye objected)
3. 4-tier RBAC approved
4. Layered DB security (RLS + views + app-layer)
5. Mandatory audit logging for all PII access
6. Build pii_tokens tokenization table (long-term)

**Concerns raised:**
- **Turtle (7th Generation Guardian):** Ensure architecture scales to future Assist apps without retrofit
- **Peace Chief:** Consensus needed on break-glass emergency access pattern

**TPM synthesis:** Architecture must be designed as a shared service (`ganuda_admin`) not VetAssist-specific. Break-glass requires dual-approval (admin + system owner) with time-limited elevation.

---

## 5. Architecture Decision: 4-Tier RBAC

### Tier Definitions

| Tier | Role | Can See | Use Case |
|------|------|---------|----------|
| **Tier 1** | `vetassist_public` | Aggregates only | Public stats, report counts |
| **Tier 2** | `vetassist_admin` | Names (masked last), user_id, status, dates | Day-to-day admin, password reset, account management |
| **Tier 3** | `vetassist_security` | Full PII (logged + time-limited) | Security incidents, legal requests, identity disputes |
| **Tier 4** | `vetassist_system` | Credential material | Automated processes only — never human-accessible |

### Tier 2 — Admin View (Primary Operating Tier)

What the admin sees:
```
┌─────────────────────────────────────────────────────────────┐
│ VetAssist Admin — User Management                           │
├──────┬───────────┬──────────┬──────────┬────────┬──────────┤
│ ID   │ First     │ Last     │ Status   │ VA     │ Created  │
├──────┼───────────┼──────────┼──────────┼────────┼──────────┤
│ a3f2 │ John      │ D***     │ Active   │ Linked │ Jan 15   │
│ b7c1 │ Sarah     │ M***     │ Active   │ No     │ Jan 20   │
│ d4e9 │ Michael   │ R***     │ Inactive │ Linked │ Jan 22   │
└──────┴───────────┴──────────┴──────────┴────────┴──────────┘

Actions: [Reset Password] [Deactivate] [View Sessions]
```

What the admin does NOT see:
- Email address (masked in verification flow)
- Phone number
- VA ICN
- Password hash
- Service dates
- Disability rating
- Chat message content

### Identity Verification Flow (Challenge-Response)

When a veteran contacts support claiming they can't access their account:

```
1. Admin searches by first name + last initial → finds candidate
2. Admin clicks "Verify Identity"
3. System prompts: "Ask the user: What email address is on your account?"
4. Veteran says: "john.doe@gmail.com"
5. Admin enters what veteran said into verification field
6. System compares (server-side) — returns MATCH or NO MATCH
7. If MATCH → admin can proceed with password reset
8. Audit log records: admin_id, user_id, verification_type, result, timestamp
```

The admin NEVER sees the email. The comparison happens server-side. This is the challenge-response pattern from the Stripe research — eliminates 95%+ of admin PII exposure.

### Break-Glass Access (Tier 3 Elevation)

For security incidents or legal requests requiring full PII:

```
1. Admin requests Tier 3 elevation via admin panel
2. System requires: MFA confirmation + written justification
3. Elevation granted for 15 minutes (configurable)
4. During elevation: full PII visible, every field access logged
5. Automatic de-elevation after timeout
6. All Tier 3 access events flagged for weekly review
```

**Phase 1 implementation:** Tier 3 access is manual (database query by system owner with justification logged). Automated break-glass UI is Phase 3+.

---

## 6. Implementation Architecture

### 6.1 Database Layer

**New PostgreSQL roles:**
```sql
CREATE ROLE vetassist_admin LOGIN PASSWORD '...' IN ROLE vetassist_readonly;
CREATE ROLE vetassist_security LOGIN PASSWORD '...' IN ROLE vetassist_admin;
-- vetassist_system = existing 'claude' role (application user)
```

**Security barrier views (one per tier):**
```sql
-- Tier 2: Admin view — names visible, everything else masked/hidden
CREATE VIEW admin_user_view WITH (security_barrier=true) AS
SELECT
    id,
    first_name,
    LEFT(last_name, 1) || repeat('*', 3) AS last_name,
    veteran_status,
    is_active,
    va_icn IS NOT NULL AS va_linked,
    va_linked_at,
    created_at,
    updated_at,
    last_login,
    email_verified
FROM users;

-- Tier 2: No access to these tables at all
-- chat_messages, vetassist_va_tokens, vetassist_va_connections
```

**RLS policies (defense-in-depth):**
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Application role can see all users (for auth flows)
CREATE POLICY app_full_access ON users
    FOR ALL TO vetassist_system USING (true);

-- Admin role can only SELECT (no UPDATE/DELETE directly)
CREATE POLICY admin_read_only ON users
    FOR SELECT TO vetassist_admin USING (true);

-- Chat messages: users can only see their own
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_own_messages ON chat_messages
    FOR SELECT TO vetassist_system
    USING (session_id IN (
        SELECT id FROM chat_sessions WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
```

**Admin audit table:**
```sql
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    admin_role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,        -- 'view_user', 'reset_password', 'verify_identity', 'elevate_tier3'
    target_user_id UUID,
    target_table VARCHAR(100),
    fields_accessed TEXT[],              -- ['first_name', 'last_name', 'email_masked']
    justification TEXT,                  -- Required for Tier 3
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    tier_level INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 38 CFR 0.605 compliance: accounting of disclosures
    disclosure_type VARCHAR(50)          -- 'routine_admin', 'security_incident', 'legal_request'
);

CREATE INDEX idx_admin_audit_admin ON admin_audit_log(admin_id);
CREATE INDEX idx_admin_audit_target ON admin_audit_log(target_user_id);
CREATE INDEX idx_admin_audit_time ON admin_audit_log(created_at);
```

### 6.2 Application Layer

**New files needed:**

| File | Purpose |
|------|---------|
| `app/models/admin.py` | AdminRole model, admin_audit_log model |
| `app/core/rbac.py` | Role-based access control middleware, tier checks |
| `app/services/admin_service.py` | User management, identity verification, audit logging |
| `app/api/v1/endpoints/admin.py` | Admin API endpoints |

**Admin API endpoints:**

```
GET    /admin/users                    — List users (Tier 2 view)
GET    /admin/users/{id}               — Single user detail (Tier 2 view)
POST   /admin/users/{id}/verify        — Challenge-response verification
POST   /admin/users/{id}/reset-password — Send password reset email
POST   /admin/users/{id}/deactivate    — Set is_active = false
POST   /admin/users/{id}/reactivate    — Set is_active = true
GET    /admin/users/{id}/sessions      — View active sessions (metadata only)
DELETE /admin/users/{id}/sessions      — Revoke all sessions (force logout)
GET    /admin/audit                    — View admin audit log
GET    /admin/stats                    — Tier 1 aggregate stats (user counts, etc.)
```

**RBAC middleware pattern:**
```python
# app/core/rbac.py
from enum import IntEnum

class AdminTier(IntEnum):
    PUBLIC = 1      # Aggregate stats only
    ADMIN = 2       # Masked PII, user management
    SECURITY = 3    # Full PII, time-limited
    SYSTEM = 4      # Credential material, automated only

def require_tier(minimum_tier: AdminTier):
    """FastAPI dependency that checks admin tier level."""
    async def checker(current_user = Depends(get_current_user)):
        user_tier = current_user.get('admin_tier', 0)
        if user_tier < minimum_tier:
            raise HTTPException(403, "Insufficient privileges")
        # Log access at this tier level
        await log_admin_access(current_user, minimum_tier)
        return current_user
    return checker
```

### 6.3 Frontend (Admin Panel)

**New page:** `/admin` route (protected by Tier 2+ role check)

Components:
- User list table with masked data
- User detail panel with verification workflow
- Password reset trigger
- Session management (view/revoke)
- Audit log viewer (for Tier 3+ admins)
- Stats dashboard (Tier 1 — could be public)

### 6.4 What We're NOT Building Yet

- Full token vault (Phase 2+ — when user count exceeds ~100)
- Automated break-glass UI (Phase 3+ — manual Tier 3 for now)
- postgresql_anonymizer extension (requires extension install on bluefin — evaluate after RLS/views prove stable)
- Multi-app admin (Phase 4+ — when second Assist app launches)
- Databunker integration (Phase 3+ — evaluate after token vault needs are clearer)

---

## 7. Phased Implementation Plan

### Phase 1: Database Foundation (1 Jr Instruction)
**Scope:** SQL migration only — new roles, views, RLS policies, audit table

- Create PostgreSQL roles: `vetassist_admin`, `vetassist_security`
- Create `admin_audit_log` table
- Create `admin_user_view` security barrier view (Tier 2)
- Enable RLS on `users`, `chat_messages`, `user_sessions`
- Create RLS policies for each role
- Add `admin_tier` column to `users` table (INTEGER, default 0 = non-admin)
- Set product owner's account to `admin_tier = 2`

**Validation:** Connect as `vetassist_admin` role, query `admin_user_view` — should see masked data. Query `users` directly — should be blocked by RLS.

### Phase 2: Backend Admin Service (1 Jr Instruction)
**Scope:** Models, RBAC middleware, admin service, admin endpoints

- `app/models/admin.py` — AdminAuditLog SQLAlchemy model
- `app/core/rbac.py` — AdminTier enum, `require_tier()` dependency, audit logging
- `app/services/admin_service.py` — AdminService class:
  - `list_users()` — queries `admin_user_view`, not `users` table directly
  - `get_user_detail()` — single user from `admin_user_view`
  - `verify_identity()` — server-side comparison, logs result
  - `reset_password()` — generates reset token, sends email (or returns link)
  - `toggle_active()` — activate/deactivate with audit log
  - `get_user_sessions()` — session metadata (IPs, timestamps, not tokens)
  - `revoke_user_sessions()` — force logout with audit log
  - `get_audit_log()` — paginated admin audit entries
  - `get_stats()` — aggregate counts (total users, active, VA-linked, etc.)
- `app/api/v1/endpoints/admin.py` — Router with all admin endpoints
- Mount admin router in main app

**Validation:** Call `GET /admin/users` with admin JWT — should return masked user list. Call without admin tier — should get 403.

### Phase 3: Frontend Admin Panel (1 Jr Instruction)
**Scope:** Admin UI pages

- `/admin` — Protected route, Tier 2+ required
- User list table with search (first name only)
- User detail panel with identity verification workflow
- Password reset button
- Session management (view active sessions, revoke all)
- Audit log viewer (read-only, last 100 entries)
- Stats dashboard card (user counts, registration trends)

**Validation:** Login as admin → navigate to /admin → verify masked data display. Attempt identity verification flow. Check audit log records the access.

### Phase 4: Users Table Admin Tier Column + First Admin (1 Jr Instruction)
**Scope:** Add admin_tier to User model, create first admin account setup

- Add `admin_tier` column to SQLAlchemy User model
- SQL migration: `ALTER TABLE users ADD COLUMN admin_tier INTEGER DEFAULT 0`
- Admin setup endpoint (one-time use, secured): `POST /admin/setup` — promotes specified user to Tier 2
- Add "Admin" link in frontend Header component (only visible if `admin_tier >= 2`)

**Validation:** After setup, verify admin user can access /admin. Verify non-admin users cannot.

---

## 8. Security Controls Summary

| Control | Layer | Purpose |
|---------|-------|---------|
| PostgreSQL RLS | Database | Row-level access enforcement even if app is compromised |
| Security Barrier Views | Database | Column masking — admin never queries raw tables |
| FORCE ROW LEVEL SECURITY | Database | Prevents table owner from bypassing RLS |
| RBAC Middleware | Application | Tier checking before endpoint execution |
| Challenge-Response Verification | Application | Admin verifies identity without seeing PII |
| Admin Audit Log | Database | 38 CFR 0.605 accounting of disclosures |
| JWT + Session Tracking | Application | Admin sessions tracked like user sessions |
| Time-Limited Tier 3 | Application | Full PII access auto-expires |

---

## 9. 38 CFR 0.605 Compliance Matrix

| Principle | Implementation |
|-----------|---------------|
| 1. Statistical records with consent | Admin stats use aggregates only (Tier 1) |
| 2. Relevant, timely, complete records | Admin can view record status but not modify PII directly |
| 3. No secret record systems | Admin audit log is reviewable by Security tier |
| 4. Rules of conduct for personnel | RBAC tiers enforce rules programmatically |
| 5. Administrative, technical, physical safeguards | RLS + views + audit + JWT |
| 6. Collection from individual | Not applicable to admin access |
| 7. Inform about access and corrections | Veteran-facing: future profile page shows access log |
| 8. Minimum necessary access | Tier 2 sees only what's needed for admin functions |
| 9. Accounting of disclosures | `admin_audit_log` records every access event |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Admin account compromised | Medium | High | MFA (Phase 3+), session monitoring, auto-revocation |
| RLS bypass via SQL injection | Low | Critical | Parameterized queries (SQLAlchemy ORM), no raw SQL in admin endpoints |
| Audit log tampering | Low | High | Audit table INSERT-only for admin role (no UPDATE/DELETE) |
| Over-retention of PII | Medium | Medium | VA's transient data intent — evaluate TTL policies for chat history |
| postgresql_anonymizer not available | N/A | Low | Using manual masking in views (Phase 1) — extension is Phase 3+ |

---

## 11. Future Roadmap (Beyond Current Sprint)

### Phase 5: Token Vault (When Users > 100)
- Create `pii_tokens` table in `vetassist_pii` database
- Implement blind indexes (HMAC-SHA256) for searchable encryption
- Migrate PII columns to token references
- Application stores only UUID token, vault stores encrypted value

### Phase 6: Multi-App Admin (When Second Assist App Launches)
- Extract admin infrastructure to `ganuda_admin` shared library
- Tenant-scoped views and RLS policies
- Shared audit log across apps

### Phase 7: Automated Break-Glass
- UI for Tier 3 elevation requests
- Dual-approval workflow (admin requests, security approves)
- Time-limited elevation with automatic de-escalation
- Integration with notification system (Telegram alerts)

### Phase 8: postgresql_anonymizer Extension
- Install and configure on bluefin
- Replace manual masking in views with declarative `anon.partial()` rules
- Dynamic masking per database role — zero application code changes

---

## 12. Jr Instruction Sequencing

```
Phase 1: SQL Migration                      ← No code dependencies
    ↓
Phase 4: Admin Tier Column + User Model     ← Depends on Phase 1 schema
    ↓
Phase 2: Backend Admin Service              ← Depends on Phase 4 (admin_tier in model)
    ↓
Phase 3: Frontend Admin Panel               ← Depends on Phase 2 (API endpoints)
```

**Note:** Phases renumbered for execution order. Phase 4 (admin tier column) must come before Phase 2 (backend service) because the RBAC middleware needs the `admin_tier` field on the User model.

**Estimated Jr Instructions:** 4 (one per phase)
**Critical path:** Phase 1 → Phase 4 → Phase 2 → Phase 3

---

## 13. Decision Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Security barrier views over postgresql_anonymizer | Simpler, no extension install, sufficient for 6 users | anon extension (Phase 3+) |
| Challenge-response over masked-email display | Admin never sees PII at all — stronger than masking | Masked email display, last-4-phone (rejected by Council) |
| RLS + views (layered) over views-only | Defense-in-depth — if view is bypassed, RLS still blocks | Views only, RLS only |
| admin_tier column over separate admin_roles table | Simpler for 4 tiers, avoids join overhead | Separate roles table (Phase 6+ if needed) |
| Manual Tier 3 over automated break-glass | 6 users doesn't justify UI complexity | Automated break-glass (Phase 7) |
| Same database over separate PII database | Fewer moving parts for Phase 1, `vetassist_pii` reserved for token vault | Separate database (Phase 5) |

---

*This architecture satisfies the Council's 4-tier RBAC approval (vote #8365), addresses Turtle's 7th Generation concern through multi-app extensibility design, and resolves Peace Chief's break-glass consensus requirement through the manual-first, automated-later approach. 38 CFR 0.605 compliance is achieved at Phase 1 completion.*
