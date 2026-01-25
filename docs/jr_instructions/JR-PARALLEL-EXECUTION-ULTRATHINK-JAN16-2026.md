# ULTRATHINK: Parallel Task Execution - January 16, 2026

## Strategic Analysis

Four independent work streams can execute simultaneously without blocking each other:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION STREAMS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STREAM A                STREAM B              STREAM C                 │
│  VetAssist Hardening     Observability         Security                 │
│  ─────────────────       ─────────────         ────────                 │
│  │                       │                     │                        │
│  ├─► systemd service     ├─► OpenObserve       ├─► Secrets migration   │
│  │   (redfin)            │   (greenfin)        │   (silverfin)         │
│  │                       │                     │                        │
│  └─► goldfin token       └─► Log forwarding    └─► API key vault       │
│      integration             (all nodes)           setup                │
│                                                                         │
│  Target: redfin          Target: greenfin      Target: silverfin       │
│  Jr: Infrastructure      Jr: Infrastructure    Jr: Infrastructure      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why These Can Run in Parallel

| Stream | Dependencies | Conflicts | Safe to Parallel |
|--------|--------------|-----------|------------------|
| A: VetAssist systemd | None - local to redfin | None | ✅ |
| B: OpenObserve | None - new deployment | None | ✅ |
| C: Secrets migration | silverfin ready (✅) | None | ✅ |

---

## STREAM A: VetAssist Production Hardening

### A1: Create VetAssist Backend Systemd Service

**Target:** redfin
**File:** `/etc/systemd/system/vetassist-backend.service`

```ini
[Unit]
Description=VetAssist Backend API
After=network.target postgresql.service vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/vetassist/backend
Environment=PATH=/ganuda/vetassist/backend/venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/vetassist/backend
EnvironmentFile=/ganuda/vetassist/backend/.env
ExecStart=/ganuda/vetassist/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vetassist-backend

[Install]
WantedBy=multi-user.target
```

**Deployment:**
```bash
sudo cp /ganuda/scripts/systemd/vetassist-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vetassist-backend
sudo systemctl start vetassist-backend
sudo systemctl status vetassist-backend
```

### A2: VetAssist goldfin Token Integration

**Purpose:** Connect PIIService tokenization to goldfin vault storage

**Update** `/ganuda/vetassist/backend/.env`:
```bash
# goldfin PII Vault Connection
PII_VAULT_HOST=goldfin
PII_VAULT_PORT=5432
PII_VAULT_DB=vetassist_pii
PII_VAULT_USER=vetassist_app
PII_VAULT_PASSWORD=<from silverfin vault>
```

**Test connectivity:**
```bash
PGPASSWORD=$PII_VAULT_PASSWORD psql -h goldfin -U vetassist_app -d vetassist_pii -c "SELECT 1;"
```

---

## STREAM B: OpenObserve Log Management

### B1: Deploy OpenObserve on greenfin

**Target:** greenfin (network tier - sees all traffic)

```bash
# Install OpenObserve
curl -L https://raw.githubusercontent.com/openobserve/openobserve/main/download.sh | sh

# Create data directory
sudo mkdir -p /ganuda/openobserve/data
sudo chown dereadi:dereadi /ganuda/openobserve/data

# Create systemd service
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
sudo systemctl enable --now openobserve
```

### B2: Configure Log Forwarding from All Nodes

**Promtail config for each node** (`/etc/promtail/config.yml`):
```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

clients:
  - url: http://greenfin:5080/api/default/logs

scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: systemd
          host: ${HOSTNAME}
          __path__: /var/log/syslog

  - job_name: ganuda
    static_configs:
      - targets:
          - localhost
        labels:
          job: ganuda
          host: ${HOSTNAME}
          __path__: /ganuda/logs/*.log
```

---

## STREAM C: Secrets Migration to silverfin

### C1: Configure FreeIPA Vault for API Keys

**Target:** silverfin

```bash
# On silverfin, as admin
kinit admin

# Create vault container for Cherokee AI
ipa vault-add cherokee-ai-secrets --type=symmetric

# Store API keys
ipa vault-archive cherokee-ai-secrets \
  --data="$(cat << 'EOF'
{
  "llm_gateway_admin": "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5",
  "pii_vault_password": "<generate new>",
  "openobserve_admin": "CherokeeLogs2026!"
}
EOF
)"

# Grant access to service accounts
ipa vault-add-member cherokee-ai-secrets --users=vetassist-svc
```

### C2: Create Service Accounts

```bash
# Create service account for VetAssist
ipa user-add vetassist-svc \
  --first=VetAssist \
  --last=Service \
  --shell=/sbin/nologin \
  --password

# Create service account for monitoring
ipa user-add monitor-svc \
  --first=Monitor \
  --last=Service \
  --shell=/sbin/nologin \
  --password
```

### C3: Retrieve Secrets Script

**File:** `/ganuda/scripts/get-secrets.sh`
```bash
#!/bin/bash
# Retrieve secrets from silverfin FreeIPA vault
# Must have valid Kerberos ticket

SECRET_NAME=$1
ipa vault-retrieve cherokee-ai-secrets --out=/tmp/secrets.json
jq -r ".$SECRET_NAME" /tmp/secrets.json
rm -f /tmp/secrets.json
```

---

## Execution Plan

### Phase 1: Parallel Deployment (All streams start simultaneously)

| Stream | Task | Node | Command |
|--------|------|------|---------|
| A | VetAssist systemd | redfin | `systemctl enable --now vetassist-backend` |
| B | OpenObserve install | greenfin | `curl ... \| sh` |
| C | FreeIPA vault setup | silverfin | `ipa vault-add ...` |

### Phase 2: Integration (After Phase 1 completes)

| Task | Depends On | Command |
|------|------------|---------|
| Log forwarding | B complete | Deploy promtail to all nodes |
| Secrets retrieval | C complete | Test `get-secrets.sh` |
| VetAssist vault connection | A+C complete | Update .env with vault creds |

---

## Verification Checklist

```bash
# Stream A - VetAssist
systemctl is-active vetassist-backend
curl -s http://localhost:8001/health

# Stream B - OpenObserve
systemctl is-active openobserve
curl -s http://greenfin:5080/healthz

# Stream C - Secrets
ipa vault-show cherokee-ai-secrets
```

---

## Council Vote Reference

- Research prioritization: `c5c9b8e17a480e66`
- Quantum concepts: `17e643596102eac9`

---

*Cherokee AI Federation - For the Seven Generations*
*"Many hands make light work. Many Jrs make fast progress."*
