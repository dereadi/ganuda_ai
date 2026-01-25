# JR Instruction: Create jr-queue-worker Systemd Service

## Overview

The `jr_work_queue` table tasks are not being executed because there's no daemon processing them. The existing `jr-executor.service` runs `jr_task_executor.py` which uses the `jr_task_announcements` table (bidding system).

Need to create a systemd service for `jr_queue_worker.py`.

## Problem

| Table | Daemon | Status |
|-------|--------|--------|
| `jr_task_announcements` | `jr_task_executor.py` | Running (jr-executor.service) |
| `jr_work_queue` | `jr_queue_worker.py` | **NOT RUNNING** |

Tasks queued via `jr_work_queue` are marked complete without execution.

## Solution

Create `/etc/systemd/system/jr-queue-worker.service`:

```bash
sudo tee /etc/systemd/system/jr-queue-worker.service << 'EOF'
[Unit]
Description=Cherokee AI Jr Queue Worker
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_queue_worker.py "it_triad_jr"
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-queue-worker

[Install]
WantedBy=multi-user.target
EOF
```

## Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable jr-queue-worker
sudo systemctl start jr-queue-worker
sudo systemctl status jr-queue-worker
```

## Verification

```bash
systemctl is-active jr-queue-worker
```

```bash
journalctl -u jr-queue-worker -n 20 --no-pager
```

```bash
ps aux | grep jr_queue_worker
```

## Task Consolidation (Future)

Consider consolidating `jr_task_announcements` and `jr_work_queue` into a single table/daemon to avoid confusion. The bidding system could use the same queue with a `bidding_round` column.

---

*Cherokee AI Federation - For the Seven Generations*
