# KB: LLM-Ansible Self-Healing Architecture

**Date**: February 14, 2026
**Kanban**: #1781 (13 SP, RC-2026-02B)
**Council Vote**: #1872d8f580eaec28 (PROCEED WITH CAUTION, 0.874)
**Related**: KB-ADAPTIVE-GPU-POWER-MONITORING-FEB11-2026, ULTRATHINK-ANSIBLE-FEDERATION-PLAYBOOKS-FEB14-2026

## Summary

Automated remediation pipeline that bridges Eagle Eye detection to Ansible execution
via LLM-generated playbooks. Closes the gap between "we know something is wrong"
and "we fixed it" — the gap that cost us hours during the Feb 7 and Feb 11 outages.

## Architecture

```
Detection Layer (existing)
  └── Eagle Eye / Governance Agent / Sanctuary State
        │
        ▼ PostgreSQL NOTIFY on 'federation_alerts'
        │
Event-Driven Ansible (NEW)
  └── ansible-rulebook with pg_listener source
        │
        ▼ triage_alert.yml
        │
Remediation Engine (NEW)
  ├── Classify alert (Qwen 72B, constrained prompt)
  ├── RAG search thermal_memory_archive for similar past remediations
  ├── Select Jinja2 template (restart_service, config_drift, resource_cleanup)
  ├── LLM fills template variables (module whitelist enforced)
  └── Stage candidate playbook at /ganuda/ansible/staging/
        │
        ▼
Validation Pipeline (NEW)
  ├── Gate 1: ansible-lint --strict
  ├── Gate 2: Module whitelist (Turtle's 7GEN constraint)
  └── Gate 3: Crawdad council vote (security review)
        │
        ▼
TPM Approval (Telegram /approve or /deny)
        │
        ▼
Execution (ansible-playbook with ARA callback)
        │
        ▼
ARA → thermal_memory_archive (learning loop)
```

## Key Design Decisions

1. **LLM fills TEMPLATES, never writes free-form YAML** — Turtle's 7GEN constraint.
   Playbook structure comes from human-written Jinja2 templates. LLM only provides
   variable values (service name, node, file path, etc.)

2. **Module whitelist** — Only 20 approved Ansible modules. No `raw`, `script`, or
   `reboot`. Crawdad's security gate.

3. **Three-gate validation** — ansible-lint (syntax) → whitelist (7GEN) → council vote
   (security). All three must pass before TPM sees the playbook.

4. **--check first** — Dry run always precedes real execution.

5. **Feedback loop** — ARA records every execution. Bridge script writes results to
   thermal_memory_archive with embeddings. Future RAG searches find these, making
   subsequent remediations smarter.

## File Inventory

| File | Purpose |
|------|---------|
| `/ganuda/scripts/sql/create_federation_alerts_trigger.sql` | PostgreSQL NOTIFY trigger |
| `/ganuda/ansible/rulebooks/federation_alerts.yml` | EDA rulebook |
| `/ganuda/ansible/rulebooks/inventory.yml` | EDA inventory |
| `/ganuda/ansible/remediation/triage_alert.yml` | Alert triage playbook |
| `/ganuda/ansible/remediation/engine.py` | Core remediation engine |
| `/ganuda/ansible/remediation/module_whitelist.py` | Approved Ansible modules |
| `/ganuda/ansible/remediation/prompt_templates.py` | LLM prompt templates |
| `/ganuda/ansible/remediation/validator.py` | 3-gate validation pipeline |
| `/ganuda/ansible/remediation/crawdad_review_prompt.py` | Security review prompt |
| `/ganuda/ansible/remediation/ara_thermal_bridge.py` | ARA → thermal memory |
| `/ganuda/ansible/templates/remediation/restart_service.yml.j2` | Service restart template |
| `/ganuda/ansible/templates/remediation/config_drift.yml.j2` | Config drift template |
| `/ganuda/ansible/templates/remediation/resource_cleanup.yml.j2` | Resource cleanup template |

## Dependencies (Manual Install)

```
pip install ansible-rulebook psycopg2-binary ansible-lint "ara[server]" jinja2
```

## Deployment Sequence

1. Deploy PostgreSQL NOTIFY trigger (on bluefin)
2. Install pip dependencies (on redfin)
3. Start ARA server (on redfin)
4. Start EDA rulebook daemon (on redfin)
5. Test with synthetic alert (insert high-temp thermal memory)
6. Verify full pipeline: detect → classify → generate → validate → approve → execute → record

## Research Sources

- **Event-Driven Ansible (EDA)**: Red Hat's ansible-rulebook, pg_listener source
- **ARA (ARA Records Ansible)**: Execution recording to PostgreSQL, Apache 2.0
- **MicroRemed (Nov 2025)**: Multi-agent SRE framework — diagnose → generate → validate
- **IBM watsonx Ansible Lightspeed**: RAG-grounded generation with module whitelist
- **AWX Approval Nodes**: Native pause-and-approve workflow (future enhancement)

## Lessons Learned

- pg_listener is the cleanest bridge between our PostgreSQL-native architecture and
  event-driven automation. No new message bus needed.
- Module whitelist is the key to making Turtle happy — constrain the output space,
  and human-readability follows naturally.
- Three-gate validation may seem heavy, but Feb 11 outage showed what happens when
  changes run without proper gates (Jr executor guardrail blocked >50% file loss).
- ARA feedback loop means the system literally learns from its own remediations.
  First few will be basic, but over time the RAG context gets richer.

---

*For Seven Generations — Cherokee AI Federation*
