# Jr Instructions: Evaluate QServe Quantization for vLLM

**Date**: 2025-12-27
**Priority**: #2 - Council Quick Win (after Reflexion)
**Assigned To**: Jr on redfin
**Risk Level**: Medium (requires vLLM restart)

---

## Objective

Evaluate QServe W4A8KV4 quantization to improve throughput on redfin. Current state:
- GPU: NVIDIA RTX PRO 6000 Blackwell (96GB)
- Model: Qwen2.5-Coder-32B @ FP16 (~64GB model weights)
- Current throughput: ~27 tok/sec
- Memory used: 96.5GB (maxed out)

**Target**: 2-3x throughput with W4A8KV4 quantization

---

## Research Summary

**Paper**: QServe: W4A8KV4 Quantization (MLSys 2025)
- 4-bit weights + 8-bit activations + 4-bit KV cache
- Reduces 32B model from ~64GB to ~20GB
- Frees memory for larger batch sizes
- Achieves 2.4-3.5x throughput on 72B models

**Alternative**: ATOM 4-bit (MLSys 2024)
- 7.7x over FP16, 2.5x over INT8
- Mixed-precision with outlier handling

---

## Phase 1: Research (No Production Impact)

### Step 1: Check vLLM quantization support
```bash
# On redfin
cd /home/dereadi/cherokee_venv
source bin/activate
python -c "import vllm; print(vllm.__version__)"

# Check supported quantization methods
vllm serve --help | grep -A5 quantization
```

### Step 2: Check if quantized model exists
```bash
# Search HuggingFace for pre-quantized Qwen2.5-32B
# Options: AWQ, GPTQ, GGUF

ls /ganuda/models/
# Do we have any quantized variants?
```

### Step 3: Benchmark current performance
```bash
# Save baseline metrics
curl -s http://localhost:8000/metrics | grep -E "(vllm_|tokens)" > /ganuda/benchmarks/baseline_$(date +%Y%m%d).txt

# Test with standard prompt
time curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-coder-32b", "prompt": "Write a Python function to sort a list:", "max_tokens": 200}'
```

---

## Phase 2: Quantized Model Download (Requires Disk Space)

### Option A: AWQ Quantization (Recommended for vLLM)
```bash
# Check HuggingFace for AWQ version
# Qwen/Qwen2.5-Coder-32B-Instruct-AWQ (if exists)
# Or community quantization

huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ \
  --local-dir /ganuda/models/qwen2.5-32b-awq
```

### Option B: GPTQ Quantization
```bash
huggingface-cli download TheBloke/Qwen2.5-32B-Instruct-GPTQ \
  --local-dir /ganuda/models/qwen2.5-32b-gptq
```

---

## Phase 3: Testing (Staging - Off-Peak Hours)

### Step 1: Stop production vLLM
```bash
# ONLY during off-peak hours
# Notify TPM first

sudo systemctl stop vllm  # or kill process
```

### Step 2: Start with quantized model
```bash
# AWQ example
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-32b-awq \
  --port 8000 \
  --quantization awq \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32000 \
  --max-num-seqs 512 \
  --trust-remote-code
```

### Step 3: Benchmark
```bash
# Compare throughput
curl -s http://localhost:8000/metrics | grep -E "(vllm_|tokens)" > /ganuda/benchmarks/awq_$(date +%Y%m%d).txt

# Run same test prompt
time curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-32b-awq", "prompt": "Write a Python function to sort a list:", "max_tokens": 200}'
```

### Step 4: Quality check
Run 10 standard prompts and compare output quality between FP16 and quantized.

---

## Rollback Plan

If quantized model has quality issues:
```bash
# Restore original
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-coder-32b \
  --port 8000 \
  --gpu-memory-utilization 0.70 \
  --max-model-len 15000 \
  --max-num-seqs 256 \
  --trust-remote-code \
  --enforce-eager
```

---

## Success Criteria

- [ ] Baseline benchmark captured
- [ ] Quantized model downloaded
- [ ] Throughput improvement measured (target: 2x+)
- [ ] Quality regression tested (acceptable loss < 5%)
- [ ] Memory reduction confirmed
- [ ] Production recommendation documented

---

## Output

Write findings to: `/ganuda/docs/kb/KB-00XX-QServe-Quantization-Results.md`

Include:
- Throughput before/after
- Memory usage before/after
- Quality comparison
- Recommendation (deploy or not)

---

*For Seven Generations*
