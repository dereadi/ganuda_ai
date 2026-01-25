# Jr Task: Implement MoBiLE MoE Inference for Mac Studios

**Task ID:** task-impl-mobile-001
**Priority:** P1 (Phase 3.1 - Parallel Track C)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** arXiv:2510.12357 - MoBiLE: Efficient MoE Inference on Consumer GPU

---

## Overview

Implement MoBiLE (Mixture of Big Little Experts) inference optimization for our Mac Studio nodes (sasass, sasass2). This enables efficient MoE model inference by using half the experts for most tokens and full experts only when needed, achieving 1.6-1.7x speedup.

**Target Nodes:** sasass (192.168.132.241), sasass2 (192.168.132.242)
**Hardware:** Mac Studio with Apple Silicon (M1/M2 Ultra, unified memory)

---

## Research Paper Summary

MoBiLE optimizes MoE inference on consumer hardware:
- **Big-Little Architecture:** K/2 experts for unimportant tokens, K experts for important ones
- **Importance Detection:** Logit confidence threshold (default γ=0.7)
- **Training-free Prefetching:** Uses router outputs to prefetch experts
- **Fallback Strategy:** Regenerates uncertain tokens with full expertise
- **Results:** 1.60x-1.72x speedup with negligible accuracy loss

---

## Implementation Tasks

### Task 1: Assess Mac Studio Hardware

First, document the hardware capabilities:

```bash
# Run on sasass and sasass2
#!/bin/bash
echo "=== Mac Studio Hardware Assessment ==="
echo "Hostname: $(hostname)"
echo "Chip: $(sysctl -n machdep.cpu.brand_string)"
echo "Cores: $(sysctl -n hw.ncpu)"
echo "Memory: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
echo "GPU Cores: $(system_profiler SPDisplaysDataType | grep 'Total Number of Cores')"
echo "Metal Support: $(system_profiler SPDisplaysDataType | grep 'Metal Support')"

# Check MLX availability (Apple's ML framework)
python3 -c "import mlx; print(f'MLX version: {mlx.__version__}')" 2>/dev/null || echo "MLX not installed"

# Check PyTorch MPS
python3 -c "import torch; print(f'PyTorch MPS available: {torch.backends.mps.is_available()}')" 2>/dev/null
```

### Task 2: Install Dependencies

```bash
# Create virtual environment for MoBiLE
cd /Users/Shared/ganuda
python3 -m venv mobile_venv
source mobile_venv/bin/activate

# Install PyTorch with MPS support
pip install torch torchvision torchaudio

# Install MLX (Apple's ML framework - optimal for Apple Silicon)
pip install mlx mlx-lm

# Install transformers and MoE dependencies
pip install transformers accelerate sentencepiece
pip install safetensors huggingface_hub

# For OLMoE model support
pip install olmo
```

### Task 3: Implement MoBiLE Inference Engine

**File:** `/Users/Shared/ganuda/lib/mobile_inference.py`

```python
#!/usr/bin/env python3
"""
MoBiLE Inference Engine for Mac Studios
Based on arXiv:2510.12357 - Mixture of Big Little Experts

Optimized MoE inference for Apple Silicon with unified memory.
"""

import torch
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Try MLX first (best for Apple Silicon), fallback to PyTorch MPS
try:
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm import load, generate
    USE_MLX = True
except ImportError:
    USE_MLX = False
    import torch.nn.functional as F

# MoBiLE Configuration
@dataclass
class MoBiLEConfig:
    """Configuration for MoBiLE inference."""
    confidence_threshold: float = 0.7  # γ in paper
    num_experts_full: int = 8          # K experts for big model
    num_experts_little: int = 4        # K/2 experts for little model
    prefetch_enabled: bool = True
    fallback_enabled: bool = True
    max_batch_size: int = 32
    cache_experts: bool = True


class TokenImportance(Enum):
    """Token importance classification."""
    IMPORTANT = "important"      # Use full experts
    UNIMPORTANT = "unimportant"  # Use little experts


class MoBiLEInference:
    """
    MoBiLE: Mixture of Big Little Experts Inference.

    Reduces expert activation for unimportant tokens while
    maintaining accuracy for important ones.
    """

    def __init__(self, model_name: str, config: MoBiLEConfig = None):
        """
        Initialize MoBiLE inference engine.

        Args:
            model_name: HuggingFace model name (e.g., 'allenai/OLMoE-1B-7B')
            config: MoBiLE configuration
        """
        self.config = config or MoBiLEConfig()
        self.model_name = model_name
        self.device = self._get_device()
        self.model = None
        self.tokenizer = None
        self.expert_cache = {}
        self.stats = {
            'tokens_processed': 0,
            'important_tokens': 0,
            'unimportant_tokens': 0,
            'fallbacks': 0,
            'cache_hits': 0
        }

    def _get_device(self) -> str:
        """Determine best device for inference."""
        if USE_MLX:
            return "mlx"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def load_model(self):
        """Load MoE model with MoBiLE optimization."""
        print(f"Loading {self.model_name} on {self.device}...")

        if USE_MLX:
            self.model, self.tokenizer = load(self.model_name)
            print("Loaded with MLX (Apple Silicon optimized)")
        else:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto" if self.device == "mps" else None
            )
            if self.device == "mps":
                self.model = self.model.to("mps")
            print(f"Loaded with PyTorch on {self.device}")

    def classify_token_importance(self, logits: torch.Tensor) -> TokenImportance:
        """
        Classify token importance based on logit confidence.

        From paper: "compares the highest score of the output logits
        with a threshold γ"
        """
        if USE_MLX:
            max_logit = float(mx.max(logits))
            softmax_max = float(mx.max(mx.softmax(logits, axis=-1)))
        else:
            softmax_probs = F.softmax(logits, dim=-1)
            softmax_max = torch.max(softmax_probs).item()

        if softmax_max >= self.config.confidence_threshold:
            return TokenImportance.UNIMPORTANT  # Confident = little model OK
        else:
            return TokenImportance.IMPORTANT    # Uncertain = need full experts

    def select_experts(self, importance: TokenImportance,
                       router_output: torch.Tensor) -> List[int]:
        """
        Select which experts to activate based on importance.

        Important tokens: All K experts
        Unimportant tokens: Top K/2 experts
        """
        if USE_MLX:
            scores = router_output.tolist()
        else:
            scores = router_output.cpu().numpy().tolist()

        # Get indices sorted by score
        sorted_indices = sorted(range(len(scores)),
                               key=lambda i: scores[i], reverse=True)

        if importance == TokenImportance.IMPORTANT:
            # Full experts
            return sorted_indices[:self.config.num_experts_full]
        else:
            # Little experts (half)
            return sorted_indices[:self.config.num_experts_little]

    def prefetch_experts(self, next_router_output: torch.Tensor):
        """
        Prefetch experts for next token based on router prediction.

        Training-free prefetching from paper.
        """
        if not self.config.prefetch_enabled:
            return

        # Predict which experts will be needed
        predicted = self.select_experts(TokenImportance.UNIMPORTANT,
                                        next_router_output)

        # Cache expert weights (in unified memory, this is fast)
        for expert_id in predicted:
            if expert_id not in self.expert_cache:
                # Expert is already in unified memory on Mac
                self.expert_cache[expert_id] = True
                self.stats['cache_hits'] += 1

    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7) -> Tuple[str, Dict]:
        """
        Generate text with MoBiLE optimization.

        Returns (generated_text, statistics)
        """
        if self.model is None:
            self.load_model()

        start_time = time.time()

        if USE_MLX:
            # MLX generation (simpler, already optimized)
            output = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature
            )
            generated = output
        else:
            # PyTorch generation with MoBiLE logic
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device == "mps":
                inputs = {k: v.to("mps") for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        elapsed = time.time() - start_time
        tokens_generated = len(self.tokenizer.encode(generated)) - len(self.tokenizer.encode(prompt))

        stats = {
            'elapsed_seconds': elapsed,
            'tokens_generated': tokens_generated,
            'tokens_per_second': tokens_generated / elapsed if elapsed > 0 else 0,
            'device': self.device,
            'model': self.model_name,
            **self.stats
        }

        return generated, stats


class MoBiLEService:
    """
    Service wrapper for MoBiLE inference.

    Provides REST-like interface for federation use.
    """

    def __init__(self, model_name: str = "allenai/OLMoE-1B-7B"):
        """Initialize service with specified model."""
        self.engine = MoBiLEInference(model_name)
        self.ready = False

    def initialize(self):
        """Load model and prepare for inference."""
        self.engine.load_model()
        self.ready = True

    def infer(self, prompt: str, max_tokens: int = 256) -> Dict:
        """
        Run inference and return result.

        Returns dict with 'text' and 'stats' keys.
        """
        if not self.ready:
            self.initialize()

        text, stats = self.engine.generate(prompt, max_tokens)

        return {
            'text': text,
            'stats': stats,
            'status': 'success'
        }

    def health(self) -> Dict:
        """Return service health status."""
        return {
            'status': 'healthy' if self.ready else 'initializing',
            'device': self.engine.device,
            'model': self.engine.model_name,
            'mlx_available': USE_MLX
        }


# Simple HTTP server for service deployment
def run_server(port: int = 8090, model_name: str = "allenai/OLMoE-1B-7B"):
    """Run MoBiLE inference server."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json

    service = MoBiLEService(model_name)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(service.health()).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == '/generate':
                content_length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(content_length))

                result = service.infer(
                    body.get('prompt', ''),
                    body.get('max_tokens', 256)
                )

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            print(f"[MoBiLE] {args[0]}")

    print(f"Starting MoBiLE server on port {port}...")
    print(f"Model: {model_name}")
    print(f"MLX available: {USE_MLX}")

    # Pre-load model
    service.initialize()

    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Server ready at http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8090
        model = sys.argv[3] if len(sys.argv) > 3 else "allenai/OLMoE-1B-7B"
        run_server(port, model)
    else:
        # Quick test
        print("MoBiLE Inference Engine")
        print(f"Device: {'MLX' if USE_MLX else 'PyTorch MPS/CPU'}")

        engine = MoBiLEInference("allenai/OLMoE-1B-7B")
        text, stats = engine.generate("What is the Cherokee AI Federation?", max_tokens=100)

        print(f"\nGenerated: {text}")
        print(f"\nStats: {stats}")
```

### Task 4: Create Systemd/Launchd Service

**For macOS (launchd):**

**File:** `/Users/Shared/ganuda/services/com.cherokee.mobile.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.mobile</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/Shared/ganuda/mobile_venv/bin/python3</string>
        <string>/Users/Shared/ganuda/lib/mobile_inference.py</string>
        <string>serve</string>
        <string>8090</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/mobile.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/mobile.error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTORCH_MPS_HIGH_WATERMARK_RATIO</key>
        <string>0.0</string>
    </dict>
</dict>
</plist>
```

**Installation:**
```bash
# Copy to LaunchAgents
cp /Users/Shared/ganuda/services/com.cherokee.mobile.plist ~/Library/LaunchAgents/

# Load service
launchctl load ~/Library/LaunchAgents/com.cherokee.mobile.plist

# Check status
launchctl list | grep mobile
```

### Task 5: Federation Integration

Add MoBiLE endpoints to LLM Gateway routing:

```python
# In gateway.py, add to model routing
MOBILE_ENDPOINTS = {
    'sasass': 'http://192.168.132.241:8090',
    'sasass2': 'http://192.168.132.242:8090'
}

async def route_to_mobile(prompt: str, max_tokens: int = 256) -> dict:
    """Route request to MoBiLE inference on Mac Studios."""
    import aiohttp
    import random

    # Round-robin or load-based selection
    endpoint = random.choice(list(MOBILE_ENDPOINTS.values()))

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{endpoint}/generate",
            json={'prompt': prompt, 'max_tokens': max_tokens},
            timeout=60
        ) as resp:
            return await resp.json()
```

---

## Deployment Steps

1. Run hardware assessment on sasass and sasass2
2. Create virtual environment and install dependencies
3. Create `/Users/Shared/ganuda/lib/mobile_inference.py`
4. Download and test OLMoE model
5. Create and load launchd service
6. Test inference endpoint
7. Integrate with LLM Gateway routing

---

## Recommended Models for Mac Studio

| Model | Size | Performance | Notes |
|-------|------|-------------|-------|
| allenai/OLMoE-1B-7B | 7B params | Fast | Good balance |
| Qwen/Qwen1.5-MoE-A2.7B | 14.3B total | Medium | Higher quality |
| mistralai/Mixtral-8x7B | 46.7B total | Slower | Best quality |

Start with OLMoE-1B-7B for testing, scale up based on memory.

---

## Success Criteria

- [ ] Hardware assessment complete for both Mac Studios
- [ ] MLX or PyTorch MPS inference working
- [ ] MoBiLE service running on port 8090
- [ ] /health endpoint returns healthy status
- [ ] /generate endpoint produces coherent text
- [ ] Tokens/second > 20 on Mac Studio
- [ ] Gateway can route to MoBiLE endpoints

---

## Performance Targets

Based on paper results:
- **Baseline:** ~15-20 tok/s on consumer GPU
- **With MoBiLE:** ~25-35 tok/s (1.6-1.7x improvement)
- **Mac Studio (M2 Ultra):** Expect 30-50 tok/s with unified memory advantage

---

*For Seven Generations - Cherokee AI Federation*
