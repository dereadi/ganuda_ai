# Jr Task: Trunk Port Configuration with Verbose Logging

**Date**: January 6, 2026
**Priority**: HIGH
**Target**: TP-Link TL-SG1428PE (192.168.132.132) + greenfin (192.168.132.224)
**Prerequisite**: Switch credentials updated (admin / same as bluefin postgres)
**TPM**: Flying Squirrel (dereadi)

## Background

We need a trunk port so greenfin can access multiple VLANs (1, 10, 20) for Ansible patching of Sanctum nodes. All cross-VLAN access must be logged for audit trail.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  greenfin (port 17 - TRUNK)                                     │
│  ├── eth0      : 192.168.132.224/24  (VLAN 1 - untagged/native)│
│  ├── eth0.10   : 192.168.10.1/24     (VLAN 10 - tagged)        │
│  └── eth0.20   : 192.168.20.1/24     (VLAN 20 - tagged)        │
│                                                                  │
│  Can reach:                                                      │
│  - silverfin (192.168.10.10) via eth0.10                        │
│  - goldfin (192.168.20.10) via eth0.20                          │
│                                                                  │
│  All connections logged to:                                      │
│  - /var/log/ganuda/sanctum-access.log                           │
│  - thermal_memory_archive (audit type)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Switch Configuration

### Task 1.1: Configure Port 17 as Trunk

1. Browse to http://192.168.132.132
2. Login with updated credentials
3. Navigate to **VLAN > 802.1Q VLAN**
4. For each VLAN, configure port 17:

| VLAN ID | Port 17 Mode | Notes |
|---------|--------------|-------|
| 1 | Untagged | Native VLAN (existing compute traffic) |
| 10 | Tagged | Identity VLAN (silverfin) |
| 20 | Tagged | Sanctum VLAN (goldfin) |

5. Navigate to **VLAN > 802.1Q PVID Setting**
6. Set Port 17 PVID = 1 (native VLAN)

### Task 1.2: Verify Configuration

After saving, verify in the VLAN membership table:
- Port 17 should show membership in VLANs 1, 10, 20
- VLANs 10 and 20 should show port 17 as "T" (tagged)
- VLAN 1 should show port 17 as "U" (untagged)

---

## PHASE 2: greenfin Network Configuration

### Task 2.1: Create VLAN Interfaces

SSH to greenfin and create the VLAN subinterfaces:

```bash
# Create netplan config for VLAN interfaces
sudo nano /etc/netplan/01-vlans.yaml
```

Contents:
```yaml
network:
  version: 2
  vlans:
    eth0.10:
      id: 10
      link: eth0
      addresses:
        - 192.168.10.1/24
      # NO gateway - isolated network
    eth0.20:
      id: 20
      link: eth0
      addresses:
        - 192.168.20.1/24
      # NO gateway - isolated network
```

Apply configuration:
```bash
sudo netplan apply
```

### Task 2.2: Verify VLAN Interfaces

```bash
# Check interfaces exist
ip addr show eth0.10
ip addr show eth0.20

# Test connectivity (after Sanctum nodes are online)
ping -c 2 192.168.10.10  # silverfin
ping -c 2 192.168.20.10  # goldfin
```

---

## PHASE 3: Verbose Logging Setup

### Task 3.1: Create Log Directory

```bash
sudo mkdir -p /var/log/ganuda
sudo chown dereadi:dereadi /var/log/ganuda
```

### Task 3.2: Configure iptables Logging

Create firewall rules to log all new connections to Sanctum VLANs:

```bash
# Log new connections to Identity VLAN (silverfin)
sudo iptables -A OUTPUT -o eth0.10 -m state --state NEW -j LOG \
  --log-prefix "[SANCTUM-IDENTITY] " --log-level 4

# Log new connections to Sanctum VLAN (goldfin)
sudo iptables -A OUTPUT -o eth0.20 -m state --state NEW -j LOG \
  --log-prefix "[SANCTUM-PII] " --log-level 4

# Log incoming from Sanctum (for auth requests from goldfin)
sudo iptables -A INPUT -i eth0.10 -m state --state NEW -j LOG \
  --log-prefix "[FROM-IDENTITY] " --log-level 4
sudo iptables -A INPUT -i eth0.20 -m state --state NEW -j LOG \
  --log-prefix "[FROM-SANCTUM] " --log-level 4
```

### Task 3.3: Make iptables Rules Persistent

```bash
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

### Task 3.4: Configure rsyslog for Dedicated Log File

Create `/etc/rsyslog.d/50-sanctum-access.conf`:
```
# Route Sanctum access logs to dedicated file
:msg, contains, "SANCTUM-" /var/log/ganuda/sanctum-access.log
:msg, contains, "FROM-IDENTITY" /var/log/ganuda/sanctum-access.log
:msg, contains, "FROM-SANCTUM" /var/log/ganuda/sanctum-access.log
```

Restart rsyslog:
```bash
sudo systemctl restart rsyslog
```

---

## PHASE 4: Thermal Memory Logging

### Task 4.1: Create Audit Script

Create `/ganuda/scripts/sanctum-audit-to-thermal.sh`:

```bash
#!/bin/bash
# Reads sanctum access log and writes to thermal memory
# Run via cron every 5 minutes

LOG_FILE="/var/log/ganuda/sanctum-access.log"
MARKER_FILE="/ganuda/scripts/.sanctum-audit-position"
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_PASS="jawaseatlasers2"
DB_NAME="zammad_production"

# Get last position
if [ -f "$MARKER_FILE" ]; then
    LAST_POS=$(cat "$MARKER_FILE")
else
    LAST_POS=0
fi

# Get new lines
NEW_LINES=$(tail -c +$LAST_POS "$LOG_FILE" 2>/dev/null)

if [ -n "$NEW_LINES" ]; then
    # Count connections by type
    IDENTITY_COUNT=$(echo "$NEW_LINES" | grep -c "SANCTUM-IDENTITY")
    PII_COUNT=$(echo "$NEW_LINES" | grep -c "SANCTUM-PII")

    if [ $((IDENTITY_COUNT + PII_COUNT)) -gt 0 ]; then
        TIMESTAMP=$(date +%Y-%m-%d_%H%M)
        CONTENT="SANCTUM ACCESS AUDIT - $TIMESTAMP
Connections to Identity VLAN (silverfin): $IDENTITY_COUNT
Connections to PII VLAN (goldfin): $PII_COUNT
Source: greenfin trunk port logging"

        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
        INSERT INTO thermal_memory_archive (
            memory_hash, original_content, temperature_score,
            tags, source_triad, source_node, memory_type
        ) VALUES (
            md5('sanctum_audit_$TIMESTAMP'),
            '$CONTENT',
            75.0,
            ARRAY['sanctum', 'audit', 'access-log', 'security'],
            'ops',
            'greenfin',
            'audit'
        ) ON CONFLICT (memory_hash) DO NOTHING;"
    fi
fi

# Update position
wc -c < "$LOG_FILE" > "$MARKER_FILE"
```

Make executable:
```bash
chmod +x /ganuda/scripts/sanctum-audit-to-thermal.sh
```

### Task 4.2: Add Cron Job

```bash
crontab -e
# Add:
*/5 * * * * /ganuda/scripts/sanctum-audit-to-thermal.sh
```

---

## PHASE 5: Ansible Integration

### Task 5.1: Update Ansible Inventory

Add to `/ganuda/ansible/inventory_federation.ini`:

```ini
[sanctum]
silverfin ansible_host=192.168.10.10 ansible_user=dereadi
goldfin ansible_host=192.168.20.10 ansible_user=dereadi

[sanctum:vars]
ansible_python_interpreter=/usr/bin/python3
# Access via greenfin trunk port
```

### Task 5.2: Test Connectivity (after hardware arrives)

```bash
# From greenfin
ansible sanctum -m ping -i /ganuda/ansible/inventory_federation.ini
```

---

## Verification Checklist

- [ ] Port 17 configured as trunk with VLANs 1 (U), 10 (T), 20 (T)
- [ ] greenfin has eth0.10 (192.168.10.1) and eth0.20 (192.168.20.1)
- [ ] iptables logging rules active
- [ ] Logs appearing in /var/log/ganuda/sanctum-access.log
- [ ] Audit script writing to thermal memory
- [ ] Cron job scheduled

---

## Security Notes

- Trunk port is a **privileged access point** - greenfin becomes the only compute node that can reach Sanctum
- All access is logged for audit compliance
- Consider disabling trunk port when not actively patching (via switch web UI)
- Review sanctum-access.log weekly for anomalies

---

## Log Format Examples

```
Jan  6 14:23:15 greenfin kernel: [SANCTUM-IDENTITY] IN= OUT=eth0.10 SRC=192.168.10.1 DST=192.168.10.10 PROTO=TCP DPT=22
Jan  6 14:23:18 greenfin kernel: [SANCTUM-PII] IN= OUT=eth0.20 SRC=192.168.20.1 DST=192.168.20.10 PROTO=TCP DPT=22
```

---

## For Seven Generations
