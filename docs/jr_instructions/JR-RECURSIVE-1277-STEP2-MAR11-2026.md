# [RECURSIVE] sasass2 Triage — Thunderduck Zero (crash loops, credential scrub, thermalize artifacts) - Step 2

**Parent Task**: #1277
**Auto-decomposed**: 2026-03-11T15:49:06.607762
**Original Step Title**: URGENT — Credential Scrub

---

### Step 2: URGENT — Credential Scrub

File: `/Users/Shared/ganuda/lib/xontrib_cherokee.py`

Contains hardcoded DB password `jawaseatlasers2`. This is a Crawdad violation.

1. Replace the hardcoded password with environment variable lookup:
```python
import os
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
```

2. If the file has other hardcoded credentials, scrub them all.
3. Verify the password is NOT in git history. If it is, flag for Chief — may need rotation.
