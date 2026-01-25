# Jr Instructions: Home Hub Lovelace-Style UI - December 20, 2025

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Reference**: Home Assistant Lovelace Dashboard Design

---

## OBJECTIVE

Restyle the Home Hub interface to match Home Assistant's Lovelace dashboard design:
- Card-based tile layout with rounded corners
- Device tiles with icon, name, and state
- Color-coded status (on=amber/yellow, off=gray)
- Grid layout that reflows on mobile
- Section headers with room/zone groupings
- Glance cards for quick status overview

---

## VISUAL REFERENCE

Home Assistant Lovelace uses:
```
┌─────────────────────────────────────────────────────┐
│  🏠 Home                                            │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  💡     │ │  🔊     │ │  🌡️     │ │  📺     │   │
│  │ Light   │ │ Sonos   │ │ Thermo  │ │ TV      │   │
│  │   ON    │ │ Playing │ │  72°F   │ │   OFF   │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                     │
│  Living Room ───────────────────────────────────   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │  💡     │ │  🔊     │ │  🌡️     │               │
│  │ Lamp    │ │ Speaker │ │ Sensor  │               │
│  │   OFF   │ │ Paused  │ │  68°F   │               │
│  └─────────┘ └─────────┘ └─────────┘               │
└─────────────────────────────────────────────────────┘
```

---

### Task 1: Update CSS for Lovelace-Style Cards

Add to `/ganuda/home/dereadi/sag_unified_interface/static/css/unified.css`:

```css
/* ==================== LOVELACE-STYLE HOME HUB ==================== */

.home-hub-container {
    padding: 16px;
    background: #1c1c1c;
    min-height: 100vh;
}

/* Section Headers (Room/Zone names) */
.hub-section {
    margin-bottom: 24px;
}

.hub-section-header {
    font-size: 1.25rem;
    font-weight: 500;
    color: #e1e1e1;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #333;
}

/* Card Grid - Responsive */
.hub-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
}

@media (min-width: 768px) {
    .hub-card-grid {
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    }
}

/* Device Tile Card */
.hub-tile {
    background: #2a2a2a;
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}

.hub-tile:hover {
    background: #333;
    border-color: #444;
}

.hub-tile.active {
    background: linear-gradient(135deg, #3d3d00 0%, #2a2a00 100%);
    border-color: #ffc107;
}

.hub-tile.offline {
    opacity: 0.5;
}

/* Tile Icon */
.hub-tile-icon {
    font-size: 2rem;
    margin-bottom: 8px;
}

.hub-tile.active .hub-tile-icon {
    color: #ffc107;
}

.hub-tile:not(.active) .hub-tile-icon {
    color: #888;
}

/* Tile Name */
.hub-tile-name {
    font-size: 0.85rem;
    color: #e1e1e1;
    text-align: center;
    margin-bottom: 4px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Tile State */
.hub-tile-state {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
}

.hub-tile.active .hub-tile-state {
    color: #ffc107;
}

/* Glance Card (compact row of badges) */
.hub-glance {
    background: #2a2a2a;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}

.hub-glance-title {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 12px;
}

.hub-glance-items {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
}

.hub-glance-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 60px;
}

.hub-glance-item-icon {
    font-size: 1.5rem;
    margin-bottom: 4px;
}

.hub-glance-item-value {
    font-size: 0.8rem;
    color: #e1e1e1;
}

.hub-glance-item-label {
    font-size: 0.65rem;
    color: #666;
}

/* Alert Card */
.hub-alert-card {
    background: #2a1a1a;
    border: 1px solid #5c2a2a;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}

.hub-alert-card.warning {
    background: #2a2a1a;
    border-color: #5c5c2a;
}

.hub-alert-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.hub-alert-icon {
    font-size: 1.25rem;
}

.hub-alert-title {
    font-size: 0.9rem;
    font-weight: 500;
    color: #ff6b6b;
}

.hub-alert-card.warning .hub-alert-title {
    color: #ffc107;
}

.hub-alert-body {
    font-size: 0.8rem;
    color: #aaa;
}

/* Stats Row */
.hub-stats-row {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.hub-stat-card {
    background: #2a2a2a;
    border-radius: 12px;
    padding: 16px 24px;
    flex: 1;
    min-width: 120px;
    text-align: center;
}

.hub-stat-value {
    font-size: 2rem;
    font-weight: 600;
    color: #e1e1e1;
}

.hub-stat-value.success { color: #4caf50; }
.hub-stat-value.warning { color: #ffc107; }
.hub-stat-value.danger { color: #ff6b6b; }

.hub-stat-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    margin-top: 4px;
}
```

---

### Task 2: Update JavaScript to Render Lovelace-Style Layout

Replace the `loadHomeHubView()` function in `/ganuda/home/dereadi/sag_unified_interface/static/js/control-room.js`:

```javascript
function loadHomeHubView() {
    var container = document.getElementById('homehub-content');
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading Home Hub...</div>';

    // Fetch all data in parallel
    Promise.all([
        fetch('/api/home-hub/devices').then(r => r.json()),
        fetch('/api/home-hub/security-status').then(r => r.json()),
        fetch('/api/home-hub/firmware').then(r => r.json())
    ]).then(function([devData, secData, fwData]) {
        var html = '<div class="home-hub-container">';

        // === STATS ROW ===
        var online = devData.devices.filter(d => d.online).length;
        var offline = devData.devices.length - online;
        var alerts = secData.alerts_count || 0;

        html += '<div class="hub-stats-row">';
        html += '<div class="hub-stat-card"><div class="hub-stat-value success">' + online + '</div><div class="hub-stat-label">Online</div></div>';
        html += '<div class="hub-stat-card"><div class="hub-stat-value">' + offline + '</div><div class="hub-stat-label">Offline</div></div>';
        html += '<div class="hub-stat-card"><div class="hub-stat-value ' + (alerts > 0 ? 'danger' : '') + '">' + alerts + '</div><div class="hub-stat-label">Alerts</div></div>';
        html += '<div class="hub-stat-card"><div class="hub-stat-value">' + (fwData.firmware ? fwData.firmware.length : 0) + '</div><div class="hub-stat-label">Firmware</div></div>';
        html += '</div>';

        // === SECURITY ALERTS ===
        if (secData.high_risk && secData.high_risk.length > 0) {
            secData.high_risk.forEach(function(alert) {
                html += '<div class="hub-alert-card">';
                html += '<div class="hub-alert-header"><span class="hub-alert-icon">🚨</span><span class="hub-alert-title">' + alert.device + '</span></div>';
                html += '<div class="hub-alert-body">' + alert.warning + '</div>';
                html += '</div>';
            });
        }

        if (secData.stale_devices && secData.stale_devices.length > 0) {
            html += '<div class="hub-alert-card warning">';
            html += '<div class="hub-alert-header"><span class="hub-alert-icon">⚠️</span><span class="hub-alert-title">' + secData.stale_devices.length + ' Stale Devices</span></div>';
            html += '<div class="hub-alert-body">Devices not seen in 7+ days: ' + secData.stale_devices.map(d => d.device).join(', ') + '</div>';
            html += '</div>';
        }

        // === DEVICES BY ZONE ===
        var byZone = {};
        devData.devices.forEach(function(d) {
            var zone = d.zone || 'Unassigned';
            if (!byZone[zone]) byZone[zone] = [];
            byZone[zone].push(d);
        });

        // Sort zones alphabetically, but put 'Unassigned' last
        var zoneNames = Object.keys(byZone).sort(function(a, b) {
            if (a === 'Unassigned' || a === 'unassigned') return 1;
            if (b === 'Unassigned' || b === 'unassigned') return -1;
            return a.localeCompare(b);
        });

        zoneNames.forEach(function(zone) {
            html += '<div class="hub-section">';
            html += '<div class="hub-section-header">' + zone + '</div>';
            html += '<div class="hub-card-grid">';

            byZone[zone].forEach(function(device) {
                var icon = getDeviceIcon(device.type, device.vendor);
                var isActive = device.online;
                var tileClass = 'hub-tile' + (isActive ? ' active' : '') + (!isActive ? ' offline' : '');
                var state = isActive ? 'Online' : 'Offline';

                // Special states based on device type
                if (device.type === 'sonos' || (device.vendor && device.vendor.toLowerCase().includes('sonos'))) {
                    state = isActive ? 'Ready' : 'Offline';
                }

                html += '<div class="' + tileClass + '" data-ip="' + (device.ip || '') + '" data-type="' + (device.type || '') + '">';
                html += '<div class="hub-tile-icon">' + icon + '</div>';
                html += '<div class="hub-tile-name">' + device.name + '</div>';
                html += '<div class="hub-tile-state">' + state + '</div>';
                html += '</div>';
            });

            html += '</div></div>';
        });

        html += '</div>';
        container.innerHTML = html;

        // Add click handlers for controllable devices
        container.querySelectorAll('.hub-tile').forEach(function(tile) {
            tile.addEventListener('click', function() {
                var ip = this.dataset.ip;
                var type = this.dataset.type;
                if (type === 'sonos') {
                    showSonosControl(ip);
                }
            });
        });

    }).catch(function(err) {
        container.innerHTML = '<div class="hub-alert-card"><div class="hub-alert-title">Error loading Home Hub</div><div class="hub-alert-body">' + err + '</div></div>';
    });
}

function getDeviceIcon(type, vendor) {
    type = (type || '').toLowerCase();
    vendor = (vendor || '').toLowerCase();

    // Vendor-specific
    if (vendor.includes('sonos')) return '🔊';
    if (vendor.includes('daikin')) return '❄️';
    if (vendor.includes('cisco') || vendor.includes('linksys')) return '📡';
    if (vendor.includes('amazon') || vendor.includes('echo')) return '🔵';
    if (vendor.includes('espressif') || vendor.includes('esp')) return '📟';
    if (vendor.includes('apple')) return '🍎';
    if (vendor.includes('samsung')) return '📺';
    if (vendor.includes('philips') || vendor.includes('hue')) return '💡';

    // Type-based
    if (type.includes('speaker') || type.includes('audio')) return '🔊';
    if (type.includes('light') || type.includes('bulb')) return '💡';
    if (type.includes('thermostat') || type.includes('hvac')) return '🌡️';
    if (type.includes('camera')) return '📷';
    if (type.includes('tv') || type.includes('display')) return '📺';
    if (type.includes('router') || type.includes('network')) return '📡';
    if (type.includes('sensor')) return '📊';
    if (type.includes('plug') || type.includes('switch')) return '🔌';
    if (type.includes('lock')) return '🔐';
    if (type.includes('motion')) return '🚶';

    return '📱'; // default
}

function showSonosControl(ip) {
    // Simple control popup (future: modal with volume slider)
    var action = confirm('Sonos at ' + ip + '\n\nClick OK to Play, Cancel to Pause');
    var endpoint = action ? 'play' : 'pause';

    fetch('/api/home-hub/control/sonos/' + endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip})
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            console.log('Sonos ' + endpoint + ':', data);
        }
    });
}
```

---

### Task 3: Update Home Hub HTML Container

In `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`, ensure the Home Hub view container is simple:

```html
<!-- Home Hub View -->
<div id="homehub-view" class="view-content">
    <div id="homehub-content">
        <div class="loading">Loading Home Hub...</div>
    </div>
</div>
```

(Remove any existing `<h2>Home Hub</h2>` header - the Lovelace style puts stats at top instead)

---

## SUCCESS CRITERIA

1. Home Hub displays with dark theme (#1c1c1c background)
2. Stats row shows Online/Offline/Alerts/Firmware counts
3. Security alerts appear as red/yellow cards at top
4. Devices grouped by zone with section headers
5. Each device is a rounded tile with icon, name, state
6. Active devices have amber glow, offline devices are dimmed
7. Grid reflows responsively on mobile
8. Clicking Sonos tiles triggers play/pause prompt

---

## TESTING

```bash
# Reload SAG UI and navigate to Home Hub
curl -s http://192.168.132.223:4000/home-hub | grep "home-hub-container"

# Visual test in browser - should see:
# - Dark background
# - Stats row at top (4 cards)
# - Security alerts (if any)
# - Zone sections with device tile grids
# - Amber/gray device tiles based on online status
```

---

*For Seven Generations - Cherokee AI Federation*
