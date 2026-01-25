# QServe Quantization Research - Phase 1 Findings

**Date**: 2025-12-27
**Node**: redfin (192.168.132.223)
**Status**: Research Complete - Ready for Phase 2
**Risk**: LOW (No production changes made)

---

## Executive Summary

Phase 1 research confirms that **AWQ quantization** is the optimal path forward for improving vLLM throughput on redfin. The current FP16 model is using 97GB of 98GB available GPU memory (99.3% utilization), leaving minimal room for batch processing. Quantization to AWQ 4-bit can reduce model memory from 62GB to approximately 16-18GB, freeing up ~45GB for larger batch sizes and improved throughput.

**Key Finding**: Official AWQ quantized model exists and is ready to deploy: `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ`

---

## Current Production State

### vLLM Configuration
- **vLLM Version**: 0.11.2
- **Model**: Qwen2.5-Coder-32B (FP16)
- **Model Path**: `/ganuda/models/qwen2.5-coder-32b`
- **Model Size on Disk**: 62GB
- **GPU**: NVIDIA RTX PRO 6000 Blackwell
- **Total GPU Memory**: 97,887 MiB (96GB)
- **GPU Memory Used**: 97,164 MiB (99.3% utilization)
- **GPU Utilization**: 0% (idle at time of measurement)

### Performance Baseline (from vLLM metrics)

**Token Processing**:
- Total prompt tokens processed: 65,389
- Total generation tokens: 9,050
- Total requests: 89

**Latency Metrics**:
- Average time to first token: 0.532 seconds (47.4s total / 89 requests)
- Average time per output token: 0.049 seconds (441.6s / 8,961 tokens)
- **Effective throughput: ~20.4 tokens/second** (1 / 0.049s)

**Cache Performance**:
- Prefix cache queries: 65,389 tokens
- Prefix cache hits: 34,560 tokens (52.9% hit rate)
- No preemptions (good stability)
- KV cache usage: 0% (at idle)

**Key Observation**: Most latency (8,880 of 8,961 samples) falls in the <0.05s bucket, indicating consistent performance but memory-bound batch sizes limiting throughput.

---

## vLLM Quantization Support

vLLM 0.11.2 supports **29 quantization methods**, including:

### Recommended for Production:
1. **awq** - Best for inference, well-tested with vLLM
2. **gptq** - Alternative 4-bit quantization
3. **gptq_marlin** - Optimized GPTQ kernel
4. **awq_marlin** - Optimized AWQ kernel

### Other Available Methods:
- fp8, fp8_e4m3, fp8_e5m2 (FP8 variants)
- bitsandbytes, hqq (dynamic quantization)
- gguf (LLaMA.cpp format)
- modelopt, torchao, auto-round
- And 16+ others

**Recommendation**: Use **AWQ** with standard kernel or **awq_marlin** for best vLLM compatibility.

---

## Available Pre-Quantized Models

### Official Qwen AWQ Models (RECOMMENDED)

1. **Qwen/Qwen2.5-Coder-32B-Instruct-AWQ**
   - Official 4-bit AWQ quantization
   - Direct from Qwen team
   - Best compatibility and quality assurance
   - HuggingFace: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ
   - Expected size: ~16-18GB

### Official Qwen GPTQ Models (Alternative)

2. **Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4**
   - Official 4-bit GPTQ quantization
   - HuggingFace: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4
   - Expected size: ~16-18GB

3. **Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8**
   - Official 8-bit GPTQ (higher quality, larger size)
   - HuggingFace: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8
   - Expected size: ~32-34GB

### Community Models (Not Recommended)
- kaitchup/Qwen2.5-Coder-32B-Instruct-AutoRound-GPTQ-4bit
- kaitchup/Qwen2.5-Coder-32B-Instruct-AutoRound-GPTQ-2bit (too aggressive)
- parasail-ai/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8-128k

**Note**: GGUF models exist but are primarily for llama.cpp, not optimal for vLLM.

---

## Expected Performance Improvements

### Memory Savings
- **Current**: 62GB FP16 model → 97GB GPU memory used
- **After AWQ**: ~16-18GB model → ~50GB GPU memory used
- **Freed Memory**: ~45-47GB (48% reduction in usage)

### Throughput Improvements
Based on QServe paper (MLSys 2025) and similar deployments:

- **Current**: ~20 tok/sec (memory-bound, minimal batching)
- **Expected with AWQ**: 40-70 tok/sec (2-3.5x improvement)
- **Primary gain**: Larger batch sizes enabled by freed memory
- **Secondary gain**: Faster memory access for weights

### Quality Impact
- AWQ 4-bit typically shows <2% quality degradation
- Perplexity increase: ~0.1-0.3 points
- Code generation: Minimal impact on short completions
- Should verify with quality tests in Phase 2

---

## Recommended Approach: AWQ Quantization

### Why AWQ over GPTQ?

1. **Better vLLM Support**: AWQ is first-class citizen in vLLM
2. **Official Model Available**: Qwen provides official AWQ version
3. **Performance**: AWQ typically faster inference than GPTQ
4. **Marlin Kernel**: awq_marlin provides optimized inference
5. **Memory Efficiency**: Similar compression to GPTQ with better speed

### Why Not Other Methods?

- **FP8**: Requires specific GPU support, 8-bit not as compressed as 4-bit
- **GGUF**: Optimized for llama.cpp, not vLLM
- **BitsAndBytes**: Dynamic quantization, slower than static AWQ
- **2-bit**: Too aggressive, quality degradation unacceptable

---

## Phase 2 Plan: Staging Test

### Prerequisites
1. Download AWQ model: ~18GB download (verify disk space on redfin)
2. Schedule off-peak window for testing
3. Notify TPM before vLLM restart

### Test Configuration
```bash
# Download model
ssh dereadi@192.168.132.223
cd /ganuda/models
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct-AWQ \
  --local-dir qwen2.5-coder-32b-awq

# Start vLLM with AWQ
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-coder-32b-awq \
  --port 8000 \
  --quantization awq \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32000 \
  --max-num-seqs 512 \
  --trust-remote-code \
  --enable-prefix-caching
```

### Success Criteria
- [ ] GPU memory usage <60GB (target: ~50GB)
- [ ] Throughput ≥40 tok/sec (2x improvement)
- [ ] Quality degradation <5% on test prompts
- [ ] No errors or crashes under load
- [ ] Latency remains acceptable (<1s TTFT)

### Rollback Plan
Restore FP16 model with original configuration (documented in Jr instructions).

---

## Disk Space Check

Current `/ganuda/models` usage:
```
qwen2.5-coder-32b:              62GB (FP16 - current)
qwen2.5-coder-32b-awq:          ~18GB (estimated - to download)
```

**Action Required**: Verify free space on redfin `/ganuda` partition before downloading AWQ model.

```bash
ssh dereadi@192.168.132.223 "df -h /ganuda"
```

---

## Risk Assessment

### Phase 2 Risks (Staging Test)
- **Low**: Download failure (retry/resume supported)
- **Medium**: Quality degradation >5% (rollback to FP16)
- **Low**: Performance not meeting 2x target (keep FP16, try GPTQ)
- **Low**: vLLM compatibility issues (well-tested quantization)

### Mitigation
- Test during off-peak hours
- Keep FP16 model available for instant rollback
- Run quality tests before declaring success
- Document all configuration changes

---

## Next Steps

### Immediate (Phase 2 - Staging)
1. **Verify disk space** on redfin `/ganuda` partition
2. **Download AWQ model**: `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ`
3. **Schedule off-peak window** for vLLM restart
4. **Run staging test** with AWQ configuration
5. **Benchmark throughput** and compare to baseline
6. **Quality test**: 10+ standard prompts comparing FP16 vs AWQ
7. **Document results** and make go/no-go decision

### If Successful (Phase 3 - Production)
1. Update vLLM systemd service config
2. Switch to AWQ model in production
3. Monitor for 24-48 hours
4. Archive FP16 model (don't delete yet)
5. Update documentation

### If Unsuccessful
1. Rollback to FP16 immediately
2. Try GPTQ-Int4 as alternative
3. Consider GPTQ-Int8 if quality is critical
4. Document findings and recommendations

---

## Thermal Memory Archive

Baseline metrics saved to: `/ganuda/benchmarks/baseline_20251227.txt`

This document written to: `/Users/Shared/ganuda/docs/jr_instructions/JR-2025-12-27-QServe-Phase1-Research-Findings.md`

Copy to redfin KB when ready:
```bash
scp /Users/Shared/ganuda/docs/jr_instructions/JR-2025-12-27-QServe-Phase1-Research-Findings.md \
  dereadi@192.168.132.223:/ganuda/docs/kb/KB-2025-12-27-QServe-Phase1-Findings.md
```

---

## References

- QServe Paper: W4A8KV4 Quantization (MLSys 2025)
- vLLM Documentation: https://docs.vllm.ai/en/latest/
- Qwen2.5-Coder-32B-AWQ: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ
- Qwen2.5-Coder-32B-GPTQ-Int4: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4

---

**For Seven Generations**

*Research conducted by Jr Agent on behalf of Cherokee AI Federation*
*TPM: Derek Readi*
*Node: redfin (192.168.132.223)*
*Date: 2025-12-27*
