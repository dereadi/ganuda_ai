# Jr Instructions: Centralized Log Management with OpenObserve

**Council Vote**: Pending - recommend Infrastructure Jr review
**Priority**: P2 (creature comfort - improves operational visibility)
**Assigned To**: Infrastructure Jr.
**Created**: 2025-12-18

## Context

The Cherokee AI Federation currently has logs scattered across nodes:
- `/ganuda/logs/` on redfin (352MB+ files, no rotation)
- Service logs in `/tmp/` (lost on reboot)
- No centralized search capability
- No alerting on log patterns

## Why OpenObserve

| Feature | OpenObserve | Elasticsearch | Loki |
|---------|-------------|---------------|------|
| Storage Cost | 140x lower | Baseline | 10x lower |
| Query Language | SQL | DSL | LogQL |
| Single Binary | Yes | No | No |
| Air-Gapped | Yes | Yes | Yes |
| Memory Usage | Low | High | Medium |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   redfin    │     │  bluefin    │     │  greenfin   │
│  (services) │     │ (database)  │     │  (daemons)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │    Vector/Fluent Bit (log shippers)   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   OpenObserve   │
                  │  (on bluefin)   │
                  │   Port 5080     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Grafana Link   │
                  │  (dashboards)   │
                  └─────────────────┘
```

## Tasks

### Task 1: Deploy OpenObserve on Bluefin

**File**: `/ganuda/docker/openobserve/docker-compose.yml`

```yaml
version: '3.8'
services:
  openobserve:
    image: public.ecr.aws/zinclabs/openobserve:latest
    container_name: openobserve
    restart: unless-stopped
    ports:
      - "5080:5080"
    environment:
      - ZO_ROOT_USER_EMAIL=cherokee@federation.local
      - ZO_ROOT_USER_PASSWORD=${OPENOBSERVE_PASSWORD}
      - ZO_DATA_DIR=/data
    volumes:
      - openobserve_data:/data
    networks:
      - cherokee_net

volumes:
  openobserve_data:

networks:
  cherokee_net:
    external: true
```

**Verification**:
```bash
curl -s http://192.168.132.222:5080/healthz
# Should return: {"status":"ok"}
```

### Task 2: Configure Log Shippers on Each Node

**File**: `/ganuda/scripts/install_vector.sh`

Vector is a lightweight log shipper written in Rust.

```bash
#!/bin/bash
# Install Vector log shipper

curl -sSL https://sh.vector.dev | bash -s -- -y

cat > /etc/vector/vector.toml << 'EOF'
[sources.ganuda_logs]
type = "file"
include = ["/ganuda/logs/*.log"]
read_from = "beginning"

[sources.journald]
type = "journald"
current_boot_only = true
include_units = ["vllm", "llm-gateway", "kanban"]

[transforms.add_metadata]
type = "remap"
inputs = ["ganuda_logs", "journald"]
source = '''
.node = "${HOSTNAME}"
.federation = "cherokee"
'''

[sinks.openobserve]
type = "http"
inputs = ["add_metadata"]
uri = "http://192.168.132.222:5080/api/default/default/_json"
method = "post"
auth.strategy = "basic"
auth.user = "cherokee@federation.local"
auth.password = "${OPENOBSERVE_PASSWORD}"
encoding.codec = "json"
EOF

systemctl enable vector
systemctl start vector
```

### Task 3: Add Log Rotation

**File**: `/ganuda/scripts/logrotate_ganuda.conf`

```
/ganuda/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 dereadi dereadi
    postrotate
        # Signal services to reopen log files if needed
        killall -HUP python3 2>/dev/null || true
    endscript
}
```

Install:
```bash
sudo cp /ganuda/scripts/logrotate_ganuda.conf /etc/logrotate.d/ganuda
sudo logrotate -f /etc/logrotate.d/ganuda  # Test run
```

### Task 4: Create Thermal Memory Log Dashboard

Add OpenObserve as Grafana data source, then create dashboard for:
- Error rate by service
- Thermal memory access patterns
- Council vote latency
- Jr task execution times
- API gateway request volume

### Task 5: Configure Alerts

In OpenObserve, create alerts for:
- `ERROR` count > 10 in 5 minutes
- Service restart detected
- Database connection failures
- Memory threshold breaches

### Task 6: Seed to Thermal Memory

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, current_stage, temperature_score
) VALUES (
    md5('log_management_openobserve_' || NOW()::text),
    'LOG MANAGEMENT: OpenObserve deployed on bluefin:5080. Vector shippers on all nodes. SQL queries for logs. Retention: 7 days compressed. Alerts configured for ERROR patterns.',
    'FRESH',
    90
);
```

## Success Criteria

1. [ ] OpenObserve accessible at http://192.168.132.222:5080
2. [ ] Logs flowing from all 3 Linux nodes
3. [ ] Log rotation working (no files > 100MB)
4. [ ] Grafana dashboard showing log metrics
5. [ ] Alert fires on test ERROR injection
6. [ ] Thermal memory updated with deployment info

## Air-Gap Notes

For air-gapped deployment:
1. Pre-pull Docker image: `docker pull public.ecr.aws/zinclabs/openobserve:latest`
2. Save: `docker save openobserve:latest > openobserve.tar`
3. Transfer to bluefin, load: `docker load < openobserve.tar`
4. Vector binary can be downloaded once and copied to nodes

## References

- OpenObserve Docs: https://openobserve.ai/docs/
- Vector Config: https://vector.dev/docs/
- GitHub: https://github.com/openobserve/openobserve

---
*For Seven Generations - Cherokee AI Federation*
