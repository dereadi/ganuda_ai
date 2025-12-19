# Cherokee AI Federation - Node IP Mapping

**Updated**: 2025-11-28
**Source**: User confirmation

## IP Address Reference

| Node | Local Network | Tailscale VPN | Role & Services |
|------|---------------|---------------|-----------------|
| **bluefin** | 192.168.132.222 | 100.112.254.96 | PostgreSQL hub (triad_federation, zammad_production) |
| **redfin** | 192.168.132.223 | 100.116.27.89 | GPU dev node, IT Jrs workspace, SAG (:4000), Visual Kanban (:8002) |
| **greenfin** | 192.168.132.224 | 100.100.243.116 | macOS local dev, cherokee_venv |
| **yellowfin** | 192.168.132.221 | TBD | IoT legacy node |
| **bmasass** | 192.168.132.21 | 100.103.27.106 | Mobile device (M4 Max MacBook Pro), travel laptop |
| **sasass** | 192.168.132.241 | TBD | TBD |
| **sasass2** | 192.168.132.242 | TBD | TBD |

## Connection Guidelines

### When on Local Network (Home/Office)
Use local IPs (192.168.132.x):
```bash
# PostgreSQL
psql -h 192.168.132.222 -U claude -d triad_federation

# SSH to redfin
ssh dereadi@192.168.132.223

# Visual Kanban Board
http://192.168.132.223:8002
```

### When Remote (Vegas, Travel, Mobile)
Use Tailscale IPs (100.x.x.x):
```bash
# PostgreSQL (via redfin bridge)
ssh dereadi@100.116.27.89 "psql -h 192.168.132.222 ..."

# SSH to redfin
ssh dereadi@100.116.27.89

# Visual Kanban Board
http://100.116.27.89:8002
```

### From bmasass (Mobile Device)
Always use Tailscale IPs or SSH bridge:
```bash
# Thermal memory access (via redfin)
ssh dereadi@100.116.27.89 'source /home/dereadi/cherokee_venv/bin/activate && python3 -c "
import psycopg2
conn = psycopg2.connect(host=\"192.168.132.222\", user=\"claude\", password=\"jawaseatlasers2\", database=\"triad_federation\")
..."'
```

## PostgreSQL Access Restrictions (pg_hba.conf)

**Allowed hosts** (based on connection testing):
- ✅ localhost (bluefin itself)
- ❌ 100.103.27.106 (bmasass Tailscale) - BLOCKED
- ❌ 100.116.27.89 (redfin Tailscale) - BLOCKED
- ✅ 192.168.132.223 (redfin local) - ALLOWED (needs verification)

**Workaround**: Use redfin as SSH bridge + local IP to bluefin

## Services Running

### bluefin (192.168.132.222 / 100.112.254.96)
- PostgreSQL :5432
- Thermal memory (triad_shared_memories table)
- Zammad database (zammad_production)

### redfin (192.168.132.223 / 100.116.27.89)
- SAG Unified Interface :4000
- Visual Kanban Board :8002 ✅
- Cherokee Desktop :5555
- Grafana :3000
- IT Jrs workspace: /ganuda/

### greenfin (192.168.132.224 / 100.100.243.116)
- macOS local development
- cherokee_venv (Python virtual environment)

### bmasass (192.168.132.21 / 100.103.27.106)
- Mobile command post
- Security-hardened (FileVault, SIP, Gatekeeper)
- Strategic planning and TPM operations

## Air-Gapped Operation Notes

When internet is unavailable:
- Local IPs (192.168.132.x) continue working
- Tailscale IPs (100.x.x.x) may not work
- Federation remains operational on local network
- Thermal memory accessible via local network

## Node Naming Pattern

- **[color]fin** nodes: Primary infrastructure (bluefin, redfin, greenfin, yellowfin)
- **[name]sass** nodes: Security/specialized (bmasass=mobile, sasass, sasass2)

## Complete Cluster

**7 Total Nodes**:
1. bluefin (hub)
2. redfin (GPU/dev)
3. greenfin (macOS local)
4. yellowfin (IoT)
5. bmasass (mobile)
6. sasass
7. sasass2

## Update History

- 2025-11-28 09:45: Complete cluster confirmed (sasass, sasass2 added)
- 2025-11-28 09:15: Initial mapping (bluefin, redfin, greenfin, bmasass)
- Local IP pattern: 192.168.132.x (various subnets)
- Tailscale VPN: 100.x.x.x range
