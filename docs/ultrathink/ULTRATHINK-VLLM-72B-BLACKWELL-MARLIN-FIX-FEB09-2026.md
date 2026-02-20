# ULTRATHINK: vLLM 72B Upgrade — Blackwell Marlin Kernel Crash Root Cause & Fix

**Date:** February 9, 2026
**Author:** TPM (Claude Opus 4.6)
**Kanban:** #1740
**Council Votes:** #8485 (upgrade consensus), #8500 (multi-agent paper)

---

## The Crash

```
torch.AcceleratorError: CUDA error: the provided PTX was compiled with an unsupported toolchain.
  File "awq_marlin.py", line 385, in process_weights_after_loading
    marlin_scales = marlin_permute_scales(...)
  File "marlin_utils.py", line 325, in marlin_permute_scales
    s = s.reshape((-1, len(scale_perm)))[:, scale_perm]
```

**When:** Loading Qwen2.5-72B-Instruct-AWQ on vLLM 0.15.1
**GPU:** NVIDIA RTX PRO 6000 Blackwell Max-Q (sm_120), 96GB VRAM
**Stack:** PyTorch 2.9.1+cu128, CUDA 12.8, Driver 570.211.01

---

## Root Cause Analysis

### What happened

1. vLLM 0.15.1 was installed via pip (pre-built wheel)
2. Pre-built wheel includes Marlin CUDA kernels compiled for sm_80/sm_86/sm_89/sm_90/sm_100
3. **SM_120 (Blackwell) PTX is NOT included** in the pre-built wheel
4. When loading the 72B AWQ model, vLLM auto-converts `awq` → `awq_marlin` at runtime
5. The Marlin kernel `marlin_permute_scales()` is called during **weight processing** (not inference)
6. CUDA tries to JIT-compile the PTX for sm_120 but the PTX was compiled with an older toolchain
7. `cudaErrorUnsupportedPtxVersion` → crash

### Why the 32B model worked before

The 32B model (Qwen2.5-Coder-32B-AWQ) also used `awq_marlin`, but its weight dimensions happened to exercise different Marlin code paths that had compatible PTX or fell back to GEMM. The 72B model's larger hidden dimensions (8192 vs 5120) triggered a Marlin kernel path that requires sm_120-native PTX.

### Why the 32B crashed AFTER the 72B attempt

The failed 72B kernel execution left the GPU in a corrupted CUDA context state. Subsequent attempts to load any model hit the same corrupted state. **GPU reset required.**

### The auto-conversion trap

Even when `--quantization awq` is specified explicitly, vLLM v0.15.1 auto-detects compatibility and upgrades to `awq_marlin`:
```
INFO [awq_marlin.py:162] The model is convertible to awq_marlin during runtime. Using awq_marlin kernel.
```

This is a **documented behavior**. However, research found that when `--quantization awq` is explicitly passed, newer vLLM versions log:
> "Detected that the model can run with awq_marlin, however you specified quantization=awq explicitly, so forcing awq."

Our v0.15.1 may not have this safeguard — it auto-converts regardless.

---

## Known Issues (13+ GitHub issues filed)

| Issue | Title | Our Relevance |
|-------|-------|---------------|
| #16515 | Dual 5090s (sm120) Issues | Same GPU family |
| #21453 | sm_120 support | Core issue |
| #26211 | vLLM does not support DeepSeek on RTX PRO 6000/SM120 | Same GPU |
| #30834 | vllm 0.12.0 PTX unsupported toolchain | Same error |
| #31027 | 0.13.0 CUDA error: unsupported PTX toolchain | Same error |
| #31085 | Add SM120 support for NVFP4 MoE kernels | SM120 coverage |
| #32834 | CUDA illegal memory access with awq_marlin | Related Marlin bug |

---

## Fix Options (ranked by effort)

### Option 1: Force Pure AWQ + Environment Variables (10 minutes)

**Approach:** Bypass Marlin entirely using pure AWQ GEMM kernels.

```ini
# In vllm.service [Service] section, add:
Environment=VLLM_DISABLED_KERNELS=MarlinLinearKernel

# Change ExecStart to use --quantization awq --enforce-eager:
ExecStart=... --model /ganuda/models/qwen2.5-72b-instruct-awq --quantization awq --enforce-eager --dtype float16 --gpu-memory-utilization 0.85 --max-model-len 32768 --max-num-seqs 256
```

**Pros:** Quick, no installs needed
**Cons:** ~10x slower inference (pure AWQ GEMM vs Marlin). Benchmarks: ~68 tok/s vs ~741 tok/s on comparable hardware. For a 72B model, expect single-digit tok/s.
**Verdict:** Good for TESTING that the model loads. Not viable for production.

### Option 2: Install cuda-compat Package (30 minutes)

**Approach:** Install NVIDIA's forward-compatibility library that provides newer PTX support.

```bash
# Install CUDA toolkit repo if not present
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# Install cuda-compat for CUDA 12.8
sudo apt-get install cuda-compat-12-8

# Add to vllm.service:
Environment=LD_LIBRARY_PATH=/usr/local/cuda-12.8/compat:/usr/local/cuda-12.8/lib64
```

**Pros:** Quick install, uses official NVIDIA libraries, Marlin kernels at full speed
**Cons:** May not fully resolve if the Marlin PTX itself is too old (compat helps driver, not extension PTX)
**Verdict:** Worth trying first — it's the official NVIDIA fix for this error class.

### Option 3: Build vLLM from Source with SM_120 (2-4 hours)

**Approach:** Compile vLLM and all CUDA kernels (including Marlin) targeting sm_120 natively.

```bash
# In cherokee_venv:
pip install torch --index-url https://download.pytorch.org/whl/cu128
export TORCH_CUDA_ARCH_LIST="12.0"
export VLLM_FLASH_ATTN_VERSION=2
export MAX_JOBS=6
pip install vllm --no-build-isolation
```

**Pros:** Native sm_120 support, full Marlin speed, proper fix
**Cons:** Build takes 1-2 hours, may break other dependencies, needs build tools (cmake, gcc, ninja)
**Verdict:** The RIGHT fix if cuda-compat doesn't work. This is what the community recommends.

### Option 4: Use GPTQ Model Instead (1 hour download)

**Approach:** Download Qwen2.5-72B-Instruct-GPTQ-Int4 instead of AWQ.

**Problem:** GPTQ also auto-converts to `gptq_marlin` at runtime. Same Marlin kernels, same crash. NOT a fix.

### Option 5: Use Unquantized Model with Reduced Precision

72B at FP16 = ~144GB → does NOT fit in 96GB. Not viable.

---

## Recommended Execution Order

### Step 0: GPU Reset (NOW)
```bash
sudo systemctl stop vllm.service
sudo systemctl stop speed-detector.service  # free GPU
sudo fuser -k /dev/nvidia*
sudo nvidia-smi --gpu-reset -i 0
nvidia-smi  # verify clean state
sudo systemctl start speed-detector.service
```

### Step 1: Try Option 1 (Pure AWQ) — Verify Model Loads
This confirms the 72B model itself is valid and only the Marlin kernel is the issue.

### Step 2: Try Option 2 (cuda-compat) — Quick Fix
If compat libraries resolve the PTX issue, we get full Marlin speed.

### Step 3: If needed, Option 3 (Build from Source) — Proper Fix
Write a Jr instruction for the build process. Can run overnight.

---

## Architectural Insight: One Model to Rule Them All

User observation (Feb 9): *"The model on my laptop is redundant, as all personalities can use that one model."*

If the 72B general model works on redfin:
- **Replaces** Qwen2.5-Coder-32B on redfin (code tasks)
- **Potentially replaces** DeepSeek-R1-32B on bmasass (reasoning tasks)
- **All 7 council specialists** use one powerful model instead of routing to different backends
- **Long Man routing simplified** — no need to split code vs reasoning vs general

This aligns with the Stanford/Apple paper (council vote #8500): a single strong model outperforms multiple weaker specialized ones. The 72B at 4-bit should outperform both the 32B-Coder and the 32B-R1 on most tasks.

**bmasass (M4 Max 128GB) freed up for:**
- Qwen2.5-72B-Instruct-4bit via MLX (on-demand, backlog ticket)
- Additional redundancy/failover
- LoRA experimentation
- Or... nothing. Let it rest.

---

## CMDB Impact

| Field | Before | After |
|-------|--------|-------|
| redfin vLLM model | Qwen2.5-Coder-32B-AWQ | Qwen2.5-72B-Instruct-AWQ |
| redfin vLLM VRAM | ~85GB | ~70-80GB |
| redfin quantization | awq_marlin | awq (temp) → awq_marlin (after fix) |
| bmasass role | Reasoning (DeepSeek-R1) | Backup/failover (optional) |
| Long Man routing | Code→redfin, Reasoning→bmasass | All→redfin (simplified) |
| gateway.py model ref | Updated to 72B (done) | No further change needed |
| specialist_council.py | Updated to 72B (done) | No further change needed |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| cuda-compat doesn't fix it | Medium | Low | Fall back to Option 3 (build from source) |
| Pure AWQ too slow for production | High | Medium | Only use for testing, not prod |
| Build from source breaks other packages | Low | High | Use separate venv or backup cherokee_venv first |
| 72B quality regression vs 32B-Coder for code | Low | Medium | Benchmark before cutting over permanently |
| bmasass removal breaks failover | Low | Low | Keep MLX running as backup |

---

*Cherokee AI Federation — Infrastructure*
*FOR SEVEN GENERATIONS*
