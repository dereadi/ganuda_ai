# ULTRATHINK: P0/P1 GitHub Reconnaissance — Long Man Ordering
*Generated: February 10, 2026 — TPM (Claude Opus 4.6)*
*Method: Long Man Development Methodology — DISCOVER phase*
*Kanban Cross-Reference: #549, #546, #550, #547, #1754, #1749, #1703, #1757, #1755, #1751, #1750*

---

## Ordering Principle

Long Man technique: start with the quickest, least complicated tasks and build momentum upward toward the more complex ones. Each win feeds the next.

---

## TIER 1 — Quick Wins (2-6 hours each)

### 1. PyPDFForm Integration — Kanban #1749
**Complexity: 3-4 hours | Jr: Yes | Sudo: No**

- **Library**: [chinapandaman/PyPDFForm](https://github.com/chinapandaman/PyPDFForm) — mature, well-documented
- **What it does**: Fill VA PDF forms (21-0966, 21-526EZ, etc.) programmatically from Python dict
- **Pattern**: `pip install pypdfform` → create Flask endpoint → accept JSON → return filled PDF
- **Dependencies**: pypdfform (pip), existing VetAssist Flask backend
- **Integration point**: `/ganuda/vetassist/` backend — add `/api/forms/fill` endpoint
- **Risk**: Very low. Library is stable, no system-level changes.

### 2. Automated Health Check Scripts (Tier 1) — Kanban #550
**Complexity: 4-6 hours | Jr: Yes | Sudo: Partial (install only)**

- **Tools**: [Trivy](https://trivy.dev/) (CVE scanner) + [Lynis](https://github.com/CISOfy/lynis) (CIS audit)
- **Pattern**: Install both → create `/ganuda/scripts/security_health_check.sh` → cron daily → JSON output to DB
- **Trivy**: `curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh` — scans filesystem for CVEs
- **Lynis**: `git clone https://github.com/CISOfy/lynis` — runs 300+ CIS benchmark tests, outputs score
- **Output**: Store results in `security_health_checks` table, alert on CRITICAL findings
- **Risk**: Read-only scanning. Zero system modification.

---

## TIER 2 — Medium Effort (8-16 hours each)

### 3. Executor DLQ + Auto-Escalation — Kanban #1750
**Complexity: 16-23 hours | Jr: Yes | Sudo: Schema only**

- **Pattern**: PostgreSQL-backed DLQ (no new infrastructure needed)
- **Reference**: [TaskIQ](https://github.com/taskiq-python/taskiq) lightweight task queue patterns
- **Design**:
  - New table: `jr_failed_tasks_dlq` (original_task_id, failure_reason, escalation_level, retry_count)
  - Escalation levels: L1 auto-retry (3x exponential backoff) → L2 TPM alert → L3 council vote
  - Trigger on `jr_work_queue.status = 'failed'`
  - Webhook to Telegram for L2+ escalations
- **Integration**: Hooks into `task_executor.py` exception handling (~line 600)
- **Depends on**: Nothing. Can deploy immediately.

### 4. Presidio PII Integration — Kanban #1703
**Complexity: 12-16 hours | Jr: Yes | Sudo: Docker pull only**

- **Tool**: [microsoft/presidio](https://github.com/microsoft/presidio) — NLP + regex PII detection
- **Docker**: `docker pull mcr.microsoft.com/presidio-analyzer` (port 5002), `presidio-anonymizer` (port 5001)
- **Custom recognizers needed**:
  - VA File Number (8-9 digits, BIRLS format)
  - Military Service Number (pre-1974 format)
  - DD-214 document patterns
  - SSN (built-in but needs military context weighting)
- **Integration**: VetAssist backend calls Presidio API before storing/displaying veteran data
- **Reference**: [Presidio Custom Recognizers Guide](https://microsoft.github.io/presidio/samples/python/customizing_presidio_analyzer/)
- **Risk**: Low. Runs as isolated Docker service.

### 5. FreeIPA Vault Password Migration — Kanban #1754
**Complexity: 8-12 hours | Jr: Partial | Sudo: Yes (vault ops)**

- **Tool**: [freeipa/ansible-freeipa](https://github.com/freeipa/ansible-freeipa) — official `ipavault` module
- **Prerequisite**: KRA (Key Recovery Authority) service must be enabled on FreeIPA server
- **Pattern**:
  1. Inventory 32 edge-case password files (already identified)
  2. Script to read each, create vault entry via `ansible.builtin.ipa_vault`
  3. Update consuming scripts to use `ipa vault-retrieve` instead of file read
  4. Archive original files (don't delete until verified)
- **Reference**: [ansible-freeipa vault README](https://github.com/freeipa/ansible-freeipa/blob/master/README-vault.md)
- **Risk**: Medium. Secrets migration requires careful validation.

### 6. Tailscale ACL Spoke Quarantine — Kanban #546
**Complexity: 8-12 hours | Jr: Config only | Sudo: No**

- **Tool**: [tailscale/gitops-acl-action](https://github.com/tailscale/gitops-acl-action) — GitOps ACL management
- **Pattern**:
  - Export current ACL → `policy.hujson`
  - Define groups: hub, spoke-trusted, spoke-quarantine
  - Rules: hub→all (accept), spoke→spoke (deny), quarantine→hub-only
  - Store in GitHub, sync via gitops-acl-action
  - ACL unit tests to prevent accidental lockout
- **Reference**: [pomerium/awesome-zero-trust](https://github.com/pomerium/awesome-zero-trust)
- **Risk**: Medium. Misconfigured ACLs can lock out nodes. Test in dry-run first.

---

## TIER 3 — Substantial Effort (20-35 hours each)

### 7. Executor Step-Level Checkpointing — Kanban #1751
**Complexity: 20-30 hours | Jr: Yes | Sudo: Schema only**

- **Pattern**: Saga + lightweight DB + `@checkpoint_step` decorator
- **References**:
  - [DBOS](https://dbos.dev/) — database-oriented checkpointing
  - [python-checkpointing](https://github.com/a-rahimi/python-checkpointing) — generator-based
  - Already have: `/ganuda/lib/saga_transactions.py` (deployed Feb 10)
- **Design**:
  - New table: `task_execution_checkpoint` (task_id, step_number, step_status, input_context, output, worker_pid)
  - On startup: scan for crashed tasks (status=EXECUTING, stale worker_pid)
  - Resume from last successful checkpoint
  - Failed steps → DLQ (depends on #1750)
- **Depends on**: DLQ (#1750) should be deployed first
- **Risk**: Medium. Requires careful testing (chaos test: kill mid-execution).

### 8. FreeIPA Client Enrollment — Kanban #1757
**Complexity: 12-20 hours | Jr: Playbook | Sudo: Yes (ipa-client-install)**

- **Tool**: [freeipa/ansible-freeipa](https://github.com/freeipa/ansible-freeipa) — `ipaclient` role
- **Nodes**: redfin, greenfin, bluefin (Linux), bmasass (macOS — limited support)
- **Pattern**:
  - Ansible playbook using `ipaclient` role
  - HBAC rules per node (who can SSH where)
  - Sudo rules via FreeIPA (replaces local sudoers)
  - Kerberos SSO across federation
- **Prerequisite**: FreeIPA server must be running (silverfin)
- **Risk**: Medium-High. Client enrollment modifies PAM, SSSD, DNS resolution.

### 9. Ansible Playbooks for 5 Nodes — Kanban #1755
**Complexity: 25-35 hours | Jr: Roles | Sudo: Yes (deployment)**

- **Reference**: [Ansible-Lockdown CIS Benchmarks](https://ansible-lockdown.readthedocs.io/en/latest/CIS/CIS_table.html)
- **CIS Role**: [MVladislav/ansible-cis-ubuntu-2404](https://github.com/MVladislav/ansible-cis-ubuntu-2404) — full v1.0.0 compliance
- **Hardening Script**: [gensecaihq/Ubuntu-Security-Hardening-Script](https://github.com/gensecaihq/Ubuntu-Security-Hardening-Script) — OpenSCAP + DISA-STIG
- **Structure**:
  ```
  /ganuda/ansible/
  ├── inventory/
  │   ├── hosts.yml (all 9 nodes)
  │   └── group_vars/
  ├── roles/
  │   ├── baseline/ (CIS Level 1)
  │   ├── gpu_node/ (redfin, bluefin)
  │   ├── db_node/ (bluefin)
  │   ├── macos_node/ (bmasass, sasass, sasass2)
  │   └── web_node/ (owlfin, eaglefin — future)
  ├── playbooks/
  │   ├── site.yml
  │   ├── harden.yml
  │   └── deploy_services.yml
  └── README.md
  ```
- **Risk**: Low per-role, but full deployment requires staged rollout.

### 10. Firewall Hardening — Kanban #547
**Complexity: 12-28 hours | Jr: Rules | Sudo: Yes**

- **Tool**: [ipr-cnrs/nftables](https://github.com/ipr-cnrs/nftables) — Ansible role for nftables
- **CIS Baseline**: Ubuntu 24.04 defaults to nftables (not iptables)
- **Design**: Hub (redfin) accepts from all spokes, spokes only reach hub, quarantine tier for untrusted devices
- **Depends on**: Ansible playbook structure (#1755) for deployment
- **Risk**: High. Misconfigured rules = node lockout. Requires console access fallback plan.

### 11. MVT/Pegasus Defense — Kanban #549
**Complexity: 16-24 hours (fleet) | Jr: Wrapper | Sudo: No**

- **Tool**: [mvt-project/mvt](https://github.com/mvt-project/mvt) — Amnesty International's Mobile Verification Toolkit
- **Gap**: No fleet automation exists. MVT is designed for consensual single-device forensics.
- **Custom work**: Device inventory, credential handling, parallel scanning, aggregated reporting
- **Requires**: iOS scanning needs macOS host (bmasass), Android needs USB debugging enabled
- **Risk**: Low (read-only scanning), but fleet orchestration is novel.

---

## DEPENDENCY GRAPH

```
PyPDFForm (#1749) ─── standalone
Health Checks (#550) ─── standalone
DLQ (#1750) ─── standalone
Presidio (#1703) ─── standalone
FreeIPA Vault (#1754) ─── depends on FreeIPA server (silverfin)
Tailscale ACL (#546) ─── standalone
Checkpointing (#1751) ─── depends on DLQ (#1750)
FreeIPA Client (#1757) ─── depends on FreeIPA server (silverfin)
Ansible (#1755) ─── standalone (but feeds #547, #1757)
Firewall (#547) ─── depends on Ansible (#1755)
MVT (#549) ─── standalone
```

---

## RECOMMENDED EXECUTION ORDER (Long Man)

| Wave | Items | Total Hours | Jr Instructions |
|------|-------|-------------|-----------------|
| Wave 1 (Tonight) | PyPDFForm, Health Checks, DLQ | 23-33h | 3 instructions |
| Wave 2 (Tomorrow) | Presidio, FreeIPA Vault, Tailscale ACL | 28-40h | 3 instructions |
| Wave 3 (This Week) | Checkpointing, FreeIPA Client, Ansible | 57-85h | 3 instructions |
| Wave 4 (Next Week) | Firewall, MVT | 28-52h | 2 instructions |

---

## COUNCIL DELIBERATION NOTES

Per Long Man methodology (DISCOVER → DELIBERATE → ADAPT → BUILD → REVIEW):
- **DISCOVER**: Complete (this document)
- **DELIBERATE**: Queue for council vote on Wave 1 priority ordering
- **ADAPT**: Adjust based on council flags (expect Crawdad SECURITY flag on health checks, Eagle Eye VISIBILITY on DLQ)
- **BUILD**: Jr instructions below
- **REVIEW**: Post-execution audit via execution_audit.py

---

*For Seven Generations*
