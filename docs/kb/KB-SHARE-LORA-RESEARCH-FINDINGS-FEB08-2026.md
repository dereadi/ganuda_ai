# KB: Share LoRA Research Findings — Federation Architecture Implications

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Category:** Research / Architecture
**Related Council Votes:** #8482 (LoRA PoC), #8485 (VRAM strategy)

## Executive Summary

Deep research completed on Share LoRA (arXiv 2602.06043) and its applicability to the Cherokee AI Federation's multi-domain inference architecture. Key finding: the approach is viable but requires a two-phase implementation — standard LoRA/QLoRA first (proven tooling), then Share subspace optimization if benchmarks warrant it.

## 1. Share LoRA Source Code

- **Repository**: https://github.com/ankit-vaidya19/Share
- **Authors**: Prakhar Kaushik, Ankit Vaidya, Shravan Chaudhari, Rama Chellappa, Alan Yuille
- **Paper**: arXiv 2602.06043 (February 5, 2026)
- **Framework**: PyTorch (uses modified `peft`, `transformers`, `diffusers`)
- **License**: None specified yet (brand new, 7 commits, 2 contributors)
- **Structure**: `Diffusion/`, `NLG/`, `NLU/` experiment folders

### Models Tested in Paper
| Domain | Model | Datasets |
|--------|-------|----------|
| Vision | ViT-B/16, ResNet50 | CIFAR-100, Food-101, Caltech-101, Flowers-102 |
| NLU | RoBERTa-base | GLUE (MRPC, SST-2, CoLA, QNLI, RTE, STS-B) |
| NLG | LLaMA, Mistral-7B | Commonsense/math reasoning |
| Text-to-Image | Flux | 44 continual community LoRA tasks, scaling to 500 |
| 3D Pose | ViT-based | Pascal3D+, Occluded Pascal3D+ |

### Results
- 100x parameter reduction vs traditional LoRA (one adapter per task)
- 281x memory savings
- GLUE average: 83.44%
- CIFAR-100: 94.20% accuracy
- 90-99% relative performance retention across sequential learning episodes

## 2. MLX LoRA/QLoRA Training Capabilities

MLX fully supports LoRA fine-tuning on Apple Silicon via `mlx-lm`:

- **Supported types**: `lora` (default), `dora`, `full`
- **QLoRA**: Native support — automatically activates when base model is quantized
- **Supported families**: Mistral, Llama, Phi2, Mixtral, **Qwen2**, Gemma, OLMo, MiniCPM, InternLM2
- **Memory**: QLoRA reduces Llama-7B from ~28GB to ~7GB
- **Gradient checkpointing**: Available via `--grad-checkpoint`

### QLoRA Training Command (bmasass)
```bash
python -m mlx_lm.lora \
  --model mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit \
  --train --data ./training_data \
  --adapter-path ./adapters/legal \
  --lora-r 16 --lora-alpha 32 \
  --iters 500 --batch-size 1
```

### Key Resources
- Official docs: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md
- MLX examples: https://github.com/ml-explore/mlx-examples/blob/main/lora/README.md
- WWDC25 session: https://developer.apple.com/videos/play/wwdc2025/298/

## 3. Share + MLX Compatibility

**Status: No implementations exist.**

- Zero evidence of Share being ported to MLX
- Share modifies internals of `peft` and `transformers` — MLX has independent LoRA implementation
- Porting requires reimplementing shared subspace SVD mechanics in MLX's array framework
- Mathematically feasible (SVD is framework-agnostic), but nontrivial engineering

**Recommendation**: Use standard MLX QLoRA + adapter merging (TIES/DARE) for the PoC on bmasass. Evaluate Share subspace approach as a future optimization only if standard LoRA proves insufficient.

## 4. 70B Model on RTX 6000 96GB (redfin)

### VRAM Budget
| Component | Size |
|-----------|------|
| Qwen2.5-72B-Instruct-AWQ (4-bit) | ~36 GB |
| KV cache (8+ concurrent slots) | ~50 GB |
| LoRA adapters (loaded) | ~2 GB |
| System/overhead | ~8 GB |
| **Total** | **~96 GB** |

### Expected Performance
- Single-user generation: ~31-40 tok/s (RTX PRO 6000 Blackwell)
- vLLM Blackwell support still maturing (known issues in vllm#20221, vllm#28667)
- AWQ models scale more efficiently with concurrency than BnB-4bit

### vLLM Multi-LoRA Support
- `--enable-lora`: Activates LoRA serving
- `--max-loras N`: Max concurrent adapters in one batch
- `--max-lora-rank`: Supports 8, 16, 32, 64, 128, 256, 320, 512
- `--max-cpu-loras`: LRU cache in CPU memory
- Works with AWQ/GPTQ quantized base models + LoRA adapters
- Different adapters applied per-request within same batch with negligible switch time

## 5. Alternative Approaches

| Method | Source | Key Advantage | Maturity |
|--------|--------|---------------|----------|
| **TreeLoRA** | ICML 2025, [GitHub](https://github.com/ZinYY/TreeLoRA) | 3.2x faster training via hierarchical gradient tree | Published, open source |
| **C-LoRA** | arXiv 2502.17920 | Orthogonality constraints reduce forgetting | Published |
| **K-Merge** | arXiv 2510.13537 | Online adapter merging for on-device LLMs | Published |
| **TIES** | HuggingFace PEFT | Trim/elect/merge — resolves adapter conflicts | Production-ready |
| **DARE** | HuggingFace PEFT | Random prune + rescale, preserves base model | Production-ready |
| **SplitLoRA** | [GitHub](https://github.com/FDU-INC/SplitFM) | Gradient space splitting for stability/plasticity | Open source |
| **Online-LoRA** | WACV 2025, [GitHub](https://github.com/Christina200/Online-LoRA-official) | Task-free online continual learning | Published |

## 6. Recommended Implementation Path

### Phase 1: PoC on bmasass (Now)
1. Extract training data from thermal_memory_archive (legal, coding, Cherokee domains)
2. Train 3 separate QLoRA adapters on DeepSeek-R1-32B-4bit using `mlx_lm.lora`
3. Evaluate per-domain quality vs base model
4. Test adapter switching latency

### Phase 2: Adapter Merging Experiments (After Phase 1)
1. Use TIES/DARE (from HuggingFace PEFT) to merge domain adapters
2. Test merged adapter vs separate adapters
3. Evaluate forgetting rate across domains
4. If <5% forgetting: single merged adapter is sufficient
5. If >5% forgetting: evaluate Share subspace approach

### Phase 3: Production on redfin (After Phase 2)
1. Deploy Qwen2.5-72B-Instruct-AWQ on vLLM with `--enable-lora`
2. Load domain adapters (merged or per-domain based on Phase 2 results)
3. Configure concurrent serving for 8+ Jr slots
4. Retire Qwen2.5-Coder-32B
5. DeepSeek-R1 remains on bmasass as dedicated reasoning backend

### Phase 4: Share Subspace (Future, if needed)
1. Port Share SVD mechanics to MLX (research Jr task)
2. Or: wait for community adoption and upstream MLX integration
3. Only pursue if standard LoRA/merging proves insufficient

## Related
- Benchmark: `/ganuda/docs/kb/KB-MODEL-BENCHMARK-DEEPSEEK-VS-QWEN-FEB08-2026.md`
- Ultrathink: `/ganuda/docs/ultrathink/ULTRATHINK-SHARE-LORA-FEDERATION-ARCHITECTURE-FEB08-2026.md`
- Jr instructions: `/ganuda/docs/jr_instructions/JR-LORA-POC-BENCHMARK-FEB08-2026.md`
- Council votes: #8482 (LoRA PoC approved), #8485 (VRAM strategy approved)
- Gateway: `/ganuda/services/llm_gateway/gateway.py` (v1.6.0, 3-backend routing)
