# Jr Task: Integrate SAG Flask with Django API Backend

**Task ID:** task-sag-django-integration-001
**Priority:** P2
**Node:** redfin
**Created:** December 21, 2025
**Requested By:** TPM
**Council Vote:** 8ce23768823684a4 (79.5% confidence, PROCEED)

---

## Context

The Council has voted to integrate Django 6.0 (port 4001) with SAG Flask (port 4000) using **Option B: Django as API Backend**. SAG remains the primary ITSM frontend while Django provides REST API endpoints for thermal memory and tribe data.

### Current Architecture

| Service | Port | Database | Memories |
|---------|------|----------|----------|
| SAG Flask | 4000 | triad_federation | 10,664 (triad_shared_memories) |
| Django | 4001 | zammad_production | 6,693 (thermal_memory_archive) |

### Council Reasoning

- SAG has more memories and is established - don't disrupt it
- Django APIs allow gradual integration
- Databases remain separate - no risky migration
- Seven Generations: sustainable, incremental approach

---

## Django API Endpoints (Already Available)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/thermal/hot?limit=N` | GET | Top N hottest memories |
| `/api/thermal/search?q=QUERY` | GET | Search memories by keyword |
| `/api/thermal/explain` | GET | Plain language explanation of thermal memory |
| `/api/tribe` | GET | Active tribe members (specialists + Jrs) |

**Base URL:** `http://192.168.132.223:4001`

---

## Implementation Steps

### Step 1: Create Django API Client in SAG

Create `/ganuda/home/dereadi/sag_unified_interface/django_api_client.py`:

```python
#!/usr/bin/env python3
"""
Django API Client - Bridge SAG Flask to Django REST API

Provides access to thermal_memory_archive and tribe data from Django.
For Seven Generations - Cherokee AI Federation
"""

import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger('DjangoAPIClient')

DJANGO_BASE_URL = "http://127.0.0.1:4001"  # localhost on redfin
TIMEOUT = 10  # seconds


class DjangoAPIClient:
    """Client for Django REST API endpoints"""

    def __init__(self, base_url: str = DJANGO_BASE_URL):
        self.base_url = base_url

    def get_hot_memories(self, limit: int = 10) -> List[Dict]:
        """
        Get hottest memories from thermal_memory_archive

        Returns list of dicts with: hash, content, temperature, created
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/thermal/hot",
                params={"limit": limit},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Django API error (hot): {e}")
            return []

    def search_memories(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search thermal memories by keyword

        Returns list of matching memories
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/thermal/search",
                params={"q": query, "limit": limit},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Django API error (search): {e}")
            return []

    def get_tribe_status(self) -> Dict:
        """
        Get active tribe members

        Returns dict with specialists and jr_agents
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tribe",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Django API error (tribe): {e}")
            return {"specialists": [], "jr_agents": [], "error": str(e)}

    def get_thermal_explanation(self) -> str:
        """Get plain language explanation of thermal memory"""
        try:
            response = requests.get(
                f"{self.base_url}/api/thermal/explain",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get("explanation", "Thermal memory explanation unavailable")
        except requests.RequestException as e:
            logger.error(f"Django API error (explain): {e}")
            return f"Error fetching explanation: {e}"

    def health_check(self) -> bool:
        """Check if Django API is available"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/",
                timeout=5,
                allow_redirects=False
            )
            return response.status_code in [200, 302]
        except:
            return False
```

### Step 2: Add Django Tab to SAG Interface

Update `/ganuda/home/dereadi/sag_unified_interface/app.py` to add a new tab.

Find the tab configuration section and add:

```python
# In the TABS configuration (around line 80-100)
TABS = [
    {"id": "events", "name": "Events", "icon": "bell"},
    {"id": "kanban", "name": "Kanban", "icon": "columns"},
    {"id": "monitoring", "name": "Monitoring", "icon": "activity"},
    {"id": "grafana", "name": "Grafana", "icon": "bar-chart"},
    {"id": "email", "name": "Email", "icon": "mail"},
    {"id": "django", "name": "Council", "icon": "users"},  # NEW TAB
]
```

### Step 3: Add Django Routes to SAG

Add these routes to `app.py`:

```python
from django_api_client import DjangoAPIClient

django_client = DjangoAPIClient()

@app.route('/api/django/hot')
def django_hot_memories():
    """Proxy to Django hot memories API"""
    limit = request.args.get('limit', 10, type=int)
    memories = django_client.get_hot_memories(limit)
    return jsonify(memories)

@app.route('/api/django/search')
def django_search():
    """Proxy to Django search API"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    memories = django_client.search_memories(query, limit)
    return jsonify(memories)

@app.route('/api/django/tribe')
def django_tribe():
    """Proxy to Django tribe status API"""
    tribe = django_client.get_tribe_status()
    return jsonify(tribe)

@app.route('/api/django/health')
def django_health():
    """Check Django API health"""
    is_healthy = django_client.health_check()
    return jsonify({
        "django_api": "healthy" if is_healthy else "unavailable",
        "url": "http://192.168.132.223:4001"
    })
```

### Step 4: Create Django Tab Template

Create `/ganuda/home/dereadi/sag_unified_interface/templates/tabs/django_tab.html`:

```html
<div id="django-tab" class="tab-content">
    <div class="django-header">
        <h2>Cherokee AI Council - Django Admin</h2>
        <div class="django-status">
            <span id="django-health-status">Checking...</span>
            <a href="http://192.168.132.223:4001/admin/" target="_blank" class="btn btn-sm">
                Open Admin
            </a>
        </div>
    </div>

    <div class="django-sections">
        <!-- Hot Memories Section -->
        <div class="section">
            <h3>🔥 Hottest Tribal Memories</h3>
            <div id="hot-memories-list" class="memory-list">
                Loading...
            </div>
            <button onclick="loadHotMemories()" class="btn">Refresh</button>
        </div>

        <!-- Memory Search -->
        <div class="section">
            <h3>🔍 Search Thermal Memory</h3>
            <div class="search-box">
                <input type="text" id="memory-search-input" placeholder="Search memories...">
                <button onclick="searchMemories()" class="btn">Search</button>
            </div>
            <div id="memory-search-results" class="memory-list"></div>
        </div>

        <!-- Tribe Status -->
        <div class="section">
            <h3>👥 Active Tribe Members</h3>
            <div id="tribe-status" class="tribe-grid">
                Loading...
            </div>
        </div>
    </div>
</div>

<script>
async function loadHotMemories() {
    const container = document.getElementById('hot-memories-list');
    try {
        const response = await fetch('/api/django/hot?limit=10');
        const memories = await response.json();

        if (memories.length === 0) {
            container.innerHTML = '<p>No memories found</p>';
            return;
        }

        container.innerHTML = memories.map(m => `
            <div class="memory-card temp-${getTempClass(m.temperature)}">
                <div class="memory-temp">${m.temperature.toFixed(0)}°</div>
                <div class="memory-content">${escapeHtml(m.content.substring(0, 200))}...</div>
                <div class="memory-date">${new Date(m.created).toLocaleDateString()}</div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="error">Error loading memories: ${e}</p>`;
    }
}

async function searchMemories() {
    const query = document.getElementById('memory-search-input').value;
    const container = document.getElementById('memory-search-results');

    if (!query) return;

    container.innerHTML = 'Searching...';

    try {
        const response = await fetch(`/api/django/search?q=${encodeURIComponent(query)}`);
        const memories = await response.json();

        if (memories.length === 0) {
            container.innerHTML = '<p>No matches found</p>';
            return;
        }

        container.innerHTML = memories.map(m => `
            <div class="memory-card">
                <div class="memory-temp">${m.temperature.toFixed(0)}°</div>
                <div class="memory-content">${escapeHtml(m.content.substring(0, 200))}...</div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="error">Error: ${e}</p>`;
    }
}

async function loadTribeStatus() {
    const container = document.getElementById('tribe-status');
    try {
        const response = await fetch('/api/django/tribe');
        const tribe = await response.json();

        let html = '<div class="specialists"><h4>7 Specialists</h4>';
        tribe.specialists.forEach(s => {
            html += `<span class="specialist-badge">${s.name}</span>`;
        });
        html += '</div>';

        html += '<div class="jr-agents"><h4>Jr Agents</h4>';
        if (tribe.jr_agents && tribe.jr_agents.length > 0) {
            tribe.jr_agents.forEach(jr => {
                html += `<span class="jr-badge">${jr.agent_id} (${jr.node_name})</span>`;
            });
        } else {
            html += '<span>No active Jr agents</span>';
        }
        html += '</div>';

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p class="error">Error: ${e}</p>`;
    }
}

async function checkDjangoHealth() {
    const status = document.getElementById('django-health-status');
    try {
        const response = await fetch('/api/django/health');
        const data = await response.json();
        status.innerHTML = data.django_api === 'healthy'
            ? '✅ Django Online'
            : '❌ Django Offline';
        status.className = data.django_api === 'healthy' ? 'healthy' : 'unhealthy';
    } catch (e) {
        status.innerHTML = '❌ Django Unreachable';
        status.className = 'unhealthy';
    }
}

function getTempClass(temp) {
    if (temp >= 90) return 'hot';
    if (temp >= 50) return 'warm';
    if (temp >= 10) return 'cool';
    return 'cold';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load on tab activation
document.addEventListener('DOMContentLoaded', () => {
    checkDjangoHealth();
    loadHotMemories();
    loadTribeStatus();
});
</script>

<style>
.django-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
}
.django-sections {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}
.section {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 8px;
}
.memory-list {
    max-height: 400px;
    overflow-y: auto;
}
.memory-card {
    background: white;
    padding: 10px;
    margin: 8px 0;
    border-radius: 4px;
    border-left: 4px solid #ccc;
}
.memory-card.temp-hot { border-left-color: #e74c3c; }
.memory-card.temp-warm { border-left-color: #f39c12; }
.memory-card.temp-cool { border-left-color: #3498db; }
.memory-card.temp-cold { border-left-color: #95a5a6; }
.memory-temp {
    font-weight: bold;
    font-size: 1.2em;
}
.memory-content {
    margin: 5px 0;
    color: #333;
}
.memory-date {
    font-size: 0.8em;
    color: #888;
}
.search-box {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}
.search-box input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}
.specialist-badge, .jr-badge {
    display: inline-block;
    padding: 4px 8px;
    margin: 2px;
    border-radius: 4px;
    font-size: 0.9em;
}
.specialist-badge { background: #3498db; color: white; }
.jr-badge { background: #27ae60; color: white; }
.healthy { color: #27ae60; }
.unhealthy { color: #e74c3c; }
.btn {
    padding: 8px 16px;
    background: #2c3e50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
.btn:hover { background: #34495e; }
</style>
```

### Step 5: Include Tab in Main Template

In `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`, add:

```html
<!-- In the tab buttons section -->
<button class="tab-btn" data-tab="django">
    <i class="icon-users"></i> Council
</button>

<!-- In the tab contents section -->
{% include 'tabs/django_tab.html' %}
```

---

## Testing

### 1. Verify Django API is accessible from SAG

```bash
# On redfin
curl -s http://127.0.0.1:4001/api/thermal/hot?limit=3 | jq .
```

### 2. Test the new SAG endpoints

```bash
# After updating app.py
curl -s http://192.168.132.223:4000/api/django/hot | jq .
curl -s http://192.168.132.223:4000/api/django/health | jq .
```

### 3. Restart SAG Flask

```bash
# Find and restart SAG
pkill -f "python3 app.py"
cd /ganuda/home/dereadi/sag_unified_interface
source venv/bin/activate
nohup python3 app.py > /tmp/sag.log 2>&1 &
```

### 4. Verify in browser

Open http://192.168.132.223:4000 and check:
- New "Council" tab appears
- Hot memories load
- Search works
- Tribe status shows

---

## Database Bridging (Future Phase)

Once stable, consider creating a unified view:

```sql
-- On bluefin, create a combined memory view
CREATE VIEW unified_thermal_memories AS
SELECT
    memory_hash as id,
    original_content as content,
    temperature_score as temperature,
    'zammad' as source_db,
    created_at
FROM thermal_memory_archive

UNION ALL

SELECT
    id::text,
    content,
    temperature,
    'triad' as source_db,
    created_at
FROM dblink('dbname=triad_federation',
    'SELECT id, content, temperature, created_at FROM triad_shared_memories')
AS t(id int, content text, temperature float, created_at timestamp);
```

This is **Phase 2** - only after SAG/Django integration is stable.

---

## Success Criteria

1. ✅ Django API client created in SAG directory
2. ✅ New "Council" tab visible in SAG interface
3. ✅ Hot memories display from Django API
4. ✅ Memory search works
5. ✅ Tribe status shows specialists and Jrs
6. ✅ Health check indicates Django status
7. ✅ No errors in SAG logs

---

## Rollback Plan

If integration causes issues:

```bash
# Restore SAG app.py from backup
cp /ganuda/home/dereadi/sag_unified_interface/app.py.backup /ganuda/home/dereadi/sag_unified_interface/app.py

# Restart SAG
pkill -f "python3 app.py"
cd /ganuda/home/dereadi/sag_unified_interface && nohup python3 app.py > /tmp/sag.log 2>&1 &
```

The Django service can continue running independently.

---

*For Seven Generations - Cherokee AI Federation*

**Council Vote Reference:** 8ce23768823684a4
