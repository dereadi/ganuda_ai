# Jr Instruction: Simple Import Path Fix for VetAssist

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Problem

File `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py` has wrong import on line 10.

**Current (wrong):**
```python
from app.api.v1.schemas.response import MessageResponse
```

**Should be:**
```python
from app.schemas.auth import MessageResponse
```

---

## Fix

Use sed to replace line 10:

```bash
sed -i 's/from app.api.v1.schemas.response import MessageResponse/from app.schemas.auth import MessageResponse/' /ganuda/vetassist/backend/app/api/v1/endpoints/auth.py
```

---

## Verify

```bash
grep "MessageResponse" /ganuda/vetassist/backend/app/api/v1/endpoints/auth.py
```

Should show: `from app.schemas.auth import MessageResponse`

---

## Success Criteria

The sed command runs without error and grep shows the corrected import path.
