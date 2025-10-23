#!/usr/bin/env python3
"""
Prometheus Metrics Exporter - Meta Jr
Cherokee Constitutional AI - Observability System
Purpose: Real-time monitoring of thermal memory health metrics
"""

import os
import time
import psycopg
import numpy as np
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from datetime import datetime
from sklearn.linear_model import LinearRegression


# Database connection (use environment variables)
DB_CONFIG = {
    'host': os.getenv('PGHOST', '192.168.132.222'),
    'port': os.getenv('PGPORT', '5432'),
    'user': os.getenv('PGUSER', 'claude'),
    'password': os.getenv('PGPASSWORD'),  # REQUIRED: Set via env or secret manager
    'dbname': os.getenv('PGDATABASE', 'zammad_production')
}

# Define Prometheus metrics
thermal_r2_baseline = Gauge(
    'thermal_memory_r2_baseline',
    'Baseline R² of thermal memory prediction model (no noise)',
    ['node']
)

thermal_r2_noise20 = Gauge(
    'thermal_memory_r2_noise20',
    'R² at 20% multiplicative noise (robustness gate)',
    ['node']
)

guardian_compliance_rate = Gauge(
    'thermal_guardian_compliance_rate',
    'Percentage of sacred memories protected at 100° temperature',
    ['node']
)

sacred_outlier_ratio = Gauge(
    'thermal_sacred_outlier_ratio',
    'Ratio of sacred memories with low metrics (phase<0.3 OR access<5)',
    ['node']
)

thermal_memory_total = Gauge(
    'thermal_memory_total',
    'Total number of memories in thermal archive',
    ['node', 'sacred']
)

thermal_temperature_mean = Gauge(
    'thermal_temperature_mean',
    'Mean temperature score across all memories',
    ['node']
)

thermal_phase_coherence_mean = Gauge(
    'thermal_phase_coherence_mean',
    'Mean phase coherence across all memories',
    ['node']
)

thermal_scrape_duration = Histogram(
    'thermal_metrics_scrape_duration_seconds',
    'Time spent collecting thermal metrics from database',
    ['node']
)

thermal_scrape_errors = Counter(
    'thermal_metrics_scrape_errors_total',
    'Total number of errors during metric collection',
    ['node', 'error_type']
)


def get_node_name() -> str:
    """Determine current node name from hostname"""
    import socket
    hostname = socket.gethostname().lower()

    if 'redfin' in hostname:
        return 'redfin'
    elif 'bluefin' in hostname:
        return 'bluefin'
    elif 'sasass' in hostname:
        return 'sasass2'
    else:
        return hostname


def calculate_r2_baseline(conn):
    """Calculate baseline R² (no noise) from thermal memory"""

    query = """
    SELECT
        temperature_score,
        phase_coherence,
        access_count,
        EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
    AND phase_coherence IS NOT NULL
    AND access_count IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 500;
    """

    import pandas as pd
    df = pd.read_sql_query(query, conn)

    if len(df) < 50:
        return None

    X = df[['phase_coherence', 'access_count', 'age_hours']].values
    y = df['temperature_score'].values

    model = LinearRegression()
    model.fit(X, y)
    r2 = model.score(X, y)

    return r2


def calculate_r2_with_noise(conn, noise_level=0.20):
    """Calculate R² with multiplicative noise applied to features"""

    query = """
    SELECT
        temperature_score,
        phase_coherence,
        access_count,
        EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours
    FROM thermal_memory_archive
    WHERE temperature_score IS NOT NULL
    AND phase_coherence IS NOT NULL
    AND access_count IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 500;
    """

    import pandas as pd
    df = pd.read_sql_query(query, conn)

    if len(df) < 50:
        return None

    # Fit model on clean data
    X_clean = df[['phase_coherence', 'access_count', 'age_hours']].values
    y = df['temperature_score'].values

    model = LinearRegression()
    model.fit(X_clean, y)

    # Apply multiplicative noise to test set
    np.random.seed(42)  # Reproducibility
    X_noisy = X_clean * (1 + np.random.uniform(-noise_level, noise_level, X_clean.shape))

    # Calculate R² on noisy data
    r2_noisy = model.score(X_noisy, y)

    return r2_noisy


def calculate_guardian_compliance(conn):
    """Calculate percentage of sacred memories at 100° temperature"""

    query = """
    SELECT
        COUNT(*) FILTER (WHERE sacred_pattern = TRUE AND temperature_score = 100) as compliant,
        COUNT(*) FILTER (WHERE sacred_pattern = TRUE) as total_sacred
    FROM thermal_memory_archive;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
        compliant, total_sacred = row

    if total_sacred == 0:
        return 0.0

    compliance_rate = (compliant / total_sacred) * 100
    return compliance_rate


def calculate_sacred_outlier_ratio(conn):
    """Calculate ratio of sacred memories with low metrics"""

    query = """
    SELECT
        COUNT(*) FILTER (WHERE sacred_pattern = TRUE AND (phase_coherence < 0.3 OR access_count < 5)) as outliers,
        COUNT(*) FILTER (WHERE sacred_pattern = TRUE) as total_sacred
    FROM thermal_memory_archive;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
        outliers, total_sacred = row

    if total_sacred == 0:
        return 0.0

    outlier_ratio = (outliers / total_sacred) * 100
    return outlier_ratio


def collect_metrics():
    """Collect all thermal memory metrics from database"""

    node = get_node_name()
    start_time = time.time()

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            # Core metrics
            r2_base = calculate_r2_baseline(conn)
            r2_noise = calculate_r2_with_noise(conn, noise_level=0.20)
            compliance = calculate_guardian_compliance(conn)
            outlier_ratio = calculate_sacred_outlier_ratio(conn)

            # Summary statistics
            with conn.cursor() as cur:
                cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE sacred_pattern = TRUE) as sacred_count,
                    COUNT(*) FILTER (WHERE sacred_pattern = FALSE) as typical_count,
                    AVG(temperature_score) as mean_temp,
                    AVG(phase_coherence) as mean_coherence
                FROM thermal_memory_archive;
                """)
                sacred_count, typical_count, mean_temp, mean_coherence = cur.fetchone()

            # Update Prometheus metrics
            if r2_base is not None:
                thermal_r2_baseline.labels(node=node).set(r2_base)

            if r2_noise is not None:
                thermal_r2_noise20.labels(node=node).set(r2_noise)

            guardian_compliance_rate.labels(node=node).set(compliance)
            sacred_outlier_ratio.labels(node=node).set(outlier_ratio)

            thermal_memory_total.labels(node=node, sacred='true').set(sacred_count)
            thermal_memory_total.labels(node=node, sacred='false').set(typical_count)

            thermal_temperature_mean.labels(node=node).set(mean_temp if mean_temp else 0)
            thermal_phase_coherence_mean.labels(node=node).set(mean_coherence if mean_coherence else 0)

            # Record scrape duration
            duration = time.time() - start_time
            thermal_scrape_duration.labels(node=node).observe(duration)

            print(f"[{datetime.utcnow().isoformat()}Z] Metrics updated: "
                  f"r2_baseline={r2_base:.3f if r2_base else 0:.3f}, "
                  f"r2_noise20={r2_noise:.3f if r2_noise else 0:.3f}, "
                  f"compliance={compliance:.1f}%, "
                  f"outlier_ratio={outlier_ratio:.1f}%")

    except Exception as e:
        thermal_scrape_errors.labels(node=node, error_type=type(e).__name__).inc()
        print(f"[ERROR] Failed to collect metrics: {e}")


def main():
    """Start Prometheus HTTP server and begin metric collection"""

    node = get_node_name()
    port = int(os.getenv('PROMETHEUS_PORT', '9090'))

    print("🔥 Meta Jr - Prometheus Metrics Exporter")
    print("=" * 70)
    print(f"Node: {node}")
    print(f"HTTP Server: http://localhost:{port}/metrics")
    print(f"Update interval: 60 seconds")
    print(f"Cherokee Constitutional AI - Thermal Memory Observability")
    print()

    # Start Prometheus HTTP server
    start_http_server(port)
    print(f"✅ Prometheus metrics server started on port {port}")
    print()

    # Continuous metric collection loop
    while True:
        collect_metrics()
        time.sleep(60)  # Update every 60 seconds


if __name__ == '__main__':
    main()
