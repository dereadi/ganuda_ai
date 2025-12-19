# Jr Build Instructions: SAG Homepage Redesign
## Priority: HIGH - Face of the Federation
## Estimated Effort: 4 Phases

---

## Objective

Transform SAG Unified Interface homepage from observational dashboard to interactive control room.

**Key Shift:** Users don't just watch. They **operate**.

---

## Reference Documents

- `/Users/dereadi/Documents/sag_unified_interface_homepage_redesign_sketch.md` (Design spec)
- `/ganuda/docs/ULTRATHINK_SAG_UI_REDESIGN_DEC14_2025.md` (Strategic analysis)

---

## Current State

Location: `/home/dereadi/sag_unified_interface/` on redfin
- `app.py` - Flask backend (72KB)
- `templates/index.html` - Main template
- `static/css/unified.css` - Styles
- `static/js/unified.js` - Frontend logic

Running at: http://192.168.132.223:4000

---

## Phase 1: Layout Foundation

### Task 1.1: Create New Base Layout

Modify `templates/index.html` to implement three-zone layout:

```html
<body>
  <!-- Command Bar (Top) -->
  <header class="command-bar">
    <div class="search-container">
      <input type="text" id="global-search" placeholder="Search devices, services, IPs...">
    </div>
    <div class="scope-selector">
      <select id="scope-select">
        <option value="all">All Systems</option>
        <option value="nodes">Nodes Only</option>
        <option value="services">Services Only</option>
        <option value="iot">IoT Devices</option>
      </select>
    </div>
    <div class="quick-actions">
      <button id="btn-health-check" class="action-btn">Run Health Check</button>
      <button id="btn-maintenance" class="action-btn">Maintenance Mode</button>
    </div>
    <div class="system-status">
      <span id="status-indicator" class="status-healthy">● Healthy</span>
    </div>
  </header>

  <div class="main-container">
    <!-- Sidebar (Left) -->
    <nav class="sidebar">
      <div class="nav-section">
        <h4>OVERVIEW</h4>
        <a href="#" class="nav-item active">Home</a>
      </div>
      <div class="nav-section">
        <h4>SYSTEMS</h4>
        <a href="#nodes" class="nav-item">Nodes</a>
        <a href="#services" class="nav-item">Services</a>
        <a href="#iot" class="nav-item">IoT Devices</a>
      </div>
      <div class="nav-section">
        <h4>OPERATIONS</h4>
        <a href="#alerts" class="nav-item">Alerts</a>
        <a href="#changes" class="nav-item">Changes</a>
        <a href="#logs" class="nav-item">Logs</a>
      </div>
      <div class="nav-section">
        <h4>GOVERNANCE</h4>
        <a href="#triads" class="nav-item">Triads</a>
        <a href="#audit" class="nav-item">Audit</a>
      </div>
    </nav>

    <!-- Main Control Surface -->
    <main class="control-surface">
      <!-- Content goes here -->
    </main>
  </div>

  <!-- Configuration Drawer (Hidden by default) -->
  <aside id="config-drawer" class="config-drawer hidden">
    <!-- Drawer content -->
  </aside>
</body>
```

### Task 1.2: Create New CSS Structure

Add to `static/css/unified.css`:

```css
/* ========================================
   SAG Control Room Layout
   ======================================== */

:root {
  --spacing-unit: 8px;
  --color-healthy: #22c55e;
  --color-warning: #eab308;
  --color-critical: #ef4444;
  --color-neutral: #6b7280;
  --color-surface: #1f2937;
  --color-surface-raised: #374151;
  --color-text: #f9fafb;
  --color-text-muted: #9ca3af;
  --color-accent: #3b82f6;
}

/* Command Bar */
.command-bar {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing-unit) * 2);
  padding: calc(var(--spacing-unit) * 2);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-surface-raised);
  position: sticky;
  top: 0;
  z-index: 100;
}

.search-container input {
  width: 300px;
  padding: var(--spacing-unit);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-neutral);
  border-radius: 4px;
  color: var(--color-text);
}

.scope-selector select {
  padding: var(--spacing-unit);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-neutral);
  border-radius: 4px;
  color: var(--color-text);
}

.quick-actions {
  display: flex;
  gap: var(--spacing-unit);
  margin-left: auto;
}

.action-btn {
  padding: var(--spacing-unit) calc(var(--spacing-unit) * 2);
  background: var(--color-accent);
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-weight: 500;
}

.action-btn:hover {
  filter: brightness(1.1);
}

.system-status {
  padding: 0 calc(var(--spacing-unit) * 2);
}

.status-healthy { color: var(--color-healthy); }
.status-warning { color: var(--color-warning); }
.status-critical { color: var(--color-critical); }

/* Main Container */
.main-container {
  display: flex;
  min-height: calc(100vh - 60px);
}

/* Sidebar */
.sidebar {
  width: 200px;
  background: var(--color-surface);
  padding: calc(var(--spacing-unit) * 2);
  border-right: 1px solid var(--color-surface-raised);
  flex-shrink: 0;
}

.nav-section {
  margin-bottom: calc(var(--spacing-unit) * 3);
}

.nav-section h4 {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-unit);
}

.nav-item {
  display: block;
  padding: var(--spacing-unit);
  color: var(--color-text);
  text-decoration: none;
  border-radius: 4px;
  margin-bottom: 2px;
}

.nav-item:hover {
  background: var(--color-surface-raised);
}

.nav-item.active {
  background: var(--color-accent);
}

/* Control Surface */
.control-surface {
  flex: 1;
  padding: calc(var(--spacing-unit) * 3);
  background: #111827;
  overflow-y: auto;
}

/* Configuration Drawer */
.config-drawer {
  position: fixed;
  right: 0;
  top: 0;
  width: 400px;
  height: 100vh;
  background: var(--color-surface);
  border-left: 1px solid var(--color-surface-raised);
  padding: calc(var(--spacing-unit) * 3);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 200;
  overflow-y: auto;
}

.config-drawer.open {
  transform: translateX(0);
}

.config-drawer.hidden {
  display: none;
}
```

### Task 1.3: Preserve Existing Functionality

Move current widgets into the new layout structure. Do NOT delete functionality yet - just reorganize.

---

## Phase 2: Control Surface Implementation

### Task 2.1: Status Summary Row

Add to control surface:

```html
<section class="status-summary">
  <div class="status-card">
    <h3>SYSTEMS</h3>
    <div class="status-value">
      <span class="big-number" id="systems-healthy">6</span> Healthy
    </div>
    <div class="status-detail" id="systems-down">0 Down</div>
  </div>
  
  <div class="status-card">
    <h3>ALERTS</h3>
    <div class="status-value">
      <span class="big-number warning" id="alerts-warning">2</span> Warning
    </div>
    <div class="status-detail" id="alerts-critical">0 Critical</div>
  </div>
  
  <div class="status-card">
    <h3>UTILIZATION</h3>
    <div class="status-value">
      CPU <span id="cpu-util">42%</span>
    </div>
    <div class="status-detail">RAM <span id="ram-util">58%</span></div>
  </div>
  
  <div class="status-card">
    <h3>CHANGES</h3>
    <div class="status-value">
      <span class="big-number" id="changes-pending">1</span> Pending
    </div>
    <div class="status-detail">Last: <span id="last-change">5m ago</span></div>
  </div>
</section>
```

CSS for status cards:

```css
.status-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: calc(var(--spacing-unit) * 2);
  margin-bottom: calc(var(--spacing-unit) * 3);
}

.status-card {
  background: var(--color-surface);
  padding: calc(var(--spacing-unit) * 2);
  border-radius: 8px;
  border: 1px solid var(--color-surface-raised);
}

.status-card h3 {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-unit);
}

.status-value {
  font-size: 18px;
  color: var(--color-text);
}

.big-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-healthy);
}

.big-number.warning {
  color: var(--color-warning);
}

.big-number.critical {
  color: var(--color-critical);
}

.status-detail {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 4px;
}
```

### Task 2.2: Node Cards

```html
<section class="systems-grid">
  <h2>Active Systems</h2>
  <div class="card-grid">
    <!-- Template for node card -->
    <div class="system-card" data-node="bluefin">
      <div class="card-header">
        <span class="card-icon">🖥️</span>
        <span class="card-title">Bluefin</span>
        <span class="card-status status-healthy">● Active</span>
      </div>
      <div class="card-metrics">
        <span>CPU 38%</span> | <span>RAM 61%</span>
      </div>
      <div class="card-detail">
        DB: Healthy
      </div>
      <div class="card-actions">
        <button class="btn-configure" data-target="bluefin">Configure</button>
        <button class="btn-restart" data-target="bluefin">Restart</button>
      </div>
    </div>
    
    <!-- Repeat for other nodes -->
  </div>
</section>
```

CSS:

```css
.systems-grid h2 {
  color: var(--color-text);
  font-size: 16px;
  font-weight: 600;
  margin-bottom: calc(var(--spacing-unit) * 2);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: calc(var(--spacing-unit) * 2);
}

.system-card {
  background: var(--color-surface);
  border: 1px solid var(--color-surface-raised);
  border-radius: 8px;
  padding: calc(var(--spacing-unit) * 2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-unit);
  margin-bottom: calc(var(--spacing-unit) * 2);
}

.card-icon {
  font-size: 20px;
}

.card-title {
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
}

.card-status {
  font-size: 13px;
}

.card-metrics {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: var(--spacing-unit);
}

.card-detail {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: calc(var(--spacing-unit) * 2);
}

.card-actions {
  display: flex;
  gap: var(--spacing-unit);
}

.card-actions button {
  flex: 1;
  padding: var(--spacing-unit);
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.btn-configure {
  background: var(--color-surface-raised);
  color: var(--color-text);
  border: 1px solid var(--color-neutral) !important;
}

.btn-restart {
  background: var(--color-accent);
  color: white;
}
```

### Task 2.3: IoT Device Cards

```html
<section class="iot-grid">
  <h2>IoT Devices</h2>
  <div class="card-grid" id="iot-cards">
    <!-- Dynamically populated -->
  </div>
</section>
```

JavaScript template for IoT cards:

```javascript
function renderIoTCard(device) {
  return `
    <div class="iot-card" data-ip="${device.ip}">
      <div class="card-header">
        <span class="card-icon">🏠</span>
        <span class="card-title">${device.ip}</span>
        <span class="card-status ${device.online ? 'status-healthy' : 'status-critical'}">
          ● ${device.online ? 'Active' : 'Offline'}
        </span>
      </div>
      <div class="card-detail">
        Type: ${device.type || 'Unknown'}<br>
        Last Seen: ${device.lastSeen}
      </div>
      <div class="card-toggles">
        <label class="toggle-row">
          <span>Managed</span>
          <input type="checkbox" class="toggle-managed" ${device.managed ? 'checked' : ''}>
        </label>
        <label class="toggle-row">
          <span>Monitoring</span>
          <input type="checkbox" class="toggle-monitoring" ${device.monitoring ? 'checked' : ''}>
        </label>
      </div>
      <div class="card-actions">
        <button class="btn-configure" data-target="${device.ip}">Configure</button>
        <button class="btn-isolate" data-target="${device.ip}">Isolate</button>
      </div>
    </div>
  `;
}
```

---

## Phase 3: Configuration Drawer

### Task 3.1: Drawer Structure

```html
<aside id="config-drawer" class="config-drawer">
  <div class="drawer-header">
    <h2 id="drawer-title">Configure: Device</h2>
    <button id="drawer-close" class="drawer-close">×</button>
  </div>
  
  <div class="drawer-tabs">
    <button class="tab active" data-tab="runtime">Runtime</button>
    <button class="tab" data-tab="alerts">Alerts</button>
    <button class="tab" data-tab="network">Network</button>
    <button class="tab" data-tab="security">Security</button>
  </div>
  
  <div class="drawer-content" id="drawer-content">
    <!-- Tab content rendered here -->
  </div>
  
  <div class="drawer-footer">
    <div class="pending-changes">
      <span id="pending-count">0</span> pending changes
    </div>
    <div class="drawer-actions">
      <button id="btn-discard" class="btn-secondary">Discard</button>
      <button id="btn-apply" class="btn-primary">Apply</button>
    </div>
  </div>
</aside>
```

### Task 3.2: Configuration Schema

Create `/home/dereadi/sag_unified_interface/config_schema.py`:

```python
"""
SAG Configuration Schema
UI-driven configuration with validation
"""

CONFIG_SCHEMA = {
    "monitoring": {
        "pollIntervalSeconds": {
            "type": "number",
            "min": 5,
            "max": 300,
            "default": 30,
            "label": "Poll Interval (seconds)"
        },
        "autoManage": {
            "type": "boolean",
            "default": True,
            "label": "Auto-Manage Device"
        }
    },
    "alerts": {
        "cpuWarnThreshold": {
            "type": "number",
            "min": 50,
            "max": 100,
            "default": 70,
            "label": "CPU Warning Threshold (%)"
        },
        "ramWarnThreshold": {
            "type": "number",
            "min": 50,
            "max": 100,
            "default": 80,
            "label": "RAM Warning Threshold (%)"
        },
        "offlineAfterMinutes": {
            "type": "number",
            "min": 1,
            "max": 60,
            "default": 5,
            "label": "Mark Offline After (minutes)"
        }
    },
    "security": {
        "enableTriadSecurity": {
            "type": "boolean",
            "default": False,
            "label": "Enable Triad Security Review"
        },
        "requireApproval": {
            "type": "boolean",
            "default": False,
            "label": "Require Change Approval"
        }
    }
}

def validate_setting(category, key, value):
    """Validate a setting against schema"""
    if category not in CONFIG_SCHEMA:
        return False, f"Unknown category: {category}"
    if key not in CONFIG_SCHEMA[category]:
        return False, f"Unknown setting: {key}"
    
    schema = CONFIG_SCHEMA[category][key]
    
    if schema["type"] == "number":
        if not isinstance(value, (int, float)):
            return False, "Must be a number"
        if value < schema.get("min", float("-inf")):
            return False, f"Minimum value is {schema['min']}"
        if value > schema.get("max", float("inf")):
            return False, f"Maximum value is {schema['max']}"
    
    elif schema["type"] == "boolean":
        if not isinstance(value, bool):
            return False, "Must be true or false"
    
    return True, None
```

### Task 3.3: Backend API Endpoints

Add to `app.py`:

```python
from config_schema import CONFIG_SCHEMA, validate_setting

# Staged changes storage (in production, use database)
staged_changes = {}

@app.route('/api/config/schema')
def get_config_schema():
    """Return configuration schema for UI rendering"""
    return jsonify(CONFIG_SCHEMA)

@app.route('/api/config/<target>')
def get_config(target):
    """Get current configuration for a target"""
    # Fetch from database or defaults
    config = get_target_config(target)
    return jsonify(config)

@app.route('/api/config/<target>/stage', methods=['POST'])
def stage_change(target):
    """Stage a configuration change (does not apply yet)"""
    data = request.json
    category = data.get('category')
    key = data.get('key')
    value = data.get('value')
    
    # Validate
    valid, error = validate_setting(category, key, value)
    if not valid:
        return jsonify({"error": error}), 400
    
    # Stage the change
    if target not in staged_changes:
        staged_changes[target] = {}
    staged_changes[target][f"{category}.{key}"] = {
        "value": value,
        "staged_at": datetime.utcnow().isoformat(),
        "staged_by": get_current_user()
    }
    
    return jsonify({
        "staged": True,
        "pending_count": len(staged_changes.get(target, {}))
    })

@app.route('/api/config/<target>/apply', methods=['POST'])
def apply_changes(target):
    """Apply all staged changes for a target"""
    if target not in staged_changes:
        return jsonify({"error": "No pending changes"}), 400
    
    changes = staged_changes[target]
    
    # Apply each change
    for setting_path, change in changes.items():
        category, key = setting_path.split('.', 1)
        apply_setting(target, category, key, change['value'])
        
        # Log to audit
        log_config_change(
            target=target,
            setting=setting_path,
            old_value=get_current_value(target, category, key),
            new_value=change['value'],
            changed_by=change['staged_by']
        )
    
    # Clear staged changes
    del staged_changes[target]
    
    return jsonify({"applied": True, "count": len(changes)})

@app.route('/api/config/<target>/discard', methods=['POST'])
def discard_changes(target):
    """Discard all staged changes for a target"""
    if target in staged_changes:
        del staged_changes[target]
    return jsonify({"discarded": True})
```

### Task 3.4: Frontend Drawer Logic

Add to `static/js/unified.js`:

```javascript
// Configuration Drawer
const configDrawer = {
  target: null,
  pendingChanges: {},
  
  async open(target) {
    this.target = target;
    this.pendingChanges = {};
    
    document.getElementById('drawer-title').textContent = `Configure: ${target}`;
    document.getElementById('config-drawer').classList.add('open');
    document.getElementById('config-drawer').classList.remove('hidden');
    
    // Load schema and current config
    const [schema, config] = await Promise.all([
      fetch('/api/config/schema').then(r => r.json()),
      fetch(`/api/config/${target}`).then(r => r.json())
    ]);
    
    this.renderTab('runtime', schema, config);
  },
  
  close() {
    document.getElementById('config-drawer').classList.remove('open');
    setTimeout(() => {
      document.getElementById('config-drawer').classList.add('hidden');
    }, 300);
  },
  
  renderTab(tabName, schema, config) {
    const content = document.getElementById('drawer-content');
    let html = '';
    
    const category = schema[tabName];
    if (!category) return;
    
    for (const [key, def] of Object.entries(category)) {
      const currentValue = config[tabName]?.[key] ?? def.default;
      
      if (def.type === 'boolean') {
        html += `
          <label class="config-row">
            <span>${def.label}</span>
            <input type="checkbox" 
                   data-category="${tabName}" 
                   data-key="${key}"
                   ${currentValue ? 'checked' : ''}>
          </label>
        `;
      } else if (def.type === 'number') {
        html += `
          <label class="config-row">
            <span>${def.label}</span>
            <input type="number" 
                   data-category="${tabName}" 
                   data-key="${key}"
                   value="${currentValue}"
                   min="${def.min || ''}"
                   max="${def.max || ''}">
          </label>
        `;
      }
    }
    
    content.innerHTML = html;
    
    // Attach change listeners
    content.querySelectorAll('input').forEach(input => {
      input.addEventListener('change', (e) => this.stageChange(e.target));
    });
  },
  
  async stageChange(input) {
    const category = input.dataset.category;
    const key = input.dataset.key;
    const value = input.type === 'checkbox' ? input.checked : Number(input.value);
    
    const response = await fetch(`/api/config/${this.target}/stage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, key, value })
    });
    
    const result = await response.json();
    if (result.staged) {
      document.getElementById('pending-count').textContent = result.pending_count;
    }
  },
  
  async apply() {
    const response = await fetch(`/api/config/${this.target}/apply`, {
      method: 'POST'
    });
    
    const result = await response.json();
    if (result.applied) {
      this.close();
      showNotification(`Applied ${result.count} changes`);
    }
  },
  
  async discard() {
    await fetch(`/api/config/${this.target}/discard`, { method: 'POST' });
    this.close();
  }
};

// Event listeners
document.getElementById('drawer-close').addEventListener('click', () => configDrawer.close());
document.getElementById('btn-apply').addEventListener('click', () => configDrawer.apply());
document.getElementById('btn-discard').addEventListener('click', () => configDrawer.discard());

// Configure buttons
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('btn-configure')) {
    configDrawer.open(e.target.dataset.target);
  }
});
```

---

## Phase 4: Polish & Integration

### Task 4.1: Visual Refinement

Apply design rules:
- [ ] Green = success/active only (no decorative green)
- [ ] Remove glowing borders
- [ ] Verify 8px spacing grid
- [ ] Single accent color (blue)
- [ ] Typography scale: 11px labels, 13px body, 16px headings

### Task 4.2: Remove Deprecated Widgets

From homepage, remove or move to secondary views:
- [ ] Markets widget → separate Markets page
- [ ] Weather widget → remove or move to footer
- [ ] Full metric charts → Monitoring page
- [ ] Agent grids → Triads page

### Task 4.3: Responsive Design

```css
@media (max-width: 1024px) {
  .status-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .sidebar {
    width: 60px;
  }
  
  .sidebar .nav-item span {
    display: none;
  }
}

@media (max-width: 768px) {
  .command-bar {
    flex-wrap: wrap;
  }
  
  .sidebar {
    display: none;
  }
  
  .config-drawer {
    width: 100%;
  }
}
```

### Task 4.4: Audit Logging

Ensure all configuration changes are logged:

```python
def log_config_change(target, setting, old_value, new_value, changed_by):
    """Log configuration change to audit table"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO config_audit_log 
            (target, setting, old_value, new_value, changed_by, changed_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (target, setting, json.dumps(old_value), json.dumps(new_value), changed_by))
        conn.commit()
```

---

## Testing Checklist

### Functionality
- [ ] Command bar search filters correctly
- [ ] Scope selector filters all views
- [ ] Node cards display accurate status
- [ ] IoT cards show real-time data
- [ ] Configuration drawer opens/closes
- [ ] Staged changes persist until apply/discard
- [ ] Apply commits changes and logs to audit
- [ ] Discard clears staged changes

### Visual
- [ ] No glowing borders
- [ ] Consistent 8px spacing
- [ ] Green only for healthy/success
- [ ] Cards are readable in <3 seconds
- [ ] Buttons have clear affordance

### Performance
- [ ] Page loads in <2 seconds
- [ ] Secondary views lazy load
- [ ] No unnecessary API calls

---

## Success Criteria

1. ✅ Operator assesses system health in <3 seconds
2. ✅ Configuration changes are staged, reviewed, auditable
3. ✅ No accidental destructive actions (staged changes pattern)
4. ✅ Works without external dependencies (air-gapped ready)
5. ✅ Scales visually from 6 nodes to 60 nodes

---

## File Locations

| File | Purpose |
|------|---------|
| `templates/index.html` | Main page structure |
| `static/css/unified.css` | All styles |
| `static/js/unified.js` | Frontend logic |
| `config_schema.py` | Configuration schema |
| `app.py` | Backend API |

---

*For Seven Generations*
