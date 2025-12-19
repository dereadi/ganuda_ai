# FARA-7B Setup Guide - Cherokee AI Federation

**Created:** 2025-12-02
**Author:** Command Post (TPM)
**Location:** redfin (192.168.132.223)
**Status:** OPERATIONAL - Model loaded and tested successfully

---

## What is FARA-7B?

Microsoft's first **Computer Use Agent** - a 7B parameter model that can operate mouse and keyboard to complete tasks autonomously. Unlike chat models, FARA-7B:

- Processes screenshots visually (like a human)
- Generates actions: click, type, scroll, navigate
- Runs locally on device (no cloud required)
- Includes "Critical Point" safety pauses

---

## Hardware Requirements

| Resource | Minimum | redfin Actual |
|----------|---------|---------------|
| GPU VRAM | 16GB | **102GB** (RTX PRO 6000 Blackwell) |
| Disk | 20GB | **979GB free** |
| Python | 3.10+ | **3.12.3** |
| PyTorch | 2.0+ | **2.9.0+cu128** |

---

## Installation (COMPLETED)

Model location: `/ganuda/models/fara-7b/`

Dependencies (already in cherokee_venv):
- transformers 4.57.3
- torch 2.9.0+cu128
- huggingface-hub 0.36.0
- qwen-vl-utils 0.0.14

---

## Test Script

```bash
# Activate venv
source /home/dereadi/cherokee_venv/bin/activate

# Run test
python3 /ganuda/models/fara-7b/test_fara.py
```

Expected output:
```
============================================================
FARA-7B Test - Cherokee AI Federation
============================================================

GPU Available: True
GPU Name: NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition
GPU Memory: 102.0 GB

Loading model from /ganuda/models/fara-7b...
Processor loaded in 0.4s
Model loaded in 2.2s

Model dtype: torch.bfloat16
Device: cuda:0
GPU Memory Used: 16.6 GB

============================================================
SUCCESS: FARA-7B loaded and ready!
============================================================
```

---

## Basic Usage

**IMPORTANT:** FARA-7B is based on the Qwen2.5-VL architecture (vision-language model).
Use `Qwen2_5_VLForConditionalGeneration`, NOT `AutoModelForCausalLM`.

```python
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

MODEL_PATH = '/ganuda/models/fara-7b'

# Load model - Use Qwen2_5_VLForConditionalGeneration for FARA
processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True
)

# Load screenshot
screenshot = Image.open('screenshot.png')

# Create prompt
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": screenshot},
            {"type": "text", "text": "Click the 'Events' tab"}
        ]
    }
]

# Generate action
text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=[text], images=[screenshot], return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
action = processor.decode(outputs[0], skip_special_tokens=True)
print(action)
```

---

## Action Types

FARA outputs structured actions:

| Action | Format | Example |
|--------|--------|---------|
| Click | `click(x, y)` | `click(450, 120)` |
| Type | `type("text")` | `type("search query")` |
| Scroll | `scroll(direction)` | `scroll(down)` |
| Navigate | `goto("url")` | `goto("http://...")` |
| Wait | `wait()` | Wait for page load |

---

## Critical Points

FARA automatically pauses before sensitive actions:
- Entering personal information
- Completing purchases
- Making calls / sending emails
- Submitting applications
- Signing into accounts

When detected, model outputs: `CRITICAL_POINT: <reason>`

IT Jr must implement user approval workflow before proceeding.

---

## IT Jr Mission: Integration Tasks

### IT Jr 2 (Frontend)
1. Add screenshot capture to SAG interface
2. Create action visualization overlay
3. Build Critical Point approval dialog

### IT Jr 1 (Backend)
1. Create `/api/fara/capture` endpoint
2. Create `/api/fara/execute` endpoint
3. Implement action executor (pyautogui or playwright)

### IT Jr 3 (Database)
1. Log all FARA actions to thermal memory
2. Track success/failure rates
3. Store Critical Point approvals

---

## Safety Guidelines

1. **Never bypass Critical Points** - always get user approval
2. **Log all actions** to thermal memory for audit
3. **Test in isolation** before connecting to real interfaces
4. **Rate limit** actions to prevent runaway automation

---

## References

- [Microsoft Research Blog](https://www.microsoft.com/en-us/research/blog/fara-7b-an-efficient-agentic-model-for-computer-use/)
- [Hugging Face Model](https://huggingface.co/microsoft/Fara-7B)
- [Azure AI Foundry Labs](https://labs.ai.azure.com/projects/fara-7b/)

---

## Download Status

To check download progress:
```bash
du -sh /ganuda/models/fara-7b/
ls -lh /ganuda/models/fara-7b/*.safetensors
```

Expected final size: ~15GB (4 safetensor shards)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
