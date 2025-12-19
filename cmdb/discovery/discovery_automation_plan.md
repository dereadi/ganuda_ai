# CMDB Discovery Automation Plan

**Author**: IT Jr 3 (Automation & Discovery)
**Date**: 2025-11-28
**Status**: PLAN COMPLETE - Ready for Implementation
**Target**: Automated infrastructure discovery for CMDB

---

## Executive Summary

Automate the discovery and registration of infrastructure components (servers, services, IoT devices) into the CMDB to maintain accurate, up-to-date configuration data without manual intervention.

---

## Current Discovery Mechanisms (Inventory)

### 1. Ansible Inventory
**Location**: `/etc/ansible/hosts` or `/ganuda/ansible/` (likely)
**Coverage**: redfin, bluefin, greenfin, yellowfin
**Data Available**:
- Hostnames
- IP addresses (local + Tailscale)
- SSH connectivity
- Ansible facts (OS, CPU, RAM, disk, packages)

**Frequency**: On-demand (manual ansible runs)

**Assessment**: ✅ Excellent source for server discovery

---

### 2. Hardware Inventory Scripts
**Possible locations**:
- `/ganuda/scripts/hardware_inventory.py`
- Cherokee Desktop monitoring agents
- Custom system info scripts

**Data Available**:
- CPU/GPU specifications
- Memory capacity
- Disk space
- Network interfaces

**Frequency**: Varies (manual or cron-based)

**Assessment**: ⚠️ May exist, needs verification

---

### 3. IoT Device Registry
**Source**: IoT Device Management in SAG (:4000)
**Database**: Likely `zammad_production.iot_devices` table
**Coverage**: yellowfin, smart home devices, sensors

**Data Available**:
- Device names and types
- IP addresses (if networked)
- Device status
- Last seen timestamps

**Frequency**: Real-time (IoT scanner Jr runs autonomously)

**Assessment**: ✅ Active and maintained

---

### 4. Service Port Scanning
**Tool**: nmap or custom scanner
**Coverage**: All nodes on 192.168.132.x network
**Data Available**:
- Open ports
- Service banners/versions
- HTTP endpoints

**Frequency**: Manual (security scans)

**Assessment**: ⚠️ Not automated, potential security tool

---

### 5. Docker Container Discovery
**Method**: `docker ps` on nodes running Docker
**Coverage**: redfin (likely), possibly others
**Data Available**:
- Container names
- Images
- Ports mapped
- Running status

**Frequency**: Real-time (if Docker is running)

**Assessment**: ⚠️ Need to verify Docker usage

---

### 6. Package Inventories
**Methods**:
- `dpkg -l` (Debian/Ubuntu)
- `rpm -qa` (RHEL/Fedora)
- `brew list` (macOS)

**Coverage**: All nodes
**Data Available**:
- Installed software
- Versions
- Package managers

**Frequency**: On-demand

**Assessment**: ✅ Useful for software CI tracking

---

## Auto-Discovery Strategy

### Phase 1: Ansible-Based Discovery (Week 1)
**Goal**: Auto-discover all servers and basic info

**Method**:
1. Run `ansible all -m setup` to gather facts
2. Parse facts → insert/update cmdb_configuration_items
3. Schedule via cron: Daily at 02:00

**Data to capture**:
```python
{
    "ci_name": ansible_hostname,
    "ci_type": "server",
    "ip_addresses": [ansible_default_ipv4.address, ansible_tailscale_ip],
    "hardware_specs": {
        "cpu": ansible_processor,
        "ram": ansible_memtotal_mb,
        "os": ansible_distribution,
        "kernel": ansible_kernel
    },
    "discovered_at": NOW(),
    "last_verified_at": NOW()
}
```

**Script location**: `/ganuda/cmdb/discovery/ansible_discovery.py`

---

### Phase 2: Service Discovery (Week 2)
**Goal**: Auto-discover services running on each server

**Methods**:
1. **systemd**: `systemctl list-units --type=service --state=running`
2. **Port scan**: `ss -tlnp` or `netstat -tlnp`
3. **Process list**: `ps aux | grep python`

**Service detection rules**:
```python
PORT_TO_SERVICE = {
    5432: "postgresql",
    4000: "sag_unified_interface",
    8002: "visual_kanban",
    3000: "grafana",
    5555: "cherokee_desktop"
}

# HTTP endpoints
if port == 80 or port == 443 or port > 3000:
    try:
        response = requests.get(f"http://{ip}:{port}")
        if "SAG" in response.text:
            service_name = "sag_unified_interface"
    except:
        pass
```

**Data to capture**:
```python
{
    "ci_name": f"{service_name}_{node_name}",
    "ci_type": "web_service" or "database",
    "ports": [port],
    "software_specs": {
        "detected_via": "port_scan",
        "url": f"http://{ip}:{port}"
    },
    "discovered_at": NOW()
}
```

**Relationships**:
```python
# Link service to server
INSERT INTO cmdb_relationships (source_ci, target_ci, relationship_type)
VALUES (service_id, server_id, 'runs_on');
```

---

### Phase 3: IoT Device Discovery (Week 3)
**Goal**: Sync IoT devices from SAG into CMDB

**Method**:
1. Query `zammad_production.iot_devices`
2. Insert as `ci_type='iot_device'`
3. Link to yellowfin (or appropriate hub)

**Query**:
```sql
SELECT
    device_name,
    device_type,
    ip_address,
    last_seen,
    status
FROM zammad_production.iot_devices
WHERE status = 'active';
```

**Data to capture**:
```python
{
    "ci_name": device_name,
    "ci_type": "iot_device",
    "ip_addresses": [ip_address] if ip_address else [],
    "hardware_specs": {
        "device_type": device_type,
        "last_seen": last_seen
    },
    "status": status,
    "discovered_at": NOW()
}
```

---

### Phase 4: Package/Software Discovery (Week 4)
**Goal**: Track installed software on all nodes

**Method**:
1. Ansible command: `ansible all -m package_facts`
2. Parse package lists
3. Insert major packages as CIs (PostgreSQL, Python, Node.js, etc.)

**Filter criteria** (to avoid thousands of packages):
- Only packages matching critical services
- Databases: postgresql, mysql, redis
- Web servers: nginx, apache2
- Runtimes: python3, node, java

**Data to capture**:
```python
{
    "ci_name": f"{package_name}_{node_name}",
    "ci_type": "software",
    "software_specs": {
        "version": package_version,
        "package_manager": "apt" or "brew",
        "installed_on": node_name
    },
    "discovered_at": NOW()
}
```

---

## Discovery Automation Schedule

### Cron Jobs (on redfin)

**Daily Discovery (02:00)**:
```bash
0 2 * * * /ganuda/cmdb/discovery/ansible_discovery.py >> /ganuda/logs/cmdb_discovery.log 2>&1
```

**Hourly Service Check (on the hour)**:
```bash
0 * * * * /ganuda/cmdb/discovery/service_discovery.py >> /ganuda/logs/cmdb_discovery.log 2>&1
```

**Weekly IoT Sync (Sunday 03:00)**:
```bash
0 3 * * 0 /ganuda/cmdb/discovery/iot_sync.py >> /ganuda/logs/cmdb_discovery.log 2>&1
```

---

## Conflict Resolution

### What if CI changes between discoveries?

**Rules**:
1. **IP address changes**: Update ip_addresses array, write to cmdb_changes
2. **Service moves nodes**: Update relationships, mark old as deleted
3. **Hardware upgrade**: Update hardware_specs JSONB, log change
4. **CI disappears**: Mark status='retired', don't delete (audit trail)

**Change detection**:
```python
def update_ci(ci_name, new_data):
    existing = get_ci_by_name(ci_name)

    if existing is None:
        # New CI - insert
        insert_ci(new_data)
        log_change(ci_name, 'create', new_data)
    else:
        # Check for changes
        changes = diff(existing, new_data)

        if changes:
            update_ci(ci_name, new_data)
            log_change(ci_name, 'update', before=existing, after=new_data)
```

**Thermal memory integration**:
```python
# Write significant changes to thermal memory
if change_is_significant(changes):
    write_to_thermal_memory(
        content=f"CMDB Discovery: {ci_name} {change_type}",
        temperature=0.65
    )
```

---

## Discovery Agent Architecture

### Main Script: `ansible_discovery.py`

```python
#!/usr/bin/env python3
"""
CMDB Ansible Discovery Agent
Runs daily to discover/update server CIs
"""

import subprocess
import json
import psycopg2
from datetime import datetime

def run_ansible_facts():
    """Run ansible setup module on all hosts"""
    cmd = ["ansible", "all", "-m", "setup", "--one-line"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return parse_ansible_output(result.stdout)

def parse_ansible_output(output):
    """Parse ansible facts into CI data"""
    cis = []
    for line in output.strip().split('\n'):
        hostname, facts_json = line.split(' | SUCCESS => ', 1)
        facts = json.loads(facts_json)['ansible_facts']

        ci = {
            'ci_name': facts['ansible_hostname'],
            'ci_type': 'server',
            'ip_addresses': [
                facts['ansible_default_ipv4']['address'],
                # Add Tailscale IP if exists
            ],
            'hardware_specs': {
                'cpu': facts['ansible_processor'][0],
                'ram_mb': facts['ansible_memtotal_mb'],
                'os': facts['ansible_distribution'],
                'kernel': facts['ansible_kernel']
            }
        }
        cis.append(ci)

    return cis

def upsert_to_cmdb(cis):
    """Insert or update CIs in database"""
    conn = psycopg2.connect(
        host="192.168.132.222",
        database="triad_federation",
        user="claude",
        password="jawaseatlasers2"
    )

    for ci in cis:
        # Use ON CONFLICT DO UPDATE for upsert
        # Log changes to cmdb_changes table
        pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting CMDB discovery...")

    cis = run_ansible_facts()
    print(f"Discovered {len(cis)} servers")

    upsert_to_cmdb(cis)
    print("Discovery complete")
```

---

## Testing Strategy

### Phase 1 Test (Ansible Discovery)
1. Run `ansible_discovery.py` manually
2. Verify 7 servers updated in cmdb_configuration_items
3. Check cmdb_changes for create/update entries
4. Verify no duplicates (ON CONFLICT works)

### Phase 2 Test (Service Discovery)
1. Run `service_discovery.py` on redfin only
2. Verify SAG, Kanban, Grafana detected
3. Check relationships created (service → redfin)
4. Verify ports captured correctly

### Phase 3 Test (IoT Sync)
1. Run `iot_sync.py`
2. Compare cmdb_configuration_items with iot_devices table
3. Verify counts match
4. Check relationships to yellowfin

---

## Success Criteria

✅ Daily Ansible discovery running via cron
✅ All 7 servers auto-update in CMDB
✅ Services detected and linked to servers
✅ IoT devices synced weekly
✅ Changes logged to cmdb_changes table
✅ Significant changes written to thermal memory
✅ No duplicate CIs created
✅ Discovery logs written to /ganuda/logs/cmdb_discovery.log

---

## Monitoring & Alerting

### Discovery Health Checks

**Monitor**:
- Last successful discovery timestamp
- Number of CIs discovered per run
- Discovery failures/errors

**Alert if**:
- No discovery run in 25 hours (daily should run at 02:00)
- CI count drops significantly (server went offline?)
- Repeated failures

**Integration**: Write alerts to thermal memory (temp 0.70)

---

## Future Enhancements (Phase 5+)

1. **Network Device Discovery**: SNMP polling for routers/switches
2. **Cloud Resource Discovery**: If Federation expands to cloud
3. **Dependency Auto-Detection**: Analyze logs to infer dependencies
4. **Performance Metrics**: CPU/RAM usage → CMDB
5. **Certificate Expiry Tracking**: SSL certs as CIs
6. **Compliance Scanning**: Link to security scan results

---

## File Structure

```
/ganuda/cmdb/discovery/
├── ansible_discovery.py       # Phase 1: Server discovery
├── service_discovery.py        # Phase 2: Service detection
├── iot_sync.py                 # Phase 3: IoT device sync
├── package_discovery.py        # Phase 4: Software inventory
├── discovery_common.py         # Shared functions
├── requirements.txt            # Python dependencies
└── README.md                   # Discovery system docs

/ganuda/logs/
└── cmdb_discovery.log          # Discovery logs

/etc/cron.d/
└── cmdb_discovery              # Cron schedule
```

---

## Dependencies

**Python packages**:
```
psycopg2-binary>=2.9
requests>=2.28
ansible>=2.14  # For running ansible commands
```

**System requirements**:
- Ansible installed on redfin
- SSH access to all nodes (already configured)
- PostgreSQL access (already configured)
- Python 3.9+ with cherokee_venv

---

## Next Steps

1. **Verify Ansible inventory** exists and is current
2. **Write ansible_discovery.py** (Phase 1)
3. **Test manually** before scheduling cron
4. **Deploy cron job** for daily runs
5. **Monitor first week** of automated discovery
6. **Implement Phases 2-4** incrementally

---

**Plan Status**: ✅ COMPLETE - Ready for implementation
**Estimated Dev Time**: 4 weeks (phased approach)
**Dependencies**: Ansible inventory, database access
**Blockers**: None

---

*Planned by IT Jr 3, 2025-11-28*
*Cherokee AI Federation - Automation Excellence*
