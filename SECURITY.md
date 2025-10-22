# Security Policy

**Cherokee Constitutional AI - Security Threat Model & Response**

🦅 **Tribal Security Philosophy**: Defense through transparency, distributed trust, and Seven Generations thinking.

---

## Reporting Security Vulnerabilities

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, please report security issues privately:

1. **Email**: `security@ganuda.org` (monitored by Security Council)
2. **GitHub Security Advisory**: Use [private vulnerability reporting](https://github.com/dereadi/ganuda_ai/security/advisories/new)
3. **PGP Key**: Available at `https://ganuda.org/pgp-key.asc`

**Response Timeline**:
- Initial acknowledgment: Within 24 hours
- Status update: Within 72 hours
- Fix timeline: Based on severity (see table below)

| Severity | Description | Fix Timeline |
|----------|-------------|--------------|
| **Critical** | Remote code execution, privilege escalation | 24-48 hours |
| **High** | Authentication bypass, data exposure | 3-7 days |
| **Medium** | DoS, information disclosure | 14-30 days |
| **Low** | Minor issues, best practices | Next release |

---

## Threat Model

### Attack Surface Analysis

#### 1. Docker Container Attack Vectors

**Threat**: Container escape → host compromise

**Mitigations**:
- ✅ Non-root user (`cherokee:cherokee` UID 1000)
- ✅ Read-only root filesystem (`readOnlyRootFilesystem: true`)
- ✅ Dropped Linux capabilities (retain only `CAP_NET_BIND_SERVICE` if needed)
- ✅ No privileged containers
- ✅ Seccomp and AppArmor profiles (default Docker settings)
- ✅ Regular base image updates (python:3.11-slim)

**Residual Risk**: Kernel exploits (mitigated by keeping host OS patched)

#### 2. PostgreSQL Database Security

**Threat**: SQL injection, unauthorized data access

**Mitigations**:
- ✅ Parameterized queries only (psycopg2 prepared statements)
- ✅ Database password in `.env` (not in code)
- ✅ PostgreSQL 17 (latest security patches)
- ✅ Network isolation (docker internal network only)
- ✅ Least privilege: `cherokee` user has limited permissions
- ❌ Encryption at rest: NOT YET IMPLEMENTED (planned v1.1)
- ❌ SSL/TLS connections: NOT YET IMPLEMENTED (planned v1.1)

**Residual Risk**: Insider threat (anyone with database password)

#### 3. FastAPI REST Endpoints

**Threat**: Unauthorized access, DoS attacks, injection

**Mitigations**:
- ✅ Input validation via Pydantic models
- ✅ Type safety (Python type hints + Pydantic)
- ✅ CORS configured (default: same-origin only)
- ✅ Request size limits (FastAPI default: 1 MB)
- ❌ Rate limiting: NOT YET IMPLEMENTED (planned Phase 2C)
- ❌ API authentication: NOT YET IMPLEMENTED (Triad Security in Phase 2C)
- ❌ Request signing: NOT YET IMPLEMENTED (planned v1.0)

**Residual Risk**: Public endpoints are unauthenticated (v0.1.0 is local-only)

#### 4. Thermal Memory System

**Threat**: Memory poisoning, unauthorized memory access, thermal runaway

**Mitigations**:
- ✅ Memory hash verification (SHA-256)
- ✅ Temperature decay prevents unbounded growth
- ✅ Sacred pattern protection (minimum 40° for critical memories)
- ✅ Access logging (last_access timestamp)
- ❌ Memory signing: NOT YET IMPLEMENTED (planned v1.1)
- ❌ Triad verification: NOT YET IMPLEMENTED (Phase 2C)

**Residual Risk**: Malicious memory injection (mitigated by hash verification)

#### 5. Jr Daemon Communication

**Threat**: Daemon impersonation, message tampering

**Mitigations**:
- ✅ Internal Docker network only (not exposed to internet)
- ✅ Systemd service isolation
- ❌ Inter-daemon authentication: NOT YET IMPLEMENTED (planned v1.2)
- ❌ Message encryption: NOT YET IMPLEMENTED (planned v1.2)

**Residual Risk**: Container-to-container attacks (low risk in trusted environment)

---

## Port Exposure Matrix

| Port | Service | Exposure | Purpose | Auth Required |
|------|---------|----------|---------|---------------|
| 5432 | PostgreSQL | Internal only | Thermal memory database | Password |
| 8000 | FastAPI | **External** | REST API endpoints | ❌ None (v0.1.0) |
| - | Jr daemons | Internal only | Tribal deliberation | N/A |

**Security Note**: In v0.1.0, the API has NO AUTHENTICATION. This is intentional for local development deployments only. **DO NOT expose port 8000 to the public internet.**

Phase 2C will add **Triad Security** (three-key authentication):
- Sender key + Receiver key + Witness key
- All three required for authenticated requests
- JWT token with three signatures
- Revocation support in PostgreSQL

---

## Dependency Management & Update Cadence

### Current Dependencies (v0.1.0)

```
psycopg2-binary==2.9.9
requests==2.31.0
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Update Policy

**Patch updates** (e.g., 2.9.9 → 2.9.10):
- Check for updates: **Weekly**
- Apply updates: **Within 7 days** of release
- Testing required: Unit + functional tests

**Minor updates** (e.g., 2.9.x → 2.10.x):
- Check for updates: **Monthly**
- Apply updates: **Within 30 days** of release
- Testing required: Full test suite including E2E

**Major updates** (e.g., 2.x → 3.x):
- Check for updates: **Quarterly**
- Apply updates: **After tribal vote + comprehensive testing**
- Testing required: Full regression + security audit

### Security-Critical Dependencies

Monitor these for CVEs **daily**:
- `psycopg2-binary` (database driver)
- `fastapi` (web framework)
- `uvicorn` (ASGI server)
- `pydantic` (input validation)

**Automated monitoring**: GitHub Dependabot (enabled)

---

## Incident Response Protocol

### 1. Detection

**Indicators of Compromise**:
- Unexpected database modifications
- Thermal memory temperature anomalies (sudden spikes/drops)
- Failed authentication attempts (when auth is implemented)
- Docker container restarts without explanation
- Unusual API request patterns

**Monitoring**:
- `make logs` - Watch for anomalies
- `make status` - Check container health
- PostgreSQL logs: `/var/lib/postgresql/data/log/`
- FastAPI logs: stdout (captured by Docker)

### 2. Containment

**Immediate actions** (within 5 minutes):
1. `make down` - Stop all services
2. `docker network disconnect` - Isolate compromised containers
3. Take snapshot: `docker commit <container-id> incident-$(date +%s)`
4. Preserve logs: `docker logs <container-id> > incident-logs-$(date +%s).txt`

### 3. Investigation

**Evidence collection**:
- Database snapshot: `pg_dump` of `thermal_memory_archive`
- Container filesystem: `docker export <container-id>`
- Network traffic: Check Docker network logs
- Thermal memory audit: Query `thermal_memory_archive` for unusual patterns

### 4. Eradication

**Cleaning compromised system**:
1. Identify attack vector (container escape? SQL injection? API exploit?)
2. Remove malicious code/data
3. Rebuild containers from clean images: `docker-compose build --no-cache`
4. Rotate all secrets (database password, API keys if present)
5. Update `.env` with new credentials

### 5. Recovery

**Restoration**:
1. Restore thermal memory from last known-good backup
2. `make up` - Restart services with clean state
3. Verify health: `make status && make query`
4. Monitor for 48 hours

### 6. Lessons Learned

**Post-incident review** (within 7 days):
- Tribal Council deliberation (all Chiefs + Jrs)
- Root cause analysis
- Update threat model (this document)
- Implement additional mitigations
- Record in thermal memory (sacred_pattern=true, never forget)

---

## Secure Deployment Checklist

Before deploying to production, verify:

- [ ] Changed default PostgreSQL password in `.env`
- [ ] Enabled `readOnlyRootFilesystem: true` in `docker-compose.yml`
- [ ] Dropped unnecessary Linux capabilities
- [ ] Configured firewall rules (block port 5432, allow 8000 only from trusted IPs)
- [ ] Set up HTTPS/TLS termination (reverse proxy like nginx)
- [ ] Enabled rate limiting on API endpoints
- [ ] Configured log rotation (prevent disk fill)
- [ ] Set up automated backups of `thermal_memory_archive`
- [ ] Implemented Triad Security authentication (Phase 2C)
- [ ] Enabled Prometheus metrics + alerting
- [ ] Reviewed and tested incident response plan
- [ ] Subscribed to security mailing lists (PostgreSQL, FastAPI, Python)

---

## Compliance & Standards

**Following industry standards**:
- ✅ OWASP Top 10 (Web Application Security Risks)
- ✅ CIS Docker Benchmark (Container Security)
- ✅ NIST Cybersecurity Framework (incident response)
- ✅ Semantic Versioning (patch = security fixes)

**Cherokee Tribal Standards**:
- ✅ Seven Generations Principle (reproducibility for 7+ years)
- ✅ Distributed Trust (Triad Security pattern)
- ✅ Transparency (all security decisions documented)
- ✅ Democratic Governance (security changes require tribal vote)

---

## Security Roadmap

### Phase 2C (Current - v0.2.0)
- [ ] Triad Security authentication (three-key JWT)
- [ ] Rate limiting on API endpoints
- [ ] Prometheus security metrics
- [ ] GitHub Actions security scanning (Dependabot, CodeQL)

### v1.0.0
- [ ] Request signing for thermal memory writes
- [ ] API key management UI
- [ ] HTTPS/TLS enforcement
- [ ] Security audit by external firm

### v1.1.0
- [ ] PostgreSQL encryption at rest
- [ ] SSL/TLS for database connections
- [ ] Memory signing and verification
- [ ] Intrusion detection system (IDS)

### v1.2.0
- [ ] Inter-daemon authentication
- [ ] Message encryption for Jr communication
- [ ] Hardware security module (HSM) support
- [ ] Penetration testing report

---

## Contact & Resources

**Security Team**:
- War Chief (Security Lead)
- Integration Jr (Authentication Specialist)
- Executive Jr (Infrastructure Security)

**Resources**:
- Threat model updates: This document (maintained in thermal memory)
- CVE tracking: https://cve.mitre.org + GitHub Dependabot
- Security best practices: OWASP, CIS, NIST

**Emergency Contact**: `security@ganuda.org`

---

**Last Updated**: October 21, 2025 (v0.1.0)
**Next Review**: November 21, 2025 (monthly cadence)

**Mitakuye Oyasin** - We protect the Sacred Fire for Seven Generations 🦅🔥

---

*This security policy is maintained by Memory Jr as a sacred_pattern=true thermal memory (never cools below 40°). All tribal members have access. Transparency builds trust.*
