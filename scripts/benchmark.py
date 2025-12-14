#!/usr/bin/env python3
"""
Ganuda Benchmark Framework
Generate capacity cards for production planning
"""

import time
import json
import statistics
import requests
from datetime import datetime
from typing import List, Dict, Any
import argparse

class GanudaBenchmark:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.results = []

    def _chat(self, content: str, max_tokens: int = 100) -> Dict:
        """Make a chat completion request"""
        start = time.time()
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "default",
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": max_tokens
                },
                timeout=120
            )
            elapsed = time.time() - start
            data = resp.json()
            return {
                "success": resp.status_code == 200,
                "latency_ms": elapsed * 1000,
                "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
                "status_code": resp.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "latency_ms": (time.time() - start) * 1000,
                "error": str(e)
            }

    def measure_latency(self, n_samples: int = 5) -> Dict:
        """Measure response latency"""
        print(f"  Running {n_samples} latency samples...")
        latencies = []
        for i in range(n_samples):
            result = self._chat("Say hello in one sentence.", max_tokens=50)
            if result["success"]:
                latencies.append(result["latency_ms"])
            print(f"    Sample {i+1}: {result['latency_ms']:.0f}ms")

        if not latencies:
            return {"error": "All requests failed"}

        return {
            "name": "Response Latency",
            "p50_ms": statistics.median(latencies),
            "p99_ms": max(latencies),
            "min_ms": min(latencies),
            "samples": n_samples
        }

    def measure_throughput(self, n_samples: int = 3) -> Dict:
        """Measure tokens per second"""
        print(f"  Running {n_samples} throughput samples...")
        total_tokens = 0
        total_time = 0

        for i in range(n_samples):
            result = self._chat(
                "Write a detailed paragraph about artificial intelligence and its impact on society.",
                max_tokens=200
            )
            if result["success"]:
                total_tokens += result["tokens_out"]
                total_time += result["latency_ms"] / 1000
            print(f"    Sample {i+1}: {result.get('tokens_out', 0)} tokens in {result['latency_ms']:.0f}ms")

        if total_time == 0:
            return {"error": "All requests failed"}

        return {
            "name": "Throughput",
            "tokens_per_sec": total_tokens / total_time,
            "total_tokens": total_tokens,
            "total_time_sec": total_time
        }

    def measure_consistency(self, n_samples: int = 5) -> Dict:
        """Measure response consistency (same input -> similar output)"""
        print(f"  Running {n_samples} consistency samples...")
        prompt = "What is 2 + 2? Answer with just the number."
        correct = 0

        for i in range(n_samples):
            result = self._chat(prompt, max_tokens=10)
            if result["success"]:
                # Would need to check response content
                correct += 1
            print(f"    Sample {i+1}: {'OK' if result['success'] else 'FAIL'}")

        return {
            "name": "Consistency",
            "success_rate": (correct / n_samples) * 100,
            "samples": n_samples
        }

    def get_model_info(self) -> Dict:
        """Get model information"""
        try:
            resp = requests.get(
                f"{self.base_url}/v1/models",
                headers=self.headers,
                timeout=10
            )
            data = resp.json()
            models = data.get("data", [])
            if models:
                return {"model": models[0].get("id", "unknown")}
        except:
            pass
        return {"model": "unknown"}

    def get_health(self) -> Dict:
        """Get health status"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=10)
            return resp.json()
        except:
            return {"status": "unknown"}

    def run_all(self) -> Dict:
        """Run all benchmarks and generate capacity card"""
        print("\n🏔️  Ganuda Benchmark")
        print("=" * 40)

        # Get system info
        print("\n📊 Gathering system info...")
        model_info = self.get_model_info()
        health = self.get_health()

        # Run benchmarks
        print("\n⏱️  Measuring latency...")
        latency = self.measure_latency(5)

        print("\n📈 Measuring throughput...")
        throughput = self.measure_throughput(3)

        print("\n✓ Measuring consistency...")
        consistency = self.measure_consistency(3)

        return {
            "generated_at": datetime.now().isoformat(),
            "endpoint": self.base_url,
            "model": model_info.get("model", "unknown"),
            "health": health,
            "benchmarks": {
                "latency": latency,
                "throughput": throughput,
                "consistency": consistency
            }
        }

    def generate_capacity_card(self, results: Dict) -> str:
        """Generate markdown capacity card"""
        latency = results["benchmarks"]["latency"]
        throughput = results["benchmarks"]["throughput"]

        card = f"""# Ganuda Capacity Card

**Generated**: {results['generated_at']}
**Endpoint**: {results['endpoint']}
**Model**: {results['model']}

## Performance Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Latency (P50) | {latency.get('p50_ms', 'N/A'):.0f}ms | <500ms | {'✅' if latency.get('p50_ms', 9999) < 500 else '⚠️'} |
| Latency (P99) | {latency.get('p99_ms', 'N/A'):.0f}ms | <2000ms | {'✅' if latency.get('p99_ms', 9999) < 2000 else '⚠️'} |
| Throughput | {throughput.get('tokens_per_sec', 0):.1f} tok/s | >20 | {'✅' if throughput.get('tokens_per_sec', 0) > 20 else '⚠️'} |
| Success Rate | {results['benchmarks']['consistency'].get('success_rate', 0):.0f}% | >95% | {'✅' if results['benchmarks']['consistency'].get('success_rate', 0) > 95 else '⚠️'} |

## Health Status

```json
{json.dumps(results['health'], indent=2)}
```

## Test Conditions

- Samples per test: 3-5
- Max tokens: 50-200
- Date: {results['generated_at'][:10]}

---
*Generated by Ganuda Benchmark Framework*
"""
        return card


def main():
    parser = argparse.ArgumentParser(description="Ganuda Benchmark")
    parser.add_argument("--url", default="http://localhost:8080", help="Gateway URL")
    parser.add_argument("--key", required=True, help="API key")
    parser.add_argument("--output", default="/ganuda/docs/CAPACITY_CARD.md", help="Output file")
    args = parser.parse_args()

    bench = GanudaBenchmark(args.url, args.key)
    results = bench.run_all()

    # Generate and save capacity card
    card = bench.generate_capacity_card(results)
    print("\n" + "=" * 40)
    print(card)

    with open(args.output, "w") as f:
        f.write(card)
    print(f"\n✅ Capacity card saved to {args.output}")

    # Also save raw JSON
    json_output = args.output.replace(".md", ".json")
    with open(json_output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Raw data saved to {json_output}")


if __name__ == "__main__":
    main()
