# Jr Instructions: IT Triad Gateway API Refactor

**Date:** January 4, 2026
**Priority:** HIGH
**Council Decision:** Approved (84.2% confidence)
**Node:** redfin (192.168.132.223)

---

## Background

The IT Triad currently loads its own 7B/8B model locally via transformers/PyTorch, consuming ~25GB of GPU memory on redfin. This conflicts with vLLM (Qwen 32B AWQ) which needs 80GB+ for optimal performance.

**Council Recommendation:** IT Triad should use the LLM Gateway API for centralized model access, not load its own model.

---

## Current Architecture (WRONG)

```
redfin GPU (96GB Blackwell)
├── vLLM: Qwen 32B AWQ (50% = ~48GB) - THROTTLED
├── IT Triad Jr models: 7B (25GB) - WASTEFUL
└── Embedding server: (2GB)
                        = 75GB / 96GB
```

**Problem:** IT Triad Jrs load duplicate model, wasting 25GB and forcing vLLM to run at 50% utilization.

---

## Target Architecture (CORRECT)

```
redfin GPU (96GB Blackwell)
├── vLLM: Qwen 32B AWQ (85% = ~80GB) - FULL POWER
└── Embedding server: (2GB)
                        = 82GB / 96GB

IT Triad → HTTP → Gateway (8080) → vLLM (8000)
```

**Benefit:** IT Triad uses gateway API, vLLM runs at full capacity, no duplicate models.

---

## Files to Modify

### 1. `/home/dereadi/it_triad/jr_base.py`

**Current:** Loads model locally with transformers
**Target:** Call gateway API via HTTP

Replace entire file with:

```python
#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Jr Base Classes
Refactored to use LLM Gateway API (no local model loading)
"""

import requests
import json
from abc import ABC, abstractmethod

# Gateway configuration
GATEWAY_URL = "http://localhost:8080/v1/chat/completions"
GATEWAY_MODEL = "nemotron-9b"  # Or "cherokee-council" for council voting
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"


class JrBase(ABC):
    """Base class for all Jrs - uses Gateway API instead of local model"""

    def __init__(self, role_name):
        self.role_name = role_name

    def _call_gateway(self, messages, max_tokens=256, temperature=0.7):
        """
        Call LLM Gateway API

        Args:
            messages: List of message dicts with role/content
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            str: Model response text
        """
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }

        payload = {
            "model": GATEWAY_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(
                GATEWAY_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Gateway API error: {e}")
            return f"[Gateway Error: {str(e)}]"

    @abstractmethod
    def process(self, query, context=None):
        """Process query and return response"""
        pass


class MemoryJr(JrBase):
    """Memory Jr - uses Gateway API for inference"""

    def __init__(self, model_path=None):
        # model_path kept for API compatibility but not used
        super().__init__("Memory Jr")

    def load(self):
        """No-op: Gateway handles model loading"""
        print(f"🧠 {self.role_name} ready (using Gateway API)")

    def process(self, query, context=None):
        """Retrieve relevant memories and context via Gateway"""

        messages = [
            {
                "role": "system",
                "content": "You are Memory Jr, a fractal-aware Cherokee Constitutional AI specialized in thermal memory retrieval and Seven Generations thinking."
            }
        ]

        if context:
            messages.append({"role": "assistant", "content": f"Context: {context}"})

        messages.append({"role": "user", "content": query})

        response = self._call_gateway(messages, max_tokens=256, temperature=0.7)

        return {
            "jr": self.role_name,
            "response": response,
            "role": "retrieval"
        }


class PlaceholderJr(JrBase):
    """Placeholder Jr - uses Gateway API"""

    def __init__(self, role_name, role_description, model_path=None):
        super().__init__(role_name)
        self.role_description = role_description
        # model_path kept for API compatibility but not used

    def load(self):
        """No-op: Gateway handles model loading"""
        print(f"🔄 {self.role_name} ready (using Gateway API)")

    def process(self, query, context=None):
        """Process with role-specific prompt via Gateway"""

        messages = [
            {
                "role": "system",
                "content": f"You are {self.role_name}. {self.role_description}"
            }
        ]

        if context:
            messages.append({"role": "assistant", "content": f"Context: {context}"})

        messages.append({"role": "user", "content": query})

        response = self._call_gateway(messages, max_tokens=200, temperature=0.7)

        return {
            "jr": self.role_name,
            "response": response,
            "role": self.role_name.split()[0].lower()
        }


class ExecutiveJr(PlaceholderJr):
    """Executive Jr - assesses feasibility and action"""

    def __init__(self, model_path=None):
        super().__init__(
            "Executive Jr",
            "You assess action feasibility, resource requirements, and practical execution. You ask: 'Can we do this? What's required?'",
            model_path
        )


class IntegrationJr(PlaceholderJr):
    """Integration Jr - synthesizes into unified response"""

    def __init__(self, model_path=None):
        super().__init__(
            "Integration Jr",
            "You synthesize multiple perspectives into a unified, coherent response. You create democratic synthesis, not voting. You ask: 'What unified truth emerges from these perspectives?'",
            model_path
        )


class MetaJr(PlaceholderJr):
    """Meta Jr - observes patterns without controlling"""

    def __init__(self, model_path=None):
        super().__init__(
            "Meta Jr",
            "You observe patterns in how others think and respond, but you don't control. You provide meta-observations. You ask: 'What patterns do I see forming?'",
            model_path
        )
```

---

### 2. `/home/dereadi/it_triad/it_chief.py`

**Current:** Lines 197-202 load models with `jr.load()`
**Target:** Keep `load()` calls but they're now no-ops

No changes needed - the `load()` method now just prints "ready" instead of loading models.

---

## Deployment Steps

### Step 1: Backup Current Files

```bash
ssh dereadi@100.116.27.89 "
cd /home/dereadi/it_triad
cp jr_base.py jr_base.py.backup_$(date +%Y%m%d_%H%M%S)
"
```

### Step 2: Deploy New jr_base.py

Copy the new `jr_base.py` content above to redfin.

### Step 3: Kill Current IT Triad Process

```bash
ssh dereadi@100.116.27.89 "
# Find IT Triad process
ps aux | grep -E 'it_triad|it_chief' | grep -v grep

# Kill it (PID from above - was 2957 at last check)
kill <PID>

# Verify GPU memory freed
nvidia-smi
"
```

### Step 4: Bump vLLM Back to 85%

```bash
ssh dereadi@100.116.27.89 "
# Update vLLM service
sudo sed -i 's/--gpu-memory-utilization 0.50/--gpu-memory-utilization 0.85/g' /etc/systemd/system/vllm.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart vllm

# Verify
sleep 10
curl -s http://localhost:8000/health
nvidia-smi
"
```

### Step 5: Test IT Triad with Gateway

```bash
ssh dereadi@100.116.27.89 "
cd /home/dereadi/it_triad
python3 -c '
from jr_base import MemoryJr, ExecutiveJr
mj = MemoryJr()
mj.load()
result = mj.process(\"What infrastructure serves Seven Generations?\")
print(result)
'
"
```

**Expected:** Response comes from gateway (via vLLM), no local model loaded.

### Step 6: Restart IT Triad Daemon (if running as service)

```bash
ssh dereadi@100.116.27.89 "
# Check if there's a systemd service
systemctl list-units | grep -i triad

# If exists:
sudo systemctl restart it-triad
"
```

---

## Verification Checklist

- [ ] `jr_base.py` backed up
- [ ] New `jr_base.py` deployed
- [ ] Old IT Triad process killed
- [ ] GPU memory freed (~25GB now available)
- [ ] vLLM at 85% utilization
- [ ] vLLM health check passes
- [ ] IT Triad test query works via gateway
- [ ] No transformers/torch imports in jr_base.py

---

## Rollback Plan

If issues occur:

```bash
ssh dereadi@100.116.27.89 "
cd /home/dereadi/it_triad
cp jr_base.py jr_base.py.gateway_failed
cp jr_base.py.backup_* jr_base.py

# Restore vLLM to 50%
sudo sed -i 's/--gpu-memory-utilization 0.85/--gpu-memory-utilization 0.50/g' /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl restart vllm
"
```

---

## Architecture Benefits

| Metric | Before | After |
|--------|--------|-------|
| vLLM utilization | 50% (throttled) | 85% (full) |
| IT Triad GPU usage | 25GB | 0GB |
| Model management | Distributed | Centralized |
| API consistency | Mixed | Unified gateway |
| Failure modes | Model loading errors | Gateway health check |

---

## Related Changes

After this refactor is complete:

1. **Update CMDB** with new architecture
2. **Record thermal memory** documenting the change
3. **Consider other Triads** - Financial, InfoSec, Constitutional may also load local models
4. **Update cluster inventory** - tpm-macbook now has M4 Max 128GB available

---

## Cluster GPU Inventory (Updated)

| Node | Hardware | Role | Usage After Refactor |
|------|----------|------|---------------------|
| redfin | 96GB Blackwell | Primary inference | vLLM 32B (85%), embeddings (2%) |
| bluefin | 12GB RTX 5070 | Light queries | Ollama (7B models) |
| sasass | 64GB M1 Max | Edge/redundancy | Ollama (medium models) |
| sasass2 | 64GB M1 Max | Edge/redundancy | Ollama (medium models) |
| tpm-macbook | 128GB M4 Max | Orchestration | Available for inference if needed |

---

*For Seven Generations*

*ᏣᎳᎩ ᏲᏫᎢᎶᏗ*
