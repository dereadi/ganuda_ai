#!/usr/bin/env python3
"""
Shield Server — Rule-based Anomaly Engine (P-3).
LLM analysis added in P-2. Reference: fire_guard.py threshold pattern.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger('shield.anomaly')

# Anomaly rules — each returns (anomaly_type, severity, description) or None
RULES = []


def rule(func):
    """Decorator to register anomaly rules."""
    RULES.append(func)
    return func


@rule
def check_off_hours(snapshot: Dict, baseline: Dict) -> Optional[tuple]:
    """Activity outside normal working hours."""
    hour = datetime.fromisoformat(snapshot['timestamp']).hour
    if baseline.get('typical_hours'):
        start, end = baseline['typical_hours']
        if hour < start or hour > end:
            return ("off_hours_access", "warning",
                    f"Activity at {hour}:00 — outside typical hours ({start}:00-{end}:00)")
    elif hour < 6 or hour > 22:
        return ("off_hours_access", "warning",
                f"Activity at {hour}:00 — outside default hours (6:00-22:00)")
    return None


@rule
def check_credential_clipboard(snapshot: Dict, baseline: Dict) -> Optional[tuple]:
    """Sensitive content detected in clipboard."""
    if snapshot.get('clipboard_sensitive'):
        return ("credential_clipboard", "warning",
                f"Sensitive content ({snapshot.get('clipboard_type', '?')}) detected in clipboard")
    return None


@rule
def check_unusual_application(snapshot: Dict, baseline: Dict) -> Optional[tuple]:
    """Application not seen in baseline period."""
    app = snapshot.get('active_application', '')
    known_apps = baseline.get('known_applications', set())
    if app and known_apps and app not in known_apps:
        return ("unusual_application", "info",
                f"Application '{app}' not in baseline set")
    return None


@rule
def check_high_network(snapshot: Dict, baseline: Dict) -> Optional[tuple]:
    """Network connections significantly above baseline."""
    conn_count = snapshot.get('network_connections', 0)
    baseline_avg = baseline.get('avg_network_connections', 10)
    if conn_count > baseline_avg * 3 and conn_count > 20:
        return ("unusual_network", "warning",
                f"Network connections ({conn_count}) significantly above baseline ({baseline_avg})")
    return None


class AnomalyEngine:
    """Rule-based anomaly detection with baseline learning."""

    def __init__(self):
        self.baselines = {}  # per-employee baselines
        self.learning_period_days = 14
        self.history = defaultdict(list)  # per-employee recent history

    def update_baseline(self, employee_id: str, snapshot: Dict):
        """Update behavioral baseline from activity snapshot."""
        self.history[employee_id].append(snapshot)

        # Keep last 14 days of history
        cutoff = datetime.now() - timedelta(days=self.learning_period_days)
        self.history[employee_id] = [
            s for s in self.history[employee_id]
            if datetime.fromisoformat(s['timestamp']) > cutoff
        ]

        history = self.history[employee_id]
        if len(history) < 10:
            return  # Not enough data for baseline

        # Build baseline
        hours = [datetime.fromisoformat(s['timestamp']).hour for s in history]
        apps = set(s.get('active_application', '') for s in history if s.get('active_application'))
        net_conns = [s.get('network_connections', 0) for s in history if s.get('network_connections', 0) > 0]

        self.baselines[employee_id] = {
            'typical_hours': (min(hours), max(hours)) if hours else None,
            'known_applications': apps,
            'avg_network_connections': sum(net_conns) / len(net_conns) if net_conns else 10,
            'sample_count': len(history),
            'updated_at': datetime.now().isoformat(),
        }

    def evaluate(self, snapshot: Dict) -> List[Dict]:
        """Run all anomaly rules against a snapshot. Returns list of anomalies."""
        employee_id = snapshot.get('employee_id', '')
        baseline = self.baselines.get(employee_id, {})

        # Update baseline
        self.update_baseline(employee_id, snapshot)

        # If still in learning period, don't flag anomalies
        if baseline.get('sample_count', 0) < 10:
            return []

        anomalies = []
        for rule_func in RULES:
            try:
                result = rule_func(snapshot, baseline)
                if result:
                    anomaly_type, severity, description = result
                    anomalies.append({
                        'anomaly_type': anomaly_type,
                        'severity': severity,
                        'description': description,
                        'machine_id': snapshot.get('machine_id', ''),
                        'employee_id': employee_id,
                        'trigger_data': {
                            'snapshot_timestamp': snapshot.get('timestamp'),
                            'rule': rule_func.__name__,
                        },
                        'detected_at': datetime.now().isoformat(),
                    })
            except Exception as e:
                logger.warning(f"Rule {rule_func.__name__} failed: {e}")

        return anomalies


def check_missing_heartbeat(agents: Dict, threshold_seconds: int = 300) -> List[Dict]:
    """Check for agents that haven't sent a heartbeat. Run periodically on server."""
    anomalies = []
    now = datetime.now()
    for machine_id, agent in agents.items():
        last_hb = agent.get('last_heartbeat')
        if last_hb:
            if isinstance(last_hb, str):
                last_hb = datetime.fromisoformat(last_hb)
            if (now - last_hb).total_seconds() > threshold_seconds:
                anomalies.append({
                    'anomaly_type': 'missing_heartbeat',
                    'severity': 'warning',
                    'description': f"Agent {machine_id} last heartbeat {int((now - last_hb).total_seconds())}s ago",
                    'machine_id': machine_id,
                    'employee_id': agent.get('employee_id', ''),
                    'detected_at': now.isoformat(),
                })
    return anomalies
