# Jr Task: VLAN Configuration for Sanctum Network

**Date**: January 5, 2026
**Priority**: HIGH
**Target**: TP-Link TL-SG1428PE (192.168.132.132)
**Prerequisite**: goldfin and silverfin hardware ready

## Background

The Cherokee AI Federation is adding two secure nodes:
- **Silverfin**: FreeIPA identity authority (LDAP/Kerberos, YubiKey auth)
- **Goldfin**: PII Alcove for veteran data (encrypted, Tailscale-only)

These must be network-isolated from the compute cluster (redfin/bluefin/greenfin) at Layer 2.

## VLAN Architecture

| VLAN ID | Name | Subnet | Purpose | Ports |
|---------|------|--------|---------|-------|
| 1 | Compute | 192.168.132.0/24 | redfin, bluefin, greenfin, sasass | 1-12 |
| 10 | Identity | 192.168.10.0/24 | silverfin (FreeIPA) | 13-14 |
| 20 | Sanctum | 192.168.20.0/24 | goldfin (PII) | 15-16 |
| 99 | Management | 192.168.99.0/24 | Switch mgmt, IPMI | 27-28 |

## Task 1: Access Switch Web UI

1. Browse to http://192.168.132.132
2. Login with admin credentials (same as postgres)
3. Navigate to **VLAN > 802.1Q VLAN**

## Task 2: Create VLANs

Create the following VLANs:

### VLAN 10 - Identity
- VLAN ID: 10
- VLAN Name: Identity
- Member Ports: 13, 14 (Untagged)
- Remove ports 13, 14 from VLAN 1

### VLAN 20 - Sanctum
- VLAN ID: 20
- VLAN Name: Sanctum
- Member Ports: 15, 16 (Untagged)
- Remove ports 15, 16 from VLAN 1

### VLAN 99 - Management
- VLAN ID: 99
- VLAN Name: Management
- Member Ports: 27, 28 (Untagged)
- Keep switch management on this VLAN

## Task 3: Configure PVID

Set the Port VLAN ID (PVID) for each port:

| Port | PVID | Description |
|------|------|-------------|
| 1-12 | 1 | Compute VLAN (default) |
| 13-14 | 10 | Identity VLAN (silverfin) |
| 15-16 | 20 | Sanctum VLAN (goldfin) |
| 17-26 | 1 | Available (default) |
| 27-28 | 99 | Management |

Navigate to **VLAN > 802.1Q PVID Setting** and configure.

## Task 4: Inter-VLAN Routing Rules

VLANs are isolated at Layer 2. For controlled communication, configure on the router/firewall:

### Allowed Traffic (goldfin ↔ silverfin only for auth):
```
# Goldfin (192.168.20.x) → Silverfin (192.168.10.x)
ALLOW 192.168.20.0/24 → 192.168.10.0/24 : TCP 389 (LDAP)
ALLOW 192.168.20.0/24 → 192.168.10.0/24 : TCP 636 (LDAPS)
ALLOW 192.168.20.0/24 → 192.168.10.0/24 : TCP 88 (Kerberos)
ALLOW 192.168.20.0/24 → 192.168.10.0/24 : UDP 88 (Kerberos)
ALLOW 192.168.20.0/24 → 192.168.10.0/24 : TCP 464 (Kerberos password)

# Silverfin → Goldfin (deny by default, no need for identity to access PII)
DENY 192.168.10.0/24 → 192.168.20.0/24 : ALL
```

### Compute VLAN Access:
```
# Compute nodes can auth to silverfin
ALLOW 192.168.132.0/24 → 192.168.10.0/24 : TCP 389,636,88 (LDAP/Kerberos)

# Compute nodes CANNOT access goldfin directly
DENY 192.168.132.0/24 → 192.168.20.0/24 : ALL

# Exception: Tailscale overlay (goldfin accessible via Tailscale only)
```

## Task 5: Assign Static IPs (No DHCP - Isolated by Design)

These VLANs have **NO router, NO DHCP, NO internet access**.
This is intentional - true air gap security.

### Network Configuration

#### silverfin (VLAN 10 - Identity)
```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.10.10/24
      # NO gateway - isolated network
```

#### goldfin (VLAN 20 - Sanctum)
```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.20.10/24
      # NO gateway - Tailscale handles external access
```

### Static IP Summary

| Node | VLAN | IP Address | Gateway | Internet Access |
|------|------|------------|---------|-----------------|
| silverfin | 10 | 192.168.10.10/24 | NONE | NO - isolated |
| goldfin | 20 | 192.168.20.10/24 | NONE | Tailscale only |

### Why No Gateway?

- **True isolation**: No Layer 3 routing = no path to internet or compute VLAN
- **Tailscale overlay**: goldfin accessible via Tailscale for authorized users
- **Auth traffic only**: goldfin → silverfin for Kerberos/LDAP (ports 88, 389, 636)

## Task 6: Verify Isolation

After setup, verify from each node:

```bash
# From redfin (compute) - should FAIL
ping 192.168.20.10  # goldfin - should timeout

# From redfin (compute) - should SUCCEED
ping 192.168.10.10  # silverfin - should respond (for auth)

# From goldfin (sanctum) - should SUCCEED
ping 192.168.10.10  # silverfin - should respond (for auth)

# From goldfin (sanctum) - should FAIL
ping 192.168.132.223  # redfin - should timeout (isolated)
```

## Port Assignments Summary

```
TL-SG1428PE Port Layout:
┌─────────────────────────────────────────────────────────────┐
│  1   2   3   4   5   6   7   8   9  10  11  12  │ COMPUTE  │
│  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●  │ VLAN 1   │
├─────────────────────────────────────────────────────────────┤
│ 13  14  │ 15  16  │ 17  18  19  20  21  22  23  │          │
│  ●   ●  │  ●   ●  │  ○   ○   ○   ○   ○   ○   ○  │          │
│ IDENT   │ SANCTUM │ AVAILABLE                   │          │
│ VLAN 10 │ VLAN 20 │                             │          │
├─────────────────────────────────────────────────────────────┤
│ 24  25  26  │ 27  28  │ SFP1  SFP2              │          │
│  ○   ○   ○  │  ●   ●  │  ○     ○                │          │
│ AVAILABLE   │ MGMT 99 │ UPLINK                  │          │
└─────────────────────────────────────────────────────────────┘
● = Assigned   ○ = Available
```

## Current Port Assignments (Pre-VLAN)

| Port | Device | Notes |
|------|--------|-------|
| 1 | redfin | GPU inference |
| 2 | bluefin | Database |
| 3 | greenfin | Daemons |
| 4-5 | sasass/sasass2 | Mac Studios |
| 13 | silverfin | (pending) FreeIPA |
| 15 | goldfin | (pending) PII Alcove |

## Acceptance Criteria

- [ ] VLANs 10, 20, 99 created on switch
- [ ] Ports assigned to correct VLANs
- [ ] PVIDs configured
- [ ] Compute cannot ping Sanctum (192.168.20.x)
- [ ] Goldfin can reach Silverfin for auth
- [ ] Switch management on VLAN 99

## Security Notes

- Goldfin accessible via Tailscale only (no direct LAN access from compute)
- YubiKey required for silverfin admin access
- All goldfin data encrypted at rest (LUKS)
- FreeIPA on silverfin provides central auth for entire Federation

## For Seven Generations
