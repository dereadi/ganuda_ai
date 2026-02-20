# GitHub Security Audit Protocol

**Effective:** 2026-02-04
**Authority:** Council Vote (audit_hash: 1fbe7767c0b0babc)
**Status:** MANDATORY

## Rule

**All GitHub pulls from untrusted sources require security audit before installation.**

No exceptions. No "it looks fine." No "it's popular so it's probably safe."

## What Triggers This Protocol

1. Any `git clone` from external repositories
2. Any `npm install` / `pip install` from packages not already in our vetted list
3. Any dependency that pulls code from GitHub at runtime
4. Any MCP server, plugin, or extension from external sources

## Trusted Sources (Audit Waived)

- Anthropic official repositories
- Cherokee AI Federation internal repositories
- Previously audited and approved packages (see `/ganuda/docs/security/approved-packages.yaml`)

## Audit Requirements

### Tier 1: Quick Scan (< 100 lines of code)
- Manual code review by Jr
- Check for: credential access, network calls, filesystem writes, eval/exec patterns
- Document findings in audit log

### Tier 2: Standard Audit (100-1000 lines)
- Automated static analysis (if tooling available)
- Manual review of critical paths
- Dependency tree review (what does IT pull?)
- Council vote required before installation

### Tier 3: Deep Audit (> 1000 lines or high-risk)
- Full code review
- Sandboxed execution test
- Behavioral analysis: does it do what it claims?
- Network traffic analysis during test run
- Council vote with Crawdad explicit approval required

## Audit Checklist

```
[ ] Repository age and activity (avoid brand-new repos)
[ ] Contributor history (who wrote this?)
[ ] Open issues / security advisories
[ ] License compatibility
[ ] Credential access patterns (API keys, tokens, passwords)
[ ] Network calls (where does data go?)
[ ] Filesystem access (what can it read/write?)
[ ] Code execution patterns (eval, exec, subprocess)
[ ] Dependency chain (recursive audit for high-risk deps)
[ ] Outbound data exfiltration vectors
```

## Documentation

Every audit produces:
1. Audit report in `/ganuda/docs/security/audits/`
2. Entry in `approved-packages.yaml` if approved
3. Council vote hash for traceability

## Enforcement

Jr executor will check for audit approval before executing installation tasks. Tasks referencing unaudited external code will be blocked with status `awaiting_security_audit`.

---

*This protocol exists because the council caught a fast-track. Crawdad was right.*

*ᎠᏎᏃ ᎠᏂᎦᏔᎲᏍᎩ — Trust but verify.*

---
**Origin:** Council vote on Moltbook MCP installation (2026-02-04)
**Raised by:** Crawdad (Security), supported by Turtle, Gecko, Peace Chief, Raven
