# Jr Build Instructions: Privacy Statement
## Priority: HIGH - Trust Documentation

---

## Objective

Create a clear, honest privacy statement that explains:
1. What data Ganuda collects
2. Where data is stored
3. Who has access
4. What we do NOT do

**Key Principle**: Users trust us with their AI interactions. Be transparent.

---

## Document 1: PRIVACY.md (User-Facing)

Location: `/ganuda/docs/PRIVACY.md`

```markdown
# Ganuda Privacy Statement

**Last Updated**: December 2025

## Overview

Ganuda is designed for privacy. When you self-host Ganuda, your data stays on your infrastructure. We do not collect, transmit, or have access to your prompts, responses, or usage data.

## What Ganuda Stores

When you run Ganuda, the following data is stored **on your own infrastructure**:

### API Request Logs

| Data | Stored | Purpose | Retention |
|------|--------|---------|-----------|
| Request timestamp | Yes | Audit trail | Configurable (default 90 days) |
| API key ID | Yes | Usage tracking | Configurable |
| Endpoint called | Yes | Analytics | Configurable |
| Response status | Yes | Error tracking | Configurable |
| Token counts | Yes | Quota enforcement | Configurable |
| Latency | Yes | Performance monitoring | Configurable |
| Request body | Optional | Debugging | Configurable (default OFF) |
| Response body | No | N/A | Never stored |

### User Data

| Data | Stored | Purpose |
|------|--------|---------|
| Username | Yes | Authentication |
| Password hash | Yes | Authentication (never plaintext) |
| Session tokens | Yes | Active sessions |
| Login timestamps | Yes | Security audit |

### Inference Data

| Data | Stored | Where |
|------|--------|-------|
| Prompts | Passed through | Not retained by Ganuda |
| Responses | Passed through | Not retained by Ganuda |
| Conversation history | Your application | Not stored by Ganuda |

## What Ganuda Does NOT Store

- **Prompt content**: Your actual prompts are not logged by default
- **Response content**: AI responses are never logged
- **Personal information**: We don't collect names, emails, or identifiers
- **Usage analytics**: No telemetry sent to external services
- **IP addresses**: Optional, disabled by default

## Data Flow

```
Your Application
      │
      ▼
┌─────────────────┐
│  Ganuda Gateway │ ◄─── Logs: timestamp, tokens, latency
│                 │      Does NOT log: prompt/response content
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Inference       │ ◄─── Your configured backend
│ (OpenAI/vLLM)   │      (data handling per their policy)
└─────────────────┘
```

## Third-Party Services

Ganuda connects to your configured inference backend:

### If Using OpenAI

Your prompts are sent to OpenAI's API. See [OpenAI's Privacy Policy](https://openai.com/privacy/).

### If Using Anthropic

Your prompts are sent to Anthropic's API. See [Anthropic's Privacy Policy](https://www.anthropic.com/privacy).

### If Using Local vLLM

Your prompts stay entirely on your infrastructure. No external transmission.

## Your Controls

### Disable Request Logging

In `ganuda.yaml`:
```yaml
logging:
  audit:
    enabled: false
```

### Reduce Log Retention

```yaml
logging:
  audit:
    retention_days: 7  # Keep logs only 7 days
```

### Disable IP Logging

```yaml
logging:
  audit:
    log_ip: false
```

## Data Deletion

### Delete All Logs

```bash
docker exec -it ganuda-postgres psql -U ganuda -c "TRUNCATE api_audit_log;"
```

### Delete User Data

```bash
docker exec -it ganuda-postgres psql -U ganuda -c "DELETE FROM sag_users WHERE username = 'user-to-delete';"
```

### Full Data Wipe

```bash
make clean  # Removes all containers and volumes
```

## Security

- All passwords are hashed (never stored in plaintext)
- Session tokens are cryptographically random
- Database credentials are configurable
- HTTPS supported for production deployments

## Air-Gapped Operation

Ganuda can run completely offline:

1. Use local vLLM for inference
2. No external network connections required
3. All data stays within your network

## Contact

For privacy questions, open an issue on [GitHub](https://github.com/cherokee-ai/ganuda/issues).

---

*Built with privacy in mind by Cherokee AI Federation*
```

---

## Document 2: DATA_HANDLING.md (Technical Reference)

Location: `/ganuda/docs/DATA_HANDLING.md`

```markdown
# Ganuda Data Handling Reference

Technical details on how Ganuda handles data.

## Database Schema

### api_audit_log

Stores API request metadata (NOT content).

```sql
CREATE TABLE api_audit_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64),      -- Unique request identifier
    key_id VARCHAR(64),          -- API key used (hashed)
    endpoint VARCHAR(200),       -- e.g., /v1/chat/completions
    method VARCHAR(10),          -- GET, POST, etc.
    status_code INTEGER,         -- HTTP response code
    tokens_used INTEGER,         -- Token count
    latency_ms INTEGER,          -- Response time
    ip_address VARCHAR(45),      -- Optional, configurable
    created_at TIMESTAMP         -- When request occurred
    -- NOTE: request_body and response NOT stored by default
);
```

### What's NOT in the audit log

- `messages` array content (your prompts)
- `choices` array content (AI responses)
- `system` prompts
- Any PII from your application

## Logging Levels

### Level: MINIMAL (Recommended for privacy)

```yaml
logging:
  audit:
    enabled: true
    log_requests: false   # Don't log request bodies
    log_responses: false  # Don't log response bodies
    log_ip: false         # Don't log IP addresses
```

Stored: timestamp, endpoint, status, tokens, latency

### Level: STANDARD (Default)

```yaml
logging:
  audit:
    enabled: true
    log_requests: false
    log_responses: false
    log_ip: true
```

Stored: Above + IP address

### Level: DEBUG (Development only)

```yaml
logging:
  audit:
    enabled: true
    log_requests: true    # WARNING: Logs prompt content
    log_responses: false
    log_ip: true
```

Stored: Above + full request body

**WARNING**: Debug level logs prompt content. Use only for troubleshooting.

## Data Retention

### Automatic Cleanup

Configure in `ganuda.yaml`:

```yaml
logging:
  audit:
    retention_days: 90
```

Cleanup runs via cron job:

```sql
DELETE FROM api_audit_log WHERE created_at < NOW() - INTERVAL '90 days';
```

### Manual Cleanup

```bash
# Delete logs older than 30 days
docker exec -it ganuda-postgres psql -U ganuda -c \
  "DELETE FROM api_audit_log WHERE created_at < NOW() - INTERVAL '30 days';"

# Count remaining logs
docker exec -it ganuda-postgres psql -U ganuda -c \
  "SELECT COUNT(*) FROM api_audit_log;"
```

## Encryption

### At Rest

- Database: Depends on your PostgreSQL configuration
- Recommend: Enable PostgreSQL TDE or disk encryption

### In Transit

- API: HTTPS supported (configure SSL certificates)
- Internal: Docker network isolation

### Passwords

- Hashed with PBKDF2-SHA256 (600,000 iterations)
- Never stored in plaintext
- Salt per password

## Session Handling

```sql
CREATE TABLE sag_sessions (
    session_id VARCHAR(64),  -- Random token (secrets.token_hex(32))
    user_id INTEGER,
    expires_at TIMESTAMP,    -- Auto-expires after 24 hours
    ip_address VARCHAR(45),  -- For security audit
    created_at TIMESTAMP
);
```

Sessions are:
- Cryptographically random
- Time-limited (configurable)
- Invalidated on logout
- Cleaned up automatically

## Inference Backend Data Flow

### Request Path

```
1. Client sends request to Ganuda
2. Ganuda validates API key
3. Ganuda logs metadata (NOT content)
4. Ganuda forwards to inference backend
5. Backend processes and responds
6. Ganuda returns response to client
7. Response content NOT logged
```

### What Ganuda Sees

- Full request (temporarily, in memory)
- Full response (temporarily, in memory)

### What Ganuda Stores

- Request metadata only
- Token counts (from backend response)
- Timing information

### What Ganuda Does NOT Store

- Prompt text
- Response text
- System prompts
- Function call data

## Compliance Considerations

### GDPR

- User data can be deleted on request
- No data transmitted outside your infrastructure
- Audit logs can be purged

### HIPAA

- Use local vLLM (no external transmission)
- Enable encryption at rest
- Configure minimal logging
- Implement access controls

### SOC 2

- Audit logging provides evidence
- Access controls via API keys
- Session management documented
```

---

## Document 3: Security Overview for Public Site

For ganuda.us public site:

```markdown
## Privacy by Design

### Your Data Stays Yours

When you self-host Ganuda:
- Prompts stay on your infrastructure
- No telemetry sent externally
- Complete audit trail you control

### What We Don't Do

- ❌ Collect your prompts
- ❌ Store AI responses
- ❌ Send analytics externally
- ❌ Require cloud connection
- ❌ Access your deployment

### What You Control

- ✅ All logging settings
- ✅ Data retention periods
- ✅ User access
- ✅ Encryption settings
- ✅ Network isolation
```

---

## Checklist for Implementation

### Files to Create

- [ ] `/ganuda/docs/PRIVACY.md` - User-facing privacy statement
- [ ] `/ganuda/docs/DATA_HANDLING.md` - Technical data reference
- [ ] Update `/ganuda/README.md` - Link to privacy docs
- [ ] Update public site - Privacy section

### Configuration Defaults

Ensure `ganuda.yaml` defaults are privacy-respecting:

```yaml
logging:
  audit:
    enabled: true           # Audit trail important
    log_requests: false     # Don't log prompt content
    log_responses: false    # Don't log response content
    log_ip: false           # Don't log IPs by default
    retention_days: 90      # Reasonable retention
```

### Database

Ensure audit log table doesn't have columns for request/response body by default.

---

## Success Criteria

1. ✅ Clear statement of what is/isn't collected
2. ✅ Users can verify claims by reading code
3. ✅ Configuration options for privacy levels
4. ✅ Data deletion procedures documented
5. ✅ Third-party data handling explained
6. ✅ Air-gapped operation documented

---

*For Seven Generations*
