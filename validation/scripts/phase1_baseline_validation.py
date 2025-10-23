#!/usr/bin/env python3
"""
Challenge 7 - Phase 1: Baseline Validation
War Chief's 3-Phase Plan
Gate 1: R² ∈ [0.63, 0.73]
"""
import json
import hashlib
import numpy as np
import pandas as pd
import psycopg2
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.utils import resample
from scipy import stats

# Fixed seed (OpenAI requirement)
np.random.seed(42)

print("🦅 WAR CHIEF - PHASE 1: BASELINE VALIDATION")
print("=" * 60)

# Database connection
conn = psycopg2.connect(
    host="192.168.132.222",
    port=5432,
    user="claude",
    password="jawaseatlasers2",
    database="zammad_production"
)

# Query 90 memories (balanced sacred/non-sacred for variance)
# Per Challenge 4 finding: 99.8% of sacred have low metrics
# Need to query ALL memories (not just sacred) to get temperature variance
query = """
(
    SELECT
        id,
        temperature_score,
        phase_coherence,
        access_count,
        EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours,
        sacred_pattern
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
      AND phase_coherence IS NOT NULL
      AND access_count IS NOT NULL
      AND sacred_pattern = TRUE
    ORDER BY RANDOM()
    LIMIT 45
)
UNION ALL
(
    SELECT
        id,
        temperature_score,
        phase_coherence,
        access_count,
        EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours,
        sacred_pattern
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
      AND phase_coherence IS NOT NULL
      AND access_count IS NOT NULL
      AND sacred_pattern = FALSE
    ORDER BY RANDOM()
    LIMIT 45
);
"""

print("\n📊 Querying 90 thermal memories from hub (REDFIN)...")
df = pd.read_sql_query(query, conn)
conn.close()

print(f"✅ Retrieved {len(df)} memories")
print(f"   - Sacred: {df['sacred_pattern'].sum()}")
print(f"   - Non-sacred: {(~df['sacred_pattern']).sum()}")

# Save dataset for reproducibility
dataset_json = df.to_json(orient='records', indent=2)
dataset_hash = hashlib.sha256(dataset_json.encode()).hexdigest()

with open('/ganuda/jr_assignments/meta_jr_hub/baseline_dataset.json', 'w') as f:
    f.write(dataset_json)

print(f"\n🔐 Dataset SHA256: {dataset_hash[:16]}...")

# Prepare features and target
X = df[['phase_coherence', 'access_count', 'age_hours']].values
y = df['temperature_score'].values

print("\n📈 Calculating baseline R² (partial correlation)...")

# Fit model on clean data
model = LinearRegression()
model.fit(X, y)
r_squared = model.score(X, y)

print(f"   Baseline R² = {r_squared:.4f}")

# Gate 1 Check
gate1_pass = 0.63 <= r_squared <= 0.73
print(f"\n🚪 GATE 1 CHECK: R² ∈ [0.63, 0.73]")
print(f"   Status: {'✅ PASS' if gate1_pass else '❌ FAIL'}")

if not gate1_pass:
    print(f"   ⚠️  HALT: Baseline R² outside acceptable range!")
    print(f"   Recalibration needed before proceeding to Phase 2")

# Bootstrap confidence interval (B=500)
print("\n🔄 Bootstrap analysis (B=500 iterations)...")
bootstrap_r2 = []

for i in range(500):
    # Resample with replacement
    X_boot, y_boot = resample(X, y, random_state=i)
    model_boot = LinearRegression()
    model_boot.fit(X_boot, y_boot)
    bootstrap_r2.append(model_boot.score(X_boot, y_boot))

bootstrap_r2 = np.array(bootstrap_r2)
ci_lower = np.percentile(bootstrap_r2, 2.5)
ci_upper = np.percentile(bootstrap_r2, 97.5)

print(f"   Bootstrap R² mean: {np.mean(bootstrap_r2):.4f}")
print(f"   95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

# Permutation test (1000 permutations)
print("\n🔀 Permutation test (1000 iterations)...")
permutation_r2 = []

for i in range(1000):
    y_perm = np.random.permutation(y)
    model_perm = LinearRegression()
    model_perm.fit(X, y_perm)
    permutation_r2.append(model_perm.score(X, y_perm))

permutation_r2 = np.array(permutation_r2)
p_value = np.mean(permutation_r2 >= r_squared)

print(f"   Null R² mean: {np.mean(permutation_r2):.4f}")
print(f"   Null R² max: {np.max(permutation_r2):.4f}")
print(f"   p-value: {p_value:.6f}")
print(f"   Significant: {'✅ YES' if p_value < 0.05 else '❌ NO'}")

# Feature importance
print("\n🔍 Feature importance (coefficients):")
feature_names = ['phase_coherence', 'access_count', 'age_hours']
for name, coef in zip(feature_names, model.coef_):
    print(f"   {name}: {coef:.4f}")
print(f"   Intercept: {model.intercept_:.4f}")

# Sacred vs Non-Sacred breakdown
print("\n🛡️ Guardian Protection Analysis:")
X_sacred = df[df['sacred_pattern']][['phase_coherence', 'access_count', 'age_hours']].values
y_sacred = df[df['sacred_pattern']]['temperature_score'].values
X_nonsacred = df[~df['sacred_pattern']][['phase_coherence', 'access_count', 'age_hours']].values
y_nonsacred = df[~df['sacred_pattern']]['temperature_score'].values

r2_sacred = None
r2_nonsacred = None

if len(X_sacred) > 0 and len(X_nonsacred) > 0:
    model_sacred = LinearRegression()
    model_sacred.fit(X_sacred, y_sacred)
    r2_sacred = model_sacred.score(X_sacred, y_sacred)

    model_nonsacred = LinearRegression()
    model_nonsacred.fit(X_nonsacred, y_nonsacred)
    r2_nonsacred = model_nonsacred.score(X_nonsacred, y_nonsacred)

    print(f"   Sacred R²: {r2_sacred:.4f}")
    print(f"   Non-Sacred R²: {r2_nonsacred:.4f}")
    print(f"   Protection Δ: {r2_sacred - r2_nonsacred:.4f}")
else:
    print(f"   ⚠️  Insufficient data for Guardian analysis")
    print(f"   Sacred count: {len(X_sacred)}, Non-sacred count: {len(X_nonsacred)}")

# Save results
results = {
    "phase": "1_baseline_validation",
    "timestamp": datetime.now().isoformat(),
    "node": "redfin",
    "dataset": {
        "sample_size": len(df),
        "sacred_count": int(df['sacred_pattern'].sum()),
        "nonsacred_count": int((~df['sacred_pattern']).sum()),
        "sha256": dataset_hash,
        "seed": 42
    },
    "baseline_r_squared": float(r_squared),
    "bootstrap": {
        "iterations": 500,
        "mean_r2": float(np.mean(bootstrap_r2)),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "std": float(np.std(bootstrap_r2))
    },
    "permutation_test": {
        "iterations": 1000,
        "null_mean_r2": float(np.mean(permutation_r2)),
        "null_max_r2": float(np.max(permutation_r2)),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05)
    },
    "gate1": {
        "criteria": "R² ∈ [0.63, 0.73]",
        "status": "PASS" if gate1_pass else "FAIL",
        "pass": gate1_pass
    },
    "model": {
        "coefficients": {
            "phase_coherence": float(model.coef_[0]),
            "access_count": float(model.coef_[1]),
            "age_hours": float(model.coef_[2])
        },
        "intercept": float(model.intercept_)
    },
    "guardian_protection": {
        "sacred_r2": float(r2_sacred) if len(X_sacred) > 0 else None,
        "nonsacred_r2": float(r2_nonsacred) if len(X_nonsacred) > 0 else None,
        "protection_delta": float(r2_sacred - r2_nonsacred) if len(X_sacred) > 0 and len(X_nonsacred) > 0 else None
    }
}

# Calculate results hash
results_json = json.dumps(results, indent=2, sort_keys=True)
results_hash = hashlib.sha256(results_json.encode()).hexdigest()
results["artifact_hash"] = results_hash

with open('/ganuda/jr_assignments/meta_jr_hub/phase1_baseline_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved: phase1_baseline_results.json")
print(f"🔐 Results SHA256: {results_hash[:16]}...")

print("\n" + "=" * 60)
if gate1_pass:
    print("🦅 PHASE 1 COMPLETE - Ready for Phase 2 (Noise Injection)")
else:
    print("⚠️  PHASE 1 FAILED - Recalibration needed")
print("=" * 60)
