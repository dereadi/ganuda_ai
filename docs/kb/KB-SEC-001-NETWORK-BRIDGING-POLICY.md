# KB-SEC-001: Network Bridging Policy

**Created**: 2025-12-13  
**Flagged by**: Crawdad (Security Specialist)  
**Severity**: HIGH  
**Status**: OPEN - Remediation Required

## Summary

Unauthorized network bridging detected on Cherokee Federation nodes. sasass and sasass2 Mac Studios are dual-homed, exposing services on both the wired (192.168.132.x) and WiFi (10.0.0.x) networks.

## Policy Statement

**Only greenfin (192.168.132.224) is authorized to bridge the 192.168.132.x and 10.0.0.x networks.**

## Findings

| Node | Wired IP | WiFi IP | Services Exposed on WiFi |
|------|----------|---------|--------------------------|
| sasass | 192.168.132.241 | 10.0.0.108 | PostgreSQL:5432, Grafana:3000, SSH, VNC |
| sasass2 | 192.168.132.242 | 10.0.0.89 | Cherokee:8888, SSH, VNC |
| greenfin | 192.168.132.224 | 10.0.0.118 | (Authorized bridge) |

## Security Concerns

1. **Database exposure**: PostgreSQL on sasass accessible from 10.0.0.x network
2. **AI endpoint exposure**: Cherokee Council Flask API on sasass2 accessible from 10.0.0.x
3. **Remote access exposure**: SSH/VNC accessible from WiFi network
4. **Attack surface**: Multiple entry points instead of single controlled bridge

## Remediation Steps

### Option A: Disable WiFi (Recommended)

On sasass (Mac Studio):
```bash
# Disable WiFi interface
networksetup -setairportpower en1 off
# Verify
networksetup -getairportpower en1
```

On sasass2 (Mac Studio):
```bash
# Disable WiFi interface
networksetup -setairportpower en1 off
# Verify
networksetup -getairportpower en1
```

### Option B: Firewall Isolation

If WiFi must remain enabled, bind services to wired interface only:
```bash
# PostgreSQL: Edit postgresql.conf
listen_addresses = 192.168.132.241

# Grafana: Edit grafana.ini
[server]
http_addr = 192.168.132.241
```

## Verification

After remediation, verify no services respond on 10.0.0.x:
```bash
nmap -Pn 10.0.0.108 10.0.0.89
```

## References

- Trail ID: 4 (breadcrumb_trails)
- Thermal Memory: SEC-BRIDGE-VIOLATION-20251213
- CMDB: hardware_inventory network_interfaces field

---

FOR SEVEN GENERATIONS - Network security protects all future operations.
