# JR Instruction: Multi-GPU Inference Setup (5070 + RTX 6000)
## Task ID: MULTI-GPU-001
## Priority: P2

---

## Objective

Link RTX 5070 (workstation) with RTX 6000 (redfin) for distributed inference, increasing total context window and throughput.

---

## Architecture Options

### Option A: Ray Cluster with vLLM (Recommended)

Run vLLM on both GPUs with Ray for distributed inference.

```
┌─────────────────┐     ┌─────────────────┐
│  Workstation    │     │    Redfin       │
│  RTX 5070       │────▶│  RTX 6000       │
│  vLLM worker    │     │  vLLM head      │
│  Port 8001      │     │  Port 8000      │
└─────────────────┘     └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
            Load Balancer
              Port 8080
```

### Option B: Separate Instances + Load Balancer

Simpler setup - run independent vLLM instances, use nginx/haproxy to balance.

---

## Implementation (Option B - Faster)

### Step 1: Setup vLLM on workstation (5070)

```bash
# On workstation with RTX 5070
pip install vllm

# Run vLLM with smaller model or same model
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --host 0.0.0.0 \
  --port 8001 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.9
```

### Step 2: Create load balancer config on redfin

Create `/ganuda/config/nginx-llm-balance.conf`:

```nginx
upstream llm_cluster {
    # RTX 6000 on redfin (primary - larger model)
    server 127.0.0.1:8000 weight=3;

    # RTX 5070 on workstation (secondary - smaller/faster)
    server WORKSTATION_IP:8001 weight=2;

    # Health checks
    keepalive 32;
}

server {
    listen 8080;

    location /v1/ {
        proxy_pass http://llm_cluster;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        return 200 'OK';
    }
}
```

### Step 3: Smart routing based on request size

Create `/ganuda/services/llm_router.py`:

```python
#!/usr/bin/env python3
"""
LLM Request Router - Route based on context size
Small requests → 5070 (faster)
Large requests → RTX 6000 (more context)
"""

from flask import Flask, request, jsonify
import requests
import tiktoken

app = Flask(__name__)

ENDPOINTS = {
    'small': 'http://WORKSTATION_IP:8001',  # RTX 5070 - 7B model
    'large': 'http://127.0.0.1:8000',        # RTX 6000 - 32B model
}

CONTEXT_THRESHOLD = 8000  # tokens

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(enc.encode(text))

@app.route('/v1/chat/completions', methods=['POST'])
def route_completion():
    data = request.json
    messages = data.get('messages', [])

    # Count total tokens
    total_tokens = sum(count_tokens(m.get('content', '')) for m in messages)

    # Route based on size
    if total_tokens < CONTEXT_THRESHOLD:
        endpoint = ENDPOINTS['small']
    else:
        endpoint = ENDPOINTS['large']

    # Forward request
    resp = requests.post(
        f"{endpoint}/v1/chat/completions",
        json=data,
        timeout=300
    )

    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

## Verification

```bash
# Test both endpoints
curl http://127.0.0.1:8000/health
curl http://WORKSTATION_IP:8001/health

# Test router
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## Benefits

1. **Increased throughput** - 2 GPUs processing in parallel
2. **Smart routing** - Small requests go to faster 7B model
3. **Failover** - If one GPU down, other handles requests
4. **Larger effective context** - Can route huge requests to RTX 6000

---

*Cherokee AI Federation - For Seven Generations*
