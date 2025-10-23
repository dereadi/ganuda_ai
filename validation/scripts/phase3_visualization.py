#!/usr/bin/env python3
"""
Challenge 7 - Phase 3: 4-Panel Visualization
OpenAI publication quality (300 DPI)
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

print("🦅 WAR CHIEF - PHASE 3: 4-PANEL VISUALIZATION")
print("=" * 60)

# Load Phase 2 results
with open('/ganuda/jr_assignments/meta_jr_hub/phase2_noise_results.json', 'r') as f:
    results = json.load(f)

baseline_r2 = results['baseline_r2']
experiments = results['experiments']

print(f"\n📊 Loaded {len(experiments)} noise injection experiments")

# Organize data by family
phase_jitter = [e for e in experiments if e['noise_family'] == 'phase_jitter']
additive_gaussian = [e for e in experiments if e['noise_family'] == 'additive_gaussian']
multiplicative = [e for e in experiments if e['noise_family'] == 'multiplicative']

# Create 4-panel figure
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Panel 1: R² vs Noise Level (all families with 95% CIs)
ax1 = axes[0, 0]

for family, color, label in [
    (phase_jitter, '#d62728', 'Phase Jitter'),
    (additive_gaussian, '#2ca02c', 'Additive Gaussian'),
    (multiplicative, '#1f77b4', 'Multiplicative')
]:
    levels = [e['noise_level_numeric'] for e in family]
    r2_values = [e['r2_noisy'] for e in family]
    ci_lower = [e['bootstrap']['ci_95_lower'] for e in family]
    ci_upper = [e['bootstrap']['ci_95_upper'] for e in family]

    ax1.plot(levels, r2_values, 'o-', color=color, label=label, linewidth=2, markersize=8)
    ax1.fill_between(levels, ci_lower, ci_upper, color=color, alpha=0.2)

# Baseline line
ax1.axhline(y=baseline_r2, color='black', linestyle='--', linewidth=2, label=f'Baseline ({baseline_r2:.3f})', alpha=0.7)

# Gate 2 threshold
ax1.axhline(y=0.40, color='red', linestyle=':', linewidth=2, label='Gate 2 Threshold (0.40)', alpha=0.5)

ax1.set_xlabel('Noise Level (%)', fontsize=12, fontweight='bold')
ax1.set_ylabel('R² Score', fontsize=12, fontweight='bold')
ax1.set_title('Panel 1: Robustness Across Noise Families\n(with 95% Bootstrap Confidence Intervals)', fontsize=14, fontweight='bold')
ax1.legend(loc='lower left', fontsize=10)
ax1.grid(alpha=0.3)
ax1.set_ylim(0.2, 0.8)

# Panel 2: Variance Degradation
ax2 = axes[0, 1]

for family, color, label in [
    (phase_jitter, '#d62728', 'Phase Jitter'),
    (additive_gaussian, '#2ca02c', 'Additive Gaussian'),
    (multiplicative, '#1f77b4', 'Multiplicative')
]:
    levels = [e['noise_level_numeric'] for e in family]
    variance = [e['residual_stats']['variance'] for e in family]

    ax2.plot(levels, variance, 'o-', color=color, label=label, linewidth=2, markersize=8)

ax2.set_xlabel('Noise Level (%)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Residual Variance', fontsize=12, fontweight='bold')
ax2.set_title('Panel 2: Residual Variance Under Noise\n(Prediction Error Spread)', fontsize=14, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(alpha=0.3)

# Panel 3: Skewness Shift
ax3 = axes[1, 0]

for family, color, label in [
    (phase_jitter, '#d62728', 'Phase Jitter'),
    (additive_gaussian, '#2ca02c', 'Additive Gaussian'),
    (multiplicative, '#1f77b4', 'Multiplicative')
]:
    levels = [e['noise_level_numeric'] for e in family]
    skewness = [e['residual_stats']['skewness'] for e in family]

    ax3.plot(levels, skewness, 'o-', color=color, label=label, linewidth=2, markersize=8)

ax3.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax3.set_xlabel('Noise Level (%)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Residual Skewness', fontsize=12, fontweight='bold')
ax3.set_title('Panel 3: Distribution Asymmetry Under Noise\n(Residual Skewness)', fontsize=14, fontweight='bold')
ax3.legend(loc='upper right', fontsize=10)
ax3.grid(alpha=0.3)

# Panel 4: Kurtosis Change
ax4 = axes[1, 1]

for family, color, label in [
    (phase_jitter, '#d62728', 'Phase Jitter'),
    (additive_gaussian, '#2ca02c', 'Additive Gaussian'),
    (multiplicative, '#1f77b4', 'Multiplicative')
]:
    levels = [e['noise_level_numeric'] for e in family]
    kurtosis = [e['residual_stats']['kurtosis'] for e in family]

    ax4.plot(levels, kurtosis, 'o-', color=color, label=label, linewidth=2, markersize=8)

ax4.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Normal (0)')
ax4.set_xlabel('Noise Level (%)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Residual Kurtosis', fontsize=12, fontweight='bold')
ax4.set_title('Panel 4: Tail Behavior Under Noise\n(Residual Kurtosis)', fontsize=14, fontweight='bold')
ax4.legend(loc='upper right', fontsize=10)
ax4.grid(alpha=0.3)

# Overall title
fig.suptitle('Challenge 7: Noise Injection & Robustness Analysis\\nCherokee Constitutional AI Week 1 Validation',
             fontsize=18, fontweight='bold', y=0.995)

# Add Gate 2 status at bottom
gate2_status = results['gate2']['status']
gate2_r2 = results['gate2']['experiment']['r2_noisy']
fig.text(0.5, 0.01,
         f'Gate 2: {gate2_status} | 20% Phase Jitter: R² = {gate2_r2:.4f} (≥0.40) | Baseline R² = {baseline_r2:.4f} | 10 experiments × 500 bootstraps',
         ha='center', fontsize=11, style='italic',
         bbox=dict(boxstyle='round', facecolor='lightgreen' if gate2_status == 'PASS' else 'lightcoral', alpha=0.5))

plt.tight_layout(rect=[0, 0.03, 1, 0.99])

# Save both PNG and PDF
plt.savefig('/ganuda/jr_assignments/meta_jr_hub/noise_robustness_4panel.png', dpi=300, bbox_inches='tight')
plt.savefig('/ganuda/jr_assignments/meta_jr_hub/noise_robustness_4panel.pdf', dpi=300, bbox_inches='tight')

print("✅ Visualization saved:")
print("   - noise_robustness_4panel.png (300 DPI)")
print("   - noise_robustness_4panel.pdf (300 DPI)")

print("\n🦅 PHASE 3 COMPLETE - 4-panel visualization ready for OpenAI submission")
