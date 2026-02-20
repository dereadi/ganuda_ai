# KB: vLLM Native sm_120 Build — 32.4 tok/s on Blackwell

**Date**: February 9, 2026
**Kanban**: #1740
**Node**: redfin (192.168.132.223)
**GPU**: NVIDIA RTX PRO 6000 Blackwell (sm_120), 96GB GDDR7

## Summary

Built vLLM v0.15.1 from source with `TORCH_CUDA_ARCH_LIST="12.0"` to get native Marlin + Flash Attention CUDA kernels for Blackwell sm_120. This eliminated all workaround flags and achieved **32.4 tokens/sec** (4-10x over the workaround config).

## Before (Workaround)

Pre-built pip wheels lacked sm_120 kernels. Required three workarounds:
1. `VLLM_DISABLED_KERNELS=MarlinLinearKernel` (disabled Marlin quantization acceleration)
2. `--attention-backend TRITON_ATTN` (CLI arg, NOT env var — V1 engine only reads CLI)
3. `--enforce-eager` (disabled torch.compile/CUDA graphs)

Result: ~3-8 tok/s. Functional but slow.

## After (Native Build)

Source build with `TORCH_CUDA_ARCH_LIST="12.0"` compiled native sm_120 kernels:
- Marlin AWQ quantization kernels (confirmed: `strings` shows `arch sm_120`)
- Flash Attention v2 kernels
- torch.compile active (not enforce-eager)

Service config (`/ganuda/config/vllm.service.native`):
```
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-72b-instruct-awq \
  --port 8000 \
  --quantization awq_marlin \
  --dtype float16 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 32768 \
  --max-num-seqs 256 \
  --trust-remote-code
```

No workaround flags. Clean config.

## Benchmark

- **Model**: Qwen2.5-72B-Instruct-AWQ
- **Throughput**: 32.4 tokens/sec
- **Model load**: 38.77 GiB
- **KV cache**: 39.31 GiB, 128,816 tokens capacity
- **Quantization**: awq_marlin (native Marlin kernels)

## Build Process

1. `scripts/build_vllm_sm120.sh` — Steps 1-4 (deps, backup, clone v0.15.1, build)
2. Network drop interrupted between Step 4 and 5
3. `scripts/resume_vllm_sm120_step5.sh` — Steps 5-7 (smoke test, deploy, benchmark)
4. Build logs: `/ganuda/logs/vllm-source-build-*.log`, `/ganuda/logs/vllm-sm120-resume-*.log`

## Key Details

- CUDA 12.8 toolkit at `/ganuda/cuda-12.8`
- Build env: `CMAKE_CUDA_COMPILER=$CUDA_HOME/bin/nvcc`, `MAX_JOBS=16`
- Old workaround config preserved at `/ganuda/config/vllm.service.workaround`
- `cuda-compat-12-8` (575 driver) is TESLA-only placeholder — does NOT help workstation GPUs

## Rollback

If native build fails after restart:
```bash
sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl restart vllm.service
```
