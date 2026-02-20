# Jr Instruction: VA Account Linking — Verification & Database Migration

**Task ID:** VETASSIST-VA-LINK-VERIFY-001
**Assigned:** Software Engineer Jr.
**Priority:** P2
**Created:** 2026-02-02
**TPM:** Claude Opus 4.5
**Depends on:** None

---

## Context

VA account linking backend code has been implemented:
- `POST /auth/link-va` endpoint exists in `auth.py:222`
- `GET /auth/va/callback` handles linked-login mode in `va_auth.py:80`
- `User` model has `va_icn` and `va_linked_at` columns
- `UserResponse` schema includes `va_linked: bool` and `va_linked_at`
- `VALinkRequest` schema exists in `schemas/auth.py`

**What may NOT be done:** The SQLAlchemy model has the columns, but the actual PostgreSQL table on bluefin may not have had the `ALTER TABLE` migration applied. If the columns don't exist in the database, the link-va endpoint will crash.

This task verifies the database is ready and the full linking flow works end-to-end.

---

## Step 1: Verify Database Columns Exist

Connect to bluefin and check:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d users"
```

Look for `va_icn` and `va_linked_at` columns.

**If columns DO NOT exist**, run the migration:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_icn VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_linked_at TIMESTAMPTZ;
```

**If columns already exist**, skip to Step 2.

Verify after migration:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('va_icn', 'va_linked_at');"
```

Expected: Two rows showing `va_icn` (character varying, YES) and `va_linked_at` (timestamp with time zone, YES).

---

## Step 2: Verify Backend Endpoints Respond

Test that the backend serves the relevant endpoints without import errors:

```bash
# Health check
curl -s https://vetassist.ganuda.us/api/v1/health | python3 -m json.tool

# Auth login (get a token)
curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ganuda.test","password":"testpass123"}' | python3 -m json.tool

# Get profile (should show va_linked field)
curl -s https://vetassist.ganuda.us/api/v1/auth/me \
  -H "Authorization: Bearer <token_from_above>" | python3 -m json.tool
```

The `/auth/me` response should include `"va_linked": false` and `"va_linked_at": null` for a user who hasn't linked.

---

## Step 3: Verify VA OAuth Flow Initiates

```bash
# This should return a redirect to VA.gov sandbox
curl -s -I "https://vetassist.ganuda.us/api/v1/auth/va/login"
```

Expected: `302 Found` with `Location:` header pointing to `sandbox-api.va.gov` or similar.

---

## Step 4: Verify Link-VA Endpoint Rejects Invalid Tokens

```bash
curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/link-va \
  -H "Authorization: Bearer <valid_auth_token>" \
  -H "Content-Type: application/json" \
  -d '{"va_session_token":"invalid-token-value"}'
```

Expected: `401` with `"Invalid VA session token"` — this confirms the endpoint is wired up and the JWT validation works.

---

## Step 5: Document Results

Report in your task output:
1. Whether `va_icn`/`va_linked_at` columns existed or needed migration
2. Whether `/auth/me` returns `va_linked` field
3. Whether `/auth/va/login` redirects to VA.gov
4. Whether `/auth/link-va` properly rejects invalid tokens
5. Any errors encountered

---

## Acceptance Criteria

1. `va_icn` and `va_linked_at` columns exist in the `users` table on bluefin
2. `va_icn` has a UNIQUE constraint
3. `GET /auth/me` response includes `va_linked` and `va_linked_at` fields
4. `GET /auth/va/login` redirects to VA.gov OAuth
5. `POST /auth/link-va` rejects invalid VA tokens with 401
6. No import errors or 500s on any endpoint

---

## Frontend Note

Frontend work for VA linking (settings page with "Link VA.gov Account" button, VA success page updates) will be deployed by the TPM separately since frontend files are outside the RLM override scope. The backend endpoints verified here are the foundation for that frontend work.

---

*For Seven Generations*
*Cherokee AI Federation — VetAssist Auth Team*
