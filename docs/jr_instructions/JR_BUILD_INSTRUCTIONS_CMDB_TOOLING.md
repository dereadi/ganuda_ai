# Jr Build Instructions: CMDB Tooling

**Task ID:** JR-CMDB-TOOLING-001
**Priority:** High
**Assigned Specialist:** Gecko (Technical Integration)
**Date:** 2025-12-25

---

## Context

The Cherokee AI Federation has deployed many services across 6 nodes but **ZERO** entries tagged as `cmdb_entry` in thermal_memory_archive. This means:
- No authoritative record of what's deployed where
- No version tracking
- No dependency mapping
- Ansible playbooks can't reference current state

## Objective

Build CMDB tooling to track all deployed services, their configurations, dependencies, and status.

---

## Requirements

### 1. CMDB Entry Schema

Create a standardized CMDB entry structure in thermal_memory_archive:

```sql
-- Tags array must include 'cmdb_entry' and service type
-- Metadata jsonb should include:
{
  "cmdb_type": "service" | "database" | "cron" | "config" | "hardware",
  "cmdb_id": "CMDB-service-node",  -- e.g., CMDB-llm_gateway-redfin
  "service_name": "llm_gateway",
  "node": "redfin",
  "port": 8080,
  "version": "1.1",
  "status": "running" | "stopped" | "degraded",
  "path": "/ganuda/services/llm_gateway/",
  "systemd_unit": "llm-gateway.service",
  "dependencies": ["vllm", "postgresql"],
  "api_endpoints": ["/v1/chat/completions", "/health"],
  "config_files": ["/ganuda/services/llm_gateway/config.yaml"],
  "last_verified": "2025-12-25T10:00:00",
  "owner": "dereadi",
  "documentation": "KB-2025-0001"
}
```

### 2. CMDB Registration Script

Create `/ganuda/scripts/cmdb_register.py` on redfin:

```python
#!/usr/bin/env python3
"""
Register or update a CMDB entry in thermal memory.

Usage:
  python cmdb_register.py --type service \
    --name llm_gateway \
    --node redfin \
    --port 8080 \
    --version "1.1" \
    --status running \
    --path "/ganuda/services/llm_gateway/" \
    --systemd "llm-gateway.service" \
    --deps "vllm,postgresql"
"""

import argparse
import psycopg2
import hashlib
import json
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def register_cmdb_entry(args):
    cmdb_id = f"CMDB-{args.name}-{args.node}"

    content = f"""# CMDB: {args.name} on {args.node}

**CMDB ID:** {cmdb_id}
**Type:** {args.type}
**Status:** {args.status}
**Last Verified:** {datetime.now().isoformat()}

## Service Details
- **Node:** {args.node}
- **Port:** {args.port or 'N/A'}
- **Version:** {args.version or 'Unknown'}
- **Path:** {args.path or 'N/A'}
- **Systemd Unit:** {args.systemd or 'N/A'}

## Dependencies
{args.deps.replace(',', ', ') if args.deps else 'None specified'}

## Configuration Files
{args.configs or 'None specified'}
"""

    metadata = {
        "cmdb_type": args.type,
        "cmdb_id": cmdb_id,
        "service_name": args.name,
        "node": args.node,
        "port": args.port,
        "version": args.version,
        "status": args.status,
        "path": args.path,
        "systemd_unit": args.systemd,
        "dependencies": args.deps.split(',') if args.deps else [],
        "config_files": args.configs.split(',') if args.configs else [],
        "last_verified": datetime.now().isoformat(),
        "owner": args.owner or "dereadi"
    }

    memory_hash = hashlib.sha256(f"{cmdb_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Check if entry exists
    cur.execute("""
        SELECT id FROM thermal_memory_archive
        WHERE 'cmdb_entry' = ANY(tags)
        AND metadata->>'cmdb_id' = %s
    """, (cmdb_id,))
    existing = cur.fetchone()

    if existing:
        # Update existing entry
        cur.execute("""
            UPDATE thermal_memory_archive
            SET original_content = %s,
                metadata = %s,
                last_access = NOW(),
                temperature_score = 0.8
            WHERE id = %s
        """, (content, json.dumps(metadata), existing[0]))
        print(f"Updated CMDB entry: {cmdb_id} (ID: {existing[0]})")
    else:
        # Create new entry
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, current_stage, temperature_score,
             created_at, tags, metadata, keywords)
            VALUES (%s, %s, 'warm', 0.8, NOW(),
                    ARRAY['cmdb_entry', %s, %s], %s, %s)
            RETURNING id
        """, (
            memory_hash,
            content,
            args.type,
            args.node,
            json.dumps(metadata),
            [args.name.lower(), args.node.lower(), args.type.lower()]
        ))
        entry_id = cur.fetchone()[0]
        print(f"Created CMDB entry: {cmdb_id} (ID: {entry_id})")

    conn.commit()
    conn.close()
    return cmdb_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Register CMDB entry')
    parser.add_argument('--type', required=True,
                        choices=['service', 'database', 'cron', 'config', 'hardware'])
    parser.add_argument('--name', required=True, help='Service/resource name')
    parser.add_argument('--node', required=True, help='Node hostname')
    parser.add_argument('--port', type=int, help='Port number')
    parser.add_argument('--version', help='Version string')
    parser.add_argument('--status', default='running',
                        choices=['running', 'stopped', 'degraded', 'unknown'])
    parser.add_argument('--path', help='Installation path')
    parser.add_argument('--systemd', help='Systemd unit name')
    parser.add_argument('--deps', help='Comma-separated dependencies')
    parser.add_argument('--configs', help='Comma-separated config file paths')
    parser.add_argument('--owner', default='dereadi', help='Owner username')

    args = parser.parse_args()
    register_cmdb_entry(args)
```

### 3. CMDB Query Script

Create `/ganuda/scripts/cmdb_query.py`:

```python
#!/usr/bin/env python3
"""
Query CMDB for services and resources.

Usage:
  python cmdb_query.py --node redfin
  python cmdb_query.py --service llm_gateway
  python cmdb_query.py --status running
  python cmdb_query.py --all
"""

import argparse
import psycopg2
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def query_cmdb(node=None, service=None, status=None, show_all=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT metadata->>'cmdb_id',
               metadata->>'service_name',
               metadata->>'node',
               metadata->>'port',
               metadata->>'status',
               metadata->>'version',
               metadata->>'last_verified'
        FROM thermal_memory_archive
        WHERE 'cmdb_entry' = ANY(tags)
    """
    params = []

    if node:
        query += " AND metadata->>'node' = %s"
        params.append(node)
    if service:
        query += " AND metadata->>'service_name' ILIKE %s"
        params.append(f'%{service}%')
    if status:
        query += " AND metadata->>'status' = %s"
        params.append(status)

    query += " ORDER BY metadata->>'node', metadata->>'service_name'"

    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()

    if not results:
        print("No CMDB entries found.")
        return

    # Print table header
    print(f"\n{'CMDB ID':<35} {'Service':<20} {'Node':<12} {'Port':<8} {'Status':<10} {'Version':<10}")
    print('=' * 100)

    for cmdb_id, svc, nd, port, stat, ver, verified in results:
        print(f"{cmdb_id or 'N/A':<35} {svc or 'N/A':<20} {nd or 'N/A':<12} {port or 'N/A':<8} {stat or 'N/A':<10} {ver or 'N/A':<10}")

    print(f"\nTotal: {len(results)} entries")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query CMDB')
    parser.add_argument('--node', help='Filter by node')
    parser.add_argument('--service', help='Filter by service name')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--all', action='store_true', help='Show all entries')

    args = parser.parse_args()
    query_cmdb(args.node, args.service, args.status, args.all)
```

### 4. Initial CMDB Population

Use this data to seed the CMDB:

| Node | Service | Port | Status |
|------|---------|------|--------|
| redfin | vllm | 8000 | running |
| redfin | llm_gateway | 8080 | running |
| redfin | sag_ui | 4000 | running |
| redfin | kanban | 3001 | running |
| redfin | hive_mind_bidding | - | running |
| bluefin | postgresql | 5432 | running |
| bluefin | grafana | 3000 | running |
| greenfin | promtail | - | running |

### 5. CMDB Auto-Discovery Hook

Create `/ganuda/lib/cmdb_discovery.py` that:
- Scans systemd units on each node
- Checks listening ports
- Updates CMDB entries with current status
- Flags services that are in CMDB but not running

---

## Acceptance Criteria

1. [ ] `cmdb_register.py` script deployed to `/ganuda/scripts/`
2. [ ] `cmdb_query.py` script deployed to `/ganuda/scripts/`
3. [ ] Initial CMDB population complete (minimum 8 entries)
4. [ ] Scripts tested and working
5. [ ] CMDB entries visible in thermal memory with proper tags

---

## Dependencies

- Python 3.x with psycopg2
- PostgreSQL access to bluefin
- SSH access to all nodes for discovery

## Estimated Complexity

Medium - SQL and Python scripting, network scanning for discovery.

---

*For Seven Generations*
