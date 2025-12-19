# Jr Build Instructions: FARA Visual Assistant

## Priority: MEDIUM - Visual AI Capability on sasass

---

## Status: OPERATIONAL

FARA-7B is deployed on sasass (Mac Studio M2 Max) and successfully reading screen content.

**Current capabilities:**
- Screen capture and analysis via `fara_look.py`
- Resize large screenshots to fit MPS memory (max 1280 dimension)
- Answer questions about visible screen content
- Strips tool_call artifacts from responses

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    sasass (Mac Studio M2 Max)                    │
│                         192.168.132.241                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌────────────────────┐    ┌─────────────────────────────────┐ │
│   │  screencapture     │───▶│  PIL Image Processing           │ │
│   │  (macOS native)    │    │  - Resize to max 1280px         │ │
│   └────────────────────┘    │  - LANCZOS resampling           │ │
│                             └───────────────┬─────────────────┘ │
│                                             │                    │
│                                             ▼                    │
│   ┌─────────────────────────────────────────────────────────────┐│
│   │              FARA-7B (Qwen2.5-VL)                           ││
│   │              /Users/Shared/ganuda/models/fara-7b            ││
│   │                                                             ││
│   │   • 16GB model (4 shards)                                   ││
│   │   • float16 precision                                       ││
│   │   • MPS acceleration                                        ││
│   │   • ~18 second load time                                    ││
│   │   • Computer-use trained (GUI understanding)                ││
│   └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current Script

Location: `/Users/Shared/ganuda/scripts/fara_look.py`

**Usage:**
```bash
# Ask about current screen
python3 /Users/Shared/ganuda/scripts/fara_look.py "What do you see on this screen?"

# Ask specific question about visible content
python3 /Users/Shared/ganuda/scripts/fara_look.py "Read the text in the Chrome browser"

# Default question if no argument
python3 /Users/Shared/ganuda/scripts/fara_look.py
```

**Key parameters:**
- `MAX_DIMENSION = 1280` - Resize threshold to avoid MPS memory overflow
- `max_new_tokens = 500` - Response length limit

---

## Future Enhancements

### 1. Persistent Model Loading (Reduce Latency)

Current: Model loads fresh each invocation (~18 seconds)
Goal: Keep model warm in memory via background service

```python
# fara_service.py - Long-running service
from flask import Flask, request, jsonify
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

app = Flask(__name__)

# Load model once at startup
MODEL_PATH = "/Users/Shared/ganuda/models/fara-7b"
processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="mps",
    trust_remote_code=True
)

@app.route("/analyze", methods=["POST"])
def analyze():
    # Accept base64 image or file path
    # Return analysis
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
```

### 2. Region Capture

Capture specific screen regions instead of full screen:
```bash
# Capture specific window
screencapture -l <window_id> /tmp/window.png

# Capture region (interactive)
screencapture -i /tmp/region.png

# Capture coordinates
screencapture -R x,y,w,h /tmp/region.png
```

### 3. Integration with Telegram

Allow TPM to request screen analysis via telegram:
```
/look What's on my screen right now?
/look Read the error message in Terminal
```

### 4. Scheduled Screenshots

Periodic screen capture for monitoring:
```python
# Every 5 minutes, capture and summarize
# Store interesting observations to thermal memory
```

---

## Known Limitations

1. **Memory constraint**: 5120x1440 causes 41GB allocation error, hence resize
2. **Load time**: ~18 seconds cold start
3. **Single screen**: Only captures primary display currently
4. **No mouse interaction**: Read-only, FARA's tool_calls are stripped

---

## Dependencies (sasass)

```
torch==2.0+ (MPS support)
torchvision
transformers
accelerate
Pillow
```

Installed via: `pip3 install <package> --user`

---

## Testing

```bash
# Basic test
ssh dereadi@192.168.132.241 "python3 /Users/Shared/ganuda/scripts/fara_look.py"

# Specific question
ssh dereadi@192.168.132.241 "python3 /Users/Shared/ganuda/scripts/fara_look.py 'What applications are open?'"
```

---

*For Seven Generations*
