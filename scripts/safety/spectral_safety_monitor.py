#!/usr/bin/env python3
"""Spectral Safety Monitor: SVD analysis of LoRA weight deltas.
Detects anomalous weight changes in fine-tuned adapters.
Usage: python3 spectral_safety_monitor.py /path/to/lora/adapter"""

import json
import os
import sys
from datetime import datetime

import numpy as np

def load_adapter_weights(adapter_path):
    """Load LoRA adapter weights from safetensors or numpy files."""
    weights = {}
    for fname in os.listdir(adapter_path):
        if fname.endswith(".npy"):
            key = fname.replace(".npy", "")
            weights[key] = np.load(os.path.join(adapter_path, fname))
        elif fname.endswith(".safetensors"):
            try:
                from safetensors.numpy import load_file
                st_weights = load_file(os.path.join(adapter_path, fname))
                weights.update(st_weights)
            except ImportError:
                print(f"Warning: safetensors not installed, skipping {fname}")
    return weights

def analyze_layer(name, weight_matrix):
    """Perform SVD analysis on a single weight matrix."""
    if weight_matrix.ndim != 2:
        return None
    try:
        U, S, Vt = np.linalg.svd(weight_matrix, full_matrices=False)
    except np.linalg.LinAlgError:
        return {"layer": name, "error": "SVD failed to converge"}
    total_energy = np.sum(S ** 2)
    cumulative = np.cumsum(S ** 2) / total_energy if total_energy > 0 else np.zeros_like(S)
    effective_rank = np.sum(cumulative < 0.99) + 1
    spectral_ratio = S[0] / S[1] if len(S) > 1 and S[1] > 1e-10 else float("inf")
    return {
        "layer": name,
        "shape": list(weight_matrix.shape),
        "top_singular_value": float(S[0]),
        "singular_value_std": float(np.std(S)),
        "spectral_ratio": float(spectral_ratio),
        "effective_rank": int(effective_rank),
        "total_rank": int(len(S)),
        "rank_utilization": round(effective_rank / len(S), 4),
        "energy_top1_pct": round(float(S[0] ** 2 / total_energy * 100), 2) if total_energy > 0 else 0,
        "energy_top5_pct": round(float(np.sum(S[:5] ** 2) / total_energy * 100), 2) if total_energy > 0 else 0
    }

def detect_anomalies(layer_results, sv_threshold=3.0, rank_threshold=0.1):
    """Flag layers with anomalous spectral properties."""
    anomalies = []
    sv_values = [r["top_singular_value"] for r in layer_results if "error" not in r]
    if not sv_values:
        return anomalies
    sv_mean = np.mean(sv_values)
    sv_std = np.std(sv_values)
    for result in layer_results:
        if "error" in result:
            anomalies.append({"layer": result["layer"], "reason": result["error"], "severity": "ERROR"})
            continue
        flags = []
        if sv_std > 0 and (result["top_singular_value"] - sv_mean) / sv_std > sv_threshold:
            flags.append(f"top SV {sv_threshold} std above mean ({result['top_singular_value']:.4f} vs mean {sv_mean:.4f})")
        if result["rank_utilization"] < rank_threshold:
            flags.append(f"rank utilization {result['rank_utilization']:.4f} below threshold {rank_threshold}")
        if result["spectral_ratio"] > 100:
            flags.append(f"spectral ratio {result['spectral_ratio']:.1f} indicates rank collapse")
        if flags:
            anomalies.append({
                "layer": result["layer"],
                "reasons": flags,
                "severity": "HIGH" if len(flags) > 1 else "MEDIUM"
            })
    return anomalies

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 spectral_safety_monitor.py /path/to/adapter")
        sys.exit(1)
    adapter_path = sys.argv[1]
    if not os.path.isdir(adapter_path):
        print(f"Error: {adapter_path} is not a directory")
        sys.exit(1)
    weights = load_adapter_weights(adapter_path)
    if not weights:
        print("No weight files found in adapter directory")
        sys.exit(1)
    layer_results = []
    for name, w in sorted(weights.items()):
        result = analyze_layer(name, w)
        if result:
            layer_results.append(result)
    anomalies = detect_anomalies(layer_results)
    report = {
        "generated_at": datetime.now().isoformat(),
        "adapter_path": adapter_path,
        "layers_analyzed": len(layer_results),
        "anomalies_found": len(anomalies),
        "safety_status": "PASS" if not anomalies else "FAIL",
        "anomalies": anomalies,
        "layer_details": layer_results
    }
    os.makedirs("/ganuda/reports", exist_ok=True)
    output_path = "/ganuda/reports/spectral-safety-report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {output_path}")
    print(f"Status: {report['safety_status']} ({len(anomalies)} anomalies in {len(layer_results)} layers)")
    for a in anomalies:
        print(f"  [{a['severity']}] {a['layer']}: {a.get('reasons', a.get('reason'))}")

if __name__ == "__main__":
    main()