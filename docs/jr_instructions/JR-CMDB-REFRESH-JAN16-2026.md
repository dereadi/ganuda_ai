# JR Instruction: CMDB Full Refresh

## Metadata
```yaml
task_id: cmdb_refresh_jan16
priority: 1
assigned_to: Infrastructure Jr.
target_node: all
estimated_duration: 45_minutes
```

## Overview

The CMDB is stale (34 days since last scan for most nodes). silverfin and goldfin are completely missing from hardware_inventory. This task refreshes all CMDB data.

## Tasks

### Task 1: Scan All Linux Nodes

Run hardware scan on each node and insert/update hardware_inventory:

```bash
#!/bin/bash
# Run from redfin or any node with SSH access to all others

NODES="redfin bluefin greenfin silverfin goldfin"
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_PASS="jawaseatlasers2"
DB_NAME="zammad_production"

for NODE in $NODES; do
    echo "=== Scanning $NODE ==="

    # Get hardware info via SSH (or locally if current node)
    if [ "$NODE" == "$(hostname -s)" ]; then
        CPU_INFO=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
        MEM_TOTAL=$(free -b | awk '/Mem:/ {print $2}')
        GPU_COUNT=$(nvidia-smi -L 2>/dev/null | wc -l || echo 0)
        OS_INFO=$(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')
        KERNEL=$(uname -r)
    else
        CPU_INFO=$(ssh $NODE "lscpu | grep 'Model name' | cut -d: -f2 | xargs" 2>/dev/null || echo "SSH failed")
        MEM_TOTAL=$(ssh $NODE "free -b | awk '/Mem:/ {print \$2}'" 2>/dev/null || echo 0)
        GPU_COUNT=$(ssh $NODE "nvidia-smi -L 2>/dev/null | wc -l" 2>/dev/null || echo 0)
        OS_INFO=$(ssh $NODE "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'" 2>/dev/null || echo "Unknown")
        KERNEL=$(ssh $NODE "uname -r" 2>/dev/null || echo "Unknown")
    fi

    echo "  CPU: $CPU_INFO"
    echo "  Memory: $MEM_TOTAL"
    echo "  GPUs: $GPU_COUNT"
    echo "  OS: $OS_INFO"

    # Upsert into hardware_inventory
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME << SQL
    INSERT INTO hardware_inventory (hostname, cpu_info, memory_total, gpu_count, os_info, kernel_version, scan_timestamp)
    VALUES ('$NODE', '$CPU_INFO', $MEM_TOTAL, $GPU_COUNT, '$OS_INFO', '$KERNEL', NOW())
    ON CONFLICT (hostname) DO UPDATE SET
        cpu_info = EXCLUDED.cpu_info,
        memory_total = EXCLUDED.memory_total,
        gpu_count = EXCLUDED.gpu_count,
        os_info = EXCLUDED.os_info,
        kernel_version = EXCLUDED.kernel_version,
        scan_timestamp = NOW();
SQL
done

echo "=== Hardware scan complete ==="
```

### Task 2: Scan Mac Nodes

```bash
#!/bin/bash
# Scan Mac nodes

MAC_NODES="sasass sasass2"
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_PASS="jawaseatlasers2"
DB_NAME="zammad_production"

for NODE in $MAC_NODES; do
    echo "=== Scanning $NODE ==="

    CPU_INFO=$(ssh $NODE "sysctl -n machdep.cpu.brand_string" 2>/dev/null || echo "SSH failed")
    MEM_TOTAL=$(ssh $NODE "sysctl -n hw.memsize" 2>/dev/null || echo 0)
    OS_INFO=$(ssh $NODE "sw_vers -productName && sw_vers -productVersion" 2>/dev/null | tr '\n' ' ' || echo "macOS Unknown")
    KERNEL=$(ssh $NODE "uname -r" 2>/dev/null || echo "Unknown")

    echo "  CPU: $CPU_INFO"
    echo "  Memory: $MEM_TOTAL"
    echo "  OS: $OS_INFO"

    PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME << SQL
    INSERT INTO hardware_inventory (hostname, cpu_info, memory_total, gpu_count, os_info, kernel_version, scan_timestamp)
    VALUES ('$NODE', '$CPU_INFO', $MEM_TOTAL, 0, '$OS_INFO', '$KERNEL', NOW())
    ON CONFLICT (hostname) DO UPDATE SET
        cpu_info = EXCLUDED.cpu_info,
        memory_total = EXCLUDED.memory_total,
        os_info = EXCLUDED.os_info,
        kernel_version = EXCLUDED.kernel_version,
        scan_timestamp = NOW();
SQL
done
```

### Task 3: Update Thermal Memory with Node Status

```sql
-- Insert CMDB entries for each node into thermal memory

-- REDFIN
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_redfin_' || now()::text),
    'CMDB ENTRY: REDFIN - AI Inference Node
Updated: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || '
Status: OPERATIONAL

Hardware:
- GPU: NVIDIA RTX 5090 (96GB VRAM)
- Role: vLLM inference, LLM Gateway, SAG UI

Services Running:
- vllm.service (port 8000)
- llm-gateway.service (port 8080)
- jr-executor.service
- jr-queue-worker.service
- VetAssist backend (port 8001)

Network:
- IP: 192.168.132.223
- VLAN: Compute tier

Key Paths:
- /ganuda/services/llm_gateway/
- /ganuda/vetassist/
- /ganuda/jr_executor/',
    'FRESH', 85.0, true,
    ARRAY['cmdb', 'redfin', 'infrastructure', 'gpu', 'vllm'],
    '{"type": "cmdb_entry", "node": "redfin", "scan_date": "2026-01-16"}'::jsonb
);

-- BLUEFIN
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_bluefin_' || now()::text),
    'CMDB ENTRY: BLUEFIN - Database Node
Updated: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || '
Status: OPERATIONAL

Hardware:
- Role: PostgreSQL database, persistent knowledge

Services Running:
- PostgreSQL 15 (zammad_production database)
- Grafana (port 3000)

Key Tables:
- thermal_memory_archive (5,200+ entries)
- jr_work_queue
- jr_task_announcements
- duyuktv_tickets
- hardware_inventory
- council_votes

Network:
- IP: 192.168.132.222
- VLAN: Compute tier',
    'FRESH', 85.0, true,
    ARRAY['cmdb', 'bluefin', 'infrastructure', 'postgresql', 'database'],
    '{"type": "cmdb_entry", "node": "bluefin", "scan_date": "2026-01-16"}'::jsonb
);

-- GREENFIN
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_greenfin_' || now()::text),
    'CMDB ENTRY: GREENFIN - Network Bridge
Updated: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || '
Status: OPERATIONAL

Role: Inter-VLAN router, gateway to security zones

Services Running:
- nftables firewall
- Squid proxy
- Promtail (log forwarding)

Network:
- IP: 192.168.132.224
- Bridges: VLAN 10, VLAN 20, Compute tier
- Critical path for silverfin/goldfin access',
    'FRESH', 85.0, true,
    ARRAY['cmdb', 'greenfin', 'infrastructure', 'router', 'firewall'],
    '{"type": "cmdb_entry", "node": "greenfin", "scan_date": "2026-01-16"}'::jsonb
);

-- SILVERFIN
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_silverfin_' || now()::text),
    'CMDB ENTRY: SILVERFIN - Identity Authority
Updated: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || '
Status: OPERATIONAL

Role: FreeIPA Identity + Secrets Management

Services Running:
- FreeIPA (CHEROKEE.LOCAL realm)
- 389 Directory Server
- Kerberos KDC
- Certificate Authority

Security:
- VLAN 10 (Identity tier)
- Tailscale access
- LUKS encrypted

Domain:
- Realm: CHEROKEE.LOCAL
- Manages: User authentication, host enrollment',
    'FRESH', 90.0, true,
    ARRAY['cmdb', 'silverfin', 'infrastructure', 'freeipa', 'identity', 'security'],
    '{"type": "cmdb_entry", "node": "silverfin", "scan_date": "2026-01-16"}'::jsonb
);

-- GOLDFIN
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_goldfin_' || now()::text),
    'CMDB ENTRY: GOLDFIN - PII Vault
Updated: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || '
Status: OPERATIONAL

Role: PII and interim PCI data storage

Databases:
- vetassist_pii: SSN, addresses, medical data
- vetassist_pci: Credit cards, billing (interim until platinumfin)

Security:
- VLAN 20 (Data tier)
- Tailscale access only
- LUKS encrypted
- PostgreSQL with pgcrypto

Integration:
- Presidio tokenization from redfin
- Token storage for PII redaction',
    'FRESH', 95.0, true,
    ARRAY['cmdb', 'goldfin', 'infrastructure', 'pii', 'vault', 'security'],
    '{"type": "cmdb_entry", "node": "goldfin", "scan_date": "2026-01-16"}'::jsonb
);
```

### Task 4: Add Missing Nodes to hardware_inventory

```sql
-- Ensure silverfin and goldfin exist in hardware_inventory
INSERT INTO hardware_inventory (hostname, os_info, scan_timestamp)
VALUES
    ('silverfin', 'Rocky Linux 9', NOW()),
    ('goldfin', 'Rocky Linux 9', NOW())
ON CONFLICT (hostname) DO UPDATE SET scan_timestamp = NOW();
```

### Task 5: Create CMDB Summary Entry

```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern, keywords, metadata)
VALUES (
    md5('cmdb_summary_' || now()::text),
    'CMDB REFRESH COMPLETE - January 16, 2026

FEDERATION INFRASTRUCTURE STATUS:

COMPUTE TIER:
- redfin: OPERATIONAL (GPU inference, vLLM, Gateway)
- bluefin: OPERATIONAL (PostgreSQL, Grafana)

NETWORK TIER:
- greenfin: OPERATIONAL (Inter-VLAN router, firewall)

SECURITY MOUNTAINS:
- silverfin (VLAN 10): OPERATIONAL (FreeIPA CHEROKEE.LOCAL)
- goldfin (VLAN 20): OPERATIONAL (PII vault)
- platinumfin (VLAN 30): PLANNED Q3 2026

MAC TIER:
- sasass: AVAILABLE (Mac Studio)
- sasass2: AVAILABLE (Mac Studio)
- tpm-macbook: ACTIVE (Claude Code CLI)

SERVICES:
- vLLM: active (port 8000)
- LLM Gateway: active (port 8080)
- jr-executor: active
- jr-queue-worker: active
- PostgreSQL: active
- FreeIPA: active

Last CMDB Refresh: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI'),
    'FRESH', 90.0, true,
    ARRAY['cmdb', 'summary', 'infrastructure', 'status', 'refresh'],
    '{"type": "cmdb_summary", "scan_date": "2026-01-16", "nodes_scanned": 7}'::jsonb
);
```

## Verification

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT hostname, TO_CHAR(scan_timestamp, 'YYYY-MM-DD HH24:MI') as scanned FROM hardware_inventory ORDER BY scan_timestamp DESC;"
```

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) as cmdb_entries FROM thermal_memory_archive WHERE keywords @> ARRAY['cmdb'] AND created_at > NOW() - INTERVAL '1 hour';"
```

---

*Cherokee AI Federation - For the Seven Generations*
