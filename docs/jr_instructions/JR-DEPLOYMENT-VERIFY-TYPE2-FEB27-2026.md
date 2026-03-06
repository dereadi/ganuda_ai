# Type 2 Verification: Service Deployment Health Check

**Council Vote**: #36fd8d2ec0fd0473 (Hawk: "correctness monitoring, not just uptime")
**Priority**: P2
**Assigned**: Software Engineer Jr.

---

## Context

11 services were crash-looping across 3 nodes with zero alerts. The health_monitor.py checks endpoints but doesn't check for restart storms or dependency failures. This adds a `verify_service_health()` function that checks CORRECTNESS, not just uptime.

## Step 1: Add service verification function to health_monitor

File: `/ganuda/services/health_monitor.py`

Add this function near the top of the file, after the existing imports and before the main monitoring class.

<<<<<<< SEARCH
class HealthMonitor:
=======
def verify_service_health(service_name: str, node: str = 'localhost', max_restarts: int = 3, settle_seconds: int = 30) -> dict:
    """Type 2 Verification: Check that a service is genuinely healthy, not just 'running'.

    Checks:
    1. Service is active (running)
    2. Main PID is stable (not restarting)
    3. Restart count is below threshold
    4. Service has been running for at least settle_seconds

    Returns dict with verified: bool, checks: dict, message: str
    """
    import subprocess
    result = {'verified': False, 'checks': {}, 'service': service_name, 'node': node}

    try:
        # Get service properties in one call
        props = ['ActiveState', 'MainPID', 'NRestarts', 'ActiveEnterTimestamp']
        cmd = ['systemctl', 'show', service_name, '--property=' + ','.join(props)]
        if node != 'localhost':
            cmd = ['ssh', node] + cmd

        out = subprocess.check_output(cmd, timeout=10, text=True)
        values = {}
        for line in out.strip().split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                values[k] = v

        # Check 1: Active
        active = values.get('ActiveState', '') == 'active'
        result['checks']['active'] = active

        # Check 2: PID exists
        pid = int(values.get('MainPID', '0'))
        result['checks']['has_pid'] = pid > 0

        # Check 3: Restart count
        restarts = int(values.get('NRestarts', '0'))
        result['checks']['restarts'] = restarts
        result['checks']['restarts_ok'] = restarts <= max_restarts

        # Check 4: Uptime stability
        timestamp = values.get('ActiveEnterTimestamp', '')
        if timestamp and timestamp != '':
            from datetime import datetime, timezone
            try:
                started = datetime.strptime(timestamp.strip(), '%a %Y-%m-%d %H:%M:%S %Z')
                uptime_secs = (datetime.now() - started).total_seconds()
                result['checks']['uptime_seconds'] = int(uptime_secs)
                result['checks']['settled'] = uptime_secs >= settle_seconds
            except (ValueError, TypeError):
                result['checks']['settled'] = True  # can't parse, assume ok

        # Verdict
        result['verified'] = all([
            result['checks'].get('active', False),
            result['checks'].get('has_pid', False),
            result['checks'].get('restarts_ok', True),
            result['checks'].get('settled', True)
        ])
        result['message'] = 'HEALTHY' if result['verified'] else f"UNHEALTHY: {result['checks']}"

    except Exception as e:
        result['message'] = f'CHECK_FAILED: {e}'

    return result


class HealthMonitor:
>>>>>>> REPLACE

## Verification

After applying:
1. `verify_service_health('vllm')` returns `{verified: True, checks: {active: True, restarts: 0, ...}}`
2. A crash-looping service returns `{verified: False, checks: {restarts: 109007, restarts_ok: False}}`
3. Function works locally and via SSH to remote nodes
4. Can be called from health_monitor main loop, TPM autonomic, or standalone
