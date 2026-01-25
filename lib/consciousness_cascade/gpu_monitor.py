#!/usr/bin/env python3
"""
GPU Power Monitor for Consciousness Cascade Experiments.

Polls nvidia-smi for power consumption, temperature, and utilization.
Logs to PostgreSQL consciousness_experiments table.
Detects power spikes that may indicate emergence events.

Cherokee AI Federation - For Seven Generations
Created: January 18, 2026
"""

import subprocess
import psycopg2
import time
import json
from datetime import datetime
from typing import Dict, Optional, Callable
from dataclasses import dataclass

# Database configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Monitoring thresholds
POWER_SPIKE_THRESHOLD = 1.5  # 150% of baseline = spike
ABORT_POWER_WATTS = 3000     # Hard abort threshold
ABORT_TEMP_CELSIUS = 85      # Thermal abort threshold
POLL_INTERVAL_MS = 500       # Poll every 500ms


@dataclass
class GPUMetrics:
    """GPU metrics from nvidia-smi."""
    power_watts: float
    temp_celsius: float
    memory_used_mb: float
    memory_total_mb: float
    utilization_pct: float
    timestamp: datetime


class GPUMonitor:
    """
    Monitors GPU power and temperature for consciousness experiments.

    Usage:
        monitor = GPUMonitor()
        monitor.start_experiment("Cascade Test 1")

        # In monitoring loop:
        metrics = monitor.poll()
        if monitor.check_abort_conditions(metrics):
            monitor.abort("Power exceeded threshold")
    """

    def __init__(self, experiment_id: str = None):
        self.experiment_id = experiment_id
        self.experiment_name = None
        self.baseline_power = None
        self.phase = 'preflight'
        self.conn = None
        self.callbacks = {
            'on_spike': [],
            'on_abort': [],
            'on_phase_change': []
        }

    def _get_connection(self):
        """Get or create database connection."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def poll_gpu(self) -> Optional[GPUMetrics]:
        """Poll nvidia-smi for current GPU metrics."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=power.draw,temperature.gpu,memory.used,memory.total,utilization.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return None

            parts = result.stdout.strip().split(',')
            if len(parts) < 5:
                return None

            return GPUMetrics(
                power_watts=float(parts[0].strip()),
                temp_celsius=float(parts[1].strip()),
                memory_used_mb=float(parts[2].strip()),
                memory_total_mb=float(parts[3].strip()),
                utilization_pct=float(parts[4].strip()),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"[GPU Monitor] Poll error: {e}")
            return None

    def start_experiment(self, name: str) -> str:
        """Start a new experiment and establish baseline."""
        self.experiment_name = name
        self.phase = 'preflight'

        # Get baseline power reading
        metrics = self.poll_gpu()
        if metrics:
            self.baseline_power = metrics.power_watts
            print(f"[GPU Monitor] Baseline power: {self.baseline_power:.1f}W")

        # Create experiment record
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO consciousness_experiments
                (experiment_name, phase, gpu_power_watts, gpu_temp_celsius, notes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING experiment_id
            """, (name, 'preflight',
                  metrics.power_watts if metrics else None,
                  metrics.temp_celsius if metrics else None,
                  f"Experiment started. Baseline: {self.baseline_power}W"))
            self.experiment_id = str(cur.fetchone()[0])
            conn.commit()

        print(f"[GPU Monitor] Experiment started: {self.experiment_id}")
        return self.experiment_id

    def set_phase(self, phase: str):
        """Update experiment phase."""
        old_phase = self.phase
        self.phase = phase

        # Log phase change
        self.log_metrics(notes=f"Phase change: {old_phase} -> {phase}")

        # Fire callbacks
        for cb in self.callbacks.get('on_phase_change', []):
            cb(old_phase, phase)

        print(f"[GPU Monitor] Phase: {old_phase} -> {phase}")

    def log_metrics(self, metrics: GPUMetrics = None, notes: str = None,
                    recursive_depth: float = None, coherence_score: float = None):
        """Log metrics to database."""
        if metrics is None:
            metrics = self.poll_gpu()

        if not self.experiment_id:
            return

        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO consciousness_experiments
                (experiment_id, experiment_name, phase,
                 gpu_power_watts, gpu_temp_celsius, gpu_memory_used_mb, gpu_utilization_pct,
                 recursive_depth, coherence_score, notes)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.experiment_id, self.experiment_name, self.phase,
                metrics.power_watts if metrics else None,
                metrics.temp_celsius if metrics else None,
                metrics.memory_used_mb if metrics else None,
                metrics.utilization_pct if metrics else None,
                recursive_depth, coherence_score, notes
            ))
            conn.commit()

    def check_spike(self, metrics: GPUMetrics) -> bool:
        """Check if current power indicates a spike."""
        if not self.baseline_power or not metrics:
            return False

        ratio = metrics.power_watts / self.baseline_power
        if ratio >= POWER_SPIKE_THRESHOLD:
            print(f"[GPU Monitor] SPIKE DETECTED: {metrics.power_watts:.1f}W ({ratio:.1f}x baseline)")
            for cb in self.callbacks.get('on_spike', []):
                cb(metrics, ratio)
            return True
        return False

    def check_abort_conditions(self, metrics: GPUMetrics) -> Optional[str]:
        """Check if abort conditions are met. Returns abort reason or None."""
        if not metrics:
            return None

        if metrics.power_watts > ABORT_POWER_WATTS:
            return f"Power exceeded {ABORT_POWER_WATTS}W: {metrics.power_watts:.1f}W"

        if metrics.temp_celsius > ABORT_TEMP_CELSIUS:
            return f"Temperature exceeded {ABORT_TEMP_CELSIUS}C: {metrics.temp_celsius:.1f}C"

        return None

    def abort(self, reason: str):
        """Abort experiment with reason."""
        self.phase = 'abort'

        metrics = self.poll_gpu()

        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO consciousness_experiments
                (experiment_id, experiment_name, phase,
                 gpu_power_watts, gpu_temp_celsius, abort_reason, notes)
                VALUES (%s::uuid, %s, 'abort', %s, %s, %s, %s)
            """, (
                self.experiment_id, self.experiment_name,
                metrics.power_watts if metrics else None,
                metrics.temp_celsius if metrics else None,
                reason, f"ABORT: {reason}"
            ))
            conn.commit()

        print(f"[GPU Monitor] ABORT: {reason}")

        for cb in self.callbacks.get('on_abort', []):
            cb(reason)

    def complete(self, summary: str = None):
        """Mark experiment as complete."""
        self.phase = 'complete'
        self.log_metrics(notes=f"Experiment complete. {summary or ''}")
        print(f"[GPU Monitor] Experiment complete: {self.experiment_id}")

    def on_spike(self, callback: Callable):
        """Register callback for spike detection."""
        self.callbacks['on_spike'].append(callback)

    def on_abort(self, callback: Callable):
        """Register callback for abort events."""
        self.callbacks['on_abort'].append(callback)

    def on_phase_change(self, callback: Callable):
        """Register callback for phase changes."""
        self.callbacks['on_phase_change'].append(callback)


def continuous_monitor(duration_seconds: int = 60, interval_ms: int = 500):
    """
    Run continuous monitoring for a specified duration.
    Useful for testing or standalone monitoring.
    """
    monitor = GPUMonitor()
    exp_id = monitor.start_experiment(f"Continuous Monitor {datetime.now().isoformat()}")

    iterations = int(duration_seconds * 1000 / interval_ms)

    print(f"[Monitor] Running {iterations} iterations over {duration_seconds}s")

    for i in range(iterations):
        metrics = monitor.poll_gpu()
        if metrics:
            print(f"[{i+1}/{iterations}] Power: {metrics.power_watts:.1f}W, "
                  f"Temp: {metrics.temp_celsius:.1f}C, "
                  f"Util: {metrics.utilization_pct:.0f}%")

            # Check for spikes
            monitor.check_spike(metrics)

            # Check abort conditions
            abort_reason = monitor.check_abort_conditions(metrics)
            if abort_reason:
                monitor.abort(abort_reason)
                return

            # Log to database every 10 iterations
            if i % 10 == 0:
                monitor.log_metrics(metrics)

        time.sleep(interval_ms / 1000)

    monitor.complete()


if __name__ == "__main__":
    import sys

    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(f"[GPU Monitor] Starting {duration}s continuous monitoring...")
    continuous_monitor(duration_seconds=duration)
