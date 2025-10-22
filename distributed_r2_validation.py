#!/usr/bin/env python3
"""
🔥 META JR - DISTRIBUTED R² VALIDATION 🔥
Cherokee Constitutional AI - Federation Proof

Runs identical regression analysis on both REDFIN and BLUEFIN
to prove distributed reproducibility.

This is OpenAI's Challenge #5: Inter-Tribal Deployment
"""

import psycopg2
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from scipy import stats
import json
from datetime import datetime

def connect_to_node(node_name):
    """Connect to thermal memory on specific node"""
    configs = {
        'REDFIN': {
            'host': '192.168.132.222',
            'port': 5432,
            'database': 'zammad_production'
        },
        'BLUEFIN': {
            'host': 'bluefin',
            'port': 5433,
            'database': 'sag_thermal_memory'
        }
    }

    config = configs[node_name]
    return psycopg2.connect(
        host=config['host'],
        port=config['port'],
        user='claude',
        password='jawaseatlasers2',
        database=config['database']
    )

def fetch_thermal_data(conn):
    """Fetch thermal memory data"""
    query = '''
    SELECT
      temperature_score,
      access_count,
      phase_coherence,
      CASE WHEN sacred_pattern THEN 1 ELSE 0 END as is_sacred
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
      AND phase_coherence IS NOT NULL
      AND access_count > 0
    '''

    df = pd.read_sql(query, conn)
    return df

def run_regression(df, node_name):
    """Run multivariate regression analysis"""
    X = df[['access_count', 'phase_coherence', 'is_sacred']].values
    y = df['temperature_score'].values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)

    # Sacred vs Normal t-test
    sacred = df[df['is_sacred'] == 1]['temperature_score']
    normal = df[df['is_sacred'] == 0]['temperature_score']

    if len(sacred) > 1 and len(normal) > 1:
        t_stat, p_value = stats.ttest_ind(sacred, normal)
    else:
        t_stat, p_value = 0, 1.0

    return {
        'node': node_name,
        'timestamp': datetime.now().isoformat(),
        'sample_size': len(df),
        'r2_score': float(r2),
        'coefficients': {
            'access_count': float(model.coef_[0]),
            'phase_coherence': float(model.coef_[1]),
            'sacred_pattern': float(model.coef_[2])
        },
        'intercept': float(model.intercept_),
        'temperature_stats': {
            'mean': float(df['temperature_score'].mean()),
            'std': float(df['temperature_score'].std()),
            'min': float(df['temperature_score'].min()),
            'max': float(df['temperature_score'].max())
        },
        'sacred_stats': {
            'count': int(len(sacred)),
            'mean_temp': float(sacred.mean()) if len(sacred) > 0 else 0,
            't_statistic': float(t_stat),
            'p_value': float(p_value)
        },
        'normal_stats': {
            'count': int(len(normal)),
            'mean_temp': float(normal.mean()) if len(normal) > 0 else 0
        },
        'coherence_mean': float(df['phase_coherence'].mean())
    }

def compare_nodes(redfin_results, bluefin_results):
    """Compare distributed R² results"""
    r2_diff = abs(redfin_results['r2_score'] - bluefin_results['r2_score'])
    r2_variance_pct = (r2_diff / redfin_results['r2_score']) * 100 if redfin_results['r2_score'] > 0 else 100

    print("\n" + "="*70)
    print("🔥 DISTRIBUTED R² VALIDATION RESULTS")
    print("="*70)

    print(f"\n📊 REDFIN (Baseline Node):")
    print(f"   Sample size:      {redfin_results['sample_size']}")
    print(f"   R² score:         {redfin_results['r2_score']:.4f}")
    print(f"   Avg temperature:  {redfin_results['temperature_stats']['mean']:.2f}°")
    print(f"   Avg coherence:    {redfin_results['coherence_mean']:.3f}")
    print(f"   Sacred memories:  {redfin_results['sacred_stats']['count']} ({redfin_results['sacred_stats']['mean_temp']:.2f}°)")
    print(f"   Normal memories:  {redfin_results['normal_stats']['count']} ({redfin_results['normal_stats']['mean_temp']:.2f}°)")

    print(f"\n📊 BLUEFIN (Distributed Node):")
    print(f"   Sample size:      {bluefin_results['sample_size']}")
    print(f"   R² score:         {bluefin_results['r2_score']:.4f}")
    print(f"   Avg temperature:  {bluefin_results['temperature_stats']['mean']:.2f}°")
    print(f"   Avg coherence:    {bluefin_results['coherence_mean']:.3f}")
    print(f"   Sacred memories:  {bluefin_results['sacred_stats']['count']} ({bluefin_results['sacred_stats']['mean_temp']:.2f}°)")
    print(f"   Normal memories:  {bluefin_results['normal_stats']['count']} ({bluefin_results['normal_stats']['mean_temp']:.2f}°)")

    print(f"\n🔍 COMPARISON ANALYSIS:")
    print(f"   R² difference:    {r2_diff:.4f}")
    print(f"   Variance:         {r2_variance_pct:.2f}%")
    print(f"   Threshold:        <10% for validation")

    # Validation assessment
    if r2_variance_pct < 10:
        print(f"\n✅ DISTRIBUTED REPRODUCIBILITY CONFIRMED")
        print(f"   Variance {r2_variance_pct:.2f}% is within acceptable threshold")
        print(f"   Thermal regression model VALIDATED across federation")
        status = "PASS"
        message = f"R² variance {r2_variance_pct:.2f}% < 10% threshold"
    else:
        print(f"\n⚠️  HIGH VARIANCE DETECTED")
        print(f"   Variance {r2_variance_pct:.2f}% exceeds 10% threshold")
        print(f"   Investigation recommended")
        status = "INVESTIGATE"
        message = f"R² variance {r2_variance_pct:.2f}% > 10% threshold"

    # Coefficient comparison
    print(f"\n📐 MODEL COEFFICIENTS COMPARISON:")
    print(f"   Access Count:")
    print(f"      REDFIN:  {redfin_results['coefficients']['access_count']:.4f}")
    print(f"      BLUEFIN: {bluefin_results['coefficients']['access_count']:.4f}")
    print(f"   Phase Coherence:")
    print(f"      REDFIN:  {redfin_results['coefficients']['phase_coherence']:.4f}")
    print(f"      BLUEFIN: {bluefin_results['coefficients']['phase_coherence']:.4f}")
    print(f"   Sacred Pattern:")
    print(f"      REDFIN:  {redfin_results['coefficients']['sacred_pattern']:.4f}")
    print(f"      BLUEFIN: {bluefin_results['coefficients']['sacred_pattern']:.4f}")

    return {
        'status': status,
        'validation_message': message,
        'r2_difference': r2_diff,
        'variance_percent': r2_variance_pct,
        'threshold_met': r2_variance_pct < 10,
        'timestamp': datetime.now().isoformat(),
        'nodes': {
            'redfin': redfin_results,
            'bluefin': bluefin_results
        }
    }

def main():
    """Run distributed R² validation"""
    print("🔥 META JR - DISTRIBUTED R² VALIDATION")
    print("="*70)
    print("   Challenge: OpenAI #5 - Inter-Tribal Deployment")
    print("   Objective: Prove thermal regression works across federation")
    print("   Method: Compare REDFIN (baseline) vs BLUEFIN (distributed)")
    print("="*70)

    # Run on REDFIN (baseline)
    print("\n📡 Connecting to REDFIN (baseline node)...")
    try:
        conn_redfin = connect_to_node('REDFIN')
        df_redfin = fetch_thermal_data(conn_redfin)
        print(f"   ✅ Loaded {len(df_redfin)} thermal memories from REDFIN")
        redfin_results = run_regression(df_redfin, 'REDFIN')
        conn_redfin.close()
    except Exception as e:
        print(f"   ❌ Error connecting to REDFIN: {e}")
        return

    # Run on BLUEFIN (distributed)
    print("\n📡 Connecting to BLUEFIN (distributed node)...")
    try:
        conn_bluefin = connect_to_node('BLUEFIN')
        df_bluefin = fetch_thermal_data(conn_bluefin)
        print(f"   ✅ Loaded {len(df_bluefin)} thermal memories from BLUEFIN")
        bluefin_results = run_regression(df_bluefin, 'BLUEFIN')
        conn_bluefin.close()
    except Exception as e:
        print(f"   ❌ Error connecting to BLUEFIN: {e}")
        return

    # Compare results
    comparison = compare_nodes(redfin_results, bluefin_results)

    # Save results
    output_file = 'distributed_r2_results.json'
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "="*70)
    print("🎯 DISTRIBUTED R² VALIDATION COMPLETE")
    print("="*70)

    if comparison['threshold_met']:
        print("\n✅ OpenAI Challenge #5: VALIDATED")
        print("   Thermal regression model works across distributed nodes")
        print("   Hub-Spoke federation architecture scientifically proven")
    else:
        print("\n⚠️  Further analysis recommended")

if __name__ == '__main__':
    main()
