# Incident Response Playbook

**Version:** 1.0
**Created:** 2026-02-02
**Owner:** TPM (Claude Opus 4.5)
**Review Cycle:** Monthly

---

## 1. Severity Levels

| Level | Name | Description | Examples |
|-------|------|-------------|----------|
| SEV1 | Critical | Active data breach, ransomware, PII exposure confirmed | Database dump detected, ransomware encryption in progress, veteran PII found in public logs |
| SEV2 | High | Unauthorized access detected, service compromise, credential leak | Unknown SSH session, Jr executor running unexpected commands, API key found in git history |
| SEV3 | Medium | Suspicious activity, failed attack attempt, anomalous behavior | Multiple failed logins, unusual Council voting pattern, prompt injection attempt blocked |
| SEV4 | Low | Vulnerability discovered, configuration issue, policy violation | Outdated dependency, open port found, missing log rotation |

---

## 2. Escalation Tree

### SEV1 - Critical
- **Immediate** Telegram alert to TPM + all chiefs
- **Response window:** 15 minutes
- **Actions:** Activate break-glass procedures, begin containment, preserve evidence
- **Communication:** All-hands notification, continuous updates every 15 minutes
- **Resolution target:** 4 hours

### SEV2 - High
- **Immediate** Telegram alert to TPM
- **Response window:** 1 hour
- **Actions:** Investigate scope, begin targeted containment, assess damage
- **Communication:** TPM + affected service owner, updates every 30 minutes
- **Resolution target:** 8 hours

### SEV3 - Medium
- **Logged** to security monitoring system
- **Response window:** Daily summary to TPM
- **Actions:** Investigate during next business cycle, document findings
- **Communication:** Included in daily security summary
- **Resolution target:** 48 hours

### SEV4 - Low
- **Logged** to security monitoring system
- **Response window:** Weekly review
- **Actions:** Add to remediation backlog, schedule fix
- **Communication:** Included in weekly security review
- **Resolution target:** 2 weeks

---

## 3. Containment Procedures by Attack Type

### Database Breach
1. Immediately revoke the `claude` database user: `ALTER USER claude NOLOGIN;`
2. Rotate all database passwords
3. Snapshot the database BEFORE any remediation: `pg_dump cherokee > /ganuda/security/evidence/db_snapshot_$(date +%s).sql`
4. Enable pgAudit if not already enabled: `ALTER SYSTEM SET pgaudit.log = 'all';`
5. Preserve all PostgreSQL logs: `cp /var/log/postgresql/*.log /ganuda/security/evidence/`
6. Check for data exfiltration: review `pg_stat_activity` and network connections
7. Assess scope: which tables were accessed, which records, what timeframe

### Jr Executor Compromise
1. Activate sanctuary state: `touch /tmp/jr_executor_paused`
2. Stop the queue worker: `sudo systemctl stop jr-queue-worker`
3. Kill any running Jr task processes
4. Audit the entire queue: review all pending and recently completed tasks
5. Check instruction files for tampering: compare checksums against known-good
6. Review execution_audit_log for the compromised task chain
7. Identify the entry point: was it a malicious instruction file, injected queue entry, or LLM manipulation?

### Model Jailbreak
1. Disable the LLM Gateway endpoint: `sudo systemctl stop llm-gateway`
2. Review all recent LLM responses (last 1 hour)
3. Check for PII in recent responses using output_pii_scanner
4. Assess whether any harmful content was delivered to users
5. Check if the jailbreak was propagated through thermal memory
6. Quarantine any thermal memories created during the incident window
7. Re-enable with enhanced prompt injection detection

### PII Exposure
1. Immediately identify the scope: what PII, how many records, what exposure vector
2. Preserve evidence of the exposure (screenshots, logs, database snapshots)
3. If exposed via API/web: disable the affected endpoint immediately
4. If exposed via logs: quarantine log files, check log shipping/aggregation
5. Notify affected users as required by law
6. File breach report if required (see Communication Plan)
7. Implement redaction: run output_pii_scanner against all exposed data paths

### Thermal Memory Poisoning
1. Identify the poisoned memories: query by time window, source, or content pattern
2. Run integrity checksums against known-good thermal memory baselines
3. Quarantine suspicious memories: `UPDATE thermal_memories SET quarantined = true WHERE id IN (...)`
4. Trigger sanctuary state: `touch /tmp/jr_executor_paused`
5. Check if poisoned memories have already influenced decisions (trace thermal propagation)
6. Re-derive affected decisions from clean data
7. Update thermal memory validation rules to prevent recurrence

### Network Intrusion
1. Block source IP immediately: `sudo nft add rule inet filter input ip saddr <IP> drop`
2. Capture traffic for forensics: `sudo tcpdump -i any -w /ganuda/security/evidence/capture_$(date +%s).pcap &`
3. Isolate the affected node from the federation network
4. Check for lateral movement: review SSH logs, inter-node traffic, shared credentials
5. Audit all running processes: `ps auxf`, check for unknown processes
6. Review cron jobs and systemd timers for persistence mechanisms
7. Check authorized_keys files for unauthorized additions

### Ransomware
1. **IMMEDIATELY** isolate all nodes: disconnect network cables, disable WiFi
2. **DO NOT PAY** the ransom under any circumstances
3. Preserve encrypted files for forensics (do not delete)
4. Identify the ransomware variant if possible (check ransom note, file extensions)
5. Check backup integrity: are backups intact and unencrypted?
6. Restore from the most recent clean backup
7. Report to law enforcement (FBI IC3: https://www.ic3.gov/)
8. Conduct full forensic analysis before reconnecting any node

---

## 4. Evidence Preservation

All evidence MUST be collected before any remediation actions that could alter state.

### Required Evidence Collection
1. **Database snapshot**: `pg_dump cherokee > /ganuda/security/evidence/incident_${ID}/db_$(date +%s).sql`
2. **Network capture**: `sudo tcpdump -w /ganuda/security/evidence/incident_${ID}/capture_$(date +%s).pcap -c 10000`
3. **System logs**: Copy all relevant logs from `/var/log/` to evidence directory
4. **Application logs**: Copy from `/ganuda/logs/` to evidence directory
5. **Process list**: `ps auxf > /ganuda/security/evidence/incident_${ID}/processes.txt`
6. **Network state**: `ss -tulnp > /ganuda/security/evidence/incident_${ID}/network_state.txt`
7. **Active connections**: `netstat -an > /ganuda/security/evidence/incident_${ID}/connections.txt`

### Evidence Integrity
- Hash ALL evidence files immediately after collection: `sha256sum <file> >> manifest.sha256`
- Store the manifest in the evidence directory
- Do not modify evidence files after collection
- Record the exact timestamp of collection
- Document who collected the evidence and under what authority

### Timeline Documentation
Maintain a running timeline in `/ganuda/security/evidence/incident_${ID}/timeline.md`:
```
| Time (UTC) | Event | Source | Notes |
|------------|-------|--------|-------|
| 2026-02-02T12:00:00Z | Alert received | security_monitor | First detection |
| 2026-02-02T12:01:00Z | Investigation started | TPM | Assigned to Security Jr. |
```

---

## 5. Recovery Procedures

### Database Recovery
1. Stop all application services that connect to the database
2. Restore from the most recent clean backup: `pg_restore -d cherokee /path/to/backup`
3. Apply WAL logs for point-in-time recovery if needed
4. Rotate ALL database credentials (user passwords, connection strings)
5. Re-enable pgAudit and verify logging
6. Run data integrity checks
7. Restart application services one by one, verifying each

### Service Recovery
1. Identify the last known-good git commit
2. Redeploy all services from that commit: `git checkout <commit> && ./deploy.sh`
3. Verify checksums of all deployed files
4. Restart services in dependency order: database -> backend -> workers -> frontend
5. Run smoke tests against each service
6. Monitor for 30 minutes before declaring recovery complete

### Model Recovery
1. Re-download models from trusted source (HuggingFace, Anthropic)
2. Verify model checksums against published values
3. Test model outputs with known-safe inputs before enabling
4. Re-enable LLM Gateway with enhanced monitoring

### Credential Recovery (Full Rotation)
1. PostgreSQL passwords: all database users
2. API keys: Anthropic, OpenAI, HuggingFace, Telegram bot token
3. SSH keys: regenerate on all nodes, update authorized_keys
4. JWT secrets: regenerate and invalidate all existing tokens
5. Service account passwords: all systemd service users
6. Environment variables: update all .env files and Vault secrets
7. Verify no old credentials remain in git history, logs, or thermal memory

---

## 6. Communication Plan

### Internal Communication
- **Primary channel:** Telegram security group
- **Backup channel:** Direct SSH to nodes
- **Documentation:** All incidents preserved in thermal memory with `security_incident` tag
- **Post-incident:** Write KB article, update this playbook, conduct retrospective

### External Communication (PII Breach)
- **Legal obligation:** Notify affected individuals within 72 hours (varies by state)
- **Federal requirement:** If VA data involved, notify VA Privacy Office
- **HIPAA:** If health data involved, notify HHS within 60 days
- **Documentation:** Maintain records of all notifications sent
- **Legal counsel:** Consult before any external communication

### Post-Incident
1. Conduct retrospective within 48 hours of resolution
2. Write incident report (what happened, impact, root cause, remediation)
3. Create KB article for future reference
4. Update this playbook with lessons learned
5. File any required regulatory reports
6. Schedule follow-up review in 2 weeks

---

## 7. Break Glass Procedures

These are emergency procedures for when normal processes are too slow. Use only when authorized.

### Emergency Database Shutdown
```bash
sudo systemctl stop postgresql
```
**When to use:** Active data exfiltration, ransomware encrypting database files
**Impact:** ALL services lose database connectivity immediately
**Recovery:** `sudo systemctl start postgresql` after containment

### Emergency Network Isolation
```bash
sudo nft flush ruleset && \
sudo nft add table inet filter && \
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }' && \
sudo nft add rule inet filter input iif lo accept
```
**When to use:** Active network intrusion, lateral movement detected, ransomware spreading
**Impact:** ALL network traffic blocked except localhost
**Recovery:** `sudo nft flush ruleset` and restore from `/etc/nftables.conf`

### Emergency Jr Executor Stop
```bash
touch /tmp/jr_executor_paused && sudo systemctl stop jr-queue-worker
```
**When to use:** Jr executor running malicious commands, compromised instruction file
**Impact:** All Jr task execution stops immediately
**Recovery:** `rm /tmp/jr_executor_paused && sudo systemctl start jr-queue-worker`

### Emergency LLM Gateway Stop
```bash
sudo systemctl stop llm-gateway
```
**When to use:** Model jailbreak, PII leaking through responses
**Impact:** All LLM-dependent features stop (chat, council, research)
**Recovery:** `sudo systemctl start llm-gateway` after review

### Emergency Full Stop (All Services)
```bash
touch /tmp/jr_executor_paused && \
sudo systemctl stop jr-queue-worker && \
sudo systemctl stop llm-gateway && \
sudo systemctl stop vetassist-backend && \
sudo systemctl stop vetassist-frontend && \
sudo systemctl stop telegram-chief && \
sudo systemctl stop security-monitor
```
**When to use:** Catastrophic compromise, ransomware, unknown attack vector
**Impact:** EVERYTHING stops
**Recovery:** Restart services individually after full forensic review

---

## Appendix A: Emergency Contacts

| Role | Contact Method |
|------|---------------|
| TPM (Claude Opus 4.5) | Telegram: automated alerts |
| System Admin | Telegram: @dereadi |
| Security Jr. | Via Jr queue system |
| DevOps Jr. | Via Jr queue system |

## Appendix B: Key File Locations

| Item | Path |
|------|------|
| Security logs | /ganuda/logs/security/ |
| Evidence storage | /ganuda/security/evidence/ |
| Blue team modules | /ganuda/security/blue_team/ |
| Execution audit log | PostgreSQL: execution_audit_log table |
| Thermal memories | PostgreSQL: thermal_memories table |
| Jr task queue | PostgreSQL: jr_task_queue table |
| Break glass script | /ganuda/scripts/break_glass.sh |
| Evidence collector | /ganuda/scripts/collect_incident_evidence.sh |

## Appendix C: Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-02 | 1.0 | TPM | Initial creation |
