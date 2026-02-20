# Jr Instruction: Ouro Looped LLM Benchmark on Redfin

**Task ID**: OURO-BENCH-001
**Priority**: P2 (Architecture Evaluation)
**Kanban**: #1764
**Assigned Specialist**: Gecko (Technical Integration)
**Estimated Hours**: 4-6h
**Related KB**: KB-OURO-LOOPED-LLM-FEDERATION-IMPACT-FEB11-2026

---

## Context

Ouro is a looped language model from ByteDance (arXiv:2510.25741) where the same transformer weights iterate 4x per token. The 2.6B model claims to match 7-8B standard models on reasoning benchmarks. We need to validate this claim against our actual council voting workload before any deployment decision.

**IMPORTANT**: vLLM does NOT support adaptive exit for Ouro. All benchmarks must use HuggingFace transformers directly. Requires `transformers < 4.56.0` (recommend 4.54.1).

---

## Step 1: Set Up Benchmark Environment

Create `/ganuda/benchmarks/ouro/setup.sh`

```text
#!/bin/bash
# Ouro Benchmark Setup
# Run on redfin as dereadi

cd /ganuda/benchmarks/ouro

python3 -m venv venv
source venv/bin/activate

pip install "transformers==4.54.1" torch accelerate sentencepiece
pip install huggingface_hub

# Download models (Apache 2.0)
huggingface-cli download ByteDance/Ouro-2.6B --local-dir ./models/Ouro-2.6B
huggingface-cli download ByteDance/Ouro-2.6B-Thinking --local-dir ./models/Ouro-2.6B-Thinking

echo "Setup complete. Models downloaded."
```

---

## Step 2: Create Benchmark Script

Create `/ganuda/benchmarks/ouro/benchmark_council.py`

```python
#!/usr/bin/env python3
"""
Ouro vs Qwen Benchmark — Council Voting Prompts

Tests Ouro-2.6B and Ouro-2.6B-Thinking against actual Cherokee AI
council voting prompts. Compares with Qwen2.5-72B via gateway API.

Measures: quality (human-rated), latency, VRAM usage, loop behavior.
"""

import os
import sys
import json
import time
import torch
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OuroBenchmark")

# Council-style test prompts (representative of actual workload)
COUNCIL_PROMPTS = [
    {
        "id": "security_review",
        "prompt": "As Crawdad (Security Specialist), evaluate the security implications of deploying a new UPS monitoring daemon that connects to a smart plug via local WiFi API. The daemon will have SSH access to all 6 federation nodes for graceful shutdown. What are the attack vectors and mitigations?",
        "category": "security"
    },
    {
        "id": "seven_gen",
        "prompt": "As Turtle (Seven Generations Wisdom), assess whether replacing a proven 72B language model with an experimental 2.6B looped model aligns with the principle of making decisions that benefit the next seven generations. Consider both the compute efficiency gains and the stability risks.",
        "category": "wisdom"
    },
    {
        "id": "technical_integration",
        "prompt": "As Gecko (Technical Integration), design the deployment architecture for adding a 1.4B reasoning co-processor alongside an existing 7B vision model on a 12GB GPU. Both models must serve inference simultaneously without OOM. Specify memory allocation, inference framework, and request routing.",
        "category": "technical"
    },
    {
        "id": "strategy_planning",
        "prompt": "As Raven (Strategic Planning), evaluate whether the Cherokee AI Federation should invest engineering resources in evaluating looped language models (Ouro architecture) now, or wait for the technology to mature. Consider: models are 1.4B-2.6B only, no quantized variants exist, training code is not public, but the architecture shows 2-3x parameter efficiency.",
        "category": "strategy"
    },
    {
        "id": "reasoning_math",
        "prompt": "A federation of 6 compute nodes consumes 1800W total. A solar battery has 3800Wh capacity. Grid power fails at 2:00 AM. At what time will the battery reach 20% capacity (requiring graceful shutdown)? Show your reasoning step by step.",
        "category": "reasoning"
    },
    {
        "id": "cultural_integration",
        "prompt": "As Spider (Cultural Integration), explain how the Cherokee concept of Gadugi (community working together) applies to a distributed AI system where multiple small models collaborate instead of relying on a single large model. How does this shift in architecture reflect indigenous values of distributed responsibility?",
        "category": "cultural"
    },
]


def load_ouro_model(model_path: str, ut_steps: int = 4):
    """Load Ouro model with configurable loop steps."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

    logger.info(f"Loading {model_path} with {ut_steps} recurrent steps...")
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.total_ut_steps = ut_steps

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        config=config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    # Report VRAM usage
    if torch.cuda.is_available():
        vram_mb = torch.cuda.memory_allocated() / 1024 / 1024
        logger.info(f"VRAM used: {vram_mb:.0f} MB")

    return model, tokenizer


def run_inference(model, tokenizer, prompt: str, max_tokens: int = 512) -> Dict:
    """Run inference and measure latency."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = inputs["input_ids"].shape[1]

    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            temperature=1.0,
        )
    elapsed = time.time() - start

    output_ids = outputs[0][input_len:]
    response = tokenizer.decode(output_ids, skip_special_tokens=True)
    tokens_generated = len(output_ids)

    return {
        "response": response,
        "latency_s": round(elapsed, 2),
        "tokens": tokens_generated,
        "tok_per_s": round(tokens_generated / elapsed, 1) if elapsed > 0 else 0,
        "vram_mb": round(torch.cuda.memory_allocated() / 1024 / 1024) if torch.cuda.is_available() else 0,
    }


def query_qwen_72b(prompt: str) -> Dict:
    """Query Qwen 72B via federation gateway for comparison."""
    import urllib.request
    url = "http://localhost:8080/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5",
    }
    payload = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers=headers)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        elapsed = time.time() - start
        response = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens", len(response.split()))
        return {
            "response": response,
            "latency_s": round(elapsed, 2),
            "tokens": tokens,
            "tok_per_s": round(tokens / elapsed, 1) if elapsed > 0 else 0,
            "vram_mb": 86000,  # Known from nvidia-smi
        }
    except Exception as e:
        logger.error(f"Qwen 72B query failed: {e}")
        return {"response": f"ERROR: {e}", "latency_s": 0, "tokens": 0, "tok_per_s": 0, "vram_mb": 0}


def main():
    results_dir = Path("/ganuda/benchmarks/ouro/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_results = {"timestamp": timestamp, "benchmarks": []}

    # Models to test
    models_to_test = [
        ("Ouro-2.6B", "./models/Ouro-2.6B", [1, 2, 4]),
        ("Ouro-2.6B-Thinking", "./models/Ouro-2.6B-Thinking", [1, 2, 4]),
    ]

    for model_name, model_path, loop_counts in models_to_test:
        for loops in loop_counts:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {model_name} with {loops} loops")
            logger.info(f"{'='*60}")

            model, tokenizer = load_ouro_model(model_path, ut_steps=loops)

            for prompt_data in COUNCIL_PROMPTS:
                logger.info(f"  Prompt: {prompt_data['id']}")
                result = run_inference(model, tokenizer, prompt_data["prompt"])
                all_results["benchmarks"].append({
                    "model": model_name,
                    "loops": loops,
                    "prompt_id": prompt_data["id"],
                    "category": prompt_data["category"],
                    **result,
                })

            # Free GPU memory
            del model
            torch.cuda.empty_cache()

    # Qwen 72B comparison
    logger.info(f"\n{'='*60}")
    logger.info("Testing Qwen2.5-72B via gateway")
    logger.info(f"{'='*60}")

    for prompt_data in COUNCIL_PROMPTS:
        logger.info(f"  Prompt: {prompt_data['id']}")
        result = query_qwen_72b(prompt_data["prompt"])
        all_results["benchmarks"].append({
            "model": "Qwen2.5-72B-Instruct-AWQ",
            "loops": 1,
            "prompt_id": prompt_data["id"],
            "category": prompt_data["category"],
            **result,
        })

    # Save results
    output_file = results_dir / f"benchmark_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"\nResults saved to {output_file}")

    # Print summary table
    print(f"\n{'Model':<30} {'Loops':<6} {'Avg tok/s':<10} {'Avg Latency':<12} {'VRAM MB':<10}")
    print("-" * 70)

    from collections import defaultdict
    summary = defaultdict(lambda: {"tok_s": [], "latency": [], "vram": 0})

    for b in all_results["benchmarks"]:
        key = f"{b['model']}|{b['loops']}"
        summary[key]["tok_s"].append(b["tok_per_s"])
        summary[key]["latency"].append(b["latency_s"])
        summary[key]["vram"] = b["vram_mb"]

    for key, vals in sorted(summary.items()):
        model, loops = key.split("|")
        avg_toks = sum(vals["tok_s"]) / len(vals["tok_s"])
        avg_lat = sum(vals["latency"]) / len(vals["latency"])
        print(f"{model:<30} {loops:<6} {avg_toks:<10.1f} {avg_lat:<12.1f}s {vals['vram']:<10}")


if __name__ == "__main__":
    main()
```

---

## Validation Checklist

- [ ] Virtual environment created at `/ganuda/benchmarks/ouro/venv`
- [ ] transformers==4.54.1 installed (NOT newer)
- [ ] Both Ouro models downloaded from HuggingFace
- [ ] Benchmark runs all 6 council prompts against both Ouro variants at 1, 2, and 4 loops
- [ ] Qwen 72B comparison via gateway API completes
- [ ] Results JSON saved with latency, token/s, VRAM, and response text
- [ ] Summary table printed to stdout

---

## Expected Outcome

This benchmark will tell us:
1. **Quality gap**: How much worse is Ouro-2.6B vs Qwen 72B on OUR prompts (not academic benchmarks)?
2. **Loop benefit**: Does 4 loops meaningfully outperform 1 loop on council-style reasoning?
3. **VRAM cost**: Exact memory footprint for co-hosting decisions
4. **Latency**: Whether loop overhead is acceptable for interactive use

If quality is within 70% of Qwen 72B on council prompts, Ouro is viable as a secondary/triage model on redfin or as primary on bluefin. If below 50%, we wait for larger looped models.

---

*For Seven Generations — measure before you move.*
