# JR Instruction: Research Endpoint Security Addendum

**JR ID:** JR-RESEARCH-SECURITY-ADDENDUM-JAN28-2026
**Priority:** P1 (Security)
**Assigned To:** Security Jr.
**Council Concern:** Crawdad [SECURITY CONCERN]
**Related:** JR-DEPLOY-RESEARCH-WORKER-JAN28-2026

---

## Security Concerns Identified

### 1. Anonymous Access Allowed

**Issue:** `validate_api_key()` allows anonymous access with 100k quota (line 488):
```python
if raw_key is None:
    return APIKeyInfo(key_id="anonymous", user_id="anonymous", quota_remaining=100000, rate_limit=60)
```

**Risk:** Research queries can be submitted without authentication.

**Mitigation:** Add explicit API key requirement for research endpoints.

### 2. Missing Audit Logging

**Issue:** Research endpoints (`/v1/research/async`, `/v1/research/status`) don't call `log_audit()`.

**Risk:** Research queries not tracked in `api_audit_log`.

**Mitigation:** Add audit logging to research endpoints.

### 3. Job ID Path Traversal

**Issue:** `job_id` parameter used directly in file paths without validation.

**Risk:** Potential path traversal if job_id contains `../`.

**Mitigation:** Validate job_id format (alphanumeric + hyphen only).

---

## Required Code Changes

### File: `/ganuda/services/llm_gateway/gateway.py`

#### Change 1: Require API key for research endpoints

Add decorator or check to reject anonymous:

```python
@app.post("/v1/research/async")
async def queue_research_job(request: ResearchQuery, api_key: APIKeyInfo = Depends(validate_api_key)):
    # Reject anonymous access for research
    if api_key.key_id == "anonymous":
        raise HTTPException(status_code=401, detail="API key required for research")
    ...
```

#### Change 2: Add audit logging

```python
@app.post("/v1/research/async")
async def queue_research_job(request: ResearchQuery, req: Request, api_key: APIKeyInfo = Depends(validate_api_key)):
    start = time.time()
    client_ip = req.client.host if req.client else None

    # ... existing code ...

    elapsed_ms = int((time.time() - start) * 1000)
    log_audit(api_key.key_id[:16], "/v1/research/async", "POST", 200, elapsed_ms, 0, client_ip)
```

#### Change 3: Validate job_id format

```python
import re

def validate_job_id(job_id: str) -> bool:
    """Validate job_id is safe (alphanumeric + hyphen only)"""
    return bool(re.match(r'^research-[a-f0-9]{12}$', job_id))

@app.get("/v1/research/status/{job_id}")
async def get_research_status(job_id: str, api_key: APIKeyInfo = Depends(validate_api_key)):
    if not validate_job_id(job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    ...
```

### File: `/ganuda/services/research_worker.py`

#### Change 4: Sanitize output file path

```python
def process_job(job_id, query, max_steps, output_file, callback_type, callback_target):
    # Validate output_file is within expected directory
    if not output_file.startswith("/ganuda/research/completed/"):
        fail_job(job_id, "Invalid output path")
        return
    ...
```

---

## Validation

After applying changes:

1. Test anonymous access rejected:
```bash
curl -X POST http://localhost:8080/v1/research/async \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
# Should return 401
```

2. Test path traversal blocked:
```bash
curl http://localhost:8080/v1/research/status/../../../etc/passwd \
  -H "X-API-Key: ck-..."
# Should return 400 Invalid job_id format
```

3. Verify audit log entries:
```sql
SELECT * FROM api_audit_log WHERE endpoint LIKE '/v1/research%' ORDER BY timestamp DESC LIMIT 5;
```

---

## Deployment Order

1. Apply security patches to gateway.py
2. Apply sanitization to research_worker.py
3. Restart llm-gateway
4. Deploy research-worker.service
5. Test security controls

---

FOR SEVEN GENERATIONS
