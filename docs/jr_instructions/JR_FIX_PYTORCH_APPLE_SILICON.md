# Jr Task: Fix PyTorch SIGBUS Crash on Apple Silicon (sasass)

**Ticket:** #1696-BLOCKER
**Priority:** P0 (Blocking T5 Testing)
**Node:** sasass (Mac Studio M1 Max)
**Created:** December 21, 2025
**Specialist:** Gecko (Technical Integration)

---

## Problem Description

When attempting to load T5/Gemma models on sasass (Mac Studio M1 Max with 64GB RAM), PyTorch crashes with a memory alignment fault:

```
Exception Type:        EXC_BAD_ACCESS (SIGBUS)
Exception Subtype:     EXC_ARM_DA_ALIGN at 0x000000034230f7fe
Thread 0 Crashed:
libBLAS.dylib  cblas_sgemm + 404
```

This is a known issue with PyTorch on Apple Silicon where certain BLAS operations fail due to memory alignment requirements.

---

## Root Cause

The crash occurs in `cblas_sgemm` (single-precision matrix multiplication) when PyTorch tensors are not properly aligned for ARM NEON/AMX operations. This is triggered during model weight loading.

---

## Solution Options

### Option 1: Use MPS-Compatible PyTorch (Recommended)

```bash
# On sasass
cd /Users/Shared/ganuda/models

# Create clean venv
python3.11 -m venv venv-t5
source venv-t5/bin/activate

# Install MPS-aware PyTorch
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install transformers
pip install transformers accelerate sentencepiece
```

### Option 2: Force CPU with Aligned Tensors

Create wrapper script that forces proper alignment:

```python
# /Users/Shared/ganuda/lib/safe_model_loader.py

import torch
import os

# Force CPU and disable MPS
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

def load_model_safe(model_name):
    """Load transformers model with Apple Silicon safety"""
    from transformers import AutoModel, AutoTokenizer

    # Ensure float32 for BLAS compatibility
    torch.set_default_dtype(torch.float32)

    # Load to CPU explicitly
    model = AutoModel.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer
```

### Option 3: Use MLX Instead (Apple Native)

For long-term, consider using Apple's MLX framework which is native to Apple Silicon:

```bash
pip install mlx mlx-lm

# MLX has native T5 support
python -c "from mlx_lm import load; model, tokenizer = load('google/t5-base')"
```

---

## Verification Steps

After applying fix:

```bash
# Test basic model loading
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'MPS available: {torch.backends.mps.is_available()}')

from transformers import T5ForConditionalGeneration, T5Tokenizer
print('Loading T5-base...')
model = T5ForConditionalGeneration.from_pretrained('t5-base', torch_dtype=torch.float32)
tokenizer = T5Tokenizer.from_pretrained('t5-base')
print('Model loaded successfully')

# Quick inference test
input_text = 'translate English to German: Hello, how are you?'
inputs = tokenizer(input_text, return_tensors='pt')
outputs = model.generate(**inputs, max_length=50)
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f'Result: {result}')
print('T5 OPERATIONAL on Apple Silicon')
"
```

---

## Success Criteria

1. T5-base loads without SIGBUS crash
2. Basic inference completes
3. Memory usage stays under 32GB
4. Ready for T5-Gemma 2 testing

---

## Fallback Plan

If PyTorch continues to crash on sasass:

1. **Shift T5 testing to redfin** (Linux with CUDA - known stable)
2. **Use sasass for other tasks** (Constitution engine, Jr state manager)
3. **Document incompatibility** in thermal memory

---

## Notes

- This is a known PyTorch issue on Apple Silicon M1/M2/M3
- The crash is NOT in our code - it's in Apple's BLAS library
- MLX may be better long-term for Mac Studio edge inference
- HuggingFace models need explicit `torch_dtype=torch.float32`

---

*For Seven Generations - Cherokee AI Federation*
