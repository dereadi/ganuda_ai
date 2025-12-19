# RUNBOOK: Cherokee Node Unreachable

## Symptoms
- ping to node IP fails
- SSH connection refused/timeout
- Services on that node unavailable

## Severity
**P2** - Single node failure (federation degrades gracefully)

## Node Reference
| Node | IP | Role | Impact if Down |
|------|-----|------|----------------|
| bluefin | 192.168.132.222 | Database | **CRITICAL** - All services fail |
| redfin | 192.168.132.223 | GPU/LLM | Council votes fail, no inference |
| greenfin | 192.168.132.224 | Monitoring | Alerting degraded |
| sasass | 192.168.132.241 | Edge | Dev affected only |
| sasass2 | 192.168.132.242 | Edge | Dev affected only |

## Diagnosis
```bash
# From TPM workstation
ping -c 3 192.168.132.XXX

# Check from another node
ssh dereadi@192.168.132.222 "ping -c 3 192.168.132.XXX"

# Traceroute
traceroute 192.168.132.XXX

# Check ARP cache
arp -a | grep 192.168.132.XXX
```

## Resolution Steps

### Step 1: Verify Network Path
```bash
traceroute 192.168.132.XXX
arp -a | grep 192.168.132.XXX
```

### Step 2: Physical Access (if available)
- Check power LED
- Check network cable connection
- Check for kernel panic on screen
- Power cycle if frozen

### Step 3: Remote Management (if configured)
- Use IPMI/iLO/iDRAC for server nodes
- Use network power switch if available

### Step 4: Failover Procedures

**If bluefin (database) down:**
- ESCALATE IMMEDIATELY - all services depend on DB
- Check for hardware failure
- Consider failover to backup if exists

**If redfin (GPU) down:**
- LLM inference unavailable
- Council votes will fail
- Gateway returns degraded health
- Services continue without AI features

**If greenfin (monitoring) down:**
- Alerting degraded but services continue
- Check Grafana manually
- Longhouse monitor offline

**If sasass/sasass2 (edge) down:**
- Development affected only
- Production continues normally

## Prevention
- Configure watchdog timers on all nodes
- Set up out-of-band management (IPMI)
- Monitor with heartbeat checks every 60s
- Cross-node health checks in Grafana

## Post-Incident
- Review /var/log/kern.log for crash cause
- Check dmesg output after recovery
- Update thermal memory with incident
- Consider adding redundancy if repeated

---
Cherokee AI Federation | FOR SEVEN GENERATIONS
