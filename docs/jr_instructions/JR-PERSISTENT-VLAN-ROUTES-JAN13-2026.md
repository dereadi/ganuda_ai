# JR-PERSISTENT-VLAN-ROUTES-JAN13-2026: Make Inter-VLAN Routes Persistent

**Created**: 2026-01-13
**Author**: TPM (Flying Squirrel) + Claude
**Priority**: HIGH
**Target Nodes**: bluefin, redfin, silverfin, greenfin

---

## Background

Inter-VLAN routing through greenfin is now working, but the routes are not persistent across reboots. This Jr instruction documents how to make them permanent.

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         greenfin (Router)                          │
│                        192.168.132.224                             │
│                                                                     │
│  eno1 (VLAN 1)         eno1.10 (VLAN 10)        eno1.20 (VLAN 20) │
│  192.168.132.224       192.168.10.1              192.168.20.1      │
└────────┬──────────────────────┬─────────────────────────┬──────────┘
         │                      │                         │
    Compute VLAN            DMZ VLAN               Sanctum VLAN
    192.168.132.0/24        192.168.10.0/24        192.168.20.0/24
         │                      │                         │
    ┌────┴────┐            ┌────┴────┐              ┌─────┴─────┐
    │ bluefin │            │silverfin│              │  goldfin  │
    │ redfin  │            │(FreeIPA)│              │   (PII)   │
    │ sasass* │            │         │              │           │
    └─────────┘            └─────────┘              └───────────┘
```

---

## Node-by-Node Instructions

### 1. greenfin (Router) - Make rp_filter=0 Persistent

```bash
# Create sysctl config
sudo tee /etc/sysctl.d/99-vlan-routing.conf << 'EOF'
# Disable reverse path filtering for inter-VLAN routing
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.eno1.rp_filter = 0
net.ipv4.conf.eno1/10.rp_filter = 0
net.ipv4.conf.eno1/20.rp_filter = 0

# Ensure IP forwarding is enabled
net.ipv4.ip_forward = 1
EOF

# Apply immediately
sudo sysctl --system

# Verify
cat /proc/sys/net/ipv4/conf/all/rp_filter
```

**Note**: For sysctl files, dots in interface names are represented as `/` (eno1.10 → eno1/10).

---

### 2. bluefin (Ubuntu) - Persistent Route via Netplan

```bash
# Edit netplan config
sudo nano /etc/netplan/01-netcfg.yaml

# Add routes section under the interface (example structure):
```

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      addresses:
        - 192.168.132.222/24
      routes:
        - to: default
          via: 192.168.132.1
        - to: 192.168.10.0/24
          via: 192.168.132.224
        - to: 192.168.20.0/24
          via: 192.168.132.224
      nameservers:
        addresses:
          - 192.168.132.1
```

```bash
# Apply
sudo netplan apply

# Verify
ip route | grep "192.168.10\|192.168.20"
```

---

### 3. redfin (Ubuntu) - Persistent Route via Netplan

```bash
# First, find the interface name
ip addr | grep -E "^[0-9].*state UP"

# Edit netplan config
sudo nano /etc/netplan/01-netcfg.yaml

# Add routes section (same as bluefin, adjust interface name):
```

```yaml
network:
  version: 2
  ethernets:
    <interface_name>:
      addresses:
        - 192.168.132.223/24
      routes:
        - to: default
          via: 192.168.132.1
        - to: 192.168.10.0/24
          via: 192.168.132.224
        - to: 192.168.20.0/24
          via: 192.168.132.224
      nameservers:
        addresses:
          - 192.168.132.1
```

```bash
# Apply
sudo netplan apply
```

---

### 4. silverfin (Rocky Linux) - Persistent Route

```bash
# Create route file for eno1
sudo tee /etc/sysconfig/network-scripts/route-eno1 << 'EOF'
192.168.132.0/24 via 192.168.10.1 dev eno1
EOF

# Restart networking
sudo nmcli connection reload
sudo nmcli connection down eno1 && sudo nmcli connection up eno1

# Verify
ip route | grep 192.168.132
```

**Optional**: Disable WiFi on silverfin (identity server shouldn't need it):

```bash
sudo nmcli radio wifi off
# Or permanently:
sudo nmcli connection delete <wifi_connection_name>
```

---

### 5. goldfin (Rocky Linux on VLAN 20) - Persistent Route

```bash
# Create route file for the VLAN 20 interface
sudo tee /etc/sysconfig/network-scripts/route-<interface> << 'EOF'
192.168.132.0/24 via 192.168.20.1 dev <interface>
EOF

# Restart networking
sudo nmcli connection reload
sudo nmcli connection down <interface> && sudo nmcli connection up <interface>
```

---

## Verification After All Changes

From any compute node (bluefin, redfin):

```bash
# Test VLAN 10 (DMZ - silverfin/FreeIPA)
ping -c 2 192.168.10.10

# Test VLAN 20 (Sanctum - goldfin)
ping -c 2 192.168.20.10

# Verify routes are persistent
ip route | grep -E "192.168.10|192.168.20"
```

---

## Reboot Test

After making changes persistent, reboot each node and verify routes survive:

```bash
sudo reboot

# After reboot:
ip route | grep -E "192.168.10|192.168.20"
ping -c 1 192.168.10.10
```

---

## Archive to Thermal Memory

After completing all nodes:

```bash
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'PERSISTENT VLAN ROUTES CONFIGURED - January 13, 2026

  All nodes configured with persistent inter-VLAN routes:
  - greenfin: sysctl rp_filter=0 in /etc/sysctl.d/99-vlan-routing.conf
  - bluefin: netplan routes to 192.168.10.0/24 and 192.168.20.0/24
  - redfin: netplan routes to 192.168.10.0/24 and 192.168.20.0/24
  - silverfin: route-eno1 file for 192.168.132.0/24
  - goldfin: route file for 192.168.132.0/24

  Inter-VLAN routing survives reboots.

  For Seven Generations.',
  90, 'tpm',
  ARRAY['routing', 'persistent', 'netplan', 'sysctl', 'january-2026'],
  'federation'
);"
```

---

**For Seven Generations**: Persistent routing enables stable identity federation.
