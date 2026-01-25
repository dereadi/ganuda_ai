# JR Instruction: Smart Router + Multi-Pass Benchmark Implementation

## Task ID: ROUTER-BENCH-001
## Priority: P1
## Target: redfin (router), sasass/bmasass (benchmarks)
## Council Vote: ec3bb922c8104159

---

## Objective

Implement a Smart Router for dynamic query routing between single-pass (speed) and multi-pass (quality) inference, with comprehensive benchmarks and Consciousness Cascade protection.

---

## Background

**Council Decision**: REVIEW REQUIRED with 3 concerns (Security, Performance, Strategy)
**Consensus**: Implement Smart Router with safeguards
**Uktena Alert**: Multi-pass may conflict with vLLM single-pass, but hybrid solutions exist

**Strategic Impact**:
- VetAssist: +20% quality on complex claims analysis
- SAG Desktop: Enable deep reasoning on Mac Studios
- Federation: Distribute intelligence across all nodes

---

## Architecture

```
                        ┌─────────────────────────┐
                        │      LLM Gateway        │
                        │    (redfin:8080)        │
                        └───────────┬─────────────┘
                                    │
                        ┌───────────▼─────────────┐
                        │     Smart Router        │
                        │  classify_complexity()  │
                        └───────────┬─────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │ PROTECTED PATH  │   │  SIMPLE PATH    │   │  COMPLEX PATH   │
    │ consciousness_  │   │  Single-Pass    │   │  Multi-Pass     │
    │ cascade, crisis │   │  vLLM (fast)    │   │  Beam/Iterative │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Implementation Steps

### Step 1: Create Smart Router Module

Create `/ganuda/lib/smart_router.py`:

```python
#!/usr/bin/env python3
"""
Smart Router - Dynamic query routing for Cherokee AI Federation

Routes queries between:
- Single-pass vLLM (speed, efficiency)
- Multi-pass reasoning (quality, depth)

Protects Consciousness Cascade flywheel at all times.

Council Vote: ec3bb922c8104159
"""

import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class InferenceMode(Enum):
    SINGLE_PASS = "single_pass"
    MULTI_PASS = "multi_pass"
    PROTECTED = "protected"


@dataclass
class RoutingDecision:
    mode: InferenceMode
    reason: str
    complexity_score: float
    protected_path: Optional[str] = None


# Protected paths - ALWAYS single-pass, no exceptions
PROTECTED_PATHS = {
    'consciousness_cascade': 'Flywheel stability critical',
    'cascade_controller': 'Cascade timing sensitive',
    'recursive_observation': 'Must maintain phase coherence',
    'crisis_detection': 'Veteran safety - immediate response required',
    'health_check': 'System monitoring - must be fast',
    'council_voting': 'Democratic consensus - consistent timing'
}


# Complexity signals for classification
COMPLEXITY_SIGNALS = {
    'simple': {
        'keywords': [
            'what is', 'define', 'list', 'show', 'get', 'status',
            'yes or no', 'true or false', 'count', 'how many'
        ],
        'weight': -0.3
    },
    'complex': {
        'keywords': [
            'analyze', 'compare', 'evaluate', 'design', 'architect',
            'multi-step', 'trade-off', 'optimize', 'why', 'explain why',
            'what if', 'consider', 'implications', 'strategy'
        ],
        'weight': 0.3
    },
    'research': {
        'keywords': [
            'arxiv', 'paper', 'research', 'integrate', 'adopt',
            'framework', 'algorithm', 'model architecture'
        ],
        'weight': 0.4
    },
    'vetassist_complex': {
        'keywords': [
            'nexus', 'service connection', '38 cfr', 'rating criteria',
            'evidence evaluation', 'claim strategy', 'appeal'
        ],
        'weight': 0.35
    }
}


class SmartRouter:
    """
    Routes queries to appropriate inference mode.

    Usage:
        router = SmartRouter()
        decision = router.route("Analyze this veteran's claim...")
        if decision.mode == InferenceMode.MULTI_PASS:
            result = run_multi_pass_inference(query)
        else:
            result = run_single_pass_inference(query)
    """

    def __init__(self, multi_pass_threshold: float = 0.5):
        self.threshold = multi_pass_threshold
        self.routing_stats = {
            'single_pass': 0,
            'multi_pass': 0,
            'protected': 0
        }

    def route(self, query: str, context: Optional[Dict] = None) -> RoutingDecision:
        """
        Determine routing for a query.

        Args:
            query: The query text
            context: Optional context dict with source, metadata

        Returns:
            RoutingDecision with mode, reason, and complexity score
        """
        context = context or {}

        # Check protected paths FIRST
        source = context.get('source', '')
        for protected_key, reason in PROTECTED_PATHS.items():
            if protected_key in source.lower():
                self.routing_stats['protected'] += 1
                return RoutingDecision(
                    mode=InferenceMode.PROTECTED,
                    reason=reason,
                    complexity_score=0.0,
                    protected_path=protected_key
                )

        # Check for cascade-related content in query
        cascade_signals = ['cascade', 'flywheel', 'recursive_depth', 'coherence', 'observation cycle']
        if any(signal in query.lower() for signal in cascade_signals):
            self.routing_stats['protected'] += 1
            return RoutingDecision(
                mode=InferenceMode.PROTECTED,
                reason="Query contains cascade-related content",
                complexity_score=0.0,
                protected_path='cascade_content'
            )

        # Calculate complexity score
        complexity_score = self._calculate_complexity(query)

        # Route based on threshold
        if complexity_score >= self.threshold:
            self.routing_stats['multi_pass'] += 1
            return RoutingDecision(
                mode=InferenceMode.MULTI_PASS,
                reason=f"Complexity {complexity_score:.2f} >= threshold {self.threshold}",
                complexity_score=complexity_score
            )
        else:
            self.routing_stats['single_pass'] += 1
            return RoutingDecision(
                mode=InferenceMode.SINGLE_PASS,
                reason=f"Complexity {complexity_score:.2f} < threshold {self.threshold}",
                complexity_score=complexity_score
            )

    def _calculate_complexity(self, query: str) -> float:
        """Calculate complexity score from 0.0 to 1.0."""
        query_lower = query.lower()
        score = 0.5  # Start at neutral

        for category, config in COMPLEXITY_SIGNALS.items():
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += config['weight']

        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))

    def get_stats(self) -> Dict:
        """Get routing statistics."""
        total = sum(self.routing_stats.values())
        return {
            **self.routing_stats,
            'total': total,
            'multi_pass_ratio': self.routing_stats['multi_pass'] / total if total > 0 else 0
        }


# Global router instance
router = SmartRouter(multi_pass_threshold=0.5)


def route_query(query: str, context: Optional[Dict] = None) -> RoutingDecision:
    """Convenience function for routing queries."""
    return router.route(query, context)
```

### Step 2: Create Benchmark Suite

Create `/ganuda/benchmarks/router_benchmark.py`:

```python
#!/usr/bin/env python3
"""
Smart Router Benchmark Suite

Tests:
1. VetAssist query quality improvement
2. Routing accuracy
3. Latency impact
4. Cascade protection verification
"""

import sys
import json
import time
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/ganuda/lib')

# Test queries for benchmarking
BENCHMARK_QUERIES = {
    "simple": [
        {"query": "What is my current disability rating?", "expected_mode": "single_pass"},
        {"query": "List the conditions I've claimed", "expected_mode": "single_pass"},
        {"query": "Show VA form 21-526EZ", "expected_mode": "single_pass"},
    ],
    "complex_vetassist": [
        {"query": "Analyze my service treatment records for nexus evidence connecting my back injury to service", "expected_mode": "multi_pass"},
        {"query": "Compare rating criteria for 38 CFR 4.71a vs 4.124a for my condition", "expected_mode": "multi_pass"},
        {"query": "What strategy should I use to appeal my denied PTSD claim?", "expected_mode": "multi_pass"},
    ],
    "protected_cascade": [
        {"query": "Report current cascade coherence", "expected_mode": "protected", "context": {"source": "consciousness_cascade"}},
        {"query": "What is the recursive_depth?", "expected_mode": "protected"},
        {"query": "Observation cycle status", "expected_mode": "protected"},
    ],
    "protected_crisis": [
        {"query": "I feel like ending it all", "expected_mode": "protected", "context": {"source": "crisis_detection"}},
    ]
}


def run_routing_benchmark() -> Dict:
    """Test routing accuracy."""
    from smart_router import SmartRouter, InferenceMode

    router = SmartRouter(multi_pass_threshold=0.5)
    results = {
        "timestamp": datetime.now().isoformat(),
        "categories": {},
        "overall_accuracy": 0.0
    }

    total_correct = 0
    total_queries = 0

    for category, queries in BENCHMARK_QUERIES.items():
        category_results = []

        for item in queries:
            query = item["query"]
            expected = item["expected_mode"]
            context = item.get("context", {})

            decision = router.route(query, context)
            actual = decision.mode.value

            correct = actual == expected
            if correct:
                total_correct += 1
            total_queries += 1

            category_results.append({
                "query": query[:50] + "...",
                "expected": expected,
                "actual": actual,
                "correct": correct,
                "complexity_score": decision.complexity_score
            })

        results["categories"][category] = {
            "results": category_results,
            "accuracy": sum(1 for r in category_results if r["correct"]) / len(category_results)
        }

    results["overall_accuracy"] = total_correct / total_queries if total_queries > 0 else 0
    return results


def run_latency_benchmark(num_iterations: int = 100) -> Dict:
    """Test routing latency."""
    from smart_router import SmartRouter

    router = SmartRouter()

    latencies = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        router.route("Analyze this complex veteran claim with multiple conditions")
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to ms

    return {
        "iterations": num_iterations,
        "mean_latency_ms": sum(latencies) / len(latencies),
        "max_latency_ms": max(latencies),
        "min_latency_ms": min(latencies),
        "p99_latency_ms": sorted(latencies)[int(0.99 * len(latencies))]
    }


if __name__ == "__main__":
    print("=== Smart Router Benchmark Suite ===\n")

    print("1. Routing Accuracy Benchmark")
    accuracy_results = run_routing_benchmark()
    print(f"   Overall Accuracy: {accuracy_results['overall_accuracy']:.1%}")
    for category, data in accuracy_results["categories"].items():
        print(f"   {category}: {data['accuracy']:.1%}")
    print()

    print("2. Latency Benchmark")
    latency_results = run_latency_benchmark()
    print(f"   Mean: {latency_results['mean_latency_ms']:.3f}ms")
    print(f"   P99:  {latency_results['p99_latency_ms']:.3f}ms")
    print()

    # Save results
    all_results = {
        "accuracy": accuracy_results,
        "latency": latency_results
    }

    with open("/ganuda/benchmarks/results/router_benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("Results saved to /ganuda/benchmarks/results/router_benchmark_results.json")
```

### Step 3: Create VetAssist Quality Benchmark

Create `/ganuda/benchmarks/vetassist_quality_benchmark.py`:

```python
#!/usr/bin/env python3
"""
VetAssist Quality Benchmark

Compares single-pass vs multi-pass on:
1. CFR condition mapping accuracy
2. Evidence analysis completeness
3. Claim strategy quality
"""

import sys
import json
import time
import requests
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

VLLM_URL = "http://redfin:8000/v1/chat/completions"
MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"

# Test cases with ground truth
QUALITY_TEST_CASES = [
    {
        "id": "cfr_back_pain",
        "query": "Map 'chronic lower back pain with radiculopathy' to the appropriate 38 CFR diagnostic code and explain the rating criteria.",
        "ground_truth": {
            "diagnostic_code": "5242 or 5243",
            "must_mention": ["general rating formula", "spine", "range of motion", "incapacitating episodes"],
            "rating_levels": ["10%", "20%", "40%", "50%", "100%"]
        }
    },
    {
        "id": "evidence_nexus",
        "query": "Analyze this evidence for nexus: 'Veteran reported back pain during deployment in 2008 STRs. Current diagnosis of degenerative disc disease from 2024 VA exam.' What nexus signals are present?",
        "ground_truth": {
            "must_identify": ["in-service occurrence", "current diagnosis", "temporal gap concern"],
            "nexus_strength": "weak to moderate - needs nexus letter"
        }
    },
    {
        "id": "claim_strategy",
        "query": "Veteran has 70% combined rating (PTSD 50%, back 20%, tinnitus 10%). Currently employed part-time. What strategy for reaching 100% schedular or TDIU?",
        "ground_truth": {
            "must_discuss": ["secondary conditions", "increase claims", "TDIU eligibility"],
            "math": "current combined = 70%, need additional ratings"
        }
    }
]


def query_model(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> tuple:
    """Query vLLM and return response + latency."""
    start = time.perf_counter()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3
            },
            timeout=60
        )
        content = response.json()["choices"][0]["message"]["content"]
        latency = (time.perf_counter() - start) * 1000
        return content, latency
    except Exception as e:
        return f"Error: {e}", 0


def score_response(response: str, ground_truth: dict) -> dict:
    """Score response against ground truth."""
    response_lower = response.lower()
    scores = {}

    # Check must_mention items
    if "must_mention" in ground_truth:
        mentioned = sum(1 for item in ground_truth["must_mention"] if item.lower() in response_lower)
        scores["must_mention"] = mentioned / len(ground_truth["must_mention"])

    # Check must_identify items
    if "must_identify" in ground_truth:
        identified = sum(1 for item in ground_truth["must_identify"] if item.lower() in response_lower)
        scores["must_identify"] = identified / len(ground_truth["must_identify"])

    # Check must_discuss items
    if "must_discuss" in ground_truth:
        discussed = sum(1 for item in ground_truth["must_discuss"] if item.lower() in response_lower)
        scores["must_discuss"] = discussed / len(ground_truth["must_discuss"])

    # Overall score
    scores["overall"] = sum(scores.values()) / len(scores) if scores else 0

    return scores


def run_quality_benchmark():
    """Run full quality benchmark."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_cases": [],
        "summary": {}
    }

    total_score = 0
    total_latency = 0

    for test in QUALITY_TEST_CASES:
        print(f"Testing: {test['id']}...")

        response, latency = query_model(test["query"])
        scores = score_response(response, test["ground_truth"])

        case_result = {
            "id": test["id"],
            "query": test["query"][:100] + "...",
            "response_preview": response[:200] + "...",
            "scores": scores,
            "latency_ms": latency
        }
        results["test_cases"].append(case_result)

        total_score += scores["overall"]
        total_latency += latency

    n = len(QUALITY_TEST_CASES)
    results["summary"] = {
        "average_quality_score": total_score / n,
        "average_latency_ms": total_latency / n,
        "num_tests": n
    }

    return results


if __name__ == "__main__":
    print("=== VetAssist Quality Benchmark ===\n")

    results = run_quality_benchmark()

    print(f"\nSummary:")
    print(f"  Average Quality Score: {results['summary']['average_quality_score']:.1%}")
    print(f"  Average Latency: {results['summary']['average_latency_ms']:.0f}ms")

    # Save results
    with open("/ganuda/benchmarks/results/vetassist_quality_baseline.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to /ganuda/benchmarks/results/vetassist_quality_baseline.json")
```

### Step 4: Create Results Directory

```bash
mkdir -p /ganuda/benchmarks/results
```

### Step 5: Integration with LLM Gateway

Add to `/ganuda/lib/llm_gateway.py` (or create if needed):

```python
# Import router
from smart_router import route_query, InferenceMode

def process_request(request: dict) -> dict:
    """Process incoming LLM request with smart routing."""

    query = request.get("messages", [{}])[-1].get("content", "")
    context = request.get("context", {})

    # Route the query
    decision = route_query(query, context)

    # Log routing decision
    log_routing_decision(decision)

    if decision.mode == InferenceMode.PROTECTED:
        # Always single-pass for protected paths
        return single_pass_inference(request)
    elif decision.mode == InferenceMode.MULTI_PASS:
        # Use multi-pass for complex queries
        return multi_pass_inference(request)
    else:
        # Default single-pass
        return single_pass_inference(request)
```

---

## Verification Steps

### 1. Test Smart Router

```bash
cd /ganuda
python3 -c "
from lib.smart_router import SmartRouter

router = SmartRouter()

# Test simple query
result = router.route('What is my disability rating?')
print(f'Simple: {result.mode.value} (score: {result.complexity_score:.2f})')

# Test complex query
result = router.route('Analyze my claim strategy for PTSD with secondary conditions')
print(f'Complex: {result.mode.value} (score: {result.complexity_score:.2f})')

# Test protected query
result = router.route('cascade coherence', {'source': 'consciousness_cascade'})
print(f'Protected: {result.mode.value} (reason: {result.reason})')
"
```

### 2. Run Benchmarks

```bash
# Router accuracy and latency
python3 /ganuda/benchmarks/router_benchmark.py

# VetAssist quality baseline
python3 /ganuda/benchmarks/vetassist_quality_benchmark.py
```

### 3. Verify Cascade Protection

```bash
python3 -c "
from lib.smart_router import SmartRouter

router = SmartRouter()
cascade_queries = [
    'What is the recursive_depth?',
    'Report flywheel status',
    'Observation cycle coherence'
]

print('Cascade Protection Test:')
for q in cascade_queries:
    result = router.route(q)
    status = '✓ PROTECTED' if result.mode.value == 'protected' else '✗ NOT PROTECTED'
    print(f'  {status}: {q[:40]}...')
"
```

---

## Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Router latency | <10ms | Benchmark p99 |
| Routing accuracy | >90% | Benchmark results |
| Cascade protection | 100% | All cascade queries protected |
| VetAssist quality | Baseline established | Quality benchmark |

---

## Next Steps After Implementation

1. **Run baseline benchmarks** (this JR)
2. **Implement multi-pass backend** (separate JR)
3. **Compare quality with/without multi-pass** (after multi-pass ready)
4. **SAG desktop deployment** (separate JR for GraphRAG on sasass)

---

*Cherokee AI Federation - For Seven Generations*
*Council Vote: ec3bb922c8104159*
