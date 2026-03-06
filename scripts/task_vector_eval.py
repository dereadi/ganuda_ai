#!/usr/bin/env python3
"""Task Vector Merging Evaluation: TIES/DARE merge of LoRA adapters.
Usage: python3 task_vector_eval.py --adapter1 /path/a --adapter2 /path/b --output /path/merged"""

import argparse
import json
import os
from datetime import datetime

import numpy as np

def load_weights(path):
    weights = {}
    for f in os.listdir(path):
        if f.endswith(".npy"):
            weights[f.replace(".npy", "")] = np.load(os.path.join(path, f))
    return weights

def ties_merge(w1, w2, trim_pct=0.2):
    """TIES: Trim low-magnitude, elect sign by majority, disjoint merge."""
    merged = {}
    all_keys = set(list(w1.keys()) + list(w2.keys()))
    for key in all_keys:
        a = w1.get(key, np.zeros_like(w2.get(key, np.zeros(1))))
        b = w2.get(key, np.zeros_like(w1.get(key, np.zeros(1))))
        if a.shape != b.shape:
            merged[key] = a if np.linalg.norm(a) > np.linalg.norm(b) else b
            continue
        thresh_a = np.percentile(np.abs(a), trim_pct * 100)
        thresh_b = np.percentile(np.abs(b), trim_pct * 100)
        a_trimmed = np.where(np.abs(a) > thresh_a, a, 0)
        b_trimmed = np.where(np.abs(b) > thresh_b, b, 0)
        sign_votes = np.sign(a_trimmed) + np.sign(b_trimmed)
        elected_sign = np.sign(sign_votes)
        elected_sign[elected_sign == 0] = np.sign(a_trimmed[elected_sign == 0])
        magnitudes = (np.abs(a_trimmed) + np.abs(b_trimmed)) / 2
        merged[key] = elected_sign * magnitudes
    return merged

def compute_merge_stats(w1, w2, merged):
    stats = {}
    for key in merged:
        a = w1.get(key, np.zeros_like(merged[key]))
        b = w2.get(key, np.zeros_like(merged[key]))
        m = merged[key]
        sign_agree = np.mean(np.sign(a) == np.sign(b)) if a.size > 0 else 0
        sparsity = np.mean(m == 0) if m.size > 0 else 0
        stats[key] = {
            "shape": list(m.shape),
            "sign_agreement": round(float(sign_agree), 4),
            "merged_sparsity": round(float(sparsity), 4),
            "norm_a": round(float(np.linalg.norm(a)), 4),
            "norm_b": round(float(np.linalg.norm(b)), 4),
            "norm_merged": round(float(np.linalg.norm(m)), 4)
        }
    return stats

def main():
    parser = argparse.ArgumentParser(description="TIES merge evaluation")
    parser.add_argument("--adapter1", required=True)
    parser.add_argument("--adapter2", required=True)
    parser.add_argument("--output", default="/ganuda/reports/task-vector-merge-eval.json")
    parser.add_argument("--trim", type=float, default=0.2)
    args = parser.parse_args()
    w1 = load_weights(args.adapter1)
    w2 = load_weights(args.adapter2)
    if not w1 or not w2:
        print("Error: no .npy weight files found in adapter directories")
        return
    merged = ties_merge(w1, w2, trim_pct=args.trim)
    stats = compute_merge_stats(w1, w2, merged)
    report = {
        "generated_at": datetime.now().isoformat(),
        "adapter1": args.adapter1,
        "adapter2": args.adapter2,
        "trim_pct": args.trim,
        "layers_merged": len(merged),
        "layer_stats": stats
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Merge report: {args.output}")
    print(f"Layers merged: {len(merged)}")
    mean_agree = np.mean([s["sign_agreement"] for s in stats.values()])
    print(f"Mean sign agreement: {mean_agree:.4f}")

if __name__ == "__main__":
    main()