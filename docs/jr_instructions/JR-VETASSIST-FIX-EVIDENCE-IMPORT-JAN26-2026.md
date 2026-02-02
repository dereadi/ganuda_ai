# Jr Instruction: Fix VetAssist Evidence get_current_user Import

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Fix

```bash
sed -i 's/from .auth import get_current_user/from app.core.security import get_current_user/' /ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py
```

---

## Verify

```bash
grep "get_current_user" /ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py | head -1
```

Should show: `from app.core.security import get_current_user`
