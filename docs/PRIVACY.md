# Ganuda Gateway Privacy Statement

**Effective Date**: December 14, 2025
**Version**: 1.0

---

## Our Commitment

Ganuda Gateway is designed for environments where privacy, control, and data sovereignty matter. We believe your data is yours - we don't want it, we don't need it, and we've built our architecture to prove it.

---

## What Ganuda Collects

### By Default

| Data Type | Collected | Stored | Purpose |
|-----------|-----------|--------|---------|
| API requests | Yes | Local only | Request routing |
| Request metadata | Yes | Local audit log | Security & debugging |
| Response content | No | No | - |
| User prompts | No | No | - |
| Model outputs | No | No | - |

### Audit Logging (Optional, Enabled by Default)

When `logging.audit_enabled: true` in your config:

- **Stored locally**: Request ID, timestamp, endpoint, status code, token counts, response time
- **NOT stored**: Prompt content, response content, user data
- **Retention**: Configurable (default 90 days)
- **Location**: Your database, your control

To disable:
```yaml
logging:
  audit_enabled: false
```

---

## What Ganuda Does NOT Do

1. **No telemetry** - We don't phone home
2. **No analytics** - No usage tracking to external services
3. **No prompt logging** - Your conversations are not stored
4. **No model training** - Your data never trains our models
5. **No third-party sharing** - Data stays on your infrastructure
6. **No cloud dependency** - Runs fully air-gapped if needed

---

## Data Flow

```
User Request
     │
     ▼
┌─────────────────┐
│ Ganuda Gateway  │ ◄── Your infrastructure
│                 │
│ • Validates key │
│ • Routes request│
│ • Logs metadata │ ◄── Local DB only
│   (not content) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Inference       │ ◄── Your choice:
│ Backend         │     • Local vLLM (air-gapped)
│                 │     • External API (your account)
└────────┬────────┘
         │
         ▼
    Response
```

---

## External API Backend

If you configure Ganuda to use an external API (OpenAI, Anthropic, etc.):

- Your prompts are sent to that provider
- That provider's privacy policy applies
- Ganuda does not store or inspect the content
- You control the API key and account

For maximum privacy, use local inference with vLLM.

---

## Intelligence Modules

Optional modules (Council, Memory, etc.) when enabled:

| Module | Data Stored | Location | Deletable |
|--------|-------------|----------|-----------|
| Council | Vote records | Local DB | Yes |
| Thermal Memory | Context summaries | Local DB | Yes |
| Breadcrumbs | Decision trails | Local DB | Yes |
| Audit Log | Request metadata | Local DB | Yes |

All module data:
- Stored in YOUR PostgreSQL database
- Never transmitted externally
- Deletable on request
- Configurable retention

---

## Your Rights

1. **Access**: Query your local database anytime
2. **Delete**: Truncate tables or drop data as needed
3. **Export**: Standard PostgreSQL export tools work
4. **Modify**: Full control over your installation

---

## Air-Gapped Operation

Ganuda supports fully disconnected operation:

1. Use local vLLM inference
2. Disable external API backends
3. No internet required after initial setup
4. All functionality works offline

---

## Security Measures

- API key authentication required by default
- Request rate limiting (configurable)
- Audit logging for security review
- No default passwords in production
- TLS recommended for production deployments

---

## Changes to This Policy

We will update this document as Ganuda evolves. Material changes will be noted in release notes.

---

## Contact

Questions about privacy? Open an issue at:
https://github.com/cherokee-ai/ganuda/issues

---

*For Seven Generations - Cherokee AI Federation*

*Your data. Your infrastructure. Your control.*
