# Resource Request: GPU Memory for Embedding Service
## December 14, 2025

---

## Situation

The Embedding Service cannot run - **GPU memory exhausted**.

### Current GPU Allocation (RTX 6000 - 96GB):

| Process | PID | Memory | Purpose |
|---------|-----|--------|---------|
| vLLM | 2771208 | **70GB (70%)** | Nemotron 9B inference |
| IT Triad CLI | 2846883 | **25GB** | Triad monitoring |
| **Free** | - | **~2GB** | Not enough for embeddings |

### Required for Embedding Service:
- BGE-large model needs **~4GB** GPU memory
- Current free: **2GB** - insufficient

---

## Options for Tribe Decision

### Option A: Reduce vLLM Memory (Recommended)
- Change vLLM from 70% to **60%** utilization
- Frees ~10GB for embedding service
- Requires vLLM restart (brief inference outage)

```bash
# Edit /etc/systemd/system/vllm.service
# Change: --gpu-memory-utilization 0.70
# To:     --gpu-memory-utilization 0.60
sudo systemctl daemon-reload
sudo systemctl restart vllm.service
```

### Option B: Stop IT Triad CLI Temporarily
- Kill process 2846883 during backfill
- Restart after 5,360 embeddings complete (~15-20 min)
- No vLLM changes needed

```bash
kill 2846883
# Run backfill
# Restart IT Triad after
```

### Option C: Run Embedding on CPU
- Slower but no GPU conflict
- Already configured as fallback
- ~10x slower than GPU

---

## Recommendation

**Option A** - Reduce vLLM to 60%. 

The 9B model only needs ~12GB for weights. At 60% (58GB), we still have plenty of KV cache for inference while leaving room for embedding service.

---

## Awaiting Tribe Decision

*For Seven Generations*
