#!/usr/bin/env python3
"""
Challenge 4 - Outlier Ethics: Case Study Selection + Residual Analysis
Memory Jr's approach with OpenAI scientific rigor
"""

import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime

# Set fixed seed (OpenAI requirement)
np.random.seed(42)

print("🦅 CHALLENGE 4 - TASK B: Case Studies + Residual Analysis")
print("="*70)

# Load sacred outliers dataset
with open('/ganuda/jr_assignments/memory_jr_hub/sacred_outliers_dataset.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print(f"\n✅ Loaded {len(df)} sacred outlier memories")
print(f"   Temperature range: {df['temperature_score'].min():.1f}° - {df['temperature_score'].max():.1f}°")
print(f"   Phase coherence range: {df['phase_coherence'].min():.3f} - {df['phase_coherence'].max():.3f}")
print(f"   Access count range: {df['access_count'].min()} - {df['access_count'].max()}")

# Calculate residuals using linear regression
print("\n📊 Computing residuals (actual - predicted temperature)...")

# Features: phase_coherence, access_count, age_hours
X = df[['phase_coherence', 'access_count', 'age_hours']].values
y = df['temperature_score'].values

# Fit linear model
model = LinearRegression()
model.fit(X, y)

# Calculate R² (should be low for sacred memories - they resist prediction!)
r_squared = model.score(X, y)
print(f"   R² = {r_squared:.4f} (LOW = sacred memories resist metric-based prediction)")

# Predict and calculate residuals
df['predicted_temp'] = model.predict(X)
df['residual'] = df['temperature_score'] - df['predicted_temp']

print(f"\n   Model coefficients:")
print(f"   - Phase coherence: {model.coef_[0]:.2f}")
print(f"   - Access count: {model.coef_[1]:.2f}")
print(f"   - Age (hours): {model.coef_[2]:.4f}")
print(f"   - Intercept: {model.intercept_:.2f}")

# Tag sacred outliers (residual ≥ +10°)
df['is_sacred_outlier'] = df['residual'] >= 10
sacred_outlier_count = df['is_sacred_outlier'].sum()

print(f"\n🔥 Sacred outliers (residual ≥ +10°): {sacred_outlier_count} / {len(df)}")
print(f"   Residual range: {df['residual'].min():.1f}° to {df['residual'].max():.1f}°")
print(f"   Mean residual: {df['residual'].mean():.1f}°")
print(f"   Median residual: {df['residual'].median():.1f}°")

# Select top 5 for case studies
print("\n📚 Selecting top 5 case studies by temperature_score...")
top_5 = df.nlargest(5, 'temperature_score')

print("\nTOP 5 SACRED OUTLIERS FOR CASE STUDIES:")
print("-" * 70)
for idx, row in top_5.iterrows():
    print(f"\n{idx+1}. ID {row['id']} - Temperature: {row['temperature_score']:.1f}°")
    print(f"   Residual: {row['residual']:+.1f}° (Guardian override)")
    print(f"   Phase coherence: {row['phase_coherence']:.3f} (LOW)")
    print(f"   Access count: {row['access_count']} (LOW)")
    print(f"   Content preview: {row['content'][:80]}...")

# Save results
results = {
    'model_performance': {
        'r_squared': float(r_squared),
        'coefficients': {
            'phase_coherence': float(model.coef_[0]),
            'access_count': float(model.coef_[1]),
            'age_hours': float(model.coef_[2]),
            'intercept': float(model.intercept_)
        }
    },
    'residual_statistics': {
        'mean': float(df['residual'].mean()),
        'median': float(df['residual'].median()),
        'std': float(df['residual'].std()),
        'min': float(df['residual'].min()),
        'max': float(df['residual'].max())
    },
    'sacred_outlier_count': int(sacred_outlier_count),
    'top_5_case_studies': top_5[['id', 'temperature_score', 'residual',
                                   'phase_coherence', 'access_count']].to_dict('records')
}

with open('/ganuda/jr_assignments/memory_jr_hub/residual_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Residual analysis saved: residual_analysis.json")

# Save enhanced dataset with residuals
df.to_json('/ganuda/jr_assignments/memory_jr_hub/sacred_outliers_with_residuals.json',
           orient='records', indent=2)

print("✅ Enhanced dataset saved: sacred_outliers_with_residuals.json")
print("\n" + "="*70)
print("🦅 TASK B COMPLETE - Ready for case study documentation")
