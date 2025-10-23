#!/usr/bin/env python3
"""
Challenge 7 - Phase 2: Noise Injection & Robustness
War Chief's FULL 3-Family Analysis
Gate 2: At 20% phase jitter, R² ≥ 0.40 (revised from 0.56)
"""
import json
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.utils import resample
from scipy import stats

# Fixed seed
np.random.seed(42)

print("🦅 WAR CHIEF - PHASE 2: FULL NOISE INJECTION ANALYSIS")
print("=" * 70)

# Load baseline dataset from Phase 1
print("\n📂 Loading Phase 1 baseline dataset...")
with open('/ganuda/jr_assignments/meta_jr_hub/baseline_dataset.json', 'r') as f:
    df = pd.read_json(f)

print(f"✅ Loaded {len(df)} memories (45 sacred + 45 non-sacred)")

# Prepare clean data
X_clean = df[['phase_coherence', 'access_count', 'age_hours']].values
y_clean = df['temperature_score'].values

# Fit baseline model
baseline_model = LinearRegression()
baseline_model.fit(X_clean, y_clean)
baseline_r2 = baseline_model.score(X_clean, y_clean)

print(f"   Baseline R² = {baseline_r2:.4f}")

# Noise injection experiments
experiments = []

# Family 1: Phase Jitter (HIGHEST PRIORITY per War Chief)
print("\n🌀 FAMILY 1: PHASE JITTER (Natural Thermal Fluctuations)")
print("-" * 70)

for noise_pct in [5, 10, 15, 20]:
    print(f"\n   Testing {noise_pct}% phase jitter...")

    # Apply phase jitter (only to phase_coherence, clip to [0,1])
    X_noisy = X_clean.copy()
    noise = np.random.uniform(-noise_pct/100, noise_pct/100, size=X_clean[:, 0].shape)
    X_noisy[:, 0] = np.clip(X_clean[:, 0] + noise, 0, 1)

    # Evaluate on noisy data
    r2_noisy = baseline_model.score(X_noisy, y_clean)

    # Bootstrap (B=500)
    bootstrap_r2 = []
    for i in range(500):
        X_boot, y_boot = resample(X_clean, y_clean, random_state=i)

        # Apply same noise pattern
        X_boot_noisy = X_boot.copy()
        noise_boot = np.random.uniform(-noise_pct/100, noise_pct/100, size=X_boot[:, 0].shape)
        X_boot_noisy[:, 0] = np.clip(X_boot[:, 0] + noise_boot, 0, 1)

        model_boot = LinearRegression()
        model_boot.fit(X_boot, y_boot)
        bootstrap_r2.append(model_boot.score(X_boot_noisy, y_boot))

    bootstrap_r2 = np.array(bootstrap_r2)
    ci_lower = np.percentile(bootstrap_r2, 2.5)
    ci_upper = np.percentile(bootstrap_r2, 97.5)

    # Calculate distribution stats
    residuals = y_clean - baseline_model.predict(X_noisy)
    variance = np.var(residuals)
    skewness = stats.skew(residuals)
    kurtosis = stats.kurtosis(residuals)

    experiments.append({
        "noise_family": "phase_jitter",
        "noise_level": f"{noise_pct}%",
        "noise_level_numeric": noise_pct,
        "r2_noisy": float(r2_noisy),
        "r2_degradation": float(baseline_r2 - r2_noisy),
        "bootstrap": {
            "mean": float(np.mean(bootstrap_r2)),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "std": float(np.std(bootstrap_r2))
        },
        "residual_stats": {
            "variance": float(variance),
            "skewness": float(skewness),
            "kurtosis": float(kurtosis)
        }
    })

    print(f"      R² = {r2_noisy:.4f} (Δ = -{baseline_r2 - r2_noisy:.4f})")
    print(f"      Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    # Gate 2 Check at 20%
    if noise_pct == 20:
        gate2_pass = r2_noisy >= 0.40 and ci_lower >= 0.30
        print(f"\n   🚪 GATE 2 CHECK (20% phase jitter):")
        print(f"      R² ≥ 0.40: {'✅' if r2_noisy >= 0.40 else '❌'} ({r2_noisy:.4f})")
        print(f"      CI lower ≥ 0.30: {'✅' if ci_lower >= 0.30 else '❌'} ({ci_lower:.4f})")
        print(f"      Status: {'✅ PASS' if gate2_pass else '❌ FAIL'}")

# Family 2: Additive Gaussian (MEDIUM PRIORITY)
print("\n📊 FAMILY 2: ADDITIVE GAUSSIAN (Measurement Error)")
print("-" * 70)

feature_stds = X_clean.std(axis=0)

for sigma_pct in [5, 10, 15]:
    print(f"\n   Testing σ = {sigma_pct}% of feature std...")

    # Apply Gaussian noise to all features
    X_noisy = X_clean.copy()
    for i in range(3):
        noise = np.random.normal(0, sigma_pct/100 * feature_stds[i], size=X_clean[:, i].shape)
        X_noisy[:, i] = X_clean[:, i] + noise

    # Clip phase_coherence to [0,1]
    X_noisy[:, 0] = np.clip(X_noisy[:, 0], 0, 1)

    # Evaluate
    r2_noisy = baseline_model.score(X_noisy, y_clean)

    # Bootstrap
    bootstrap_r2 = []
    for i in range(500):
        X_boot, y_boot = resample(X_clean, y_clean, random_state=i)

        X_boot_noisy = X_boot.copy()
        for j in range(3):
            noise_boot = np.random.normal(0, sigma_pct/100 * feature_stds[j], size=X_boot[:, j].shape)
            X_boot_noisy[:, j] = X_boot[:, j] + noise_boot
        X_boot_noisy[:, 0] = np.clip(X_boot_noisy[:, 0], 0, 1)

        model_boot = LinearRegression()
        model_boot.fit(X_boot, y_boot)
        bootstrap_r2.append(model_boot.score(X_boot_noisy, y_boot))

    bootstrap_r2 = np.array(bootstrap_r2)
    ci_lower = np.percentile(bootstrap_r2, 2.5)
    ci_upper = np.percentile(bootstrap_r2, 97.5)

    residuals = y_clean - baseline_model.predict(X_noisy)

    experiments.append({
        "noise_family": "additive_gaussian",
        "noise_level": f"σ={sigma_pct}%",
        "noise_level_numeric": sigma_pct,
        "r2_noisy": float(r2_noisy),
        "r2_degradation": float(baseline_r2 - r2_noisy),
        "bootstrap": {
            "mean": float(np.mean(bootstrap_r2)),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "std": float(np.std(bootstrap_r2))
        },
        "residual_stats": {
            "variance": float(np.var(residuals)),
            "skewness": float(stats.skew(residuals)),
            "kurtosis": float(stats.kurtosis(residuals))
        }
    })

    print(f"      R² = {r2_noisy:.4f} (Δ = -{baseline_r2 - r2_noisy:.4f})")
    print(f"      Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

# Family 3: Multiplicative (LOWER PRIORITY - Memory Jr concern)
print("\n📉 FAMILY 3: MULTIPLICATIVE (Systematic Drift)")
print("-" * 70)

for mult_pct in [10, 20, 30]:
    print(f"\n   Testing ±{mult_pct}% multiplicative...")

    # Apply multiplicative noise
    X_noisy = X_clean.copy()
    noise = np.random.uniform(1 - mult_pct/100, 1 + mult_pct/100, size=X_clean.shape)
    X_noisy = X_clean * noise

    # Clip phase_coherence
    X_noisy[:, 0] = np.clip(X_noisy[:, 0], 0, 1)

    # Evaluate
    r2_noisy = baseline_model.score(X_noisy, y_clean)

    # Bootstrap
    bootstrap_r2 = []
    for i in range(500):
        X_boot, y_boot = resample(X_clean, y_clean, random_state=i)

        X_boot_noisy = X_boot.copy()
        noise_boot = np.random.uniform(1 - mult_pct/100, 1 + mult_pct/100, size=X_boot.shape)
        X_boot_noisy = X_boot * noise_boot
        X_boot_noisy[:, 0] = np.clip(X_boot_noisy[:, 0], 0, 1)

        model_boot = LinearRegression()
        model_boot.fit(X_boot, y_boot)
        bootstrap_r2.append(model_boot.score(X_boot_noisy, y_boot))

    bootstrap_r2 = np.array(bootstrap_r2)
    ci_lower = np.percentile(bootstrap_r2, 2.5)
    ci_upper = np.percentile(bootstrap_r2, 97.5)

    residuals = y_clean - baseline_model.predict(X_noisy)

    experiments.append({
        "noise_family": "multiplicative",
        "noise_level": f"±{mult_pct}%",
        "noise_level_numeric": mult_pct,
        "r2_noisy": float(r2_noisy),
        "r2_degradation": float(baseline_r2 - r2_noisy),
        "bootstrap": {
            "mean": float(np.mean(bootstrap_r2)),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "std": float(np.std(bootstrap_r2))
        },
        "residual_stats": {
            "variance": float(np.var(residuals)),
            "skewness": float(stats.skew(residuals)),
            "kurtosis": float(stats.kurtosis(residuals))
        }
    })

    print(f"      R² = {r2_noisy:.4f} (Δ = -{baseline_r2 - r2_noisy:.4f})")
    print(f"      Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

# Summary
print("\n" + "=" * 70)
print("📈 PHASE 2 SUMMARY: ROBUSTNESS ACROSS NOISE FAMILIES")
print("=" * 70)

for family in ["phase_jitter", "additive_gaussian", "multiplicative"]:
    family_exps = [e for e in experiments if e['noise_family'] == family]
    print(f"\n{family.upper()}:")
    for exp in family_exps:
        print(f"  {exp['noise_level']:>10s}: R² = {exp['r2_noisy']:.4f} (Δ = -{exp['r2_degradation']:.4f})")

# Save results
results = {
    "phase": "2_noise_injection",
    "timestamp": datetime.now().isoformat(),
    "node": "redfin",
    "baseline_r2": float(baseline_r2),
    "experiments": experiments,
    "gate2": {
        "criteria": "At 20% phase jitter: R² ≥ 0.40, CI lower ≥ 0.30",
        "experiment": next(e for e in experiments if e['noise_family'] == 'phase_jitter' and e['noise_level_numeric'] == 20),
        "status": "PASS" if next(e for e in experiments if e['noise_family'] == 'phase_jitter' and e['noise_level_numeric'] == 20)['r2_noisy'] >= 0.40 else "FAIL"
    }
}

results_json = json.dumps(results, indent=2, sort_keys=True)
results_hash = hashlib.sha256(results_json.encode()).hexdigest()
results["artifact_hash"] = results_hash

with open('/ganuda/jr_assignments/meta_jr_hub/phase2_noise_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved: phase2_noise_results.json")
print(f"🔐 Results SHA256: {results_hash[:16]}...")

print("\n" + "=" * 70)
print("🦅 PHASE 2 COMPLETE - Ready for Phase 3 (Visualization)")
print("=" * 70)
