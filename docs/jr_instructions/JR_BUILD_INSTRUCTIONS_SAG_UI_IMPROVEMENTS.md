# Jr Build Instructions: SAG UI Improvements & Configurability

**Priority**: MEDIUM
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Integration Jr / Dev Triad Jr
**Date**: December 13, 2025

## Objective

Enhance the SAG Unified Interface with better configurability, UX improvements, and self-learning capabilities based on Tribe analysis.

## Current State Analysis

### What Works Well
- Multi-tab architecture (Events, Kanban, Monitoring, Grafana, IoT, Email, Console, Tribe)
- Sacred Fire theme with Cherokee branding
- Real-time event management with tier filtering
- Redis-based alert subscription
- Integration with thermal memory, Kanban, and email intelligence
- Command console for mission dispatch
- Tribe dashboard with stigmergy visualization

### Files Reviewed
```
/ganuda/home/dereadi/sag_unified_interface/
├── app.py                    (2287 lines - Flask backend)
├── templates/index.html      (623 lines - main UI)
├── static/
│   ├── css/unified.css       (29KB)
│   ├── css/sidebar.css       (10KB)
│   ├── css/dark-theme.css
│   ├── css/light-theme.css
│   └── js/
│       ├── unified.js        (1327 lines)
│       └── sidebar.js
```

---

## Improvement Categories

### 1. CONFIGURABILITY - Settings Panel

**Problem**: All settings are hardcoded (URLs, refresh intervals, thresholds)

**Solution**: Add a Settings tab with persistent configuration

```html
<!-- Add to tab navigation -->
<button class="tab-btn" data-tab="settings">⚙️ Settings</button>

<!-- Settings Tab Content -->
<div id="settings-tab" class="tab-content">
    <h2 style="margin-bottom: 20px; color: var(--sacred-green);">⚙️ Configuration</h2>

    <div class="settings-grid">
        <!-- Refresh Intervals -->
        <div class="settings-section">
            <h3>Refresh Intervals</h3>
            <div class="setting-row">
                <label>Events refresh (seconds):</label>
                <input type="number" id="setting-events-refresh" value="30" min="5" max="300">
            </div>
            <div class="setting-row">
                <label>Alerts refresh (seconds):</label>
                <input type="number" id="setting-alerts-refresh" value="10" min="5" max="60">
            </div>
            <div class="setting-row">
                <label>IoT devices refresh (seconds):</label>
                <input type="number" id="setting-iot-refresh" value="60" min="30" max="300">
            </div>
        </div>

        <!-- Service URLs -->
        <div class="settings-section">
            <h3>Service Endpoints</h3>
            <div class="setting-row">
                <label>Kanban URL:</label>
                <input type="text" id="setting-kanban-url" value="http://192.168.132.223:8002">
            </div>
            <div class="setting-row">
                <label>Grafana URL:</label>
                <input type="text" id="setting-grafana-url" value="http://192.168.132.223:3000">
            </div>
            <div class="setting-row">
                <label>Monitoring URL:</label>
                <input type="text" id="setting-monitoring-url" value="http://192.168.132.223:5555">
            </div>
        </div>

        <!-- Display Preferences -->
        <div class="settings-section">
            <h3>Display Preferences</h3>
            <div class="setting-row">
                <label>Default event limit:</label>
                <input type="number" id="setting-event-limit" value="50" min="10" max="200">
            </div>
            <div class="setting-row">
                <label>Show dismissed alerts:</label>
                <input type="checkbox" id="setting-show-dismissed">
            </div>
            <div class="setting-row">
                <label>Auto-expand sidebar:</label>
                <input type="checkbox" id="setting-sidebar-open" checked>
            </div>
            <div class="setting-row">
                <label>Sound on CRITICAL alerts:</label>
                <input type="checkbox" id="setting-sound-alerts">
            </div>
        </div>

        <!-- Theme -->
        <div class="settings-section">
            <h3>Theme</h3>
            <div class="setting-row">
                <label>Color scheme:</label>
                <select id="setting-theme">
                    <option value="dark">Sacred Fire (Dark)</option>
                    <option value="light">Dawn Light</option>
                    <option value="high-contrast">High Contrast</option>
                </select>
            </div>
        </div>
    </div>

    <div class="settings-actions">
        <button onclick="saveSettings()" class="btn-primary">💾 Save Settings</button>
        <button onclick="resetSettings()" class="btn-secondary">↩️ Reset to Defaults</button>
        <button onclick="exportSettings()" class="btn-secondary">📤 Export</button>
        <button onclick="importSettings()" class="btn-secondary">📥 Import</button>
    </div>
</div>
```

**JavaScript for Settings:**
```javascript
// Settings management
const DEFAULT_SETTINGS = {
    eventsRefresh: 30,
    alertsRefresh: 10,
    iotRefresh: 60,
    kanbanUrl: 'http://192.168.132.223:8002',
    grafanaUrl: 'http://192.168.132.223:3000',
    monitoringUrl: 'http://192.168.132.223:5555',
    eventLimit: 50,
    showDismissed: false,
    sidebarOpen: true,
    soundAlerts: false,
    theme: 'dark'
};

function loadSettings() {
    const saved = localStorage.getItem('sagSettings');
    return saved ? {...DEFAULT_SETTINGS, ...JSON.parse(saved)} : DEFAULT_SETTINGS;
}

function saveSettings() {
    const settings = {
        eventsRefresh: parseInt(document.getElementById('setting-events-refresh').value),
        alertsRefresh: parseInt(document.getElementById('setting-alerts-refresh').value),
        iotRefresh: parseInt(document.getElementById('setting-iot-refresh').value),
        kanbanUrl: document.getElementById('setting-kanban-url').value,
        grafanaUrl: document.getElementById('setting-grafana-url').value,
        monitoringUrl: document.getElementById('setting-monitoring-url').value,
        eventLimit: parseInt(document.getElementById('setting-event-limit').value),
        showDismissed: document.getElementById('setting-show-dismissed').checked,
        sidebarOpen: document.getElementById('setting-sidebar-open').checked,
        soundAlerts: document.getElementById('setting-sound-alerts').checked,
        theme: document.getElementById('setting-theme').value
    };

    localStorage.setItem('sagSettings', JSON.stringify(settings));
    applySettings(settings);
    showNotification('Settings saved!', 'success');
}

function applySettings(settings) {
    // Update refresh intervals
    if (window.eventsInterval) clearInterval(window.eventsInterval);
    window.eventsInterval = setInterval(loadEvents, settings.eventsRefresh * 1000);

    // Update iframe URLs
    document.querySelector('#kanban-tab iframe').src = settings.kanbanUrl;
    document.querySelector('#grafana-tab iframe').src = settings.grafanaUrl;
    document.querySelector('#monitoring-tab iframe').src = settings.monitoringUrl;

    // Apply theme
    document.body.className = `theme-${settings.theme}`;
}

function exportSettings() {
    const settings = loadSettings();
    const blob = new Blob([JSON.stringify(settings, null, 2)], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sag-settings.json';
    a.click();
}
```

---

### 2. UX IMPROVEMENTS

#### 2.1 Keyboard Shortcuts

```javascript
// Add keyboard navigation
document.addEventListener('keydown', function(e) {
    // Alt + number for tab switching
    if (e.altKey && e.key >= '1' && e.key <= '8') {
        const tabIndex = parseInt(e.key) - 1;
        const tabs = document.querySelectorAll('.tab-btn');
        if (tabs[tabIndex]) tabs[tabIndex].click();
    }

    // Ctrl + R to refresh current tab
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        refreshCurrentTab();
    }

    // Escape to close modals
    if (e.key === 'Escape') {
        closeAllModals();
    }

    // / to focus search (if added)
    if (e.key === '/' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        document.getElementById('global-search')?.focus();
    }
});
```

#### 2.2 Global Search

```html
<!-- Add to header -->
<div class="header-search">
    <input type="text" id="global-search" placeholder="Search events, devices, emails... (Press /)"
           oninput="debounce(globalSearch, 300)(this.value)">
    <div id="search-results" class="search-dropdown"></div>
</div>
```

```javascript
async function globalSearch(query) {
    if (query.length < 2) {
        document.getElementById('search-results').style.display = 'none';
        return;
    }

    const results = await fetch(`/api/search?q=${encodeURIComponent(query)}`).then(r => r.json());

    const container = document.getElementById('search-results');
    container.innerHTML = results.map(r => `
        <div class="search-result" onclick="navigateTo('${r.type}', ${r.id})">
            <span class="result-type">${r.type}</span>
            <span class="result-title">${r.title}</span>
        </div>
    `).join('');
    container.style.display = 'block';
}
```

#### 2.3 Notifications Toast System

```javascript
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => toast.classList.add('fade-out'), duration - 300);
    setTimeout(() => toast.remove(), duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}
```

---

### 3. IoT DEVICE MANAGEMENT ENHANCEMENTS

**Current**: Basic device list
**Improved**: Interactive management with authorization workflow

```html
<!-- Enhanced IoT Tab -->
<div id="iot-tab" class="tab-content">
    <h2>🏠 IoT Device Management</h2>

    <!-- Quick Filters -->
    <div class="iot-filters">
        <button class="filter-btn active" onclick="filterIoT('all')">All</button>
        <button class="filter-btn" onclick="filterIoT('active')">🟢 Active</button>
        <button class="filter-btn" onclick="filterIoT('inactive')">🔴 Inactive</button>
        <button class="filter-btn" onclick="filterIoT('unauthorized')">⚠️ Unauthorized</button>
        <button class="filter-btn" onclick="filterIoT('new')">🆕 New (24h)</button>
    </div>

    <!-- Action Bar -->
    <div class="iot-actions">
        <button onclick="triggerIoTScan()" class="btn-primary">🔍 Scan Network</button>
        <button onclick="exportIoTDevices()" class="btn-secondary">📤 Export CSV</button>
        <button onclick="showBulkAuthorize()" class="btn-secondary">✓ Bulk Authorize</button>
    </div>

    <!-- Statistics with click-to-filter -->
    <div class="stats-row">
        <div class="stat-card clickable" onclick="filterIoT('all')">
            <div class="stat-value" id="iot-total-devices">-</div>
            <div class="stat-label">Total Devices</div>
        </div>
        <!-- ... other stats ... -->
    </div>

    <!-- Device Grid with Actions -->
    <div id="iot-devices-list" class="iot-devices-grid"></div>
</div>
```

**Device Card with Actions:**
```javascript
function renderIoTDevice(device) {
    const statusClass = device.status === 'active' ? 'online' : 'offline';
    const authBadge = device.is_authorized ?
        '<span class="badge authorized">✓ Authorized</span>' :
        '<span class="badge unauthorized">⚠️ Pending</span>';

    return `
        <div class="iot-device-card ${statusClass}" data-mac="${device.mac_address}">
            <div class="device-header">
                <span class="device-ip">${device.ip_address}</span>
                ${authBadge}
            </div>
            <div class="device-vendor">${device.vendor || 'Unknown'}</div>
            <div class="device-mac">${device.mac_address}</div>
            <div class="device-meta">
                <span>Last seen: ${formatRelativeTime(device.last_seen)}</span>
                ${device.device_class ? `<span class="device-class">${device.device_class}</span>` : ''}
            </div>
            <div class="device-actions">
                ${!device.is_authorized ? `
                    <button onclick="authorizeDevice('${device.mac_address}')" class="btn-sm btn-success">✓ Authorize</button>
                    <button onclick="blockDevice('${device.mac_address}')" class="btn-sm btn-danger">✗ Block</button>
                ` : `
                    <button onclick="revokeDevice('${device.mac_address}')" class="btn-sm btn-warning">Revoke</button>
                `}
                <button onclick="showDeviceDetails('${device.mac_address}')" class="btn-sm">Details</button>
            </div>
        </div>
    `;
}
```

---

### 4. SELF-LEARNING INTEGRATION

Add usage analytics that feed back into thermal memory:

```python
# Add to app.py

@app.route('/api/analytics/track', methods=['POST'])
def track_usage():
    """Track UI usage patterns for self-learning"""
    data = request.json

    # Log to thermal memory
    thermal_client.store({
        'type': 'ui_usage',
        'action': data.get('action'),
        'tab': data.get('tab'),
        'duration': data.get('duration'),
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.now().isoformat()
    }, temperature=50)  # Start warm, decay naturally

    return jsonify({'status': 'tracked'})


@app.route('/api/analytics/suggestions')
def get_suggestions():
    """Get UI improvement suggestions based on usage patterns"""
    # Query thermal memory for UI usage patterns
    patterns = thermal_client.search('ui_usage', limit=100)

    suggestions = analyze_usage_patterns(patterns)

    return jsonify({
        'suggestions': suggestions,
        'based_on_samples': len(patterns)
    })


def analyze_usage_patterns(patterns):
    """Analyze patterns and generate suggestions"""
    suggestions = []

    # Most used tabs
    tab_counts = {}
    for p in patterns:
        tab = p.get('tab')
        if tab:
            tab_counts[tab] = tab_counts.get(tab, 0) + 1

    if tab_counts:
        most_used = max(tab_counts, key=tab_counts.get)
        suggestions.append({
            'type': 'default_tab',
            'message': f'Consider making "{most_used}" the default tab',
            'confidence': tab_counts[most_used] / len(patterns)
        })

    return suggestions
```

**Frontend tracking:**
```javascript
// Track tab switches
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        fetch('/api/analytics/track', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'tab_switch',
                tab: this.dataset.tab,
                timestamp: Date.now()
            })
        });
    });
});

// Track session duration per tab
let currentTab = 'events';
let tabStartTime = Date.now();

function trackTabDuration() {
    const duration = Date.now() - tabStartTime;
    fetch('/api/analytics/track', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            action: 'tab_duration',
            tab: currentTab,
            duration: duration
        })
    });
}

// Track before tab switch
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        trackTabDuration();
        currentTab = this.dataset.tab;
        tabStartTime = Date.now();
    });
});
```

---

### 5. MOBILE RESPONSIVENESS

**Current issue**: Fixed sidebar doesn't work well on mobile

```css
/* Add to unified.css */

@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        left: -280px;
        width: 280px;
        height: 100vh;
        transition: left 0.3s ease;
        z-index: 1000;
    }

    .sidebar.open {
        left: 0;
    }

    .main-content {
        margin-left: 0 !important;
        padding: 10px;
    }

    .tab-nav {
        overflow-x: auto;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
    }

    .tab-btn {
        padding: 8px 12px;
        font-size: 0.9em;
    }

    .stats-row {
        flex-direction: column;
    }

    .stat-card {
        width: 100%;
        margin-bottom: 10px;
    }

    .iot-devices-grid {
        grid-template-columns: 1fr;
    }

    .tribe-columns {
        flex-direction: column;
    }

    /* Floating toggle button for mobile */
    .mobile-sidebar-toggle {
        display: block;
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--sacred-green);
        color: var(--bg-primary);
        border: none;
        font-size: 24px;
        z-index: 999;
        box-shadow: 0 4px 12px rgba(0, 255, 0, 0.3);
    }
}

@media (min-width: 769px) {
    .mobile-sidebar-toggle {
        display: none;
    }
}
```

---

### 6. ACCESSIBILITY IMPROVEMENTS

```html
<!-- Add skip link -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Add ARIA labels -->
<nav class="tab-nav" role="tablist" aria-label="Main navigation">
    <button class="tab-btn active" data-tab="events" role="tab"
            aria-selected="true" aria-controls="events-tab">📊 Event Management</button>
    <!-- ... -->
</nav>

<div id="events-tab" class="tab-content active" role="tabpanel"
     aria-labelledby="events-tab-btn" tabindex="0">
```

```css
/* Focus indicators */
.tab-btn:focus,
.filter-btn:focus,
button:focus {
    outline: 2px solid var(--sacred-green);
    outline-offset: 2px;
}

/* Skip link */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--sacred-green);
    color: var(--bg-primary);
    padding: 8px;
    z-index: 100;
}

.skip-link:focus {
    top: 0;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## Backend Endpoints to Add

```python
# Add to app.py

@app.route('/api/search')
def global_search():
    """Global search across events, IoT devices, emails"""
    query = request.args.get('q', '').lower()
    results = []

    # Search events
    events = event_manager.get_events(limit=100)
    for e in events:
        if query in e['title'].lower() or query in e.get('description', '').lower():
            results.append({
                'type': 'event',
                'id': e['id'],
                'title': e['title'],
                'tier': e['tier']
            })

    # Search IoT devices
    devices = get_iot_devices()
    for d in devices:
        if query in d['ip_address'] or query in d.get('vendor', '').lower():
            results.append({
                'type': 'iot',
                'id': d['mac_address'],
                'title': f"{d['ip_address']} - {d.get('vendor', 'Unknown')}"
            })

    return jsonify(results[:20])


@app.route('/api/settings', methods=['GET', 'POST'])
def user_settings():
    """Get or save user settings (server-side persistence)"""
    if request.method == 'GET':
        # Return from database or defaults
        return jsonify(get_user_settings(request.remote_addr))
    else:
        settings = request.json
        save_user_settings(request.remote_addr, settings)
        return jsonify({'status': 'saved'})


@app.route('/api/iot/scan', methods=['POST'])
def trigger_iot_scan():
    """Trigger an IoT network scan"""
    # Call the scanner on greenfin
    result = subprocess.run(
        ['ssh', 'dereadi@192.168.132.224', '/ganuda/scripts/iot_scan.sh', 'discovery'],
        capture_output=True,
        timeout=120
    )
    return jsonify({
        'status': 'completed' if result.returncode == 0 else 'failed',
        'output': result.stdout.decode()
    })


@app.route('/api/iot/<mac_address>/authorize', methods=['POST'])
def authorize_iot_device(mac_address):
    """Authorize an IoT device"""
    data = request.json or {}
    notes = data.get('notes', 'Authorized via SAG UI')

    # Update database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE iot_devices
        SET is_authorized = true, notes = COALESCE(notes || ' | ', '') || %s
        WHERE mac_address = %s
        RETURNING ip_address, vendor
    """, (notes, mac_address))
    result = cursor.fetchone()
    conn.commit()

    return jsonify({
        'status': 'authorized',
        'mac_address': mac_address,
        'device': result
    })
```

---

## Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 1 | Settings Panel | Medium | High |
| 2 | Keyboard Shortcuts | Low | Medium |
| 3 | IoT Management Enhancements | Medium | High |
| 4 | Global Search | Medium | Medium |
| 5 | Mobile Responsiveness | Medium | Medium |
| 6 | Self-Learning Analytics | High | High |
| 7 | Accessibility | Low | Medium |
| 8 | Toast Notifications | Low | Low |

---

## Verification Checklist

- [ ] Settings tab added with all configuration options
- [ ] Settings persist in localStorage and optionally server-side
- [ ] Keyboard shortcuts working (Alt+1-8, Ctrl+R, Escape, /)
- [ ] Global search endpoint added
- [ ] IoT device authorization workflow complete
- [ ] Mobile responsive design tested on phone/tablet
- [ ] Usage analytics tracking to thermal memory
- [ ] ARIA labels and focus indicators added
- [ ] Toast notification system working

---

FOR SEVEN GENERATIONS - Continuous improvement honors the user's time.
