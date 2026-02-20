# ULTRATHINK: Ansible Playbooks for Cherokee AI Federation

**Date**: February 14, 2026
**Kanban**: #1755 (21 SP, RC-2026-02B)
**Council Vote**: #1bcd4a66217c3a21 (PROCEED, 0.89, unanimous — zero concerns)
**Method**: Long Man Development Methodology

---

## DISCOVER

### Current State
- 2 stub playbooks (greenfin-firewall.yml, redfin-caddy.yml) — reference files that don't exist
- Basic inventory with 6 hosts (redfin, bluefin, greenfin, sasass, sasass2, tpm-macbook)
- No ansible.cfg, no roles/, no group_vars/, no host_vars/

### Infrastructure Inventory
- **45 systemd service files** across /ganuda/scripts/systemd/ and /ganuda/services/
- **3 nftables configs** (redfin, bluefin, greenfin)
- **4 dependency manifests** (redfin, bluefin, greenfin, goldfin)
- **6 KB articles** documenting config management architecture

### Service-Node Affinity
- **redfin** (15 services): vLLM, gateway, SAG, VetAssist, Jr executors, bots
- **bluefin** (7 services): VLM, YOLO, tribal-vision, speed-detector
- **greenfin** (4 services): embedding, thermal-purge, promtail, openobserve
- **sasass** (1 launchd): MLX DeepSeek
- **sasass2** (0 managed): Munki server (nginx, manual)

## DELIBERATE

Council unanimous PROCEED. Key decisions:
1. **3-phase decomposition** approved (Foundation → Linux → macOS)
2. **FreeIPA deferred** — separate effort, not part of this sprint
3. **No Ansible Vault yet** — use secrets_loader.py references
4. **GPU stack ABI-sensitive** — pin exact versions from dependency manifests

## ADAPT → BUILD

### Phase 1: Foundation (8 SP)
- `ansible.cfg` — pipelining, fact caching, yaml output
- `requirements.yml` — ansible.posix, community.general
- `group_vars/linux.yml` — common packages, paths, DB config
- `group_vars/macos.yml` — Homebrew, Munki client
- `group_vars/gpu_nodes.yml` — CUDA, torch, vLLM versions
- `host_vars/` for all 5 nodes — ports, services, firewall configs

### Phase 2: Linux Playbooks (8 SP)
- `sync-federation.yml` — common packages, dirs, fail2ban
- `deploy-services.yml` — systemd units per node (reads managed_services from host_vars)
- `deploy-firewall.yml` — nftables deployment with backup
- `site.yml` — master orchestrator (sync → firewall → services)

### Phase 3: macOS Playbooks (5 SP)
- `deploy-macos.yml` — Homebrew, Munki client/server, launchd plists
- `smoke-test.yml` — connectivity validation for all 5 nodes

### LLM-Ansible Integration Research
- **llm-workflow-engine** (3.7K stars): Uses Ansible playbooks as LLM workflow orchestrator
- **IBM watsonx Code Assistant**: AI-powered Ansible Lightspeed with prompt tuning
- Future: Our council could validate playbooks before execution (Crawdad security review)

## Jr Queue Status
| Task ID | Phase | Status |
|---------|-------|--------|
| 577ae5179... | Phase 1: Foundation | QUEUED |
| 46f2aa006... | Phase 2: Linux | QUEUED |
| 9d74af017... | Phase 3: macOS | QUEUED |

---

*For Seven Generations — Cherokee AI Federation*
