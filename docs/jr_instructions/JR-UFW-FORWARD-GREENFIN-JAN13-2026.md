# JR-UFW-FORWARD-GREENFIN-JAN13-2026: Enable UFW Forwarding for Inter-VLAN Routing

**Created**: 2026-01-13
**Author**: TPM (Flying Squirrel) + Claude
**Priority**: HIGH
**Target Node**: greenfin (192.168.132.224)

---

## Problem

bluefin (192.168.132.222) cannot reach silverfin (192.168.10.10) even though:
- Route exists: `192.168.10.0/24 via 192.168.132.224 dev enp5s0`
- greenfin has `ip_forward=1` enabled
- greenfin CAN ping silverfin directly
- greenfin has VLAN 10 interface `eno1.10` (192.168.10.1) UP

**Root Cause**: UFW is active on greenfin and likely has implicit FORWARD rules that DROP packets even though `DEFAULT_FORWARD_POLICY="ACCEPT"` is set in `/etc/default/ufw`.

---

## Diagnosis (Completed)

```bash
# greenfin can reach silverfin
ping -c 2 192.168.10.10  # SUCCESS

# bluefin cannot reach silverfin via greenfin
ssh bluefin "ping -c 2 192.168.10.10"  # 100% packet loss

# UFW is active
systemctl is-active ufw  # active

# ip_forward is enabled
cat /proc/sys/net/ipv4/ip_forward  # 1

# DEFAULT_FORWARD_POLICY is ACCEPT
grep FORWARD /etc/default/ufw  # DEFAULT_FORWARD_POLICY="ACCEPT"
```

---

## Solution

Run the following commands on greenfin as root:

### Step 1: Check current UFW FORWARD rules

```bash
sudo ufw status verbose
sudo iptables -L FORWARD -n -v --line-numbers
```

### Step 2: Allow forwarding between interfaces

```bash
# Allow forwarding from compute VLAN to DMZ VLAN
sudo ufw route allow in on eno1 out on eno1.10

# Allow forwarding from DMZ VLAN back to compute VLAN (for return traffic)
sudo ufw route allow in on eno1.10 out on eno1
```

### Step 3: Also allow VLAN 20 (Sanctum) forwarding

```bash
# Allow forwarding from compute VLAN to Sanctum VLAN
sudo ufw route allow in on eno1 out on eno1.20

# Allow return traffic from Sanctum VLAN
sudo ufw route allow in on eno1.20 out on eno1
```

### Step 4: Reload UFW

```bash
sudo ufw reload
```

### Step 5: Verify

```bash
# Check new rules
sudo ufw status verbose

# Test from bluefin
ssh bluefin "ping -c 3 192.168.10.10"
```

---

## Alternative: Disable UFW for Testing

If the above doesn't work, temporarily disable UFW to confirm it's the blocker:

```bash
sudo ufw disable
# Test from bluefin
ssh bluefin "ping -c 3 192.168.10.10"
# Re-enable UFW
sudo ufw enable
```

---

## Post-Fix: Archive to Thermal Memory

```bash
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'UFW FORWARD RULES FIXED ON GREENFIN - January 13, 2026

  Problem: bluefin could not reach silverfin (VLAN 10) via greenfin even with ip_forward=1

  Root Cause: UFW was blocking FORWARD chain despite DEFAULT_FORWARD_POLICY=ACCEPT

  Solution: Added ufw route allow rules for inter-VLAN forwarding:
  - eno1 <-> eno1.10 (Compute <-> DMZ)
  - eno1 <-> eno1.20 (Compute <-> Sanctum)

  Nodes now reachable across VLANs via greenfin.

  For Seven Generations.',
  90, 'tpm',
  ARRAY['ufw', 'routing', 'vlan', 'greenfin', 'fix', 'january-2026'],
  'federation'
);"
```

---

## Context

This is needed for:
1. bluefin, redfin to reach silverfin (FreeIPA on VLAN 10) for domain joining
2. All compute nodes to reach goldfin (PII Sanctum on VLAN 20) when needed
3. Proper inter-VLAN routing architecture

---

**For Seven Generations**: Proper network segmentation with controlled routing.
