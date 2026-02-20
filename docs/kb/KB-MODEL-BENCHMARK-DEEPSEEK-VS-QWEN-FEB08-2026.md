# KB: Model Benchmark — DeepSeek-R1-32B vs Qwen2.5-Coder-32B

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Category:** Performance / Architecture

## Test Setup

| Model | Node | Hardware | Backend | Port |
|-------|------|----------|---------|------|
| DeepSeek-R1-Distill-Qwen-32B-4bit | bmasass (.21) | M4 Max 128GB | MLX | 8800 |
| Qwen2.5-Coder-32B-AWQ | redfin (.223) | RTX 6000 96GB | vLLM | 8000 |

Both accessed through LLM Gateway v1.6.0 at redfin:8080.

## Results

| Domain | Model | Time | Tokens | tok/s | Quality |
|--------|-------|------|--------|-------|---------|
| Legal | DeepSeek-R1 | 41.3s | 955 | 23.1 | Structured numbered criteria, detailed |
| Legal | Qwen-Coder | 8.0s | 526 | 65.5 | Accurate but concise |
| Coding | DeepSeek-R1 | 65.9s | 1,500 | 22.8 | Detailed with reasoning chain |
| Coding | Qwen-Coder | 9.3s | 609 | 65.8 | Clean, practical, production-ready |
| Cherokee | DeepSeek-R1 | 50.2s | 1,136 | 22.6 | Rich philosophical essay with sections |
| Cherokee | Qwen-Coder | 11.5s | 756 | 65.5 | Solid explanation, less depth |

## Key Findings

1. **Speed**: Qwen2.5-Coder is ~3x faster (65 vs 23 tok/s). This is primarily hardware difference (RTX 6000 CUDA vs M4 Max MLX), not model quality.

2. **Depth**: DeepSeek-R1 produces significantly more detailed, structured, and thoughtful responses. The chain-of-thought reasoning adds quality but consumes tokens and time.

3. **Token usage**: DeepSeek-R1 uses 1.5-2.5x more tokens per response. The reasoning chain (invisible to the user) accounts for 200-500 additional tokens.

4. **Legal domain**: Both models correctly identified 38 CFR 4.130 criteria for 70% PTSD rating. DeepSeek was more structured with numbered specific criteria.

5. **Coding domain**: Both produced working psycopg2 code. Qwen was more concise and "copy-paste ready." DeepSeek explained the reasoning behind design choices.

6. **Cherokee domain**: DeepSeek produced a richer philosophical answer connecting Gadugi to distributed AI. Qwen was accurate but more surface-level.

## Verdict

**Different tools for different jobs.** Not a replacement, a complement.

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| Jr task execution | Qwen-Coder | Speed matters, tasks are well-defined |
| Legal analysis (VetAssist) | DeepSeek-R1 | Depth and structure matter |
| Council votes | Either | Council uses Qwen internally already |
| Strategic planning | DeepSeek-R1 | Reasoning chain produces better analysis |
| Quick coding tasks | Qwen-Coder | Fast, practical, less overhead |
| Cherokee cultural questions | DeepSeek-R1 | Richer, more thoughtful responses |

## Gateway Routing

Access via `redfin:8080/v1/chat/completions`:
- `"model": "deepseek-r1"` or `"model": "reasoning"` → bmasass:8800 (MLX)
- `"model": "cherokee-council"` or `"model": "gpt-4"` → redfin:8000 (vLLM)

## Future: 70B on Redfin

Council vote #8485 approved upgrading redfin to a 70B model at 4-bit (~40GB) with Share LoRA subspace. If the PoC succeeds:
- One 70B model handles all domains via shared subspace
- 56GB free VRAM enables 8+ concurrent Jr slots
- DeepSeek-R1 on bmasass remains the dedicated reasoning backend
- Effective 3-backend architecture: coding (redfin), reasoning (bmasass), vision (bluefin)

## Related
- Benchmark data: `/ganuda/docs/research/benchmark_head_to_head_feb08.json`
- Ultrathink: `/ganuda/docs/ultrathink/ULTRATHINK-SHARE-LORA-FEDERATION-ARCHITECTURE-FEB08-2026.md`
- Council votes: #8482 (LoRA PoC), #8485 (VRAM strategy)
- Gateway: `/ganuda/services/llm_gateway/gateway.py` (v1.6.0)
