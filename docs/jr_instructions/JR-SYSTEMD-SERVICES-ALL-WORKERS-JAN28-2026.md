# JR Instruction: Systemd Services for All Jr Workers

**JR ID:** JR-SYSTEMD-SERVICES-ALL-WORKERS-JAN28-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr.
**Ultrathink:** ULTRATHINK-PHASE3-PRODUCTION-HARDENING-JAN28-2026.md

---

## Objective

Create and install systemd services for all Jr worker types to enable managed auto-restart, journald logging, and proper service dependencies.

---

## Files to Create

| File | Description |
|------|-------------|
| `/ganuda/scripts/systemd/jr-se.service` | Software Engineer Jr. worker |
| `/ganuda/scripts/systemd/jr-it-triad.service` | IT Triad Jr. worker |
| `/ganuda/scripts/systemd/jr-research.service` | Research Jr. worker |
| `/ganuda/scripts/systemd/jr-infra.service` | Infrastructure Jr. worker |

---

## Service Template

### Software Engineer Jr.

Create `/ganuda/scripts/systemd/jr-se.service`:

```ini
[Unit]
Description=Cherokee AI Jr - Software Engineer
After=network.target llm-gateway.service vllm.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -u jr_queue_worker.py "Software Engineer Jr."
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-se

# Resource limits
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### IT Triad Jr.

Create `/ganuda/scripts/systemd/jr-it-triad.service`:

```ini
[Unit]
Description=Cherokee AI Jr - IT Triad
After=network.target llm-gateway.service vllm.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -u jr_queue_worker.py "it_triad_jr"
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-it-triad

MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### Research Jr.

Create `/ganuda/scripts/systemd/jr-research.service`:

```ini
[Unit]
Description=Cherokee AI Jr - Research
After=network.target llm-gateway.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -u jr_queue_worker.py "Research Jr."
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-research

MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### Infrastructure Jr.

Create `/ganuda/scripts/systemd/jr-infra.service`:

```ini
[Unit]
Description=Cherokee AI Jr - Infrastructure
After=network.target llm-gateway.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -u jr_queue_worker.py "Infrastructure Jr."
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-infra

MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

---

## Installation Script

Create `/ganuda/scripts/install_jr_services.sh`:

```bash
#!/bin/bash
# Install Jr worker systemd services

set -e

SYSTEMD_DIR=/etc/systemd/system
SCRIPTS_DIR=/ganuda/scripts/systemd

echo "Installing Jr worker services..."

# Link services
for service in jr-se jr-it-triad jr-research jr-infra; do
    if [ -f "$SCRIPTS_DIR/${service}.service" ]; then
        sudo ln -sf "$SCRIPTS_DIR/${service}.service" "$SYSTEMD_DIR/${service}.service"
        echo "  Linked ${service}.service"
    fi
done

# Reload systemd
sudo systemctl daemon-reload

# Enable services
for service in jr-se jr-it-triad jr-research jr-infra; do
    sudo systemctl enable ${service}.service
    echo "  Enabled ${service}.service"
done

echo "Done. Start services with: sudo systemctl start jr-se jr-it-triad jr-research jr-infra"
```

---

## Verification

```bash
# Check service status
systemctl status jr-se jr-it-triad jr-research jr-infra

# View logs
journalctl -u jr-se -f

# Check all Jr logs
journalctl -u "jr-*" --since "1 hour ago"
```

---

## Rollback

```bash
# Stop and disable services
sudo systemctl stop jr-se jr-it-triad jr-research jr-infra
sudo systemctl disable jr-se jr-it-triad jr-research jr-infra

# Remove links
sudo rm /etc/systemd/system/jr-*.service
sudo systemctl daemon-reload
```

---

FOR SEVEN GENERATIONS
