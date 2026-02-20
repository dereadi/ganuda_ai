# KB: vLLM Blackwell GPU (sm_120) Triton Attention Fix

**Date:** 2026-02-09
**Kanban:** #1740
**Node:** bluefin (NVIDIA RTX PRO 6000 Blackwell Max-Q)
**Status:** Resolved

---

## Environment

| Component | Version |
|-----------|---------|
| GPU | NVIDIA RTX PRO 6000 Blackwell Max-Q (sm_120), 96 GB VRAM |
| vLLM | 0.15.1 (pip wheel) |
| PyTorch | 2.9.1+cu128 |
| CUDA Toolkit | 12.8 |
| NVIDIA Driver | 570.211.01 |
| Model | Qwen2.5-72B-Instruct-AWQ |

---

## Problem

vLLM crashes with `torch.AcceleratorError: CUDA error: the provided PTX was compiled with an unsupported toolchain` (cudaErrorUnsupportedPtxVersion) when serving Qwen2.5-72B-Instruct-AWQ on the Blackwell RTX PRO 6000.

The crash occurs at two separate points during startup and inference:

1. **Marlin kernels during AWQ weight conversion** -- vLLM auto-promotes `awq` quantization to `awq_marlin` for performance, then attempts to run pre-compiled Marlin GEMM kernels that do not support sm_120.
2. **Flash Attention C extension (`_vllm_fa2_C.varlen_fwd`) during forward pass** -- the pre-built Flash Attention shared library shipped with the pip wheel was compiled for sm_80/86/89/90/100 but NOT sm_120.

Both failures share the same root cause: the pre-built CUDA extensions in the vLLM pip wheel were never compiled for Blackwell (compute capability 12.0 / sm_120).

---

## Root Cause

Pre-built vLLM pip wheels compile all CUDA extensions (Marlin quantization kernels, Flash Attention, CUDA graphs) targeting a fixed set of GPU architectures: sm_80, sm_86, sm_89, sm_90, and sm_100. The Blackwell architecture (sm_120) is not included. When these pre-compiled PTX/SASS binaries are loaded on a Blackwell GPU, the CUDA runtime rejects them with `cudaErrorUnsupportedPtxVersion`.

This is a packaging gap, not a fundamental incompatibility. The underlying algorithms all work on Blackwell when compiled from source with the correct architecture target.

---

## Solution

All three parts are required together. Omitting any one of them results in a crash.

### 1. Disable Marlin Kernels

```bash
export VLLM_DISABLED_KERNELS=MarlinLinearKernel
```

This environment variable prevents the Marlin kernel from being selected during quantization backend resolution. vLLM falls back to the pure AWQ GEMM path, which uses PyTorch-native operations that JIT-compile correctly for sm_120.

### 2. Use Triton-Based Attention Backend

```bash
vllm serve ... --attention-backend TRITON_ATTN
```

This CLI argument tells vLLM to use the Triton-based attention implementation instead of the pre-built Flash Attention C extension. Triton JIT-compiles its kernels at runtime, which means it generates correct sm_120 code on the fly.

### 3. Enforce Eager Mode (Skip CUDA Graphs)

```bash
vllm serve ... --enforce-eager
```

CUDA graph capture also triggers sm_120-incompatible code paths in the pre-built extensions. Eager mode avoids this entirely.

### 4. Point Triton to a Compatible ptxas

```bash
export TRITON_PTXAS_PATH=/path/to/triton/bundled/ptxas
```

Triton's bundled ptxas (V12.8.93) supports sm_120. The system ptxas may be an older version that does not. Verify with:

```bash
$TRITON_PTXAS_PATH --version
# Expected: Cuda compilation tools, release 12.8, V12.8.93
```

### Working Service File

The production systemd unit is at `/ganuda/config/vllm.service`. The key environment and argument lines:

```ini
[Service]
Environment="VLLM_DISABLED_KERNELS=MarlinLinearKernel"
Environment="TRITON_PTXAS_PATH=/path/to/triton/bundled/ptxas"
ExecStart=/path/to/vllm serve Qwen2.5-72B-Instruct-AWQ \
    --attention-backend TRITON_ATTN \
    --enforce-eager \
    ...
```

---

## What Did NOT Work

| Attempt | Why It Failed |
|---------|---------------|
| `--quantization awq` alone | vLLM auto-promotes AWQ to `awq_marlin` regardless of the explicit flag, so Marlin kernels still load and crash. |
| `VLLM_ATTENTION_BACKEND=TRITON_FLASH_ATTN` env var | This environment variable is ignored by the V1 engine. Backend selection in V1 must go through the CLI `--attention-backend` argument. |
| `cuda-compat-12-8` package | The version available (575) is an empty placeholder. The package description states it is for "TESLA cards only" and provides no actual compatibility shim for consumer/workstation Blackwell GPUs. |
| Fixing only one crash point | The Marlin fix alone gets past weight loading but crashes in Flash Attention. The attention fix alone crashes during weight conversion. Both must be addressed. |

### Note on the 32B Model

Qwen2.5-Coder-32B-AWQ happened to work on sm_120 before this fix was applied. This is because the 32B model's smaller weight dimensions exercised different Marlin code paths that did not trigger the incompatible kernels. This was coincidental and not a reliable workaround.

---

## Performance Notes

- **Pure AWQ GEMM is approximately 10x slower than Marlin** for quantized matrix multiplication. This is the cost of the fallback path.
- **Triton attention adds some overhead** compared to the pre-compiled Flash Attention C extension, due to JIT compilation on first request and slightly less optimized codegen.
- **Observed throughput:** 22 tokens generated in approximately 1 second for short prompts. Adequate for interactive use; not ideal for high-throughput batch serving.

---

## Future Improvement

Build vLLM from source with explicit Blackwell architecture support:

```bash
export TORCH_CUDA_ARCH_LIST="12.0"
pip install vllm --no-binary vllm
# or
git clone https://github.com/vllm-project/vllm.git
cd vllm && TORCH_CUDA_ARCH_LIST="12.0" pip install -e .
```

This would compile Marlin, Flash Attention, and all other CUDA extensions natively for sm_120, eliminating the need for the three workarounds and restoring full Marlin + Flash Attention performance. Monitor the vLLM release notes for official sm_120 support in future pip wheels.
