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
    "greenfin": {"ip": "100.100.243.116", "zone": "trusted", "role": "Monitoring/Daemons"},
    "bmasass": {"ip": "100.103.27.106", "zone": "trusted", "role": "War Chief Mac (M4 Max)"},
    "sasass": {"ip": "100.93.205.120", "zone": "trusted", "role": "Mac Studio Edge Dev"},
    "goldfin": {"ip": "100.77.238.80", "zone": "limited", "role": "Linux Edge (offline)"},
    "iphone172": {"ip": "100.79.102.118", "zone": "limited", "role": "Mobile"},
    "joes-ipad": {"ip": "100.72.234.34", "zone": "quarantine", "role": "Joe iPad"},
    "joes-mac-studio": {"ip": "100.106.9.80", "zone": "quarantine", "role": "Joe Mac Studio"},
    "joes-macbook-air": {"ip": "100.107.145.52", "zone": "quarantine", "role": "Joe MacBook Air"},
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