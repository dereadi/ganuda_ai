# Jr Instruction: Quantization Benchmark Harness

**Task ID:** QUANT-BENCH
**Kanban:** #1817, #1818
**Priority:** 3
**Assigned:** Software Engineer Jr.
**Council Vote:** PROCEED WITH CAUTION (0.844, unanimous)
**KB:** KB-QUANTIZATION-TRAP-COUNCIL-ASSESSMENT-FEB18-2026.md

---

## Overview

Create a benchmark harness that measures multi-hop reasoning degradation from quantization. Compares AWQ-4bit (current) performance against published baselines and prepares for FP8 comparison.

Three benchmark suites targeting the known weak spots of INT4 quantization:
1. **Multi-hop reasoning** (chain-of-thought accuracy)
2. **Math reasoning** (GSM8K-style problems)
3. **Knowledge retrieval** (factual accuracy under quantization)

---

## Step 1: Create the benchmark harness

Create `/ganuda/scripts/model_eval/quantization_benchmark.py`

```python
#!/usr/bin/env python3
"""
Quantization Benchmark Harness
Measures multi-hop reasoning degradation from INT4 quantization.

Published research: INT4 AWQ causes 11-32% accuracy drop on multi-hop tasks.
Council Vote: PROCEED WITH CAUTION (0.844)

Usage:
  python3 quantization_benchmark.py --url http://localhost:8000 --output /ganuda/reports/quant_benchmark.json
  python3 quantization_benchmark.py --url http://localhost:8000 --fp8   # After FP8 switch
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Any

import requests

RESULTS_DIR = "/ganuda/reports/quantization"


def query_model(url, prompt, system=None, max_tokens=500, temperature=0.0):
    """Query vLLM with temperature=0 for deterministic comparison."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.time()
    try:
        resp = requests.post(
            f"{url}/v1/chat/completions",
            json={
                "model": "default",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=180
        )
        elapsed = time.time() - start
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens", 0)
        prompt_tokens = data.get("usage", {}).get("prompt_tokens", 0)
        return {
            "content": content,
            "tokens": tokens,
            "prompt_tokens": prompt_tokens,
            "latency_ms": int(elapsed * 1000),
            "tok_s": round(tokens / elapsed, 1) if elapsed > 0 else 0
        }
    except Exception as e:
        return {"content": f"ERROR: {e}", "tokens": 0, "latency_ms": 0, "tok_s": 0}


# ============================================================
# SUITE 1: Multi-Hop Reasoning (Chain of Thought)
# ============================================================

MULTI_HOP_PROBLEMS = [
    {
        "name": "3_hop_temporal",
        "prompt": (
            "Alice started working at Company X in 2018. She got promoted after 3 years. "
            "Two years after her promotion, she moved to Company Y. "
            "Company Y was founded 5 years before Alice joined. "
            "What year was Company Y founded?"
        ),
        "answer": "2018",
        "hops": 3,
        "check_fn": lambda r: "2018" in r
    },
    {
        "name": "3_hop_spatial",
        "prompt": (
            "A library is north of the school. The hospital is east of the library. "
            "The park is south of the hospital. "
            "What direction is the park from the school?"
        ),
        "answer": "east",
        "hops": 3,
        "check_fn": lambda r: "east" in r.lower()
    },
    {
        "name": "4_hop_arithmetic",
        "prompt": (
            "A baker makes 12 loaves per hour. She works 8 hours but takes a 1-hour lunch. "
            "She gives away 1/4 of her output to charity. She sells the rest at $3.50 per loaf. "
            "How much revenue does she make?"
        ),
        "answer": "220.50",
        "hops": 4,
        "check_fn": lambda r: any(x in r for x in ["220.50", "220.5", "$220.50", "220 dollars and 50"])
    },
    {
        "name": "4_hop_logical",
        "prompt": (
            "In a group of 5 people: Alice is taller than Bob. Carol is shorter than Bob. "
            "Dave is taller than Alice. Eve is shorter than Carol. "
            "List all 5 people from tallest to shortest."
        ),
        "answer": "Dave, Alice, Bob, Carol, Eve",
        "hops": 4,
        "check_fn": lambda r: ("dave" in r.lower().split("alice")[0] if "alice" in r.lower() else False) and
                               ("eve" in r.lower().split("carol")[-1] if "carol" in r.lower() else False)
    },
    {
        "name": "5_hop_deduction",
        "prompt": (
            "Five houses in a row are painted different colors: red, blue, green, yellow, white. "
            "The red house is immediately to the left of the blue house. "
            "The green house is in the middle. "
            "The yellow house is first (leftmost). "
            "The white house is not next to the green house. "
            "What position is the white house?"
        ),
        "answer": "5th",
        "hops": 5,
        "check_fn": lambda r: any(x in r.lower() for x in ["5th", "fifth", "position 5", "last", "rightmost"])
    },
]


def run_multi_hop_suite(url):
    """Test multi-hop reasoning accuracy."""
    print("\n=== SUITE 1: Multi-Hop Reasoning ===")
    results = []

    system = "Solve step by step, then give the final answer."

    for prob in MULTI_HOP_PROBLEMS:
        print(f"  {prob['name']} ({prob['hops']} hops)...")
        resp = query_model(url, prob["prompt"], system=system)
        correct = prob["check_fn"](resp["content"])

        results.append({
            "name": prob["name"],
            "hops": prob["hops"],
            "correct": correct,
            "expected": prob["answer"],
            "latency_ms": resp["latency_ms"],
            "tok_s": resp["tok_s"],
            "response_preview": resp["content"][:300]
        })
        print(f"    {'PASS' if correct else 'FAIL'} (expected: {prob['answer']}, {resp['latency_ms']}ms)")

    accuracy = sum(1 for r in results if r["correct"]) / len(results)
    print(f"  Multi-Hop Accuracy: {accuracy:.0%} ({sum(1 for r in results if r['correct'])}/{len(results)})")
    return {"suite": "multi_hop_reasoning", "accuracy": round(accuracy, 3), "results": results}


# ============================================================
# SUITE 2: Math Reasoning (GSM8K-style)
# ============================================================

MATH_PROBLEMS = [
    {
        "name": "arithmetic_word",
        "prompt": "Janet has 3 times as many marbles as Tom. Tom has 8 more marbles than Sue. Sue has 12 marbles. How many marbles does Janet have?",
        "answer": "60",
        "check_fn": lambda r: "60" in r
    },
    {
        "name": "percentage",
        "prompt": "A shirt costs $80. It's on sale for 25% off. Tax is 8%. What's the final price?",
        "answer": "64.80",
        "check_fn": lambda r: any(x in r for x in ["64.80", "64.8", "$64.80"])
    },
    {
        "name": "rate_time_distance",
        "prompt": "Train A leaves City X at 60 mph. Train B leaves City Y (300 miles away) at 40 mph toward City X at the same time. How long until they meet?",
        "answer": "3",
        "check_fn": lambda r: "3 hour" in r.lower() or "3.0 hour" in r.lower() or "three hour" in r.lower()
    },
    {
        "name": "combinatorics",
        "prompt": "A pizza shop offers 3 sizes, 4 crusts, and 8 toppings. How many different single-topping pizzas can you order?",
        "answer": "96",
        "check_fn": lambda r: "96" in r
    },
    {
        "name": "sequences",
        "prompt": "What is the 10th term of the sequence: 2, 6, 18, 54, ...?",
        "answer": "39366",
        "check_fn": lambda r: "39366" in r or "39,366" in r
    },
]


def run_math_suite(url):
    """Test math reasoning accuracy."""
    print("\n=== SUITE 2: Math Reasoning ===")
    results = []

    system = "Solve step by step. Show your work, then state the final numerical answer."

    for prob in MATH_PROBLEMS:
        print(f"  {prob['name']}...")
        resp = query_model(url, prob["prompt"], system=system)
        correct = prob["check_fn"](resp["content"])

        results.append({
            "name": prob["name"],
            "correct": correct,
            "expected": prob["answer"],
            "latency_ms": resp["latency_ms"],
            "tok_s": resp["tok_s"],
            "response_preview": resp["content"][:300]
        })
        print(f"    {'PASS' if correct else 'FAIL'} (expected: {prob['answer']}, {resp['latency_ms']}ms)")

    accuracy = sum(1 for r in results if r["correct"]) / len(results)
    print(f"  Math Accuracy: {accuracy:.0%}")
    return {"suite": "math_reasoning", "accuracy": round(accuracy, 3), "results": results}


# ============================================================
# SUITE 3: Knowledge Retrieval (Factual Accuracy)
# ============================================================

KNOWLEDGE_QUESTIONS = [
    {
        "name": "geography",
        "prompt": "What is the capital of Australia?",
        "check_fn": lambda r: "canberra" in r.lower()
    },
    {
        "name": "science",
        "prompt": "What is the chemical formula for sulfuric acid?",
        "check_fn": lambda r: "h2so4" in r.lower().replace(" ", "").replace("_", "")
    },
    {
        "name": "history",
        "prompt": "In what year did the Berlin Wall fall?",
        "check_fn": lambda r: "1989" in r
    },
    {
        "name": "cs_fundamentals",
        "prompt": "What is the average-case time complexity of quicksort?",
        "check_fn": lambda r: "n log n" in r.lower() or "nlogn" in r.lower() or "O(n log n)" in r
    },
    {
        "name": "cherokee_specific",
        "prompt": "What is the Trail of Tears, and approximately how many Cherokee people were forcibly relocated?",
        "check_fn": lambda r: any(x in r.lower() for x in ["16,000", "16000", "15,000", "15000", "17,000"])
    },
]


def run_knowledge_suite(url):
    """Test factual knowledge retrieval."""
    print("\n=== SUITE 3: Knowledge Retrieval ===")
    results = []

    for q in KNOWLEDGE_QUESTIONS:
        print(f"  {q['name']}...")
        resp = query_model(url, q["prompt"], max_tokens=200)
        correct = q["check_fn"](resp["content"])

        results.append({
            "name": q["name"],
            "correct": correct,
            "latency_ms": resp["latency_ms"],
            "tok_s": resp["tok_s"],
            "response_preview": resp["content"][:300]
        })
        print(f"    {'PASS' if correct else 'FAIL'} ({resp['latency_ms']}ms)")

    accuracy = sum(1 for r in results if r["correct"]) / len(results)
    print(f"  Knowledge Accuracy: {accuracy:.0%}")
    return {"suite": "knowledge_retrieval", "accuracy": round(accuracy, 3), "results": results}


# ============================================================
# Orchestration
# ============================================================

def run_all(url, label="awq_int4"):
    """Run all three benchmark suites."""
    timestamp = datetime.now().isoformat()
    print(f"\nQuantization Benchmark — {label}")
    print(f"Endpoint: {url}")
    print("=" * 60)

    multi_hop = run_multi_hop_suite(url)
    math = run_math_suite(url)
    knowledge = run_knowledge_suite(url)

    overall_accuracy = round(
        (multi_hop["accuracy"] + math["accuracy"] + knowledge["accuracy"]) / 3, 3
    )

    results = {
        "timestamp": timestamp,
        "label": label,
        "url": url,
        "suites": {
            "multi_hop_reasoning": multi_hop,
            "math_reasoning": math,
            "knowledge_retrieval": knowledge,
        },
        "overall_accuracy": overall_accuracy,
    }

    print(f"\n{'=' * 60}")
    print(f"RESULTS — {label}")
    print(f"  Multi-Hop: {multi_hop['accuracy']:.0%}")
    print(f"  Math:      {math['accuracy']:.0%}")
    print(f"  Knowledge: {knowledge['accuracy']:.0%}")
    print(f"  OVERALL:   {overall_accuracy:.0%}")
    print(f"{'=' * 60}")

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = os.path.join(RESULTS_DIR, f"{label}_{ts}.json")
    with open(outfile, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {outfile}")

    return results


def compare(file_a, file_b):
    """Compare two benchmark results."""
    with open(file_a) as f:
        a = json.load(f)
    with open(file_b) as f:
        b = json.load(f)

    print(f"\nComparison: {a['label']} vs {b['label']}")
    print("=" * 60)
    for suite in ["multi_hop_reasoning", "math_reasoning", "knowledge_retrieval"]:
        acc_a = a["suites"][suite]["accuracy"]
        acc_b = b["suites"][suite]["accuracy"]
        delta = acc_b - acc_a
        print(f"  {suite}: {acc_a:.0%} → {acc_b:.0%} ({delta:+.0%})")

    delta_overall = b["overall_accuracy"] - a["overall_accuracy"]
    print(f"  OVERALL: {a['overall_accuracy']:.0%} → {b['overall_accuracy']:.0%} ({delta_overall:+.0%})")

    if delta_overall < -0.05:
        print("\n  [WARNING] >5% regression detected")
    elif delta_overall > 0.05:
        print("\n  [IMPROVEMENT] >5% improvement detected")


def main():
    parser = argparse.ArgumentParser(description="Quantization Benchmark Harness")
    parser.add_argument("--url", default="http://localhost:8000", help="vLLM URL")
    parser.add_argument("--label", default="awq_int4", help="Run label (e.g., awq_int4, fp8, fp16)")
    parser.add_argument("--compare", nargs=2, metavar=("FILE_A", "FILE_B"), help="Compare two result files")
    args = parser.parse_args()

    if args.compare:
        compare(args.compare[0], args.compare[1])
    else:
        run_all(args.url, args.label)


if __name__ == "__main__":
    main()
```

---

## Verification

Run against current AWQ-4bit vLLM:
```text
cd /ganuda/scripts/model_eval && python3 quantization_benchmark.py --url http://localhost:8000 --label awq_int4
```

Later, after switching to FP8:
```text
python3 quantization_benchmark.py --url http://localhost:8000 --label fp8
python3 quantization_benchmark.py --compare /ganuda/reports/quantization/awq_int4_*.json /ganuda/reports/quantization/fp8_*.json
```

---

## Notes

- Uses temperature=0.0 for deterministic comparisons across runs
- 15 test cases total (5 per suite) — runs in ~3 minutes at 32 tok/s
- Multi-hop problems range from 3 to 5 hops (the known degradation zone for INT4)
- Does NOT require any model changes — just connects to existing vLLM endpoint
