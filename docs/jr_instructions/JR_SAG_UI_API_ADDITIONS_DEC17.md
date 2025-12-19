# Jr Instructions: SAG UI API Endpoint Additions

**Priority**: 1 (High)
**Assigned Jr**: Software Engineer Jr.
**Target**: redfin (192.168.132.223)
**File**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

---

## Overview

Add missing API endpoints to SAG Unified Interface. The app.py file has been restored to a clean state after sed command corruption. Add these endpoints carefully at the END of the file, BEFORE the final `if __name__ == "__main__":` block.

---

## ENDPOINT 1: /api/alerts

**Purpose**: Get unified alerts from sag_events with severity filtering

**Add this code** at approximately line 2730 (before `if __name__`):

```python
@app.route("/api/alerts")
def api_alerts():
    """Get unified alerts from events with severity filtering"""
    import psycopg2
    import psycopg2.extras
    try:
        severity = request.args.get("severity")
        limit = request.args.get("limit", 50, type=int)

        conn = psycopg2.connect(**event_manager.db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT id, title, description, source, tier as severity,
                   category, created_at, dismissed, reviewed
            FROM sag_events
            WHERE tier IN ('CRITICAL', 'WARNING', 'ACTION_REQUIRED')
            AND dismissed = false
        """
        params = []

        if severity:
            query += " AND tier = %s"
            params.append(severity.upper())

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        alerts = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in api_alerts: {e}")
        return jsonify({"error": str(e)}), 500
```

**Test**:
```bash
curl http://192.168.132.223:4000/api/alerts
curl http://192.168.132.223:4000/api/alerts?severity=CRITICAL
```

---

## ENDPOINT 2: /api/monitoring/overview

**Purpose**: Get health status from all federation services

**Add this code** after the alerts endpoint:

```python
@app.route("/api/monitoring/overview")
def api_monitoring_overview():
    """Get monitoring overview from all services"""
    import requests as http_requests
    import socket

    services_health = []

    # Check each service
    checks = [
        ('vLLM', 'http://192.168.132.223:8000/health'),
        ('LLM Gateway', 'http://192.168.132.223:8080/health'),
        ('SAG UI', 'http://192.168.132.223:4000/health'),
        ('Grafana', 'http://192.168.132.222:3000/api/health'),
    ]

    for name, url in checks:
        try:
            resp = http_requests.get(url, timeout=3)
            status = 'healthy' if resp.status_code == 200 else 'degraded'
            services_health.append({
                'name': name,
                'url': url,
                'status': status,
                'response_time_ms': int(resp.elapsed.total_seconds() * 1000)
            })
        except http_requests.exceptions.Timeout:
            services_health.append({'name': name, 'url': url, 'status': 'timeout', 'response_time_ms': 3000})
        except Exception as e:
            services_health.append({'name': name, 'url': url, 'status': 'error', 'error': str(e)})

    # Get database stats
    try:
        import psycopg2
        conn = psycopg2.connect(**event_manager.db_config)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM thermal_memory_archive")
        memory_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM council_votes")
        votes_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        db_stats = {'thermal_memories': memory_count, 'council_votes': votes_count, 'status': 'healthy'}
    except Exception as e:
        db_stats = {'status': 'error', 'error': str(e)}

    healthy = sum(1 for s in services_health if s['status'] == 'healthy')
    total = len(services_health)

    return jsonify({
        'overall_status': 'healthy' if healthy == total else 'degraded',
        'services': services_health,
        'database': db_stats,
        'summary': f'{healthy}/{total} services healthy',
        'timestamp': datetime.now().isoformat()
    })
```

**Test**:
```bash
curl http://192.168.132.223:4000/api/monitoring/overview
```

---

## ENDPOINT 3: /api/federation/nodes (Fix)

**Purpose**: Return all 6 federation nodes with proper reachability checks

**Find the existing FEDERATION_NODES configuration** and update to:

```python
FEDERATION_NODES = [
    {
        'node_id': 'redfin',
        'name': 'Cherokee (Redfin)',
        'hostname': '192.168.132.223',
        'role': 'GPU Inference & Gateway',
        'services': [
            {'name': 'vLLM', 'port': 8000, 'health': '/health'},
            {'name': 'LLM Gateway', 'port': 8080, 'health': '/health'},
            {'name': 'SAG UI', 'port': 4000, 'health': '/health'}
        ]
    },
    {
        'node_id': 'bluefin',
        'name': 'Bluefin',
        'hostname': '192.168.132.222',
        'role': 'Database & Analytics',
        'services': [
            {'name': 'PostgreSQL', 'port': 5432, 'health': None},
            {'name': 'Grafana', 'port': 3000, 'health': '/api/health'}
        ]
    },
    {
        'node_id': 'greenfin',
        'name': 'Greenfin',
        'hostname': '192.168.132.224',
        'role': 'Flow Monitoring',
        'services': [
            {'name': 'Promtail', 'port': 9080, 'health': '/ready'}
        ]
    },
    {
        'node_id': 'sasass',
        'name': 'Mac Studio (sasass)',
        'hostname': '192.168.132.241',
        'role': 'Edge Development',
        'services': []
    },
    {
        'node_id': 'sasass2',
        'name': 'Mac Studio (sasass2)',
        'hostname': '192.168.132.242',
        'role': 'Edge Development (BigMac/Dr.Joe)',
        'services': []
    },
    {
        'node_id': 'tpm-macbook',
        'name': 'TPM MacBook',
        'hostname': 'localhost',
        'role': 'Command Post',
        'services': []
    }
]
```

---

## DEPLOYMENT STEPS

1. **Backup first**:
```bash
cd /ganuda/home/dereadi/sag_unified_interface
cp app.py app.py.backup_$(date +%Y%m%d_%H%M%S)
```

2. **Make edits** using a text editor (nano, vim) - DO NOT use sed for multi-line edits

3. **Verify syntax**:
```bash
source /ganuda/home/dereadi/cherokee_venv/bin/activate
cd /ganuda/home/dereadi/sag_unified_interface
python3 -c "import app; print('Syntax OK')"
```

4. **Restart service**:
```bash
pkill -f "sag_unified_interface/app.py"
nohup /ganuda/home/dereadi/cherokee_venv/bin/python3 app.py > /dev/null 2>&1 &
```

5. **Test all endpoints**:
```bash
curl http://localhost:4000/api/alerts
curl http://localhost:4000/api/monitoring/overview
curl http://localhost:4000/api/federation/summary
```

---

## IMPORTANT NOTES

- DO NOT use sed for multi-line code additions - it causes corruption
- Use a proper text editor (nano, vim)
- Always backup before editing
- Test syntax before restarting
- The file currently ends around line 2731

---

*Created: December 17, 2025*
*FOR SEVEN GENERATIONS*
