# JR Instruction: Deploy Research Worker Service

**JR ID:** JR-DEPLOY-RESEARCH-WORKER-JAN28-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr.
**Council Vote:** 166956a7959c2232
**Related:** JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026

---

## Objective

Deploy the research-worker systemd service on redfin and restart the LLM Gateway to enable async research endpoints.

---

## Prerequisites

Files already created:
- `/ganuda/lib/research_dispatcher.py`
- `/ganuda/services/research_worker.py`
- `/ganuda/scripts/systemd/research-worker.service`
- Database table `research_jobs` in zammad_production

---

## Deployment Steps

### Step 1: Deploy systemd service

```bash
sudo ln -sf /ganuda/scripts/systemd/research-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable research-worker
sudo systemctl start research-worker
```

### Step 2: Verify service running

```bash
systemctl status research-worker
journalctl -u research-worker -f
```

Expected output: "Research Worker starting... Poll interval: 10s"

### Step 3: Restart LLM Gateway

```bash
sudo systemctl restart llm-gateway
```

### Step 4: Verify new endpoints

```bash
curl http://localhost:8080/health
```

Should show `/v1/research/async` and `/v1/research/status` endpoints available.

---

## Validation Test

### Queue a test research job:

```bash
curl -X POST http://localhost:8080/v1/research/async \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"query": "VA tinnitus rating criteria", "max_steps": 5}'
```

Expected response:
```json
{"job_id": "research-abc123", "status": "queued", "estimated_time": "3-5 minutes"}
```

### Check job status:

```bash
curl http://localhost:8080/v1/research/status/research-abc123 \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
```

### Verify output file created:

```bash
ls -la /ganuda/research/completed/
```

---

## Rollback

If issues occur:

```bash
sudo systemctl stop research-worker
sudo systemctl disable research-worker
sudo rm /etc/systemd/system/research-worker.service
sudo systemctl daemon-reload
```

---

## CMDB Update Required

After successful deployment, update thermal_memory_archive:
- Service: research-worker
- Node: redfin
- Port: N/A (background worker)
- Dependencies: ii-researcher, PostgreSQL, vLLM

---

FOR SEVEN GENERATIONS
