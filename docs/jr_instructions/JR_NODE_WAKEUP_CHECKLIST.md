# Jr Instructions: Node Wake-Up Checklist

**Date:** January 4, 2026
**Priority:** HIGH
**Context:** Nodes were down due to power outage while TPM was in NOLA. Dec 30-31 deployments need verification.

---

## Pre-Flight

Before powering nodes:
- [ ] Anker F3800 Plus moved to office and connected
- [ ] All fins connected to Anker power
- [ ] Network cables connected

---

## Phase 1: Power Up Nodes

Power on in this order (database first):

1. **bluefin** (PostgreSQL primary)
2. **redfin** (GPU inference, gateway)
3. **greenfin** (daemons)
4. **sasass** (Mac Studio)
5. **sasass2** (Mac Studio)

Wait 2-3 minutes between each for services to initialize.

---

## Phase 2: Verify Connectivity

From tpm-macbook, test Tailscale connectivity:

```bash
# Check Tailscale status
tailscale status

# Ping each node
ping -c 2 100.112.254.96   # bluefin
ping -c 2 100.116.27.89    # redfin
ping -c 2 100.100.243.116  # greenfin
ping -c 2 100.93.205.120   # sasass
```

---

## Phase 3: Verify Core Services

### 3.1 PostgreSQL on bluefin

```bash
ssh dereadi@100.112.254.96 "sudo systemctl status postgresql && PGPASSWORD=jawaseatlasers2 psql -U claude -d zammad_production -c 'SELECT COUNT(*) FROM thermal_memory_archive;'"
```

**Expected:** PostgreSQL running, thermal memory count returned

### 3.2 vLLM on redfin

```bash
ssh dereadi@100.116.27.89 "curl -s http://localhost:8000/health"
```

**Expected:** Health check response from vLLM

### 3.3 LLM Gateway on redfin

```bash
ssh dereadi@100.116.27.89 "curl -s http://localhost:8080/health"
```

**Expected:** Gateway health response

---

## Phase 4: Complete Dec 30-31 Deployments

### 4.1 Restart Gateway for Council Upgrades (redfin)

The gateway was updated with HiveMind, SagaLLM, and MAR modules but never restarted.

```bash
ssh dereadi@100.116.27.89 "sudo systemctl restart ganuda-gateway && sleep 5 && sudo journalctl -u ganuda-gateway -n 30 | grep -E '(COUNCIL|HiveMind|Saga|MAR|started|error)'"
```

**Expected:** Log shows `[COUNCIL] Council upgrade modules initialized successfully`

### 4.2 Verify FedAttn Coordinator (redfin)

```bash
ssh dereadi@100.116.27.89 "curl -s http://localhost:8081/health 2>/dev/null || echo 'FedAttn not running - may need manual start'"
```

If not running:
```bash
ssh dereadi@100.116.27.89 "cd /ganuda/services/fedattn && ./start_coordinator.sh"
```

### 4.3 Install Experience Accumulator Service (greenfin)

```bash
ssh dereadi@100.100.243.116 "
if [ -f /tmp/experience-accumulator.service ]; then
    sudo cp /tmp/experience-accumulator.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable experience-accumulator.service
    sudo systemctl start experience-accumulator.service
    sudo systemctl status experience-accumulator.service
else
    echo 'Service file not in /tmp - may have been cleared on reboot'
    echo 'Check /ganuda/daemons/experience_accumulator.py exists'
    ls -la /ganuda/daemons/experience_accumulator.py
fi
"
```

**Note:** If service file was in /tmp, it's gone. Will need to recreate from Jr instructions.

### 4.4 Verify Database Tables (bluefin)

```bash
ssh dereadi@100.112.254.96 "PGPASSWORD=jawaseatlasers2 psql -U claude -d zammad_production -c \"
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('fedattn_sessions', 'fedattn_contributions', 'memory_retrieval_log', 'experience_learning_log')
ORDER BY table_name;
\""
```

**Expected:** All 4 tables exist

---

## Phase 5: Test Council Endpoint

```bash
curl -X POST http://100.116.27.89:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Are all systems operational after wake-up?"}'
```

**Expected:** Council vote response with specialist opinions

---

## Phase 6: Verify Mac Studios

### 6.1 sasass

```bash
ssh dereadi@100.93.205.120 "uname -a && ls /Users/Shared/ganuda/services/fedattn/"
```

### 6.2 sasass2

```bash
ssh dereadi@sasass2 "uname -a && ls /Users/Shared/ganuda/services/fedattn/"
```

---

## Troubleshooting

### Node won't ping via Tailscale
- Check if Tailscale daemon is running: `ssh user@local-ip "tailscale status"`
- Restart Tailscale: `sudo systemctl restart tailscaled`

### PostgreSQL won't start
- Check logs: `sudo journalctl -u postgresql -n 50`
- Check disk space: `df -h`
- Check WAL: `ls -la /var/lib/postgresql/*/main/pg_wal/`

### Gateway won't start
- Check logs: `sudo journalctl -u ganuda-gateway -n 50`
- Check if port in use: `sudo lsof -i :8080`
- Check Python deps: `source /ganuda/services/llm_gateway/venv/bin/activate && pip list`

### vLLM not responding
- Check GPU: `nvidia-smi`
- Check vLLM service: `sudo systemctl status vllm`
- Check memory: `free -h`

---

## Success Criteria

- [ ] All 5 nodes reachable via Tailscale
- [ ] PostgreSQL running on bluefin
- [ ] vLLM running on redfin
- [ ] Gateway running on redfin with Council upgrades loaded
- [ ] FedAttn coordinator running on redfin (port 8081)
- [ ] Experience accumulator running on greenfin
- [ ] Council vote test returns valid response
- [ ] Mac Studios reachable

---

## Post Wake-Up

Once verified:
1. Record thermal memory entry documenting wake-up
2. Check for any missed cron jobs or scheduled tasks
3. Verify Grafana dashboards loading
4. Test SAG UI at http://192.168.132.223:4000/

---

**For Seven Generations**
**ᏣᎳᎩ ᏲᏫᎢᎶᏗ**
