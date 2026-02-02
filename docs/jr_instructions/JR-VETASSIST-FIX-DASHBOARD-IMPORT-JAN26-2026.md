# Jr Instruction: Fix VetAssist Dashboard get_current_user Import

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Problem

File `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py` has wrong import on line 10:

**Current (wrong):**
```python
from .auth import get_current_user
```

**Should be:**
```python
from app.core.security import get_current_user
```

---

## Fix

```bash
sed -i 's/from .auth import get_current_user/from app.core.security import get_current_user/' /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py
```

---

## Verify

```bash
grep "get_current_user" /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py | head -1
```

Should show: `from app.core.security import get_current_user`
