# KB: VetAssist Split Database Architecture

**KB ID:** KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026
**Date:** 2026-01-27
**Status:** Active

---

## Overview

VetAssist uses a **split-database architecture** with data distributed across two PostgreSQL databases on bluefin (192.168.132.222):

| Database | Purpose | Backend Config |
|----------|---------|----------------|
| `triad_federation` | Auth, users, chat sessions | `.env` DATABASE_URL |
| `zammad_production` | Wizard sessions, thermal memory, CMDB | database_config.py default |

## Connection Details

### triad_federation
- **Used by**: FastAPI backend auth endpoints, SQLAlchemy ORM
- **Tables**: users, user_sessions, chat_sessions, chat_messages, council_validations
- **Configured in**: `/ganuda/vetassist/backend/.env`

```bash
DATABASE_URL=postgresql://claude:jawaseatlasers2@192.168.132.222:5432/triad_federation
```

### zammad_production
- **Used by**: Dashboard endpoints (raw psycopg2), wizard data, thermal memory
- **Tables**: vetassist_wizard_sessions, thermal_memory_archive, etc.
- **Configured in**: `/ganuda/vetassist/backend/app/core/database_config.py` (default)

## Linking Users to Wizard Data

The `veteran_id` field is the foreign key that links across databases:

1. User authenticates via `triad_federation.users` table
2. User's `id` (UUID) serves as `veteran_id`
3. Dashboard queries `zammad_production.vetassist_wizard_sessions WHERE veteran_id = ?`

**Important**: When creating new users, ensure the user's `id` in `triad_federation.users` matches the `veteran_id` used in wizard sessions.

## Example Query Flow

```
1. POST /api/v1/auth/login
   → Queries triad_federation.users by email
   → Returns JWT with user.id as subject

2. GET /api/v1/dashboard/{veteran_id}
   → Uses veteran_id from JWT
   → Queries zammad_production.vetassist_wizard_sessions
   → Returns claims/evidence from wizard
```

## Troubleshooting

### Symptom: Login returns "Incorrect email or password" but user exists

**Cause**: User may have been created in wrong database (zammad_production instead of triad_federation)

**Solution**: Verify user exists in correct database:
```bash
# Check triad_federation (backend auth)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d triad_federation \
  -c "SELECT id, email FROM users WHERE email = 'user@example.com';"

# If missing, create in triad_federation
```

### Symptom: Dashboard shows no claims after login

**Cause**: User's `id` in triad_federation doesn't match `veteran_id` in wizard sessions

**Solution**: Ensure IDs match:
```bash
# Find veteran_id in wizard sessions
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production \
  -c "SELECT veteran_id FROM vetassist_wizard_sessions WHERE ..."

# Update user's id to match, or create new user with matching id
```

## Future Consideration

Consider consolidating to single database to simplify:
- Easier to maintain referential integrity
- Simpler connection management
- Atomic transactions across user and wizard data

---

FOR SEVEN GENERATIONS
