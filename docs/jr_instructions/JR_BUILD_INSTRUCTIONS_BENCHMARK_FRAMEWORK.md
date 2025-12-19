# Jr Build Instructions: Ganuda Benchmark & Evaluation Framework
## Priority: HIGH - Required for v1.0 Trust Documentation

---

## Context: The Yi Ma Principle

> "We are at the point we can analyze what we have versus the new thing and judge or benchmark each to see if the next shiny thing is really worth investing code and time on it."

Professor Yi Ma's research on intelligence principles provides a framework for evaluating AI systems:

1. **Parsimony** - Does the system find the simplest representation?
2. **Self-Consistency** - Can it recreate/predict from its model?
3. **Memorization vs Understanding** - Does it truly compress or just store?

**Key Insight**: Intelligence is not about solving the hardest problem. It's about identifying what is *easy to learn first*. Nature finds the easiest things with minimal energy to learn the most knowledge.

---

## Objective

Create a benchmark framework that:
1. Measures Ganuda Gateway performance objectively
2. Compares new features/models against baselines
3. Prevents "shiny object" syndrome - validate before adopting
4. Publishes reproducible capacity cards

---

## Benchmark Categories

### 1. Latency Benchmarks

| Metric | Measurement | Target |
|--------|-------------|--------|
| Cold Start | Time from service start to first response | < 30s |
| TTFT (Time to First Token) | Request to first token | < 500ms |
| P50 Latency | 50th percentile response time | < 200ms |
| P99 Latency | 99th percentile response time | < 2s |
| Concurrent Latency | P50 under 4 concurrent requests | < 400ms |

### 2. Throughput Benchmarks

| Metric | Measurement | Target |
|--------|-------------|--------|
| Tokens/sec (single) | Single request throughput | > 25 tok/s |
| Tokens/sec (batch) | Batch of 4 requests | > 80 tok/s |
| Requests/min | Max sustained requests | > 100 rpm |
| Max Concurrent | Requests before degradation | >= 4 |

### 3. Quality Benchmarks (Yi Ma Principles)

| Metric | Measurement | Purpose |
|--------|-------------|---------|
| Response Consistency | Same prompt → similar response | Self-consistency check |
| Compression Ratio | Input tokens / useful output | Parsimony measure |
| Hallucination Rate | Factual errors per 100 responses | Understanding vs memorization |
| Task Completion | % of requests that achieve goal | Practical utility |

### 4. Resource Benchmarks

| Metric | Measurement | Target |
|--------|-------------|--------|
| VRAM Usage | GPU memory at steady state | < 24GB |
| RAM Usage | System memory | < 8GB |
| CPU Usage | Average during inference | < 50% |
| Disk I/O | Read/write during operation | Minimal |

---

## Implementation Tasks

### Task 1: Create Benchmark Runner

Location: `/ganuda/scripts/benchmark.py`

```python
#!/usr/bin/env python3
"""
Ganuda Benchmark Framework
Based on Yi Ma's principles: Parsimony, Self-Consistency, Verification
"""

import time
import json
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import List, Optional
import argparse

@dataclass
class BenchmarkResult:
    name: str
    metric: str
    value: float
    unit: str
    target: Optional[float] = None
    passed: Optional[bool] = None

@dataclass
class CapacityCard:
    model: str
    hardware: str
    timestamp: str
    results: List[BenchmarkResult]

    def to_markdown(self) -> str:
        lines = [
            "# Ganuda Capacity Card",
            f"**Model**: {self.model}",
            f"**Hardware**: {self.hardware}",
            f"**Generated**: {self.timestamp}",
            "",
            "## Results",
            "| Metric | Value | Target | Status |",
            "|--------|-------|--------|--------|"
        ]
        for r in self.results:
            status = "✅" if r.passed else "❌" if r.passed is False else "—"
            target = f"{r.target}{r.unit}" if r.target else "—"
            lines.append(f"| {r.name} | {r.value:.2f}{r.unit} | {target} | {status} |")
        return "\n".join(lines)


class GanudaBenchmark:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def measure_cold_start(self) -> BenchmarkResult:
        """Measure time from restart to first response"""
        # This requires service restart capability
        # For now, measure first request latency
        start = time.time()
        self._chat_request("Hello")
        elapsed = time.time() - start
        return BenchmarkResult(
            name="First Request Latency",
            metric="cold_start",
            value=elapsed * 1000,
            unit="ms",
            target=500,
            passed=elapsed < 0.5
        )

    def measure_ttft(self, n_samples: int = 10) -> BenchmarkResult:
        """Measure time to first token"""
        latencies = []
        for _ in range(n_samples):
            start = time.time()
            # Stream request to measure TTFT
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "default",
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "stream": True,
                    "max_tokens": 10
                },
                stream=True
            )
            for chunk in resp.iter_lines():
                if chunk:
                    latencies.append(time.time() - start)
                    break

        p50 = statistics.median(latencies) * 1000
        return BenchmarkResult(
            name="Time to First Token (P50)",
            metric="ttft_p50",
            value=p50,
            unit="ms",
            target=500,
            passed=p50 < 500
        )

    def measure_throughput(self, n_samples: int = 5) -> BenchmarkResult:
        """Measure tokens per second"""
        total_tokens = 0
        total_time = 0

        for _ in range(n_samples):
            start = time.time()
            resp = self._chat_request(
                "Write a paragraph about the Cherokee Nation.",
                max_tokens=200
            )
            elapsed = time.time() - start
            tokens = resp.get("usage", {}).get("completion_tokens", 0)
            total_tokens += tokens
            total_time += elapsed

        tok_per_sec = total_tokens / total_time if total_time > 0 else 0
        return BenchmarkResult(
            name="Throughput",
            metric="tokens_per_sec",
            value=tok_per_sec,
            unit=" tok/s",
            target=25,
            passed=tok_per_sec >= 25
        )

    def measure_concurrent(self, n_concurrent: int = 4) -> BenchmarkResult:
        """Measure latency under concurrent load"""
        def single_request():
            start = time.time()
            self._chat_request("Hello", max_tokens=20)
            return time.time() - start

        with ThreadPoolExecutor(max_workers=n_concurrent) as executor:
            latencies = list(executor.map(lambda _: single_request(), range(n_concurrent)))

        p50 = statistics.median(latencies) * 1000
        return BenchmarkResult(
            name=f"Concurrent Latency ({n_concurrent} req)",
            metric="concurrent_p50",
            value=p50,
            unit="ms",
            target=400,
            passed=p50 < 400
        )

    def measure_consistency(self, n_samples: int = 5) -> BenchmarkResult:
        """Yi Ma's self-consistency: same input → consistent output"""
        prompt = "What is 2 + 2?"
        responses = []

        for _ in range(n_samples):
            resp = self._chat_request(prompt, max_tokens=50)
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            responses.append(content)

        # Check if all responses contain "4"
        consistent = sum(1 for r in responses if "4" in r) / len(responses)
        return BenchmarkResult(
            name="Response Consistency",
            metric="consistency",
            value=consistent * 100,
            unit="%",
            target=95,
            passed=consistent >= 0.95
        )

    def _chat_request(self, content: str, max_tokens: int = 100) -> dict:
        resp = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json={
                "model": "default",
                "messages": [{"role": "user", "content": content}],
                "max_tokens": max_tokens
            }
        )
        return resp.json()

    def run_all(self) -> CapacityCard:
        """Run all benchmarks and generate capacity card"""
        import datetime

        results = [
            self.measure_cold_start(),
            self.measure_ttft(),
            self.measure_throughput(),
            self.measure_concurrent(),
            self.measure_consistency()
        ]

        # Get model info
        models_resp = requests.get(
            f"{self.base_url}/v1/models",
            headers=self.headers
        ).json()
        model_name = models_resp.get("data", [{}])[0].get("id", "unknown")

        return CapacityCard(
            model=model_name,
            hardware="redfin - RTX 5090 96GB",
            timestamp=datetime.datetime.now().isoformat(),
            results=results
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ganuda Benchmark")
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--key", required=True)
    parser.add_argument("--output", default="capacity_card.md")
    args = parser.parse_args()

    bench = GanudaBenchmark(args.url, args.key)
    card = bench.run_all()

    print(card.to_markdown())

    with open(args.output, "w") as f:
        f.write(card.to_markdown())

    print(f"\nCapacity card written to {args.output}")
```

### Task 2: Create Comparison Framework

Location: `/ganuda/scripts/compare_models.py`

```python
#!/usr/bin/env python3
"""
Model Comparison Framework
"See if the next shiny thing is really worth investing code and time on it"
"""

import json
from benchmark import GanudaBenchmark, CapacityCard
from dataclasses import dataclass
from typing import List

@dataclass
class ComparisonResult:
    baseline: CapacityCard
    challenger: CapacityCard
    winner: str
    improvements: List[str]
    regressions: List[str]
    recommendation: str

def compare_cards(baseline: CapacityCard, challenger: CapacityCard) -> ComparisonResult:
    """Compare two capacity cards and determine if upgrade is worthwhile"""

    improvements = []
    regressions = []

    baseline_metrics = {r.metric: r.value for r in baseline.results}
    challenger_metrics = {r.metric: r.value for r in challenger.results}

    # Higher is better for: tokens_per_sec, consistency
    higher_better = {"tokens_per_sec", "consistency"}
    # Lower is better for: latency metrics
    lower_better = {"cold_start", "ttft_p50", "concurrent_p50"}

    for metric, baseline_val in baseline_metrics.items():
        challenger_val = challenger_metrics.get(metric, baseline_val)

        if metric in higher_better:
            if challenger_val > baseline_val * 1.1:  # 10% improvement threshold
                improvements.append(f"{metric}: {baseline_val:.1f} → {challenger_val:.1f}")
            elif challenger_val < baseline_val * 0.9:
                regressions.append(f"{metric}: {baseline_val:.1f} → {challenger_val:.1f}")

        elif metric in lower_better:
            if challenger_val < baseline_val * 0.9:  # 10% improvement threshold
                improvements.append(f"{metric}: {baseline_val:.1f} → {challenger_val:.1f}")
            elif challenger_val > baseline_val * 1.1:
                regressions.append(f"{metric}: {baseline_val:.1f} → {challenger_val:.1f}")

    # Determine winner and recommendation
    if len(regressions) > 0 and len(improvements) == 0:
        winner = "baseline"
        recommendation = "REJECT: Challenger shows regressions with no improvements"
    elif len(improvements) > len(regressions):
        winner = "challenger"
        recommendation = "ADOPT: Net improvement over baseline"
    elif len(regressions) > len(improvements):
        winner = "baseline"
        recommendation = "REJECT: Net regression vs baseline"
    else:
        winner = "tie"
        recommendation = "INVESTIGATE: Mixed results, manual review needed"

    return ComparisonResult(
        baseline=baseline,
        challenger=challenger,
        winner=winner,
        improvements=improvements,
        regressions=regressions,
        recommendation=recommendation
    )
```

### Task 3: Create Capacity Card Template

Location: `/ganuda/docs/CAPACITY_CARD_TEMPLATE.md`

```markdown
# Ganuda Capacity Card

## Model Information
- **Model**: [Model Name]
- **Parameters**: [Size]
- **Quantization**: [None/INT8/INT4]
- **Context Window**: [Tokens]

## Hardware
- **Node**: [redfin/bluefin/etc]
- **GPU**: [Model]
- **VRAM**: [Total/Used]
- **CPU**: [Model]
- **RAM**: [Total]

## Performance Metrics

### Latency
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Cold Start | Xms | <30,000ms | ✅/❌ |
| TTFT (P50) | Xms | <500ms | ✅/❌ |
| TTFT (P99) | Xms | <2,000ms | ✅/❌ |
| Response (P50) | Xms | <200ms | ✅/❌ |
| Concurrent (4) | Xms | <400ms | ✅/❌ |

### Throughput
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Tokens/sec | X | >25 | ✅/❌ |
| Requests/min | X | >100 | ✅/❌ |
| Max Concurrent | X | >=4 | ✅/❌ |

### Quality (Yi Ma Principles)
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Consistency | X% | >95% | ✅/❌ |
| Task Completion | X% | >90% | ✅/❌ |

### Resources
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| VRAM Usage | XGB | <24GB | ✅/❌ |
| RAM Usage | XGB | <8GB | ✅/❌ |
| CPU Usage | X% | <50% | ✅/❌ |

## Test Conditions
- **Date**: [YYYY-MM-DD]
- **Duration**: [X minutes]
- **Requests**: [Total count]
- **Load Pattern**: [Sequential/Concurrent/Burst]

## Recommendation
[PRODUCTION READY / NEEDS OPTIMIZATION / NOT RECOMMENDED]

---
*Generated by Ganuda Benchmark Framework*
```

---

## Yi Ma Integration: Decision Framework

Before adopting any new model, architecture, or feature:

### The Three Questions

1. **Parsimony**: Is this the simplest solution that works?
   - Does it add unnecessary complexity?
   - Can we achieve the same with less?

2. **Self-Consistency**: Does it maintain coherent behavior?
   - Same inputs → consistent outputs?
   - Does it degrade gracefully under load?

3. **Verification**: Can we prove it's better?
   - Benchmark against baseline
   - Quantify improvements
   - Identify regressions

### Decision Matrix

| Improvements | Regressions | Decision |
|--------------|-------------|----------|
| Many | None | ADOPT |
| Some | None | ADOPT with monitoring |
| Some | Some | INVESTIGATE further |
| None | Some | REJECT |
| None | None | SKIP (no value) |

---

## File Locations

| File | Purpose |
|------|---------|
| `/ganuda/scripts/benchmark.py` | Main benchmark runner |
| `/ganuda/scripts/compare_models.py` | A/B comparison tool |
| `/ganuda/docs/CAPACITY_CARD_TEMPLATE.md` | Card template |
| `/ganuda/benchmarks/` | Stored benchmark results |

---

## Usage

```bash
# Run benchmarks
python /ganuda/scripts/benchmark.py \
  --url http://localhost:8080 \
  --key $GANUDA_API_KEY \
  --output /ganuda/benchmarks/$(date +%Y%m%d).md

# Compare two runs
python /ganuda/scripts/compare_models.py \
  --baseline /ganuda/benchmarks/baseline.json \
  --challenger /ganuda/benchmarks/new_model.json
```

---

## Success Criteria

- [ ] Benchmark script runs without errors
- [ ] Generates readable capacity card
- [ ] Comparison framework identifies improvements/regressions
- [ ] Results stored in `/ganuda/benchmarks/`
- [ ] Documentation explains methodology

---

## Integration with Product Decisions

Every new feature, model, or architecture change must:

1. Run benchmarks on current baseline
2. Implement change in test environment
3. Run benchmarks on challenger
4. Compare results
5. Only merge if: improvements > regressions AND no critical regressions

This prevents "shiny object" syndrome and ensures we build trust through measured improvement.

---

*For Seven Generations*

*"Intelligence is precisely the ability to identify what is easy to address first."* - Yi Ma
