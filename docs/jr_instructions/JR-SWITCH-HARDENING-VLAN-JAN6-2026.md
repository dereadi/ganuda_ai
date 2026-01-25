# Jr Task: TP-Link TL-SG1428PE Switch Hardening + VLAN Configuration

**Date**: January 6, 2026
**Priority**: HIGH
**Target**: TP-Link TL-SG1428PE (192.168.132.132)
**Manual**: https://www.manualslib.com/manual/3206987/Tp-Link-Tl-Sg1428pe.html
**TPM**: Flying Squirrel (dereadi)

## Background

The TL-SG1428PE is our core switch for the Cherokee AI Federation. Before configuring VLANs for goldfin/silverfin, we need to harden the switch itself to reduce attack surface.

## Switch Capabilities (from manual)

| Feature | Description |
|---------|-------------|
| VLAN | MTU, Port-Based, 802.1Q (up to 32 VLANs) |
| QoS | 4 queues, 802.1P, DSCP |
| PoE | Per-port control, system power limit |
| Monitoring | Port stats, mirroring, cable test |
| Security | Storm control, loop prevention |
| LAG | Link aggregation for bandwidth |
| IGMP | Multicast snooping |

---

## PHASE 1: SWITCH HARDENING (Do First!)

### Task 1.1: Change Default Credentials

**CRITICAL** - Default is admin/admin

1. Browse to http://192.168.132.132
2. Login with current credentials
3. Navigate to **System > User Account**
4. Change username from `admin` to something non-obvious (e.g., `ganuda_admin`)
5. Set strong password (use password manager)
6. Save credentials to `/Users/Shared/ganuda/docs/api_keys/switch_credentials.enc` (encrypted)

### Task 1.2: Change Switch IP (Optional - Reduces Exposure)

Consider moving switch management to VLAN 99:
1. Navigate to **System > System IP**
2. Change from 192.168.132.132 to 192.168.99.1
3. **WARNING**: You'll lose access until you configure a device on VLAN 99

Alternative: Keep on 192.168.132.x but use less obvious IP (e.g., 192.168.132.253)

### Task 1.3: Update Device Description

1. Navigate to **System > System Info**
2. Set Device Description: `Cherokee-AI-Core-Switch`
3. Set Location: `Federation Compound`

### Task 1.4: Enable Storm Control

Protects against broadcast storms:
1. Navigate to **Switching > Storm Control**
2. Enable for all ports
3. Set thresholds:
   - Broadcast: 1000 pps
   - Multicast: 1000 pps
   - Unknown Unicast: 500 pps

### Task 1.5: Enable Loop Prevention

1. Navigate to **Switching > Loop Prevention**
2. Enable globally
3. Set recovery time: 60 seconds

### Task 1.6: Backup Current Config

1. Navigate to **System > System Tools > Backup & Restore**
2. Export current configuration
3. Save to `/Users/Shared/ganuda/backups/switch/TL-SG1428PE_backup_YYYYMMDD.cfg`

---

## PHASE 2: VLAN CONFIGURATION

### Task 2.1: Enable 802.1Q VLAN Mode

1. Navigate to **VLAN > 802.1Q VLAN**
2. Enable 802.1Q VLAN (this disables other VLAN modes)
3. **Note**: Existing VLAN config may be lost - ensure backup first

### Task 2.2: Create VLANs

| VLAN ID | Name | Purpose |
|---------|------|---------|
| 1 | Compute | redfin, bluefin, greenfin, sasass (default) |
| 10 | Identity | silverfin - FreeIPA |
| 20 | Sanctum | goldfin - PII Alcove |
| 99 | Management | Switch mgmt, future IPMI |

For each VLAN:
1. Click **Add**
2. Enter VLAN ID
3. Enter VLAN Name (max 10 chars)
4. Configure member ports (see below)
5. Save

### Task 2.3: Port Assignments

**UPDATED January 10, 2026 - Revised for actual deployment:**

```
Port Configuration (ACTUAL):
┌─────────────────────────────────────────────────────────────┐
│  Port 14:     silverfin - VLAN 10 Untagged, PVID 10        │
│  Port 16:     goldfin - VLAN 20 Untagged, PVID 20          │
│  Port 18:     greenfin trunk - VLANs 1,10,20 all Tagged    │
│  All other:   VLAN 1 (Compute) - Untagged (default)        │
└─────────────────────────────────────────────────────────────┘
```

**CRITICAL - Web UI Radio Button Values:**
The TP-Link web interface uses these values for port membership:
- **value=0** = Untagged
- **value=1** = Tagged
- **value=2** = Not Member (default)

Form field names discovered via inspection:
- `qvlan_en[value=1]` - Enable 802.1Q
- `vid` - VLAN ID input field
- `vname` - VLAN Name input field
- `selType_N` - Port N membership (where N is port number)
- `Create` button - Creates new VLAN
- `Modify` button - Modifies selected VLAN

### Task 2.4: Configure PVID

Navigate to **VLAN > 802.1Q PVID Setting**:

**ACTUAL PVID Configuration (Updated Jan 10):**

| Port | PVID | Purpose |
|------|------|---------|
| 14 | 10 | silverfin native VLAN |
| 16 | 20 | goldfin native VLAN |
| 18 | 1 | greenfin trunk (native VLAN 1) |
| All others | 1 | Compute network |

### Task 2.5: Static IP Configuration (No DHCP on Sanctum VLANs)

These VLANs are **isolated by design** - no router, no DHCP, no internet.
Static IPs only. Tailscale provides external access to goldfin.

#### VLAN 10 - Identity (silverfin)
```yaml
# /etc/netplan/00-installer-config.yaml (Ubuntu)
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.10.10/24
      # NO gateway - isolated network
      nameservers:
        addresses: []  # No DNS needed
```

#### VLAN 20 - Sanctum (goldfin)
```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.20.10/24
      # NO gateway - Tailscale handles external access
      nameservers:
        addresses: []
```

#### Static IP Summary

| Node | VLAN | Static IP | Gateway | Internet | Notes |
|------|------|-----------|---------|----------|-------|
| silverfin | 10 | 192.168.10.10/24 | NONE | NO | FreeIPA identity server |
| goldfin | 20 | 192.168.20.10/24 | NONE | Tailscale only | PII Alcove - encrypted |

#### Why No Gateway?

- **Security**: These nodes should NOT route to the internet or compute VLAN
- **Isolation**: Layer 2 VLAN isolation + no Layer 3 routing = true air gap
- **Tailscale**: goldfin uses Tailscale overlay for authorized remote access
- **Auth only**: goldfin → silverfin allowed for Kerberos/LDAP (ports 88, 389, 636)

#### Communication Between Sanctum Nodes

silverfin and goldfin CAN communicate if you add a route:
```bash
# On goldfin - route to silverfin for auth
sudo ip route add 192.168.10.0/24 dev eth0

# On silverfin - route to goldfin (if needed)
sudo ip route add 192.168.20.0/24 dev eth0
```

But this requires a Layer 3 device or direct cable between VLANs.
Alternative: Use a trunk port with tagged VLANs on a dual-NIC device.

---

## PHASE 3: PoE CONFIGURATION (Optional)

If goldfin/silverfin are PoE devices:

1. Navigate to **PoE > PoE Config**
2. Enable PoE on ports 13-16 only
3. Set per-port power limits as needed
4. Enable PoE Auto Recovery (ping-based) for critical devices

---

## PHASE 4: QoS FOR PRIORITY TRAFFIC

### Task 4.1: Prioritize Database Traffic

1. Navigate to **QoS > QoS Basic**
2. Set priority mode: Port-Based
3. Assign bluefin port (port 2) to **Highest** priority

### Task 4.2: Prioritize GPU Inference

1. Set redfin port (port 1) to **High** priority

---

## PHASE 5: MONITORING SETUP

### Task 5.1: Enable Port Mirroring (Optional)

For security monitoring:
1. Navigate to **Monitoring > Port Mirror**
2. Mirror ports 13-16 (Identity/Sanctum) to a monitoring port
3. Connect IDS/monitoring device to mirror port

### Task 5.2: Document Port Statistics Baseline

1. Navigate to **Monitoring > Port Statistics**
2. Record current stats for all ports
3. Save to KB for future comparison

---

## VERIFICATION CHECKLIST

After configuration:

- [ ] Can access switch with new credentials
- [ ] Storm control enabled on all ports
- [ ] Loop prevention enabled
- [ ] VLANs 1, 10, 20, 99 created
- [ ] Ports assigned to correct VLANs
- [ ] PVIDs set correctly
- [ ] From compute VLAN: Can reach Identity (192.168.10.x)
- [ ] From compute VLAN: CANNOT reach Sanctum (192.168.20.x)
- [ ] Config backup saved
- [ ] Credentials stored securely

---

## ROLLBACK PROCEDURE

If something breaks:
1. Factory reset: Hold reset button 5+ seconds
2. Access at default IP (likely 192.168.0.1)
3. Restore from backup config file

---

## Security Notes

- **Never leave default credentials** - this is a common attack vector
- **Document all changes** in thermal memory
- **Test isolation** before connecting PII systems
- **Keep firmware updated** - check https://www.tp-link.com/us/support/download/tl-sg1428pe/

---

## Sources

- [TP-Link TL-SG1428PE Manual](https://www.manualslib.com/manual/3206987/Tp-Link-Tl-Sg1428pe.html)
- [TP-Link Downloads](https://www.tp-link.com/us/support/download/tl-sg1428pe/)
- [VLAN Config Guide (Page 49)](https://www.manualowl.com/m/TP-Link/TL-SG1428PE/Manual/631948?page=49)

---

For Seven Generations.
