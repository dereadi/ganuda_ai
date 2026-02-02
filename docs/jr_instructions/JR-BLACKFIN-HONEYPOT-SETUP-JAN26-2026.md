# Jr Instruction: Setup blackfin Honeypot Server

**Task ID:** To be assigned
**Jr Type:** Infrastructure Jr.
**Priority:** P2
**Category:** Security Infrastructure
**Council Approved:** Yes (T-Pot on isolated VLAN)

---

## Overview

Dell server repurposed as honeypot for tribal security monitoring.

- **Hostname:** blackfin
- **Purpose:** Honeypot / threat detection
- **OS:** T-Pot (telekom-security/tpotce)

---

## Network Architecture (Council Recommendation)

### VLAN Isolation
- **VLAN ID:** TBD (suggest VLAN 99 - "DMZ-Weak")
- **Subnet:** 192.168.199.0/24 (or similar isolated range)
- **Gateway:** greenfin routes but NO access to production VLANs

### Firewall Rules (greenfin nftables)
```
# Allow inbound from anywhere (it's a honeypot)
# Block outbound to production VLANs (10, 20, 30)
# Allow outbound to internet for C2 simulation logging
```

### Intentional Weak Posture
- Open common ports: 22, 23, 80, 443, 3389, 445, 3306, 5432
- Weak SSH banner (outdated version string)
- No rate limiting
- Basic HTTP server with "admin/admin" login page

---

## T-Pot Installation

T-Pot bundles 20+ honeypots including:
- Cowrie (SSH/Telnet)
- Dionaea (malware collection)
- Honeytrap (low-interaction)
- Conpot (ICS/SCADA)
- Mailoney (SMTP)

### Install Steps

1. **Download ISO**: https://github.com/telekom-security/tpotce
2. **Install Debian base** (or use T-Pot ISO directly)
3. **Run T-Pot installer**:
   ```bash
   git clone https://github.com/telekom-security/tpotce
   cd tpotce/iso/installer/
   sudo ./install.sh --type=user
   ```

---

## Eagle Eye Integration

T-Pot provides Elasticsearch + Kibana. Export to Eagle Eye via:

1. **Filebeat** → OpenObserve (greenfin)
2. **Webhook alerts** → Telegram bot for critical events
3. **Daily summary** → Standup discussion

---

## CMDB Entry

Add to hardware_inventory:
```sql
INSERT INTO hardware_inventory (hostname, ip_address, role, vlan, location)
VALUES ('blackfin', '192.168.199.10', 'honeypot', 99, 'rack-1');
```

---

## Do NOT

- Connect blackfin to production VLANs
- Use production credentials on blackfin
- Allow outbound to bluefin/redfin/greenfin

---

## Success Criteria

1. T-Pot dashboard accessible at https://blackfin:64297
2. Honeypots receiving traffic
3. Alerts flowing to Eagle Eye
4. VLAN isolation verified with `ping` tests
