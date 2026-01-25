# Jr Instruction: MLX Migration for sasass Mac Studios

**Created:** December 24, 2025
**Priority:** HIGH VALUE, MEDIUM EFFORT
**Council Vote:** 2c12318a (85% confidence)
**Target Nodes:** sasass (192.168.132.241), sasass2 (192.168.132.242)

---

## Executive Summary

Migrate from current Ollama setup to native MLX framework on our Mac Studio cluster for 2-3x inference throughput improvement. Research (arXiv:2511.05502) shows MLX achieves 230 tok/s vs 9 tok/s for PyTorch MPS on Apple Silicon.

### Hardware Inventory

| Node | Chip | Memory | Disk Free | Current LLM |
|------|------|--------|-----------|-------------|
| sasass | M1 Max | 64GB | 474GB | Ollama |
| sasass2 | M1 Max | 64GB | TBD | T5 only |

### Expected Performance (M1 Max 64GB)

| Model | Quantization | Memory | Prompt tok/s | Gen tok/s |
|-------|--------------|--------|--------------|-----------|
| Qwen2.5-32B | 4-bit | ~18GB | ~60-80 | ~15-20 |
| Qwen2.5-32B | 8-bit | ~32GB | ~95 | ~10 |
| Qwen2.5-14B | 4-bit | ~8GB | ~100+ | ~30+ |
| Llama-3.2-8B | 4-bit | ~5GB | ~150+ | ~40+ |
| Qwen3-30B-MoE | 4-bit | ~18GB | ~80+ | ~25+ |

---

## Phase 1: Environment Setup

### 1.1 Create MLX Virtual Environment

```bash
# On sasass (192.168.132.241)
cd /Users/Shared/ganuda
python3 -m venv mlx_venv
source mlx_venv/bin/activate

# Install MLX and dependencies
pip install --upgrade pip
pip install mlx mlx-lm
pip install fastapi uvicorn httpx

# Verify installation
python3 -c "import mlx; print(f'MLX version: {mlx.__version__}')"
python3 -c "import mlx.core as mx; print(f'Default device: {mx.default_device()}')"
```

### 1.2 Verify GPU Access

```bash
# Should show 'gpu' or 'metal'
python3 << 'EOF'
import mlx.core as mx
print(f"Device: {mx.default_device()}")
print(f"Metal available: {mx.metal.is_available()}")

# Quick benchmark
import time
a = mx.random.normal((4096, 4096))
b = mx.random.normal((4096, 4096))
mx.eval(a)
mx.eval(b)

start = time.time()
for _ in range(10):
    c = mx.matmul(a, b)
    mx.eval(c)
elapsed = time.time() - start
print(f"10x matmul (4096x4096): {elapsed:.2f}s")
EOF
```

---

## Phase 2: Model Selection and Download

### 2.1 Recommended Models for 64GB M1 Max

**Primary Model (Council-equivalent):**
```bash
# Qwen2.5-32B-Instruct 4-bit - Best quality for 64GB
mlx_lm.download --model mlx-community/Qwen2.5-32B-Instruct-4bit
```

**Fast Model (Quick responses):**
```bash
# Qwen2.5-14B-Instruct 4-bit - Faster, still capable
mlx_lm.download --model mlx-community/Qwen2.5-14B-Instruct-4bit
```

**Coding Model:**
```bash
# Qwen2.5-Coder-32B 4-bit
mlx_lm.download --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit
```

**MoE Model (Efficient):**
```bash
# Qwen3-30B-A3B (3B active params) - Very efficient
mlx_lm.download --model mlx-community/Qwen3-30B-A3B-4bit
```

### 2.2 Test Model Loading

```bash
# Quick chat test
mlx_lm.chat --model mlx-community/Qwen2.5-32B-Instruct-4bit

# Generation test with metrics
mlx_lm.generate \
  --model mlx-community/Qwen2.5-32B-Instruct-4bit \
  --prompt "Explain the Seven Generations principle in Cherokee culture" \
  --max-tokens 200 \
  --verbose
```

---

## Phase 3: OpenAI-Compatible API Server

### 3.1 Create MLX API Server

Create `/Users/Shared/ganuda/services/mlx_server/mlx_api.py`:

```python
#!/usr/bin/env python3
"""
MLX OpenAI-Compatible API Server for Cherokee AI Federation
Provides /v1/chat/completions endpoint compatible with LLM Gateway
"""

import os
import sys
import time
import uuid
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# MLX imports
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.utils import TokenizerWrapper

# Configuration
MODEL_PATH = os.environ.get("MLX_MODEL", "mlx-community/Qwen2.5-32B-Instruct-4bit")
HOST = os.environ.get("MLX_HOST", "0.0.0.0")
PORT = int(os.environ.get("MLX_PORT", "8000"))
MAX_TOKENS = int(os.environ.get("MLX_MAX_TOKENS", "4096"))

app = FastAPI(
    title="MLX LLM Server",
    description="Cherokee AI Federation MLX Inference Server",
    version="1.0.0"
)

# Global model and tokenizer
model = None
tokenizer = None
model_name = None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "mlx-default"
    messages: List[Message]
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None


class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Usage


def load_model():
    """Load the MLX model and tokenizer."""
    global model, tokenizer, model_name

    print(f"Loading model: {MODEL_PATH}")
    start = time.time()
    model, tokenizer = load(MODEL_PATH)
    elapsed = time.time() - start
    model_name = MODEL_PATH.split("/")[-1]
    print(f"Model loaded in {elapsed:.1f}s")
    print(f"Device: {mx.default_device()}")


def format_chat_prompt(messages: List[Message]) -> str:
    """Format messages into a chat prompt for the model."""
    # Qwen chat format
    formatted = ""
    for msg in messages:
        if msg.role == "system":
            formatted += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
        elif msg.role == "user":
            formatted += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        elif msg.role == "assistant":
            formatted += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"

    # Add assistant prefix for generation
    formatted += "<|im_start|>assistant\n"
    return formatted


@app.on_event("startup")
async def startup():
    load_model()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": model_name,
        "device": str(mx.default_device()),
        "framework": "mlx"
    }


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": model_name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "cherokee-ai"
        }]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint."""
    global model, tokenizer

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Format prompt
    prompt = format_chat_prompt(request.messages)

    # Tokenize for counting
    prompt_tokens = tokenizer.encode(prompt)

    # Generate
    start = time.time()

    if request.stream:
        # Streaming response
        async def generate_stream():
            response_text = ""
            for token in generate(
                model, tokenizer, prompt,
                max_tokens=request.max_tokens or MAX_TOKENS,
                temp=request.temperature or 0.7,
                top_p=request.top_p or 0.9
            ):
                response_text += token
                chunk = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final chunk
            final = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )

    else:
        # Non-streaming response
        response_tokens = []
        for token in generate(
            model, tokenizer, prompt,
            max_tokens=request.max_tokens or MAX_TOKENS,
            temp=request.temperature or 0.7,
            top_p=request.top_p or 0.9
        ):
            response_tokens.append(token)

        response_text = "".join(response_tokens)
        elapsed = time.time() - start

        # Count tokens
        completion_tokens = len(tokenizer.encode(response_text))

        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=model_name,
            choices=[ChatChoice(
                index=0,
                message=Message(role="assistant", content=response_text),
                finish_reason="stop"
            )],
            usage=Usage(
                prompt_tokens=len(prompt_tokens),
                completion_tokens=completion_tokens,
                total_tokens=len(prompt_tokens) + completion_tokens
            )
        )


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
```

### 3.2 Create Systemd Service (for Linux-style management on macOS)

Create `/Users/Shared/ganuda/services/mlx_server/start_mlx.sh`:

```bash
#!/bin/bash
# MLX Server Startup Script

cd /Users/Shared/ganuda
source mlx_venv/bin/activate

export MLX_MODEL="mlx-community/Qwen2.5-32B-Instruct-4bit"
export MLX_HOST="0.0.0.0"
export MLX_PORT="8000"
export MLX_MAX_TOKENS="4096"

exec python3 /Users/Shared/ganuda/services/mlx_server/mlx_api.py
```

### 3.3 Create LaunchDaemon (macOS native)

Create `/Library/LaunchDaemons/com.cherokee.mlx-server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.mlx-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/Shared/ganuda/services/mlx_server/start_mlx.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/mlx-server.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/mlx-server.error.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda</string>
</dict>
</plist>
```

---

## Phase 4: Gateway Integration

### 4.1 Add MLX Backend to LLM Gateway

The existing gateway at redfin (192.168.132.223:8080) should be updated to route requests to MLX:

```python
# In gateway.py, add MLX backend configuration
MLX_BACKENDS = [
    {"host": "192.168.132.241", "port": 8000, "name": "sasass-mlx"},
    {"host": "192.168.132.242", "port": 8000, "name": "sasass2-mlx"},
]

# Add health check for MLX backends
async def check_mlx_health(backend):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://{backend['host']}:{backend['port']}/health")
            return resp.status_code == 200
    except:
        return False
```

### 4.2 Load Balancing Strategy

```python
# Round-robin with health checking
class MLXLoadBalancer:
    def __init__(self, backends):
        self.backends = backends
        self.current = 0
        self.healthy = set()

    async def get_backend(self):
        # Refresh health status
        for backend in self.backends:
            if await check_mlx_health(backend):
                self.healthy.add(backend['name'])
            else:
                self.healthy.discard(backend['name'])

        # Round-robin among healthy backends
        available = [b for b in self.backends if b['name'] in self.healthy]
        if not available:
            raise HTTPException(503, "No healthy MLX backends")

        backend = available[self.current % len(available)]
        self.current += 1
        return backend
```

---

## Phase 5: Testing and Validation

### 5.1 Performance Benchmarks

```bash
# Run on sasass after setup
cd /Users/Shared/ganuda
source mlx_venv/bin/activate

# Benchmark script
python3 << 'EOF'
import time
import httpx

BASE_URL = "http://localhost:8000"

# Warmup
resp = httpx.post(f"{BASE_URL}/v1/chat/completions", json={
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}, timeout=60)

# Benchmark
prompts = [
    "Explain quantum computing in simple terms",
    "Write a Python function to sort a list",
    "What is the Seven Generations principle?",
    "Describe the architecture of a neural network",
    "How does photosynthesis work?"
]

results = []
for prompt in prompts:
    start = time.time()
    resp = httpx.post(f"{BASE_URL}/v1/chat/completions", json={
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }, timeout=120)
    elapsed = time.time() - start

    data = resp.json()
    tokens = data["usage"]["completion_tokens"]
    tok_per_sec = tokens / elapsed

    results.append({
        "prompt": prompt[:40],
        "tokens": tokens,
        "time": elapsed,
        "tok/s": tok_per_sec
    })
    print(f"{prompt[:40]}... | {tokens} tokens | {elapsed:.1f}s | {tok_per_sec:.1f} tok/s")

avg_tps = sum(r["tok/s"] for r in results) / len(results)
print(f"\nAverage: {avg_tps:.1f} tok/s")
EOF
```

### 5.2 Security Sandbox Testing (per Crawdad)

```bash
# Create isolated test environment
mkdir -p /Users/Shared/ganuda/mlx_sandbox
cd /Users/Shared/ganuda/mlx_sandbox

# Test with non-production data only
# Monitor for any unexpected network activity
# Check file system access patterns
```

### 5.3 Comparison with Current vLLM

```bash
# Query both backends with same prompt
PROMPT="Explain the Cherokee AI Federation architecture"

# vLLM on redfin
time curl -s http://192.168.132.223:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}],\"max_tokens\":200}"

# MLX on sasass
time curl -s http://192.168.132.241:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}],\"max_tokens\":200}"
```

---

## Phase 6: Rollout Plan

### Week 1: Setup and Testing
- [ ] Create mlx_venv on sasass
- [ ] Install MLX and dependencies
- [ ] Download primary model (Qwen2.5-32B-4bit)
- [ ] Run benchmark tests
- [ ] Compare with vLLM baseline

### Week 2: API Server
- [ ] Deploy mlx_api.py
- [ ] Configure LaunchDaemon
- [ ] Test OpenAI compatibility
- [ ] Verify streaming works

### Week 3: Gateway Integration
- [ ] Add MLX backend to gateway
- [ ] Implement load balancing
- [ ] Test failover behavior
- [ ] Monitor performance metrics

### Week 4: Production Cutover
- [ ] Gradual traffic shift (10% -> 50% -> 100%)
- [ ] Monitor for regressions
- [ ] Document any issues
- [ ] Full production on MLX

---

## Rollback Plan

If issues arise:

```bash
# Stop MLX server
sudo launchctl unload /Library/LaunchDaemons/com.cherokee.mlx-server.plist

# Revert gateway to vLLM-only
# Update gateway.py to remove MLX backends

# Restart gateway
ssh dereadi@192.168.132.223 'sudo systemctl restart llm-gateway'
```

---

## Seven Generations Consideration

This migration embodies the principle that **substrate changes, wisdom endures**:

- The inference engine migrates from vLLM/CUDA to MLX/Metal
- The API interface remains OpenAI-compatible
- The thermal memories persist unchanged
- The Council voting logic continues unmodified
- The Jr agents connect to the same endpoints

**Modular architecture** (per Turtle's guidance): The MLX server is a drop-in replacement. We can migrate again when M5 or future chips arrive - the federation's knowledge and coordination patterns transcend any specific framework.

---

## Validation Checklist

- [ ] MLX venv created and activated
- [ ] Model downloaded and cached
- [ ] Health endpoint responding
- [ ] Chat completions working
- [ ] Streaming mode functional
- [ ] Performance meets 20+ tok/s target
- [ ] Gateway integration complete
- [ ] Load balancing verified
- [ ] Failover tested
- [ ] Production traffic migrated

---

*For Seven Generations - the substrate evolves, the wisdom endures.*

*Created: December 24, 2025*
*Council Vote: 2c12318a*
