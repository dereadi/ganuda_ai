#!/usr/bin/env python3
"""
SAG UI API Endpoint Additions
Run on redfin to add missing endpoints to app.py
"""

import shutil
from datetime import datetime

APP_FILE = "/ganuda/home/dereadi/sag_unified_interface/app.py"

ALERTS_ENDPOINT = '''
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

'''

MONITORING_ENDPOINT = '''
@app.route("/api/monitoring/overview")
def api_monitoring_overview():
    """Get monitoring overview from all services"""
    import requests as http_requests
    import psycopg2

    services_health = []

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

    try:
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

'''

def main():
    # Backup
    backup_path = f"{APP_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(APP_FILE, backup_path)
    print(f"Backup created: {backup_path}")

    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Check if endpoints already exist
    alerts_exists = '@app.route("/api/alerts")' in content
    monitoring_exists = '@app.route("/api/monitoring/overview")' in content

    if alerts_exists:
        print("Alerts endpoint already exists, skipping")

    if monitoring_exists:
        print("Monitoring endpoint already exists, skipping")

    if alerts_exists and monitoring_exists:
        print("Both endpoints exist, nothing to do")
        return

    # Find the main block to insert before (unique marker)
    marker = "if __name__ == '__main__':"

    if marker not in content:
        print(f"Error: Could not find marker '{marker}' in app.py")
        return

    # Build insertion
    insertion = ""
    if not alerts_exists:
        insertion += ALERTS_ENDPOINT
        print("Will add /api/alerts endpoint")
    if not monitoring_exists:
        insertion += MONITORING_ENDPOINT
        print("Will add /api/monitoring/overview endpoint")

    # Insert before the main block (only once, since marker is unique)
    content = content.replace(marker, insertion + "\n" + marker, 1)

    with open(APP_FILE, 'w') as f:
        f.write(content)

    print("Endpoints added successfully!")
    print(f"File updated: {APP_FILE}")

if __name__ == "__main__":
    main()
