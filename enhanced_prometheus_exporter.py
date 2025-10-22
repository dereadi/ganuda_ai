#!/usr/bin/env python3
"""
🔥 META JR - ENHANCED PROMETHEUS EXPORTER WITH SELF-REGULATION 🔥
Cherokee Constitutional AI - Observational Self-Regulation

This Prometheus exporter monitors thermal memory health and automatically
triggers audits when degraded performance is detected for 30+ minutes.

OpenAI Challenge Response: Requirement #2 - Self-Regulating Monitoring
"""

import psycopg2
import time
import json
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

# Core regression metrics
thermal_r2_multivariate = Gauge('thermal_r2_multivariate', 'R² multivariate model')
thermal_r2_1h_rolling = Gauge('thermal_r2_1h_rolling', '1-hour rolling average R²')
thermal_r2_24h_rolling = Gauge('thermal_r2_24h_rolling', '24-hour rolling average R²')

# Health state classification
thermal_health_state = Gauge('thermal_health_state', 'Health state (2=healthy, 1=warning, 0=degraded)')
thermal_degraded_duration_minutes = Gauge('thermal_degraded_duration_minutes', 'Minutes in degraded state')

# Temperature metrics
thermal_sacred_temperature = Gauge('thermal_sacred_temperature', 'Avg sacred memory temp')
thermal_normal_temperature = Gauge('thermal_normal_temperature', 'Avg normal memory temp')
thermal_sacred_pvalue = Gauge('thermal_sacred_pvalue', 'P-value for sacred vs normal')

# System metrics
thermal_sample_size = Gauge('thermal_sample_size', 'Number of memories analyzed')
thermal_phase_coherence_mean = Gauge('thermal_phase_coherence_mean', 'Avg coherence')

# Self-regulation metrics
thermal_auto_audit_triggered = Counter('thermal_auto_audit_triggered_total', 'Auto-audit trigger count')
thermal_last_audit_timestamp = Gauge('thermal_last_audit_timestamp', 'Unix timestamp of last audit')

# Constitutional protection metrics (Medicine Woman's requirement)
thermal_sacred_min_temperature = Gauge('thermal_sacred_min_temperature', 'Minimum sacred memory temperature')
thermal_sacred_count = Gauge('thermal_sacred_count', 'Number of sacred memories')
thermal_constitutional_violation = Counter('thermal_constitutional_violation_total', 'Sacred temp < 40° violations')

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Connect to REDFIN thermal memory database"""
    return psycopg2.connect(
        host='192.168.132.222',
        port=5432,
        user='claude',
        password='jawaseatlasers2',
        database='zammad_production'
    )

# =============================================================================
# REGRESSION ANALYSIS
# =============================================================================

def calculate_regression_metrics(conn):
    """Calculate thermal regression R² score"""
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

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()

    if len(rows) < 10:
        return None

    # Prepare data
    temperatures = np.array([r[0] for r in rows])
    access_counts = np.array([r[1] for r in rows])
    coherences = np.array([r[2] for r in rows])
    sacred = np.array([r[3] for r in rows])

    # Multivariate regression
    X = np.column_stack([access_counts, coherences, sacred])
    y = temperatures

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)

    # Sacred vs Normal statistics
    sacred_temps = temperatures[sacred == 1]
    normal_temps = temperatures[sacred == 0]

    from scipy import stats
    if len(sacred_temps) > 1 and len(normal_temps) > 1:
        t_stat, p_value = stats.ttest_ind(sacred_temps, normal_temps)
    else:
        p_value = 1.0

    return {
        'r2': float(r2),
        'sample_size': len(rows),
        'sacred_temp': float(sacred_temps.mean()) if len(sacred_temps) > 0 else 0,
        'sacred_temp_min': float(sacred_temps.min()) if len(sacred_temps) > 0 else 0,
        'sacred_count': int(len(sacred_temps)),
        'normal_temp': float(normal_temps.mean()) if len(normal_temps) > 0 else 0,
        'p_value': float(p_value),
        'coherence_mean': float(coherences.mean()),
        'timestamp': datetime.now().isoformat()
    }

# =============================================================================
# ROLLING AVERAGES
# =============================================================================

class RollingAverageTracker:
    """Track rolling averages for R² scores"""

    def __init__(self):
        self.history = []  # List of (timestamp, r2) tuples

    def add_sample(self, r2):
        """Add new R² sample"""
        self.history.append((datetime.now(), r2))

        # Remove samples older than 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        self.history = [(ts, r2) for ts, r2 in self.history if ts > cutoff]

    def get_1h_average(self):
        """Calculate 1-hour rolling average"""
        cutoff = datetime.now() - timedelta(hours=1)
        recent = [r2 for ts, r2 in self.history if ts > cutoff]
        return np.mean(recent) if recent else None

    def get_24h_average(self):
        """Calculate 24-hour rolling average"""
        if not self.history:
            return None
        return np.mean([r2 for ts, r2 in self.history])

# =============================================================================
# HEALTH STATE CLASSIFICATION
# =============================================================================

class HealthStateMonitor:
    """Monitor health state and trigger auto-audits"""

    def __init__(self):
        self.degraded_since = None
        self.last_audit = None
        self.sacred_violation_since = None  # Track constitutional violations

    def classify_health(self, r2):
        """Classify health state based on R² score"""
        if r2 >= 0.65:
            return 2, "healthy"
        elif r2 >= 0.50:
            return 1, "warning"
        else:
            return 0, "degraded"

    def update(self, r2, metrics=None):
        """Update health state and check for auto-audit trigger"""
        state_code, state_name = self.classify_health(r2)

        if state_code == 0:  # Degraded
            if self.degraded_since is None:
                self.degraded_since = datetime.now()
                print(f"⚠️  DEGRADED STATE ENTERED (R² = {r2:.4f})")

            degraded_duration = (datetime.now() - self.degraded_since).total_seconds() / 60

            # Auto-audit trigger: 30 minutes in degraded state
            if degraded_duration >= 30 and (self.last_audit is None or
                (datetime.now() - self.last_audit).total_seconds() >= 1800):
                self.trigger_audit(r2, degraded_duration, metrics=metrics)
                self.last_audit = datetime.now()

            return state_code, state_name, degraded_duration
        else:
            if self.degraded_since is not None:
                duration = (datetime.now() - self.degraded_since).total_seconds() / 60
                print(f"✅ RECOVERED FROM DEGRADED STATE (was degraded for {duration:.1f} minutes)")
            self.degraded_since = None
            return state_code, state_name, 0

    def check_sacred_violation(self, sacred_min_temp, sacred_count):
        """Check for constitutional violations (Medicine Woman's requirement)"""
        CONSTITUTIONAL_FLOOR = 40.0  # Sacred memories must stay >= 40°

        if sacred_count > 0 and sacred_min_temp < CONSTITUTIONAL_FLOOR:
            if self.sacred_violation_since is None:
                self.sacred_violation_since = datetime.now()
                print(f"⚠️  CONSTITUTIONAL VIOLATION DETECTED: Sacred memory at {sacred_min_temp:.2f}° (floor: 40°)")

            violation_duration = (datetime.now() - self.sacred_violation_since).total_seconds() / 60

            # Trigger audit after 10 minutes of violation
            if violation_duration >= 10 and (self.last_audit is None or
                (datetime.now() - self.last_audit).total_seconds() >= 600):
                self.trigger_constitutional_audit(sacred_min_temp, sacred_count, violation_duration)
                self.last_audit = datetime.now()
                thermal_constitutional_violation.inc()

            return True, violation_duration
        else:
            if self.sacred_violation_since is not None:
                duration = (datetime.now() - self.sacred_violation_since).total_seconds() / 60
                print(f"✅ CONSTITUTIONAL COMPLIANCE RESTORED (violation lasted {duration:.1f} minutes)")
            self.sacred_violation_since = None
            return False, 0

    def trigger_audit(self, r2, degraded_duration, metrics=None):
        """Trigger automatic audit"""
        print("\n" + "="*70)
        print("🚨 AUTO-AUDIT TRIGGERED")
        print("="*70)
        print(f"   Reason: Degraded state for {degraded_duration:.1f} minutes")
        print(f"   Current R²: {r2:.4f} (threshold: 0.50)")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("="*70 + "\n")

        # Increment counter
        thermal_auto_audit_triggered.inc()

        # Log audit event (with sacred memory stats per Medicine Woman's requirement)
        audit_event = {
            'timestamp': datetime.now().isoformat(),
            'r2': r2,
            'degraded_duration_minutes': degraded_duration,
            'trigger': 'auto_audit_30min_degraded',
            'sacred_count': metrics.get('sacred_count', 0) if metrics else 0,
            'sacred_temp_min': metrics.get('sacred_temp_min', 0) if metrics else 0,
            'sacred_temp_avg': metrics.get('sacred_temp', 0) if metrics else 0
        }

        with open('thermal_audit_log.json', 'a') as f:
            f.write(json.dumps(audit_event) + '\n')

        # Emergency council could be called here in production
        # For now, just log the event

    def trigger_constitutional_audit(self, sacred_min_temp, sacred_count, violation_duration):
        """Trigger constitutional violation audit"""
        print("\n" + "="*70)
        print("🚨 CONSTITUTIONAL VIOLATION AUDIT")
        print("="*70)
        print(f"   Violation: Sacred memory temperature < 40°")
        print(f"   Current minimum: {sacred_min_temp:.2f}°")
        print(f"   Sacred memory count: {sacred_count}")
        print(f"   Duration: {violation_duration:.1f} minutes")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("="*70 + "\n")

        # Log constitutional violation
        audit_event = {
            'timestamp': datetime.now().isoformat(),
            'trigger': 'constitutional_violation',
            'sacred_min_temp': sacred_min_temp,
            'sacred_count': sacred_count,
            'violation_duration_minutes': violation_duration,
            'constitutional_floor': 40.0
        }

        with open('thermal_audit_log.json', 'a') as f:
            f.write(json.dumps(audit_event) + '\n')

        # In production, this would召集 Emergency Council

# =============================================================================
# MAIN MONITORING LOOP
# =============================================================================

def monitor_thermal_health():
    """Main monitoring loop with self-regulation"""
    print("🔥 ENHANCED PROMETHEUS EXPORTER - SELF-REGULATING THERMAL MONITOR")
    print("="*70)
    print("   OpenAI Requirement #2: Observational Self-Regulation")
    print("   Features:")
    print("     - Rolling averages (1h, 24h)")
    print("     - Health state classification (healthy/warning/degraded)")
    print("     - Auto-audit trigger (30 min degraded)")
    print("="*70 + "\n")

    rolling_tracker = RollingAverageTracker()
    health_monitor = HealthStateMonitor()

    while True:
        try:
            conn = get_connection()
            metrics = calculate_regression_metrics(conn)
            conn.close()

            if metrics:
                # Update core metrics
                thermal_r2_multivariate.set(metrics['r2'])
                thermal_sample_size.set(metrics['sample_size'])
                thermal_sacred_temperature.set(metrics['sacred_temp'])
                thermal_normal_temperature.set(metrics['normal_temp'])
                thermal_sacred_pvalue.set(metrics['p_value'])
                thermal_phase_coherence_mean.set(metrics['coherence_mean'])

                # Update constitutional protection metrics (Medicine Woman's requirement)
                thermal_sacred_min_temperature.set(metrics['sacred_temp_min'])
                thermal_sacred_count.set(metrics['sacred_count'])

                # Update rolling averages
                rolling_tracker.add_sample(metrics['r2'])
                r2_1h = rolling_tracker.get_1h_average()
                r2_24h = rolling_tracker.get_24h_average()

                if r2_1h:
                    thermal_r2_1h_rolling.set(r2_1h)
                if r2_24h:
                    thermal_r2_24h_rolling.set(r2_24h)

                # Update health state
                state_code, state_name, degraded_minutes = health_monitor.update(metrics['r2'], metrics=metrics)
                thermal_health_state.set(state_code)
                thermal_degraded_duration_minutes.set(degraded_minutes)

                # Check for constitutional violations
                violation_active, violation_duration = health_monitor.check_sacred_violation(
                    metrics['sacred_temp_min'],
                    metrics['sacred_count']
                )

                # Update last audit timestamp if exists
                if health_monitor.last_audit:
                    thermal_last_audit_timestamp.set(health_monitor.last_audit.timestamp())

                # Log status
                status_msg = (f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                             f"R²={metrics['r2']:.4f} | "
                             f"1h={r2_1h:.4f if r2_1h else 'N/A'} | "
                             f"24h={r2_24h:.4f if r2_24h else 'N/A'} | "
                             f"State={state_name.upper()} | "
                             f"Sacred={metrics['sacred_temp_min']:.1f}°")

                if violation_active:
                    status_msg += f" ⚠️ VIOLATION"

                print(status_msg)

            time.sleep(60)  # Check every minute

        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            time.sleep(60)

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Start Prometheus HTTP server on port 9100
    start_http_server(9100)
    print(f"📊 Prometheus metrics server started on :9100")
    print(f"   Visit http://localhost:9100/metrics\n")

    # Start monitoring
    monitor_thermal_health()
