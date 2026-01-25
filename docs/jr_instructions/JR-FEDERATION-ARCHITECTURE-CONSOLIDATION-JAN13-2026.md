# Jr Instructions: Federation Architecture Consolidation

**Task ID**: ARCH-CONSOLIDATION-001
**Priority**: CRITICAL (P0)
**Date**: January 13, 2026
**Target Nodes**: greenfin, bluefin, redfin
**Assigned To**: IT Triad Jr + Executive Jr
**Council Approval**: Obtained (confidence 0.794, 1 Crawdad security concern noted)

---

## Executive Summary

The Federation has experienced architecture drift ("split-brain"). Multiple nodes are running duplicate or conflicting services, causing:
- 17GB RAM wasted on greenfin (old Cherokee Triad with local model)
- GPU VRAM exhaustion on redfin (IT Triad was loading 25GB local model)
- Duplicate Ollama instances (redfin + greenfin)
- Duplicate Executive Jr (redfin + bluefin)
- 8 VetAssist Jr instructions written but 0 executed in 27 days

**Council Consensus**: Consolidate services per node role. All inference through Gateway API so Jrs can learn.

---

## Target Architecture (Post-Consolidation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FEDERATION CANONICAL ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REDFIN (192.168.132.223) - GPU Inference Node                             │
│  ├── vLLM (port 8000) - Qwen 32B AWQ                                       │
│  ├── LLM Gateway (port 8080) - ALL inference routes here                   │
│  ├── SAG UI (port 4000) - ITSM frontend                                    │
│  ├── Ollama (port 11434) - Embedding models ONLY                           │
│  ├── Telegram Chief (singleton)                                            │
│  ├── IT Triad (uses Gateway API, NOT local models)                         │
│  └── Monitoring Dashboard, Heartbeat                                       │
│                                                                             │
│  BLUEFIN (192.168.132.222) - Database + Coordination                       │
│  ├── PostgreSQL (port 5432) - zammad_production, triad_federation          │
│  ├── Home Assistant (port 8123)                                            │
│  ├── Frigate NVR (port 8971)                                               │
│  ├── Executive Jr (singleton - coordinates Jrs)                            │
│  ├── Cherokee Legal Council (uses Gateway API)                             │
│  ├── WOPR Crawler                                                          │
│  └── Supabase stack (image search)                                         │
│                                                                             │
│  GREENFIN (192.168.132.224) - Router + Daemons                             │
│  ├── nftables router (VLANs 1/10/20)                                       │
│  ├── Jr execution daemons (uses Gateway API)                               │
│  ├── Sacred Fire daemon                                                    │
│  ├── Thermal memory purge                                                  │
│  ├── Promtail (log forwarding)                                             │
│  └── Heartbeat                                                             │
│  ├── STOP: Old Cherokee Triad (frees 17GB RAM)                             │
│  └── STOP: Ollama (use redfin's Ollama)                                    │
│                                                                             │
│  SILVERFIN (192.168.10.10) - Identity (VLAN 10/DMZ)                        │
│  └── FreeIPA (CHEROKEE.LOCAL realm)                                        │
│                                                                             │
│  GOLDFIN (192.168.20.10) - PII Sanctum (VLAN 20)                           │
│  └── vetassist_pii database (pending FreeIPA domain join)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Stop Old Cherokee Triad on Greenfin

### Why
The old Cherokee Triad on greenfin is loading a local model (17GB RAM) instead of using the Gateway API. This is legacy code from before the January 5 refactor.

### Commands (Run on greenfin as root/dereadi)

```bash
# SSH to greenfin
ssh dereadi@192.168.132.224

# Find the old triad process
ps aux | grep -E "(cherokee_triad|python.*triad)" | grep -v grep

# If found, get the PID and kill it
# pkill -f "cherokee_triad"

# Or if running as systemd:
sudo systemctl stop cherokee-triad.service
sudo systemctl disable cherokee-triad.service

# Verify RAM freed
free -h
```

### Verification
- Memory usage should drop by ~17GB
- No python processes loading transformers models

---

## Step 2: Stop Ollama on Greenfin

### Why
Ollama is running on BOTH redfin AND greenfin. Only need one instance (redfin).

### Commands (Run on greenfin)

```bash
# Check if Ollama running
systemctl status ollama

# Stop and disable
sudo systemctl stop ollama
sudo systemctl disable ollama

# Verify
curl http://localhost:11434/api/tags  # Should fail
```

### Configuration Update
Update any scripts on greenfin that use `localhost:11434` to use `192.168.132.223:11434` (redfin).

---

## Step 3: Stop Duplicate Executive Jr on Redfin

### Why
Executive Jr should only run on bluefin (coordination node). Running on redfin creates duplicate task assignments.

### Commands (Run on redfin)

```bash
# SSH to redfin
ssh dereadi@192.168.132.223

# Find Executive Jr
ps aux | grep -E "executive.*jr|exec_jr" | grep -v grep

# Stop it
pkill -f "executive_jr"

# Or if systemd:
sudo systemctl stop executive-jr-autonomic.service
sudo systemctl disable executive-jr-autonomic.service
```

---

## Step 4: Verify IT Triad Uses Gateway API

### Why
The IT Triad on redfin was loading a 25GB local model because `it_chief.py` imports from `/home/dereadi/cherokee_triad/jr_base.py` (old code) instead of `/home/dereadi/it_triad/jr_base.py` (refactored).

### Fix Already Applied (January 13, 2026)
```bash
cp /home/dereadi/it_triad/jr_base.py /home/dereadi/cherokee_triad/jr_base.py
```

### Verification
```bash
# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# IT Triad should NOT appear in GPU processes
nvidia-smi | grep -i python

# vLLM should be the primary GPU user (~60GB)
```

---

## Step 5: Update Service Registry

### Write to thermal_memory

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'FEDERATION ARCHITECTURE CONSOLIDATED - January 13, 2026

CHANGES APPLIED:
1. Stopped old Cherokee Triad on greenfin (freed 17GB RAM)
2. Stopped Ollama on greenfin (use redfin''s instance)
3. Stopped duplicate Executive Jr on redfin (runs on bluefin only)
4. Fixed IT Triad on redfin to use Gateway API (freed 25GB VRAM)

CANONICAL ARCHITECTURE:
- REDFIN: vLLM + Gateway + SAG + Ollama + IT Triad (Gateway mode)
- BLUEFIN: PostgreSQL + Home Assistant + Executive Jr + Legal Council
- GREENFIN: Router + Jr daemons + Sacred Fire (NO local models)

ALL INFERENCE THROUGH GATEWAY API (port 8080)
This allows Jrs to observe ALL requests and learn.

Council approved with 0.794 confidence. Crawdad noted security concern addressed.

For Seven Generations.',
  98, 'tpm',
  ARRAY['architecture', 'consolidation', 'council-approved', 'january-2026'],
  'federation'
);
```

---

## Step 6: Ensure Jrs Can Observe and Learn

### Architecture Principle
The Gateway API at `http://192.168.132.223:8080` should be the ONLY path for LLM inference. This allows:
- Centralized logging of all requests
- Jr agents to observe patterns
- Council to review decisions
- Thermal memory to capture learnings

### Configuration Check

All scripts should use:
```python
GATEWAY_URL = "http://192.168.132.223:8080/v1/chat/completions"
# NOT: local model loading
# NOT: http://localhost:11434 (Ollama direct)
```

### Jr Learning Loop
```
User/Service → Gateway API → vLLM → Response
                    ↓
              Logged to thermal_memory
                    ↓
              Jr agents observe
                    ↓
              Jrs update their patterns
```

---

## Step 7: Architecture Enforcement (Ongoing)

### Daily Check Script (Cron on greenfin)

Create `/ganuda/scripts/architecture_check.sh`:

```bash
#!/bin/bash
# Architecture enforcement check
# Runs daily at 05:00

VIOLATIONS=""

# Check: No local models on greenfin
if pgrep -f "transformers|AutoModelForCausalLM" > /dev/null; then
    VIOLATIONS="$VIOLATIONS\n- greenfin running local models!"
fi

# Check: No Ollama on greenfin
if systemctl is-active ollama > /dev/null 2>&1; then
    VIOLATIONS="$VIOLATIONS\n- Ollama running on greenfin!"
fi

# Check: Gateway is reachable
if ! curl -s http://192.168.132.223:8080/health | grep -q "healthy"; then
    VIOLATIONS="$VIOLATIONS\n- Gateway API not healthy!"
fi

# Report to thermal memory if violations
if [ -n "$VIOLATIONS" ]; then
    PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
    INSERT INTO triad_shared_memories (content, temperature, source_triad, tags)
    VALUES ('ARCHITECTURE VIOLATION DETECTED:\n$VIOLATIONS', 95, 'eagle_eye', ARRAY['alert', 'architecture', 'violation']);"
fi
```

---

## Success Criteria

- [ ] greenfin RAM usage < 8GB (was 17GB+ with old triad)
- [ ] Only redfin running Ollama (port 11434)
- [ ] Only bluefin running Executive Jr
- [ ] IT Triad on redfin using Gateway API (0 GPU usage from triad)
- [ ] vLLM healthy on port 8000
- [ ] Gateway healthy on port 8080
- [ ] All Jr instructions can be executed (vLLM available)
- [ ] Thermal memory updated with consolidation record

---

## Rollback Plan

If issues arise:
1. Executive Jr on redfin: `sudo systemctl start executive-jr-autonomic`
2. Ollama on greenfin: `sudo systemctl start ollama`
3. Old Triad on greenfin: `sudo systemctl start cherokee-triad`

Note: Rollback means returning to split-brain state. Only do if consolidation causes service failures.

---

*For Seven Generations*
