# RUNBOOK: GPU Wedged / vLLM Unresponsive

## Symptoms
- vLLM requests timing out
- nvidia-smi shows 100% utilization with no throughput
- GPU memory not releasing after requests complete
- Gateway /health shows vllm: "unhealthy"

## Diagnosis

1. Check vLLM service status:
   ```bash
   systemctl status vllm.service
   journalctl -u vllm -n 50 --no-pager
   ```

2. Check GPU state:
   ```bash
   nvidia-smi
   nvidia-smi -q | head -50
   ```

3. Check for zombie processes:
   ```bash
   ps aux | grep -E "vllm|python.*vllm"
   ```

4. Check API responsiveness:
   ```bash
   curl -s http://localhost:8000/health
   time curl -s -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"nvidia/NVIDIA-Nemotron-Nano-9B-v2","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
   ```

## Resolution

### Level 1: Graceful Restart
```bash
sudo systemctl restart vllm
# Wait 30s for model to load
sleep 30
curl http://localhost:8000/health
```

### Level 2: Forced Restart with GPU Reset
```bash
sudo systemctl stop vllm
sleep 10
sudo nvidia-smi -r  # Reset GPU
sleep 5
sudo systemctl start vllm
```

### Level 3: Nuclear Option (Maintenance Window)
```bash
# Schedule downtime first!
sudo systemctl stop vllm llm-gateway
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia
sleep 5
sudo modprobe nvidia
sudo systemctl start vllm llm-gateway
```

## Prevention
- Monitor GPU memory: alert at 90% utilization
- Set request timeouts in gateway (30s default)
- Implement circuit breaker for repeated failures
- Schedule weekly vLLM restarts during low-traffic window

## Escalation
If Level 2 doesn't resolve:
1. Page on-call engineer
2. Check thermal throttling: `nvidia-smi -q -d TEMPERATURE`
3. Review recent code changes to vLLM config
