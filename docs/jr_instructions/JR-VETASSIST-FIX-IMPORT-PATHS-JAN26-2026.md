# Jr Instruction: Fix VetAssist Import Paths

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0 (Blocking startup)
**Category:** Bug Fix

---

## Problem

Wrong import path in `app/api/v1/endpoints/auth.py`:

```python
# WRONG (line 10):
from app.api.v1.schemas.response import MessageResponse

# CORRECT:
from app.schemas.auth import MessageResponse
```

The path `app.api.v1.schemas` doesn't exist. `MessageResponse` is defined in `app/schemas/auth.py:85`.

---

## Fix

Edit `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

Change line 10 from:
```python
from app.api.v1.schemas.response import MessageResponse
```

To:
```python
from app.schemas.auth import MessageResponse
```

---

## Additional Check

After fixing, run this to find any other broken imports:

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -c "from app.main import app; print('SUCCESS')"
```

If more errors appear, fix them the same way - find where the class actually lives and correct the import path.

---

## Success Criteria

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -c "from app.main import app; print('App imports OK')"
```

Output: "App imports OK"
