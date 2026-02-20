# KB: Ouro Looped Language Models — Federation Impact Assessment

**Date**: February 11, 2026
**Source**: "Scaling Latent Reasoning via Looped Language Models" — arXiv:2510.25741
**Authors**: Jason Eshraghian, Rui-Jie Zhu et al. (NeuroDump / Ouro)
**Homepage**: https://ouro-llm.github.io/
**Related Thermals**: #82859 (Nate Hagens Compute Crisis), #84025 (Ouro Discovery), LoRA Council Deliberation (#82860)
**Kanban**: #1764
**Council Vote**: PROCEED WITH CAUTION (confidence 0.889, audit hash 65ecf909845960cb)
**GitHub**: https://github.com/OuroHub (no public repos yet — code "Coming Soon")
**HuggingFace**: ByteDance/Ouro-{1.4B,2.6B,1.4B-Thinking,2.6B-Thinking} (Apache 2.0)
**Jr Instructions**: JR-OURO-BENCHMARK-COUNCIL-PROMPTS-FEB11-2026

### Model Availability (Verified Feb 11)

| Model | HF Path | License | Quantized |
|-------|---------|---------|-----------|
| Ouro-1.4B | ByteDance/Ouro-1.4B | Apache 2.0 | No |
| Ouro-2.6B | ByteDance/Ouro-2.6B | Apache 2.0 | 1 variant |
| Ouro-1.4B-Thinking | ByteDance/Ouro-1.4B-Thinking | Apache 2.0 | No |
| Ouro-2.6B-Thinking | ByteDance/Ouro-2.6B-Thinking | Apache 2.0 | No |

### Critical Deployment Caveats

1. **vLLM: Adaptive exit NOT supported** — always runs full `total_ut_steps`. Lose dynamic compute allocation.
2. **transformers pinned**: Requires `< 4.56.0` (recommend 4.54.1)
3. **Custom code**: Requires `trust_remote_code=True`
4. **No quantized weights published** (must self-quantize for memory-constrained nodes)
5. **Architecture**: 24 layers, 2048 hidden, SwiGLU, RoPE, 49K vocab, 4K context (→64K)
6. **Training**: 7.7T tokens (6T pre-train → 2.6T anneal → 20B long context → 300B mid-train)

---

## Executive Summary

Ouro introduces a **third axis of scaling** for language models: looping. Instead of scaling parameters (model size) or data (training tokens), the same transformer weights are iterated multiple times per token via an exit-gated loop. A 2.6B looped model matches or exceeds 7-8B standard models on reasoning benchmarks. This directly addresses the compute/data wall identified in thermal #82859.

---

## Core Architecture

### Standard Transformer
Input → Forward Pass → Output Token

### Looped Transformer (Ouro)
Input → Forward Pass → Exit Gate → {EXIT if confident, LOOP if not} → Output Token

- **Exit Gate**: Dense layer + sigmoid, producing instantaneous exit probability
- **Survival Probability**: Unconditional exit probability = P(survived all prior loops) × P(exit this loop)
- **CDF Thresholding**: Cumulative density exceeds threshold → exit; max loops reached → forced exit
- **Latent Space Reasoning**: Loops operate on latent vectors, NOT vocabulary tokens — no chain-of-thought token generation needed

### Key Insight: Where Looping Helps

| Task Type | Looping Benefit | Why |
|-----------|----------------|-----|
| Knowledge Storage/Retrieval | **None** | Storage requires parameters, not compute cycles |
| Knowledge Manipulation/Reasoning | **Massive** | Extra loops = extra internal computation for reasoning |

This was validated using synthetic benchmarks from "Physics of Language Models" (Zhu & Allen-Zhu):
- Biographical fact recall: 1 loop ≈ 4 loops (no improvement)
- Multi-step reasoning over stored facts: 1 loop = 14% accuracy, 4 loops = dramatically higher

---

## Technical Details

### Reward Hacking Problem (Solved)
Initial training collapsed — one exit gate dominated all others via self-reinforcing cycle. Model learned to always exit at the same loop regardless of input complexity.

**Solution**: Entropy regularization via KL divergence against uniform prior distribution. Penalizes deviation from uniform exit distribution. Geometric prior (PonderNet, DeepMind) caused undertraining of later loops; uniform prior outperformed.

### KV Cache Strategy
- **Training/Prefill**: Parallel processing; each loop's KV cache only available to same-loop tokens (necessary for parallelism)
- **Inference/Decoding**: Sequential; next token gets KV cache from corresponding loop of previous token
- **Tested alternatives**: Exit-loop-only cache, averaged cache, first-loop cache. First-loop cache degraded; others performed similarly.

### Training Pipeline
- Phase 1: 1.4B model trained on 3T tokens
- Fork: 2.6B created by duplicating non-embedding layers (resembles 2x loop pass)
- Total: 7.7 trillion training tokens across phases
- Quality of training data increased across phases

### Results
- **Ouro 2.6B vs Gemma 3 (12B)**: Ouro outperforms despite being ~5x smaller
- **Ouro 2.6B vs QwQ 3 (8B)**: Competitive despite being 3x smaller (QwQ also trained on 3x more tokens)
- **Loop Extrapolation**: Some benchmarks improve going 4→8 loops; others degrade. Overlooping generally safer than underlooping.

---

## Federation Impact Assessment

### Redfin — RTX PRO 6000 Blackwell 96GB (192.168.132.223)

**Current**: Qwen2.5-72B-Instruct-AWQ consuming 86GB VRAM. Single-model serving.

**Ouro Opportunity**:
- A looped 14B-32B model matching 72B reasoning quality would use ~15-35GB VRAM
- Frees 50-60GB for co-hosting: vision models, embedding service, parallel council inference
- Alternatively: looped 72B could outperform current non-looped 72B on reasoning tasks
- Blackwell's compute density (high FLOPS/watt) is ideal for iterative workloads — loops are pure compute, not memory
- **Latency tradeoff**: Each loop adds inference time. 4 loops ≈ 4x single-token compute. But total sequence length decreases (no chain-of-thought tokens), so end-to-end may be neutral or better.

### Bluefin — RTX 5070 12GB (192.168.132.222)

**Current**: Qwen2-VL-7B-Instruct-AWQ for vision (7.4GB used)

**Ouro Opportunity**:
- This is the memory-constrained edge case where looped models shine most
- A looped 1.4B reasoning model could fit alongside the VLM in remaining 5GB
- Could serve as a local reasoning co-processor for vision pipeline decisions
- Currently no text reasoning model on bluefin — this would add capability without hardware cost

### bmasass — M4 Max 128GB Unified Memory (192.168.132.21)

**Current**: MLX DeepSeek-R1-Distill-Qwen-32B-4bit (~20GB) for air-gapped/field use

**Ouro Opportunity**:
- MLX already supports custom architectures — looped models would need MLX port
- A looped 2.6B on Apple Silicon could match the 32B reasoning model at 1/10th the memory
- Frees 18GB+ for additional field models or larger context windows
- Apple Neural Engine could potentially accelerate the loop computation
- Critical for Constitutional DyTopo (#82856) — smaller model = faster field decisions

### Council Architecture Impact

The 7-Specialist Council currently routes ALL specialists through the 72B on redfin. If looped models deliver equivalent reasoning at smaller sizes:
- Specialists could run on dedicated smaller looped models
- True parallel council voting (currently sequential through one model)
- Per-specialist fine-tuned looped models (cultural tuning with fewer parameters to adjust)

---

## Connection to Existing Work

### Compute Crisis (Thermal #82859)
Ouro directly addresses the Nate Hagens finding: inference compute is structurally constrained. Looping decouples compute scaling from parameter scaling. You don't need bigger GPUs — you need the same GPU doing more iterations.

### LoRA Deliberation (KB-LORA-COUNCIL-DELIBERATION-FEB10-2026)
Text LoRA was deprioritized because 72B was "sufficient." Looped models reframe this: instead of fine-tuning a big model (LoRA on 72B), you could train a small looped model that achieves the same reasoning depth with 1/3 the parameters. LoRA on a 14B looped model = tiny adapter, fast training, field-deployable.

### Thermal Memory RAG Optimization (#1760)
Looped models excel at knowledge manipulation, not storage. RAG (retrieval) + looped reasoning (manipulation) is a natural pairing. Retrieve with embeddings, reason with loops.

---

## Recommended Actions

1. **Immediate (Research)**: Jr research task to evaluate Ouro model availability, MLX compatibility, vLLM looped model support
2. **Short-term (Benchmark)**: Download Ouro 2.6B, benchmark against Qwen2.5-7B on our council voting prompts using redfin
3. **Medium-term (Integration)**: If benchmarks hold, deploy looped model on bluefin as reasoning co-processor
4. **Long-term (Architecture)**: Evaluate looped pre-training for Cherokee-specific models — cultural reasoning via loops, not vocabulary

---

## Papers Cited in Source Material

- Scaling Laws for Neural Language Models (Kaplan et al.) — arXiv:2001.08361
- Will we run out of data? (Villalobos et al.) — arXiv:2211.04325
- Does RL Really Incentivize Reasoning Beyond Base Model? — arXiv:2504.13837
- Universal Transformers — arXiv:1807.03819
- PonderNet: Learning to Ponder — arXiv:2107.05407
- Physics of Language Models (Allen-Zhu & Li) — https://physics.allen-zhu.com/

---

*For Seven Generations — compute efficiency is a sovereignty issue.*
