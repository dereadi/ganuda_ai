# KB: Qwen3.6-35B-A3B Split-Brain Deployment on Redfin

**Date**: April 16, 2026
**Node**: redfin (192.168.132.223)
**GPU**: NVIDIA RTX PRO 6000 Blackwell Max-Q, 96GB GDDR7 (single card)
**Council Vote**: `#6f390eda` — 12-1 APPROVED (Coyote REJECT, standing dissent on new architecture risk)

## Summary

Deploying Qwen3.6-35B-A3B as a split-brain architecture on redfin, replacing Qwen2.5-72B-Instruct-AWQ as primary inference. Two instances of the same model serve different roles — perceiver and reasoner — on a single 96GB GPU.

## Why Qwen3.6-35B-A3B

- **Architecture**: Sparse MoE, 35B total / 3B active parameters. 256 experts, 8 routed + 1 shared. 40 layers with Gated DeltaNet (3/4 layers linear attention) + Gated Attention (1/4 layers full attention).
- **Context**: 262K native, extensible to 1M via YaRN.
- **Multimodal**: Native vision + video support. No separate VLM pipeline needed.
- **License**: Apache 2.0.
- **Key benchmarks**: SWE-bench Verified 73.4, Terminal-Bench 2.0 51.5, AIME26 92.7, GPQA Diamond 86.0, RefCOCO 92.0 (spatial intelligence).

### Relevance to Federation

1. **ARC-AGI-3 visual agent**: Spatial intelligence (RefCOCO 92.0) + native vision = perceiver model for the visual agent pipeline.
2. **Code comprehension**: Replaces 72B for `_try_code_plan` tier in ganuda_agent.py. Same quality at 1/10th active compute.
3. **MoE routing fix**: DeltaNet architecture mitigates the MoE routing distraction (Yonsei/Alibaba deer signal) — visual tokens reach reasoning layers by construction.

## Split-Brain Architecture (Revised — Chiral Pair)

Initial plan was two Qwen3.6-35B-A3B instances. Failed: full 35B weights in BF16 = ~70GB (all 256 experts must be resident). Two copies exceed 96GB.

**Revised architecture: heterogeneous chiral pair.**

| Instance | Model | Role | Port | VRAM |
|----------|-------|------|------|------|
| Brain-A | **Qwen3.6-35B-A3B** | Perceiver — vision, spatial, game state | 8000 | ~70GB |
| Brain-B | **Gemma 4 26B-A4B** | Reasoner — math, strategy, code planning | 8010 | ~15GB (FP8) |
| *Reserve* | KV cache | — | — | ~11GB |

### Why Heterogeneous

- **Chiral validation by construction.** Different companies (Alibaba vs Google), different architectures (DeltaNet MoE vs Gemma MoE), different training data. When one hallucinates, the other likely won't.
- **Complementary benchmarks.** Qwen3.6: RefCOCO 92.0 (spatial), SWE-bench 73.4 (coding). Gemma 4: AIME 88.3 (math), GPQA 82.3 (science).
- **VRAM budget works.** 70GB + 15GB + 11GB headroom = 96GB.
- **Both MoE, both Apache 2.0.** Same deployment pattern, same license.

## Previous Deployment (Rollback Target)

| Service | Model | Port | GPU Mem |
|---------|-------|------|---------|
| vllm.service | Qwen2.5-72B-Instruct-AWQ | 8000 | 62GB |
| vllm-elisi.service | Qwen2.5-3B-Instruct | 9100 | 9GB |
| vllm-redfin-vlm.service | Qwen2-VL-7B-AWQ | 9101 | 8GB |

**Rollback**: Weights remain on disk at `/ganuda/models/qwen2.5-72b-instruct-awq`. Swap back by restarting original systemd services.

## Upgrade Path

### Prerequisites
- vLLM >= 0.19.0 (was 0.15.1+cu128, source-built for sm_120)
- Model weights downloaded to HF cache (~70GB BF16)

### Steps

1. Download model: `hf download Qwen/Qwen3.6-35B-A3B`
2. Upgrade vLLM: `pip install vllm==0.19.0` in cherokee_venv
   - **Risk**: Pre-built wheel may lack sm_120 kernels. If inference is slow, rebuild from source with `TORCH_CUDA_ARCH_LIST="12.0"` (see KB-VLLM-NATIVE-SM120-BUILD-SUCCESS-FEB09-2026.md)
3. Stop current services: `systemctl stop vllm vllm-elisi vllm-redfin-vlm`
4. Start Brain-A (perceiver):
   ```bash
   /home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
     --model Qwen/Qwen3.6-35B-A3B \
     --port 8000 \
     --dtype bfloat16 \
     --gpu-memory-utilization 0.42 \
     --max-model-len 131072 \
     --max-num-seqs 64 \
     --reasoning-parser qwen3 \
     --trust-remote-code
   ```
5. Start Brain-B (reasoner):
   ```bash
   /home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
     --model Qwen/Qwen3.6-35B-A3B \
     --port 8010 \
     --dtype bfloat16 \
     --gpu-memory-utilization 0.42 \
     --max-model-len 131072 \
     --max-num-seqs 64 \
     --reasoning-parser qwen3 \
     --enable-auto-tool-choice --tool-call-parser qwen3_coder \
     --trust-remote-code
   ```
6. Update LLM Gateway routing to split perceiver/reasoner traffic
7. Validate: benchmark both instances, compare to 72B baseline

### Sampling Parameters (from Qwen team)

**Thinking mode (general)**: temp=1.0, top_p=0.95, top_k=20, presence_penalty=1.5
**Thinking mode (coding)**: temp=0.6, top_p=0.95, top_k=20, presence_penalty=0.0
**Instruct mode (general)**: temp=0.7, top_p=0.8, top_k=20, presence_penalty=1.5

## Coyote's Dissent (Recorded)

Coyote (lone REJECT) raised valid concerns about replacing a proven 72B deployment with an untested architecture. Mitigations:
- Weights on disk for instant rollback
- Benchmark before cutting over production traffic
- Elisi observer can monitor for quality regression
- 72B AWQ path stays available as fallback in consultation-ring

## Deer Signal Context

- **Be My Eyes** (Nov 2025): Qwen2.5-VL-7B perceiver + DeepSeek-R1 reasoner = same split-brain pattern. We're running both roles on a BETTER model.
- **MoE Routing Distraction** (Yonsei/Alibaba Apr 2026): DeltaNet architecture structurally prevents the routing failure mode.
- **Graph RAG** (NYU Shanghai): Explicit graph structure outperforms dense RAG by 33pp on multi-hop reasoning — validates thermal memory architecture that feeds both brains.
