# Jr Instruction: Update Tailscale ACL Policy for Actual Topology

**Priority**: P0 — Security hardening
**Kanban**: #546
**Assigned Jr**: Infrastructure Jr.

## Context

The Tailscale ACL policy JSON has stale references. `tailscale status` shows the actual mesh topology. The policy references `darrells-macbook-pro` which should be `bmasass`. Also missing: `sasass`, `goldfin`, `iphone172`. Joe's devices should be in quarantine zone.

## Step 1: Update the ACL policy with correct topology

File: `/ganuda/home/dereadi/security_jr/spoke_security_phase1/tailscale_acl_policy.json`

<<<<<<< SEARCH
    "group:quarantine": [],
    "group:limited": [],
    "group:trusted": [
      "redfin@tail0e8cb6.ts.net",
      "bluefin@tail0e8cb6.ts.net",
      "greenfin@tail0e8cb6.ts.net",
      "darrells-macbook-pro@tail0e8cb6.ts.net"
    ]
  },
  "hosts": {
    "redfin": "100.116.27.89",
    "bluefin": "100.112.254.96",
    "greenfin": "100.100.243.116",
    "bmasass": "100.103.27.106"
  },
=======
    "group:quarantine": [
      "joes-ipad@tail0e8cb6.ts.net",
      "joes-mac-studio@tail0e8cb6.ts.net",
      "joes-macbook-air@tail0e8cb6.ts.net"
    ],
    "group:limited": [
      "goldfin@tail0e8cb6.ts.net",
      "iphone172@tail0e8cb6.ts.net"
    ],
    "group:trusted": [
      "redfin@tail0e8cb6.ts.net",
      "bluefin@tail0e8cb6.ts.net",
      "greenfin@tail0e8cb6.ts.net",
      "bmasass@tail0e8cb6.ts.net",
      "sasass@tail0e8cb6.ts.net"
    ]
  },
  "hosts": {
    "redfin": "100.116.27.89",
    "bluefin": "100.112.254.96",
    "greenfin": "100.100.243.116",
    "bmasass": "100.103.27.106",
    "sasass": "100.93.205.120",
    "goldfin": "100.77.238.80",
    "iphone172": "100.79.102.118"
  },
>>>>>>> REPLACE

## Verification

After applying, confirm:
1. `darrells-macbook-pro` no longer appears in the file
2. `bmasass` is in `group:trusted`
3. `sasass` is in `group:trusted`
4. Joe's devices are in `group:quarantine`
5. `goldfin` and `iphone172` are in `group:limited`
6. All 7 hosts are listed with correct IPs

## For Seven Generations
