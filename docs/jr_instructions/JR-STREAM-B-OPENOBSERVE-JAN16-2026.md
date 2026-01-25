# JR Instruction: Stream B - OpenObserve Log Management

## Metadata
```yaml
task_id: stream_b_openobserve
priority: 1
parallel_stream: B
assigned_to: Infrastructure Jr.
target_node: greenfin
```

## Overview

Deploy OpenObserve on greenfin for centralized log management across the Cherokee AI Federation.

## Tasks

### Task 1: Install OpenObserve on greenfin

```bash
ssh greenfin << 'REMOTE'
cd /tmp
curl -L https://github.com/openobserve/openobserve/releases/download/v0.10.0/openobserve-v0.10.0-linux-amd64.tar.gz -o openobserve.tar.gz
tar xzf openobserve.tar.gz
sudo mv openobserve /usr/local/bin/
sudo chmod +x /usr/local/bin/openobserve
rm openobserve.tar.gz
echo "OpenObserve installed"
REMOTE
```

### Task 2: Create Data Directory

```bash
ssh greenfin << 'REMOTE'
sudo mkdir -p /ganuda/openobserve/data
sudo chown dereadi:dereadi /ganuda/openobserve/data
REMOTE
```

### Task 3: Create Systemd Service

```bash
ssh greenfin << 'REMOTE'
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

sudo systemctl daemon-reload
sudo systemctl enable openobserve
sudo systemctl start openobserve
REMOTE
```

## Verification

```bash
ssh greenfin "systemctl is-active openobserve && echo 'OpenObserve: ACTIVE'"
```

```bash
ssh greenfin "curl -s http://localhost:5080/healthz"
```

---

*Cherokee AI Federation - For the Seven Generations*
