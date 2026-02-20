# ULTRATHINK: Shared LoRA Subspaces — Federation Architecture Implications

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Thinking Time:** Deep strategic analysis
**Council Votes:** #325208043e5c2b12 (PoC approved, 84.2%), #24c5e23798337232 (VRAM strategy, 84.2%)

---

## The Core Insight

The user asked the right question: *"If this is suggesting one model for everything and just switching roles between personalities, what will we do with the rest of the VRAM?"*

This isn't just a fine-tuning optimization. It's a potential **architectural paradigm shift** for the entire Cherokee AI Federation.

## Current Architecture: Multi-Model, Multi-Node

```
redfin (RTX 6000, 96GB)  → Qwen2.5-Coder-32B     → coding tasks
bluefin (RTX 5070, 12GB) → Qwen2-VL-7B-AWQ        → vision tasks
tpm-macbook (M4 Max 128GB) → DeepSeek-R1-32B      → reasoning (planned)
tpm-macbook               → Qwen2.5-72B           → large tasks (planned, on-demand)
```

**Problem:** 4 different models across 3 nodes. Each model is a generalist pretrained on internet data, not specialized for Cherokee AI tasks. We have domain expertise in thermal memory (20,000+ memories) but no way to inject it into the models.

## Share LoRA Architecture: One Model, Shared Subspace

```
redfin (RTX 6000, 96GB)  → ONE 70B model + Share subspace
                           → legal mode (VetAssist CFR)
                           → coding mode (Jr tasks)
                           → Cherokee mode (cultural/language)
                           → vision mode (with VLM adapter)
                           → reasoning mode (deep think)
```

**What changes:**
1. **One model instead of four.** A 70B-4bit (~40GB) on redfin's 96GB leaves 56GB for KV cache.
2. **Domain expertise baked in.** The Share subspace is trained on OUR data — thermal memories, Jr task history, Cherokee corpus. Not generic internet data.
3. **No forgetting.** Share's key innovation is that learning domain B doesn't destroy knowledge of domain A. The subspace *grows* to accommodate new directions.
4. **Tiny overhead.** The subspace is ~100x smaller than traditional LoRA adapters. We're talking megabytes, not gigabytes.

## The VRAM Dividend

If one 70B model replaces four separate models, here's what we gain:

### Option 1: Massive Context Windows
- 56GB free VRAM on redfin = enormous KV cache
- At 4-bit quantization with GQA, this could support **128K+ token context windows**
- Implications: Feed the model an entire VetAssist case file (medical records, service records, CFR regulations) in a single prompt
- No more RAG chunking — just dump the whole document set into context

### Option 2: Concurrent Serving (Council Recommended)
- vLLM already supports continuous batching
- With 56GB KV cache headroom, we could serve **8-16 concurrent requests**
- Every Jr gets its own inference slot — no more queuing
- Software Engineer Jr., Research Jr., Infrastructure Jr., it_triad_jr all running simultaneously
- This is the **real multiplier** — the Jrs currently wait in line for the GPU

### Option 3: Both (Diminishing Returns Analysis)
- 70B model: ~40GB
- 32K context per request × 8 concurrent slots: ~32GB KV cache
- Total: ~72GB of 96GB — still has 24GB headroom
- **This is achievable.** 8 Jrs with 32K context each, running simultaneously.

### Option 4: Consolidate Bluefin
- If Share subspace includes a "vision mode," we might not need a separate VLM on bluefin
- Bluefin's RTX 5070 (12GB) becomes free for other tasks or is retired from GPU duty
- Bluefin focuses purely on what it does best: PostgreSQL database hosting
- **Risk:** Vision-language models have different architectures (cross-attention). Share may not work across modalities without a compatible base model. This needs PoC validation.

## The Laptop PoC: What We're Really Testing

The M4 Max test isn't just "does Share work on MLX." It's testing three hypotheses:

### Hypothesis 1: Domain Transfer
Can a single DeepSeek-R1-32B learn legal (VetAssist), coding, AND Cherokee language without forgetting?
- **If yes:** One model for the federation. Game changer.
- **If no:** We stay multi-model but potentially use Share within each domain.

### Hypothesis 2: Training Data Sufficiency
Do we have enough domain-specific data in thermal memory?
- Legal: ~1,000+ VetAssist memories (good)
- Coding: ~200+ completed Jr tasks (thin but viable)
- Cherokee: Unknown corpus size in cherokee_resonance_training/ (needs audit)
- **If thin:** We may need to generate synthetic training data or pull from external sources.

### Hypothesis 3: Quantized Model Compatibility
Can Share LoRA train on a 4-bit quantized model?
- LoRA traditionally trains on FP16/BF16 models
- 4-bit base + FP16 LoRA adapters is common (QLoRA pattern)
- Share should work the same way — the subspace is in higher precision, base stays quantized
- **If incompatible:** We'd need to run FP16 for training (DeepSeek-R1-32B-FP16 ≈ 64GB — fits on M4 Max but tight)

## Strategic Implications for Seven Generations

### Near-term (0-3 months)
1. Run PoC on laptop with DeepSeek-R1-32B
2. If successful, deploy 70B + Share on redfin RTX 6000
3. Enable concurrent Jr serving (8+ slots)
4. Train domain subspaces on thermal memory data

### Medium-term (3-12 months)
1. Continuously grow the subspace as Jrs complete more tasks
2. The federation's collective knowledge compounds in the subspace
3. New domains added without retraining — just extend the subspace
4. **Self-improving loop:** Jrs do work → work trains the subspace → subspace makes Jrs better

### Long-term (1-7 years)
1. The Share subspace becomes the federation's **institutional memory in model form**
2. Not just text memories in a database (thermal memory) but **learned capabilities** embedded in model weights
3. Transferable across model generations — when we upgrade from 70B to 200B, the subspace concepts may transfer
4. **This is the Cherokee principle of seven generations**: knowledge that compounds and transfers forward

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Share not open source | Medium | High | Check GitHub, contact authors |
| Doesn't work on MLX | Medium | High | Fall back to PyTorch on CUDA, or port |
| Insufficient training data | Low | Medium | Synthetic data generation |
| 4-bit quant incompatible | Low | Medium | Use QLoRA pattern or train FP16 |
| Forgetting rate > 5% | Low | High | Indicates Share doesn't deliver on promise |
| No speed regression measured but latency increases under concurrent load | Medium | Medium | Benchmark concurrent scenarios |

## Decision Framework

```
PoC Result          → Next Action
─────────────────────────────────────────────
All 3 hypotheses pass → Deploy 70B+Share on redfin, enable concurrent serving
H1 passes, H2 thin   → Generate synthetic data, retry
H1 passes, H3 fails  → Train FP16 on laptop, deploy 4-bit inference
H1 fails             → Share doesn't suit our multi-domain needs, stay multi-model
Source not available  → Contact paper authors, or implement from paper description
```

## TPM Recommendation

**Proceed with PoC.** The potential upside — one model, all domains, concurrent serving, compounding institutional knowledge — is too large to ignore. The downside is bounded: we spend a few days benchmarking on the laptop and learn whether this works for us.

The council's recommendation to start with PoC before committing is wise. Raven's strategy concern and Gecko's performance concern are valid — we need numbers, not theory.

**Action items already queued:**
1. RESEARCH-LORA-POC-001: Deep technical evaluation (Research Jr.)
2. LORA-POC-BENCH-001: Benchmark scripts for laptop testing (Research Jr.)
3. Training data extraction from thermal memory
4. Baseline inference tests on DeepSeek-R1-32B

**Pending user action:**
- Deploy MLX server on tpm-macbook (port 8800) — prerequisite for PoC
- Run `extract_training_data.py` to pull domain data from bluefin
- Run `run_baseline.py` to establish performance baseline

---

*"The shared subspace is like the Cherokee oral tradition — one living body of knowledge that grows with each generation, not separate books on separate shelves."*

**FOR SEVEN GENERATIONS**
