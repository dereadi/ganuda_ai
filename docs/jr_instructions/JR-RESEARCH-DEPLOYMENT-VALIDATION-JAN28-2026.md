# JR Instruction: Research Worker Deployment Validation

**JR ID:** JR-RESEARCH-DEPLOYMENT-VALIDATION-JAN28-2026
**Priority:** P1
**Assigned To:** QA Jr., Performance Jr.
**Council Vote:** 2abc1578335da202
**Addresses:** Gecko, Raven, Eagle Eye, Turtle, Peace Chief concerns

---

## Purpose

Address all Council concerns before production deployment of research-worker.

---

## Concern Resolution Matrix

| Specialist | Concern | Resolution |
|------------|---------|------------|
| Crawdad | Credential rotation | API keys in PostgreSQL with FSE decay |
| Raven | Staging test | Test on dev endpoint first |
| Gecko | Performance baselines | Capture metrics before/after |
| Eagle Eye | Audit logging | Verify logs captured in api_audit_log |
| Peace Chief | Stakeholder consensus | Document TPM approval with conditions |
| Turtle | 7GEN impact | Cultural alignment verified - Cherokee AI Federation |

---

## Pre-Deployment Checklist

### 1. Security Controls (Crawdad)

- [ ] API keys stored as SHA256 hashes in PostgreSQL
- [ ] FSE decay implements key strength evolution
- [ ] No plaintext credentials in code or logs
- [ ] Key rotation via `/v1/fse/rotate/{key_id}` endpoint

**Verification:**
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT key_id, fse_strength FROM api_keys LIMIT 3;"
```

### 2. Performance Baseline (Gecko)

Capture current gateway metrics before deployment:

```bash
# Current endpoint latency
curl -s -w "\n%{time_total}s\n" http://192.168.132.223:8080/health

# Database connection pool status
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'zammad_production';"
```

**Resource limits for research-worker:**
- Max concurrent jobs: 1 (single worker)
- Memory limit: 2GB (systemd)
- Restart delay: 10s

### 3. Staging Test (Raven)

Before production, test with limited scope:

```bash
# Queue test job
curl -X POST http://localhost:8080/v1/research/async \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"query": "Cherokee AI Federation purpose", "max_steps": 3}'

# Monitor worker logs
journalctl -u research-worker -f

# Verify completion
ls -la /ganuda/research/completed/
```

### 4. Audit Trail (Eagle Eye)

After test job completes:

```sql
-- Verify audit entries
SELECT endpoint, method, status_code, response_time_ms, created_at
FROM api_audit_log
WHERE endpoint LIKE '/v1/research%'
ORDER BY created_at DESC
LIMIT 5;
```

**Required metrics endpoints:**
- `/health` - Gateway health
- `/v1/research/health` - ii-researcher availability
- systemd journal for research-worker logs

### 5. Seven Generations Impact (Turtle)

**Cultural Alignment Verification:**

- Cherokee AI Federation principles: ✅ Service runs under Cherokee governance
- Tribal data sovereignty: ✅ Research results stored on tribal infrastructure (redfin)
- Knowledge preservation: ✅ Results saved to /ganuda/research/completed/
- Sustainable resource use: ✅ Single worker, rate-limited API access
- Future generations benefit: ✅ Builds research capability for VetAssist and federation

**175-Year Impact Assessment:**
- Positive: Establishes self-hosted research infrastructure reducing external dependencies
- Neutral: No cultural data at risk (searches public web only)
- Risk mitigation: All results audited and stored locally

### 6. Stakeholder Consensus (Peace Chief)

**Approval Chain:**
1. Security Jr. - Apply security patches to gateway.py ✅ JR written
2. Infrastructure Jr. - Deploy systemd service ✅ JR written
3. QA Jr. - Execute staging test ⏳ This JR
4. TPM - Final approval after test results ⏳ Pending

**Documented Agreement:**
- Council vote 2abc1578335da202 reviewed
- All 7 specialists consulted
- Conditional approval with validation requirements

---

## Deployment Sequence

1. **Security patches first** (JR-RESEARCH-SECURITY-ADDENDUM-JAN28-2026)
2. **Restart gateway** to pick up security changes
3. **Deploy research-worker.service** (JR-DEPLOY-RESEARCH-WORKER-JAN28-2026)
4. **Execute staging test** (this JR)
5. **Verify audit logs and performance**
6. **TPM final approval**

---

## Rollback Trigger

Stop deployment if:
- Security patches fail validation
- Performance degrades >20% baseline
- Audit logs not captured
- ii-researcher unavailable

---

FOR SEVEN GENERATIONS
