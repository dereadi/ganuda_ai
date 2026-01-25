# Jr Instructions: SAG UI Fixes - December 20, 2025

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED WITH CAUTION (84.3% confidence)
**Concerns**: Gecko (PERF), Raven (STRATEGY)

---

## OBJECTIVE

Fix critical data discrepancies in the SAG UI dashboard where API returns correct data but the UI displays incorrect or empty values.

**Source App**: `/ganuda/home/dereadi/sag_unified_interface/app.py` (2,116 lines)

---

## ASSESSMENT FINDINGS

### WORKING
- Events API (`/api/events/stats`) - 3,515 events tracked
- Council votes API (`/api/tribe/council-votes`) - 72 votes
- Thermal memory - 6,599 memories
- IoT device list API - Returns active devices
- Service health checks - 4/4 healthy
- Monitoring overview API - All services responding

### BROKEN/ISSUES
1. Federation nodes showing "unreachable" despite services running
2. CPU/RAM utilization shows "--%" (not reporting)
3. 3,496 unreviewed events (mostly RISK VIOLATION noise)
4. Triad status returning empty array
5. IoT shows "0 Online" in dashboard but API returns active devices
6. Monitoring iframe pointing to port 5555 (may not be running)

---

### Task 1: Fix Federation Node Status

**Problem**: `/api/federation/nodes` returns `"reachable": false` for redfin and greenfin despite services being healthy.

**Location**: `app.py` lines 865-905

**Root Cause Analysis**:
The node health check is likely using wrong ports or IP addresses.

**Fix Approach**:
```python
# In get_federation_nodes() around line 866
# Check if nodes are using correct health endpoints

FEDERATION_NODES = {
    'redfin': {
        'hostname': '192.168.132.223',
        'health_port': 8080,  # Gateway, not SSH
        'health_path': '/health'
    },
    'bluefin': {
        'hostname': '192.168.132.222',
        'health_port': 3000,  # Grafana
        'health_path': '/api/health'
    },
    'greenfin': {
        'hostname': '192.168.132.224',
        'health_port': 9090,  # Prometheus or monitoring
        'health_path': '/health'
    }
}

# Use requests with timeout
def check_node_health(node_id, config):
    try:
        url = f"http://{config['hostname']}:{config['health_port']}{config['health_path']}"
        resp = requests.get(url, timeout=5)
        return resp.status_code == 200
    except:
        return False
```

---

### Task 2: Fix IoT Device Count Display

**Problem**: Dashboard shows "0 Online" but `/api/iot/devices` returns active devices.

**Location**:
- `templates/index.html` line ~100 (`<span id="iot-online">0</span>`)
- JavaScript that populates this value

**Fix Approach**:
```javascript
// In static/js/unified.js or inline script
// Find the function that loads IoT stats

async function loadIoTStats() {
    const resp = await fetch('/api/iot/devices');
    const devices = await resp.json();

    const online = devices.filter(d => d.online_status === true).length;
    const total = devices.length;

    document.getElementById('iot-online').textContent = online;
    document.getElementById('iot-total').textContent = total;
}

// Call on page load and refresh
loadIoTStats();
```

---

### Task 3: Fix CPU/RAM Utilization Display

**Problem**: Shows "--%" instead of actual values.

**Location**:
- `templates/index.html` lines ~95-96
- Need to fetch from system metrics

**Fix Approach**:
Add new API endpoint and frontend call:

```python
# Add to app.py
@app.route('/api/system/metrics')
def get_system_metrics():
    import psutil
    return jsonify({
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat()
    })
```

```javascript
// Add to frontend
async function loadSystemMetrics() {
    const resp = await fetch('/api/system/metrics');
    const data = await resp.json();
    document.getElementById('cpu-util').textContent = Math.round(data.cpu_percent);
    document.getElementById('ram-util').textContent = Math.round(data.memory_percent);
}
```

---

### Task 4: Filter RISK VIOLATION Event Noise

**Problem**: 3,496 unreviewed events, mostly "RISK VIOLATION: POSITION_SIZE" noise.

**Fix Approach**:
Add auto-dismiss or bulk dismiss for specific event patterns:

```python
# Add to app.py
@app.route('/api/events/bulk-dismiss', methods=['POST'])
def bulk_dismiss_events():
    data = request.json
    pattern = data.get('pattern', '')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events
        SET dismissed = true, dismissed_at = NOW()
        WHERE message ILIKE %s AND dismissed = false
        RETURNING id
    """, (f'%{pattern}%',))
    count = cur.rowcount
    conn.commit()

    return jsonify({'dismissed': count, 'pattern': pattern})
```

---

### Task 5: Fix Triad Status Endpoint

**Problem**: `/api/sidebar/triad-status` returns empty array.

**Location**: `app.py` lines 712-771

**Fix Approach**:
Check if jr_status table is being queried correctly:

```python
@app.route('/api/sidebar/triad-status')
def get_sidebar_triad_status():
    conn = get_db()
    cur = conn.cursor()

    # Check actual table structure
    cur.execute("""
        SELECT jr_name, is_online, last_seen, jr_mountain
        FROM jr_status
        ORDER BY jr_name
    """)

    triads = []
    for row in cur.fetchall():
        triads.append({
            'name': row[0],
            'online': row[1],
            'last_seen': row[2].isoformat() if row[2] else None,
            'mountain': row[3]
        })

    return jsonify({'triads': triads})
```

---

### Task 6: Fix Monitoring IFrame

**Problem**: Points to port 5555 which may not be running.

**Location**: `templates/index.html` line ~127

**Fix Approach**:
Either:
1. Start the monitoring service on port 5555, OR
2. Update iframe to point to Grafana:

```html
<!-- Option 1: Point to Grafana -->
<iframe id="monitoring-frame"
        src="http://192.168.132.222:3000/d/federation-overview"
        style="width: 100%; height: calc(100vh - 150px); border: none;">
</iframe>

<!-- Option 2: Embed service health -->
<div id="monitoring-content">
    <!-- Dynamically loaded from /api/monitoring/overview -->
</div>
```

---

## SUCCESS CRITERIA

1. Federation nodes show correct reachability status
2. IoT device count matches API response
3. CPU/RAM shows actual percentages
4. Bulk dismiss available for event noise
5. Triad status populates from jr_status table
6. Monitoring view shows useful data

---

## TESTING

After each fix, verify:
```bash
# Test federation nodes
curl http://192.168.132.223:4000/api/federation/nodes | jq '.nodes[].reachable'

# Test IoT count
curl http://192.168.132.223:4000/api/iot/devices | jq 'length'

# Test system metrics (after adding endpoint)
curl http://192.168.132.223:4000/api/system/metrics

# Test triad status
curl http://192.168.132.223:4000/api/sidebar/triad-status | jq '.triads | length'
```

---

*For Seven Generations - Cherokee AI Federation*
