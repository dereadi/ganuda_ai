"""
RAG Evaluation Framework — Cherokee AI Federation

Evaluates retrieval quality using golden Q&A test cases against
the thermal memory semantic search pipeline.

Council Vote #33e50dc466de520e — Phase 2d.

Usage:
    python3 rag_eval.py              # Run all test cases
    python3 rag_eval.py --verbose    # Show individual results
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, "/ganuda")

import psycopg2
import psycopg2.extras
import requests

from lib.secrets_loader import get_db_config

logger = logging.getLogger(__name__)

EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/embed")
DB_CONFIG = get_db_config()

# Golden test cases: queries with known relevant memory IDs
# These should be curated from real tribal knowledge
GOLDEN_TESTS = [
    {
        "query": "power outage recovery procedure",
        "relevant_keywords": ["power", "outage", "recovery", "systemd", "restart"],
        "expected_tags": ["infrastructure"],
    },
    {
        "query": "Jr executor search replace instruction format",
        "relevant_keywords": ["SEARCH", "REPLACE", "executor", "instruction"],
        "expected_tags": ["jr_agents"],
    },
    {
        "query": "vLLM model configuration Qwen",
        "relevant_keywords": ["vllm", "qwen", "model", "awq", "marlin"],
        "expected_tags": ["llm_gateway", "infrastructure"],
    },
    {
        "query": "camera calibration lens distortion",
        "relevant_keywords": ["camera", "calibration", "lens", "distortion"],
        "expected_tags": ["infrastructure"],
    },
    {
        "query": "council vote democratic approval",
        "relevant_keywords": ["council", "vote", "approve", "deliberat"],
        "expected_tags": ["council"],
    },
    {
        "query": "telegram bot semantic memory",
        "relevant_keywords": ["telegram", "bot", "semantic", "memory"],
        "expected_tags": ["telegram", "thermal_memory"],
    },
    {
        "query": "nftables firewall configuration",
        "relevant_keywords": ["nftables", "firewall", "nft", "drop", "accept"],
        "expected_tags": ["infrastructure"],
    },
    {
        "query": "embedding service BGE large",
        "relevant_keywords": ["embedding", "bge", "1024", "greenfin", "8003"],
        "expected_tags": ["infrastructure"],
    },
]


def get_embedding(text: str) -> list:
    """Get BGE-large embedding."""
    resp = requests.post(EMBEDDING_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "embedding" in data:
        return data["embedding"]
    return data.get("embeddings", [[]])[0]


def retrieve_memories(query: str, limit: int = 10) -> List[Dict]:
    """Retrieve memories using semantic search."""
    embedding = get_embedding(query)
    if not embedding:
        return []

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT id, original_content, temperature_score, keywords, tags,
               1 - (embedding <=> %s::vector) as similarity
        FROM thermal_memory_archive
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (embedding, embedding, limit))

    results = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results


def evaluate_single(test_case: dict, results: List[Dict], verbose: bool = False) -> Dict:
    """Evaluate a single test case against retrieved results."""
    query = test_case["query"]
    keywords = test_case["relevant_keywords"]
    expected_tags = test_case.get("expected_tags", [])

    hits = 0
    tag_hits = 0
    reciprocal_rank = 0.0

    for i, r in enumerate(results):
        content_lower = r["original_content"].lower()
        kw_match = sum(1 for kw in keywords if kw.lower() in content_lower)
        tag_match = any(t in (r.get("tags") or []) for t in expected_tags)

        if kw_match >= 2:
            hits += 1
            if reciprocal_rank == 0:
                reciprocal_rank = 1.0 / (i + 1)
        if tag_match:
            tag_hits += 1

        if verbose:
            sim = r.get("similarity", 0)
            snippet = r["original_content"][:80].replace("\n", " ")
            print(f"  [{i+1}] sim={sim:.3f} kw={kw_match} tag={'Y' if tag_match else 'N'} | {snippet}")

    precision_at_5 = hits / min(5, len(results)) if results else 0
    recall = min(1.0, hits / 3)  # Assume at least 3 relevant docs exist

    return {
        "query": query,
        "hits": hits,
        "precision_at_5": round(precision_at_5, 3),
        "recall": round(recall, 3),
        "mrr": round(reciprocal_rank, 3),
        "tag_precision": round(tag_hits / len(results), 3) if results else 0,
    }


def run_evaluation(verbose: bool = False) -> Dict:
    """Run full evaluation suite."""
    print(f"RAG Evaluation — {len(GOLDEN_TESTS)} test cases")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    all_results = []

    for tc in GOLDEN_TESTS:
        if verbose:
            print(f"\nQuery: {tc['query']}")
        retrieved = retrieve_memories(tc["query"], limit=10)
        metrics = evaluate_single(tc, retrieved, verbose=verbose)
        all_results.append(metrics)

        if not verbose:
            status = "PASS" if metrics["mrr"] > 0 else "MISS"
            print(f"  [{status}] P@5={metrics['precision_at_5']:.2f} MRR={metrics['mrr']:.2f} | {tc['query']}")

    # Aggregate metrics
    avg_precision = sum(r["precision_at_5"] for r in all_results) / len(all_results)
    avg_recall = sum(r["recall"] for r in all_results) / len(all_results)
    avg_mrr = sum(r["mrr"] for r in all_results) / len(all_results)
    pass_rate = sum(1 for r in all_results if r["mrr"] > 0) / len(all_results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "test_count": len(GOLDEN_TESTS),
        "avg_precision_at_5": round(avg_precision, 3),
        "avg_recall": round(avg_recall, 3),
        "avg_mrr": round(avg_mrr, 3),
        "pass_rate": round(pass_rate, 3),
        "individual_results": all_results,
    }

    print("\n" + "=" * 60)
    print(f"Avg Precision@5: {avg_precision:.3f}")
    print(f"Avg Recall:      {avg_recall:.3f}")
    print(f"Avg MRR:         {avg_mrr:.3f}")
    print(f"Pass Rate:       {pass_rate:.0%}")

    # Save results
    report_path = "/ganuda/reports/rag_eval"
    os.makedirs(report_path, exist_ok=True)
    report_file = f"{report_path}/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults saved: {report_file}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Evaluation Framework")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    run_evaluation(verbose=args.verbose)