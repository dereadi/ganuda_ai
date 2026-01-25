# Jr Task: Add X-API-Key Header Support to Gateway

**Task ID:** task-xapikey-header-001
**Priority:** P1 (Causing recurring quota errors)
**Node:** redfin
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Problem Statement

The LLM Gateway currently only accepts API keys via:
```
Authorization: Bearer ck-cabcc...
```

But many API clients (including our own scripts) use the common pattern:
```
X-API-Key: ck-cabcc...
```

When `X-API-Key` is used, the gateway falls back to **anonymous** user with only 10 quota, causing:
```json
{"detail": "Insufficient quota for council vote"}
```

This has caused repeated confusion and failed API calls.

---

## Solution

Modify `validate_api_key()` in gateway.py to accept both header formats.

---

## Implementation

### File: `/ganuda/services/llm_gateway/gateway.py`

**Find this function (around line 385):**

```python
async def validate_api_key(authorization: str = Header(None)) -> APIKeyInfo:
    """Validate API key from Authorization header"""
    if authorization is None:
        return APIKeyInfo(key_id="anonymous", user_id="anonymous", quota_remaining=10, rate_limit=10)

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    raw_key = authorization[7:]
```

**Replace with:**

```python
async def validate_api_key(
    authorization: str = Header(None),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> APIKeyInfo:
    """
    Validate API key from Authorization or X-API-Key header.

    Accepts:
      - Authorization: Bearer ck-xxxxx
      - X-API-Key: ck-xxxxx
    """
    raw_key = None

    # Try X-API-Key header first (common pattern)
    if x_api_key is not None:
        raw_key = x_api_key
    # Fall back to Authorization: Bearer
    elif authorization is not None:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format. Use 'Bearer <key>' or X-API-Key header")
        raw_key = authorization[7:]

    # No key provided - anonymous access
    if raw_key is None:
        return APIKeyInfo(key_id="anonymous", user_id="anonymous", quota_remaining=10, rate_limit=10)
```

---

## Testing

After applying the fix, test both header formats:

```bash
# Test with X-API-Key (should work now)
curl -s http://192.168.132.223:8080/v1/models \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Test with Authorization: Bearer (should still work)
curl -s http://192.168.132.223:8080/v1/models \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Test Council vote with X-API-Key
curl -s -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Test vote", "options": ["Yes", "No"]}'

# Should NOT get "Insufficient quota" error
```

---

## Restart Gateway

After applying changes:

```bash
# On redfin
sudo systemctl restart llm-gateway

# Or if running manually:
pkill -f gateway.py
cd /ganuda/services/llm_gateway
source venv/bin/activate
nohup python3 gateway.py >> /var/log/ganuda/gateway.log 2>&1 &
```

---

## Success Criteria

1. ✅ `X-API-Key` header accepted and validated
2. ✅ `Authorization: Bearer` still works
3. ✅ Council votes work with either header format
4. ✅ No more "Insufficient quota" errors when using X-API-Key

---

## KB Article Update

Update `/ganuda/docs/kb/KB_API_AUTHENTICATION.md` to document both header formats.

---

*For Seven Generations - Cherokee AI Federation*
