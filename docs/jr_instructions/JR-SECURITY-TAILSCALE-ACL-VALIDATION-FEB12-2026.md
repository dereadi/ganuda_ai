# Jr Instruction: Tailscale ACL Spoke Quarantine — Validation Tooling

**Kanban**: #546 (Tailscale ACL Spoke Quarantine)
**Sacred Fire Priority**: 95
**Story Points**: 5
**River Cycle**: RC-2026-02A
**Long Man Step**: BUILD

## Context

Phase 1 security work (Nov 2025) created a three-zone Tailscale ACL policy at `/ganuda/home/dereadi/security_jr/spoke_security_phase1/tailscale_acl_policy.json`. The architecture:

- **QUARANTINE (Red)**: New/suspicious spokes → hub-only access (redfin)
- **LIMITED (Yellow)**: Probationary spokes → hub + SSH/HTTPS to bluefin, greenfin
- **TRUSTED (Green)**: Verified nodes → full mesh access

The policy was marked "READY FOR APPROVAL" but was **NEVER DEPLOYED** to Tailscale. The federation has changed since November (bmasass joined, new services, port shifts). We need audit and validation scripts before the Chief deploys the ACLs.

Current Tailscale node inventory:
- redfin: 100.116.27.89 (Hub/GPU)
- bluefin: 100.112.254.96 (Database)
- greenfin: 100.100.243.116 (Router)
- bmasass: 100.103.27.106 (War Chief Mac, Tailscale name: darrells-macbook-pro)

## Steps

### Step 1: Create Tailscale ACL Audit Script

Create `/ganuda/scripts/security/tailscale_acl_audit.py`

```python
#!/usr/bin/env python3
"""Audit Tailscale mesh state against ACL policy.

Kanban #546 — Tailscale ACL Spoke Quarantine
Compares live Tailscale mesh against the ACL policy JSON.
Run on any federation node with Tailscale installed.
"""
import json
import subprocess
import sys
import os

# Expected federation nodes with Tailscale IPs
EXPECTED_NODES = {
    "redfin": {"ip": "100.116.27.89", "zone": "trusted", "role": "Hub/GPU Inference"},
    "bluefin": {"ip": "100.112.254.96", "zone": "trusted", "role": "Database"},
    "greenfin": {"ip": "100.100.243.116", "zone": "trusted", "role": "Router/Daemons"},
    "darrells-macbook-pro": {"ip": "100.103.27.106", "zone": "trusted", "role": "War Chief Mac (bmasass)"},
}

ACL_POLICY_PATH = "/ganuda/home/dereadi/security_jr/spoke_security_phase1/tailscale_acl_policy.json"


def get_tailscale_status():
    """Get current Tailscale mesh status."""
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"  tailscale status returned code {result.returncode}: {result.stderr.strip()}")
    except FileNotFoundError:
        print("  ERROR: tailscale binary not found — is Tailscale installed?")
    except Exception as e:
        print(f"  ERROR: Cannot get Tailscale status: {e}")
    return None


def load_acl_policy():
    """Load the ACL policy JSON."""
    if not os.path.exists(ACL_POLICY_PATH):
        print(f"  ERROR: ACL policy not found at {ACL_POLICY_PATH}")
        return None
    try:
        with open(ACL_POLICY_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"  ERROR: Cannot parse ACL policy: {e}")
    return None


def audit():
    """Run the full Tailscale mesh audit."""
    print("=" * 60)
    print("TAILSCALE ACL AUDIT — Cherokee AI Federation")
    print("=" * 60)

    issues = []

    # 1. Tailscale daemon status
    print("\n--- Tailscale Daemon ---")
    status = get_tailscale_status()
    if not status:
        print("  FAILED: Cannot reach Tailscale daemon")
        issues.append("Tailscale daemon unreachable")
        print(f"\nISSUES: {len(issues)}")
        return 1

    self_node = status.get("Self", {})
    peers = status.get("Peer", {})
    self_name = self_node.get("HostName", "unknown")
    self_ips = self_node.get("TailscaleIPs", ["?"])
    print(f"  Self: {self_name} ({self_ips[0] if self_ips else '?'})")
    print(f"  Peers: {len(peers)}")
    print(f"  Backend: {status.get('BackendState', 'unknown')}")

    # 2. Node inventory check
    print("\n--- Node Inventory ---")
    found_nodes = {}
    found_nodes[self_name.lower()] = {
        "online": True,
        "ip": self_ips[0] if self_ips else "?",
    }
    for peer_id, peer in peers.items():
        hostname = peer.get("HostName", "").lower()
        online = peer.get("Online", False)
        ips = peer.get("TailscaleIPs", [])
        ip = ips[0] if ips else "no-ip"
        found_nodes[hostname] = {"online": online, "ip": ip}
        status_str = "ONLINE" if online else "OFFLINE"
        print(f"  {hostname:25s} {status_str:8s} {ip}")

    # Check expected vs found
    for name, info in EXPECTED_NODES.items():
        name_lower = name.lower()
        if name_lower not in found_nodes:
            print(f"  MISSING: {name} (expected {info['ip']}, role: {info['role']})")
            issues.append(f"Missing node: {name}")
        elif not found_nodes[name_lower]["online"]:
            print(f"  OFFLINE: {name}")
        else:
            # Verify IP matches
            actual_ip = found_nodes[name_lower]["ip"]
            if actual_ip != info["ip"]:
                print(f"  IP DRIFT: {name} expected {info['ip']} got {actual_ip}")
                issues.append(f"IP drift on {name}: {info['ip']} -> {actual_ip}")

    extra = set(found_nodes.keys()) - {n.lower() for n in EXPECTED_NODES} - {""}
    if extra:
        for e in extra:
            print(f"  EXTRA NODE: {e} (not in expected inventory)")
            issues.append(f"Unknown node in mesh: {e}")

    # 3. ACL policy validation
    print("\n--- ACL Policy ---")
    policy = load_acl_policy()
    if not policy:
        issues.append("ACL policy file not found or invalid")
    else:
        groups = policy.get("groups", {})
        acls = policy.get("acls", [])
        hosts = policy.get("hosts", {})

        q_count = len(groups.get("group:quarantine", []))
        l_count = len(groups.get("group:limited", []))
        t_count = len(groups.get("group:trusted", []))

        print(f"  Zones: {len(acls)} ACL rules")
        print(f"  Quarantine zone: {q_count} members")
        print(f"  Limited zone:    {l_count} members")
        print(f"  Trusted zone:    {t_count} members")
        print(f"  Hosts defined:   {len(hosts)}")

        # Verify all expected nodes are in a zone
        trusted = groups.get("group:trusted", [])
        trusted_hostnames = [t.split("@")[0].lower() for t in trusted]
        for name in EXPECTED_NODES:
            name_lower = name.lower()
            if name_lower not in trusted_hostnames and name_lower.replace("-", "") not in "".join(trusted_hostnames):
                print(f"  WARNING: {name} not found in any zone group")
                issues.append(f"{name} not in any ACL zone")

        # Verify hosts section has all nodes
        for name, info in EXPECTED_NODES.items():
            # Check by IP
            policy_hosts_ips = list(hosts.values())
            if info["ip"] not in policy_hosts_ips:
                host_key = name.lower().replace("darrells-macbook-pro", "bmasass")
                if host_key not in hosts:
                    print(f"  WARNING: {name} ({info['ip']}) not in hosts section")
                    issues.append(f"{name} missing from ACL hosts")

    # 4. Summary
    print("\n--- Summary ---")
    if issues:
        print(f"ISSUES FOUND: {len(issues)}")
        for i in issues:
            print(f"  - {i}")
        print("\nACTION: Update ACL policy before deployment")
        return 1
    else:
        print("ALL CHECKS PASSED — ACL policy is current")
        print("NEXT: Chief deploys ACLs via Tailscale admin console")
        return 0


if __name__ == "__main__":
    sys.exit(audit())
```

### Step 2: Create Zone Isolation Test Script

Create `/ganuda/scripts/security/tailscale_zone_test.py`

```python
#!/usr/bin/env python3
"""Test Tailscale zone isolation — verify expected connectivity per zone.

Kanban #546 — Tailscale ACL Spoke Quarantine
Run from each node AFTER ACL deployment to verify zone-based access controls.

Zone expectations:
  QUARANTINE: Can reach hub (redfin) only
  LIMITED:    Can reach hub + SSH/HTTPS on bluefin, greenfin
  TRUSTED:    Full mesh access to all nodes and ports
"""
import socket
import sys

# Federation services to test connectivity
# (description, host_ip, port)
CONNECTIVITY_TESTS = [
    # Hub (redfin) - all zones should reach
    ("redfin SSH", "100.116.27.89", 22),
    ("redfin LLM Gateway", "100.116.27.89", 8080),
    ("redfin vLLM", "100.116.27.89", 8000),
    ("redfin SAG UI", "100.116.27.89", 4000),
    ("redfin Kanban", "100.116.27.89", 3001),
    # Bluefin - limited+ should reach SSH/HTTPS, trusted reaches all
    ("bluefin SSH", "100.112.254.96", 22),
    ("bluefin HTTPS", "100.112.254.96", 443),
    ("bluefin PostgreSQL", "100.112.254.96", 5432),
    ("bluefin Grafana", "100.112.254.96", 3000),
    # Greenfin - limited+ should reach SSH/HTTPS, trusted reaches all
    ("greenfin SSH", "100.100.243.116", 22),
    ("greenfin HTTPS", "100.100.243.116", 443),
    ("greenfin Embedding", "100.100.243.116", 8003),
    ("greenfin Promtail", "100.100.243.116", 9080),
]

# Expected access per zone
ZONE_EXPECTATIONS = {
    "quarantine": {
        "allowed": ["redfin SSH", "redfin LLM Gateway", "redfin vLLM", "redfin SAG UI", "redfin Kanban"],
        "blocked": ["bluefin SSH", "bluefin HTTPS", "bluefin PostgreSQL", "bluefin Grafana",
                     "greenfin SSH", "greenfin HTTPS", "greenfin Embedding", "greenfin Promtail"],
    },
    "limited": {
        "allowed": ["redfin SSH", "redfin LLM Gateway", "redfin vLLM", "redfin SAG UI", "redfin Kanban",
                     "bluefin SSH", "bluefin HTTPS", "greenfin SSH", "greenfin HTTPS"],
        "blocked": ["bluefin PostgreSQL", "bluefin Grafana", "greenfin Embedding", "greenfin Promtail"],
    },
    "trusted": {
        "allowed": [t[0] for t in CONNECTIVITY_TESTS],
        "blocked": [],
    },
}


def test_port(host, port, timeout=3):
    """Test TCP connectivity to host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def run_tests():
    """Run all connectivity tests and assess zone placement."""
    print("=" * 70)
    print("TAILSCALE ZONE ISOLATION TEST — Cherokee AI Federation")
    print("=" * 70)
    print("\nTesting connectivity from THIS node to federation services...")
    print("Run AFTER ACL deployment to verify zone isolation.\n")

    print(f"{'Service':25s} {'Host':20s} {'Port':6s} {'Result':10s}")
    print("-" * 65)

    results = {}
    for desc, host, port in CONNECTIVITY_TESTS:
        reachable = test_port(host, port)
        status = "OPEN" if reachable else "BLOCKED"
        results[desc] = reachable
        print(f"{desc:25s} {host:20s} {port:<6d} {status:10s}")

    # Assess which zone this node appears to be in
    print("\n--- Zone Assessment ---")
    open_services = [name for name, reachable in results.items() if reachable]
    blocked_services = [name for name, reachable in results.items() if not reachable]

    for zone_name, expectations in ZONE_EXPECTATIONS.items():
        matches = True
        violations = []
        for svc in expectations["allowed"]:
            if svc not in open_services:
                matches = False
                violations.append(f"{svc} should be OPEN but is BLOCKED")
        for svc in expectations["blocked"]:
            if svc in open_services:
                matches = False
                violations.append(f"{svc} should be BLOCKED but is OPEN")

        if matches:
            print(f"  This node matches: {zone_name.upper()} zone")
            break
        else:
            print(f"  Not {zone_name}: {len(violations)} violations")
            for v in violations[:3]:
                print(f"    - {v}")
    else:
        print("  WARNING: Node does not match any expected zone pattern")
        print("  ACLs may not be applied or may have unexpected rules")

    print(f"\n  Total reachable: {len(open_services)}/{len(results)} services")

    # If everything is open, ACLs are likely not applied
    if len(open_services) == len(results):
        print("\n  NOTE: All services reachable — ACLs may not be applied yet")
        print("  This is expected BEFORE deployment, concerning AFTER")

    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
```

## Verification

After applying, run the audit from any federation node:

```text
python3 /ganuda/scripts/security/tailscale_acl_audit.py
```

After Chief deploys ACLs, test zone isolation from each node:

```text
python3 /ganuda/scripts/security/tailscale_zone_test.py
```

## What This Does NOT Cover

- Actual ACL deployment to Tailscale (requires Chief + admin console access)
- GitOps ACL management via `tailscale/gitops-acl-action` (future enhancement)
- Automated ACL rotation or temporal access grants
- silverfin/goldfin/sasass/sasass2 Tailscale enrollment (separate tasks)
