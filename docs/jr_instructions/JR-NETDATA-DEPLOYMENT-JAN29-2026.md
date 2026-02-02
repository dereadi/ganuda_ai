# JR Instruction: Netdata Per-Node Deployment

**JR ID:** JR-NETDATA-DEPLOYMENT-JAN29-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr.
**Related:** ULTRATHINK-CLUSTER-INFRA-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE

---

## Objective

Deploy Netdata monitoring agents on all 6 Cherokee AI nodes for real-time metrics with ML-powered anomaly detection.

---

## Problem

- Limited per-node visibility
- health_monitor.py only checks service availability
- No ML-based anomaly detection
- Manual investigation required for performance issues

---

## Solution

Netdata provides:
- Zero-config installation
- Real-time metrics (1-second granularity)
- ML-powered anomaly detection
- Low resource usage (~2% CPU, ~100MB RAM)
- Streaming to central node

---

## Node Topology

| Node | IP | Role | Priority |
|------|-----|------|----------|
| redfin | 192.168.132.223 | GPU Server | P0 |
| bluefin | 192.168.132.222 | Database (Parent) | P0 |
| greenfin | 192.168.132.224 | Daemons | P0 |
| sasass | 192.168.132.241 | Mac Studio | P1 |
| silverfin | TBD | Secrets | P2 |
| goldfin | TBD | PII Vault | P2 |

---

## Implementation

### Step 1: Install Netdata Parent (bluefin)

On bluefin (192.168.132.222):

```bash
# Install Netdata
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-install.sh
chmod +x /tmp/netdata-install.sh
sudo /tmp/netdata-install.sh --dont-wait

# Configure as parent (receiver)
sudo tee -a /etc/netdata/stream.conf << 'EOF'
[cherokee-federation]
  enabled = yes
  allow from = 192.168.132.*
  default memory mode = dbengine
  health enabled by default = auto
  default postpone alarms on connect seconds = 60
EOF

# Restart Netdata
sudo systemctl restart netdata

# Verify
curl -s http://localhost:19999/api/v1/info | jq .version
```

### Step 2: Install Netdata on GPU Node (redfin)

On redfin (192.168.132.223):

```bash
# Install
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-install.sh
sudo /tmp/netdata-install.sh --dont-wait

# Configure streaming to parent
sudo tee /etc/netdata/stream.conf << 'EOF'
[stream]
  enabled = yes
  destination = 192.168.132.222:19999
  api key = cherokee-federation
  timeout seconds = 60
  buffer size bytes = 1048576
  reconnect delay seconds = 5
  initial clock resync iterations = 60
EOF

# Enable GPU monitoring
sudo tee /etc/netdata/go.d/nvidia_smi.conf << 'EOF'
jobs:
  - name: gpu0
    binary_path: /usr/bin/nvidia-smi
EOF

# Restart
sudo systemctl restart netdata
```

### Step 3: Install on greenfin (Daemons)

On greenfin (192.168.132.224):

```bash
# Install
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-install.sh
sudo /tmp/netdata-install.sh --dont-wait

# Configure streaming
sudo tee /etc/netdata/stream.conf << 'EOF'
[stream]
  enabled = yes
  destination = 192.168.132.222:19999
  api key = cherokee-federation
EOF

# Enable PostgreSQL monitoring (if applicable)
sudo tee /etc/netdata/go.d/postgres.conf << 'EOF'
jobs:
  - name: local
    dsn: 'postgres://claude:jawaseatlasers2@localhost/zammad_production?sslmode=disable'
EOF

sudo systemctl restart netdata
```

### Step 4: Install on sasass (Mac Studio)

On sasass (192.168.132.241):

```bash
# Install via Homebrew
brew install netdata

# Configure streaming
sudo tee /usr/local/etc/netdata/stream.conf << 'EOF'
[stream]
  enabled = yes
  destination = 192.168.132.222:19999
  api key = cherokee-federation
EOF

# Start service
brew services start netdata
```

### Step 5: Configure Alerts

On bluefin (parent), create `/etc/netdata/health.d/cherokee.conf`:

```yaml
# Cherokee AI Specific Alerts

# GPU Temperature
alarm: gpu_temperature_high
    on: nvidia_smi.gpu_temperature
lookup: average -5m unaligned
 units: celsius
 every: 30s
  warn: $this > 75
  crit: $this > 85
 delay: down 5m multiplier 1.5 max 1h
  info: GPU temperature is too high
    to: sysadmin

# vLLM Memory
alarm: vllm_memory_high
    on: apps.mem
lookup: average -5m unaligned of vllm
 units: MiB
 every: 30s
  warn: $this > 28000
  crit: $this > 30000
  info: vLLM memory usage approaching limit

# PostgreSQL Connections
alarm: postgres_connections_high
    on: postgres.connections
lookup: average -5m unaligned
 units: connections
 every: 30s
  warn: $this > 80
  crit: $this > 95
  info: PostgreSQL connections nearing limit

# Research Queue Backup
alarm: research_queue_backup
    on: custom.research_queue_depth
lookup: average -5m unaligned
 units: jobs
 every: 1m
  warn: $this > 10
  crit: $this > 20
  info: Research job queue backing up
```

### Step 6: Create Custom Metrics Plugin

For Cherokee-specific metrics, create `/etc/netdata/python.d/cherokee.chart.py`:

```python
#!/usr/bin/env python3
"""Cherokee AI custom metrics for Netdata."""

from bases.FrameworkServices.SimpleService import SimpleService
import psycopg2

ORDER = ['research_queue', 'jr_tasks']

CHARTS = {
    'research_queue': {
        'options': [None, 'Research Queue Depth', 'jobs', 'cherokee', 'cherokee.research_queue', 'area'],
        'lines': [
            ['pending', 'pending', 'absolute'],
            ['running', 'running', 'absolute'],
        ]
    },
    'jr_tasks': {
        'options': [None, 'Jr Task Status', 'tasks', 'cherokee', 'cherokee.jr_tasks', 'stacked'],
        'lines': [
            ['pending', 'pending', 'absolute'],
            ['completed', 'completed', 'absolute'],
            ['failed', 'failed', 'absolute'],
        ]
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS
        self.conn = None

    def check(self):
        try:
            self.conn = psycopg2.connect(
                host='192.168.132.222',
                database='zammad_production',
                user='claude',
                password='jawaseatlasers2'
            )
            return True
        except:
            return False

    def get_data(self):
        data = {}
        try:
            cur = self.conn.cursor()

            # Research queue
            cur.execute("SELECT status, COUNT(*) FROM research_jobs GROUP BY status")
            for row in cur.fetchall():
                if row[0] in ['pending', 'running']:
                    data[row[0]] = row[1]

            # Jr tasks (last 24h)
            cur.execute("""
                SELECT status, COUNT(*)
                FROM jr_work_queue
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY status
            """)
            for row in cur.fetchall():
                data[row[0]] = row[1]

            cur.close()
        except:
            self.conn = None

        return data or None
```

---

## Verification

1. Access Netdata dashboard:
   ```
   http://192.168.132.222:19999
   ```

2. Check all nodes streaming:
   ```bash
   curl -s http://localhost:19999/api/v1/info | jq '.mirrored_hosts'
   ```

3. Verify GPU metrics (redfin):
   ```bash
   curl -s "http://192.168.132.222:19999/api/v1/data?chart=nvidia_smi.gpu_temperature&after=-60"
   ```

---

## Files Summary

| File | Node | Action |
|------|------|--------|
| `/etc/netdata/stream.conf` | All | CREATE/MODIFY |
| `/etc/netdata/health.d/cherokee.conf` | bluefin | CREATE |
| `/etc/netdata/python.d/cherokee.chart.py` | bluefin | CREATE |
| `/etc/netdata/go.d/nvidia_smi.conf` | redfin | CREATE |

---

## Access

- Parent Dashboard: http://192.168.132.222:19999
- Per-node (if needed): http://{node}:19999

---

FOR SEVEN GENERATIONS
