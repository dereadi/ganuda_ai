# Jr Instruction: SAG API Key Auth Guard

**Task ID:** SAG-AUTH
**Kanban:** #1851
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Create API key authentication middleware for SAG with rate limiting.

---

## Step 1: Create the auth guard module

Create `/ganuda/services/sag/auth_guard.py`

```python
"""SAG API Key Auth Guard: API key validation + rate limiting middleware."""

import os
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

VALID_KEYS = set(os.environ.get("SAG_API_KEYS", "").split(","))
RATE_LIMIT = 100
RATE_WINDOW = 60

_request_log = defaultdict(list)

def _check_rate_limit(api_key):
    now = time.time()
    window_start = now - RATE_WINDOW
    _request_log[api_key] = [t for t in _request_log[api_key] if t > window_start]
    if len(_request_log[api_key]) >= RATE_LIMIT:
        return False
    _request_log[api_key].append(now)
    return True

class SAGAuthGuard(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)
        api_key = request.headers.get("X-API-Key", "")
        if not api_key or api_key not in VALID_KEYS:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"}
            )
        if not _check_rate_limit(api_key):
            return JSONResponse(
                status_code=403,
                content={"error": "Rate limit exceeded", "limit": f"{RATE_LIMIT} req/{RATE_WINDOW}s"}
            )
        return await call_next(request)
```

---

## Verification

```text
python3 -c "
import os; os.environ['SAG_API_KEYS'] = 'test-key-123,test-key-456'
from auth_guard import SAGAuthGuard, VALID_KEYS
print(f'Valid keys loaded: {len(VALID_KEYS)}')
print('Auth guard ready for FastAPI middleware registration')
"
```
