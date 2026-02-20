# JR-SECURITY-AUDIT-MOLTBOOK-MCP-FEB04-2026

## Priority: P0 (Blocks #585)
## Assignee: Security Jr (Crawdad delegation)
## Estimated Effort: 4-6 hours
## Audit Tier: 3 (Deep Audit)

## Context

The TPM proposed installing the Moltbook MCP server for automated engagement monitoring. Council vote 1fbe7767c0b0babc returned REVIEW REQUIRED with 5 concerns. Per the newly established GitHub Security Audit Protocol, Tier 3 audit is required before installation.

**Repository:** https://github.com/terminalcraft/moltbook-mcp
**Purpose:** MCP server for Moltbook (AI agent social platform) integration
**Risk Level:** HIGH — runs as MCP server with API access, network capabilities

## Audit Scope

This is an external dependency from an untrusted source. Full Tier 3 audit required.

## Deliverables

### 1. Clone to Staging (NOT Production)

```bash
mkdir -p /ganuda/staging/security-review
cd /ganuda/staging/security-review
git clone https://github.com/terminalcraft/moltbook-mcp.git
cd moltbook-mcp
```

**DO NOT clone to /ganuda/services until audit approved.**

### 2. Repository Metadata Review

Document in audit report:
- [ ] Repository creation date
- [ ] Last commit date
- [ ] Number of contributors
- [ ] Contributor profiles (are they real? established?)
- [ ] Star/fork count
- [ ] Open issues, especially security-related
- [ ] Any CVEs or security advisories
- [ ] License (compatibility with our use)

### 3. Static Code Analysis

Review all JavaScript files for:

**Credential Access:**
- [ ] API key handling — where stored, how accessed
- [ ] Token management
- [ ] Password/secret patterns
- [ ] Environment variable access

**Network Calls:**
- [ ] All fetch/axios/http calls — document every endpoint
- [ ] Where does data go? (Moltbook API only, or elsewhere?)
- [ ] Any unexpected outbound connections
- [ ] WebSocket connections

**Filesystem Access:**
- [ ] What files does it read?
- [ ] What files does it write?
- [ ] Any access outside expected paths?
- [ ] State file location and contents

**Code Execution:**
- [ ] Any eval() or Function() calls
- [ ] Any exec/spawn/subprocess patterns
- [ ] Dynamic code loading
- [ ] Require/import of user-controlled paths

**Data Exfiltration Vectors:**
- [ ] What data could be sent externally?
- [ ] Is our content/credentials protected?
- [ ] Could an attacker inject data through this?

### 4. Dependency Tree Audit

```bash
npm install --package-lock-only
npm audit
```

Document:
- [ ] Total number of dependencies (direct + transitive)
- [ ] Any known vulnerabilities (npm audit output)
- [ ] High-risk dependencies (eval, network, filesystem access)
- [ ] Dependency age and maintenance status

### 5. Sandboxed Execution Test

Run in isolated environment with network monitoring:

```bash
# Create isolated test environment
# Monitor all network traffic during execution
# Log all filesystem access
# Test each tool individually
```

Document:
- [ ] Actual network calls made (compare to declared)
- [ ] Actual filesystem access (compare to declared)
- [ ] Behavior matches documentation?
- [ ] Any unexpected activity?

### 6. Outbound Filter Review

The MCP claims to have "outbound secret-leak detection." Verify:
- [ ] What patterns does it catch?
- [ ] Are our Cherokee-specific patterns covered?
- [ ] Can the filter be bypassed?
- [ ] Is it actually enforced or optional?

### 7. Prompt Injection Defense Review

The MCP claims "inbound sanitization (prompt injection defense)." Verify:
- [ ] What sanitization is applied?
- [ ] Test with known injection patterns
- [ ] Can it be bypassed?

### 8. Produce Audit Report

Create `/ganuda/docs/security/audits/moltbook-mcp-audit.md` with:
- Summary of findings
- Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Specific concerns identified
- Mitigations required before approval
- Recommendation (APPROVE / REJECT / APPROVE WITH CONDITIONS)

## Approval Process

After audit completion:
1. Submit audit report to council
2. Crawdad must explicitly approve
3. Council re-vote with audit findings
4. If approved, update `/ganuda/docs/security/approved-packages.yaml`
5. Unblock Jr task #585 for installation

## Rejection Criteria

Automatic REJECT if any of:
- Unexplained outbound network calls
- Credential exfiltration vectors
- Eval/exec of user-controlled input
- Known unpatched vulnerabilities
- Obfuscated code sections
- Dependency on unmaintained packages with known issues

## References

- Protocol: `/ganuda/docs/protocols/GITHUB-SECURITY-AUDIT-PROTOCOL.md`
- Pending package: `/ganuda/docs/security/approved-packages.yaml`
- Blocked task: Jr #585 (Moltbook MCP Integration)
- Council vote: 1fbe7767c0b0babc

---
*Cherokee AI Federation — Security*
*ᎠᏎᏃ ᎠᏂᎦᏔᎲᏍᎩ — Trust but verify.*
