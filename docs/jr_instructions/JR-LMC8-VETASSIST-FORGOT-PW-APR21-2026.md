# Jr Atomic: LMC-8 — VetAssist Forgot-Password Flow

**Parent Long Man cycle:** LMC-8 (duyuktv #1722)
**Council audit:** 348952186d1ac1ec (Apr 21 2026 top-5 ratification)
**SP:** 3
**Long Man phase:** adapt

## Task

Close the password-reset gap in VetAssist. Two sub-edits:

### Edit 1 — Add "Forgot password?" link to login page

**File:** `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`

The login page (currently 264 lines) has "create a new account" and "Login with VA.gov" links but NO forgot-password link. Add one under the password input. Use the same `<Link>` component pattern as the register link. Href: `/forgot-password`. Text: "Forgot password?". Style: right-aligned text-sm underlined link, same indigo palette as "create a new account".

### Edit 2 — Build backend `/api/v1/auth/forgot-password` endpoint

**Context:** the frontend page at `/ganuda/vetassist/frontend/app/(auth)/forgot-password/page.tsx` already POSTs to `${API_URL}/auth/forgot-password` with `{"email": "..."}`. The backend endpoint does NOT exist yet. Build it.

**Backend location:** `/ganuda/vetassist/backend/app/api/v1/` — follow existing endpoint patterns (see `admin.py` for structure).

**Create:**

1. **DB table** `vetassist_password_reset_tokens` (create via migration or direct SQL — follow project convention, check `/ganuda/vetassist/backend/migrations` if it exists, else direct SQL alembic):
   - `id` (serial pk)
   - `user_id` (int, fk to users table — check user-table name)
   - `token_hash` (varchar, sha256 hex digest of the actual token; DO NOT store raw tokens)
   - `expires_at` (timestamp, 30 min from creation)
   - `used_at` (timestamp nullable; NULL = valid, NOT NULL = consumed)
   - `created_at` (timestamp default NOW())
   - Index on token_hash

2. **Endpoint** `POST /api/v1/auth/forgot-password`:
   - Accept `{"email": "..."}`
   - Always return 200 OK with generic `{"ok": true}` — **do NOT reveal whether email exists** (enumeration protection)
   - If user exists: generate 32-byte random token (secrets.token_urlsafe(32)), store sha256 hash in DB, send email via project's existing email mechanism (check `/ganuda/vetassist/backend/app/services/` for email_service or similar — if missing, log the reset URL and flag "email stub: integrate real sender in follow-up")
   - Reset URL format: `{FRONTEND_BASE}/reset-password?token={token}`
   - Rate limit: max 3 requests per email per hour (use existing rate-limit decorator if present, else implement inline with Redis or simple in-memory TTL dict with comment flag)

3. **Stub endpoint** `POST /api/v1/auth/reset-password`:
   - Accept `{"token": "...", "new_password": "..."}`
   - Lookup token_hash, verify not expired + not used
   - Update user password_hash via existing password-hashing helper
   - Mark token used_at = NOW()
   - Return `{"ok": true}`
   - If token invalid/expired: 400 with generic error

**Important constraints:**
- Password hashing: use EXISTING helper from the auth module — do NOT roll your own bcrypt/argon2 setup
- Enumeration protection: response must NOT differ based on email existence
- Token storage: hashed only, never raw
- Add minimal tests in `/ganuda/vetassist/backend/tests/` covering the happy path + expired-token path

## Verification

```bash
cd /ganuda/vetassist/backend
# Run existing test suite — nothing should break
python -m pytest tests/ -x 2>&1 | tail -15
# Confirm endpoint registered
curl -s -X POST http://localhost:8001/api/v1/auth/forgot-password -H "Content-Type: application/json" -d '{"email":"test@example.com"}'
# Expect: {"ok": true} (generic response regardless of whether test@example.com exists)
```

## Done criteria

- [ ] Login page has "Forgot password?" link visible under password input
- [ ] DB table `vetassist_password_reset_tokens` exists with required columns + index on token_hash
- [ ] `POST /api/v1/auth/forgot-password` returns 200 with `{"ok": true}` for any email
- [ ] Token stored as sha256 hash, never raw
- [ ] `POST /api/v1/auth/reset-password` endpoint exists (even if reset-password page isn't built yet — frontend is follow-on)
- [ ] Existing test suite still passes
- [ ] At least one new test for the happy path

## Non-goals (DO NOT DO in this ticket)

- Do NOT build the `/reset-password` frontend page (follow-on ticket)
- Do NOT integrate a real email provider if one isn't already wired — log-and-stub is fine, flag follow-up
- Do NOT modify `/api/v1/auth/login` logic
- Do NOT touch VA.gov OAuth path

Report: files changed, test pass output, curl response.
