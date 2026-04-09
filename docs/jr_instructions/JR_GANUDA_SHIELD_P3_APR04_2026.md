# Jr Build Instruction: Ganuda Shield P-3 — Agent Core + Collection API

## Priority: P1 — First Revenue Product
## Date: April 4, 2026
## Council Vote: #7cfe224b87cb349f (APPROVED 12-0-1)
## Classification: PRIVATE — Commercial License — NOT Open Source
## Long Man Phase: P-3 (Foundation)

---

## What We're Building

A transparent endpoint monitoring agent that captures behavioral patterns on workstations and reports to a central collection server. The employee KNOWS the agent is running. Data NEVER leaves the customer's network.

**This is NOT a keylogger. This is behavioral pattern analysis with consent.**

---

## P-3 Scope: Agent + Collection API + Basic Storage

### Component 1: Shield Agent (runs on each workstation)

Build `/ganuda/products/ganuda-shield/agent/`

#### 1A: Consent Engine (`consent.py`)

**The agent WILL NOT START without recorded consent.** This is non-negotiable.

First launch flow:
1. Display consent window (Tkinter on Linux, native dialog on macOS)
2. Explain in plain language:
   - "This application monitors your work activity to protect company data"
   - "What is captured: application usage patterns, clipboard types (not content), file access patterns, network connection patterns"
   - "What is NOT captured: keystrokes, screen content, personal messages, browsing history"
   - "You can view your own activity dashboard at any time"
   - "Your data stays on [company name]'s server and is never sent to any third party"
3. Employee must click "I understand and consent" — not just "OK"
4. Record consent: timestamp, employee ID, machine ID, agent version, consent text hash
5. Store consent locally AND send to collection server
6. Generate consent receipt file on desktop: `ganuda-shield-consent-YYYY-MM-DD.txt`

Jurisdiction-aware (set in config):
- `jurisdiction: gdpr` → adds right to withdraw, data deletion rights, DPO contact
- `jurisdiction: ccpa` → adds California-specific disclosures
- `jurisdiction: standard` → base consent flow

#### 1B: Activity Monitor (`monitor.py`)

Pattern capture — NOT raw surveillance:

**Always captured (baseline patterns):**
```python
{
    "timestamp": "2026-04-04T10:15:30",
    "machine_id": "workstation-047",
    "employee_id": "jsmith",
    "active_application": "Microsoft Outlook",     # App name only, NOT content
    "application_category": "email",               # Classified category
    "activity_type": "typing",                     # typing, idle, mouse, switching
    "idle_duration_seconds": 0,                    # How long idle before this activity
    "clipboard_type": "text",                      # Type only, NOT content
    "clipboard_sensitive": false,                  # Was it a credential pattern?
    "network_connections_active": 3,               # Count only
    "usb_devices_connected": ["keyboard", "mouse"], # Device types, not data
    "session_hours_today": 6.5,                    # Time tracking
}
```

**NOT captured by default:**
- Keystroke content (NEVER unless escalated by anomaly AND admin authorization)
- Screen content or screenshots (NEVER unless escalated)
- File contents (NEVER — only file access PATTERNS: "opened quarterly-report.xlsx")
- Email/message content (NEVER)
- Browsing URLs (NEVER by default — only domain-level if configured: "visited github.com" not the full path)

**Captured on ANOMALY TRIGGER only (requires admin authorization):**
- Screenshot (single frame, with employee notification: "Screenshot captured due to security event")
- File transfer details (what files, where, how large)
- Detailed network connections (IPs, ports, domains)
- Clipboard CONTENT (with "[ESCALATED]" flag visible to employee on their dashboard)

The employee dashboard shows a visible indicator when escalated monitoring is active: "Enhanced monitoring active — triggered by [reason]"

#### 1C: Transport (`transport.py`)

- Batch reports every 60 seconds (not real-time — reduces network load)
- Encrypt payload with AES-256 before sending
- TLS to collection server endpoint
- If server unreachable: buffer locally (up to 24 hours), retry with exponential backoff
- Agent-side encryption key derived from server-provided token at registration
- Each report is signed with agent's machine ID + timestamp to prevent spoofing

#### 1D: Tray Icon (`tray.py`)

- System tray icon showing Shield is running
- Green = normal monitoring
- Yellow = anomaly detected (employee can click to see what triggered it)
- Red = enhanced monitoring active (employee knows immediately)
- Right-click menu:
  - "View my dashboard" → opens browser to employee self-dashboard
  - "View consent" → shows original consent text
  - "About Ganuda Shield" → version, contact info
  - "Report false alarm" → if employee thinks an anomaly is wrong, they can flag it
- The tray icon CANNOT be hidden. If someone kills the process, the server notices (heartbeat missing) and flags it as an anomaly.

#### 1E: Agent Config (`config.yaml`)

```yaml
shield:
  server_url: "https://shield.company.internal:8443"
  machine_id: "auto"  # auto-generated on first run
  employee_id: "prompt"  # ask on first run
  jurisdiction: "standard"  # gdpr, ccpa, standard
  
capture:
  interval_seconds: 60
  clipboard_types: true  # capture type, never content
  clipboard_content: false  # ONLY true on admin-authorized escalation
  application_tracking: true
  idle_detection: true
  network_connections: "count"  # "count" or "detail" (detail = escalation only)
  usb_monitoring: true
  file_access_patterns: true
  file_access_content: false  # NEVER
  screenshots: false  # ONLY on anomaly + admin auth
  
transport:
  batch_interval_seconds: 60
  buffer_max_hours: 24
  encryption: "aes256"
  
tray:
  visible: true  # CANNOT be set to false
  show_anomalies: true
  employee_dashboard_url: "https://shield.company.internal:8443/me"
```

### Component 2: Collection Server (Podman container on customer's server)

Build `/ganuda/products/ganuda-shield/server/`

#### 2A: Collection API (`api.py`)

FastAPI receiving agent reports:
- `POST /api/v1/register` — agent registration + consent recording
- `POST /api/v1/report` — receive encrypted activity batch
- `POST /api/v1/heartbeat` — agent alive signal (every 60s)
- `GET /api/v1/config/{machine_id}` — agent pulls its config (allows remote escalation)
- `POST /api/v1/anomaly/ack` — admin acknowledges/dismisses anomaly
- `POST /api/v1/employee/false-alarm` — employee flags false positive

Authentication: API key per agent, issued at registration.

#### 2B: Database Schema (`schema.sql`)

```sql
-- Consent records (immutable audit trail)
CREATE TABLE consent_log (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    consent_timestamp TIMESTAMPTZ NOT NULL,
    consent_text_hash VARCHAR(64) NOT NULL,
    jurisdiction VARCHAR(20) NOT NULL,
    agent_version VARCHAR(20) NOT NULL,
    ip_address INET,
    withdrawn_at TIMESTAMPTZ  -- GDPR right to withdraw
);

-- Activity reports (rolling retention)
CREATE TABLE activity_reports (
    id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    report_timestamp TIMESTAMPTZ NOT NULL,
    report_data JSONB NOT NULL,  -- the activity batch
    anomaly_score REAL DEFAULT 0.0,
    escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Anomalies (flagged events)
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- info, warning, critical
    description TEXT,
    evidence JSONB,  -- escalated details if authorized
    admin_action VARCHAR(20),  -- ack, dismiss, investigate
    employee_flagged_false BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent registry
CREATE TABLE agents (
    machine_id VARCHAR(100) PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    api_key VARCHAR(64) NOT NULL,
    last_heartbeat TIMESTAMPTZ,
    agent_version VARCHAR(20),
    os_type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',  -- active, silent, decommissioned
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Retention policy: auto-delete activity_reports older than configured retention (default 90 days)
-- Consent records: NEVER deleted (audit trail)
-- Anomalies: retained for 1 year minimum
```

#### 2C: Anomaly Engine (`anomaly.py`)

Baseline + deviation model:
1. Build behavioral baseline per employee over first 14 days (learning period)
2. After baseline established, flag deviations:

| Anomaly Type | Trigger | Severity |
|---|---|---|
| `off_hours_access` | Activity outside normal working hours | warning |
| `bulk_file_access` | >50 file accesses in 10 minutes | critical |
| `credential_clipboard` | Sensitive pattern in clipboard type | warning |
| `usb_data_transfer` | USB storage device + file access spike | critical |
| `missing_heartbeat` | Agent hasn't reported in >5 minutes | warning |
| `agent_killed` | Process terminated unexpectedly | critical |
| `unusual_network` | Connections to unusual external IPs | warning |
| `unusual_application` | Application not in baseline set | info |

LLM analysis (P-2): send anomaly context to local LLM for natural-language risk assessment. P-3 uses rule-based detection only.

#### 2D: Basic Admin Dashboard (`dashboard.py`)

P-3 scope — simple but functional:
- List of all registered agents with heartbeat status (green/yellow/red)
- Anomaly feed: newest first, filterable by severity
- Per-employee activity summary (hours, app categories, anomaly count)
- Click anomaly → detail view with context
- Click employee → activity timeline

Employee self-dashboard (P-2) — just a placeholder page in P-3:
- "Your activity dashboard is coming soon. Your data is being collected transparently per your consent."

#### 2E: Containerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8443
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8443", "--ssl-keyfile", "/certs/key.pem", "--ssl-certfile", "/certs/cert.pem"]
```

### Component 3: Deployment (`deploy/`)

#### 3A: Agent Installer

Linux: `curl -sSL https://shield.company.internal/install.sh | bash`
- Creates systemd service
- Runs consent flow
- Registers with server
- Starts monitoring

macOS: `.pkg` installer or `brew install` from private tap
- Requests Accessibility permissions (transparent, OS-enforced)
- Creates LaunchAgent

Windows (stretch): `.msi` installer — P-1 or later

#### 3B: Server Deployment

```bash
# One-command deployment on customer's server
podman build -t ganuda-shield-server .
podman run -d --name shield-server \
  -p 8443:8443 \
  -v shield-data:/data \
  -v shield-certs:/certs \
  ganuda-shield-server
```

---

## Constraints

- **PRIVATE REPO.** Commercial license. NOT MIT. NOT open source.
- **Consent is non-negotiable.** Agent will not start without recorded consent.
- **Transparency is non-negotiable.** Tray icon cannot be hidden. Employee dashboard must exist.
- **Content is never captured by default.** Patterns only. Escalation requires admin auth + employee notification.
- **Data sovereignty is non-negotiable.** ALL data on customer's server. Zero cloud.
- **90-day retention default.** Consent records never deleted. Activity auto-purges.
- **Crawdad audit required** before ANY customer deployment.

### Component 4: Evidence Vault (DUPLO addition — Partner Apr 4 2026)

Build `/ganuda/products/ganuda-shield/server/evidence_vault.py`

**When an anomaly escalates to evidence, the data changes classification entirely.** Different rules. Different storage. Different access. Different retention.

#### 4A: Evidence Schema (`evidence_schema.sql`)

```sql
-- SEPARATE SCHEMA with own encryption key
CREATE SCHEMA IF NOT EXISTS evidence;

-- Evidence records (IMMUTABLE — no UPDATE, no DELETE)
CREATE TABLE evidence.records (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,          -- groups evidence to an investigation
    anomaly_id INTEGER REFERENCES anomalies(id),
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    evidence_type VARCHAR(50) NOT NULL,    -- screenshot, file_transfer, clipboard_content, network_detail
    evidence_data BYTEA NOT NULL,          -- encrypted with evidence-specific Fernet key
    pii_classification VARCHAR(20),        -- none, contains_pii, contains_phi, contains_financial
    capture_timestamp TIMESTAMPTZ NOT NULL,
    capture_hash VARCHAR(64) NOT NULL,     -- SHA-256 of raw evidence at capture time
    integrity_verified BOOLEAN DEFAULT TRUE,
    legal_hold BOOLEAN DEFAULT FALSE,      -- overrides ALL retention policies
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- REVOKE modification rights — append only
REVOKE UPDATE, DELETE ON evidence.records FROM ALL;
-- Only the evidence_writer role can INSERT
-- Only the evidence_reader role can SELECT
-- Only the evidence_admin role can set legal_hold

-- Chain of custody log (who accessed what, when, why)
CREATE TABLE evidence.custody_log (
    id BIGSERIAL PRIMARY KEY,
    evidence_id BIGINT REFERENCES evidence.records(id),
    accessed_by VARCHAR(100) NOT NULL,     -- who viewed/exported
    access_type VARCHAR(20) NOT NULL,      -- view, export, legal_hold_set, legal_hold_released
    access_reason TEXT,                     -- required: why are you accessing this evidence?
    source_ip INET,
    access_timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- REVOKE modification on custody log too — immutable audit trail
REVOKE UPDATE, DELETE ON evidence.custody_log FROM ALL;

-- Evidence encryption keys (separate from main DB encryption)
-- Key stored in /ganuda/config/.evidence_vault_key (permissions 600, root-owned)
-- NEVER stored in the database itself
```

#### 4B: Evidence Collection Flow (`evidence_collector.py`)

The escalation process — NO evidence collected without authorization:

```
Anomaly detected
    ↓
Security team reviews PATTERN (no content yet)
    ↓
Security team contacts HR/Legal
    ↓
HR/Legal authorizes evidence collection (logged with authorizer ID + reason)
    ↓
Admin sets escalation flag on the agent via /api/v1/config/{machine_id}
    ↓
Agent begins detail capture:
    - Screenshots (captured with timestamp + SHA-256 hash at capture time)
    - File transfer details (filenames, sizes, destinations)
    - Clipboard CONTENT (encrypted immediately)
    - Network connection details (IPs, ports, domains)
    ↓
Employee notified: tray icon turns RED, dashboard shows "Enhanced monitoring active"
    ↓
Evidence encrypted with vault key and stored in evidence.records
    ↓
Every access to evidence logged in evidence.custody_log
```

**Requirements:**
- Authorization record must exist BEFORE evidence collection starts
- Employee MUST be notified when escalated monitoring begins (tray icon RED)
- All evidence encrypted with evidence-specific key (NOT the main DB key)
- SHA-256 hash of raw evidence computed at CAPTURE time (agent-side), stored alongside
- Integrity can be verified at any time: re-hash stored evidence, compare to capture hash
- Legal hold prevents any automated purge — only evidence_admin can release

#### 4C: Evidence Export (`evidence_export.py`)

Generates forensic-ready package for law enforcement or legal proceedings:

```
evidence_export_CASEID_YYYY-MM-DD/
    manifest.json           # Case details, evidence list, export timestamp
    chain_of_custody.csv    # Complete access log for all evidence in this case
    evidence/
        001_screenshot_2026-04-04T14-23-17.png
        001_screenshot_2026-04-04T14-23-17.sha256  # hash file
        002_file_transfer_2026-04-04T14-25-00.json
        002_file_transfer_2026-04-04T14-25-00.sha256
        ...
    integrity_verification.json   # All hashes verified at export time
    export_signature.sha256       # Hash of the entire package
```

**The export function:**
1. Verify integrity of ALL evidence (re-hash, compare to capture hash)
2. Generate manifest with case details
3. Export custody log as CSV
4. Decrypt evidence files (requires evidence_admin + reason logged)
5. Write individual hash files alongside each evidence file
6. Hash the entire package
7. Log the export in custody_log

#### 4D: PII Handling

Even a bad actor's PII is protected:
- Evidence containing PII tagged with `pii_classification`
- Access to PII-tagged evidence requires additional justification in custody_log
- GDPR: data subject access request must be honored UNLESS active investigation exception applies
- Export packages with PII flagged in manifest: "Contains PII — handle per jurisdiction requirements"
- Retention: PII evidence follows jurisdiction rules even under legal hold (GDPR max retention applies)

#### 4E: Canary Self-Audit Integration

The Security Canary runs INSIDE the evidence vault to validate its own security:
- Are evidence tables truly append-only? (Try UPDATE, verify it fails)
- Is the encryption key properly secured? (Check permissions on key file)
- Are custody logs being written for every access?
- Is the evidence schema network-isolated from the main activity schema?
- Report findings to the admin dashboard

**The tool that validates the tool. Both hands on the shield.**

---

## Testing Requirements

- [ ] Agent installs and runs consent flow
- [ ] Agent captures activity patterns correctly (verify NO content leaks)
- [ ] Transport encrypts and delivers to collection server
- [ ] Server stores reports in PostgreSQL
- [ ] Heartbeat monitoring detects agent kills
- [ ] Anomaly engine flags test scenarios (off-hours, bulk file, USB)
- [ ] Tray icon shows correct state (green/yellow/red)
- [ ] Admin dashboard shows agents and anomalies
- [ ] Employee can flag false alarm
- [ ] GDPR consent flow includes withdrawal right
- [ ] Buffer works when server is unreachable
- [ ] Podman container builds and runs clean
- [ ] Evidence vault: append-only enforced (UPDATE/DELETE fails)
- [ ] Evidence vault: encryption uses separate key from main DB
- [ ] Evidence vault: SHA-256 hash at capture matches re-hash at retrieval
- [ ] Evidence vault: custody log records every access with reason
- [ ] Evidence vault: legal hold prevents auto-purge
- [ ] Evidence vault: export generates forensic package with integrity verification
- [ ] Evidence vault: PII classification tags present on sensitive evidence
- [ ] Evidence vault: Canary self-audit catches misconfigurations
- [ ] Evidence collection requires authorization record BEFORE capture begins
- [ ] Employee tray icon turns RED when escalated monitoring active

## Regression Test Suite

Build `/ganuda/products/ganuda-shield/tests/`:

```python
# test_consent.py — consent flow completes, records correctly, blocks without consent
# test_capture.py — patterns captured, NO content leaked, sensitive types flagged
# test_transport.py — encryption works, buffer works, retry works
# test_anomaly.py — each anomaly type triggers correctly on test data
# test_tray.py — icon states correct, menu works, can't be hidden
# test_retention.py — old data purges, consent records persist
# test_escalation.py — escalation requires auth, employee notified, dashboard shows indicator
```

---

## Long Man Summary

| Phase | What Ships | Milestone |
|---|---|---|
| **P-3 (NOW)** | Agent + consent + collection API + basic anomaly + admin dashboard + evidence vault | "Data is flowing securely, evidence is court-ready" |
| P-2 | LLM anomaly analysis + employee self-dashboard + onboarding walkthrough | "Intelligence is working" |
| P-1 | Podman packaging + deployment scripts + pricing page + marketing | "Ready for first customer" |
| P-Day | First customer deployment | "Revenue starts" |

---

*Both hands on the shield. The company and the employee protecting the same thing.*

*For Seven Generations — revenue edition.*
