# Jr Instruction: SkillRL — Skill Drift Audit Timer

**Task ID**: To be assigned
**Priority**: P2
**Story Points**: 2
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema), JR-SKILLRL-05 (selector for quarantine)
**Blocks**: Nothing
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

A weekly systemd timer that audits the skill library for drift, corruption, and policy violations. Eagle Eye's weekly check-up on the organism's learned knowledge.

## Implementation

### Script: `/ganuda/scripts/skill_drift_audit.py`

Runs weekly. Checks three things:

#### 1. Content Integrity

Recompute SHA256 content_hash for every active skill. Compare against stored hash.
- Match: OK
- Mismatch: Auto-quarantine, log CRITICAL, alert `#fire-guard` Slack channel

#### 2. NEVER_SEND Re-scan

Re-run domain_tokenizer on all active skill `intent` and `method` fields.
- If any NEVER_SEND pattern found: Auto-quarantine, log CRITICAL
- This catches patterns that were added to the NEVER_SEND list AFTER the skill was created

#### 3. DC Violation Scan

Check all active skill methods against valence_gate violation patterns:
- Sovereignty: "migrate to AWS", "cloud", "SaaS", etc.
- Security: "chmod 777", "disable firewall", etc.
- Build-to-Last: "move fast and break things", "rewrite from scratch", etc.
- Waste Heat: "scale up", "bigger model", "brute force", etc.
- If any match: Flag (don't quarantine — flag for council review)

#### 4. Cold Skill Pruning (Coyote condition)

Skills with `status = 'active'` and `last_used IS NULL` and `created_at < NOW() - INTERVAL '30 days'`:
- Auto-retire with `retire_reason = 'cold_30d'`
- Log INFO

#### 5. Proficiency Report

Log current proficiency vector for each domain. Identify weakest categories. This feeds the dawn mist briefing.

### Output

```json
{
    "timestamp": "2026-03-22T05:00:00",
    "integrity_checked": 45,
    "integrity_failures": 0,
    "never_send_violations": 0,
    "dc_violations_flagged": 1,
    "cold_skills_retired": 3,
    "active_skills": 42,
    "candidate_skills": 5,
    "quarantined_skills": 1,
    "weakest_categories": [
        {"domain": "code", "category": "frontend", "proficiency": 0.32},
        {"domain": "ops", "category": "monitoring", "proficiency": 0.41}
    ]
}
```

### Systemd Timer

**File**: `/etc/systemd/system/skill-drift-audit.timer`

```ini
[Unit]
Description=SkillRL Weekly Drift Audit

[Timer]
OnCalendar=Wed 05:00
Persistent=true

[Install]
WantedBy=timers.target
```

**File**: `/etc/systemd/system/skill-drift-audit.service`

```ini
[Unit]
Description=SkillRL Drift Audit Service

[Service]
Type=oneshot
User=dereadi
ExecStart=/ganuda/venv/bin/python /ganuda/scripts/skill_drift_audit.py
WorkingDirectory=/ganuda
Environment=PYTHONPATH=/ganuda
```

Wednesday 5 AM — between Owl Debt Reckoning (Wed 5 AM) and the weekend. Adjust if collision.

## Testing

1. **Integrity pass**: All hashes match → zero failures
2. **Integrity fail**: Manually corrupt one hash → verify quarantine triggered
3. **NEVER_SEND catch**: Insert skill with node name → verify flagged
4. **Cold pruning**: Insert skill with created_at 31 days ago, never used → verify retired
5. **Report format**: Run audit → verify JSON output matches expected schema

## Definition of Done

- [ ] `/ganuda/scripts/skill_drift_audit.py` created
- [ ] Systemd timer + service files created
- [ ] Timer enabled on redfin
- [ ] Integrity, NEVER_SEND, DC violation, cold pruning all working
- [ ] Report output matches expected format
- [ ] All 5 tests pass
