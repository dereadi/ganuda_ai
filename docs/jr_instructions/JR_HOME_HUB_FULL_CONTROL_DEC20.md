# Jr Instructions: Home Hub Full Control - December 20, 2025

**Priority**: 1
**Assigned Jr**: it_triad_jr
**User Request**: "I would like to view my cameras, set my temp in the house and turn on and off things"

---

## OBJECTIVE

Build a complete home control dashboard with:
1. **Camera Feeds** - View live/snapshot from cameras
2. **Thermostat Control** - Set temperature, mode (heat/cool/auto)
3. **Switch Control** - Turn devices on/off (plugs, lights, switches)

---

## CURRENT DEVICE INVENTORY

| Category | Devices | Notes |
|----------|---------|-------|
| Cameras | 2 cameras + Ring doorbell | Need IPs/registration |
| Thermostats | 1 Nest + 2 Daikin HVAC | Nest needs Google auth |
| Switches | TP-Link, Meross | 10.0.0.3, 10.0.0.74 |
| Sonos | 8 speakers | Various |

**USER-SPECIFIED DEVICES:**
- Nest Thermostat (requires Google Device Access API)
- 2 Cameras (need make/model/IPs)
- Ring Doorbell (requires Ring API or local RTSP)

---

## PART 1: CAMERA INTEGRATION

### Task 1.1: Camera Discovery Script

Create `/ganuda/services/device_control/camera_discovery.py`:

```python
#!/usr/bin/env python3
"""
Discover cameras on network via common methods:
1. ONVIF discovery (professional cameras)
2. RTSP port scan (port 554)
3. Known vendor APIs (Ring, Nest, Wyze, Arlo)
"""

import socket
import subprocess
from typing import List, Dict

def scan_rtsp_ports(subnet: str = "192.168.132") -> List[Dict]:
    """Scan for devices with RTSP port 554 open."""
    cameras = []

    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, 554))
        if result == 0:
            cameras.append({
                'ip': ip,
                'port': 554,
                'protocol': 'rtsp',
                'url': f'rtsp://{ip}:554/stream1'
            })
        sock.close()

    return cameras

def scan_onvif(subnet: str = "192.168.132") -> List[Dict]:
    """Scan for ONVIF cameras on port 80/8080."""
    # ONVIF uses WS-Discovery multicast
    # For now, scan common ports
    cameras = []

    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        for port in [80, 8080, 8000]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, port))
            if result == 0:
                # Try to detect if it's a camera by checking for ONVIF path
                cameras.append({
                    'ip': ip,
                    'port': port,
                    'protocol': 'onvif',
                    'url': f'http://{ip}:{port}/onvif/device_service'
                })
            sock.close()

    return cameras

if __name__ == '__main__':
    print("Scanning for RTSP cameras...")
    rtsp = scan_rtsp_ports()
    print(f"Found {len(rtsp)} RTSP endpoints")
    for cam in rtsp:
        print(f"  {cam['ip']}:{cam['port']}")
```

### Task 1.2: Camera View API Endpoint

Add to `/ganuda/home/dereadi/sag_unified_interface/app.py`:

```python
@app.route('/api/home-hub/cameras')
def api_cameras():
    """Get registered cameras."""
    import psycopg2
    DB_CONFIG = {
        "host": "192.168.132.222",
        "database": "zammad_production",
        "user": "claude",
        "password": "jawaseatlasers2"
    }
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT device_name, ip_address, vendor,
               COALESCE(metadata->>'rtsp_url', 'rtsp://' || ip_address || ':554/stream1') as rtsp_url,
               COALESCE(metadata->>'snapshot_url', 'http://' || ip_address || '/snapshot.jpg') as snapshot_url
        FROM iot_devices
        WHERE device_type ILIKE '%camera%'
           OR device_name ILIKE '%cam%'
    """)

    cameras = []
    for row in cur.fetchall():
        cameras.append({
            'name': row[0],
            'ip': row[1],
            'vendor': row[2],
            'rtsp_url': row[3],
            'snapshot_url': row[4]
        })

    cur.close()
    conn.close()
    return jsonify({'cameras': cameras})


@app.route('/api/home-hub/camera/snapshot/<ip>')
def api_camera_snapshot(ip):
    """Proxy camera snapshot to avoid CORS issues."""
    import requests

    # Common snapshot URLs to try
    urls = [
        f'http://{ip}/snapshot.jpg',
        f'http://{ip}/cgi-bin/snapshot.cgi',
        f'http://{ip}/image.jpg',
        f'http://{ip}:80/snapshot.jpg'
    ]

    for url in urls:
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
                return resp.content, 200, {'Content-Type': resp.headers['content-type']}
        except:
            continue

    return jsonify({'error': 'Could not fetch snapshot'}), 404
```

### Task 1.3: Camera Grid HTML Component

Add to `loadHomeHubView()` in control-room.js:

```javascript
// === CAMERA SECTION ===
function renderCameraSection(cameras) {
    if (!cameras || cameras.length === 0) {
        return '<div class="hub-section"><div class="hub-section-header">Cameras</div><p class="text-muted">No cameras registered. Run discovery to find cameras.</p></div>';
    }

    var html = '<div class="hub-section">';
    html += '<div class="hub-section-header">Cameras (' + cameras.length + ')</div>';
    html += '<div class="camera-grid">';

    cameras.forEach(function(cam) {
        html += '<div class="camera-card">';
        html += '<img src="/api/home-hub/camera/snapshot/' + cam.ip + '" alt="' + cam.name + '" onerror="this.src=\'/static/img/no-camera.png\'">';
        html += '<div class="camera-name">' + cam.name + '</div>';
        html += '<div class="camera-controls">';
        html += '<button onclick="openCameraStream(\'' + cam.rtsp_url + '\')">Live</button>';
        html += '<button onclick="refreshSnapshot(\'' + cam.ip + '\')">Refresh</button>';
        html += '</div>';
        html += '</div>';
    });

    html += '</div></div>';
    return html;
}
```

---

## PART 2: THERMOSTAT CONTROL

### Task 2.1: Daikin Control Endpoints

Add to `/ganuda/home/dereadi/sag_unified_interface/app.py`:

```python
@app.route('/api/home-hub/thermostat/<ip>/status')
def api_thermostat_status(ip):
    """Get thermostat current status."""
    import asyncio
    try:
        from pydaikin.daikin_brp069 import DaikinBRP069
    except ImportError:
        return jsonify({'error': 'pydaikin not installed'}), 500

    async def get_status():
        device = DaikinBRP069(ip)
        await device.init()
        return {
            'ip': ip,
            'power': device.power,
            'mode': device.mode,
            'target_temp': device.target_temperature,
            'current_temp': device.current_temperature,
            'fan_mode': device.fan_mode,
            'humidity': getattr(device, 'humidity', None)
        }

    try:
        result = asyncio.run(get_status())
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/home-hub/thermostat/<ip>/set', methods=['POST'])
def api_thermostat_set(ip):
    """Set thermostat temperature and mode."""
    import asyncio
    try:
        from pydaikin.daikin_brp069 import DaikinBRP069
    except ImportError:
        return jsonify({'error': 'pydaikin not installed'}), 500

    data = request.json or {}

    async def set_values():
        device = DaikinBRP069(ip)
        await device.init()

        settings = {}
        if 'temp' in data:
            settings['target_temperature'] = float(data['temp'])
        if 'mode' in data:
            settings['mode'] = data['mode']  # cool, heat, auto, fan, dry
        if 'power' in data:
            settings['power'] = data['power']  # True/False
        if 'fan' in data:
            settings['fan_mode'] = data['fan']  # auto, low, mid, high

        if settings:
            await device.set(settings)

        return {
            'status': 'updated',
            'ip': ip,
            'settings': settings
        }

    try:
        result = asyncio.run(set_values())
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Task 2.2: Thermostat Card JavaScript

Add to control-room.js:

```javascript
function renderThermostatCard(device) {
    return `
        <div class="thermostat-card" data-ip="${device.ip}">
            <div class="thermo-header">
                <span class="thermo-icon">🌡️</span>
                <span class="thermo-name">${device.name}</span>
            </div>
            <div class="thermo-display">
                <span class="thermo-current">--°F</span>
                <span class="thermo-target">Target: --°F</span>
            </div>
            <div class="thermo-controls">
                <button class="thermo-btn" onclick="adjustTemp('${device.ip}', -1)">−</button>
                <input type="range" min="60" max="85" value="72" class="thermo-slider"
                       onchange="setTemp('${device.ip}', this.value)">
                <button class="thermo-btn" onclick="adjustTemp('${device.ip}', 1)">+</button>
            </div>
            <div class="thermo-modes">
                <button onclick="setMode('${device.ip}', 'cool')" class="mode-btn">❄️ Cool</button>
                <button onclick="setMode('${device.ip}', 'heat')" class="mode-btn">🔥 Heat</button>
                <button onclick="setMode('${device.ip}', 'auto')" class="mode-btn">🔄 Auto</button>
                <button onclick="setMode('${device.ip}', 'off')" class="mode-btn">⭕ Off</button>
            </div>
        </div>
    `;
}

function setTemp(ip, temp) {
    fetch('/api/home-hub/thermostat/' + ip + '/set', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({temp: temp})
    }).then(r => r.json()).then(data => {
        console.log('Thermostat set:', data);
        loadHomeHubView(); // Refresh
    });
}

function setMode(ip, mode) {
    fetch('/api/home-hub/thermostat/' + ip + '/set', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: mode, power: mode !== 'off'})
    }).then(r => r.json()).then(data => {
        console.log('Mode set:', data);
        loadHomeHubView();
    });
}

function adjustTemp(ip, delta) {
    // Get current value and adjust
    var slider = document.querySelector('.thermostat-card[data-ip="' + ip + '"] .thermo-slider');
    if (slider) {
        var newVal = parseInt(slider.value) + delta;
        slider.value = newVal;
        setTemp(ip, newVal);
    }
}
```

---

## PART 3: SWITCH/PLUG CONTROL

### Task 3.1: Switch Control Endpoints

Add to `/ganuda/home/dereadi/sag_unified_interface/app.py`:

```python
@app.route('/api/home-hub/switch/<ip>/status')
def api_switch_status(ip):
    """Get switch/plug status."""
    import asyncio
    try:
        from kasa import SmartPlug
    except ImportError:
        return jsonify({'error': 'python-kasa not installed'}), 500

    async def get_status():
        plug = SmartPlug(ip)
        await plug.update()
        return {
            'ip': ip,
            'alias': plug.alias,
            'is_on': plug.is_on,
            'model': plug.model,
            'rssi': getattr(plug, 'rssi', None)
        }

    try:
        result = asyncio.run(get_status())
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/home-hub/switch/<ip>/toggle', methods=['POST'])
def api_switch_toggle(ip):
    """Toggle switch on/off."""
    import asyncio
    try:
        from kasa import SmartPlug
    except ImportError:
        return jsonify({'error': 'python-kasa not installed'}), 500

    data = request.json or {}
    turn_on = data.get('on', None)  # None = toggle, True = on, False = off

    async def do_toggle():
        plug = SmartPlug(ip)
        await plug.update()

        if turn_on is None:
            # Toggle
            if plug.is_on:
                await plug.turn_off()
            else:
                await plug.turn_on()
        elif turn_on:
            await plug.turn_on()
        else:
            await plug.turn_off()

        await plug.update()
        return {
            'ip': ip,
            'is_on': plug.is_on,
            'action': 'toggled'
        }

    try:
        result = asyncio.run(do_toggle())
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Task 3.2: Switch Tile with Toggle

In the Lovelace tile rendering, add toggle functionality:

```javascript
// For switch/plug devices, make the tile toggleable
if (device.type === 'switch' || device.type === 'plug' || device.type === 'tp-link' || device.type === 'outlet') {
    tile.classList.add('toggleable');
    tile.onclick = function() {
        toggleSwitch(device.ip);
    };
}

function toggleSwitch(ip) {
    fetch('/api/home-hub/switch/' + ip + '/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    }).then(r => r.json()).then(data => {
        console.log('Switch toggled:', data);
        loadHomeHubView(); // Refresh to show new state
    }).catch(err => {
        alert('Error toggling switch: ' + err);
    });
}
```

---

## PART 4: UPDATED CSS FOR CONTROL COMPONENTS

Add to unified.css:

```css
/* Camera Grid */
.camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}

.camera-card {
    background: #2a2a2a;
    border-radius: 12px;
    overflow: hidden;
}

.camera-card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    background: #1a1a1a;
}

.camera-name {
    padding: 12px;
    font-size: 0.9rem;
}

.camera-controls {
    display: flex;
    gap: 8px;
    padding: 0 12px 12px;
}

.camera-controls button {
    flex: 1;
    padding: 8px;
    background: #333;
    border: none;
    border-radius: 6px;
    color: #fff;
    cursor: pointer;
}

.camera-controls button:hover {
    background: #444;
}

/* Thermostat Card */
.thermostat-card {
    background: #2a2a2a;
    border-radius: 12px;
    padding: 20px;
    min-width: 250px;
}

.thermo-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
}

.thermo-icon {
    font-size: 1.5rem;
}

.thermo-name {
    font-size: 1rem;
    color: #e1e1e1;
}

.thermo-display {
    text-align: center;
    margin-bottom: 16px;
}

.thermo-current {
    font-size: 3rem;
    font-weight: 300;
    color: #ffc107;
}

.thermo-target {
    display: block;
    font-size: 0.9rem;
    color: #888;
    margin-top: 4px;
}

.thermo-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.thermo-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #444;
    background: transparent;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
}

.thermo-btn:hover {
    background: #333;
    border-color: #ffc107;
}

.thermo-slider {
    flex: 1;
    -webkit-appearance: none;
    height: 8px;
    background: #333;
    border-radius: 4px;
}

.thermo-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 24px;
    height: 24px;
    background: #ffc107;
    border-radius: 50%;
    cursor: pointer;
}

.thermo-modes {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}

.mode-btn {
    padding: 10px 4px;
    background: #333;
    border: none;
    border-radius: 8px;
    color: #fff;
    font-size: 0.75rem;
    cursor: pointer;
}

.mode-btn:hover, .mode-btn.active {
    background: #ffc107;
    color: #000;
}

/* Toggleable Tiles */
.hub-tile.toggleable {
    cursor: pointer;
}

.hub-tile.toggleable:active {
    transform: scale(0.95);
}
```

---

---

## PART 5: NEST THERMOSTAT INTEGRATION

Nest requires Google Device Access API (cloud-based, not local control).

### Task 5.1: Install Google Nest Library

```bash
pip install google-nest-sdm
```

### Task 5.2: Google Device Access Setup

**One-time setup required by user:**
1. Go to https://console.nest.google.com/device-access
2. Create a project ($5 one-time fee)
3. Get: Project ID, OAuth Client ID, Client Secret
4. Store credentials in `/ganuda/secrets/nest_credentials.json`

### Task 5.3: Nest API Endpoints

Add to app.py:

```python
@app.route('/api/home-hub/nest/status')
def api_nest_status():
    """Get Nest thermostat status via Google API."""
    import json
    import os

    creds_file = '/ganuda/secrets/nest_credentials.json'
    if not os.path.exists(creds_file):
        return jsonify({
            'error': 'Nest not configured',
            'setup_url': 'https://console.nest.google.com/device-access',
            'instructions': 'Create project, save credentials to ' + creds_file
        }), 400

    # For now, return placeholder until OAuth flow is set up
    return jsonify({
        'status': 'pending_oauth',
        'message': 'Nest OAuth flow not yet implemented - see Jr task for full setup'
    })
```

---

## PART 6: RING DOORBELL INTEGRATION

Ring doorbells can be accessed via unofficial `ring_doorbell` Python library.

### Task 6.1: Install Ring Library

```bash
pip install ring_doorbell
```

### Task 6.2: Ring API Endpoints

Add to app.py:

```python
@app.route('/api/home-hub/ring/devices')
def api_ring_devices():
    """Get Ring doorbell devices."""
    try:
        from ring_doorbell import Ring, Auth
    except ImportError:
        return jsonify({'error': 'ring_doorbell not installed'}), 500

    import json
    import os

    token_file = '/ganuda/secrets/ring_token.json'

    if not os.path.exists(token_file):
        return jsonify({
            'error': 'Ring not configured',
            'instructions': 'Run ring_doorbell auth flow and save token'
        }), 400

    # Load cached token
    with open(token_file, 'r') as f:
        token = json.load(f)

    auth = Auth("CherokeeAI/1.0", token, lambda tok: save_ring_token(tok))
    ring = Ring(auth)
    ring.update_data()

    devices = []
    for doorbell in ring.devices()['doorbells']:
        devices.append({
            'name': doorbell.name,
            'id': doorbell.device_id,
            'battery': doorbell.battery_life,
            'last_event': str(doorbell.last_event)
        })

    return jsonify({'doorbells': devices})


@app.route('/api/home-hub/ring/snapshot/<device_id>')
def api_ring_snapshot(device_id):
    """Get Ring doorbell snapshot."""
    try:
        from ring_doorbell import Ring, Auth
    except ImportError:
        return jsonify({'error': 'ring_doorbell not installed'}), 500

    import json
    token_file = '/ganuda/secrets/ring_token.json'

    if not os.path.exists(token_file):
        return jsonify({'error': 'Ring not configured'}), 400

    with open(token_file, 'r') as f:
        token = json.load(f)

    auth = Auth("CherokeeAI/1.0", token, lambda tok: None)
    ring = Ring(auth)
    ring.update_data()

    for doorbell in ring.devices()['doorbells']:
        if str(doorbell.device_id) == device_id:
            # Get snapshot (may take a few seconds)
            doorbell.get_snapshot()
            # Return latest snapshot URL or cached image
            return jsonify({'snapshot_url': f'/api/home-hub/ring/image/{device_id}'})

    return jsonify({'error': 'Doorbell not found'}), 404


def save_ring_token(token):
    """Callback to save refreshed Ring token."""
    import json
    with open('/ganuda/secrets/ring_token.json', 'w') as f:
        json.dump(token, f)
```

### Task 6.3: Ring Authentication Setup Script

Create `/ganuda/scripts/ring_auth.py`:

```python
#!/usr/bin/env python3
"""One-time Ring authentication script."""

from ring_doorbell import Auth
import json

def main():
    username = input("Ring email: ")
    password = input("Ring password: ")

    auth = Auth("CherokeeAI/1.0", None, lambda t: None)

    try:
        auth.fetch_token(username, password)
    except Exception as e:
        if "2fa" in str(e).lower():
            code = input("Enter 2FA code: ")
            auth.fetch_token(username, password, code)

    # Save token
    with open('/ganuda/secrets/ring_token.json', 'w') as f:
        json.dump(auth.token, f)

    print("Token saved to /ganuda/secrets/ring_token.json")

if __name__ == '__main__':
    main()
```

---

## SUCCESS CRITERIA

1. **Cameras**:
   - Grid displays camera snapshots (if cameras exist)
   - Ring doorbell shows snapshot
   - Refresh button updates snapshot
   - "No cameras" message if none registered

2. **Thermostats**:
   - Daikin cards show current/target temp
   - Nest shows status (once configured)
   - Slider adjusts temperature
   - Mode buttons switch between cool/heat/auto/off

3. **Switches**:
   - Clicking tile toggles device on/off
   - Tile color reflects current state
   - Works with TP-Link/Kasa and Meross devices

4. **Ring Doorbell**:
   - Shows in camera grid
   - Battery level visible
   - Snapshot available (with delay)

---

## DEVICE REGISTRATION NEEDED

Before full functionality, register cameras in iot_devices:

```sql
-- Example: Add a Ring doorbell camera
INSERT INTO iot_devices (device_name, device_type, vendor, ip_address, online_status, metadata)
VALUES (
    'Front Door Camera',
    'camera',
    'Ring',
    '192.168.132.50',
    true,
    '{"rtsp_url": "rtsp://192.168.132.50:554/live", "snapshot_url": "http://192.168.132.50/snapshot.jpg"}'::jsonb
);
```

---

## TESTING

```bash
# Test thermostat endpoints
curl http://192.168.132.223:4000/api/home-hub/thermostat/10.0.0.27/status

# Test switch toggle
curl -X POST http://192.168.132.223:4000/api/home-hub/switch/10.0.0.3/toggle \
  -H "Content-Type: application/json" -d '{}'

# Test camera list
curl http://192.168.132.223:4000/api/home-hub/cameras
```

---

*For Seven Generations - Cherokee AI Federation*
