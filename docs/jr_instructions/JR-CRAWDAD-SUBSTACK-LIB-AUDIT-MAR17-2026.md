# Jr Instruction: Crawdad Security Audit — python-substack Library

**Ticket**: SUBSTACK-AUDIT-001
**Estimated SP**: 2
**Assigned**: Crawdad (Security) + Spider (Dependency Mapping)
**Blocks**: SUBSTACK-PUBLISH-001 (Deer's publishing pipeline)
**Council Vote**: #9fc9b98bd7368cb7 — REVIEW REQUIRED, 0.25 confidence, 6 concerns

---

## P-Day Countdown

| Step | What | Status |
|------|------|--------|
| **P-3** | Clone repo, read source, trace credential flow | NOT STARTED |
| **P-2** | Dependency audit, network call inventory, flag findings | NOT STARTED |
| **P-1** | Write clearance report or rejection with specific reasons | NOT STARTED |
| **P-Day** | Crawdad signs off → unblocks SUBSTACK-PUBLISH-001 | NOT STARTED |

---

## Objective

Security audit of `ma2za/python-substack` (v0.1.18, 138 stars, 53 commits) before any federation credentials touch it. This library is an unofficial reverse-engineered wrapper around Substack's private API. Council raised CRITICAL/HIGH security concerns. Nothing moves forward until Crawdad clears it.

## Context

- **Library**: https://github.com/ma2za/python-substack
- **No official Substack API exists** — all community reverse-engineering
- **Auth method**: Email/password or browser cookies
- **Council concerns**: Credential exposure through third-party code, unofficial API with undocumented behavior, vendor lock-in, silent publish failures

## Implementation

### P-3: Source Code Review

1. Clone the repository to a sandboxed location:
```bash
cd /tmp
git clone https://github.com/ma2za/python-substack.git
cd python-substack
```

2. **Trace the credential flow end-to-end**:
   - Where do email/password enter the code?
   - How are they stored in memory? Are they ever written to disk?
   - How are they transmitted? (HTTPS only? Any HTTP fallback?)
   - Are session cookies persisted? Where?
   - Is there any telemetry, analytics, or phone-home behavior?

3. **Read every HTTP call**:
   - List every URL the library contacts
   - Verify all calls go to `*.substack.com` and nowhere else
   - Check for any hardcoded URLs, webhook callbacks, or third-party endpoints
   - Look for any data exfiltration vectors (logging credentials, sending to external services)

4. **Check for code injection vectors**:
   - Does the library `eval()` or `exec()` anything?
   - Does it deserialize untrusted data (pickle, yaml.load without SafeLoader)?
   - Does it shell out to any subprocess?

### P-2: Dependency and Supply Chain Audit

1. **Enumerate all dependencies**:
```bash
cat requirements.txt setup.py pyproject.toml | grep -i require
pip install pipdeptree && pipdeptree -p python-substack
```

2. **Check each dependency**:
   - Known vulnerabilities: `pip-audit` or `safety check`
   - Maintenance status (last commit, open CVEs)
   - Any dependency that itself makes network calls

3. **Network call inventory** — produce a table:

| File | Line | URL/Host | Purpose | Credential Sent? |
|------|------|----------|---------|------------------|
| ... | ... | ... | ... | Yes/No |

4. **Flag findings** with severity:
   - CRITICAL: Credentials exposed, data exfiltration, code injection
   - HIGH: HTTP without TLS, credentials logged, abandoned dependency with CVE
   - MEDIUM: No certificate pinning, broad exception handling hiding errors
   - LOW: Missing timeouts, verbose error messages exposing internals

### P-1: Clearance Report

Write a clearance report (1 page max) to `/ganuda/docs/audits/AUDIT-PYTHON-SUBSTACK-MAR2026.md`:

```markdown
# Security Audit: python-substack v0.1.18

**Auditor**: Crawdad (Security Specialist)
**Date**: [date]
**Verdict**: CLEARED / CLEARED WITH CONDITIONS / REJECTED

## Credential Flow
[summary]

## Network Calls
[inventory table]

## Dependencies
[list with vulnerability status]

## Findings
[CRITICAL/HIGH/MEDIUM/LOW items]

## Conditions (if cleared)
[required guardrails before production use]
```

### P-Day: Sign-Off

- If CLEARED or CLEARED WITH CONDITIONS: Crawdad signs off, unblocks SUBSTACK-PUBLISH-001
- If REJECTED: Document specific reasons, suggest alternatives (e.g., direct HTTP calls to Substack API without the wrapper, or Ghost self-hosted)
- Either way, thermalize the audit result (temp 65, tag: security_audit)

## Verification

1. Every HTTP endpoint in the library is documented in the network call inventory
2. Credential flow is traced from input to wire with no gaps
3. All dependencies checked against `pip-audit` or equivalent
4. Clearance report exists at `/ganuda/docs/audits/AUDIT-PYTHON-SUBSTACK-MAR2026.md`
5. Deer is notified of verdict (blocks/unblocks her pipeline)

## What NOT To Do

- Do NOT install the library on any production node — audit in /tmp only
- Do NOT run the library with real credentials during audit — use dummy values
- Do NOT skip the dependency audit — supply chain attacks come through transitive deps
- Do NOT auto-clear because the library has 138 stars — popularity ≠ security
- Do NOT take longer than 2 SP — this is a focused audit, not a pentest
