# Jr Briefing: Pending Tasks - January 6, 2026

**TPM**: Flying Squirrel (dereadi)
**Hardware Status**: goldfin/silverfin delayed to January 7, 2026
**Priority**: Start with tasks that don't require new hardware

---

## Task Priority Order

| Priority | Task | Node | Blocked By |
|----------|------|------|------------|
| 1 | Council Enhancement (DeepMind validated) | redfin | Nothing - START NOW |
| 2 | Software Repository Setup | bluefin/greenfin | Nothing - START NOW |
| 3 | Switch VLAN Configuration | 192.168.132.132 | Hardware (Jan 7) |
| 4 | Trunk Port + Verbose Logging | switch + greenfin | Hardware (Jan 7) |

---

## PRIORITY 1: Council Enhancement

**Jr Instruction**: `/Users/Shared/ganuda/docs/jr_instructions/JR-COUNCIL-ENHANCEMENT-DEEPMIND-VALIDATED-JAN2026.md`

**What**: Enhance the 7-Specialist Council with DeepMind-validated self-critique patterns

**Scope** (Revised per Council feedback):
- ✅ Phase A: Create 7 YAML constraint files
- ✅ Phase B: Add state transition output to votes
- ❌ Phase C: SKIPPED (multi-pass voting - Peace Chief delay concern)
- ✅ Phase D: Lightweight security advisory flagging

**Node**: redfin (192.168.132.223)

**Files to Create**:
```
/ganuda/lib/specialist_constraints/
├── crawdad.yaml
├── gecko.yaml
├── turtle.yaml
├── eagle_eye.yaml
├── spider.yaml
├── peace_chief.yaml
└── raven.yaml

/ganuda/lib/constraint_loader.py
```

**Estimated Effort**: Medium (2-3 hours)

**Verification**:
```bash
# Test constraint loading
python3 -c "from constraint_loader import get_all_constraints; print(len(get_all_constraints()))"
# Should output: 7

# Test council vote with constraints
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"question": "Test constraint injection", "context": {}}'
```

---

## PRIORITY 2: Software Repository Setup

**Jr Instruction**: `/Users/Shared/ganuda/docs/jr_instructions/JR-SOFTWARE-REPO-SANCTUM-PATCHING-JAN6-2026.md`

**What**: Set up apt-mirror on bluefin so Sanctum nodes (goldfin/silverfin) can patch without internet

**Why Now**: Repository sync takes hours. Start now so it's ready when hardware arrives.

**Nodes**:
- bluefin (192.168.132.222) - storage + Apache
- greenfin (192.168.132.224) - Ansible management

**Tasks**:
1. Install apt-mirror on bluefin
2. Configure mirror.list (Ubuntu 22.04 jammy)
3. Create directory structure at `/ganuda/repo/apt-mirror`
4. Start initial sync (runs in background)
5. Configure Apache virtual host
6. Create Ansible playbook for Sanctum patching

**Estimated Effort**:
- Setup: 1 hour
- Initial sync: 4-8 hours (background)

**Start Command**:
```bash
# On bluefin
sudo apt update && sudo apt install apt-mirror apache2 -y
sudo mkdir -p /ganuda/repo/apt-mirror
```

---

## PRIORITY 3: Switch VLAN Configuration (BLOCKED - Jan 7)

**Jr Instruction**: `/Users/Shared/ganuda/docs/jr_instructions/JR-SWITCH-HARDENING-VLAN-JAN6-2026.md`

**What**: Configure VLANs on TP-Link TL-SG1428PE for Sanctum isolation

**Blocked By**: goldfin/silverfin hardware not yet connected

**Pre-work available**:
- Review Jr instruction
- Verify switch access at http://192.168.132.132 (credentials updated)
- Document current port assignments

**VLANs to Create**:
| VLAN | Name | Ports | Purpose |
|------|------|-------|---------|
| 1 | Compute | 1-12, 17-26 | redfin, bluefin, greenfin |
| 10 | Identity | 13-14 | silverfin (FreeIPA) |
| 20 | Sanctum | 15-16 | goldfin (PII) |
| 99 | Management | 27-28 | Switch mgmt |

---

## PRIORITY 4: Trunk Port + Verbose Logging (BLOCKED - Jan 7)

**Jr Instruction**: `/Users/Shared/ganuda/docs/jr_instructions/JR-TRUNK-PORT-VERBOSE-LOGGING-JAN6-2026.md`

**What**: Configure port 17 as trunk so greenfin can access all VLANs for Ansible patching

**Blocked By**: VLANs must be created first (Priority 3)

**Pre-work available**:
- Review Jr instruction
- Prepare netplan config for greenfin VLAN interfaces
- Prepare iptables logging rules

---

## Other Jr Instructions (Reference)

These are written but lower priority:

| Instruction | Status |
|-------------|--------|
| `vlan_sanctum_setup_jr.md` | Superseded by JR-SWITCH-HARDENING |
| `JR-INTERNET-JR-ROUTER-CRAWL-JAN6-2026.md` | Web4UI crawler task |

---

## Daily Standup Format

When reporting progress, please update thermal memory:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score,
    tags, source_triad, source_node, memory_type
) VALUES (
    md5('jr_progress_YYYYMMDD_taskname'),
    'JR PROGRESS: [task] - [status] - [blockers if any]',
    70.0,
    ARRAY['jr-progress', 'january-2026'],
    'ops',
    '[node]',
    'operations'
);
```

---

## Contacts

- **TPM**: Flying Squirrel (dereadi) - available via Claude Code CLI
- **Council API**: http://192.168.132.223:8080/v1/council/vote
- **Thermal Memory**: bluefin:5432 / zammad_production

---

## For Seven Generations

Start with Priority 1 and 2 today. Hardware arrives tomorrow for Priority 3 and 4.

Let's build this right.
