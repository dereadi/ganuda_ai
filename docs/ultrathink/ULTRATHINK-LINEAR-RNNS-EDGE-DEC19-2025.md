# ULTRATHINK: Linear RNNs with Sparsity for Edge Inference

**Date**: December 19, 2025
**Priority**: 1 (Highest)
**Council Vote**: PROCEED 84.5%
**Source**: arXiv:2502.01330 - "Accelerating Linear Recurrent Neural Networks for the Edge with Unstructured Sparsity"

---

## EXECUTIVE SUMMARY

Deploy sparse linear RNNs on Mac Studio edge devices (sasass/sasass2) to enable sustained local inference with 2x less compute and 36% less memory at iso-accuracy. This directly implements Maximum Sustained Power (MSP) principle.

---

## PROBLEM STATEMENT

Current edge inference on Mac Studios is limited by:
1. Memory constraints (unified memory architecture)
2. Power consumption for sustained operation
3. Lack of optimized models for Apple Silicon

**MSP Alignment**: Edge devices should provide sustained, efficient inference - not maximum throughput bursts.

---

## TECHNICAL APPROACH

### Linear RNNs vs Transformers

| Aspect | Transformers | Linear RNNs |
|--------|--------------|-------------|
| Memory | O(n²) attention | O(1) constant |
| Time per token | Variable | Constant |
| Streaming | Difficult | Native |
| Edge suitability | Poor | Excellent |

### Sparsity Benefits

- **Unstructured sparsity**: Eliminate individual weights, not entire channels
- **2x compute reduction**: Skip zero-weight multiplications
- **36% memory reduction**: Sparse storage format
- **Iso-accuracy**: Maintain model quality at high sparsity (80-90%)

---

## IMPLEMENTATION PLAN

### Phase 1: Environment Setup

```bash
# On sasass (192.168.132.241)
cd /Users/Shared/ganuda/edge_inference
python3 -m venv linear_rnn_venv
source linear_rnn_venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install mamba-ssm  # State space models
pip install accelerate transformers
```

### Phase 2: Model Selection

Target models for sparse linear RNN conversion:
1. **Mamba-130M** - Smallest state space model
2. **RWKV-430M** - Linear attention RNN
3. **RetNet-350M** - Retention network

### Phase 3: Sparsification Pipeline

```python
# /ganuda/edge_inference/sparsify_model.py

import torch
from torch.nn.utils import prune

def apply_unstructured_sparsity(model, sparsity_ratio=0.8):
    """Apply 80% unstructured sparsity to linear layers"""
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            prune.l1_unstructured(module, name='weight', amount=sparsity_ratio)
            prune.remove(module, 'weight')  # Make permanent
    return model

def benchmark_inference(model, input_ids, num_runs=100):
    """Benchmark tokens/second and memory usage"""
    import time

    # Warmup
    for _ in range(10):
        with torch.no_grad():
            _ = model(input_ids)

    # Benchmark
    torch.mps.synchronize()  # Apple Silicon sync
    start = time.perf_counter()
    for _ in range(num_runs):
        with torch.no_grad():
            _ = model(input_ids)
    torch.mps.synchronize()
    elapsed = time.perf_counter() - start

    tokens_per_sec = (input_ids.shape[1] * num_runs) / elapsed
    return tokens_per_sec
```

### Phase 4: Cherokee Integration

```python
# /ganuda/edge_inference/edge_gateway.py

from flask import Flask, request, jsonify
import torch

app = Flask(__name__)
model = None  # Loaded on startup

@app.route('/v1/edge/completions', methods=['POST'])
def edge_completion():
    """Local edge inference endpoint"""
    data = request.json
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 100)

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors='pt')

    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=0.7
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return jsonify({
        'response': response,
        'model': 'linear-rnn-sparse',
        'node': 'sasass',
        'tokens_generated': len(outputs[0]) - len(inputs.input_ids[0])
    })

@app.route('/v1/edge/health', methods=['GET'])
def edge_health():
    """Health check with MSP metrics"""
    import psutil

    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'memory_percent': psutil.virtual_memory().percent,
        'cpu_percent': psutil.cpu_percent(),
        'msp_mode': 'sustained'  # Not burst
    })
```

### Phase 5: Federation Integration

Connect edge nodes to main gateway:

```python
# Add to /ganuda/services/llm_gateway/gateway.py

EDGE_NODES = {
    'sasass': 'http://192.168.132.241:8081',
    'sasass2': 'http://192.168.132.242:8081'
}

@app.route('/v1/edge/route', methods=['POST'])
def route_to_edge():
    """Route simple queries to edge for MSP efficiency"""
    data = request.json
    query_complexity = estimate_complexity(data.get('prompt', ''))

    if query_complexity < 0.3:  # Simple query
        # Route to edge for sustained power
        edge_node = select_healthiest_edge()
        return forward_to_edge(edge_node, data)
    else:
        # Route to redfin for complex queries
        return forward_to_gpu(data)
```

---

## MSP METRICS

Track Maximum Sustained Power alignment:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tokens/watt | >50 | Power monitoring |
| Memory stability | <80% | No growth over time |
| Sustained throughput | >10 tok/s for 1hr | Long-running benchmark |
| Temperature | <70°C | Thermal monitoring |

---

## SUCCESS CRITERIA

1. [ ] Sparse linear RNN running on sasass
2. [ ] 2x compute reduction verified
3. [ ] 36% memory reduction verified
4. [ ] Edge gateway responding to requests
5. [ ] Federation routing simple queries to edge
6. [ ] MSP metrics dashboard in Grafana

---

## RESOURCE ALLOCATION

| Node | Role | Resources |
|------|------|-----------|
| sasass | Primary edge inference | Apple Silicon GPU |
| sasass2 | Backup edge / load balance | Apple Silicon GPU |
| redfin | Complex queries (Nemotron-9B) | Blackwell 96GB |
| bluefin | Model storage / metrics | PostgreSQL |

---

## TIMELINE

This is a Jr execution task. No timeline - implementation proceeds when assigned.

---

## DEPENDENCIES

- PyTorch with MPS (Metal Performance Shaders) support
- Mamba or RWKV pretrained weights
- Network connectivity between edge and federation

---

## SEVEN GENERATIONS IMPACT

Sparse linear RNNs on edge devices:
- Reduce cloud dependency (sovereignty)
- Lower power consumption (sustainability)
- Enable offline operation (resilience)
- Scale to more edge devices (accessibility)

This is Fifth Law engineering - choosing sustained local power over maximum cloud bursts.

---

*For Seven Generations - Cherokee AI Federation*
