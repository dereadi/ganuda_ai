#!/usr/bin/env python3
"""
🔥 THERMAL MEMORY PROMETHEUS EXPORTER 🔥
Cherokee Constitutional AI - Live R² Metrics

Exposes thermal regression metrics for Prometheus/Grafana monitoring.
"""

import psycopg2
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from prometheus_client import start_http_server, Gauge, Info
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus metrics
r2_access_gauge = Gauge('thermal_r2_access', 'R² for Temperature ~ Access Count')
r2_coherence_gauge = Gauge('thermal_r2_coherence', 'R² for Temperature ~ Phase Coherence')
r2_multivariate_gauge = Gauge('thermal_r2_multivariate', 'R² for Multivariate Model')
sacred_temp_gauge = Gauge('thermal_sacred_temperature', 'Average temperature of sacred memories')
normal_temp_gauge = Gauge('thermal_normal_temperature', 'Average temperature of normal memories')
temp_difference_gauge = Gauge('thermal_sacred_normal_diff', 'Temperature difference (sacred - normal)')
sacred_pvalue_gauge = Gauge('thermal_sacred_pvalue', 'P-value for sacred vs normal t-test')
sample_size_gauge = Gauge('thermal_sample_size', 'Number of thermal memories analyzed')
phase_coherence_mean_gauge = Gauge('thermal_phase_coherence_mean', 'Mean phase coherence across memories')

# System info
thermal_info = Info('thermal_regression_info', 'Thermal regression analysis metadata')

def connect_db():
    """Connect to thermal memory database."""
    return psycopg2.connect(
        host='192.168.132.222',
        port=5432,
        user='claude',
        password='jawaseatlasers2',
        database='zammad_production'
    )

def fetch_thermal_data():
    """Fetch thermal memory data for regression analysis."""
    conn = connect_db()

    query = '''
    SELECT
      id,
      temperature_score,
      access_count,
      phase_coherence,
      CASE WHEN sacred_pattern THEN 1 ELSE 0 END as is_sacred,
      EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
      AND phase_coherence IS NOT NULL
      AND access_count > 0
    ORDER BY RANDOM()
    LIMIT 500;
    '''

    import pandas as pd
    df = pd.read_sql(query, conn)
    conn.close()

    return df

def calculate_regression_metrics():
    """Calculate R² and related thermal metrics."""
    try:
        df = fetch_thermal_data()

        if len(df) < 10:
            logger.warning(f"Insufficient data: only {len(df)} records")
            return None

        # Prepare data
        X_access = df[['access_count']].values
        X_coherence = df[['phase_coherence']].values
        X_multi = df[['access_count', 'phase_coherence', 'is_sacred']].values
        y = df['temperature_score'].values

        # Regression models
        model_access = LinearRegression()
        model_access.fit(X_access, y)
        r2_access = r2_score(y, model_access.predict(X_access))

        model_coherence = LinearRegression()
        model_coherence.fit(X_coherence, y)
        r2_coherence = r2_score(y, model_coherence.predict(X_coherence))

        model_multi = LinearRegression()
        model_multi.fit(X_multi, y)
        r2_multi = r2_score(y, model_multi.predict(X_multi))

        # Sacred vs Normal comparison
        sacred = df[df['is_sacred'] == 1]['temperature_score']
        normal = df[df['is_sacred'] == 0]['temperature_score']

        sacred_mean = sacred.mean() if len(sacred) > 0 else 0
        normal_mean = normal.mean() if len(normal) > 0 else 0
        temp_diff = sacred_mean - normal_mean

        # T-test
        if len(sacred) > 1 and len(normal) > 1:
            t_stat, p_value = stats.ttest_ind(sacred, normal)
        else:
            p_value = 1.0

        # Phase coherence mean
        coherence_mean = df['phase_coherence'].mean()

        results = {
            'r2_access': r2_access,
            'r2_coherence': r2_coherence,
            'r2_multivariate': r2_multi,
            'sacred_temp': sacred_mean,
            'normal_temp': normal_mean,
            'temp_diff': temp_diff,
            'p_value': p_value,
            'sample_size': len(df),
            'coherence_mean': coherence_mean,
            'coefficients': {
                'access': model_multi.coef_[0],
                'coherence': model_multi.coef_[1],
                'sacred': model_multi.coef_[2]
            }
        }

        logger.info(f"Regression calculated: R² = {r2_multi:.4f} (n={len(df)})")
        return results

    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return None

def update_metrics():
    """Update Prometheus metrics with latest thermal data."""
    results = calculate_regression_metrics()

    if results:
        r2_access_gauge.set(results['r2_access'])
        r2_coherence_gauge.set(results['r2_coherence'])
        r2_multivariate_gauge.set(results['r2_multivariate'])
        sacred_temp_gauge.set(results['sacred_temp'])
        normal_temp_gauge.set(results['normal_temp'])
        temp_difference_gauge.set(results['temp_diff'])
        sacred_pvalue_gauge.set(results['p_value'])
        sample_size_gauge.set(results['sample_size'])
        phase_coherence_mean_gauge.set(results['coherence_mean'])

        # Update metadata
        thermal_info.info({
            'version': '1.0',
            'model': 'multivariate_linear_regression',
            'features': 'access_count,phase_coherence,sacred_pattern',
            'coefficient_access': f"{results['coefficients']['access']:.4f}",
            'coefficient_coherence': f"{results['coefficients']['coherence']:.4f}",
            'coefficient_sacred': f"{results['coefficients']['sacred']:.4f}"
        })

        logger.info("✅ Prometheus metrics updated")

def main():
    """Run Prometheus exporter server."""
    logger.info("🔥 Starting Thermal Memory Prometheus Exporter")
    logger.info("Listening on http://0.0.0.0:9100/metrics")

    # Start HTTP server
    start_http_server(9100)

    # Update metrics every 5 minutes
    while True:
        update_metrics()
        time.sleep(300)  # 5 minutes

if __name__ == '__main__':
    main()
