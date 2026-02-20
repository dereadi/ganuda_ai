# Jr Instruction: Update Tailscale Audit Script Expected Nodes

**Priority**: P1 — Fix stale inventory
**Kanban**: #546
**Assigned Jr**: Infrastructure Jr.

## Step 1: Replace EXPECTED_NODES with actual federation topology

File: `/ganuda/scripts/security/tailscale_acl_audit.py`

<<<<<<< SEARCH
EXPECTED_NODES = {
    "redfin": {"ip": "100.116.27.89", "zone": "trusted", "role": "Hub/GPU Inference"},
    "bluefin": {"ip": "100.112.254.96", "zone": "trusted", "role": "Database"},
    "greenfin": {"ip": "100.100.243.116", "zone": "trusted", "role": "Router/Daemons"},
    "darrells-macbook-pro": {"ip": "100.103.27.106", "zone": "trusted", "role": "War Chief Mac (bmasass)"},
}
=======
EXPECTED_NODES = {
    "redfin": {"ip": "100.116.27.89", "zone": "trusted", "role": "Hub/GPU Inference"},
    "bluefin": {"ip": "100.112.254.96", "zone": "trusted", "role": "Database"},
    "greenfin": {"ip": "100.100.243.116", "zone": "trusted", "role": "Monitoring/Daemons"},
    "bmasass": {"ip": "100.103.27.106", "zone": "trusted", "role": "War Chief Mac (M4 Max)"},
    "sasass": {"ip": "100.93.205.120", "zone": "trusted", "role": "Mac Studio Edge Dev"},
    "goldfin": {"ip": "100.77.238.80", "zone": "limited", "role": "Linux Edge (offline)"},
    "iphone172": {"ip": "100.79.102.118", "zone": "limited", "role": "Mobile"},
    "joes-ipad": {"ip": "100.72.234.34", "zone": "quarantine", "role": "Joe iPad"},
    "joes-mac-studio": {"ip": "100.106.9.80", "zone": "quarantine", "role": "Joe Mac Studio"},
    "joes-macbook-air": {"ip": "100.107.145.52", "zone": "quarantine", "role": "Joe MacBook Air"},
}
>>>>>>> REPLACE

## For Seven Generations
