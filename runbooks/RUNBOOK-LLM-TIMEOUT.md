# RUNBOOK: vLLM Latency / Timeout Issues

## Symptoms
- API requests taking > 30s
- Gateway returning 504 timeout errors
- Slow Council votes

## Diagnosis

1. Check current latency:
   ```bash
   time curl -s -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"nvidia/NVIDIA-Nemotron-Nano-9B-v2","messages":[{"role":"user","content":"Say hello"}],"max_tokens":10}'
   ```

2. Check GPU utilization:
   ```bash
   nvidia-smi dmon -s puc  # Power, Utilization, Clocks
   ```

3. Check concurrent requests:
   ```bash
   ss -tnp | grep 8000 | wc -l  # Active connections to vLLM
   ```

4. Check vLLM queue:
   ```bash
   curl http://localhost:8000/metrics | grep requests
   ```

## Resolution

### Level 1: Reduce Concurrent Load
```bash
# Temporarily pause Jr workers
sudo systemctl stop jr-se jr-it-triad jr-research jr-infra
# Let queue drain
sleep 60
sudo systemctl start jr-se
```

### Level 2: Adjust vLLM Parameters
Edit vLLM service to reduce max concurrent:
```bash
# Add to ExecStart: --max-num-seqs 32 (from 64)
sudo systemctl daemon-reload
sudo systemctl restart vllm
```

### Level 3: Scale Horizontally
If single GPU can't handle load:
- Consider queuing requests with priority
- Implement request batching
- Add second GPU or node

## Prevention
- Monitor P95 latency: alert if > 20s
- Implement request timeout in clients (30s)
- Use Council confidence to short-circuit low-value queries
- Cache frequent queries in thermal memory

## Escalation
If sustained high latency during normal load:
1. Check for memory leaks in vLLM
2. Review model size vs GPU memory
3. Consider model quantization
