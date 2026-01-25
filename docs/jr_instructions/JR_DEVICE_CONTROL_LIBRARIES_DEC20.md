# Jr Instructions: Device Control Libraries - December 20, 2025

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Council Context**: Home Hub UI deployed, need device control capabilities

---

## OBJECTIVE

Add direct device control to Home Hub using lightweight Python libraries instead of full Home Assistant installation. This gives us control capabilities while keeping the Federation architecture clean.

---

## LIBRARIES TO INSTALL

### Task 1: Install Device Control Libraries on Redfin

```bash
ssh redfin

# Create virtual environment for device control
cd /ganuda/services
python3 -m venv device_control_venv
source device_control_venv/bin/activate

# Sonos control
pip install soco

# Daikin HVAC
pip install pydaikin

# TP-Link/Kasa smart plugs and lights
pip install python-kasa

# ESP32/ESP8266 via MQTT
pip install paho-mqtt

# Philips Hue (if present)
pip install phue

# Save requirements
pip freeze > /ganuda/services/device_control_requirements.txt
```

---

### Task 2: Create Device Control Service

Create `/ganuda/services/device_control/controller.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Device Control Service
Direct control of IoT devices without Home Assistant dependency.
"""

import json
from typing import Dict, Any, Optional, List

# Sonos
try:
    import soco
    SONOS_AVAILABLE = True
except ImportError:
    SONOS_AVAILABLE = False

# Daikin
try:
    from pydaikin.daikin_brp069 import DaikinBRP069
    DAIKIN_AVAILABLE = True
except ImportError:
    DAIKIN_AVAILABLE = False

# Kasa
try:
    from kasa import SmartPlug, SmartBulb, Discover
    KASA_AVAILABLE = True
except ImportError:
    KASA_AVAILABLE = False


class DeviceController:
    """Unified device control interface."""

    def __init__(self):
        self.discovered_devices = {}

    # ==================== SONOS ====================

    def sonos_discover(self) -> List[Dict]:
        """Discover all Sonos speakers on network."""
        if not SONOS_AVAILABLE:
            return []

        speakers = []
        for speaker in soco.discover():
            speakers.append({
                'name': speaker.player_name,
                'ip': speaker.ip_address,
                'model': speaker.speaker_info.get('model_name', 'Unknown'),
                'volume': speaker.volume,
                'is_playing': speaker.get_current_transport_info()['current_transport_state'] == 'PLAYING'
            })
        return speakers

    def sonos_play(self, ip: str) -> Dict:
        """Play on Sonos speaker."""
        if not SONOS_AVAILABLE:
            return {'error': 'SoCo not installed'}
        speaker = soco.SoCo(ip)
        speaker.play()
        return {'status': 'playing', 'ip': ip}

    def sonos_pause(self, ip: str) -> Dict:
        """Pause Sonos speaker."""
        if not SONOS_AVAILABLE:
            return {'error': 'SoCo not installed'}
        speaker = soco.SoCo(ip)
        speaker.pause()
        return {'status': 'paused', 'ip': ip}

    def sonos_volume(self, ip: str, level: int) -> Dict:
        """Set Sonos volume (0-100)."""
        if not SONOS_AVAILABLE:
            return {'error': 'SoCo not installed'}
        speaker = soco.SoCo(ip)
        speaker.volume = max(0, min(100, level))
        return {'status': 'volume_set', 'ip': ip, 'level': speaker.volume}

    # ==================== DAIKIN ====================

    async def daikin_status(self, ip: str) -> Dict:
        """Get Daikin AC status."""
        if not DAIKIN_AVAILABLE:
            return {'error': 'pydaikin not installed'}

        device = DaikinBRP069(ip)
        await device.init()

        return {
            'ip': ip,
            'power': device.power,
            'mode': device.mode,
            'target_temp': device.target_temperature,
            'current_temp': device.current_temperature,
            'fan_mode': device.fan_mode
        }

    async def daikin_set_temp(self, ip: str, temp: float) -> Dict:
        """Set Daikin target temperature."""
        if not DAIKIN_AVAILABLE:
            return {'error': 'pydaikin not installed'}

        device = DaikinBRP069(ip)
        await device.init()
        await device.set({'target_temperature': temp})

        return {'status': 'temp_set', 'ip': ip, 'target': temp}

    async def daikin_power(self, ip: str, on: bool) -> Dict:
        """Turn Daikin on/off."""
        if not DAIKIN_AVAILABLE:
            return {'error': 'pydaikin not installed'}

        device = DaikinBRP069(ip)
        await device.init()
        await device.set({'power': on})

        return {'status': 'power_set', 'ip': ip, 'power': on}

    # ==================== KASA ====================

    async def kasa_discover(self) -> List[Dict]:
        """Discover Kasa devices on network."""
        if not KASA_AVAILABLE:
            return []

        devices = await Discover.discover()
        result = []
        for ip, device in devices.items():
            await device.update()
            result.append({
                'ip': ip,
                'alias': device.alias,
                'model': device.model,
                'is_on': device.is_on,
                'type': 'plug' if hasattr(device, 'led') else 'bulb'
            })
        return result

    async def kasa_toggle(self, ip: str, on: bool) -> Dict:
        """Turn Kasa device on/off."""
        if not KASA_AVAILABLE:
            return {'error': 'python-kasa not installed'}

        plug = SmartPlug(ip)
        await plug.update()

        if on:
            await plug.turn_on()
        else:
            await plug.turn_off()

        return {'status': 'toggled', 'ip': ip, 'is_on': on}

    # ==================== STATUS ====================

    def get_library_status(self) -> Dict:
        """Check which control libraries are available."""
        return {
            'sonos': SONOS_AVAILABLE,
            'daikin': DAIKIN_AVAILABLE,
            'kasa': KASA_AVAILABLE
        }


# CLI testing
if __name__ == '__main__':
    import sys
    controller = DeviceController()

    print("Library Status:")
    print(json.dumps(controller.get_library_status(), indent=2))

    if SONOS_AVAILABLE:
        print("\nSonos Speakers:")
        speakers = controller.sonos_discover()
        for s in speakers:
            print(f"  - {s['name']} ({s['ip']}) vol:{s['volume']}")
```

---

### Task 3: Add Control Endpoints to SAG UI

Add to `/ganuda/home/dereadi/sag_unified_interface/app.py`:

```python
@app.route('/api/home-hub/control/sonos/<action>', methods=['POST'])
def api_sonos_control(action):
    """Control Sonos speakers."""
    import sys
    sys.path.insert(0, '/ganuda/services/device_control')
    from controller import DeviceController

    data = request.json or {}
    ip = data.get('ip')

    if not ip:
        return jsonify({'error': 'IP address required'}), 400

    controller = DeviceController()

    if action == 'play':
        result = controller.sonos_play(ip)
    elif action == 'pause':
        result = controller.sonos_pause(ip)
    elif action == 'volume':
        level = data.get('level', 50)
        result = controller.sonos_volume(ip, level)
    else:
        return jsonify({'error': f'Unknown action: {action}'}), 400

    return jsonify(result)


@app.route('/api/home-hub/control/discover/<device_type>')
def api_discover_devices(device_type):
    """Discover devices by type."""
    import sys
    sys.path.insert(0, '/ganuda/services/device_control')
    from controller import DeviceController

    controller = DeviceController()

    if device_type == 'sonos':
        devices = controller.sonos_discover()
    else:
        return jsonify({'error': f'Discovery not implemented for: {device_type}'}), 400

    return jsonify({'devices': devices, 'count': len(devices)})


@app.route('/api/home-hub/control/status')
def api_control_status():
    """Check which control libraries are available."""
    import sys
    sys.path.insert(0, '/ganuda/services/device_control')
    from controller import DeviceController

    controller = DeviceController()
    return jsonify(controller.get_library_status())
```

---

### Task 4: Add Control Buttons to Home Hub JavaScript

Update the loadHomeHubView() function to add control buttons for Sonos devices:

```javascript
// Add after rendering devices by zone
// For Sonos devices, add control buttons
if (d.type === 'sonos' || d.vendor.toLowerCase().includes('sonos')) {
    zoneHtml += ` <button class="btn btn-xs btn-outline" onclick="sonosControl('${d.ip}', 'play')">Play</button>`;
    zoneHtml += ` <button class="btn btn-xs btn-outline" onclick="sonosControl('${d.ip}', 'pause')">Pause</button>`;
}

// Add Sonos control function
function sonosControl(ip, action) {
    fetch('/api/home-hub/control/sonos/' + action, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip})
    })
    .then(r => r.json())
    .then(data => {
        console.log('Sonos control:', data);
        if (data.error) {
            alert('Error: ' + data.error);
        }
    });
}
```

---

## SUCCESS CRITERIA

1. Device control libraries installed in venv on redfin
2. DeviceController class created with Sonos, Daikin, Kasa methods
3. Control endpoints added to SAG UI
4. Sonos play/pause/volume works from Home Hub
5. Device discovery returns real devices

---

## TESTING

```bash
# Test library installation
source /ganuda/services/device_control_venv/bin/activate
python3 -c "import soco; print('Sonos:', soco.discover())"

# Test controller
cd /ganuda/services/device_control
python3 controller.py

# Test API endpoints
curl http://192.168.132.223:4000/api/home-hub/control/status
curl http://192.168.132.223:4000/api/home-hub/control/discover/sonos
```

---

*For Seven Generations - Cherokee AI Federation*
