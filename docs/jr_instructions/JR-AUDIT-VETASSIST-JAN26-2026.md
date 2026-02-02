# Jr Instruction: Audit VetAssist Application

**Task ID:** To be assigned
**Jr Type:** Research Jr.
**Priority:** P1
**Category:** Audit

---

## Audit Target

- **Path:** `/ganuda/vetassist/`
- **Scope:** Full application (backend + frontend)
- **Focus Areas:** Security, Architecture, Import Dependencies

---

## Context

VetAssist backend is currently non-functional due to import errors. TPM initial investigation found:
- Circular imports in auth system
- Hardcoded credentials in multiple files
- Frontend-backend feature gap

This audit will create a formal findings report for repair planning.

---

## Audit Checklist

### 1. Backend Structure (`/ganuda/vetassist/backend/`)

- [ ] List all API endpoints in `app/api/v1/endpoints/`
- [ ] List all services in `app/services/`
- [ ] List all core modules in `app/core/`
- [ ] Map import dependencies between modules
- [ ] Identify circular imports

### 2. Security Scan

- [ ] Search for hardcoded passwords: `grep -r "password" --include="*.py"`
- [ ] Search for hardcoded hosts: `grep -r "192.168" --include="*.py"`
- [ ] Check for SQL injection risks (raw SQL queries)
- [ ] Verify authentication on protected routes

### 3. Database Access

- [ ] Identify SQLAlchemy ORM usage
- [ ] Identify raw psycopg2 usage
- [ ] Flag inconsistent patterns
- [ ] Check connection string sources

### 4. Frontend Structure (`/ganuda/vetassist/frontend/`)

- [ ] List all pages in `src/pages/` or `src/app/`
- [ ] List all components in `src/components/`
- [ ] Compare frontend routes to backend endpoints
- [ ] Identify missing UI for existing APIs

### 5. Configuration

- [ ] Check `app/core/config.py` for required env vars
- [ ] Check systemd service files
- [ ] Identify missing secrets/configuration

---

## Output Requirements

Create audit report at:
`/ganuda/docs/audits/AUDIT-VETASSIST-20260126.md`

Follow the standard audit report format from JR-AUDIT-PROTOCOL-TEMPLATE.md

Include:
- Executive summary
- Critical/High/Medium/Low findings tables
- File counts and line counts
- Prioritized recommendations
- Seven Generations assessment

---

## Success Criteria

- All checklist items completed
- Findings categorized by severity
- Clear recommendations for repair
- Report suitable for Jr task creation

---

## Do NOT

- Modify any code
- Fix issues during audit
- Skip documenting "obvious" issues
