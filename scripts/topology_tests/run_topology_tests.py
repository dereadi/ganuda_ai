#!/usr/bin/env python3
"""
Cherokee AI Multi-Agent Topology Tests
Validates Google/MIT Multi-Agent Scaling Study (Dec 2025)

Tests:
1. Sequential: Single Jr vs Chained Jrs
2. Parallel: Multi-Jr vs Sequential Single
3. Error Amplification: Independent vs Decentralized vs Centralized
"""

import requests
import time
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

VLLM_URL = "http://192.168.132.223:8000/v1/chat/completions"
RESULTS_FILE = "/ganuda/logs/topology_test_results.json"

def get_model():
    models = requests.get("http://192.168.132.223:8000/v1/models", timeout=10).json()
    return models["data"][0]["id"]

# ============================================================
# TEST 1: SEQUENTIAL - Single Deep Think vs Chained Jrs
# Expected: Chain shows -70% performance vs single agent
# ============================================================

SEQUENTIAL_TASK = """Analyze the following scenario and provide recommendations:

The Cherokee AI Federation has 6 nodes: redfin (96GB GPU), bluefin (124GB RAM services), 
greenfin (124GB RAM workers), sasass/sasass2 (Mac Studios), bmasass (air-gapped).

Question: If we need to add a new monitoring daemon that checks all nodes every 5 minutes,
which node should host it and why? Consider: CPU load, network position, failure modes.

Provide a structured analysis with:
1. Options considered
2. Pros/cons of each
3. Final recommendation with justification"""

def test_single_deep_think():
    """Single Jr with extended thinking space."""
    model = get_model()
    start = time.time()
    
    response = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": """You are a deep-thinking infrastructure Jr.
Analyze comprehensively before responding. Consider multiple angles.
Provide structured analysis with clear recommendations."""},
            {"role": "user", "content": SEQUENTIAL_TASK}
        ],
        "max_tokens": 1500,
        "temperature": 0.3
    }, timeout=120)
    
    elapsed = time.time() - start
    result = response.json()["choices"][0]["message"]["content"]
    tokens = response.json()["usage"]["completion_tokens"]
    
    return {
        "method": "single_deep_think",
        "time_seconds": round(elapsed, 2),
        "tokens_generated": tokens,
        "tokens_per_second": round(tokens / elapsed, 1),
        "output_preview": result[:500] + "..."
    }

def test_chained_3_jrs():
    """Three Jrs in chain: analyst -> reviewer -> synthesizer."""
    model = get_model()
    start = time.time()
    total_tokens = 0
    
    # Jr 1: Analyst
    r1 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are analyst_jr. Identify and analyze the options."},
            {"role": "user", "content": SEQUENTIAL_TASK}
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }, timeout=60)
    analysis = r1.json()["choices"][0]["message"]["content"]
    total_tokens += r1.json()["usage"]["completion_tokens"]
    
    # Jr 2: Reviewer
    r2 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are reviewer_jr. Review and critique the analysis."},
            {"role": "user", "content": f"Original task: {SEQUENTIAL_TASK}\n\nAnalyst said:\n{analysis}"}
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }, timeout=60)
    review = r2.json()["choices"][0]["message"]["content"]
    total_tokens += r2.json()["usage"]["completion_tokens"]
    
    # Jr 3: Synthesizer
    r3 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are synthesizer_jr. Create final recommendation."},
            {"role": "user", "content": f"Task: {SEQUENTIAL_TASK}\n\nAnalysis:\n{analysis}\n\nReview:\n{review}"}
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }, timeout=60)
    synthesis = r3.json()["choices"][0]["message"]["content"]
    total_tokens += r3.json()["usage"]["completion_tokens"]
    
    elapsed = time.time() - start
    
    return {
        "method": "chained_3_jr",
        "time_seconds": round(elapsed, 2),
        "tokens_generated": total_tokens,
        "tokens_per_second": round(total_tokens / elapsed, 1),
        "stages": {
            "analysis_preview": analysis[:200] + "...",
            "review_preview": review[:200] + "...",
            "synthesis_preview": synthesis[:200] + "..."
        }
    }

# ============================================================
# TEST 2: PARALLEL - Multi-Jr vs Sequential Single
# Expected: Parallel shows +80% improvement
# ============================================================

NODES = [
    ("bluefin", "192.168.132.222"),
    ("redfin", "192.168.132.223"),
    ("greenfin", "192.168.132.224"),
    ("sasass", "192.168.132.241"),
    ("sasass2", "192.168.132.242"),
]

def check_single_node(name, ip):
    """Check one node's status."""
    cmd = f"ssh -o ConnectTimeout=5 dereadi@{ip} 'hostname && uptime && free -h | head -2' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    return (name, result.stdout.strip() if result.returncode == 0 else f"ERROR: {result.stderr}")

def test_sequential_node_check():
    """Single process checks each node sequentially."""
    start = time.time()
    results = {}
    
    for name, ip in NODES:
        name, output = check_single_node(name, ip)
        results[name] = output
    
    elapsed = time.time() - start
    return {
        "method": "sequential_single",
        "time_seconds": round(elapsed, 2),
        "nodes_checked": len([r for r in results.values() if not r.startswith("ERROR")]),
        "results_preview": {k: v[:100] for k, v in results.items()}
    }

def test_parallel_node_check():
    """Parallel workers check all nodes simultaneously."""
    start = time.time()
    results = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_single_node, name, ip): name for name, ip in NODES}
        for future in as_completed(futures):
            name, output = future.result()
            results[name] = output
    
    elapsed = time.time() - start
    return {
        "method": "parallel_multi",
        "time_seconds": round(elapsed, 2),
        "nodes_checked": len([r for r in results.values() if not r.startswith("ERROR")]),
        "results_preview": {k: v[:100] for k, v in results.items()}
    }

# ============================================================
# TEST 3: ERROR AMPLIFICATION BY TOPOLOGY
# Expected: Independent 17x, Decentralized 7.8x, Centralized 4.4x
# ============================================================

def get_ground_truth_memory():
    """Get actual memory usage from redfin for verification."""
    result = subprocess.run(
        "free -h | grep Mem | awk '{print $3}'",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip()

FACTUAL_QUESTION = "What is the exact used memory on redfin right now? Just state the number with units."

def test_independent_voting(num_agents=3):
    """Multiple Jrs answer independently, no communication."""
    model = get_model()
    answers = []
    start = time.time()
    
    for i in range(num_agents):
        r = requests.post(VLLM_URL, json={
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are independent_jr_{i}. Answer precisely and concisely."},
                {"role": "user", "content": FACTUAL_QUESTION}
            ],
            "max_tokens": 100,
            "temperature": 0.5  # Some variance
        }, timeout=30)
        answers.append(r.json()["choices"][0]["message"]["content"])
    
    elapsed = time.time() - start
    return {
        "method": "independent_voting",
        "time_seconds": round(elapsed, 2),
        "num_agents": num_agents,
        "answers": answers,
        "consensus": len(set(answers)) == 1
    }

def test_decentralized_debate():
    """Jrs debate with each other, no orchestrator validation."""
    model = get_model()
    start = time.time()
    
    # Jr 1 answers
    r1 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are debate_jr_1. Answer the question."},
            {"role": "user", "content": FACTUAL_QUESTION}
        ],
        "max_tokens": 100,
        "temperature": 0.5
    }, timeout=30)
    a1 = r1.json()["choices"][0]["message"]["content"]
    
    # Jr 2 sees Jr 1's answer and can agree or disagree
    r2 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are debate_jr_2. Review the answer and provide your own."},
            {"role": "user", "content": f"Question: {FACTUAL_QUESTION}\n\nJr 1 said: {a1}\n\nDo you agree? Provide your answer."}
        ],
        "max_tokens": 150,
        "temperature": 0.5
    }, timeout=30)
    a2 = r2.json()["choices"][0]["message"]["content"]
    
    # Jr 3 synthesizes without validation authority
    r3 = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are debate_jr_3. Synthesize the final answer."},
            {"role": "user", "content": f"Question: {FACTUAL_QUESTION}\n\nJr 1: {a1}\n\nJr 2: {a2}\n\nSynthesize the best answer."}
        ],
        "max_tokens": 100,
        "temperature": 0.3
    }, timeout=30)
    a3 = r3.json()["choices"][0]["message"]["content"]
    
    elapsed = time.time() - start
    return {
        "method": "decentralized_debate",
        "time_seconds": round(elapsed, 2),
        "answers": {"jr1": a1, "jr2": a2, "jr3_synthesis": a3}
    }

def test_centralized_orchestrator():
    """Jrs report to orchestrator who validates and aggregates."""
    model = get_model()
    start = time.time()
    
    # Collect from independent Jrs
    answers = []
    for i in range(3):
        r = requests.post(VLLM_URL, json={
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are worker_jr_{i}. Answer precisely."},
                {"role": "user", "content": FACTUAL_QUESTION}
            ],
            "max_tokens": 100,
            "temperature": 0.5
        }, timeout=30)
        answers.append(r.json()["choices"][0]["message"]["content"])
    
    # Orchestrator validates (with actual data check capability)
    ground_truth = get_ground_truth_memory()
    
    orchestrator_prompt = f"""You are the TPM orchestrator with validation authority.

Question: {FACTUAL_QUESTION}

Ground truth from system: {ground_truth}

Three Jrs provided these answers:
- Jr 0: {answers[0]}
- Jr 1: {answers[1]}
- Jr 2: {answers[2]}

Validate these answers against ground truth. Which Jr(s) were correct?
Provide the single correct answer."""

    r_orch = requests.post(VLLM_URL, json={
        "model": model,
        "messages": [
            {"role": "system", "content": "You are TPM orchestrator. Validate Jr answers against ground truth."},
            {"role": "user", "content": orchestrator_prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }, timeout=30)
    
    elapsed = time.time() - start
    return {
        "method": "centralized_orchestrator",
        "time_seconds": round(elapsed, 2),
        "ground_truth": ground_truth,
        "jr_answers": answers,
        "orchestrator_validation": r_orch.json()["choices"][0]["message"]["content"]
    }

# ============================================================
# MAIN TEST RUNNER
# ============================================================

def run_all_tests(iterations=3):
    """Run all topology tests and collect results."""
    print("=" * 60)
    print("CHEROKEE AI TOPOLOGY TESTS")
    print(f"Validating Google/MIT Multi-Agent Scaling Study")
    print(f"Date: {datetime.now().isoformat()}")
    print("=" * 60)
    
    model = get_model()
    print(f"\nModel: {model}\n")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "iterations": iterations,
        "tests": {}
    }
    
    # TEST 1: Sequential
    print("\n>>> TEST 1: SEQUENTIAL (Single vs Chain)")
    print("-" * 40)
    
    single_results = []
    chain_results = []
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        print("    Running single deep think...")
        single = test_single_deep_think()
        single_results.append(single)
        print(f"    -> {single['time_seconds']}s, {single['tokens_generated']} tokens")
        
        print("    Running chained 3 Jrs...")
        chain = test_chained_3_jrs()
        chain_results.append(chain)
        print(f"    -> {chain['time_seconds']}s, {chain['tokens_generated']} tokens")
    
    avg_single = sum(r['time_seconds'] for r in single_results) / iterations
    avg_chain = sum(r['time_seconds'] for r in chain_results) / iterations
    
    all_results["tests"]["sequential"] = {
        "single_avg_time": round(avg_single, 2),
        "chain_avg_time": round(avg_chain, 2),
        "chain_overhead_percent": round((avg_chain - avg_single) / avg_single * 100, 1),
        "single_results": single_results,
        "chain_results": chain_results
    }
    
    print(f"\n  RESULT: Single={avg_single:.1f}s, Chain={avg_chain:.1f}s")
    print(f"  Chain overhead: {all_results['tests']['sequential']['chain_overhead_percent']}%")
    print(f"  (Google/MIT predicted: chain -70% slower)")
    
    # TEST 2: Parallel
    print("\n>>> TEST 2: PARALLEL (Multi vs Sequential)")
    print("-" * 40)
    
    seq_results = []
    par_results = []
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        print("    Running sequential node check...")
        seq = test_sequential_node_check()
        seq_results.append(seq)
        print(f"    -> {seq['time_seconds']}s, {seq['nodes_checked']} nodes")
        
        print("    Running parallel node check...")
        par = test_parallel_node_check()
        par_results.append(par)
        print(f"    -> {par['time_seconds']}s, {par['nodes_checked']} nodes")
    
    avg_seq = sum(r['time_seconds'] for r in seq_results) / iterations
    avg_par = sum(r['time_seconds'] for r in par_results) / iterations
    
    all_results["tests"]["parallel"] = {
        "sequential_avg_time": round(avg_seq, 2),
        "parallel_avg_time": round(avg_par, 2),
        "speedup_factor": round(avg_seq / avg_par, 2) if avg_par > 0 else 0,
        "improvement_percent": round((avg_seq - avg_par) / avg_seq * 100, 1),
        "sequential_results": seq_results,
        "parallel_results": par_results
    }
    
    print(f"\n  RESULT: Sequential={avg_seq:.1f}s, Parallel={avg_par:.1f}s")
    print(f"  Speedup: {all_results['tests']['parallel']['speedup_factor']}x")
    print(f"  (Google/MIT predicted: +80% improvement)")
    
    # TEST 3: Error Amplification
    print("\n>>> TEST 3: ERROR AMPLIFICATION BY TOPOLOGY")
    print("-" * 40)
    
    ind_results = []
    dec_results = []
    cen_results = []
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        print("    Running independent voting...")
        ind = test_independent_voting()
        ind_results.append(ind)
        
        print("    Running decentralized debate...")
        dec = test_decentralized_debate()
        dec_results.append(dec)
        
        print("    Running centralized orchestrator...")
        cen = test_centralized_orchestrator()
        cen_results.append(cen)
    
    all_results["tests"]["error_amplification"] = {
        "independent_results": ind_results,
        "decentralized_results": dec_results,
        "centralized_results": cen_results
    }
    
    print(f"\n  Results collected. Manual review needed for accuracy.")
    print(f"  (Google/MIT: Independent 17x, Decentralized 7.8x, Centralized 4.4x)")
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"RESULTS SAVED TO: {RESULTS_FILE}")
    print(f"{'=' * 60}")
    
    return all_results

if __name__ == "__main__":
    results = run_all_tests(iterations=3)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY vs GOOGLE/MIT PREDICTIONS")
    print("=" * 60)
    
    seq = results["tests"]["sequential"]
    print(f"\nTest 1 - Sequential Chain Overhead:")
    print(f"  Measured: {seq['chain_overhead_percent']}%")
    print(f"  Predicted: Chain should be ~70% slower (more overhead)")
    
    par = results["tests"]["parallel"]
    print(f"\nTest 2 - Parallel Speedup:")
    print(f"  Measured: {par['speedup_factor']}x ({par['improvement_percent']}% improvement)")
    print(f"  Predicted: +80% improvement")
    
    print(f"\nTest 3 - Error Amplification:")
    print(f"  See {RESULTS_FILE} for detailed analysis")
    print(f"  Predicted: Independent 17x > Decentralized 7.8x > Centralized 4.4x")
