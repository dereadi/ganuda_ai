# Jr Instructions: Home Hub UI for SAG Interface - December 20, 2025

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Integration**: Add to SAG UI at http://192.168.132.223:4000/

---

## OBJECTIVE

Create a "Home Hub" section in the SAG UI that provides:
1. IoT device dashboard with status overview
2. Firmware/patch management interface
3. Device control actions (where supported)
4. Security status indicators

**Base App**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

---

## ARCHITECTURE

```
SAG UI (port 4000)
└── /home-hub (new route)
    ├── Device Overview
    │   ├── By Zone (office, living room, etc.)
    │   ├── By Type (sonos, esp32, hvac, router)
    │   └── Online/Offline status
    ├── Firmware Manager
    │   ├── Available updates from software_repo
    │   ├── Cached packages list
    │   └── Apply update buttons
    ├── Device Control
    │   ├── Sonos: Play/Pause/Volume
    │   ├── Daikin: Temp/Mode
    │   └── ESP32: Toggle outputs
    └── Security Dashboard
        ├── Credential status
        ├── Firmware age warnings
        └── CVE alerts for devices
```

---

### Task 1: Add Home Hub Route to Flask App

Add to `app.py`:

```python
@app.route('/home-hub')
def home_hub():
    """Home Hub - IoT device management interface."""
    return render_template('home_hub.html')


@app.route('/api/home-hub/devices')
def api_home_hub_devices():
    """Get all IoT devices grouped by zone and type."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            d.device_name,
            d.device_type,
            d.vendor,
            d.ip_address,
            d.mac_address,
            d.online_status,
            d.last_seen,
            COALESCE(sz.zone_name, 'unassigned') as zone
        FROM iot_devices d
        LEFT JOIN spatial_zones sz ON d.zone_id = sz.zone_id
        ORDER BY sz.zone_name, d.device_type, d.device_name
    """)

    devices = []
    for row in cur.fetchall():
        devices.append({
            'name': row[0],
            'type': row[1],
            'vendor': row[2],
            'ip': row[3],
            'mac': row[4],
            'online': row[5],
            'last_seen': row[6].isoformat() if row[6] else None,
            'zone': row[7]
        })

    cur.close()
    return jsonify({'devices': devices, 'count': len(devices)})


@app.route('/api/home-hub/firmware')
def api_home_hub_firmware():
    """Get cached firmware and available updates."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            package_name,
            package_type,
            current_version,
            local_path,
            last_sync,
            is_cached,
            notes
        FROM software_repository
        WHERE package_type IN ('firmware', 'firmware-tool', 'library', 'integration')
        ORDER BY package_type, package_name
    """)

    firmware = []
    for row in cur.fetchall():
        firmware.append({
            'name': row[0],
            'type': row[1],
            'version': row[2],
            'path': row[3],
            'last_sync': row[4].isoformat() if row[4] else None,
            'cached': row[5],
            'notes': row[6]
        })

    cur.close()
    return jsonify({'firmware': firmware})


@app.route('/api/home-hub/security-status')
def api_home_hub_security():
    """Get security status for IoT devices."""
    conn = get_db()
    cur = conn.cursor()

    # Check for high-risk devices (Cisco/Linksys with potential default creds)
    cur.execute("""
        SELECT device_name, ip_address, vendor, last_seen
        FROM iot_devices
        WHERE vendor ILIKE '%cisco%' OR vendor ILIKE '%linksys%'
    """)

    high_risk = []
    for row in cur.fetchall():
        high_risk.append({
            'device': row[0],
            'ip': row[1],
            'vendor': row[2],
            'warning': 'FBI May 2025: EOL models actively exploited. Verify credentials changed.',
            'severity': 'critical'
        })

    # Check for devices not seen in 7+ days
    cur.execute("""
        SELECT device_name, ip_address, last_seen
        FROM iot_devices
        WHERE last_seen < NOW() - INTERVAL '7 days'
    """)

    stale = []
    for row in cur.fetchall():
        stale.append({
            'device': row[0],
            'ip': row[1],
            'last_seen': row[2].isoformat() if row[2] else None,
            'warning': 'Device not seen in 7+ days',
            'severity': 'medium'
        })

    cur.close()
    return jsonify({
        'high_risk': high_risk,
        'stale_devices': stale,
        'alerts_count': len(high_risk) + len(stale)
    })
```

---

### Task 2: Create Home Hub Template

Create `/ganuda/home/dereadi/sag_unified_interface/templates/home_hub.html`:

```html
{% extends "base.html" %}
{% block title %}Home Hub - Cherokee AI{% endblock %}

{% block content %}
<div class="container-fluid">
    <h1 class="mb-4">🏠 Home Hub</h1>

    <!-- Security Alerts Banner -->
    <div id="security-banner" class="alert alert-danger d-none mb-4">
        <strong>⚠️ Security Alerts:</strong> <span id="alert-count">0</span> issues require attention
    </div>

    <div class="row">
        <!-- Device Overview -->
        <div class="col-md-8">
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between">
                    <span>📡 IoT Devices</span>
                    <span class="badge bg-primary" id="device-count">0</span>
                </div>
                <div class="card-body">
                    <div id="devices-by-zone"></div>
                </div>
            </div>

            <!-- Firmware Manager -->
            <div class="card mb-4">
                <div class="card-header">📦 Firmware Repository</div>
                <div class="card-body">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Package</th>
                                <th>Type</th>
                                <th>Version</th>
                                <th>Cached</th>
                                <th>Last Sync</th>
                            </tr>
                        </thead>
                        <tbody id="firmware-table"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="col-md-4">
            <!-- Quick Stats -->
            <div class="card mb-4">
                <div class="card-header">📊 Quick Stats</div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Online Devices</span>
                        <span class="badge bg-success" id="online-count">0</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Offline Devices</span>
                        <span class="badge bg-secondary" id="offline-count">0</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Cached Firmware</span>
                        <span class="badge bg-info" id="firmware-count">0</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Security Alerts</span>
                        <span class="badge bg-danger" id="security-count">0</span>
                    </div>
                </div>
            </div>

            <!-- Security Issues -->
            <div class="card mb-4">
                <div class="card-header">🔒 Security Status</div>
                <div class="card-body" id="security-issues">
                    <p class="text-muted">Loading...</p>
                </div>
            </div>

            <!-- Device Types -->
            <div class="card">
                <div class="card-header">🏷️ By Type</div>
                <div class="card-body" id="devices-by-type"></div>
            </div>
        </div>
    </div>
</div>

<script>
async function loadHomeHub() {
    // Load devices
    const devResp = await fetch('/api/home-hub/devices');
    const devData = await devResp.json();

    document.getElementById('device-count').textContent = devData.count;

    // Group by zone
    const byZone = {};
    const byType = {};
    let online = 0, offline = 0;

    devData.devices.forEach(d => {
        // By zone
        if (!byZone[d.zone]) byZone[d.zone] = [];
        byZone[d.zone].push(d);

        // By type
        if (!byType[d.type]) byType[d.type] = 0;
        byType[d.type]++;

        // Online/offline
        if (d.online) online++; else offline++;
    });

    document.getElementById('online-count').textContent = online;
    document.getElementById('offline-count').textContent = offline;

    // Render by zone
    let zoneHtml = '';
    for (const [zone, devices] of Object.entries(byZone)) {
        zoneHtml += `<h6>${zone} (${devices.length})</h6><ul class="list-unstyled ms-3">`;
        devices.forEach(d => {
            const status = d.online ? '🟢' : '🔴';
            zoneHtml += `<li>${status} ${d.name} <small class="text-muted">(${d.vendor})</small></li>`;
        });
        zoneHtml += '</ul>';
    }
    document.getElementById('devices-by-zone').innerHTML = zoneHtml;

    // Render by type
    let typeHtml = '';
    for (const [type, count] of Object.entries(byType)) {
        typeHtml += `<div class="d-flex justify-content-between"><span>${type}</span><span class="badge bg-secondary">${count}</span></div>`;
    }
    document.getElementById('devices-by-type').innerHTML = typeHtml;

    // Load firmware
    const fwResp = await fetch('/api/home-hub/firmware');
    const fwData = await fwResp.json();

    document.getElementById('firmware-count').textContent = fwData.firmware.length;

    let fwHtml = '';
    fwData.firmware.forEach(f => {
        const cached = f.cached ? '✅' : '❌';
        const sync = f.last_sync ? new Date(f.last_sync).toLocaleDateString() : 'Never';
        fwHtml += `<tr>
            <td>${f.name}</td>
            <td><span class="badge bg-secondary">${f.type}</span></td>
            <td>${f.version || 'latest'}</td>
            <td>${cached}</td>
            <td>${sync}</td>
        </tr>`;
    });
    document.getElementById('firmware-table').innerHTML = fwHtml || '<tr><td colspan="5">No firmware cached yet</td></tr>';

    // Load security
    const secResp = await fetch('/api/home-hub/security-status');
    const secData = await secResp.json();

    document.getElementById('security-count').textContent = secData.alerts_count;

    if (secData.alerts_count > 0) {
        document.getElementById('security-banner').classList.remove('d-none');
        document.getElementById('alert-count').textContent = secData.alerts_count;
    }

    let secHtml = '';
    secData.high_risk.forEach(r => {
        secHtml += `<div class="alert alert-danger py-1 px-2 mb-2">
            <strong>${r.device}</strong><br>
            <small>${r.warning}</small>
        </div>`;
    });
    secData.stale_devices.forEach(s => {
        secHtml += `<div class="alert alert-warning py-1 px-2 mb-2">
            <strong>${s.device}</strong><br>
            <small>${s.warning}</small>
        </div>`;
    });
    document.getElementById('security-issues').innerHTML = secHtml || '<p class="text-success">No security issues</p>';
}

document.addEventListener('DOMContentLoaded', loadHomeHub);
setInterval(loadHomeHub, 60000);  // Refresh every minute
</script>
{% endblock %}
```

---

### Task 3: Add Navigation Link

In `templates/base.html`, add to the navbar:

```html
<li class="nav-item">
    <a class="nav-link" href="/home-hub">🏠 Home Hub</a>
</li>
```

---

### Task 4: Add Device Control API (Future)

Placeholder for device control - implement based on device type:

```python
@app.route('/api/home-hub/control/<device_type>/<action>', methods=['POST'])
def api_device_control(device_type, action):
    """Control IoT devices (future implementation)."""
    data = request.json
    device_ip = data.get('ip')

    if device_type == 'sonos':
        # Use SoCo library
        # from soco import SoCo
        # speaker = SoCo(device_ip)
        # if action == 'play': speaker.play()
        pass
    elif device_type == 'daikin':
        # Use pydaikin library
        pass

    return jsonify({'status': 'not_implemented', 'device_type': device_type, 'action': action})
```

---

## SUCCESS CRITERIA

1. `/home-hub` route accessible at http://192.168.132.223:4000/home-hub
2. Device overview shows all IoT devices grouped by zone
3. Firmware table shows cached packages from software_repository
4. Security alerts display for Cisco/Linksys and stale devices
5. Navigation link added to SAG UI navbar

---

## TESTING

```bash
# Test new endpoints
curl http://192.168.132.223:4000/api/home-hub/devices | jq '.count'
curl http://192.168.132.223:4000/api/home-hub/firmware | jq '.firmware | length'
curl http://192.168.132.223:4000/api/home-hub/security-status | jq '.alerts_count'

# Verify page loads
curl -s http://192.168.132.223:4000/home-hub | grep -o "Home Hub"
```

---

*For Seven Generations - Cherokee AI Federation*
