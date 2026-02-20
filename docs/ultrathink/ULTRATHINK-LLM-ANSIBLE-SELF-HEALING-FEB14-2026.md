# ULTRATHINK: LLM-Ansible Self-Healing Integration

**Date**: February 14, 2026
**Kanban**: #1781 (13 SP, RC-2026-02B)
**Council Vote**: #1872d8f580eaec28 (PROCEED WITH CAUTION, 0.874, Turtle 7GEN CONCERN)
**Method**: Long Man Development Methodology

---

## DISCOVER

### The Problem
Today when a service goes down, Eagle Eye detects it and a thermal memory gets written.
Then a human (TPM) reads Telegram, SSH's into the node, diagnoses, and manually restarts
or patches. Every outage is a bespoke firefight. Feb 7 and Feb 11 power outages proved this
— recovery was manual, slow, and dependent on tribal knowledge in the TPM's head.

### What Already Exists
| Component | Location | Status |
|-----------|----------|--------|
| Sanctuary State | `/ganuda/daemons/sanctuary_state.py` | LIVE — daily 5-phase self-repair |
| Governance Agent | `/ganuda/daemons/governance_agent.py` | LIVE — 30-min drift monitoring |
| Drift Detection | `/ganuda/lib/drift_detection.py` | LIVE — specialist coherence tracking |
| Circuit Breakers | In governance_agent.py | LIVE — per-specialist isolation |
| Keep AIOps | JR-KEEP-AIOPS-INTEGRATION-JAN29-2026.md | STAGED — files written, not deployed |
| Incident Response | INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md | DOCUMENTED — manual execution |
| Ansible Playbooks | `/ganuda/ansible/` | LIVE — Phase 1-3 just completed (Feb 14) |

### The Gap
We have **detection** (Eagle Eye, governance agent, sanctuary state) and we have
**infrastructure-as-code** (Ansible playbooks just landed). What's missing is the
**bridge** — the automated pipeline that turns a detected problem into a validated,
approved, executed remediation playbook.

### Research Findings (Feb 14 DISCOVER)
1. **Event-Driven Ansible (EDA)** — Red Hat's `ansible-rulebook`. Production-grade
   event→response engine with `pg_listener` source for PostgreSQL NOTIFY channels.
   Maps directly to our thermal_memory_archive on PostgreSQL.

2. **ARA (ARA Records Ansible)** — Stores playbook execution results to PostgreSQL.
   Perfect feedback loop into thermal memory. Apache 2.0 license.

3. **MicroRemed (Nov 2025 paper)** — Multi-agent SRE framework: one agent diagnoses,
   another generates Ansible playbooks, a third validates. Maps to:
   Eagle Eye → Qwen 72B → Crawdad.

4. **IBM watsonx Ansible Lightspeed** — RAG-grounded generation constrained to approved
   module whitelist. Guarantees human-readable output because it's templated from YOUR
   existing playbooks. This is how we honor Turtle's 7GEN constraint.

5. **AWX Approval Nodes** — Native pause-and-approve workflow steps with RBAC and
   API-driven approval. Wire to Telegram bot for TPM approve/deny.

## DELIBERATE

### Council Vote Summary (#1872d8f580eaec28)
- **6 of 7 PROCEED**, Turtle raised 7GEN CONCERN
- **Turtle's constraint (user-endorsed)**: All generated playbooks MUST be human-readable
  and maintainable without AI assistance. This is a DESIGN CONSTRAINT, not an afterthought.
- **Crawdad**: No LLM-generated playbook executes without council security review
- **Eagle Eye**: Wants observability at every pipeline stage
- **Gecko**: Performance concern — generation latency must not delay critical remediations

### Design Decisions
1. **Module Whitelist**: LLM can ONLY emit Ansible modules from an approved list
   (systemd, copy, template, command, shell, apt, pip, file, uri, debug, wait_for).
   No `raw`, no `script`, no arbitrary execution.
2. **RAG-Grounded Generation**: Qwen 72B generates playbooks using our existing
   `/ganuda/ansible/` playbooks as few-shot examples via thermal memory semantic search.
3. **Dual Gate**: ansible-lint (syntax) + Crawdad council vote (security) before execution.
4. **--check First**: Always dry-run before real execution. TPM approves the diff.
5. **ARA → Thermal Memory**: Every execution result feeds back as a thermal memory,
   creating a learning loop. Future remediations get smarter.
6. **No Free-Form Generation**: The LLM fills TEMPLATES, not writes from scratch.
   Templates are the human-readable playbooks Turtle demands.

### The Pipeline
```
Eagle Eye / Governance Agent detects anomaly
    │
    ▼
PostgreSQL NOTIFY on 'federation_alerts' channel
    │
    ▼
EDA Rulebook (ansible-rulebook with pg_listener)
    │
    ▼
Remediation Engine (Python)
  ├── Classify alert type (service_down, config_drift, resource_exhaustion)
  ├── RAG search: find similar past remediations in thermal memory
  ├── Select playbook template from /ganuda/ansible/templates/remediation/
  ├── Qwen 72B fills template variables (constrained by module whitelist)
  └── Write candidate playbook to /ganuda/ansible/staging/
    │
    ▼
Validation Gate
  ├── ansible-lint --strict (syntax + best practices)
  ├── ansible-playbook --check --diff (dry run)
  └── Crawdad council vote (security review of generated playbook)
    │
    ▼
TPM Approval (Telegram /approve or /deny with diff preview)
    │
    ▼
Execution (ansible-playbook with ARA callback)
    │
    ▼
ARA records results → thermal_memory_archive
    │
    ▼
Post-execution verification (smoke test playbook)
```

## ADAPT → BUILD

### Phase 1: Alert Bridge + NOTIFY Infrastructure (3 SP)
Create the PostgreSQL trigger function that fires NOTIFY on the `federation_alerts`
channel when high-temperature thermal memories are written. Create the EDA rulebook
YAML that listens on this channel and dispatches to the remediation engine.

**Files:**
- `/ganuda/scripts/sql/create_federation_alerts_trigger.sql` — NOTIFY trigger
- `/ganuda/ansible/rulebooks/federation_alerts.yml` — EDA rulebook
- `/ganuda/ansible/rulebooks/inventory.yml` — EDA-specific inventory

### Phase 2: Remediation Engine + Templates (5 SP)
The core Python engine that receives alerts, classifies them, searches thermal memory
for similar past remediations (RAG), selects a playbook template, and calls Qwen 72B
to fill it. Includes the module whitelist and template library.

**Files:**
- `/ganuda/ansible/remediation/engine.py` — Core remediation engine
- `/ganuda/ansible/remediation/module_whitelist.py` — Approved Ansible modules
- `/ganuda/ansible/remediation/prompt_templates.py` — LLM prompt templates per alert type
- `/ganuda/ansible/templates/remediation/restart_service.yml.j2` — Service restart template
- `/ganuda/ansible/templates/remediation/config_drift.yml.j2` — Config drift template
- `/ganuda/ansible/templates/remediation/resource_cleanup.yml.j2` — Resource exhaustion template

### Phase 3: Validation Pipeline + Crawdad Integration (3 SP)
The validation script that runs ansible-lint, performs dry-run, and submits to the
council for Crawdad's security review. Includes the Crawdad-specific prompt that
evaluates generated playbooks against Cherokee security constraints.

**Files:**
- `/ganuda/ansible/remediation/validator.py` — Lint + dry-run + council vote
- `/ganuda/ansible/remediation/crawdad_review_prompt.py` — Security review prompt template

### Phase 4: ARA Callback + Thermal Memory Feedback (2 SP)
ARA callback plugin configuration and the bridge script that reads ARA execution
results and writes them back to thermal_memory_archive as learnings.

**Files:**
- `/ganuda/ansible/remediation/ara_thermal_bridge.py` — ARA results → thermal memory
- `/ganuda/ansible/ansible.cfg` update — Add ARA callback plugin config

### Deployment Requirements (TPM/sudo — NOT Jr tasks)
- `pip install ansible-rulebook ara[server]` on redfin
- PostgreSQL: CREATE the NOTIFY trigger function
- systemd service for the EDA rulebook daemon
- systemd service for ARA API server
- Telegram bot extension for /approve and /deny (SR blocks on existing bot)

## REVIEW

### Turtle's 7GEN Validation Checklist
- [ ] Can a human read every generated playbook without AI assistance?
- [ ] Are all Ansible modules from the approved whitelist?
- [ ] Do generated playbooks include comments explaining each task?
- [ ] Can the federation operate manually if the LLM is unavailable?
- [ ] Are playbook templates version-controlled and reviewable?

### Crawdad's Security Validation
- [ ] No `raw` or `script` modules in whitelist
- [ ] No credential injection in generated playbooks
- [ ] --check always runs before real execution
- [ ] Council vote required before every execution
- [ ] ARA audit trail is immutable

### Eagle Eye's Observability
- [ ] Every pipeline stage emits a thermal memory
- [ ] Failed validations are visible in SAG dashboard
- [ ] Execution results tracked in ARA and thermal memory
- [ ] Alert → resolution latency is measurable

---

*For Seven Generations — Cherokee AI Federation*
