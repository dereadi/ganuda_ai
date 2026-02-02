# Jr Instruction: Remove VetAssist Hardcoded Credentials

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0 (Security)
**Category:** Security Fix
**From Review:** REVIEW-VETASSIST-20260126 - CRIT-001

---

## Problem

Hardcoded credentials found throughout VetAssist codebase:
- Database password "jawaseatlasers2" in multiple files
- API keys hardcoded
- LLM Gateway credentials embedded

This is a critical security vulnerability.

---

## Scope

Search and replace ALL hardcoded credentials in `/ganuda/vetassist/`

---

## Solution Steps

1. **Find all hardcoded credentials**:
   ```bash
   grep -r "jawaseatlasers2" /ganuda/vetassist/ --include="*.py"
   grep -r "password.*=" /ganuda/vetassist/ --include="*.py" | grep -v "def\|#\|validation"
   grep -r "192.168" /ganuda/vetassist/ --include="*.py"
   ```

2. **Create environment config pattern** in `app/core/config.py`:
   ```python
   import os

   DATABASE_URL = os.environ.get("VETASSIST_DATABASE_URL", "")
   LLM_GATEWAY_URL = os.environ.get("LLM_GATEWAY_URL", "http://localhost:8080")
   LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
   ```

3. **Replace each hardcoded value** with config import:
   ```python
   from app.core.config import DATABASE_URL, LLM_API_KEY
   ```

4. **Create .env.example** at `/ganuda/vetassist/backend/.env.example`:
   ```
   VETASSIST_DATABASE_URL=postgresql://user:pass@host:5432/vetassist
   LLM_GATEWAY_URL=http://192.168.132.223:8080
   LLM_API_KEY=your-api-key-here
   ```

---

## Do NOT

- Commit actual credentials to any file
- Create .env with real credentials (that's ops work)
- Delete credentials without replacing with env vars

---

## Success Criteria

```bash
grep -r "jawaseatlasers2" /ganuda/vetassist/ --include="*.py" | wc -l
```

Output: 0

AND

```bash
grep -r "LLM_API_KEY\|DATABASE_URL" /ganuda/vetassist/backend/app/core/config.py
```

Shows env var pattern
