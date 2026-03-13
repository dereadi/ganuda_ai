# Owl Pass Credential Audit Scanner — Fixed

**Task ID:** JR-OWL-PASS-CREDENTIAL-AUDIT-FIXED
**Priority:** P2
**Story Points:** 2
**Council Owner:** Crawdad
**DC References:** DC-10 (reflex layer security)

Deploy a fixed credential audit scanner. The previous versions (#1256, #1148) failed due to:
1. Instruction format incompatible with Jr parser (used SEARCH/REPLACE instead of Create pattern)
2. Bug in file matching: `file.endswith('*.py')` never matches (should be `.py`)
3. Script walked all of `/ganuda/` (500GB+) instead of targeting code directories

The fixed script is already at `/ganuda/scripts/credential_audit_owlpass.py`. This instruction validates it runs correctly.

### Step 1: Verify the credential audit script runs

```bash
cd /ganuda && python3 /ganuda/scripts/credential_audit_owlpass.py
```

## Verification

```bash
cd /ganuda && python3 -c "
from scripts.credential_audit_owlpass import find_files_to_scan
files = find_files_to_scan('/ganuda/')
assert len(files) > 100, f'Expected 100+ files, got {len(files)}'
print(f'PASS: Found {len(files)} files to scan')
"
```

## Acceptance Criteria
- Script scans code directories (daemons, lib, scripts, services, etc.) — not models/data/home
- Findings are redacted — actual credential values never printed
- Script completes in under 30 seconds
- Exit code 0 on success
