# Jr Task: Set Up T5 Edge Inference on greenfin

**Task ID:** task-t5-greenfin-001
**Priority:** P2
**Node:** greenfin (192.168.132.224)
**Created:** December 22, 2025
**Requested By:** TPM

---

## Discovery

greenfin has excellent hardware for T5 inference:

| Spec | Value |
|------|-------|
| CPU | AMD RYZEN AI MAX+ 395 (32 cores) |
| RAM | 124GB (102GB available) |
| GPU | Radeon 8060S (integrated, ROCm not detected) |
| OS | Ubuntu 24.04, Linux 6.14.0 |
| PyTorch | 2.8.0 (already installed) |
| Transformers | 4.57.1 (already installed) |

### Performance Test Results

| Model | Inference Time | Notes |
|-------|---------------|-------|
| T5-small | **156ms** | Faster than sasass (300-400ms) |
| T5-base | 444-1084ms | Depends on task complexity |

---

## Current State

T5 works out of the box on greenfin using system Python:
```bash
python3 -c "
from transformers import T5ForConditionalGeneration, T5Tokenizer
model = T5ForConditionalGeneration.from_pretrained('t5-small')
tokenizer = T5Tokenizer.from_pretrained('t5-small', legacy=True)
# Works!
"
```

---

## Setup Tasks

### 1. Create Dedicated Models Directory

```bash
mkdir -p /ganuda/models/t5
cd /ganuda/models/t5
```

### 2. Download Models for Offline Use

```bash
python3 -c "
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Download and cache T5-small
print('Downloading T5-small...')
T5ForConditionalGeneration.from_pretrained('t5-small', cache_dir='/ganuda/models/t5/cache')
T5Tokenizer.from_pretrained('t5-small', cache_dir='/ganuda/models/t5/cache', legacy=True)

# Download and cache T5-base
print('Downloading T5-base...')
T5ForConditionalGeneration.from_pretrained('t5-base', cache_dir='/ganuda/models/t5/cache')
T5Tokenizer.from_pretrained('t5-base', cache_dir='/ganuda/models/t5/cache', legacy=True)

print('Models cached for offline use!')
"
```

### 3. Create T5 Inference Service

Create `/ganuda/services/t5_inference/t5_service.py`:

```python
#!/usr/bin/env python3
"""
T5 Inference Service for greenfin
Cherokee AI Federation - Edge Inference Node

Provides REST API for T5 tasks:
- Translation
- Summarization
- Question Answering
"""

from flask import Flask, request, jsonify
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('T5Service')

# Load models at startup
MODEL_CACHE = '/ganuda/models/t5/cache'
models = {}

def load_model(model_name='t5-small'):
    """Load T5 model if not already loaded"""
    if model_name not in models:
        logger.info(f'Loading {model_name}...')
        models[model_name] = {
            'model': T5ForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE,
                torch_dtype=torch.float32
            ),
            'tokenizer': T5Tokenizer.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE,
                legacy=True
            )
        }
        logger.info(f'{model_name} loaded!')
    return models[model_name]


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'node': 'greenfin',
        'models_loaded': list(models.keys()),
        'service': 't5-inference'
    })


@app.route('/v1/t5/generate', methods=['POST'])
def generate():
    """
    Generate text using T5

    POST /v1/t5/generate
    {
        "prompt": "translate English to German: Hello world",
        "model": "t5-small",  # or "t5-base"
        "max_length": 100
    }
    """
    data = request.json
    prompt = data.get('prompt', '')
    model_name = data.get('model', 't5-small')
    max_length = data.get('max_length', 100)

    if not prompt:
        return jsonify({'error': 'prompt required'}), 400

    try:
        m = load_model(model_name)

        start = time.time()
        inputs = m['tokenizer'](prompt, return_tensors='pt', max_length=512, truncation=True)
        outputs = m['model'].generate(**inputs, max_length=max_length)
        result = m['tokenizer'].decode(outputs[0], skip_special_tokens=True)
        inference_ms = (time.time() - start) * 1000

        return jsonify({
            'result': result,
            'model': model_name,
            'inference_ms': round(inference_ms, 1),
            'node': 'greenfin'
        })
    except Exception as e:
        logger.error(f'Generation error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/v1/t5/translate', methods=['POST'])
def translate():
    """
    Translate text

    POST /v1/t5/translate
    {
        "text": "Hello world",
        "source": "English",
        "target": "German"
    }
    """
    data = request.json
    text = data.get('text', '')
    source = data.get('source', 'English')
    target = data.get('target', 'German')
    model_name = data.get('model', 't5-small')

    prompt = f"translate {source} to {target}: {text}"

    m = load_model(model_name)
    inputs = m['tokenizer'](prompt, return_tensors='pt', max_length=512, truncation=True)

    start = time.time()
    outputs = m['model'].generate(**inputs, max_length=200)
    result = m['tokenizer'].decode(outputs[0], skip_special_tokens=True)

    return jsonify({
        'translation': result,
        'source_lang': source,
        'target_lang': target,
        'inference_ms': round((time.time() - start) * 1000, 1)
    })


@app.route('/v1/t5/summarize', methods=['POST'])
def summarize():
    """
    Summarize text

    POST /v1/t5/summarize
    {
        "text": "Long text to summarize...",
        "model": "t5-base"
    }
    """
    data = request.json
    text = data.get('text', '')
    model_name = data.get('model', 't5-base')  # base better for summarization

    prompt = f"summarize: {text}"

    m = load_model(model_name)
    inputs = m['tokenizer'](prompt, return_tensors='pt', max_length=512, truncation=True)

    start = time.time()
    outputs = m['model'].generate(**inputs, max_length=150)
    result = m['tokenizer'].decode(outputs[0], skip_special_tokens=True)

    return jsonify({
        'summary': result,
        'inference_ms': round((time.time() - start) * 1000, 1)
    })


if __name__ == '__main__':
    # Preload t5-small
    load_model('t5-small')

    print("=" * 50)
    print("T5 Inference Service - greenfin")
    print("Cherokee AI Federation")
    print("=" * 50)

    app.run(host='0.0.0.0', port=8090, threaded=True)
```

### 4. Create Startup Script

Create `/ganuda/services/t5_inference/start_t5.sh`:

```bash
#!/bin/bash
# T5 Inference Service Startup
# greenfin - Cherokee AI Federation

cd /ganuda/services/t5_inference

# Kill existing
pkill -f t5_service.py 2>/dev/null
sleep 2

echo "[$(date)] Starting T5 Inference Service..."
nohup python3 t5_service.py >> /ganuda/logs/t5_service.log 2>&1 &

PID=$!
echo $PID > /ganuda/services/t5_inference/t5_service.pid
echo "[$(date)] T5 Service started with PID $PID on port 8090"
```

```bash
chmod +x /ganuda/services/t5_inference/start_t5.sh
mkdir -p /ganuda/logs
```

### 5. Create systemd Service (Optional)

Create `/etc/systemd/system/t5-inference.service`:

```ini
[Unit]
Description=T5 Inference Service
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/t5_inference
ExecStart=/usr/bin/python3 /ganuda/services/t5_inference/t5_service.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable t5-inference
sudo systemctl start t5-inference
```

---

## Integration with LLM Gateway

Update redfin's LLM Gateway to route T5 requests to greenfin:

```python
# In gateway.py, add T5 routing
T5_ENDPOINT = "http://192.168.132.224:8090"

@app.route('/v1/t5/<path:subpath>', methods=['POST'])
def proxy_t5(subpath):
    """Proxy T5 requests to greenfin"""
    response = requests.post(
        f"{T5_ENDPOINT}/v1/t5/{subpath}",
        json=request.json,
        timeout=60
    )
    return jsonify(response.json())
```

---

## Testing

### Direct Test
```bash
curl -X POST http://192.168.132.224:8090/v1/t5/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "I fight for the users", "target": "German"}'
```

### Via Gateway (after integration)
```bash
curl -X POST http://192.168.132.223:8080/v1/t5/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "I fight for the users", "target": "German"}'
```

---

## ROCm GPU Investigation (Future)

The Radeon 8060S is detected but ROCm doesn't see it:
```
c5:00.0 Display controller: AMD/ATI Device 1586
```

To investigate:
```bash
# Check if ROCm supports this GPU
rocminfo 2>/dev/null || echo "rocminfo not available"
/opt/rocm/bin/rocm-smi 2>/dev/null || echo "rocm-smi not available"
```

The device ID `1586` may need newer ROCm drivers. For now, CPU inference is fast enough.

---

## Success Criteria

1. ✅ T5-small loads and runs (verified)
2. ✅ T5-base loads and runs (verified)
3. ⬜ T5 service running on port 8090
4. ⬜ Health endpoint responds
5. ⬜ Translation endpoint works
6. ⬜ Summarization endpoint works
7. ⬜ Gateway integration (optional)

---

## Performance Comparison

| Node | Hardware | T5-small | T5-base | Notes |
|------|----------|----------|---------|-------|
| greenfin | AMD Ryzen AI MAX+ 395 | **156ms** | 444-1084ms | Fastest CPU |
| sasass | Apple M1 Max | 300-400ms | ~800ms | PyTorch 2.9.1 |
| redfin | GPU (Blackwell) | N/A | N/A | Reserved for Nemotron |

greenfin is the optimal T5 edge inference node.

---

*For Seven Generations - Cherokee AI Federation*
