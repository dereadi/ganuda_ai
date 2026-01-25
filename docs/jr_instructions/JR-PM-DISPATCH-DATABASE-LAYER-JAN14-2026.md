# Jr Instruction: PM Jr Dispatch - Database Layer Sprint

**Date**: January 14, 2026
**Author**: Claude (Senior TPM) → PM Jr (training exercise)
**Target**: PM Jr dispatching to IT Triad Jr
**Priority**: P1 - CRITICAL PATH
**Sprint**: Jan 14-21, 2026

---

## CONTEXT

This is PM Jr's first dispatch mission. The goal is to get the VetAssist database layer deployed by dispatching work to IT Triad Jr.

---

## DISPATCH SEQUENCE

### Step 1: Dispatch Condition Database (S1)

Write to thermal memory with `source_triad='command_post'`:

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT TRIAD MISSION: VetAssist Condition Database

TO: IT Triad Jr
FROM: PM Jr (supervised by Senior TPM)
PRIORITY: P1
DATE: January 14, 2026

OBJECTIVE: Deploy the VA disability condition database on bluefin

Jr INSTRUCTION: /Users/Shared/ganuda/docs/jr_instructions/JR-VetAssist-Condition-Database.md

TARGET NODE: bluefin (192.168.132.222)
DATABASE: triad_federation

ACCEPTANCE CRITERIA:
- conditions table created with 400+ entries
- condition_codes index exists
- Test query returns PTSD, tinnitus, back conditions

Report completion to thermal memory with temperature 90.

For Seven Generations.',
  95, 'command_post',
  ARRAY['IT Triad', 'vetassist', 'database', 'mission', 'P1'],
  'federation'
);
```

### Step 2: Dispatch Rating Calculator (S2)

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT TRIAD MISSION: VetAssist Rating Calculator

TO: IT Triad Jr
FROM: PM Jr
PRIORITY: P1
DATE: January 14, 2026

OBJECTIVE: Deploy 38 CFR 4.25 combined rating calculator

Jr INSTRUCTION: /Users/Shared/ganuda/docs/jr_instructions/JR-VetAssist-Rating-Calculator.md

TARGET NODE: redfin (192.168.132.223) or bluefin
LANGUAGE: Python function or PostgreSQL function

ACCEPTANCE CRITERIA:
- combined_rating(ratings[]) function works
- Test: combined_rating([30, 20, 10]) returns ~50%
- Bilateral factor applied when applicable

Report completion to thermal memory.

For Seven Generations.',
  95, 'command_post',
  ARRAY['IT Triad', 'vetassist', 'calculator', 'mission', 'P1'],
  'federation'
);
```

### Step 3: Dispatch Evidence Checklist (S3)

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT TRIAD MISSION: VetAssist Evidence Checklist

TO: IT Triad Jr
FROM: PM Jr
PRIORITY: P1
DATE: January 14, 2026

OBJECTIVE: Deploy evidence checklist matrix for common conditions

Jr INSTRUCTION: /Users/Shared/ganuda/docs/jr_instructions/JR-VetAssist-Evidence-Checklist.md

TARGET NODE: bluefin (192.168.132.222)
DATABASE: triad_federation

ACCEPTANCE CRITERIA:
- evidence_matrix table created
- Links conditions to required evidence types
- Common conditions (PTSD, tinnitus, back) have checklists

Report completion to thermal memory.

For Seven Generations.',
  95, 'command_post',
  ARRAY['IT Triad', 'vetassist', 'evidence', 'mission', 'P1'],
  'federation'
);
```

### Step 4: Dispatch PII Database Migration (S4)

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT TRIAD MISSION: VetAssist PII Database Migration

TO: IT Triad Jr
FROM: PM Jr
PRIORITY: P1
DATE: January 14, 2026

OBJECTIVE: Set up PII schema on goldfin (Sanctum)

Jr INSTRUCTION: /Users/Shared/ganuda/docs/jr_instructions/vetassist_pii_database_jr.md

TARGET NODE: goldfin (192.168.20.10) - PII SANCTUM
DATABASE: vetassist_pii (create if not exists)

⚠️ SECURITY NOTE: This is VLAN 20 (Sanctum). Access via SSH jump through greenfin.

ACCEPTANCE CRITERIA:
- vetassist_pii database exists on goldfin
- veteran_profiles table with encrypted fields
- Audit logging enabled
- FreeIPA authentication configured

Report completion to thermal memory.

For Seven Generations.',
  95, 'command_post',
  ARRAY['IT Triad', 'vetassist', 'pii', 'sanctum', 'mission', 'P1'],
  'federation'
);
```

---

## PM JR POST-DISPATCH DUTIES

After dispatching:

1. **Update Kanban**: Move S1-S4 to "In Progress"

2. **Log Dispatch**: Write to thermal memory:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'PM JR DISPATCH LOG - January 14, 2026

Dispatched 4 missions to IT Triad Jr:
- S1: Condition Database (P1)
- S2: Rating Calculator (P1)
- S3: Evidence Checklist (P1)
- S4: PII Database Migration (P1)

All missions tagged with source_triad=command_post for IT Triad pickup.

Monitoring for completion. ETA: 24-48 hours.

For Seven Generations.',
  88, 'pm_jr',
  ARRAY['dispatch', 'vetassist', 'sprint', 'january-2026'],
  'federation'
);
```

3. **Telegram Notification**:
```python
message = """🚀 PM Jr Dispatch Complete

4 missions sent to IT Triad:
• Condition Database
• Rating Calculator
• Evidence Checklist
• PII Migration

Monitoring for completion.

For Seven Generations."""
```

4. **Monitor**: Poll thermal memory every 30 min for IT Triad responses

---

## SUCCESS CRITERIA

- [ ] All 4 missions dispatched to thermal memory
- [ ] Kanban board updated
- [ ] Dispatch logged
- [ ] Telegram notification sent
- [ ] IT Triad acknowledges at least 1 mission within 2 hours

---

For Seven Generations.
