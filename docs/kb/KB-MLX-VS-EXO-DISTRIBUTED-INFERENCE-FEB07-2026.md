# KB: MLX vs Exo Distributed Inference Decision

**Created:** 2026-02-07
**Author:** TPM (Claude Opus 4.6)
**Category:** Architecture Decision / Infrastructure
**Council Vote:** #8475 (Approved Option b, 89% confidence, 6 concerns)

## Decision

**Use MLX on M4 Max 128GB (single node)** instead of Exo distributed inference across Mac cluster.

## Context

The Cherokee AI Federation has 3 Apple Silicon Macs with 256GB total unified memory:
- tpm-macbook: M4 Max, 128GB, TB5
- sasass: M1 Max, 64GB, TB4
- sasass2: M1 Max, 64GB, TB4

The goal was running 70B+ parameter models that don't fit on any single GPU node.

## Options Evaluated

| Option | Approach | Verdict |
|--------|----------|---------|
| (a) Exo over Ethernet | Pool 256GB via mDNS, Gigabit Ethernet | **Rejected** — latency kills throughput |
| (b) MLX on M4 Max alone | Single node, 128GB, native Apple Silicon | **Approved** |
| (c) llama.cpp RPC server | Distributed via RPC | **Rejected** — same network bottleneck |
| (d) Thunderbolt direct-connect | Hardware investment, TB5/TB4 cables | **Future** — evaluate if MLX insufficient |

## Why Exo Failed (Field Experience)

TPM tested Exo in the past and found:
1. **Gigabit Ethernet bottleneck** — 1 Gb/s = ~125 MB/s, far below the 546 GB/s memory bandwidth of M4 Max
2. **mDNS discovery unreliable** — sasass2 had intermittent connectivity (USB Ethernet dongle)
3. **Token throughput dropped to 5-10 tok/s** vs 10-15 tok/s on single node
4. **No RDMA over Ethernet** — TB5 supports RDMA but Gigabit Ethernet does not
5. **Complexity tax** — 3 nodes to maintain, debug, and monitor vs 1

## Why MLX Wins

1. **128GB is enough** — Qwen2.5 72B 4-bit needs ~40GB, leaving 88GB for KV cache and OS
2. **Native Apple Silicon** — MLX is optimized for unified memory architecture
3. **No network overhead** — zero latency between memory and compute
4. **10-15 tok/s** — acceptable for batch and interactive use
5. **Simpler operations** — one node, one service, one log file

## Council Specialist Votes

| Specialist | Vote | Rationale |
|-----------|------|-----------|
| Gecko (Perf) | (b) MLX | Latency violates SLAs over Ethernet |
| Raven (Strategy) | (d) TB | Long-term investment in TB direct-connect |
| Spider (Integration) | (d) TB | Exo integration complexity too high |
| Turtle (7Gen) | (b) MLX | Sustainability over raw power |
| Crawdad (Security) | (b) MLX | Distributed = larger attack surface |
| Eagle Eye (Monitor) | (b) MLX | Centralized = simpler observability |
| Peace Chief | (b)+(d) | Consensus: MLX now, TB later |

## Key Learnings

1. **Memory bandwidth > total memory** for LLM inference. A single M4 Max at 546 GB/s outperforms 3 nodes pooled over 1 Gb/s Ethernet.
2. **Quantization is the real enabler** — 4-bit quantization makes 70B fit on 128GB with room to spare. Don't need 256GB.
3. **Don't distribute what you can localize** — network overhead dominates compute savings for memory-bandwidth-bound workloads.
4. **TB direct-connect is the right long-term play** if we need >128GB models (405B, 671B).

## Implementation

- Jr Instruction: `JR-MAC-MLX-70B-INFERENCE-FEB07-2026.md` (Task MLX-M4MAX-001)
- Withdrawn: `JR-MAC-CLUSTER-EXO-DISTRIBUTED-INFERENCE-FEB07-2026.md` (Task EXO-CLUSTER-001)
- Port: 8800 on tpm-macbook
- Model: mlx-community/Qwen2.5-72B-Instruct-4bit
- Server: mlx_lm.server or mlx-openai-server (OpenAI-compatible)

## Avoid These Mistakes

- Don't try Exo over Gigabit Ethernet again — it doesn't work at acceptable latency
- Don't assume more nodes = more throughput for LLM inference
- Don't run FP16 when 4-bit quantization has minimal quality loss for inference
- Always check `mlx-community` on HuggingFace for pre-quantized models before converting yourself

---
**FOR SEVEN GENERATIONS** — Document decisions so future TPMs don't repeat our experiments.
