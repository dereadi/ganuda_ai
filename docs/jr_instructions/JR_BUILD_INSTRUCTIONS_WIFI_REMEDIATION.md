# Jr Build Instructions: WiFi Remediation for Mac Studios

**Priority**: HIGH  
**Security Flag**: KB-SEC-001  
**Assigned To**: Crawdad Jr (Security Operations)

## Objective

Disable WiFi on sasass and sasass2 Mac Studios to comply with network bridging policy. Only greenfin should bridge the 192.168.132.x and 10.0.0.x networks.

## Pre-Flight Checks

1. Verify wired connectivity is stable on both Mac Studios
2. Confirm no critical services depend on WiFi connectivity
3. Document current WiFi state

## Implementation Steps

### Step 1: Document Current State

```bash
# On sasass (192.168.132.241)
ssh dereadi@192.168.132.241 "networksetup -getairportpower en1"
ssh dereadi@192.168.132.241 "ifconfig en1 | grep inet"

# On sasass2 (192.168.132.242)
ssh dereadi@192.168.132.242 "networksetup -getairportpower en1"
ssh dereadi@192.168.132.242 "ifconfig en1 | grep inet"
```

### Step 2: Disable WiFi on sasass

```bash
ssh dereadi@192.168.132.241 "networksetup -setairportpower en1 off"
```

### Step 3: Disable WiFi on sasass2

```bash
ssh dereadi@192.168.132.242 "networksetup -setairportpower en1 off"
```

### Step 4: Verify Remediation

```bash
# Confirm WiFi is off
ssh dereadi@192.168.132.241 "networksetup -getairportpower en1"
ssh dereadi@192.168.132.242 "networksetup -getairportpower en1"

# Confirm no response on WiFi IPs
nmap -Pn 10.0.0.108 10.0.0.89 2>/dev/null | grep -E "(open|Host)"
```

### Step 5: Update CMDB

```sql
-- On bluefin
UPDATE hardware_inventory 
SET network_interfaces = jsonb_set(
    network_interfaces, 
    '{wifi_status}', 
    '"disabled_per_KB-SEC-001"'
)
WHERE hostname IN ('sasass', 'sasass2');
```

### Step 6: Update IoT Devices Table

```sql
-- Mark WiFi IPs as remediated
UPDATE iot_devices
SET device_type = 'REMEDIATED - WiFi disabled',
    notes = 'WiFi disabled per KB-SEC-001 network bridging policy'
WHERE ip_address IN ('10.0.0.108', '10.0.0.89');
```

## Rollback Procedure

If WiFi needs to be re-enabled:
```bash
ssh dereadi@192.168.132.241 "networksetup -setairportpower en1 on"
ssh dereadi@192.168.132.242 "networksetup -setairportpower en1 on"
```

## Success Criteria

- [ ] WiFi power off on sasass
- [ ] WiFi power off on sasass2
- [ ] No services respond on 10.0.0.108
- [ ] No services respond on 10.0.0.89
- [ ] CMDB updated
- [ ] Thermal memory logged

## Approval Required

This remediation requires TPM approval before execution as it changes network topology.

---

FOR SEVEN GENERATIONS
