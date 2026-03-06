# Jr Instruction: Service Registry — Port Map Single Source of Truth

**Task**: Create a service_registry table and seed it with all known node:port:service mappings
**Kanban**: New item (create during execution)
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Owl finding**: SAG health check has stale ports (Grafana:3000 = actually Kanban, kanban:5000 = actually :3001)

## Context

We have hardware_inventory and software_cmdb but no port/service registry.
Port assignments are scattered across MEMORY.md, nftables configs, SAG health checks, and service files.
When ports change (and they do), stale references cause false health data.

The service_registry becomes the single source of truth that SAG health, nftables rules,
monitoring dashboards, and documentation all read from.

## Steps

### Step 1: Create the table

File: `/ganuda/scripts/migrations/service_registry.sql`

Create `/ganuda/scripts/migrations/service_registry.sql`

```text
-- Service Registry: port/endpoint map per node
-- Owl audit finding Mar 5, 2026 — stale ports in SAG health check
CREATE TABLE IF NOT EXISTS service_registry (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(64) NOT NULL,
    service_name VARCHAR(128) NOT NULL,
    port INTEGER NOT NULL,
    protocol VARCHAR(10) DEFAULT 'tcp',
    bind_address VARCHAR(64) DEFAULT '0.0.0.0',
    systemd_unit VARCHAR(128),
    health_check_url VARCHAR(256),
    description TEXT,
    network_plane VARCHAR(20) DEFAULT 'management',
    access_scope VARCHAR(20) DEFAULT 'internal',
    is_active BOOLEAN DEFAULT true,
    added_date TIMESTAMP DEFAULT now(),
    last_verified TIMESTAMP,
    notes TEXT,
    UNIQUE(hostname, port, protocol)
);

COMMENT ON TABLE service_registry IS 'Single source of truth for all node:port:service mappings. Feeds SAG health, nftables, monitoring.';
COMMENT ON COLUMN service_registry.network_plane IS 'management (132.x), dmz (30.x), wireguard (10.100.x), tailscale (100.x)';
COMMENT ON COLUMN service_registry.access_scope IS 'internal, federation, public, dmz';
```

### Step 2: Seed with known services

File: `/ganuda/scripts/migrations/seed_service_registry.py`

Create `/ganuda/scripts/migrations/seed_service_registry.py`

```python
"""Seed service_registry with known port assignments.

Sources: MEMORY.md, nftables configs, systemd units, TPM audit Mar 5 2026.
"""
import os
import psycopg2

DB_CONFIG = {
    "host": os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222"),
    "dbname": os.environ.get("CHEROKEE_DB_NAME", "zammad_production"),
    "user": os.environ.get("CHEROKEE_DB_USER", "claude"),
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
    "port": int(os.environ.get("CHEROKEE_DB_PORT", "5432")),
}

SERVICES = [
    # REDFIN (192.168.132.223)
    ("redfin", "vLLM (Qwen2.5-72B-AWQ)", 8000, "tcp", "0.0.0.0", "vllm.service",
     "http://192.168.132.223:8000/health", "Primary LLM inference", "management", "internal"),
    ("redfin", "LLM Gateway", 8080, "tcp", "0.0.0.0", "llm-gateway.service",
     "http://192.168.132.223:8080/health", "Council + routing gateway", "management", "internal"),
    ("redfin", "SAG Unified Interface", 4000, "tcp", "0.0.0.0", "sag.service",
     "http://192.168.132.223:4000/v1/harness/health", "Ops console + harness endpoint", "management", "federation"),
    ("redfin", "Kanban Board (Next.js)", 3000, "tcp", "127.0.0.1", None,
     "http://192.168.132.223:3000/", "Kanban web UI (NOT Grafana)", "management", "internal"),
    ("redfin", "Kanban API", 3001, "tcp", "127.0.0.1", None,
     None, "Kanban API backend", "management", "internal"),
    ("redfin", "Jr Executor (Pipeline A)", None, "tcp", None, "jr-se.service",
     None, "TEG-enabled work queue processor", "management", "internal"),
    ("redfin", "Jr Executor (Pipeline B)", None, "tcp", None, "jr-executor.service",
     None, "Bidding/announcements processor", "management", "internal"),
    ("redfin", "PostgreSQL", 5432, "tcp", "0.0.0.0", None,
     None, "Local PG (if any) — primary DB is on bluefin", "management", "internal"),

    # BLUEFIN (192.168.132.222)
    ("bluefin", "PostgreSQL", 5432, "tcp", "0.0.0.0", "postgresql.service",
     None, "Primary federation database", "management", "internal"),
    ("bluefin", "vLLM VLM (Qwen2-VL-7B-AWQ)", 8090, "tcp", "0.0.0.0", "vlm-bluefin.service",
     None, "Vision language model inference", "management", "internal"),
    ("bluefin", "YOLO World Service", 8091, "tcp", "0.0.0.0", "yolo-world.service",
     None, "Object detection service", "management", "internal"),
    ("bluefin", "VLM Adapter", 8092, "tcp", "0.0.0.0", "vlm-adapter.service",
     None, "VLM request adapter/proxy", "management", "internal"),
    ("bluefin", "Optic Nerve", None, "tcp", None, "optic-nerve.service",
     None, "Camera vision pipeline", "management", "internal"),

    # GREENFIN (192.168.132.224)
    ("greenfin", "Embedding Server (BGE-large)", 8003, "tcp", "0.0.0.0", "cherokee-embedding.service",
     "http://192.168.132.224:8003/health", "BGE-large-en-v1.5 1024d embeddings", "management", "internal"),
    ("greenfin", "OpenObserve", 5080, "tcp", "0.0.0.0", "openobserve.service",
     None, "Log aggregation and monitoring platform", "management", "internal"),
    ("greenfin", "Promtail", 9080, "tcp", "127.0.0.1", "promtail.service",
     None, "Log shipper to OpenObserve", "management", "internal"),

    # BMASASS (100.103.27.106 Tailscale / 192.168.132.21 LAN)
    ("bmasass", "MLX DeepSeek-R1-Llama-70B", 8800, "tcp", "0.0.0.0", None,
     "http://100.103.27.106:8800/v1/models", "M4 Max 128GB, launchd service", "tailscale", "federation"),

    # OWLFIN (192.168.132.170 mgmt / 192.168.30.2 DMZ)
    ("owlfin", "Caddy Web Server", 80, "tcp", "0.0.0.0", "caddy.service",
     "http://192.168.132.170/", "DMZ web, HTTP redirect", "dmz", "public"),
    ("owlfin", "Caddy Web Server (TLS)", 443, "tcp", "0.0.0.0", "caddy.service",
     "https://ganuda.us/", "DMZ web, HTTPS primary", "dmz", "public"),
    ("owlfin", "Web Materializer", None, "tcp", None, "web-materializer.service",
     None, "Polls DB, writes to Caddy webroot", "management", "internal"),

    # EAGLEFIN (192.168.132.84 mgmt / 192.168.30.3 DMZ)
    ("eaglefin", "Caddy Web Server", 80, "tcp", "0.0.0.0", "caddy.service",
     "http://192.168.132.84/", "DMZ web failover, HTTP redirect", "dmz", "public"),
    ("eaglefin", "Caddy Web Server (TLS)", 443, "tcp", "0.0.0.0", "caddy.service",
     "https://ganuda.us/", "DMZ web failover, HTTPS", "dmz", "public"),
    ("eaglefin", "Web Materializer", None, "tcp", None, "web-materializer.service",
     None, "Polls DB, writes to Caddy webroot", "management", "internal"),

    # SILVERFIN (192.168.10.10 VLAN 10)
    ("silverfin", "FreeIPA LDAP", 389, "tcp", "0.0.0.0", "ipa.service",
     None, "FreeIPA LDAP (behind greenfin bridge)", "vlan10", "internal"),
    ("silverfin", "FreeIPA LDAPS", 636, "tcp", "0.0.0.0", "ipa.service",
     None, "FreeIPA LDAPS", "vlan10", "internal"),
    ("silverfin", "FreeIPA Web UI", 443, "tcp", "0.0.0.0", "httpd.service",
     None, "FreeIPA admin console", "vlan10", "internal"),
]

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for svc in SERVICES:
        hostname, name, port, proto, bind, unit, health, desc, plane, scope = svc
        cur.execute("""
            INSERT INTO service_registry
                (hostname, service_name, port, protocol, bind_address, systemd_unit,
                 health_check_url, description, network_plane, access_scope, last_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (hostname, port, protocol) DO UPDATE SET
                service_name = EXCLUDED.service_name,
                systemd_unit = EXCLUDED.systemd_unit,
                health_check_url = EXCLUDED.health_check_url,
                description = EXCLUDED.description,
                network_plane = EXCLUDED.network_plane,
                access_scope = EXCLUDED.access_scope,
                last_verified = now()
        """, (hostname, name, port, proto, bind, unit, health, desc, plane, scope))

    conn.commit()
    print(f"Seeded {len(SERVICES)} services into service_registry")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
```

Note: Some services have port=None (no listening port, background workers). The UNIQUE constraint
is on (hostname, port, protocol) so these will need the INSERT adjusted to handle NULL ports.
The Jr should change the UNIQUE constraint to allow NULLs or filter them out of the insert.

## Verification

```text
source /ganuda/config/secrets.env
psql -h 192.168.132.222 -U claude -d zammad_production -c "
  SELECT hostname, port, service_name, network_plane
  FROM service_registry
  WHERE is_active = true
  ORDER BY hostname, port;"
```

Expected: All known services listed with correct ports, planes, and scopes.
