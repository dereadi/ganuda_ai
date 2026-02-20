# KB: Bluefin Ollama Removal & vLLM Migration

**Date**: February 11, 2026
**Trigger**: Post-power-outage infrastructure cleanup — Ollama pegged CPU at 743%
**Council Vote**: PROCEED WITH CAUTION (confidence 0.844, audit hash 34345f25)
**Council Concern**: Turtle 7GEN (no blocking action)
**Related KB**: KB-II-RESEARCHER-GPU-RUNAWAY-ROOT-CAUSE-FEB11-2026

---

## Executive Summary

Ollama has been removed from bluefin (192.168.132.222). The only consumer was `cherokee-legal-llamas.service` which used mistral:7b-instruct and codellama:34b-instruct for legal ticket analysis. These have been migrated to the Qwen2.5-72B-Instruct-AWQ model on redfin via vLLM's OpenAI-compatible API.

---

## Why Ollama Was Removed

1. **CPU-only inference**: The RTX 5070 on bluefin only has 1.3GB free GPU VRAM (Qwen2-VL-7B vision model uses the rest). Ollama fell back to CPU, consuming 743% CPU and 6.2GB RAM for 2+ minutes per request.

2. **Inferior model**: mistral:7b-instruct (4-bit Q4_K_M) is massively outperformed by Qwen2.5-72B-Instruct-AWQ running GPU-accelerated on redfin.

3. **Database node stability**: Bluefin is the database node (PostgreSQL). CPU-intensive inference workloads risk starving DB queries and connected services.

4. **Optic nerve already migrated**: The primary Ollama use case (vision pipeline) was already migrated to vLLM (`vlm-bluefin.service`).

---

## What Changed

### Code Change

**File**: `/home/dereadi/cherokee-bluefin/tribal-llms/cherokee_legal_council_with_memory.py`
**Backup**: `cherokee_legal_council_with_memory.py.ollama_backup`

| Before | After |
|--------|-------|
| `http://localhost:11434/api/generate` | `http://192.168.132.223:8000/v1/chat/completions` |
| Ollama generate format (`prompt`, `options`) | OpenAI chat format (`messages`, `temperature`, `max_tokens`) |
| `result.get("response", "")` | `result["choices"][0]["message"]["content"]` |
| `mistral:7b-instruct` (2 llamas) | `/ganuda/models/qwen2.5-72b-instruct-awq` |
| `codellama:34b-instruct` (1 llama) | `/ganuda/models/qwen2.5-72b-instruct-awq` |

### Services Disabled

| Service | Reason |
|---------|--------|
| `ollama.service` | No consumers remaining |
| `executive-jr-autonomic.service` | Crash-looping every 60s — missing `quantum_crawdad_env` virtualenv. 4 trading bots (trend, volatility, breakout, mean_reversion) reference a deleted environment. |
| `cherokee-desktop-tunnel.service` | Failing every 5 seconds — wrong credential format (`.pem` instead of `.json`). Needs Cloudflare tunnel credential regeneration before re-enabling. |

---

## Ollama Models That Were Installed (Now Unused)

| Model | Size | Status |
|-------|------|--------|
| conscience_jr_resonance:latest | 4.9GB | Unused (Cherokee fine-tune, Oct 2025) |
| integration_jr_resonance:latest | 4.9GB | Unused |
| executive_jr_resonance:latest | 4.9GB | Unused |
| meta_jr_resonance:latest | 4.9GB | Unused |
| memory_jr_resonance:latest | 4.9GB | Unused |
| qwen2.5:14b | 9.0GB | Unused |
| llama3.1:8b | 4.9GB | Unused |
| llama3.1:70b | 42.5GB | Unused |
| codellama:34b-instruct | 19.1GB | Unused |
| mistral:7b-instruct | 4.1GB | Was last consumer |
| llama2:7b | 3.8GB | Unused |
| **Total disk** | **~104GB** | Reclaimable via `ollama rm` |

**To reclaim disk space** (optional, after confirming no issues):
```text
ollama rm conscience_jr_resonance integration_jr_resonance executive_jr_resonance meta_jr_resonance memory_jr_resonance qwen2.5:14b llama3.1:8b llama3.1:70b codellama:34b-instruct mistral:7b-instruct llama2:7b
```

---

## Performance Comparison

| Metric | Ollama (mistral:7b, CPU) | vLLM (72B, GPU) |
|--------|--------------------------|-----------------|
| Inference time | ~120s | ~2-5s |
| CPU impact | 743% (8 threads) | 0% on bluefin |
| Model quality | 7B Q4 | 72B AWQ |
| GPU memory | 0 (CPU fallback) | Runs on redfin's 96GB |
| Network | Local | 192.168.132.223:8000 |

---

## Rollback

If vLLM on redfin becomes unavailable:
1. `sudo systemctl start ollama` (on bluefin)
2. Restore backup: `cp cherokee_legal_council_with_memory.py.ollama_backup cherokee_legal_council_with_memory.py`
3. `sudo systemctl restart cherokee-legal-llamas`

---

## Additional Bluefin Cleanup Needed

1. **executive-jr-autonomic**: Either fix `quantum_crawdad_env` virtualenv or remove trading bot references from the daemon config. Currently disabled.

2. **cherokee-desktop-tunnel**: Regenerate Cloudflare tunnel credentials in `.json` format. Currently disabled.

3. **Ollama disk cleanup**: 104GB of model weights can be reclaimed after confirming stable operation.

4. **CMDB update**: Update hardware_inventory to reflect Ollama removal from bluefin service list.

---

*For Seven Generations — the hawk that carries too much cannot fly. Shed what no longer serves.*
