# Jr Instruction: greenfin as VLAN Router/Firewall with nftables

**Date**: January 9, 2026
**Assigned To**: Infrastructure Jr, Network Jr
**Node**: greenfin (192.168.132.224)
**Priority**: High
**Status**: Ready for execution
**Council Vote**: 87.3% confidence, approved with monitoring/logging requirements

---

## Overview

Configure greenfin (Debian 13) as the inter-VLAN router and firewall using nftables. greenfin will have interfaces on all three VLANs and control traffic flow between them.

**Architecture**:
```
                    INTERNET
                        │
                   [Router 192.168.132.1]
                        │
                   [TP-Link Switch]
                        │
            ┌───────────┼───────────┐
            │     TRUNK PORT 17     │
            │      (tagged)         │
            └───────────┬───────────┘
                        │
                   [GREENFIN]
                   eth0 (untagged) → 192.168.132.224 (Compute)
                   eth0.10 (tagged) → 192.168.10.1 (DMZ Gateway)
                   eth0.20 (tagged) → 192.168.20.1 (Sanctum Gateway)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   [VLAN 1]        [VLAN 10]       [VLAN 20]
   Compute          DMZ            Sanctum
   redfin          silverfin       goldfin
   bluefin         FreeIPA         PII Data
   sasass x2
```

---

## Phase 1: Enable IP Forwarding

```bash
# Enable IP forwarding permanently
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-router.conf
sudo sysctl -p /etc/sysctl.d/99-router.conf

# Verify
cat /proc/sys/net/ipv4/ip_forward
# Should output: 1
```

---

## Phase 2: Install VLAN Support

```bash
# Install vlan package
sudo apt update
sudo apt install -y vlan

# Load 8021q kernel module
sudo modprobe 8021q
echo '8021q' | sudo tee -a /etc/modules
```

---

## Phase 3: Configure VLAN Interfaces

Edit `/etc/network/interfaces` (or create `/etc/network/interfaces.d/vlans`):

```bash
sudo tee /etc/network/interfaces.d/vlans << 'EOF'
# VLAN 10 - DMZ/Identity (silverfin/FreeIPA)
auto eth0.10
iface eth0.10 inet static
    address 192.168.10.1
    netmask 255.255.255.0
    vlan-raw-device eth0

# VLAN 20 - Sanctum (goldfin/PII)
auto eth0.20
iface eth0.20 inet static
    address 192.168.20.1
    netmask 255.255.255.0
    vlan-raw-device eth0
EOF
```

**Note**: Replace `eth0` with actual interface name if different (check with `ip link`).

Bring up the interfaces:

```bash
sudo ifup eth0.10
sudo ifup eth0.20

# Verify
ip addr show eth0.10
ip addr show eth0.20
```

---

## Phase 4: Install and Configure nftables

```bash
# Install nftables (should be default on Debian 13)
sudo apt install -y nftables

# Enable nftables service
sudo systemctl enable nftables
sudo systemctl start nftables
```

---

## Phase 5: Create nftables Firewall Rules

Create `/etc/nftables.conf`:

```bash
sudo tee /etc/nftables.conf << 'EOF'
#!/usr/sbin/nft -f

# Cherokee AI Federation - greenfin Router/Firewall
# Date: January 9, 2026
# Council Vote: 87.3% confidence

flush ruleset

# Define variables for readability
define COMPUTE_NET = 192.168.132.0/24
define DMZ_NET = 192.168.10.0/24
define SANCTUM_NET = 192.168.20.0/24

define GREENFIN_COMPUTE = 192.168.132.224
define GREENFIN_DMZ = 192.168.10.1
define GREENFIN_SANCTUM = 192.168.20.1

define SILVERFIN = 192.168.10.10
define GOLDFIN = 192.168.20.10

# Main filter table
table inet filter {

    # Whitelist for services allowed to access Sanctum
    set sanctum_allowed_ips {
        type ipv4_addr
        elements = { 192.168.10.1, 192.168.10.10 }
        comment "IPs allowed to reach Sanctum (greenfin gateway, silverfin)"
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Allow established/related connections
        ct state established,related accept

        # Allow loopback
        iif lo accept

        # Allow ICMP (ping) for diagnostics
        ip protocol icmp accept

        # Allow SSH from Compute VLAN
        ip saddr $COMPUTE_NET tcp dport 22 accept

        # Allow SSH from DMZ (for management)
        ip saddr $DMZ_NET tcp dport 22 accept

        # Log and drop everything else
        log prefix "[GREENFIN-INPUT-DROP] " flags all
        drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Allow established/related connections
        ct state established,related accept

        # ===== COMPUTE → DMZ: ALLOW =====
        # Nodes can authenticate via FreeIPA
        ip saddr $COMPUTE_NET ip daddr $DMZ_NET accept

        # ===== DMZ → COMPUTE: ALLOW =====
        # FreeIPA needs to respond
        ip saddr $DMZ_NET ip daddr $COMPUTE_NET accept

        # ===== COMPUTE → SANCTUM: BLOCK =====
        # Exception: greenfin for Ansible patching (already handled by input)
        ip saddr $COMPUTE_NET ip daddr $SANCTUM_NET log prefix "[COMPUTE-TO-SANCTUM-BLOCKED] " drop

        # ===== DMZ → SANCTUM: ALLOW (silverfin auth to goldfin) =====
        # Only silverfin can reach goldfin
        ip saddr $SILVERFIN ip daddr $GOLDFIN log prefix "[DMZ-TO-SANCTUM] " accept

        # Block other DMZ → Sanctum traffic
        ip saddr $DMZ_NET ip daddr $SANCTUM_NET log prefix "[DMZ-TO-SANCTUM-BLOCKED] " drop

        # ===== SANCTUM → ANYWHERE: BLOCK (air gap) =====
        # Exception: Can reach greenfin gateway for patching window
        ip saddr $SANCTUM_NET ip daddr $GREENFIN_SANCTUM accept
        ip saddr $SANCTUM_NET log prefix "[SANCTUM-OUTBOUND-BLOCKED] " drop

        # Log and drop everything else
        log prefix "[GREENFIN-FORWARD-DROP] " flags all
        drop
    }

    chain output {
        type filter hook output priority 0; policy accept;

        # greenfin can send anywhere (it's the router)
        accept
    }
}

# NAT table for patching window (optional)
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;

        # Masquerade Sanctum traffic going to internet (patching only)
        # This is disabled by default - enable only during patching window
        # ip saddr $SANCTUM_NET oif eth0 masquerade
    }
}
EOF
```

---

## Phase 6: Apply and Test Rules

```bash
# Check syntax
sudo nft -c -f /etc/nftables.conf

# Apply rules
sudo nft -f /etc/nftables.conf

# Verify rules loaded
sudo nft list ruleset

# Check specific chain
sudo nft list chain inet filter forward
```

---

## Phase 7: Test Connectivity

From greenfin:

```bash
# Test reach to each VLAN
ping -c 2 192.168.132.223  # redfin (Compute)
ping -c 2 192.168.10.10    # silverfin (DMZ) - after VLAN config on switch
ping -c 2 192.168.20.10    # goldfin (Sanctum) - after goldfin setup
```

From redfin (Compute):

```bash
# Should work - Compute → DMZ
ping -c 2 192.168.10.10

# Should FAIL - Compute → Sanctum (blocked)
ping -c 2 192.168.20.10
```

From silverfin (DMZ):

```bash
# Should work - DMZ → Sanctum (silverfin to goldfin)
ping -c 2 192.168.20.10
```

---

## Phase 8: Configure Logging

Ensure logging goes to syslog for Promtail to pick up:

```bash
# Check logs
sudo journalctl -f | grep -E 'GREENFIN|SANCTUM|DMZ'

# Or via dmesg
sudo dmesg -w | grep -E 'GREENFIN|SANCTUM|DMZ'
```

Create rsyslog rule for firewall logs:

```bash
sudo tee /etc/rsyslog.d/50-nftables.conf << 'EOF'
# Log nftables messages to dedicated file
:msg, contains, "GREENFIN" /var/log/ganuda/nftables.log
:msg, contains, "SANCTUM" /var/log/ganuda/nftables.log
:msg, contains, "DMZ" /var/log/ganuda/nftables.log
EOF

# Create log directory
sudo mkdir -p /var/log/ganuda
sudo chown root:adm /var/log/ganuda

# Restart rsyslog
sudo systemctl restart rsyslog
```

---

## Phase 9: Patching Window Script

Create script to temporarily allow Sanctum outbound for patching:

```bash
sudo tee /ganuda/scripts/sanctum-patch-window.sh << 'EOF'
#!/bin/bash
# Enable/disable Sanctum patching window
# Usage: sanctum-patch-window.sh [open|close]

case "$1" in
    open)
        echo "Opening Sanctum patching window..."
        # Add masquerade rule
        nft add rule ip nat postrouting ip saddr 192.168.20.0/24 oif eth0 masquerade
        # Log to thermal memory
        echo "$(date -Iseconds) PATCHING_WINDOW_OPENED by $(whoami)" >> /var/log/ganuda/sanctum-access.log
        echo "Sanctum can now reach internet for apt updates"
        ;;
    close)
        echo "Closing Sanctum patching window..."
        # Remove masquerade rule (flush and reload clean rules)
        nft -f /etc/nftables.conf
        echo "$(date -Iseconds) PATCHING_WINDOW_CLOSED by $(whoami)" >> /var/log/ganuda/sanctum-access.log
        echo "Sanctum is now air-gapped"
        ;;
    status)
        echo "Current NAT rules:"
        nft list chain ip nat postrouting
        ;;
    *)
        echo "Usage: $0 {open|close|status}"
        exit 1
        ;;
esac
EOF

sudo chmod +x /ganuda/scripts/sanctum-patch-window.sh
```

---

## Phase 10: Verify nftables Persistence

```bash
# nftables loads from /etc/nftables.conf on boot via systemd
sudo systemctl status nftables

# Test by rebooting (optional)
# sudo reboot

# After reboot, verify rules
sudo nft list ruleset | head -50
```

---

## Verification Checklist

- [ ] IP forwarding enabled (`cat /proc/sys/net/ipv4/ip_forward` = 1)
- [ ] 8021q module loaded (`lsmod | grep 8021q`)
- [ ] VLAN interfaces up (eth0.10, eth0.20)
- [ ] nftables service enabled and running
- [ ] Rules loaded (`nft list ruleset`)
- [ ] Compute → DMZ: WORKS
- [ ] Compute → Sanctum: BLOCKED
- [ ] DMZ (silverfin) → Sanctum (goldfin): WORKS
- [ ] Sanctum → anywhere: BLOCKED
- [ ] Logging working (`/var/log/ganuda/nftables.log`)
- [ ] Patching window script tested

---

## Council Concerns Addressed

| Concern | Mitigation |
|---------|------------|
| **Crawdad (Security)** | Only silverfin→goldfin allowed in DMZ→Sanctum path, all logged |
| **Eagle Eye (Visibility)** | Comprehensive logging with prefixes, rsyslog to dedicated file |
| **Gecko (Performance)** | greenfin has gigabit NIC, internal traffic only, TPM monitoring for bottlenecks |
| **Raven (Strategy)** | Modular design allows adding dedicated firewall later |
| **Turtle (7GEN)** | Open standards (nftables, 802.1Q), no vendor lock-in |

---

## Rollback Plan

If something goes wrong:

```bash
# Flush all rules (allows all traffic)
sudo nft flush ruleset

# Restore default Debian rules
sudo systemctl restart nftables

# Or completely disable
sudo systemctl stop nftables
sudo systemctl disable nftables
```

---

## Dependencies

This Jr instruction requires:
1. Switch VLAN configuration complete (ports assigned to VLANs)
2. greenfin connected to trunk port (port 17)
3. silverfin moved to VLAN 10 port and IP changed to 192.168.10.10
4. goldfin set up on VLAN 20 with IP 192.168.20.10

---

## Thermal Memory Archive

Once complete:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, source_session, valid_from, memory_type
) VALUES (
    md5('greenfin_nftables_router_deployed_jan9_2026'),
    'GREENFIN NFTABLES ROUTER DEPLOYED - January 9, 2026

VLAN ROUTING:
- eth0: 192.168.132.224 (Compute)
- eth0.10: 192.168.10.1 (DMZ Gateway)
- eth0.20: 192.168.20.1 (Sanctum Gateway)

FIREWALL POLICY:
- Compute → DMZ: ALLOW
- Compute → Sanctum: BLOCK
- DMZ (silverfin) → Sanctum (goldfin): ALLOW
- Sanctum → anywhere: BLOCK (air gap)

LOGGING: /var/log/ganuda/nftables.log
PATCHING: /ganuda/scripts/sanctum-patch-window.sh

Council Vote: 87.3% confidence

For Seven Generations.',
    95.0,
    ARRAY['greenfin', 'nftables', 'router', 'firewall', 'vlan', 'dmz', 'sanctum', 'january-2026'],
    'tpm',
    'greenfin',
    'claude-session-jan9',
    NOW(),
    'cmdb_entry'
);
```

---

For Seven Generations.
