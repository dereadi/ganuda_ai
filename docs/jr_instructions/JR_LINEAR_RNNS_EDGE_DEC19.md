# Jr Instructions: Linear RNNs Sparse Edge Inference

**Priority**: 1 (Highest)
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED 84.5%
**Parallel With**: Multi-Agent Scaling Laws (P2)

---

## OBJECTIVE

Deploy sparse linear RNNs on Mac Studio (sasass) for sustained edge inference. Target: 2x less compute, 36% less memory. This implements Maximum Sustained Power principle.

---

### Task 1: Create Edge Inference Directory Structure

Create `/Users/Shared/ganuda/edge_inference/__init__.py`:

```python
"""
Cherokee AI Edge Inference Module
Linear RNNs with Sparsity for Mac Studio
For Seven Generations
"""

__version__ = '0.1.0'
```

---

### Task 2: Create Sparse Model Utilities

Create `/Users/Shared/ganuda/edge_inference/sparse_utils.py`:

```python
#!/usr/bin/env python3
"""
Sparsity utilities for edge inference
Cherokee AI Federation - MSP Aligned
"""

import torch
from torch.nn.utils import prune


def apply_unstructured_sparsity(model, sparsity_ratio=0.8):
    """
    Apply unstructured sparsity to linear layers.
    Target: 80% sparsity = 2x compute reduction
    """
    pruned_count = 0
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            prune.l1_unstructured(module, name='weight', amount=sparsity_ratio)
            prune.remove(module, 'weight')
            pruned_count += 1

    return model, pruned_count


def get_model_sparsity(model):
    """Calculate actual sparsity of model"""
    total_params = 0
    zero_params = 0

    for name, param in model.named_parameters():
        if 'weight' in name:
            total_params += param.numel()
            zero_params += (param == 0).sum().item()

    return zero_params / total_params if total_params > 0 else 0


def get_memory_footprint(model):
    """Get model memory footprint in MB"""
    param_size = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
    return (param_size + buffer_size) / (1024 * 1024)


def benchmark_inference(model, tokenizer, prompt, num_runs=50, device='mps'):
    """Benchmark inference speed on Apple Silicon"""
    import time

    inputs = tokenizer(prompt, return_tensors='pt').to(device)
    model = model.to(device)

    # Warmup
    for _ in range(5):
        with torch.no_grad():
            _ = model.generate(inputs.input_ids, max_new_tokens=10)

    # Benchmark
    if device == 'mps':
        torch.mps.synchronize()

    start = time.perf_counter()
    total_tokens = 0

    for _ in range(num_runs):
        with torch.no_grad():
            outputs = model.generate(inputs.input_ids, max_new_tokens=20)
            total_tokens += outputs.shape[1]

    if device == 'mps':
        torch.mps.synchronize()

    elapsed = time.perf_counter() - start
    tokens_per_sec = total_tokens / elapsed

    return {
        'tokens_per_second': tokens_per_sec,
        'total_time': elapsed,
        'total_tokens': total_tokens
    }
```

---

### Task 3: Create Edge Gateway Server

Create `/Users/Shared/ganuda/edge_inference/edge_gateway.py`:

```python
#!/usr/bin/env python3
"""
Edge Inference Gateway for Mac Studio
Cherokee AI Federation - Sustained Power Mode
"""

import os
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import psutil
from datetime import datetime

app = Flask(__name__)

# Global model reference
model = None
tokenizer = None
model_name = None
device = 'mps' if torch.backends.mps.is_available() else 'cpu'

# Configuration
MODEL_OPTIONS = {
    'small': 'microsoft/phi-2',  # 2.7B - good for edge
    'tiny': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
}


def load_model(size='tiny'):
    """Load model with optional sparsity"""
    global model, tokenizer, model_name

    model_id = MODEL_OPTIONS.get(size, MODEL_OPTIONS['tiny'])
    print(f"Loading {model_id} on {device}...")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map=device
    )

    model_name = model_id
    print(f"Model loaded: {model_name}")


@app.route('/v1/edge/completions', methods=['POST'])
def edge_completion():
    """Edge inference endpoint"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503

    data = request.json
    prompt = data.get('prompt', '')
    max_tokens = min(data.get('max_tokens', 100), 200)  # Cap for edge

    try:
        inputs = tokenizer(prompt, return_tensors='pt').to(device)

        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated = response[len(prompt):]

        return jsonify({
            'response': generated,
            'model': model_name,
            'node': os.uname().nodename,
            'device': device,
            'tokens_generated': len(outputs[0]) - len(inputs.input_ids[0]),
            'mode': 'sustained'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/v1/edge/health', methods=['GET'])
def edge_health():
    """Health check with MSP metrics"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)

    return jsonify({
        'status': 'healthy' if model else 'no_model',
        'node': os.uname().nodename,
        'device': device,
        'model': model_name,
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'cpu_percent': cpu,
        'msp_mode': 'sustained',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/v1/edge/models', methods=['GET'])
def list_models():
    """List available edge models"""
    return jsonify({
        'available': MODEL_OPTIONS,
        'loaded': model_name,
        'device': device
    })


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='tiny', choices=['tiny', 'small'])
    parser.add_argument('--port', default=8081, type=int)
    args = parser.parse_args()

    load_model(args.model)
    app.run(host='0.0.0.0', port=args.port)
```

---

### Task 4: Create Edge Startup Script

Create `/Users/Shared/ganuda/edge_inference/start_edge.sh`:

```bash
#!/bin/bash
# Start Edge Inference Gateway
# Cherokee AI Federation - Mac Studio

cd /Users/Shared/ganuda/edge_inference

# Create venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install torch torchvision torchaudio
    pip install transformers accelerate flask psutil
else
    source venv/bin/activate
fi

# Start gateway
echo "Starting Edge Gateway on port 8081..."
python3 edge_gateway.py --model tiny --port 8081
```

---

### Task 5: Test Edge Gateway

After creating files, test on sasass:

```bash
cd /Users/Shared/ganuda/edge_inference
chmod +x start_edge.sh
./start_edge.sh &

# Wait for startup
sleep 30

# Test health
curl http://localhost:8081/v1/edge/health

# Test inference
curl -X POST http://localhost:8081/v1/edge/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "The Cherokee AI Federation is", "max_tokens": 50}'
```

---

## SUCCESS CRITERIA

1. Edge gateway running on sasass port 8081
2. Health endpoint returns MSP metrics
3. Inference endpoint generates responses
4. Memory usage stable under 80%
5. Response time < 5 seconds for 50 tokens

---

## MSP METRICS TO TRACK

| Metric | Target |
|--------|--------|
| Memory usage | < 80% |
| CPU usage (sustained) | < 60% |
| Tokens/second | > 5 |
| Response latency | < 5s |

---

*For Seven Generations - Cherokee AI Federation*
