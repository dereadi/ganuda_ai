# KB-SAG-ARCHITECTURE: SAG Unified Interface Architecture Reference

**Date:** 2025-12-06
**Author:** TPM (Command Post)
**Category:** Architecture Reference
**Audience:** IT Jr Agents, Dev Jr Agents
**Priority:** HIGH - Reference before modifying SAG

---

## Purpose

This KB documents the SAG (Situational Awareness Gateway) Unified Interface architecture. Jr agents MUST reference this before making changes to SAG.

---

## 1. System Overview

SAG is a Flask-based web application that serves as the Cherokee AI command center, integrating multiple subsystems into a single dashboard.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAG Unified Interface                         │
│                 http://192.168.132.223:4000                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │  Events  │ │  Kanban  │ │Monitoring│ │ Grafana  │ │  IoT   ││
│  │Dashboard │ │  Board   │ │  Panel   │ │  Embed   │ │Devices ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│       │            │            │            │           │      │
│       ▼            ▼            ▼            ▼           ▼      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Flask Backend (app.py)                  ││
│  │                                                             ││
│  │  /api/events/*     /api/kanban/*    /api/metrics/*         ││
│  │  /api/federation/* /api/fara/*      /api/ganuda/*          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   PostgreSQL (bluefin)        │
              │   192.168.132.222:5432        │
              │                               │
              │   Databases:                  │
              │   - triad_federation          │
              │   - zammad_production         │
              └───────────────────────────────┘
```

---

## 2. Network Topology

| Host | IP | Role | Key Services |
|------|-----|------|--------------|
| **redfin** | 192.168.132.223 | SAG Host | Flask:4000, Visual Kanban:5000/8002 |
| **bluefin** | 192.168.132.222 | Database | PostgreSQL:5432 |
| **bmasass** | 192.168.132.50 | macOS Workstation | FARA captures, Command Post |
| **sasass** | 192.168.132.51 | Linux Workstation | Ollama LLM |
| **sasass2** | 192.168.132.52 | Linux Workstation | Ollama LLM |
| **greenfin** | 192.168.132.224 | Processing | Monitoring agents |

---

## 3. Current Tab Structure

| Tab | Icon | Function | Data Source |
|-----|------|----------|-------------|
| Event Management | 📊 | Alert dashboard, event triage | sag_events table |
| Kanban Board | 📋 | Ticket tracking (iframe) | duyuktv_tickets via port 8002 |
| Monitoring | 🔍 | Federation node status | ganuda_view_nodes |
| Grafana | 📈 | Metrics visualization | Grafana embed :3000 |
| IoT Devices | 🏠 | Device management | iot_devices table |
| Email Intelligence | 📧 | Email analysis | email_intelligence table |

---

## 4. File Structure

```
/ganuda/home/dereadi/sag_unified_interface/
│
├── app.py                      # Main Flask application (1672 lines)
│   ├── Routes: /, /api/events/*, /api/metrics/*, etc.
│   ├── Database connections
│   └── WebSocket support
│
├── templates/
│   └── index.html              # Single-page app with tabs
│       ├── Tab navigation
│       ├── Tab content divs
│       └── Embedded JavaScript
│
├── static/
│   ├── css/
│   │   └── styles.css          # Main stylesheet
│   └── js/
│       ├── unified.js          # Main app JavaScript (45KB)
│       ├── sidebar.js          # Sidebar functionality
│       └── theme-switcher.js   # Dark/light mode
│
├── event_manager.py            # Event handling logic
├── thermal_memory_client.py    # Thermal memory access
├── kanban_integration.py       # Kanban API client
├── fara_integration.py         # FARA prediction handling
├── federation_monitor.py       # Node monitoring
├── email_intelligence.py       # Email processing
└── action_integrations.py      # Action button handlers
```

---

## 5. Database Schema (Key Tables)

### triad_federation database

```sql
-- Thermal Memory (core communication)
triad_shared_memories (
    id UUID PRIMARY KEY,
    content TEXT,
    temperature FLOAT (0-100),
    source_triad VARCHAR(255),
    tags TEXT[],
    created_at TIMESTAMP
)

-- SAG Events
sag_events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    tier VARCHAR(20),  -- CRITICAL, IMPORTANT, FYI
    source VARCHAR(100),
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
)

-- Node Metrics
ganuda_view_metrics (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(50),
    cpu_percent FLOAT,
    memory_percent FLOAT,
    disk_percent FLOAT,
    timestamp TIMESTAMP
)

-- Node Status
ganuda_view_nodes (
    hostname VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20),
    last_heartbeat TIMESTAMP,
    ip_address VARCHAR(45)
)

-- Settings (to be created)
sag_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value JSONB,
    description TEXT,
    category VARCHAR(50),
    editable BOOLEAN,
    updated_at TIMESTAMP
)
```

### zammad_production database

```sql
-- Kanban Tickets
duyuktv_tickets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    priority INTEGER,
    assignee VARCHAR(100),
    thermal_zone VARCHAR(20),
    cultural_impact INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## 6. API Endpoint Reference

### Events API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events` | GET | List all events |
| `/api/events` | POST | Create new event |
| `/api/events/<id>` | GET | Get single event |
| `/api/events/<id>/resolve` | POST | Mark event resolved |

### Metrics API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics/delta` | GET | Get metric deltas |
| `/api/metrics/threshold-bar` | GET | Threshold bar data |

### Federation API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/federation/nodes` | GET | List all nodes |
| `/api/federation/nodes/<hostname>` | GET | Single node status |

### FARA API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fara/predictions` | GET | Recent predictions |
| `/api/fara/analyze` | POST | Analyze image |

---

## 7. Adding a New Tab (Step by Step)

### Step 1: Add Tab Button to index.html

```html
<!-- Find the tab-nav section -->
<nav class="tab-nav">
    <!-- Add after existing tabs -->
    <button class="tab-btn" data-tab="newtab">🆕 New Tab</button>
</nav>
```

### Step 2: Add Tab Content Div

```html
<!-- Find the tab content section -->
<div id="newtab-tab" class="tab-content">
    <div class="tab-header">
        <h2>New Tab Title</h2>
    </div>
    <div id="newtab-content">
        Loading...
    </div>
</div>
```

### Step 3: Add API Endpoints to app.py

```python
# Add near other API routes

@app.route('/api/newtab/data')
def newtab_data():
    """Get data for new tab."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM relevant_table LIMIT 100")
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
```

### Step 4: Add JavaScript (in unified.js or new file)

```javascript
async function loadNewTabData() {
    try {
        const response = await fetch('/api/newtab/data');
        const data = await response.json();
        document.getElementById('newtab-content').innerHTML =
            renderNewTabContent(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Hook into tab switching
document.querySelector('[data-tab="newtab"]')
    .addEventListener('click', loadNewTabData);
```

---

## 8. External Service Integration

### Visual Kanban (iframe)

```
SAG Tab → iframe src="http://192.168.132.223:8002"
                          │
                          ▼
          Visual Kanban Frontend (port 8002)
                          │
                          ▼ fetch('/tickets')
          Visual Kanban API (port 5000)
                          │
                          ▼ SQL query
          PostgreSQL duyuktv_tickets
```

### Grafana (iframe)

```html
<iframe src="http://192.168.132.223:3000/d/dashboard-id?kiosk"></iframe>
```

### Monitoring (port 5555)

Legacy Cherokee AI monitoring - being migrated to SAG native.

---

## 9. Authentication & Security

Currently SAG runs without authentication (internal network only).

**Future:** Add authentication via:
- Session-based login
- API key for programmatic access
- Integration with existing Cherokee identity

---

## 10. Deployment

### Starting SAG

```bash
# On redfin as dereadi
cd /ganuda/home/dereadi/sag_unified_interface
/ganuda/home/dereadi/cherokee_venv/bin/python3 app.py
```

### Process Management

```bash
# Find SAG process
pgrep -a -f "sag_unified_interface/app.py"

# Restart SAG
pkill -f "sag_unified_interface/app.py"
nohup /ganuda/home/dereadi/cherokee_venv/bin/python3 app.py >> /u/ganuda/logs/sag_app.log 2>&1 &
```

### Logs

- Main log: `/u/ganuda/logs/sag_app.log`
- App log: `/ganuda/home/dereadi/sag_unified_interface/app.log`

---

## 11. Common Integration Points

### Writing Events from External Systems

```python
import requests

def create_sag_event(title, description, tier='FYI'):
    """Create event in SAG from external system."""
    response = requests.post(
        'http://192.168.132.223:4000/api/events',
        json={
            'title': title,
            'description': description,
            'tier': tier,
            'source': 'external_system'
        }
    )
    return response.json()
```

### Reading Metrics

```python
import requests

def get_node_metrics():
    """Get current node metrics from SAG."""
    response = requests.get('http://192.168.132.223:4000/api/federation/nodes')
    return response.json()
```

---

## 12. Planned Enhancements

| Feature | Mission ID | Status |
|---------|------------|--------|
| Performance Graphs Tab | SAG-PERF-001 | Dispatched |
| Settings Control Tab | SAG-SETTINGS-001 | Dispatched |
| Command Console Tab | SAG-CONSOLE-002 | Dispatched |

---

**END OF KB-SAG-ARCHITECTURE**

Jr agents should reference this document before modifying any SAG components to understand the system context and integration points.
