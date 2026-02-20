#!/usr/bin/env python3
"""
Thermal Memory Data Extractor for DMD Analysis
Cherokee AI Federation - Resonance Analysis
For Seven Generations
"""

import psycopg2
import numpy as np
from datetime import datetime, timedelta
import json
import os

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}


def extract_thermal_timeseries(days: int = 30, interval_hours: int = 6):
    """
    Extract thermal memory data as time series for DMD analysis.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        WITH time_buckets AS (
            SELECT
                date_trunc('hour', created_at) as bucket,
                temperature_score,
                current_stage
            FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '{days} days'
        )
        SELECT
            bucket,
            COUNT(*) as total_memories,
            AVG(temperature_score) as avg_temp,
            STDDEV(temperature_score) as temp_stddev,
            COUNT(*) FILTER (WHERE current_stage = 'WHITE_HOT') as white_hot,
            COUNT(*) FILTER (WHERE current_stage = 'RED_HOT') as red_hot,
            COUNT(*) FILTER (WHERE current_stage = 'HOT') as hot,
            COUNT(*) FILTER (WHERE current_stage = 'WARM') as warm,
            COUNT(*) FILTER (WHERE current_stage = 'COOL') as cool,
            COUNT(*) FILTER (WHERE current_stage = 'FRESH') as fresh
        FROM time_buckets
        GROUP BY bucket
        ORDER BY bucket
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return None, None

    timestamps = [row[0] for row in rows]

    data_matrix = np.array([
        [float(row[1]) for row in rows],  # total_memories
        [float(row[2] or 0) for row in rows],  # avg_temp
        [float(row[3] or 0) for row in rows],  # temp_stddev
        [float(row[4]) for row in rows],  # white_hot
        [float(row[5]) for row in rows],  # red_hot
        [float(row[6]) for row in rows],  # hot
        [float(row[7]) for row in rows],  # warm
        [float(row[8]) for row in rows],  # cool
        [float(row[9]) for row in rows],  # fresh
    ], dtype=float)

    return data_matrix, timestamps


if __name__ == '__main__':
    print("Extracting thermal time series...")
    data, timestamps = extract_thermal_timeseries(days=14, interval_hours=4)
    if data is not None:
        print(f"Data shape: {data.shape}")
        print(f"Time range: {timestamps[0]} to {timestamps[-1]}")
        np.save('/ganuda/data/thermal_timeseries.npy', data)
        print("Saved to /ganuda/data/thermal_timeseries.npy")
    else:
        print("No data found")
