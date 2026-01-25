# Jr Instruction: MiroThinker v1.5 A/B Test Infrastructure

**Date**: January 7, 2026
**Assigned To**: Software Engineer Jr, Performance Jr
**Priority**: Medium
**TPM**: Flying Squirrel
**Council Vote**: 84.3% confidence, REVIEW REQUIRED (5 concerns)

---

## Background

The Council recommends A/B testing MiroThinker-v1.5-30B against our current Qwen2.5-Coder-32B-AWQ before any model swap. TPM requires substantial metric improvement to justify a change.

### Model Comparison

| Attribute | Current (Qwen2.5-Coder-32B-AWQ) | Proposed (MiroThinker-v1.5-30B) |
|-----------|-------------------------------|--------------------------------|
| Parameters | 32B dense | 30B MoE (3B active) |
| Quantization | AWQ 4-bit | BF16 or GGUF Q8 |
| Context | 32K | 256K |
| Specialty | Code generation | Tool-calling agents |
| VRAM Est. | ~20GB | ~32GB (Q8) or ~62GB (BF16) |
| Tool Calls | Standard | Up to 400 per task |

---

## Phase 1: Model Download and Setup

### Step 1.1: Download MiroThinker GGUF

```bash
# On redfin as dereadi
mkdir -p /ganuda/models/mirothinker-v1.5-30b-gguf
cd /ganuda/models/mirothinker-v1.5-30b-gguf

# Download Q8_0 quantization (best quality/size balance)
huggingface-cli download mradermacher/MiroThinker-v1.5-30B-GGUF \
  --include "*Q8_0*" \
  --local-dir .

# Verify download
ls -lh *.gguf
```

### Step 1.2: Create Second vLLM Instance

Create systemd service for MiroThinker on port 8001:

```bash
# /etc/systemd/system/vllm-mirothinker.service
[Unit]
Description=vLLM MiroThinker v1.5 30B
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/ganuda/services/llm_gateway/venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model /ganuda/models/mirothinker-v1.5-30b-gguf/MiroThinker-v1.5-30B-Q8_0.gguf \
    --port 8001 \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.45 \
    --enable-reasoning
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note**: Using 45% GPU memory to allow both models to coexist. Adjust if needed.

### Step 1.3: Verify Both Models Running

```bash
# Check Qwen (port 8000)
curl -s http://localhost:8000/v1/models | jq '.data[0].id'

# Check MiroThinker (port 8001)
curl -s http://localhost:8001/v1/models | jq '.data[0].id'
```

---

## Phase 2: A/B Test Router

### Step 2.1: Create A/B Test Endpoint in Gateway

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
import random
import time
from datetime import datetime

# A/B Test Configuration
AB_TEST_CONFIG = {
    "enabled": True,
    "model_a": {
        "name": "qwen2.5-coder-32b-awq",
        "endpoint": "http://localhost:8000/v1/chat/completions"
    },
    "model_b": {
        "name": "mirothinker-v1.5-30b",
        "endpoint": "http://localhost:8001/v1/chat/completions"
    },
    "split_ratio": 0.5,  # 50/50 split
    "metrics_table": "ab_test_results"
}

@app.route('/v1/ab/chat/completions', methods=['POST'])
def ab_test_chat():
    """A/B test endpoint - routes to either model and logs metrics."""
    start_time = time.time()

    # Randomly select model based on split ratio
    use_model_b = random.random() < AB_TEST_CONFIG["split_ratio"]
    model_config = AB_TEST_CONFIG["model_b"] if use_model_b else AB_TEST_CONFIG["model_a"]

    # Forward request to selected model
    response = requests.post(
        model_config["endpoint"],
        json=request.json,
        headers={"Content-Type": "application/json"}
    )

    elapsed_ms = (time.time() - start_time) * 1000
    result = response.json()

    # Extract metrics
    metrics = {
        "model": model_config["name"],
        "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
        "latency_ms": elapsed_ms,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Log to database (async)
    log_ab_metrics(metrics)

    # Add model indicator to response for transparency
    result["ab_test_model"] = model_config["name"]

    return jsonify(result)

def log_ab_metrics(metrics):
    """Log A/B test metrics to PostgreSQL."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ab_test_results
            (model, prompt_tokens, completion_tokens, latency_ms, tested_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            metrics["model"],
            metrics["prompt_tokens"],
            metrics["completion_tokens"],
            metrics["latency_ms"],
            metrics["timestamp"]
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to log A/B metrics: {e}")
```

### Step 2.2: Create Metrics Table

On bluefin:

```sql
-- A/B Test Results Table
CREATE TABLE IF NOT EXISTS ab_test_results (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms FLOAT,
    tool_calls_count INTEGER DEFAULT 0,
    task_completed BOOLEAN DEFAULT NULL,
    quality_score FLOAT DEFAULT NULL,
    tested_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ab_test_model ON ab_test_results(model);
CREATE INDEX idx_ab_test_timestamp ON ab_test_results(tested_at);

-- View for quick comparison
CREATE OR REPLACE VIEW ab_test_summary AS
SELECT
    model,
    COUNT(*) as total_requests,
    AVG(latency_ms) as avg_latency_ms,
    AVG(completion_tokens) as avg_completion_tokens,
    AVG(completion_tokens / NULLIF(latency_ms / 1000, 0)) as tokens_per_sec,
    AVG(quality_score) as avg_quality,
    COUNT(CASE WHEN task_completed THEN 1 END)::float / COUNT(*) as completion_rate
FROM ab_test_results
GROUP BY model;
```

---

## Phase 3: Test Suite

### Step 3.1: Create Evaluation Tasks

Create `/ganuda/scripts/ab_test_tasks.json`:

```json
{
  "test_cases": [
    {
      "id": "code_gen_1",
      "category": "code_generation",
      "prompt": "Write a Python function that implements binary search on a sorted list. Include docstring and type hints.",
      "expected_elements": ["def", "binary", "int", "List", "->"]
    },
    {
      "id": "code_gen_2",
      "category": "code_generation",
      "prompt": "Write a PostgreSQL query to find the top 10 users by total order value, joining users and orders tables.",
      "expected_elements": ["SELECT", "JOIN", "ORDER BY", "LIMIT", "SUM"]
    },
    {
      "id": "tool_call_1",
      "category": "tool_calling",
      "prompt": "I need to check the weather in Seattle and then book a flight there for tomorrow. What tools would you call and in what order?",
      "expected_elements": ["weather", "flight", "search", "book"]
    },
    {
      "id": "reasoning_1",
      "category": "reasoning",
      "prompt": "A database has 1 million rows. Query A uses a full table scan. Query B uses an index but requires a join. Under what conditions would Query A be faster?",
      "expected_elements": ["selectivity", "index", "scan", "rows"]
    },
    {
      "id": "council_sim_1",
      "category": "council_voting",
      "prompt": "As a security specialist, evaluate this proposal: 'We should expose our internal API directly to the internet to reduce latency.' What concerns would you raise?",
      "expected_elements": ["security", "authentication", "firewall", "risk"]
    }
  ]
}
```

### Step 3.2: Create Test Runner

Create `/ganuda/scripts/run_ab_test.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - A/B Test Runner
Compares Qwen2.5-Coder-32B-AWQ vs MiroThinker-v1.5-30B
"""

import json
import time
import requests
from datetime import datetime

MODELS = {
    "qwen": "http://localhost:8000/v1/chat/completions",
    "mirothinker": "http://localhost:8001/v1/chat/completions"
}

def run_test(model_name, endpoint, prompt, max_tokens=1024):
    """Run a single test against a model."""
    start = time.time()

    try:
        response = requests.post(endpoint, json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }, timeout=120)

        elapsed = (time.time() - start) * 1000
        result = response.json()

        return {
            "success": True,
            "latency_ms": elapsed,
            "content": result["choices"][0]["message"]["content"],
            "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": result.get("usage", {}).get("completion_tokens", 0)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def score_response(response, expected_elements):
    """Simple scoring based on expected elements present."""
    if not response.get("success"):
        return 0.0

    content = response["content"].lower()
    found = sum(1 for elem in expected_elements if elem.lower() in content)
    return found / len(expected_elements)

def main():
    # Load test cases
    with open("/ganuda/scripts/ab_test_tasks.json") as f:
        test_data = json.load(f)

    results = []

    for test in test_data["test_cases"]:
        print(f"\n{'='*60}")
        print(f"Test: {test['id']} ({test['category']})")
        print(f"{'='*60}")

        for model_name, endpoint in MODELS.items():
            print(f"\nRunning {model_name}...")
            response = run_test(model_name, endpoint, test["prompt"])

            if response["success"]:
                score = score_response(response, test["expected_elements"])
                tokens_per_sec = response["completion_tokens"] / (response["latency_ms"] / 1000)

                print(f"  Latency: {response['latency_ms']:.0f}ms")
                print(f"  Tokens: {response['completion_tokens']}")
                print(f"  Speed: {tokens_per_sec:.1f} tok/s")
                print(f"  Quality Score: {score:.2f}")

                results.append({
                    "test_id": test["id"],
                    "category": test["category"],
                    "model": model_name,
                    "latency_ms": response["latency_ms"],
                    "completion_tokens": response["completion_tokens"],
                    "tokens_per_sec": tokens_per_sec,
                    "quality_score": score
                })
            else:
                print(f"  FAILED: {response.get('error')}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for model in MODELS.keys():
        model_results = [r for r in results if r["model"] == model]
        if model_results:
            avg_latency = sum(r["latency_ms"] for r in model_results) / len(model_results)
            avg_speed = sum(r["tokens_per_sec"] for r in model_results) / len(model_results)
            avg_quality = sum(r["quality_score"] for r in model_results) / len(model_results)

            print(f"\n{model.upper()}:")
            print(f"  Avg Latency: {avg_latency:.0f}ms")
            print(f"  Avg Speed: {avg_speed:.1f} tok/s")
            print(f"  Avg Quality: {avg_quality:.2%}")

    # Save results
    with open(f"/ganuda/logs/ab_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to /ganuda/logs/")

if __name__ == "__main__":
    main()
```

---

## Phase 4: Success Criteria

### Metrics to Evaluate

| Metric | Current Baseline | Target for Swap |
|--------|-----------------|-----------------|
| Tokens/sec | ~27 tok/s | Must be >= 25 tok/s |
| Avg Latency | Establish baseline | Must not increase >20% |
| Quality Score | Establish baseline | Must improve >= 10% |
| Tool Call Efficiency | N/A | New capability - bonus |
| Context Utilization | 32K max | 256K available - bonus |

### Decision Matrix

| Outcome | Action |
|---------|--------|
| MiroThinker better on ALL metrics | Swap entirely |
| MiroThinker better on tool-calling, similar elsewhere | Run both (use MiroThinker for agents) |
| MiroThinker similar or worse | Keep Qwen2.5-Coder |
| Insufficient data | Extend test period |

---

## Phase 5: Reporting

### Daily Summary Query

```sql
SELECT
    model,
    DATE(tested_at) as test_date,
    COUNT(*) as requests,
    ROUND(AVG(latency_ms)::numeric, 0) as avg_latency,
    ROUND(AVG(completion_tokens / NULLIF(latency_ms / 1000, 0))::numeric, 1) as avg_tps,
    ROUND(AVG(quality_score)::numeric, 3) as avg_quality
FROM ab_test_results
GROUP BY model, DATE(tested_at)
ORDER BY test_date DESC, model;
```

### Thermal Memory Entry on Completion

Once testing is complete, archive results:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, memory_type
) VALUES (
    md5('mirothinker_ab_test_results_jan2026'),
    'A/B TEST RESULTS: Qwen2.5-Coder-32B-AWQ vs MiroThinker-v1.5-30B
    [INSERT ACTUAL RESULTS HERE]',
    95.0,
    ARRAY['ab-test', 'model-comparison', 'mirothinker', 'qwen', 'january-2026'],
    'tpm', 'redfin', 'operations'
);
```

---

## Council Concerns Addressed

| Concern | How Addressed |
|---------|---------------|
| Turtle [7GEN] | A/B test validates stability before commitment |
| Peace Chief [CONSENSUS] | Data-driven decision, not rushed swap |
| Crawdad [SECURITY] | Test in isolated environment first |
| Raven [STRATEGY] | Aligns with agent-first architecture direction |
| Gecko [PERF] | Explicit performance benchmarks required |

---

## Timeline

- **Day 1**: Download model, configure second vLLM instance
- **Day 2-3**: Implement A/B router and metrics logging
- **Day 4-7**: Run test suite, collect data
- **Day 8**: Analyze results, present to TPM
- **Decision**: TPM approves/rejects swap based on metrics

---

## Files Created

- `/etc/systemd/system/vllm-mirothinker.service`
- `/ganuda/scripts/ab_test_tasks.json`
- `/ganuda/scripts/run_ab_test.py`
- SQL table: `ab_test_results`
- SQL view: `ab_test_summary`

---

For Seven Generations.
