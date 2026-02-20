# KB: Ansible Foundation — Federation Infrastructure as Code

**Date**: February 14, 2026
**Kanban**: #1755
**Jr Tasks**: #745 (Phase 1 Foundation), #746 (Phase 2 Linux), #747 (Phase 3 macOS)
**Status**: All 3 phases COMPLETED
**River Cycle**: RC-2026-02C

## Summary

Deployed Ansible infrastructure-as-code framework across the 6-node Cherokee AI Federation. Establishes reproducible configuration management, enabling disaster recovery, new node provisioning, and drift detection via playbook-driven state enforcement.

## Architecture

```
/ganuda/ansible/
├── ansible.cfg              # ARA callback, SSH pipelining, fact caching
├── inventory.ini            # 6 nodes: 3 linux, 2 macos, gpu_nodes group
├── requirements.yml         # Galaxy collections (community.postgresql, etc.)
├── group_vars/
│   ├── linux.yml            # Security hardening, nftables, systemd defaults
│   ├── macos.yml            # Homebrew, launchd, macOS-specific config
│   └── gpu_nodes.yml        # NVIDIA driver, vLLM, CUDA, GPU monitoring
├── host_vars/
│   ├── redfin.yml           # Port 8000/8080, vLLM, gateway, SAG
│   ├── bluefin.yml          # PostgreSQL, VLM, YOLO, tribal-vision
│   ├── greenfin.yml         # Monitoring, embedding, promtail
│   ├── sasass.yml           # Mac Studio edge node
│   └── sasass2.yml          # Mac Studio edge node
├── playbooks/
│   ├── site.yml             # Master orchestrator (imports all below)
│   ├── sync-federation.yml  # /ganuda/ directory sync across nodes
│   ├── deploy-services.yml  # Systemd service deployment + restart
│   ├── deploy-firewall.yml  # nftables rules from config/nftables-*.conf
│   ├── deploy-macos.yml     # Homebrew, launchd, macOS config
│   ├── smoke-test.yml       # Post-deploy health checks (vLLM, gateway, DB)
│   ├── redfin-caddy.yml     # Caddy reverse proxy config
│   └── greenfin-firewall.yml # Greenfin-specific nftables
├── roles/                   # (empty — role structure pending)
├── templates/
│   └── remediation/         # Self-healing Jinja2 templates (see KB-LLM-ANSIBLE-SELF-HEALING)
├── remediation/             # Self-healing pipeline Python modules
├── rulebooks/               # EDA (Event-Driven Ansible) rulebooks
└── sql/                     # Database triggers (federation_alerts NOTIFY)
```

## Key Design Decisions

### 1. Inventory Structure
- **Linux group**: redfin, bluefin, greenfin (Ubuntu/Debian, systemd)
- **macOS group**: sasass, sasass2 (macOS, launchd/Homebrew)
- **gpu_nodes group**: redfin, bluefin (NVIDIA GPUs, vLLM/VLM services)
- bmasass (M4 Max) intentionally excluded — air-gapped dark council, not in Ansible management

### 2. ARA Integration
- `ansible.cfg` includes ARA callback plugin for execution recording
- Playbook results stored to PostgreSQL (when ARA server deployed)
- Feeds into self-healing thermal memory feedback loop (#1781)

### 3. SSH Pipelining
- Enabled in `ansible.cfg` for performance
- Requires `requiretty` disabled in sudoers on managed nodes (already the case)

### 4. Fact Caching
- JSON file-based fact cache at `/ganuda/ansible/.fact_cache/`
- 24-hour TTL — reduces gather_facts overhead on repeated runs

## Host Variables Reference

### redfin (192.168.132.223)
- GPU: RTX PRO 6000 96GB (Blackwell)
- Services: vllm (8000), llm-gateway (8080), sag (4000), vetassist, telegram-chief
- Caddy reverse proxy for HTTPS

### bluefin (192.168.132.222)
- GPU: RTX 5070
- PostgreSQL: zammad_production (1,694 tickets, 50+ custom tables, 89K+ thermal memories)
- Services: vlm-bluefin (8090), vlm-adapter (8092), yolo-world (8091), optic-nerve, tribal-vision

### greenfin (192.168.132.224)
- No GPU
- Monitoring: OpenObserve, promtail (9080)
- Services: cherokee-embedding (8003), cherokee-thermal-purge

### sasass/sasass2 (192.168.132.241/242)
- Mac Studios — edge development nodes
- Homebrew package management, launchd services

## Deployment

```text
# Dry run (check mode)
ansible-playbook -i /ganuda/ansible/inventory.ini /ganuda/ansible/playbooks/site.yml --check

# Deploy to specific node
ansible-playbook -i /ganuda/ansible/inventory.ini /ganuda/ansible/playbooks/deploy-services.yml --limit redfin

# Smoke test after deploy
ansible-playbook -i /ganuda/ansible/inventory.ini /ganuda/ansible/playbooks/smoke-test.yml

# Sync /ganuda/ across federation
ansible-playbook -i /ganuda/ansible/inventory.ini /ganuda/ansible/playbooks/sync-federation.yml
```

## Dependencies

```text
# Install on control node (redfin)
pip install ansible ansible-lint ara[server]

# Install Galaxy collections
ansible-galaxy collection install -r /ganuda/ansible/requirements.yml
```

## Pending Work

1. **Roles**: No roles created yet — playbooks are flat. Future: extract common patterns (systemd service deploy, nftables apply, health check) into reusable roles
2. **Vault**: Ansible Vault for secrets (DB passwords, API keys) — currently in secrets_loader.py and .env files
3. **CI/CD**: No automated playbook testing — manual `--check` runs only
4. **bmasass**: Not in inventory — add when air-gap bridge architecture (#1782) is built
5. **Software repository**: Package mirrors for offline/air-gapped deployment — coordinate with Ansible package management tasks

## Related KBs

- **KB-LLM-ANSIBLE-SELF-HEALING-ARCHITECTURE-FEB14-2026.md** — Self-healing pipeline that generates remediation playbooks
- **KB-POWER-FAILURE-RECOVERY-FEB07-2026** — Manual recovery that Ansible playbooks now codify
- **KB-GREENFIN-NFTABLES-XTABLES-COMPAT-FIX-FEB11-2026.md** — Firewall config now in deploy-firewall.yml

## Lessons Learned

1. **Jr executor multi-Create block limitation**: Phases were split into 3 separate Jr tasks (1 per phase) to avoid the mixed-step-types bug. Each phase had 3-6 Create blocks — all completed successfully because they were Create-only (no SEARCH/REPLACE mixed in).
2. **Host vars are the source of truth**: Port mappings, service lists, and node-specific config belong in host_vars, not hardcoded in playbooks. This matches our CMDB pattern.
3. **Smoke tests are essential**: The `smoke-test.yml` playbook validates deployment by hitting health endpoints — catches issues before users do.
4. **macOS requires separate playbooks**: `brew`, `launchctl`, and macOS paths (`/Users/Shared/ganuda/`) differ enough from Linux to warrant dedicated handling rather than conditional blocks.
