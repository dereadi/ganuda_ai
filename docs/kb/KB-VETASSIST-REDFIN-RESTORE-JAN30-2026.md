# KB-VETASSIST-REDFIN-RESTORE-JAN30-2026
## VetAssist Backend Restore to Redfin — Full Incident + Fix Documentation

**Created:** 2026-01-30
**Author:** TPM (Claude Code session)
**Severity:** P0 — Blocked all user testing
**Node:** redfin (192.168.132.223)
**Resolution Time:** ~2 hours from first symptom to working dashboard

---

### Symptom Timeline

1. **User reports "Not Found"** when clicking file upload on dashboard (logged in as Marcus)
2. **User reports blank screen** after running batch restore script
3. **User reports "stuck on Loading..."** after clearing browser localStorage
4. **User reports UUID error** on file upload after static file fix

---

### Root Cause Chain (4 cascading issues)

#### Issue 1: Dual Backend Conflict
- **v1.0** on redfin (`/ganuda/vetassist/backend/`, `python-jose` + `passlib`, systemd `vetassist-backend.service`)
- **v2.0** on bluefin (`/home/dereadi/cherokee_venv/`, `pyjwt` + raw `bcrypt`, nohup process)
- Caddy on redfin was proxying `/api/*` to `192.168.132.222:8001` (bluefin) instead of `localhost:8001`
- v1.0 was missing two endpoints: `POST /{veteran_id}/files` and `DELETE /{veteran_id}/files/{file_id}`
- **Decision:** Keep v1.0 on redfin, add the 2 missing endpoints. Do NOT replace with v2.0.

#### Issue 2: Next.js Standalone Build Missing Static Files
- `next.config.js` has `output: 'standalone'`
- `next build` creates `.next/standalone/` with a self-contained server
- BUT static assets (JS chunks, CSS, fonts) are NOT copied into standalone automatically
- The server runs from `.next/standalone/` (confirmed via `/proc/{pid}/cwd`)
- All `/_next/static/*` requests returned **HTTP 404** — HTML rendered but zero JS/CSS loaded
- **This is the documented Next.js behavior** — see https://nextjs.org/docs/app/api-reference/config/next-config-js/output

**CRITICAL: After every `npm run build`, you MUST run:**
```bash
cp -r .next/static .next/standalone/.next/static
```
If a `public/` directory exists:
```bash
cp -r public .next/standalone/public
```

#### Issue 3: JWT Token Mismatch After Backend Switch
- Marcus logged in through v2.0 backend (bluefin) → JWT signed with bluefin's SECRET_KEY
- Caddy reverted to v1.0 backend (redfin) → different SECRET_KEY
- Browser's stored JWT was invalid for v1.0 → auth context returned `user = null` → blank screen
- **Fix:** Clear `auth_token` from browser localStorage, re-login through v1.0

#### Issue 4: Database Schema Mismatches in Upload Endpoint (4 fixes)
1. **UUID type mismatch:** `vetassist_wizard_sessions.session_id` is UUID type, not VARCHAR. Original code used `f"dashboard-{veteran_id}"` — not a valid UUID.
   - **Fix:** `uuid.uuid5(uuid.NAMESPACE_DNS, f"dashboard-{veteran_id}")` for deterministic UUID
2. **Wrong column name:** `vetassist_wizard_files` has `file_uuid`, not `stored_name`.
   - **Fix:** Changed INSERT column to `file_uuid`
3. **ON CONFLICT requires unique constraint:** `idx_wizard_session` is a regular btree index, NOT unique. `ON CONFLICT (session_id) DO NOTHING` fails.
   - **Fix:** Replaced with SELECT-then-INSERT pattern
4. **varchar(36) overflow:** `file_uuid` is varchar(36) — exactly UUID length. Code was writing `{uuid}.pdf` (40+ chars).
   - **Fix:** Store bare UUID in `file_uuid`, keep full filename with extension only in `file_path`

---

### Files Modified

| File | Change | Node |
|------|--------|------|
| `app/api/v1/endpoints/dashboard.py` | Added upload/delete endpoints, fixed UUID + column name | redfin |
| `/etc/caddy/Caddyfile` | Reverted `reverse_proxy` from `192.168.132.222:8001` to `localhost:8001` | redfin |
| `components/dashboard/FileDropZone.tsx` | Added `Authorization: Bearer` header to upload + delete fetch | redfin |
| `components/dashboard/ScratchpadEditor.tsx` | Added `Authorization: Bearer` header to save fetch | redfin |
| `components/dashboard/ResearchPanel.tsx` | Added `Authorization: Bearer` header to GET + POST fetch | redfin |
| `.next/standalone/.next/static/` | Copied static assets from `.next/static/` | redfin |

---

### Database Schema Reference

**vetassist_wizard_sessions:**
| Column | Type | Notes |
|--------|------|-------|
| id | integer | PK auto-increment |
| session_id | **uuid** | Must be valid UUID |
| wizard_type | varchar | 'dashboard' for direct uploads |
| veteran_id | varchar | User UUID as string |
| current_step | integer | 0 for dashboard pseudo-sessions |
| answers | jsonb | '{}' for dashboard pseudo-sessions |
| status | varchar | 'active' |

**vetassist_wizard_files:**
| Column | Type | Notes |
|--------|------|-------|
| id | integer | PK auto-increment |
| session_id | **varchar** | String, NOT UUID type |
| file_uuid | varchar | Stored filename (uuid + extension) |
| original_name | varchar | User's original filename |
| category | varchar | 'other', 'medical', etc. |
| file_size | integer | Bytes |
| mime_type | varchar | 'application/pdf', 'image/jpeg', etc. |
| file_path | text | Full path on disk |
| deleted | boolean | Soft delete flag |

**Key Gotcha:** `wizard_sessions.session_id` is UUID type but `wizard_files.session_id` is VARCHAR. The dashboard GET joins them with `f.session_id::text = s.session_id::text` — both cast to text for comparison.

---

### Architecture After Fix

```
Browser → vetassist.ganuda.us → Caddy (redfin:443)
  → /api/*  → localhost:8001 (redfin v1.0 backend)  ← ALL API traffic
  → /*      → localhost:3000 (redfin Next.js frontend, standalone mode)

Backend → 192.168.132.222:5432 (bluefin PostgreSQL)  ← Database
Backend → 192.168.132.223:8080 (redfin LLM Gateway)  ← AI inference

Upload dir: /ganuda/vetassist/uploads/{veteran_id}/
```

---

### Operational Procedures

#### Rebuilding Frontend (MUST follow these steps)
```bash
cd /ganuda/vetassist/frontend
npm run build
cp -r .next/static .next/standalone/.next/static
# If public/ exists: cp -r public .next/standalone/public
pkill -f 'next-server'
sleep 2
sudo -u dereadi bash -c 'cd /ganuda/vetassist/frontend && nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &'
```

#### Restarting Backend
```bash
sudo systemctl restart vetassist-backend
curl -s http://localhost:8001/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

#### Test User Credentials
| User | Email | Password |
|------|-------|----------|
| Marcus | test1@vetassist.test | password1 |
| Sarah | test2@vetassist.test | password2 |
| David | test3@vetassist.test | password3 |
| Maria | test4@vetassist.test | password4 |
| James | test5@vetassist.test | password5 |

---

### Lessons Learned

1. **Always check `next.config.js` for `output: 'standalone'`** before deploying. Standalone mode requires manual static file copy after every build. This is not a bug — it's documented behavior for containerized deployments.

2. **Never proxy API traffic cross-node when backend and frontend are co-located.** The v2.0 bluefin proxy introduced JWT mismatch, CORS complexity, and network latency for zero benefit.

3. **Check database column types before writing INSERT statements.** The `session_id` UUID vs VARCHAR mismatch between `wizard_sessions` and `wizard_files` tables was a schema design inconsistency that caused the upload to fail silently from the frontend's perspective.

4. **When switching backends, users must re-authenticate.** Different SECRET_KEYs mean all existing JWTs are invalid. Consider a migration path or shared secret for future backend transitions.

5. **`pkill -f 'next-server'` is unreliable** for killing Next.js. Use `fuser -k 3000/tcp` or `kill $(lsof -ti:3000)` instead. The standalone server process name may not match the pattern.
