# JR Instruction: VetAssist Config Fix - PII_TOKEN_SALT

## Metadata
```yaml
task_id: vetassist_config_pii_salt
priority: 1
assigned_to: Code Jr.
target_node: redfin
blocking: true
```

## Problem

VetAssist backend fails to start with error:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
PII_TOKEN_SALT
  Extra inputs are not permitted
```

The `.env` file contains `PII_TOKEN_SALT` but the Settings class in `config.py` doesn't define this field.

## Solution

Add `PII_TOKEN_SALT` to the Settings class in `/ganuda/vetassist/backend/app/core/config.py`.

### Task 1: Add Field to Settings Class

In `/ganuda/vetassist/backend/app/core/config.py`, add after line 32 (ALGORITHM line):

```python
    # PII Protection
    PII_TOKEN_SALT: str = Field(
        default="",
        description="Salt for PII tokenization - set in .env"
    )
```

### Task 2: Restart Service

```bash
sudo systemctl restart vetassist-backend
sudo systemctl status vetassist-backend --no-pager
```

### Task 3: Verify

```bash
curl -s http://localhost:8001/health || curl -s http://localhost:8001/api/v1/health
```

## Root Cause

PII integration added `PII_TOKEN_SALT` to `.env` but didn't update the Settings model. Pydantic's default behavior rejects undefined fields.

---

*Cherokee AI Federation - For the Seven Generations*
