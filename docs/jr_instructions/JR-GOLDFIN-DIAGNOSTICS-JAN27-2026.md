# JR Instruction: Goldfin Node Diagnostics and Recovery

**JR ID:** JR-GOLDFIN-DIAGNOSTICS
**Priority:** P0 (Blocking PII Migration)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Infrastructure Jr.
**Effort:** Small (1-2 hours hands-on)

---

## Problem Statement

Goldfin node is not responding to SSH on either:
- Direct IP: 192.168.132.225 (or .226 per some docs)
- Tailscale IP: 100.77.238.80

This is blocking the VetAssist PII migration to goldfin.

## Symptoms

```
sss_ssh_knownhostsproxy: connect to host goldfin port 22: Connection timed out
Connection closed by UNKNOWN port 65535
```

Tailscale shows goldfin as "idle" which suggests the host was online at some point.

---

## Diagnostic Steps

### Step 1: Physical/Console Access

```bash
# Need physical or IPMI/iDRAC access to goldfin
# Check if system is powered on
# Check for kernel panics or boot failures
```

### Step 2: Network Diagnostics (from greenfin)

```bash
# From greenfin (same VLAN segment)
ping 192.168.132.225
ping 192.168.132.226

# Check ARP table
arp -n | grep 192.168.132.22

# Port scan (if ICMP blocked)
nmap -Pn -p 22 192.168.132.225
nmap -Pn -p 22 192.168.132.226
```

### Step 3: Tailscale Status

```bash
# Check tailscale status for goldfin
tailscale status | grep goldfin
tailscale ping goldfin
```

### Step 4: Check Switch/Router

- Verify VLAN 132 (or VLAN 20 for Sanctum) is trunked properly
- Check for MAC address in switch ARP table
- Verify no firewall rules blocking

---

## Expected Configuration (from docs)

Per JR-Goldfin-Security-Architecture.md:
- **OS**: Debian 12 (Bookworm)
- **IP**: 192.168.20.10 (VLAN 20 Sanctum) OR 192.168.132.226 (VLAN 132)
- **Tailscale**: 100.77.238.80
- **Services planned**: PostgreSQL 17, FreeIPA client, Vault agent
- **Purpose**: PII Vault for VetAssist veteran data

---

## Recovery Actions

### If powered off:
1. Power on via physical access or IPMI
2. Wait for boot
3. Verify SSH connectivity

### If boot failure:
1. Boot to rescue mode
2. Check /var/log/syslog for errors
3. Repair grub or filesystem as needed

### If network misconfigured:
1. Verify /etc/network/interfaces or netplan config
2. Verify VLAN tagging matches switch config
3. Restart networking: `systemctl restart networking`

### If Tailscale down:
1. `sudo systemctl restart tailscaled`
2. `sudo tailscale up`

---

## Success Criteria

- [ ] Goldfin responds to ping on at least one IP
- [ ] SSH accessible: `ssh dereadi@goldfin`
- [ ] Tailscale connection restored
- [ ] System services running normally

---

## Post-Recovery

Once goldfin is online, proceed with:
- JR-VETASSIST-GOLDFIN-PII-MIGRATION-JAN27-2026.md

---

## References

- JR-Goldfin-Security-Architecture.md
- JR-GOLDFIN-DUAL-DATABASE-SETUP-JAN2026.md
- KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026.md

---

FOR SEVEN GENERATIONS
