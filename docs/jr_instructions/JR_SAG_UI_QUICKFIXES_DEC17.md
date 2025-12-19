# Jr Instructions: SAG UI Quick Fixes

**Priority**: 1 (High)
**Estimated Effort**: 2-3 hours per fix
**Prerequisites**: Access to redfin, bluefin PostgreSQL

---

## FIX 1: Create /api/alerts Endpoint

**Problem**: Alerts tab returns "Not found" - no `/api/alerts` endpoint exists

**Location**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

**Add this route** (after line ~800, near other sidebar routes):

```python
@app.route('/api/alerts')
def api_alerts():
    """Get unified alerts from events with severity filtering"""
    try:
        severity = request.args.get('severity')  # CRITICAL, WARNING, INFO
        limit = request.args.get('limit', 50, type=int)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT
                id,
                title,
                description,
                source,
                tier as severity,
                category,
                created_at,
                dismissed,
                reviewed
            FROM event_stream
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
            'count': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in api_alerts: {e}")
        return jsonify({'error': str(e)}), 500
```

**Test**:
```bash
curl http://localhost:4000/api/alerts
curl http://localhost:4000/api/alerts?severity=CRITICAL
```

---

## FIX 2: Fix Federation Nodes Configuration

**Problem**: Only 2 nodes configured, all show "unreachable"

**Location**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

**Find the FEDERATION_NODES or similar config** (around line 937) and replace with:

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

**Fix reachability check** - find the check_node_health function and ensure it handles localhost:

```python
def check_node_health(node):
    """Check if a node is reachable"""
    import socket

    hostname = node.get('hostname', '')

    # Skip localhost/local nodes (always reachable from their perspective)
    if hostname in ('localhost', '127.0.0.1'):
        return {**node, 'status': 'healthy', 'reachable': True, 'last_check': datetime.now().isoformat()}

    try:
        # Try TCP connect to first service port, or default to SSH (22)
        port = 22
        if node.get('services'):
            port = node['services'][0].get('port', 22)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((hostname, port))
        sock.close()

        reachable = (result == 0)
        return {
            **node,
            'status': 'healthy' if reachable else 'unreachable',
            'reachable': reachable,
            'last_check': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            **node,
            'status': 'unreachable',
            'reachable': False,
            'last_check': datetime.now().isoformat(),
            'error': str(e)
        }
```

---

## FIX 3: Populate Kanban from Jr Work Queue

**Problem**: Kanban shows empty but we have tasks in jr_work_queue table

**Option A**: Modify `/api/kanban/tickets` to pull from jr_work_queue:

```python
@app.route('/api/kanban/tickets')
def api_kanban_tickets():
    """Get tickets from jr_work_queue for Kanban board"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Pull from jr_work_queue table
        cur.execute("""
            SELECT
                task_id as id,
                title,
                instruction_file as description,
                assigned_jr as assignee,
                priority,
                status,
                created_at,
                updated_at
            FROM jr_work_queue
            ORDER BY priority ASC, created_at DESC
        """)
        tickets = cur.fetchall()
        cur.close()
        conn.close()

        # Map status to Kanban columns
        for ticket in tickets:
            if ticket['status'] == 'pending':
                ticket['column'] = 'backlog'
            elif ticket['status'] == 'in_progress':
                ticket['column'] = 'in_progress'
            elif ticket['status'] == 'completed':
                ticket['column'] = 'done'
            else:
                ticket['column'] = 'backlog'

        return jsonify({
            'count': len(tickets),
            'tickets': tickets,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in api_kanban_tickets: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## FIX 4: Create Calendar Events Table and API

**Database Schema** (run on bluefin):
```sql
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    all_day BOOLEAN DEFAULT false,
    category VARCHAR(50),  -- meeting, deadline, reminder, maintenance
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add some sample events
INSERT INTO calendar_events (title, description, start_time, category, created_by) VALUES
('Daily Standup', 'Cherokee AI team standup', NOW() + INTERVAL '1 day', 'meeting', 'system'),
('Backup Window', 'Weekly backup to bluefin 16TB', NOW() + INTERVAL '7 days', 'maintenance', 'system');
```

**API Endpoint**:
```python
@app.route('/api/calendar/events')
def api_calendar_events():
    """Get calendar events"""
    try:
        start = request.args.get('start')  # ISO date
        end = request.args.get('end')      # ISO date

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = "SELECT * FROM calendar_events WHERE 1=1"
        params = []

        if start:
            query += " AND start_time >= %s"
            params.append(start)
        if end:
            query += " AND start_time <= %s"
            params.append(end)

        query += " ORDER BY start_time ASC"

        cur.execute(query, params)
        events = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'count': len(events),
            'events': events
        })
    except Exception as e:
        app.logger.error(f"Error in api_calendar_events: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/calendar/events', methods=['POST'])
def api_create_calendar_event():
    """Create a calendar event"""
    try:
        data = request.json

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO calendar_events (title, description, start_time, end_time, all_day, category, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('title'),
            data.get('description'),
            data.get('start_time'),
            data.get('end_time'),
            data.get('all_day', False),
            data.get('category', 'meeting'),
            data.get('created_by', 'api')
        ))

        event_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'id': event_id, 'message': 'Event created'})
    except Exception as e:
        app.logger.error(f"Error creating calendar event: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## FIX 5: Create Monitoring Overview API

**API Endpoint**:
```python
@app.route('/api/monitoring/overview')
def api_monitoring_overview():
    """Get monitoring overview from all services"""
    import requests

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
            resp = requests.get(url, timeout=3)
            status = 'healthy' if resp.status_code == 200 else 'degraded'
            services_health.append({
                'name': name,
                'url': url,
                'status': status,
                'response_time_ms': int(resp.elapsed.total_seconds() * 1000),
                'details': resp.json() if resp.headers.get('content-type', '').startswith('application/json') else None
            })
        except requests.exceptions.Timeout:
            services_health.append({'name': name, 'url': url, 'status': 'timeout', 'response_time_ms': 3000})
        except Exception as e:
            services_health.append({'name': name, 'url': url, 'status': 'error', 'error': str(e)})

    # Get database stats
    try:
        conn = get_db_connection()
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

---

## FIX 6: Integrate Telegram into Messages Tab

**Problem**: Messages tab shows zeros but Telegram bot is running

**API Update** for `/api/messages/counts`:
```python
@app.route("/api/messages/counts")
def api_messages_counts():
    """Get message counts per channel"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check for Telegram messages in database (if logged)
        telegram_count = 0
        try:
            cur.execute("SELECT count(*) FROM telegram_messages WHERE created_at > NOW() - INTERVAL '24 hours'")
            result = cur.fetchone()
            telegram_count = result[0] if result else 0
        except:
            pass  # Table may not exist

        cur.close()
        conn.close()

        return jsonify({
            "discord": 0,
            "facebook": 0,
            "instagram": 0,
            "slack": 0,
            "sms": 0,
            "telegram": telegram_count,
            "whatsapp": 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Create telegram_messages table** (on bluefin):
```sql
CREATE TABLE IF NOT EXISTS telegram_messages (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT,
    message_id INTEGER,
    from_user VARCHAR(255),
    text TEXT,
    direction VARCHAR(10),  -- 'incoming' or 'outgoing'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Update telegram_chief.py** to log messages to this table.

---

## TESTING CHECKLIST

After implementing fixes, verify:

- [ ] `curl http://192.168.132.223:4000/api/alerts` returns alerts
- [ ] `curl http://192.168.132.223:4000/api/federation/summary` shows 6 nodes
- [ ] `curl http://192.168.132.223:4000/api/kanban/tickets` shows jr_work_queue tasks
- [ ] `curl http://192.168.132.223:4000/api/calendar/events` returns events
- [ ] `curl http://192.168.132.223:4000/api/monitoring/overview` shows service health
- [ ] Restart SAG UI: `sudo systemctl restart sag-ui` or kill/restart process

---

## DEPLOYMENT

After making changes to app.py:

```bash
# On redfin
cd /ganuda/home/dereadi/sag_unified_interface

# Backup current version
cp app.py app.py.backup_$(date +%Y%m%d_%H%M%S)

# Apply changes
# ... make edits ...

# Restart the service
pkill -f "sag_unified_interface/app.py"
nohup /ganuda/home/dereadi/cherokee_venv/bin/python3 app.py > /dev/null 2>&1 &

# Verify
curl http://localhost:4000/health
```

---

*FOR SEVEN GENERATIONS*
