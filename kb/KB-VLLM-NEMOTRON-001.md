# KB-VLLM-NEMOTRON-001: vLLM and Nemotron Deployment

**Created**: 2025-12-12
**Category**: Infrastructure
**Status**: Active

---

## Summary

vLLM deployment on redfin (96GB Blackwell GPU) with Nemotron models for Jr resonance.

## Current Configuration

**Node**: redfin (192.168.132.223)
**GPU**: RTX 6000 96GB Blackwell
**vLLM Version**: 0.11.2
**Active Model**: nvidia/NVIDIA-Nemotron-Nano-9B-v2

## Model Benchmarks

| Model | Size | Context | Tok/s | Use Case |
|-------|------|---------|-------|----------|
| Qwen2.5-7B-Instruct | 7B | 8K | 33.7 | Baseline |
| Nemotron-Mini-4B | 4B | 4K | 116.8 | Fast Jr tasks |
| Nemotron-Nano-9B-v2 | 9B | 131K | 27.3 | Deep analysis |

**Key insight**: "Faster AI = Smarter AI" - Nemotron Mini 4B can do 3.5x more thinking cycles in same time.

---

## vLLM Commands

### Start Nemotron Nano 9B (Current - Deep Analysis)
```bash
nohup /home/dereadi/cherokee_venv/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model nvidia/NVIDIA-Nemotron-Nano-9B-v2 \
    --port 8000 \
    --gpu-memory-utilization 0.70 \
    > /ganuda/logs/vllm.log 2>&1 &
```

### Start Nemotron Mini 4B (Fast Tasks)
```bash
nohup /home/dereadi/cherokee_venv/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model nvidia/Nemotron-Mini-4B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.70 \
    --max-model-len 4096 \
    > /ganuda/logs/vllm.log 2>&1 &
```

### Check Status
```bash
curl http://localhost:8000/v1/models
nvidia-smi
```

---

## API Usage

**Endpoint**: `http://192.168.132.223:8000/v1/chat/completions`

**Example**:
```python
import requests

response = requests.post(
    "http://192.168.132.223:8000/v1/chat/completions",
    json={
        "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
        "messages": [
            {"role": "system", "content": "You are a helpful Jr agent."},
            {"role": "user", "content": "Analyze the system health."}
        ],
        "max_tokens": 1000
    }
)
```

---

## Jr Resonance Client

Location: `/ganuda/lib/jr_resonance_client.py`

**Features**:
- Auto-detects current model
- `resonate()` for standard queries
- `deep_think()` for extended reasoning

**Config**: `/ganuda/config/resonance.json`

---

## Troubleshooting

### vLLM Won't Start
1. Check GPU memory: `nvidia-smi`
2. Kill stuck processes: `pkill -9 -f vllm`
3. Lower memory utilization to 0.70

### Model Too Large
- Nemotron Mini 4B: max_model_len must be 4096 (not 8192)
- Nano 9B supports full 131K context

### SSH Timeout to redfin
- vLLM process in D state can block SSH
- Use console access or wait for timeout

---

## Related Documents

- `/ganuda/missions/NEMOTRON-BENCHMARK-RESULTS-2025-12-12.md`
- `/ganuda/missions/INFRA-PHASE-3A-VLLM-STARTUP-MANUAL.md`
- `/ganuda/config/resonance.json`

---

**For Seven Generations**: Faster thinking serves the tribe better.
