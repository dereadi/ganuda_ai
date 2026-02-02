# Jr Instruction: Fix VetAssist Limiter Import

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Problem

File `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py` has wrong import:

**Current (wrong):**
```python
from app.api.v1.limiter import limiter
```

**Should be:**
```python
from app.core.rate_limit import limiter
```

---

## Fix

```bash
sed -i 's/from app.api.v1.limiter import limiter/from app.core.rate_limit import limiter/' /ganuda/vetassist/backend/app/api/v1/endpoints/auth.py
```

---

## Verify

```bash
grep "limiter" /ganuda/vetassist/backend/app/api/v1/endpoints/auth.py | head -1
```

Should show: `from app.core.rate_limit import limiter`
