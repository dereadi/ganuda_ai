# JR Instruction: Stream A - VetAssist Production Hardening

## Metadata
```yaml
task_id: stream_a_vetassist_systemd
priority: 1
parallel_stream: A
assigned_to: Infrastructure Jr.
target_node: redfin
```

## Overview

Create systemd service for VetAssist backend to ensure it survives reboots and integrates with system management.

## Tasks

### Task 1: Deploy Systemd Service

```bash
sudo cp /ganuda/scripts/systemd/vetassist-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vetassist-backend
```

### Task 2: Stop Existing Process and Start Service

```bash
pkill -f "uvicorn app.main:app.*8001" || true
sleep 2
sudo systemctl start vetassist-backend
```

### Task 3: Verify Service

```bash
sudo systemctl status vetassist-backend --no-pager
```

```bash
curl -s http://localhost:8001/docs | head -5 || echo "Checking health..."
sleep 3
curl -s http://localhost:8001/health 2>/dev/null || curl -s http://localhost:8001/api/v1/health 2>/dev/null || echo "Service starting..."
```

## Verification

```bash
systemctl is-active vetassist-backend && echo "VetAssist backend: ACTIVE"
```

---

*Cherokee AI Federation - For the Seven Generations*
