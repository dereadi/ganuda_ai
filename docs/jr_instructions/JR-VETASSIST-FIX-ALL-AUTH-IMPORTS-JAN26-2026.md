# Jr Instruction: Fix All VetAssist get_current_user Imports

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Problem

Multiple endpoint files have wrong import for `get_current_user`:

**Files to fix:**
1. `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`
2. `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py`

**Current (wrong):**
```python
from .auth import get_current_user
```

**Should be:**
```python
from app.core.security import get_current_user
```

---

## Fix All Files

```bash
# Fix dashboard.py
sed -i 's/from .auth import get_current_user/from app.core.security import get_current_user/' /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py

# Fix evidence.py
sed -i 's/from .auth import get_current_user/from app.core.security import get_current_user/' /ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py
```

---

## Verify

```bash
grep -r "from .auth import get_current_user" /ganuda/vetassist/backend/app/api/v1/endpoints/
```

Should return NO results (empty output).

```bash
grep -l "from app.core.security import get_current_user" /ganuda/vetassist/backend/app/api/v1/endpoints/*.py
```

Should show both dashboard.py and evidence.py.
