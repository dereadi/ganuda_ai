# Jr Instruction: Fix MVT Scanner UnicodeDecodeError

**Priority**: P0 — Security tooling bug
**Kanban**: #549
**Assigned Jr**: Software Engineer Jr.

## Context

The MVT fleet scanner crashes in `scan_ssh_keys()` when `authorized_keys` contains non-UTF-8 binary data. The fix is to open the file with `errors='replace'`.

## Step 1: Fix encoding in scan_ssh_keys file open

File: `/ganuda/scripts/security/mvt_fleet_scanner.py`

<<<<<<< SEARCH
            with open(auth_keys) as f:
=======
            with open(auth_keys, encoding='utf-8', errors='replace') as f:
>>>>>>> REPLACE

## Verification

After applying, confirm:
1. `encoding='utf-8'` appears in mvt_fleet_scanner.py
2. `errors='replace'` appears in mvt_fleet_scanner.py

## For Seven Generations
