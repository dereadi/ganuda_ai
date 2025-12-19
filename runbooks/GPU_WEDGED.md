# RUNBOOK: GPU Wedged (vLLM Unresponsive)

## Symptoms
- vLLM requests timing out (>30s response times)
- nvidia-smi shows 100% utilization but no throughput
- GPU memory stuck at max, not releasing
- Health check: `curl http://localhost:8080/health` returns vllm: unhealthy

## Severity
**P1** - Affects all LLM inference

## Diagnosis
```bash
# Check vLLM process state
ps aux | grep vllm
journalctl -u vllm -n 50 --no-pager

# Check GPU state
nvidia-smi
nvidia-smi -q | grep -A5 "Utilization"

# Check for zombie processes
ps aux | grep defunct | grep -v grep

# Check system resources
free -h
df -h /
```

## Resolution Steps

### Step 1: Graceful Restart (try first)
```bash
sudo systemctl restart vllm
sleep 30
curl -s http://localhost:8080/health | jq .
```

### Step 2: Force GPU Reset (if Step 1 fails)
```bash
sudo systemctl stop vllm
sleep 10
sudo nvidia-smi -r  # GPU reset
sleep 5
sudo systemctl start vllm
sleep 60  # Model reload takes ~45s
curl -s http://localhost:8080/health | jq .
```

### Step 3: Nuclear Option (schedule maintenance)
```bash
# Only if Steps 1-2 fail
echo "Scheduling reboot in 5 minutes"
sudo shutdown -r +5 "GPU recovery - planned reboot"
# OR immediate if critical
sudo reboot
```

## Prevention
- Monitor GPU memory utilization (alert at 90%)
- Implement request timeouts in gateway (120s max)
- Add circuit breaker for 3+ consecutive failures
- Check for memory leaks in custom prompts

## Post-Incident
- Check /ganuda/logs/vllm.error.log for root cause
- Update this runbook if new failure mode discovered
- Create thermal memory entry for incident

---
Cherokee AI Federation | FOR SEVEN GENERATIONS
