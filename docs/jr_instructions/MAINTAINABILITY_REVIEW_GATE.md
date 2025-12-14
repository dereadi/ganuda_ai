# Maintainability Review Gate
## Cherokee AI Federation - Standard Pre-Deployment Checklist

**Purpose**: Ensure we never deploy systems we cannot maintain securely for Seven Generations.

**Trigger**: BEFORE any Jr implements code from Jr Build Instructions

**Authority**: Council vote required - any specialist can block deployment

---

## The Flock Safety Lesson

> "80,000 cameras deployed with no public audit. Android 8.1 EOL since 2021 with 900+ CVEs. Button sequence grants root shell. Debug enabled in production. Hardcoded credentials. Data retention claims contradicted by reality."

**We will not become this.**

---

## Pre-Deployment Council Vote

Before implementing ANY service from Jr Build Instructions, the Council must answer:

### 1. SECURITY (Crawdad)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Are credentials hardcoded? | NO | Must use env vars, secrets manager, or FSE |
| Is debug/verbose mode disabled? | YES | Strip before production |
| Are all dependencies current? | YES | No EOL software |
| Is input validated at boundaries? | YES | Never trust external data |
| Are admin interfaces protected? | YES | MFA, IP allowlist, or hardware keys |
| Is data encrypted at rest and in transit? | YES | TLS 1.3, AES-256 minimum |

**Crawdad must sign off: ______________ Date: __________**

### 2. SEVEN GENERATIONS (Turtle)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Who maintains this in 1 year? | Named person/role | Not "someone" |
| Who maintains this in 7 years? | Documented succession | Or sunset plan |
| What happens if maintainer leaves? | Documented handoff | Knowledge transfer plan |
| Is there a sunset/decommission plan? | YES | Nothing lives forever |
| Can we afford to maintain this? | YES | Budget allocated |
| Does this create technical debt? | Documented | Acceptable tradeoffs only |

**Turtle must sign off: ______________ Date: __________**

### 3. VISIBILITY (Eagle Eye)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Can we verify it's working correctly? | YES | Health checks, metrics |
| Can we verify data retention claims? | YES | Automated purge verification |
| Are logs captured and retained? | YES | Audit trail |
| Can we detect if it's compromised? | YES | Integrity monitoring |
| Is there alerting on failures? | YES | TPM notification |
| Can we prove compliance? | YES | Auditable evidence |

**Eagle Eye must sign off: ______________ Date: __________**

### 4. TECHNICAL (Gecko)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Is the code reviewed? | YES | By someone other than author |
| Are there automated tests? | YES | Unit + integration |
| Is rollback possible? | YES | One command restore |
| Is deployment reproducible? | YES | Ansible/script, not manual |
| Is documentation current? | YES | README, inline comments |
| Are dependencies pinned? | YES | No floating versions |

**Gecko must sign off: ______________ Date: __________**

### 5. INTEGRATION (Spider)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Does it fit existing architecture? | YES | No orphan systems |
| Are APIs documented? | YES | OpenAPI/swagger preferred |
| Is naming consistent? | YES | Follows Cherokee conventions |
| Does it integrate with thermal memory? | YES | Knowledge preserved |
| Is there a CMDB entry? | YES | Discoverable |

**Spider must sign off: ______________ Date: __________**

### 6. STRATEGY (Raven)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Does this align with roadmap? | YES | Phase 1/2/3 fit |
| Is the ROI justified? | YES | Benefit > cost |
| Are there better alternatives? | NO | Or documented why not |
| Does this create vendor lock-in? | NO | Or acceptable tradeoff |
| Can this be productized later? | Documented | Revenue opportunity? |

**Raven must sign off: ______________ Date: __________**

### 7. CONSENSUS (Peace Chief)

| Check | Required Answer | Notes |
|-------|-----------------|-------|
| Did all specialists review? | YES | None silenced |
| Are all concerns addressed? | YES | Or documented exceptions |
| Is there unanimous approval? | YES | Or documented dissent |
| Is the resonance preserved? | YES | Harmony between specialists |

**Peace Chief must sign off: ______________ Date: __________**

---

## Deployment Decision

| Outcome | Action |
|---------|--------|
| All 7 sign-offs | DEPLOY |
| 1-2 concerns, mitigations documented | DEPLOY with monitoring |
| 3+ concerns OR any BLOCK | DO NOT DEPLOY - revisit design |
| Any security BLOCK (Crawdad) | HARD STOP - no exceptions |

---

## Post-Deployment Review (30 days)

- [ ] Is the system running as expected?
- [ ] Are there any security incidents?
- [ ] Is maintenance burden acceptable?
- [ ] Should we continue, modify, or sunset?

---

## Template for Jr Instructions Header

Add this block after the metadata in ALL Jr Build Instructions:

```markdown
---

## MAINTAINABILITY REVIEW GATE

**Status**: [ ] NOT REVIEWED / [ ] APPROVED / [ ] BLOCKED

**Council Vote Date**: __________

**Concerns Raised**:
-

**Mitigations Applied**:
-

**Next Review Date**: __________

---
```

---

**For Seven Generations.**
*We build what we can maintain. We maintain what we build.*
*Better to deploy nothing than to deploy a liability.*
