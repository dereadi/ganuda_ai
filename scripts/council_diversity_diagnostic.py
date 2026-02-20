#!/usr/bin/env python3
"""
Council Embedding Diversity Diagnostic

Measures cosine similarity between specialist responses in historical council votes
to detect spectral convergence (SD-MoE spectral bias pattern).

Usage: python3 council_diversity_diagnostic.py [--limit N] [--threshold 0.85]
"""

import os
import sys
import json
import argparse
import requests
import numpy as np
import psycopg2
from itertools import combinations
from datetime import datetime

# BGE-large embedding endpoint on greenfin
EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/v1/embeddings")
EMBEDDING_MODEL = "bge-large-en-v1.5"

# Database
DB_HOST = os.environ.get("DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("DB_NAME", "zammad_production")
DB_USER = os.environ.get("DB_USER", "claude")
DB_PASS = os.environ.get("DB_PASS", "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE")


def get_embedding(text: str) -> list:
    """Get BGE-large embedding from greenfin."""
    resp = requests.post(EMBEDDING_URL, json={
        "texts": [text[:4000]]  # Truncate to avoid token limits
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def fetch_council_votes(limit: int = 50):
    """Fetch recent council votes with specialist responses."""
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT audit_hash, question, responses::text, voted_at
        FROM council_votes
        WHERE responses IS NOT NULL
          AND responses::text != 'null'
          AND responses::text != '{}'
        ORDER BY voted_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def analyze_vote(audit_hash: str, question: str, responses_json: str) -> dict:
    """Analyze embedding diversity for a single council vote."""
    try:
        responses = json.loads(responses_json) if isinstance(responses_json, str) else responses_json
    except (json.JSONDecodeError, TypeError):
        return None

    if not responses or not isinstance(responses, (dict, list)):
        return None

    # Extract specialist response texts
    specialist_texts = {}
    if isinstance(responses, dict):
        for spec_id, resp in responses.items():
            if isinstance(resp, str):
                specialist_texts[spec_id] = resp
            elif isinstance(resp, dict) and 'response' in resp:
                specialist_texts[spec_id] = resp['response']
    elif isinstance(responses, list):
        for r in responses:
            if isinstance(r, dict):
                name = r.get('name', r.get('specialist_id', 'unknown'))
                text = r.get('response', r.get('text', ''))
                if text:
                    specialist_texts[name] = text

    if len(specialist_texts) < 2:
        return None

    # Get embeddings for each specialist response
    embeddings = {}
    for spec_id, text in specialist_texts.items():
        try:
            embeddings[spec_id] = get_embedding(text)
        except Exception as e:
            print(f"  Warning: Failed to embed {spec_id}: {e}", file=sys.stderr)

    if len(embeddings) < 2:
        return None

    # Compute pairwise cosine similarities
    pairs = list(combinations(embeddings.keys(), 2))
    similarities = []
    pair_details = []
    for s1, s2 in pairs:
        sim = cosine_similarity(embeddings[s1], embeddings[s2])
        similarities.append(sim)
        pair_details.append({"pair": f"{s1}-{s2}", "cosine_sim": round(sim, 4)})

    return {
        "audit_hash": audit_hash,
        "question": question[:100],
        "num_specialists": len(embeddings),
        "num_pairs": len(pairs),
        "mean_similarity": round(float(np.mean(similarities)), 4),
        "max_similarity": round(float(np.max(similarities)), 4),
        "min_similarity": round(float(np.min(similarities)), 4),
        "std_similarity": round(float(np.std(similarities)), 4),
        "pairs": sorted(pair_details, key=lambda x: -x["cosine_sim"])
    }


def main():
    parser = argparse.ArgumentParser(description="Council Embedding Diversity Diagnostic")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent votes to analyze")
    parser.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold for convergence warning")
    args = parser.parse_args()

    print(f"Council Embedding Diversity Diagnostic")
    print(f"{'=' * 60}")
    print(f"Analyzing last {args.limit} council votes")
    print(f"Convergence threshold: {args.threshold}")
    print()

    votes = fetch_council_votes(args.limit)
    print(f"Found {len(votes)} votes with specialist responses")
    print()

    all_means = []
    convergence_warnings = []

    for audit_hash, question, responses_json, voted_at in votes:
        print(f"Vote {audit_hash} ({voted_at}):")
        result = analyze_vote(audit_hash, question, responses_json)
        if result is None:
            print("  Skipped (no parseable responses)")
            continue

        all_means.append(result["mean_similarity"])
        print(f"  Question: {result['question']}...")
        print(f"  Specialists: {result['num_specialists']}, Pairs: {result['num_pairs']}")
        print(f"  Mean similarity: {result['mean_similarity']}")
        print(f"  Range: [{result['min_similarity']}, {result['max_similarity']}]")

        # Flag high-similarity pairs
        high_sim = [p for p in result["pairs"] if p["cosine_sim"] > args.threshold]
        if high_sim:
            convergence_warnings.append(result)
            print(f"  *** CONVERGENCE WARNING: {len(high_sim)} pairs above {args.threshold} ***")
            for p in high_sim:
                print(f"    {p['pair']}: {p['cosine_sim']}")
        print()

    # Summary
    print(f"{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    if all_means:
        print(f"Votes analyzed: {len(all_means)}")
        print(f"Overall mean pairwise similarity: {np.mean(all_means):.4f}")
        print(f"Overall std: {np.std(all_means):.4f}")
        print(f"Convergence warnings: {len(convergence_warnings)} of {len(all_means)} votes")
        if np.mean(all_means) > args.threshold:
            print(f"\n*** SPECTRAL OVERLAP DETECTED ***")
            print(f"Mean specialist similarity ({np.mean(all_means):.4f}) exceeds threshold ({args.threshold})")
            print(f"Council specialists may be producing redundant responses.")
            print(f"Consider: orthogonal prompt redesign per SD-MoE (arXiv:2602.12556)")
        elif np.mean(all_means) > 0.75:
            print(f"\nModerate convergence detected. Monitor for trend.")
        else:
            print(f"\nHealthy diversity. Specialists producing genuinely different perspectives.")
    else:
        print("No votes with parseable specialist responses found.")


if __name__ == "__main__":
    main()