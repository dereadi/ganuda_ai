# Jr Instruction: FP8 Baseline Benchmark (AWQ Current Model)

**Task ID:** FP8-BASELINE
**Kanban:** #1818
**Priority:** 2
**Sacred Fire Priority:** 45
**Story Points:** 8
**Assigned:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create a benchmark script that captures baseline performance of the CURRENT AWQ model on redfin vLLM (http://192.168.132.223:8000) before any FP8 migration. Three test suites:

1. **Multi-hop reasoning** (5 questions requiring chaining facts)
2. **Math accuracy** (5 arithmetic/logic problems with known answers)
3. **Retrieval quality** (5 questions about Cherokee AI Federation facts requiring precise recall)

Each response is scored correct/incorrect/partial using embedded rubrics, tokens/second is measured, and all results save to JSON for later FP8 comparison.

---

## Step 1: Create the FP8 baseline benchmark script

Create `/ganuda/scripts/model_eval/fp8_baseline_benchmark.py`

```python
#!/usr/bin/env python3
"""
FP8 Baseline Benchmark — AWQ Model Performance Capture

Runs 3 test suites (15 questions total) against the current AWQ model
on redfin vLLM to establish baselines before FP8 migration.

Reusable: pass --model-url and --model-name for later FP8 comparison.

Usage:
  python3 fp8_baseline_benchmark.py
  python3 fp8_baseline_benchmark.py --model-url http://192.168.132.223:8000 --model-name "qwen2.5-72b-instruct-awq"
  python3 fp8_baseline_benchmark.py --model-url http://192.168.132.223:8000 --model-name "qwen2.5-72b-instruct-fp8" --output /ganuda/reports/fp8_comparison.json
"""

import os
import json
import time
import argparse
from datetime import datetime

import requests

# Defaults
DEFAULT_URL = "http://192.168.132.223:8000"
DEFAULT_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"
DEFAULT_OUTPUT = "/ganuda/reports/fp8_baseline_awq.json"


def query_model(url, model, prompt, system=None, max_tokens=400, temperature=0.0):
    """Send a prompt to the vLLM OpenAI-compatible API and return response + metrics."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.time()
    try:
        resp = requests.post(
            f"{url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=180,
        )
        elapsed = time.time() - start
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
        prompt_tokens = data.get("usage", {}).get("prompt_tokens", 0)
        tok_s = round(completion_tokens / elapsed, 2) if elapsed > 0 else 0.0
        return {
            "content": content,
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
            "latency_s": round(elapsed, 3),
            "tok_s": tok_s,
        }
    except Exception as e:
        return {
            "content": f"ERROR: {e}",
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "latency_s": 0,
            "tok_s": 0.0,
        }


# ============================================================
# Scoring helper
# ============================================================

def score_response(content, correct_keywords, partial_keywords=None):
    """
    Score a response as correct / partial / incorrect.
    - correct: ALL correct_keywords found
    - partial: at least one correct_keyword found, or any partial_keyword found
    - incorrect: none found
    Returns: ("correct"|"partial"|"incorrect", detail_string)
    """
    content_lower = content.lower()
    correct_hits = [kw for kw in correct_keywords if kw.lower() in content_lower]
    partial_hits = []
    if partial_keywords:
        partial_hits = [kw for kw in partial_keywords if kw.lower() in content_lower]

    if len(correct_hits) == len(correct_keywords):
        return "correct", f"all {len(correct_keywords)} keywords matched"
    elif correct_hits or partial_hits:
        return "partial", f"{len(correct_hits)}/{len(correct_keywords)} correct, {len(partial_hits)} partial"
    else:
        return "incorrect", "no keywords matched"


# ============================================================
# SUITE 1: Multi-Hop Reasoning
# ============================================================

MULTI_HOP_QUESTIONS = [
    {
        "name": "causal_chain_3hop",
        "prompt": (
            "Fact 1: Deforestation causes soil erosion. "
            "Fact 2: Soil erosion causes river siltation. "
            "Fact 3: River siltation causes fish population decline. "
            "Question: If a region undergoes deforestation, what happens to its fish population and why? "
            "Answer in 2-3 sentences, tracing the full chain."
        ),
        "correct_keywords": ["deforestation", "erosion", "silt", "fish"],
        "partial_keywords": ["decline", "decrease", "reduce", "chain"],
    },
    {
        "name": "temporal_chain_3hop",
        "prompt": (
            "Maria started her PhD in 2015. She finished 5 years later. "
            "She took a 2-year postdoc after finishing. Then she became an assistant professor. "
            "What year did Maria become an assistant professor?"
        ),
        "correct_keywords": ["2022"],
        "partial_keywords": ["2020", "postdoc"],
    },
    {
        "name": "logical_ordering_4hop",
        "prompt": (
            "In a race: Alice finished before Bob. Charlie finished before Alice. "
            "Dave finished after Bob but before Eve. "
            "List all five runners in order from first to last."
        ),
        "correct_keywords": ["charlie"],
        "partial_keywords": ["alice", "bob", "dave", "eve"],
    },
    {
        "name": "transitive_property",
        "prompt": (
            "If A causes B, and B causes C, and C causes D, what does A cause? "
            "Additionally: if D prevents E, does A help or harm E? "
            "Explain your reasoning step by step."
        ),
        "correct_keywords": ["a causes d", "harm"],
        "partial_keywords": ["causes c", "prevents e", "chain", "transitive"],
    },
    {
        "name": "compound_inference",
        "prompt": (
            "A bakery uses 3 eggs per cake and 2 eggs per batch of cookies. "
            "They make 10 cakes and 15 batches of cookies on Monday. "
            "Eggs come in cartons of 12. "
            "How many full cartons do they need, and how many eggs are left over?"
        ),
        "correct_keywords": ["5"],
        "partial_keywords": ["60", "carton", "left over"],
    },
]


def run_multi_hop_suite(url, model):
    """Run multi-hop reasoning suite."""
    print("\n=== SUITE 1: Multi-Hop Reasoning (5 questions) ===")
    results = []
    system = "Answer precisely. Show your reasoning step by step, then give the final answer."

    for q in MULTI_HOP_QUESTIONS:
        print(f"  {q['name']}...", end=" ", flush=True)
        resp = query_model(url, model, q["prompt"], system=system)
        grade, detail = score_response(resp["content"], q["correct_keywords"], q["partial_keywords"])
        results.append({
            "name": q["name"],
            "grade": grade,
            "detail": detail,
            "tok_s": resp["tok_s"],
            "latency_s": resp["latency_s"],
            "completion_tokens": resp["completion_tokens"],
            "response_preview": resp["content"][:250],
        })
        print(f"{grade.upper()} ({detail}) [{resp['tok_s']} tok/s]")

    counts = {"correct": 0, "partial": 0, "incorrect": 0}
    for r in results:
        counts[r["grade"]] += 1
    avg_tok_s = round(sum(r["tok_s"] for r in results) / len(results), 2)

    print(f"  Summary: {counts['correct']} correct, {counts['partial']} partial, {counts['incorrect']} incorrect | avg {avg_tok_s} tok/s")
    return {"suite": "multi_hop_reasoning", "counts": counts, "avg_tok_s": avg_tok_s, "results": results}


# ============================================================
# SUITE 2: Math Accuracy
# ============================================================

MATH_QUESTIONS = [
    {
        "name": "multi_step_arithmetic",
        "prompt": "A store sells widgets for $12.50 each. A customer buys 7 widgets and pays with a $100 bill. How much change do they receive?",
        "correct_keywords": ["12.50", "12.5"],
        "partial_keywords": ["87.50", "87.5", "change"],
    },
    {
        "name": "percentage_discount",
        "prompt": "A laptop costs $1200. It is on sale for 15% off. Sales tax is 7%. What is the total cost after discount and tax?",
        "correct_keywords": ["1090.80", "1090.8"],
        "partial_keywords": ["1020", "180", "discount", "tax"],
    },
    {
        "name": "rate_work_problem",
        "prompt": "Painter A can paint a house in 6 hours. Painter B can paint the same house in 4 hours. Working together, how long does it take them? Express as hours and minutes.",
        "correct_keywords": ["2 hour", "24 min"],
        "partial_keywords": ["2.4", "12/5", "together"],
    },
    {
        "name": "sequence_sum",
        "prompt": "What is the sum of the first 20 terms of the arithmetic sequence: 3, 7, 11, 15, ...?",
        "correct_keywords": ["820"],
        "partial_keywords": ["common difference", "4", "arithmetic"],
    },
    {
        "name": "probability_basic",
        "prompt": "A bag contains 5 red balls, 3 blue balls, and 2 green balls. You draw 2 balls without replacement. What is the probability that both are red? Express as a fraction.",
        "correct_keywords": ["2/9"],
        "partial_keywords": ["20/90", "5/10", "4/9", "without replacement"],
    },
]


def run_math_suite(url, model):
    """Run math accuracy suite."""
    print("\n=== SUITE 2: Math Accuracy (5 questions) ===")
    results = []
    system = "Solve step by step. Show all work. State the final numerical answer clearly."

    for q in MATH_QUESTIONS:
        print(f"  {q['name']}...", end=" ", flush=True)
        resp = query_model(url, model, q["prompt"], system=system)
        grade, detail = score_response(resp["content"], q["correct_keywords"], q["partial_keywords"])
        results.append({
            "name": q["name"],
            "grade": grade,
            "detail": detail,
            "tok_s": resp["tok_s"],
            "latency_s": resp["latency_s"],
            "completion_tokens": resp["completion_tokens"],
            "response_preview": resp["content"][:250],
        })
        print(f"{grade.upper()} ({detail}) [{resp['tok_s']} tok/s]")

    counts = {"correct": 0, "partial": 0, "incorrect": 0}
    for r in results:
        counts[r["grade"]] += 1
    avg_tok_s = round(sum(r["tok_s"] for r in results) / len(results), 2)

    print(f"  Summary: {counts['correct']} correct, {counts['partial']} partial, {counts['incorrect']} incorrect | avg {avg_tok_s} tok/s")
    return {"suite": "math_accuracy", "counts": counts, "avg_tok_s": avg_tok_s, "results": results}


# ============================================================
# SUITE 3: Retrieval Quality (Cherokee AI Federation Facts)
# ============================================================

RETRIEVAL_QUESTIONS = [
    {
        "name": "federation_architecture",
        "prompt": (
            "In the Cherokee AI Federation, what is the role of the Council of Seven specialists? "
            "Name at least 3 specialist roles and describe their function."
        ),
        "correct_keywords": ["crawdad", "turtle", "coyote"],
        "partial_keywords": ["security", "seven generations", "trickster", "council", "specialist"],
    },
    {
        "name": "two_wolves_parable",
        "prompt": (
            "Tell the Cherokee parable of the Two Wolves. What is the moral, "
            "and how does it relate to AI alignment?"
        ),
        "correct_keywords": ["two wolves", "feed"],
        "partial_keywords": ["good", "evil", "grandfather", "choice", "alignment", "cherokee"],
    },
    {
        "name": "seven_generations",
        "prompt": (
            "Explain the Seven Generations principle from Cherokee philosophy. "
            "How would you apply it to a technology decision about data storage?"
        ),
        "correct_keywords": ["seven generation"],
        "partial_keywords": ["future", "long-term", "sustain", "descendant", "impact", "steward"],
    },
    {
        "name": "va_disability_combined",
        "prompt": (
            "A veteran has three service-connected conditions rated at 50%, 30%, and 20%. "
            "Using VA combined rating math (not simple addition), what is their combined rating? "
            "Show the step-by-step calculation."
        ),
        "correct_keywords": ["72", "70"],
        "partial_keywords": ["combined", "bilateral", "round", "not additive", "whole body"],
    },
    {
        "name": "cfr_nexus_letter",
        "prompt": (
            "What is a nexus letter in the context of VA disability claims? "
            "What must it contain to satisfy 38 CFR requirements?"
        ),
        "correct_keywords": ["nexus"],
        "partial_keywords": ["service connection", "medical opinion", "at least as likely", "physician", "38 cfr"],
    },
]


def run_retrieval_suite(url, model):
    """Run retrieval quality suite."""
    print("\n=== SUITE 3: Retrieval Quality - Cherokee AI Federation (5 questions) ===")
    results = []
    system = (
        "You are a knowledgeable assistant for the Cherokee AI Federation. "
        "Provide accurate, specific answers drawing on Cherokee cultural knowledge "
        "and VA disability claims expertise."
    )

    for q in RETRIEVAL_QUESTIONS:
        print(f"  {q['name']}...", end=" ", flush=True)
        resp = query_model(url, model, q["prompt"], system=system)
        grade, detail = score_response(resp["content"], q["correct_keywords"], q["partial_keywords"])
        results.append({
            "name": q["name"],
            "grade": grade,
            "detail": detail,
            "tok_s": resp["tok_s"],
            "latency_s": resp["latency_s"],
            "completion_tokens": resp["completion_tokens"],
            "response_preview": resp["content"][:250],
        })
        print(f"{grade.upper()} ({detail}) [{resp['tok_s']} tok/s]")

    counts = {"correct": 0, "partial": 0, "incorrect": 0}
    for r in results:
        counts[r["grade"]] += 1
    avg_tok_s = round(sum(r["tok_s"] for r in results) / len(results), 2)

    print(f"  Summary: {counts['correct']} correct, {counts['partial']} partial, {counts['incorrect']} incorrect | avg {avg_tok_s} tok/s")
    return {"suite": "retrieval_quality", "counts": counts, "avg_tok_s": avg_tok_s, "results": results}


# ============================================================
# Orchestration
# ============================================================

def run_benchmark(url, model, output_path):
    """Run all three suites and save results."""
    timestamp = datetime.now().isoformat()
    print(f"\nFP8 Baseline Benchmark")
    print(f"Timestamp: {timestamp}")
    print(f"Endpoint:  {url}")
    print(f"Model:     {model}")
    print("=" * 60)

    suite1 = run_multi_hop_suite(url, model)
    suite2 = run_math_suite(url, model)
    suite3 = run_retrieval_suite(url, model)

    # Aggregate tokens/sec across all suites
    all_tok_s = []
    for suite in [suite1, suite2, suite3]:
        for r in suite["results"]:
            if r["tok_s"] > 0:
                all_tok_s.append(r["tok_s"])
    avg_tok_s_overall = round(sum(all_tok_s) / len(all_tok_s), 2) if all_tok_s else 0.0

    # Count totals
    total_counts = {"correct": 0, "partial": 0, "incorrect": 0}
    for suite in [suite1, suite2, suite3]:
        for grade in ["correct", "partial", "incorrect"]:
            total_counts[grade] += suite["counts"][grade]

    results = {
        "timestamp": timestamp,
        "model_url": url,
        "model_name": model,
        "avg_tokens_per_second": avg_tok_s_overall,
        "total_questions": 15,
        "total_counts": total_counts,
        "suites": {
            "multi_hop_reasoning": suite1,
            "math_accuracy": suite2,
            "retrieval_quality": suite3,
        },
    }

    print(f"\n{'=' * 60}")
    print(f"OVERALL RESULTS")
    print(f"  Correct:   {total_counts['correct']}/15")
    print(f"  Partial:   {total_counts['partial']}/15")
    print(f"  Incorrect: {total_counts['incorrect']}/15")
    print(f"  Avg tok/s: {avg_tok_s_overall}")
    print(f"{'=' * 60}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="FP8 Baseline Benchmark - Captures AWQ model performance for FP8 comparison"
    )
    parser.add_argument(
        "--model-url",
        default=DEFAULT_URL,
        help=f"vLLM endpoint URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL,
        help=f"Model name for API requests (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    run_benchmark(args.model_url, args.model_name, args.output)


if __name__ == "__main__":
    main()
```

---

## Verification

Run against the current AWQ model on redfin:
```text
python3 /ganuda/scripts/model_eval/fp8_baseline_benchmark.py
```

Later, run against FP8 for comparison:
```text
python3 /ganuda/scripts/model_eval/fp8_baseline_benchmark.py --model-url http://192.168.132.223:8000 --model-name "/ganuda/models/qwen2.5-72b-instruct-fp8" --output /ganuda/reports/fp8_comparison.json
```

Expected output: Runs 15 questions across 3 suites, prints per-question scores with tok/s, saves JSON to `/ganuda/reports/fp8_baseline_awq.json`.

---

## Notes

- Uses `temperature=0.0` for deterministic reproducibility across runs
- Only dependency is `requests` (stdlib otherwise)
- Scoring rubric uses keyword matching (correct = all keywords, partial = some, incorrect = none) -- no LLM-as-judge
- `--model-url` and `--model-name` flags make the script reusable for any model endpoint
- 15 test cases total, estimated runtime ~2-3 minutes at 32 tok/s
- Retrieval suite includes Cherokee cultural knowledge AND VetAssist CFR questions to test domain-specific recall
