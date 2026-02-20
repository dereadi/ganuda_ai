#!/usr/bin/env python3
"""Generate firewall deployment commands for the Chief to run with sudo.

Kanban #547 — Harden Hub Firewall Rules
Outputs exact commands needed per node. Does NOT execute anything.
Includes pre-flight checks and rollback instructions.

Usage: python3 /ganuda/scripts/security/firewall_deploy_helper.py [node]
  node: redfin, bluefin, or greenfin (default: auto-detect)
"""
import socket
import os
import sys
import datetime

HOSTNAME = socket.gethostname().lower()

NODES = {
    "redfin": {
        "nftables_src": "/ganuda/config/nftables-redfin.conf",
        "open_ports": "SSH(22), HTTP/S(80,443), LLM Gateway(8080), vLLM(8000), SAG(4000), Kanban(3001)",
        "internal_only": "LLM Gateway, vLLM, SAG, Kanban (192.168.132.0/24 only)",
    },
    "bluefin": {
        "nftables_src": "/ganuda/config/nftables-bluefin.conf",
        "open_ports": "SSH(22), PostgreSQL(5432), Grafana(3000), VLM(8090,8092)",
        "internal_only": "ALL ports (192.168.132.0/24 only, no public exposure)",
    },
    "greenfin": {
        "nftables_src": "/ganuda/config/nftables-greenfin.conf",
        "open_ports": "SSH(22), Embedding(8003), Promtail(9080), Squid(3128), VLAN routing",
        "internal_only": "ALL ports, plus inter-VLAN forwarding",
    },
}


def generate(node_name):
    """Generate deployment commands for a node."""
    config = NODES.get(node_name)
    if not config:
        print(f"Unknown node: {node_name}")
        print(f"Available: {', '.join(NODES.keys())}")
        return 1

    src = config["nftables_src"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    print(f"FIREWALL DEPLOYMENT — {node_name.upper()}")
    print(f"Generated: {datetime.datetime.now().isoformat()}")
    print(f"Open ports: {config['open_ports']}")
    print(f"Internal only: {config['internal_only']}")
    print("=" * 60)

    # Check config file exists
    if not os.path.exists(src):
        print(f"\nWARNING: Config file does not exist: {src}")
        if node_name == "greenfin":
            print("  Greenfin config needs to be created by TPM (router rules are complex)")
            print("  Reference: /ganuda/docs/jr_instructions/JR-GREENFIN-NFTABLES-ROUTER-JAN9-2026.md")
        print("\nCannot generate deployment commands without config file.")
        return 1

    print(f"""
IMPORTANT: Keep a SECOND SSH session open to {node_name} before starting.
If firewall rules lock you out, use the second session to roll back.

# ============================================
# PHASE 1: Pre-flight (run these first)
# ============================================

# Backup current rules
sudo nft list ruleset > /ganuda/backups/nftables-{node_name}-{timestamp}.bak

# Validate config syntax (dry-run, does NOT apply)
sudo nft -c -f {src}

# If validation fails, STOP and fix the config file first.

# ============================================
# PHASE 2: Apply firewall rules
# ============================================

# Flush existing rules and load new ones
sudo nft flush ruleset
sudo nft -f {src}

# IMMEDIATELY verify you still have SSH access
# If locked out, use second session:
#   sudo nft flush ruleset

# Verify rules loaded
sudo nft list ruleset | head -40

# Check INPUT policy is DROP
sudo nft list chain inet filter input 2>/dev/null | head -5

# ============================================
# PHASE 3: Persist for reboot survival
# ============================================

# Copy to persistence location
sudo cp {src} /etc/nftables.conf

# Enable nftables service at boot
sudo systemctl enable nftables

# Verify persistence
ls -la /etc/nftables.conf

# ============================================
# PHASE 4: Deploy fail2ban (optional but recommended)
# ============================================

# Install fail2ban
sudo apt install -y fail2ban

# Deploy Cherokee config
sudo cp /ganuda/config/fail2ban-jail.local /etc/fail2ban/jail.local

# Deploy custom filters (if Caddy/PostgreSQL on this node)
test -f /ganuda/config/fail2ban-filter-caddy-auth.conf && sudo cp /ganuda/config/fail2ban-filter-caddy-auth.conf /etc/fail2ban/filter.d/caddy-auth.conf
test -f /ganuda/config/fail2ban-filter-postgresql.conf && sudo cp /ganuda/config/fail2ban-filter-postgresql.conf /etc/fail2ban/filter.d/postgresql.conf

# Enable and start fail2ban
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

# Verify fail2ban jails
sudo fail2ban-client status

# ============================================
# PHASE 5: Post-deployment verification
# ============================================

# Run the audit script to verify everything is correct
python3 /ganuda/scripts/security/firewall_audit.py

# ============================================
# ROLLBACK (if something goes wrong)
# ============================================

# Option A: Flush all rules (emergency, opens everything)
# sudo nft flush ruleset

# Option B: Restore from backup
# sudo nft flush ruleset
# sudo nft -f /ganuda/backups/nftables-{node_name}-{timestamp}.bak
""")

    return 0


if __name__ == "__main__":
    node = sys.argv[1] if len(sys.argv) > 1 else HOSTNAME
    sys.exit(generate(node))