# Jr Instruction: Fix MVT Scanner Hostname Matching

**Priority**: P0 — Known ports not matching, all services show as false positives
**Kanban**: #549
**Assigned Jr**: Software Engineer Jr.

## Step 1: Fix hostname to match KNOWN_PORTS keys

File: `/ganuda/scripts/security/mvt_fleet_scanner.py`

<<<<<<< SEARCH
HOSTNAME = socket.gethostname().lower()
=======
HOSTNAME = socket.gethostname().lower().split('.')[0]
>>>>>>> REPLACE

## For Seven Generations
