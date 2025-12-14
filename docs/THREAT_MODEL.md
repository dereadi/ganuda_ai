# Ganuda Gateway Threat Model

**Version**: 1.0
**Date**: December 14, 2025
**Classification**: Public

---

## Overview

This document identifies threats to Ganuda Gateway deployments and describes mitigations. It follows the STRIDE methodology.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TRUST BOUNDARY                        │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Client  │───▶│   Gateway    │───▶│  Inference   │  │
│  │  (API)   │    │   (8080)     │    │  Backend     │  │
│  └──────────┘    └──────┬───────┘    └──────────────┘  │
│                         │                               │
│                         ▼                               │
│                  ┌──────────────┐                       │
│                  │  PostgreSQL  │                       │
│                  │  (5432)      │                       │
│                  └──────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

---

## Assets

| Asset | Sensitivity | Description |
|-------|-------------|-------------|
| API Keys | HIGH | Authentication credentials |
| Audit Logs | MEDIUM | Request metadata |
| Config File | HIGH | Contains DB credentials |
| Inference Backend | HIGH | Model access |
| Database | HIGH | All persistent data |

---

## STRIDE Analysis

### S - Spoofing

| Threat | Risk | Mitigation |
|--------|------|------------|
| Stolen API key used by attacker | HIGH | Key rotation, rate limiting, IP allowlisting |
| Forged requests to backend | MEDIUM | Internal network isolation, mTLS option |
| Admin impersonation | HIGH | Separate admin keys, audit logging |

**Controls:**
- API keys hashed with SHA-256
- Keys never logged in plaintext
- Rate limiting per key (configurable)
- Audit log captures key ID and IP

### T - Tampering

| Threat | Risk | Mitigation |
|--------|------|------------|
| Config file modification | HIGH | File permissions, config validation on load |
| Database record tampering | MEDIUM | DB access control, audit triggers |
| Request modification in transit | HIGH | TLS for all connections |
| Log tampering to hide activity | MEDIUM | Append-only logging, external log shipping |

**Controls:**
- Config file should be 600 permissions
- Database credentials separate from app
- TLS termination recommended at load balancer
- Immutable audit log design

### R - Repudiation

| Threat | Risk | Mitigation |
|--------|------|------------|
| User denies making request | MEDIUM | Audit log with request ID, timestamp, key ID |
| Admin denies config change | LOW | Version control config, change logging |

**Controls:**
- Every request logged with unique ID
- Audit retention configurable (default 90 days)
- Request ID returned in response headers

### I - Information Disclosure

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key leaked in logs | HIGH | Keys never logged, only hashed IDs |
| Prompt content exposed | MEDIUM | Content not logged by default |
| Config credentials exposed | HIGH | Environment variables for secrets |
| Error messages leak internals | MEDIUM | Generic error responses to clients |

**Controls:**
- Prompts/responses NOT stored in audit log
- Database password supports env var substitution
- Stack traces only in debug mode
- `/v1/config/current` redacts passwords

### D - Denial of Service

| Threat | Risk | Mitigation |
|--------|------|------------|
| Request flooding | HIGH | Rate limiting per API key |
| Large prompt attacks | MEDIUM | Max token limits enforced |
| Database connection exhaustion | MEDIUM | Connection pooling, pool limits |
| Backend overload | HIGH | Concurrency limits, queue management |

**Controls:**
- Per-key rate limits (default 60 RPM)
- Max tokens configurable
- DB pool size limited (default 10)
- Inference backend concurrency limits

### E - Elevation of Privilege

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key gains admin access | HIGH | Separate permission scopes per key |
| Container escape | LOW | Non-root user, minimal base image |
| SQL injection | HIGH | Parameterized queries only |
| Config injection | MEDIUM | YAML safe_load, env var validation |

**Controls:**
- API keys have explicit permission JSON
- Docker runs as non-root `ganuda` user
- All DB queries use parameterized statements
- Config schema validates all inputs

---

## Attack Scenarios

### Scenario 1: Stolen API Key

**Attack**: Attacker obtains valid API key from compromised client.

**Impact**: Unauthorized access to inference, potential cost/quota abuse.

**Detection**: 
- Unusual request patterns in audit log
- Requests from unexpected IPs
- Rate limit violations

**Response**:
1. Revoke key: `UPDATE api_keys SET is_active = false WHERE id = X`
2. Review audit logs for scope of access
3. Issue new key to legitimate user
4. Consider IP allowlisting

### Scenario 2: Insider Threat

**Attack**: Admin with DB access exfiltrates data.

**Impact**: API keys exposed, audit logs compromised.

**Detection**:
- DB query logging
- Unusual export operations

**Response**:
1. Rotate all API keys
2. Review DB access logs
3. Implement least-privilege access

### Scenario 3: Network Position Attack

**Attack**: Attacker on same network intercepts traffic.

**Impact**: API keys and potentially prompts exposed.

**Detection**: Difficult without TLS

**Prevention**:
1. Always use TLS in production
2. Isolate Gateway network segment
3. Use mTLS for backend communication

---

## Security Checklist

### Deployment

- [ ] TLS enabled for Gateway endpoint
- [ ] Database not exposed externally
- [ ] Config file permissions restricted (600)
- [ ] Default API key changed
- [ ] Rate limits configured appropriately
- [ ] Non-root container user confirmed

### Operations

- [ ] Audit log retention policy defined
- [ ] Key rotation schedule established
- [ ] Monitoring/alerting configured
- [ ] Backup strategy for database
- [ ] Incident response plan documented

### Network

- [ ] Gateway on isolated network segment
- [ ] Firewall rules restrict access
- [ ] Backend not directly accessible
- [ ] Internal traffic encrypted (optional mTLS)

---

## Residual Risks

| Risk | Severity | Acceptance Rationale |
|------|----------|---------------------|
| Inference backend vulnerabilities | MEDIUM | Outside Ganuda scope, user responsibility |
| Zero-day in dependencies | LOW | Regular updates, minimal dependencies |
| Physical access to server | HIGH | Physical security is deployment concern |

---

## References

- OWASP API Security Top 10
- STRIDE Threat Modeling
- CIS Docker Benchmark

---

*For Seven Generations - Cherokee AI Federation*
