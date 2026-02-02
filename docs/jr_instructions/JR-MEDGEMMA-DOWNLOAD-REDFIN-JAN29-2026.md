# JR-MEDGEMMA-DOWNLOAD-REDFIN-JAN29-2026
## Download and Serve MedGemma 4B on Redfin

**Priority:** High
**Target Node:** redfin (192.168.132.223)
**Prerequisite:** HuggingFace authentication (manual step)

### Pre-Requisite (Manual)

1. Accept license at https://huggingface.co/google/medgemma-4b-it
2. Generate token at https://huggingface.co/settings/tokens
3. On redfin: `huggingface-cli login` and paste token

### Step 1: Download Model

```bash
# Download to /ganuda/models/medgemma-4b-it
huggingface-cli download google/medgemma-4b-it \
  --local-dir /ganuda/models/medgemma-4b-it \
  --local-dir-use-symlinks False
```

Estimated size: ~8 GB (fp16). Download time at 350 Mbps: ~3 minutes.

### Step 2: Quantize to INT4 (Optional - saves VRAM)

```python
# Only needed if GPU headroom is tight (<8 GB free)
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

model = AutoModelForCausalLM.from_pretrained(
    "/ganuda/models/medgemma-4b-it",
    quantization_config=quantization_config,
    device_map="auto",
)
model.save_pretrained("/ganuda/models/medgemma-4b-it-int4")
```

INT4 size: ~2-3 GB VRAM.

### Step 3: Serve via vLLM (Separate Port)

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/medgemma-4b-it \
  --port 8003 \
  --gpu-memory-utilization 0.08 \
  --max-model-len 4096 \
  --max-num-seqs 16 \
  --trust-remote-code \
  --served-model-name medgemma
```

Or with quantized version:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/medgemma-4b-it-int4 \
  --port 8003 \
  --gpu-memory-utilization 0.04 \
  --max-model-len 4096 \
  --max-num-seqs 8 \
  --trust-remote-code \
  --served-model-name medgemma \
  --quantization bitsandbytes
```

### Current GPU State (Jan 29 2026)

| Process | VRAM | Port |
|---------|------|------|
| Qwen2.5-Coder-32B-AWQ | 76.4 GB | 8000 |
| Cherokee Resonance v1 | 8.5 GB | 8002 |
| Free | ~11 GB | - |

MedGemma fp16 needs ~8 GB. INT4 needs ~3 GB. Either fits.

### Step 4: Wire into VetAssist

Update `/ganuda/vetassist/backend/app/services/medical_document_processor.py` to use the vLLM endpoint:

```python
self.api_url = "http://192.168.132.223:8003/v1"
```

### Verification

```bash
curl -X POST http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "medgemma", "messages": [{"role": "user", "content": "What are the diagnostic criteria for PTSD according to DSM-5?"}], "max_tokens": 500}'
```
