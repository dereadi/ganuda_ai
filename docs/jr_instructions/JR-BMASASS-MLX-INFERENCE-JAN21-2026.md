# JR Instruction: Setup MLX on bmasass (M4 Max 128GB)
## Task ID: MLX-BMASASS-001
## Priority: P1
## Target: bmasass (TPM laptop, M4 Max, 128GB)

---

## Objective

Setup bmasass as primary MLX inference node. With 128GB unified memory on M4 Max, can run 70B+ parameter models - larger than redfin's vLLM setup.

---

## Capability Analysis

| Model | Parameters | Memory Needed | bmasass Capable |
|-------|------------|---------------|-----------------|
| Qwen2.5-7B | 7B | ~8GB | ✓ |
| Qwen2.5-32B | 32B | ~20GB | ✓ |
| Qwen2.5-72B | 72B | ~45GB | ✓ |
| Llama-3.1-70B | 70B | ~45GB | ✓ |
| **Qwen2.5-72B-Instruct** | 72B | ~45GB | **✓ RECOMMENDED** |

With 128GB, bmasass can run the **72B model** with room for KV cache and large contexts (100K+).

---

## Implementation

### Step 1: Install MLX and MLX-LM

```bash
# On bmasass
pip3 install mlx mlx-lm
```

### Step 2: Download Qwen2.5-72B-Instruct (4-bit quantized)

```bash
# This will take a while - ~40GB download
python3 -m mlx_lm.convert \
  --hf-path Qwen/Qwen2.5-72B-Instruct \
  --mlx-path ~/mlx-models/qwen2.5-72b-instruct-4bit \
  -q
```

### Step 3: Test inference

```bash
python3 -m mlx_lm.generate \
  --model ~/mlx-models/qwen2.5-72b-instruct-4bit \
  --prompt "You are a helpful assistant. Extract the file paths from this instruction: Create \`/ganuda/lib/test.py\` and modify \`/ganuda/lib/utils.py\`" \
  --max-tokens 100
```

### Step 4: Create OpenAI-compatible server

Create `/Users/Shared/ganuda/services/mlx_server.py`:

```python
#!/usr/bin/env python3
"""
MLX OpenAI-Compatible Server for bmasass
Cherokee AI Federation - M4 Max 128GB

Runs Qwen2.5-72B-Instruct for high-quality inference.
"""

from flask import Flask, request, jsonify
from mlx_lm import load, generate
import time

app = Flask(__name__)

MODEL_PATH = "~/mlx-models/qwen2.5-72b-instruct-4bit"
model, tokenizer = None, None

def get_model():
    global model, tokenizer
    if model is None:
        print(f"Loading {MODEL_PATH}...")
        model, tokenizer = load(MODEL_PATH)
        print("Model loaded!")
    return model, tokenizer

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL_PATH,
        "memory": "128GB",
        "chip": "M4 Max"
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat endpoint."""
    data = request.json
    messages = data.get('messages', [])
    max_tokens = data.get('max_tokens', 512)

    # Format messages into prompt
    prompt = ""
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == 'user':
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == 'assistant':
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"

    model, tokenizer = get_model()
    start = time.time()
    response = generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens)
    elapsed = time.time() - start

    return jsonify({
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "qwen2.5-72b-instruct",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response.split()),
            "total_tokens": len(prompt.split()) + len(response.split())
        },
        "_meta": {
            "inference_time_ms": int(elapsed * 1000),
            "device": "M4 Max 128GB"
        }
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    return jsonify({
        "data": [{
            "id": "qwen2.5-72b-instruct",
            "object": "model",
            "owned_by": "mlx-community"
        }]
    })

if __name__ == '__main__':
    print("Pre-loading model...")
    get_model()
    print("Starting MLX server on port 8000...")
    app.run(host='0.0.0.0', port=8000, threaded=True)
```

### Step 5: Create launchd service for auto-start

Create `~/Library/LaunchAgents/com.cherokee.mlx-server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.mlx-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/Shared/ganuda/services/mlx_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/mlx-server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/mlx-server.err</string>
</dict>
</plist>
```

Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.cherokee.mlx-server.plist
```

---

## Integration with Federation

Update LLM Gateway to use bmasass for large/complex tasks:

```python
# In gateway.py, add bmasass as endpoint
ENDPOINTS = {
    'redfin': 'http://192.168.132.220:8000',   # RTX 6000, 32B
    'bmasass': 'http://BMASASS_IP:8000',        # M4 Max, 72B
}

# Route complex tasks to bmasass
if task_complexity == 'high' or context_tokens > 32000:
    endpoint = ENDPOINTS['bmasass']
```

---

## Verification

```bash
# Health check
curl http://localhost:8000/health

# Test completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, what model are you?"}],
    "max_tokens": 100
  }'
```

---

## Performance Expectations

| Metric | Expected |
|--------|----------|
| Tokens/sec | 15-25 (72B on M4 Max) |
| Context window | 128K tokens |
| Memory usage | ~50-60GB |
| First token latency | 2-5 seconds |

---

*Cherokee AI Federation - For Seven Generations*
*bmasass: The Federation's Most Powerful Inference Node*
