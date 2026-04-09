# Jr Instruction: Cross-Node Deployment — How to Deploy Code Across the Federation

## Priority: REFERENCE — All Jrs Must Learn This
## Date: April 2, 2026
## Written By: TPM (after deploying Stoneclad Demo API because Jrs couldn't)

---

## The Problem

Jrs can write code to redfin's local filesystem. But "completed" means the code is DEPLOYED and RUNNING on the target node, not just written to disk. Writing a FastAPI app to /ganuda/backend/ and marking "done" is not deployment. Deployment means the service is listening on the target node and responding to requests.

## The Federation Nodes

| Node | IP (WireGuard) | IP (LAN) | Role | Sudo Available |
|------|---------------|----------|------|----------------|
| redfin | 10.100.0.1 | 192.168.132.223 | GPU inference, services | Yes (FreeIPA) |
| bluefin | 10.100.0.2 | 192.168.132.222 | PostgreSQL database | Yes (FreeIPA) |
| owlfin | 10.100.0.5 | 192.168.132.170 | DMZ web (Caddy) | Yes (FreeIPA) |
| eaglefin | 10.100.0.6 | 192.168.132.84 | DMZ web (Caddy) | Yes (FreeIPA) |
| sasass | — | 192.168.132.241 | Mac, FARA/Ollama | No scoped sudo |
| sasass2 | — | 192.168.132.242 | Mac, Medicine Woman | No scoped sudo |

## NOPASSWD Commands (FreeIPA-Scoped on Linux Nodes)

These run WITHOUT a password prompt:
- `sudo cat` — read protected files
- `sudo tee` — write files as root (pipe content to tee)
- `sudo cp` — copy files
- `sudo mkdir` — create directories
- `sudo chmod` — change permissions
- `sudo systemctl` — start/stop/enable/reload services
- `sudo wg` — WireGuard management

## How to Deploy a Python Service to a Remote Node

### Step 1: Write the code locally on redfin
```python
# /ganuda/api/my_service.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "alive"}
```

### Step 2: Create the target directory on the remote node
```bash
ssh dereadi@10.100.0.5 'sudo mkdir -p /ganuda/api'
```

### Step 3: Copy the file via sudo tee (scp may fail on permissions)
```bash
cat /ganuda/api/my_service.py | ssh dereadi@10.100.0.5 'sudo tee /ganuda/api/my_service.py > /dev/null'
```

### Step 4: Install dependencies if needed
```bash
ssh dereadi@10.100.0.5 '~/.local/bin/pip3 install --user --break-system-packages fastapi uvicorn psycopg2-binary'
```
Note: owlfin and eaglefin may not have pip. Bootstrap first:
```bash
ssh dereadi@10.100.0.5 'curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --user --break-system-packages'
```

### Step 5: Create a systemd service
```bash
cat << 'SERVICE' | ssh dereadi@10.100.0.5 'sudo tee /etc/systemd/system/my-service.service > /dev/null'
[Unit]
Description=My Service
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/api
Environment=PATH=/home/dereadi/.local/bin:/usr/bin:/bin
ExecStart=/home/dereadi/.local/bin/uvicorn my_service:app --host 0.0.0.0 --port 8500
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE
```

### Step 6: Enable and start
```bash
ssh dereadi@10.100.0.5 'sudo systemctl daemon-reload && sudo systemctl enable my-service && sudo systemctl start my-service'
```

### Step 7: Verify
```bash
ssh dereadi@10.100.0.5 'sudo systemctl is-active my-service'
curl -s http://10.100.0.5:8500/health
```

### Step 8: Wire Caddy (if DMZ-facing)
Update the Caddyfile to proxy traffic:
```bash
# Read current config, modify, write back via sudo tee
ssh dereadi@10.100.0.5 'sudo cat /etc/caddy/Caddyfile' > /tmp/caddy_current.txt
# Edit locally, then:
cat /tmp/caddy_updated.txt | ssh dereadi@10.100.0.5 'sudo tee /etc/caddy/Caddyfile > /dev/null'
ssh dereadi@10.100.0.5 'sudo systemctl reload caddy'
```

## Common Gotchas

1. **scp fails with "Permission denied"** — Use `sudo tee` instead
2. **pip3 not found** — Bootstrap pip with get-pip.py first
3. **PEP 668 "externally managed environment"** — Add `--break-system-packages`
4. **Two Caddy blocks for same domain** — Merge into one block with `handle` directives
5. **"Task completed" but nothing running** — Always verify with `systemctl is-active` and `curl`

## Definition of Done (for deployment tasks)

A task is NOT complete until:
- [ ] Code is on the TARGET node (not just redfin)
- [ ] Dependencies are installed on the target node
- [ ] Service is running (systemctl is-active = active)
- [ ] Endpoint responds to requests (curl returns expected data)
- [ ] If DMZ-facing: Caddy proxy is configured and reloaded

Writing code to redfin and marking "done" is a DC-9 violation — wasted joules.

---

*For Seven Generations.*
