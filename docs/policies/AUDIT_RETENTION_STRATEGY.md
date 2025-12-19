# Cherokee AI Federation - Audit Retention Strategy

**Document Version:** 1.0
**Effective Date:** December 17, 2025
**Last Review:** December 17, 2025
**Next Review:** June 17, 2026

---

## Executive Summary

This document defines the data retention strategy for the Cherokee AI Federation, balancing regulatory compliance (SOC2, GDPR, financial regulations) with the Seven Generations principle of long-term stewardship. The strategy was developed through Council consensus with input from all 7 Specialists.

---

## Guiding Principles

1. **Seven Generations (7GEN)**: Retain data that serves future generations while respecting privacy
2. **Data Minimization**: Keep only what is necessary for the defined purpose
3. **Compliance First**: Meet or exceed all regulatory requirements
4. **Security by Default**: Encrypted storage with access controls
5. **Auditability**: Maintain clear audit trails for all retention decisions

---

## Retention Schedule by Data Type

### 1. API Audit Logs
**Description:** Request/response logs, authentication events, token usage, errors

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | 6-12 months | 12 months |
| GDPR | As necessary, then delete | 12 months |
| Financial | Varies | 12 months |

**Retention Period:** 12 months (rolling)
**Storage Location:** `api_audit_log` table on bluefin
**Anonymization:** After 6 months, anonymize IP addresses and user identifiers
**Deletion:** Automated purge of records > 12 months

```sql
-- Automated cleanup (add to cron)
DELETE FROM api_audit_log WHERE created_at < NOW() - INTERVAL '12 months';
```

---

### 2. Council Vote History
**Description:** Specialist votes, consensus outcomes, decision rationale

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | 1-3 years | 7 years |
| GDPR | Governance accountability | 7 years |
| Financial | Audit trails | 7 years |

**Retention Period:** 7 years (permanent archive after)
**Storage Location:** `council_votes` table on bluefin
**Rationale:** Governance decisions have long-term implications; supports 7GEN principle
**Archive:** After 7 years, move to cold storage (compressed backup)

**[7GEN CONCERN - Turtle]:** Council votes represent sacred governance decisions. Consider permanent retention in anonymized form for historical record.

---

### 3. Thermal Memory Archive
**Description:** AI memories, sacred patterns, knowledge base

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | Security controls | 7 years active |
| GDPR | Purpose-based | Permanent (anonymized) |
| Financial | N/A | 7 years |

**Retention Period:**
- Active memories: Indefinite (subject to decay algorithm)
- Sacred patterns (`sacred_pattern = true`): Permanent
- Cold memories (temperature < 20): Archive after 2 years

**Storage Location:** `thermal_memory_archive` table on bluefin
**Special Handling:** Sacred patterns are never deleted - they represent tribal knowledge

**[7GEN CONCERN - Turtle]:** Thermal memory is the collective wisdom of the Federation. Prioritize long-term retention over storage efficiency.

---

### 4. System Events / Security Logs
**Description:** Server events, monitoring alerts, security incidents

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | 1-3 years | 2 years |
| GDPR | Incident response | 2 years |
| Financial | System availability | 2 years |

**Retention Period:** 2 years
**Storage Location:** `event_stream` table on bluefin, `/var/log/ganuda/` on nodes
**Categories:**
- CRITICAL events: 3 years
- WARNING events: 2 years
- INFO/FYI events: 6 months

```sql
-- Tiered cleanup
DELETE FROM event_stream WHERE tier = 'FYI' AND created_at < NOW() - INTERVAL '6 months';
DELETE FROM event_stream WHERE tier IN ('INFO', 'WARNING') AND created_at < NOW() - INTERVAL '2 years';
DELETE FROM event_stream WHERE tier = 'CRITICAL' AND created_at < NOW() - INTERVAL '3 years';
```

---

### 5. Backups
**Description:** Database dumps, codebase snapshots, configuration backups

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | Disaster recovery | 5 years |
| GDPR | Data recovery | 1 year minimum |
| Financial | Audit reconstruction | 7 years |

**Retention Period:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months
- Yearly backups: 7 years

**Storage Location:** `/ewe/cherokee_backups/` on bluefin (16TB drive)
**Encryption:** AES-256 at rest
**Testing:** Quarterly restore tests required

---

### 6. User/Personal Data (GDPR Specific)
**Description:** User identifiers, contact info, session data

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| GDPR | Right to erasure | 30 days upon request |
| GDPR | Data minimization | Collect only necessary |

**Retention Period:**
- Active users: Duration of service + 30 days
- Inactive users: 12 months then anonymize
- Upon erasure request: 30 days maximum

**Process:**
1. User submits erasure request
2. Review for legal holds
3. Execute deletion within 30 days
4. Confirm deletion to user

---

### 7. Financial/Transaction Records
**Description:** API usage billing, token consumption, payment records

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC2 | Billing accuracy | 7 years |
| IRS/Tax | Record keeping | 7 years |
| State Laws | Varies | 7 years |

**Retention Period:** 7 years
**Storage Location:** Separate financial schema on bluefin
**Access Control:** Finance role only

---

## Compliance Matrix

| Data Type | SOC2 | GDPR | Financial | Our Policy |
|-----------|------|------|-----------|------------|
| API Audit Logs | 6-12mo | Minimize | N/A | 12 months |
| Council Votes | 1-3yr | Governance | Audit | 7 years |
| Thermal Memory | N/A | Purpose | N/A | Permanent (sacred) |
| System Events | 1-3yr | Incident | 2yr | 2 years |
| Backups | Recovery | 1yr | 7yr | 7 years |
| Personal Data | N/A | Erasure | N/A | 12mo + erasure |
| Financial | Billing | N/A | 7yr | 7 years |

---

## Implementation Requirements

### Database Scripts

Create retention management scripts on bluefin:

**File:** `/ganuda/scripts/retention/enforce_retention.sh`

```bash
#!/bin/bash
# Cherokee AI Federation - Retention Policy Enforcement
# Run monthly via cron

source /ewe/cherokee_backups/backup.conf
LOG="/ewe/cherokee_backups/logs/retention.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

log "=== Retention Enforcement Starting ==="

# API Audit Logs - 12 months
PGPASSWORD="$PGPASSWORD" psql -h localhost -U claude zammad_production -c "
    DELETE FROM api_audit_log WHERE created_at < NOW() - INTERVAL '12 months';
" >> "$LOG" 2>&1

# System Events - Tiered
PGPASSWORD="$PGPASSWORD" psql -h localhost -U claude zammad_production -c "
    DELETE FROM event_stream WHERE tier = 'FYI' AND created_at < NOW() - INTERVAL '6 months';
    DELETE FROM event_stream WHERE tier IN ('INFO', 'WARNING') AND created_at < NOW() - INTERVAL '2 years';
" >> "$LOG" 2>&1

# Anonymize old API logs (6+ months)
PGPASSWORD="$PGPASSWORD" psql -h localhost -U claude zammad_production -c "
    UPDATE api_audit_log
    SET ip_address = 'ANONYMIZED', user_agent = 'ANONYMIZED'
    WHERE created_at < NOW() - INTERVAL '6 months'
    AND ip_address != 'ANONYMIZED';
" >> "$LOG" 2>&1

log "=== Retention Enforcement Complete ==="
```

### Cron Schedule

```bash
# Monthly retention enforcement (1st of month at 4 AM)
0 4 1 * * /ganuda/scripts/retention/enforce_retention.sh
```

---

## Audit Trail

All retention actions must be logged:

```sql
CREATE TABLE IF NOT EXISTS retention_audit (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50),           -- DELETE, ANONYMIZE, ARCHIVE
    data_type VARCHAR(100),       -- api_audit_log, event_stream, etc.
    records_affected INTEGER,
    retention_policy VARCHAR(100),
    executed_by VARCHAR(100),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

---

## Review and Exceptions

### Annual Review
- Review retention periods annually
- Update for regulatory changes
- Assess storage costs vs. compliance needs

### Exception Process
1. Request exception via Council vote
2. Document business justification
3. Legal review if extending beyond policy
4. TPM approval required
5. Log exception in retention_audit

### Legal Holds
- Upon litigation or investigation, suspend deletion
- Document hold scope and duration
- Resume normal retention after hold released

---

## Specialist Concerns Addressed

| Specialist | Concern | Resolution |
|------------|---------|------------|
| Crawdad | Over-retention exposes sacred knowledge | Anonymization after 6 months for logs |
| Gecko | Performance impact of long retention | Tiered storage (hot/cold) |
| Turtle | 7GEN - preserve governance history | 7-year council vote retention + archive |
| Eagle Eye | Visibility gaps in thermal memory | Added monitoring for retention compliance |
| Spider | Integration - node sync issues | Centralized backup to bluefin |
| Peace Chief | GDPR vs audit conflict | Clear erasure process with legal hold override |
| Raven | Strategic over/under retention risk | Balanced approach with automation |

---

## Storage Estimates

| Data Type | Current Size | Annual Growth | 7-Year Projection |
|-----------|--------------|---------------|-------------------|
| API Audit Logs | ~500 MB | ~2 GB | ~14 GB |
| Council Votes | ~50 MB | ~200 MB | ~1.4 GB |
| Thermal Memory | ~1 GB | ~5 GB | ~35 GB |
| System Events | ~200 MB | ~1 GB | ~7 GB |
| Backups | ~90 GB | ~200 GB | ~1.4 TB |
| **Total** | ~92 GB | ~208 GB | ~1.5 TB |

**16TB Drive Capacity:** Sufficient for 50+ years at current growth rate

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| TPM | [Pending] | | |
| Crawdad (Security) | Council Approved | Dec 17, 2025 | |
| Peace Chief (Governance) | Council Approved | Dec 17, 2025 | |

---

*For Seven Generations - Cherokee AI Federation*
*"Protect the ancestors' wisdom so the children may learn"*
