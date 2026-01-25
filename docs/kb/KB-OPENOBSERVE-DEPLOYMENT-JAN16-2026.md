# KB: OpenObserve Deployment on greenfin

**Date:** January 16, 2026
**Category:** Infrastructure / Logging
**Node:** greenfin
**Status:** Active

---

## Overview

OpenObserve provides centralized log management for the Cherokee AI Federation.

## Service Details

| Item | Value |
|------|-------|
| URL | http://greenfin:5080 |
| Admin Email | admin@cherokee.local |
| Admin Password | CherokeeLogs2026! |
| Data Directory | /ganuda/openobserve/data |
| Service | openobserve.service |

## Installation Steps

1. Download and install binary:
```bash
curl -L https://github.com/openobserve/openobserve/releases/download/v0.10.0/openobserve-v0.10.0-linux-amd64.tar.gz -o /tmp/openobserve.tar.gz
tar xzf /tmp/openobserve.tar.gz -C /tmp
sudo mv /tmp/openobserve /usr/local/bin/
sudo chmod +x /usr/local/bin/openobserve
```

2. Create data directory:
```bash
sudo mkdir -p /ganuda/openobserve/data
sudo chown dereadi:dereadi /ganuda/openobserve/data
```

3. Create systemd service:
```bash
sudo tee /etc/systemd/system/openobserve.service << 'EOF'
[Unit]
Description=OpenObserve Log Management
After=network.target

[Service]
Type=simple
User=dereadi
Environment=ZO_DATA_DIR=/ganuda/openobserve/data
Environment=ZO_ROOT_USER_EMAIL=admin@cherokee.local
Environment=ZO_ROOT_USER_PASSWORD=CherokeeLogs2026!
ExecStart=/usr/local/bin/openobserve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

4. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now openobserve
```

## Verification

```bash
systemctl is-active openobserve
curl -s http://localhost:5080/healthz  # Returns {"status":"ok"}
```

## Log Forwarding (Future)

Configure Promtail on each node to forward logs:

```yaml
# /etc/promtail/config.yml
clients:
  - url: http://greenfin:5080/api/default/logs

scrape_configs:
  - job_name: ganuda
    static_configs:
      - targets: [localhost]
        labels:
          job: ganuda
          host: ${HOSTNAME}
          __path__: /ganuda/logs/*.log
```

## Deployment Script

Location: `/ganuda/scripts/deploy-openobserve-greenfin.sh`

## Related

- JR Instruction: `/ganuda/docs/jr_instructions/JR-STREAM-B-OPENOBSERVE-JAN16-2026.md`
- Parallel Execution Plan: `/ganuda/docs/jr_instructions/JR-PARALLEL-EXECUTION-ULTRATHINK-JAN16-2026.md`

---

*Cherokee AI Federation - For the Seven Generations*
