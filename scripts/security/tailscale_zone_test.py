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
        "blocked": ["bluefin PostgreSQL", "greenfin Embedding", "greenfin Promtail"],
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