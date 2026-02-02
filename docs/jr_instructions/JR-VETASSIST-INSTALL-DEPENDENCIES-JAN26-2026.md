# Jr Instruction: Install VetAssist Backend Dependencies

**Task ID:** To be assigned
**Jr Type:** Infrastructure Jr.
**Priority:** P1 (Blocking other repairs)
**Category:** Infrastructure

---

## Problem

VetAssist backend venv is missing dependencies. Task #337 failed with:
```
ModuleNotFoundError: No module named 'slowapi'
```

This blocks all other backend repairs.

---

## Steps

1. **Check requirements.txt exists**:
   ```bash
   ls -la /ganuda/vetassist/backend/requirements.txt
   ```

2. **Activate venv and install**:
   ```bash
   cd /ganuda/vetassist/backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **If requirements.txt missing, create minimal one**:
   ```
   fastapi>=0.100.0
   uvicorn[standard]>=0.22.0
   python-multipart>=0.0.6
   pydantic>=2.0
   psycopg2-binary>=2.9.9
   python-jose[cryptography]>=3.3.0
   passlib[bcrypt]>=1.7.4
   slowapi>=0.1.9
   httpx>=0.24.0
   python-dotenv>=1.0.0
   ```

4. **Verify imports work**:
   ```bash
   python -c "from slowapi import Limiter; print('slowapi OK')"
   python -c "from app.main import app; print('app imports OK')"
   ```

---

## Sudo Required

If pip fails due to permissions, create `/ganuda/scripts/sudo_vetassist_deps.sh`:
```bash
#!/bin/bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install -r requirements.txt
```

Flag for TPM to run with sudo.

---

## Success Criteria

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -c "from app.main import app"
```

No import errors.
