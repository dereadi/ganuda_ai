# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Estimated SP**: [number]
**Target Node**: [redfin/bluefin/greenfin/etc]
**Port**: [service port]

---

## Objective

[What service is being deployed and why]

## Prerequisites

- [ ] Code exists at [path]
- [ ] Dependencies installed: [list]
- [ ] Config in place: [config file path]
- [ ] Port [NNNN] not in use

## Implementation

### Step 1: Create systemd unit file

**File**: `/etc/systemd/system/[service-name].service`

```ini
[Unit]
Description=[Service description]
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=[path]
ExecStart=[command]
Restart=on-failure
RestartSec=5
Environment=[KEY=VALUE]

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable [service-name]
sudo systemctl start [service-name]
```

### Step 3: Add to Fire Guard

In `/ganuda/scripts/fire_guard.py`, add health check for port [NNNN].

## Verification

```bash
# Service running
systemctl is-active [service-name]

# Health endpoint
curl -s http://localhost:[PORT]/health | python3 -m json.tool

# Logs clean
journalctl -u [service-name] --no-pager -n 20
```

## Rollback

```bash
sudo systemctl stop [service-name]
sudo systemctl disable [service-name]
```
