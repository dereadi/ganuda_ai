# JR Instruction: Downgrade PyTorch to Stable and Fix vLLM

**JR ID:** JR-VLLM-PYTORCH-STABLE
**Priority:** P0 (Blocking Council Operations)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Infrastructure Jr.
**Effort:** Small (30-60 minutes)

---

## Problem Statement

vLLM service is failing with CUDA ABI mismatch:
```
ImportError: vllm/_C.abi3.so: undefined symbol: _ZN3c104cuda29c10_cuda_check_implementationEiPKcS2_ib
```

**Root Cause:** PyTorch was upgraded to dev/nightly build (2.11.0.dev20260119+cu128) but vLLM 0.11.2 was compiled against stable PyTorch. The C++ ABI symbols don't match.

**Impact:**
- vLLM service restart loop (517+ attempts)
- Council endpoint unavailable
- LLM Gateway degraded

---

## Current State

| Component | Version | Status |
|-----------|---------|--------|
| PyTorch | 2.11.0.dev20260119+cu128 | Dev build - PROBLEMATIC |
| vLLM | 0.11.2 | ABI mismatch |
| CUDA | 12.8 | OK |
| Driver | 570.195.03 | OK |
| GPU | RTX PRO 6000 Blackwell (97GB) | OK |

---

## Solution: Downgrade to Stable PyTorch

### Step 1: Stop vLLM Service

```bash
sudo systemctl stop vllm
```

### Step 2: Downgrade PyTorch to Stable

```bash
source /home/dereadi/cherokee_venv/bin/activate

# Uninstall current dev builds
pip uninstall torch torchvision torchaudio -y

# Install stable PyTorch 2.5.x with CUDA 12.4 (most compatible with vLLM 0.11.x)
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Verify
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

### Step 3: Reinstall vLLM (to match PyTorch ABI)

```bash
pip install vllm==0.11.2 --force-reinstall --no-cache-dir
```

### Step 4: Verify and Restart

```bash
# Test vLLM import
python -c "import vllm; print(f'vLLM: {vllm.__version__}')"

# Start service
sudo systemctl start vllm

# Check status
sudo systemctl status vllm
journalctl -u vllm -f
```

---

## Alternative: Use Latest Stable vLLM

If 0.11.2 doesn't work with stable PyTorch:

```bash
# Install latest vLLM (will pull compatible PyTorch)
pip install vllm --upgrade --force-reinstall
```

---

## Verification

```bash
# Test LLM Gateway health
curl http://localhost:8080/health

# Test council endpoint
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Test: Is the council operational?", "context": "Post-fix verification"}'
```

---

## Success Criteria

- [ ] PyTorch downgraded to stable version (2.5.x)
- [ ] vLLM service starts without errors
- [ ] `nvidia-smi` shows vLLM process using GPU
- [ ] LLM Gateway health shows vLLM: healthy
- [ ] Council endpoint responds

---

## Future Maintenance

- Stay on PyTorch stable releases (not nightly/dev)
- Upgrade quarterly or when vLLM releases require it
- Test in staging before production upgrades

---

FOR SEVEN GENERATIONS
