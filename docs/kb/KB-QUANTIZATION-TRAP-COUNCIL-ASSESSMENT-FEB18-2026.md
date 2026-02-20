# KB: Quantization Trap — Council Assessment and Mitigation Plan
**Date**: February 18, 2026
**Council Vote**: #d07a22171ed7dd61 (PROCEED WITH CAUTION, 0.844)
**Kanban**: #1817 (Benchmark), #1818 (FP8 Evaluation)
**Sprint**: RC-2026-02G

## Summary

Research papers demonstrate that 4-bit quantization causes 11-32% accuracy degradation on multi-hop reasoning and Chain-of-Thought tasks. Errors compound hop-by-hop. The federation runs Qwen2.5-72B-Instruct-AWQ (INT4) on RTX PRO 6000 (96GB VRAM, Blackwell). All 7 council specialists reason through this quantized model.

Council vote was **unanimous**: yes, we are likely in the quantization trap.

## Research Sources

1. **"Quantization Meets Reasoning"** (arxiv 2501.03035) — AWQ and GPTQ introduce up to 32.39% accuracy degradation (avg 11.31%) on reasoning tasks, specifically numerical computation and reasoning planning.
2. **"Quantization Hurts Reasoning?"** (arxiv 2504.04823) — Reasoning models with long CoT are more prone to quantization error accumulation over the sequence.
3. **"The Quantization Trap: Breaking Linear Scaling Laws in Multi-Hop Reasoning"** (Henry Han et al., Baylor/Xidian) — 4-bit models suffer 30% "Deductive Trust" collapse and paradoxically consume more energy/latency than 16-bit due to casting overheads. RTX PRO 6000 called a "half-mitigation" (fixes efficiency, not reasoning fidelity).

## Current Configuration

- **Model**: Qwen2.5-72B-Instruct-AWQ (INT4, AWQ-Marlin quantization)
- **Hardware**: NVIDIA RTX PRO 6000 (96GB VRAM, Blackwell SM120)
- **Throughput**: 32 tok/s with torch.compile
- **Usage**: All council specialist reasoning, Jr instruction generation, gateway routing

## Council Findings (All 7 Specialists)

### Q1: Are we in the trap?
**Unanimous YES.** All specialists agreed 4-bit council reasoning is materially compromised for complex multi-hop deliberations.

### Q2: Does democratic voting save us?
**Partially.** Eagle Eye's key insight: "If all specialists are using the same quantized model, they may exhibit similar biases and errors, reducing the effectiveness of the voting mechanism." Quantization errors are **systematic, not random** — consensus cannot correct for shared blind spots.

### Q3: Should we investigate FP8?
**Unanimous YES.** Qwen2.5-72B at FP8 = ~72GB weights. Fits in 96GB VRAM with room for KV cache. vLLM supports `--quantization fp8`.

### Q4: Should we benchmark?
**Unanimous YES.** Measure actual degradation against full-precision reference, don't rely on published ranges.

### Q5: Best tradeoff?
**72B@4bit + voting is acceptable for now, but FP8 is the clear next step.**

### Turtle's 7GEN Concern
"This impacts the long-term reliability and trustworthiness of our council's decisions." 8,600+ votes in the archive, some potentially affected by quantization-induced reasoning errors.

## Mitigation Plan

### Phase 1: Benchmark (Kanban #1817, 5 SP)
- Run council on multi-hop reasoning benchmarks (MMLU-Pro, GSM8K-hard, ARC-Challenge)
- Compare AWQ-4bit results against API call to same model at full precision (or published benchmarks)
- Measure actual degradation percentage for our specific model and tasks
- Determine if degradation is within acceptable bounds or actionable

### Phase 2: FP8 Evaluation (Kanban #1818, 8 SP)
- Test vLLM with `--quantization fp8` on Qwen2.5-72B
- Verify VRAM fits (72GB weights + KV cache + overhead < 96GB)
- Benchmark throughput (tok/s) vs current AWQ-Marlin configuration
- Compare reasoning quality on same benchmark suite from Phase 1
- If FP8 shows meaningful improvement with acceptable throughput, plan migration

### Existing Mitigations (Already in Place)
1. **7-specialist democratic voting** — reduces impact of individual reasoning errors
2. **Coyote metacognitive layer** — flags when consensus is suspiciously uniform
3. **CRAG (Corrective RAG)** — verifies retrieved information against ground truth
4. **Reliability inversion** — penalizes over-recalled memories (reduces compounding)
5. **TPM oversight** — Chief reviews council votes and applies judgment

## VRAM Budget Analysis

| Precision | Weight Size | KV Cache (8K ctx) | Total Est. | Fits 96GB? |
|-----------|------------|-------------------|-----------|------------|
| FP16      | ~144 GB    | ~8 GB             | ~152 GB   | NO         |
| FP8       | ~72 GB     | ~8 GB             | ~80 GB    | YES (16GB headroom) |
| INT4 (current) | ~36 GB | ~8 GB           | ~44 GB    | YES (52GB headroom) |

## Chief's Principle (Feb 18 2026)

> "I constantly question how much I know. I am willing to go back and fact check multiple times, even when I think I know the answer. I have a few disabilities that make this challenging, but I have learned to build around the disabilities, AND/OR use them to see other data more clearly that others struggle to."

The CRAG system, reliability inversion, and immune system are direct implementations of this cognitive pattern. The Council should operate the same way: assume you might be wrong, verify against ground truth, use the weird angles.

## Lessons Learned

- **Don't trust quantization is "free."** We accepted AWQ-4bit as a necessary tradeoff for fitting 72B in VRAM. The research says the cost is higher than we assumed.
- **Democratic voting is NOT a complete fix** for systematic model degradation. If all voters share the same blind spot, consensus amplifies the error.
- **Benchmark before migrating.** Get actual numbers for our workload before changing the production model.
- **FP8 is the likely sweet spot** for our hardware — 2x the precision of INT4, still fits in VRAM.

For Seven Generations.
