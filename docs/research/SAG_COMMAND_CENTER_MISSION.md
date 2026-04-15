# COMMAND POST - IT JR MISSION: SAG COMMAND CENTER IMPLEMENTATION (Phase 1)

**DATE:** 2025-12-02 17:55 PST
**FROM:** Command Post (TPM)
**TO:** IT Jr 2 (PRIMARY), IT Jr 1 (SUPPORT), IT Jr 3 (DATABASE)
**PRIORITY:** HIGH
**MISSION ID:** SAG-CMDCENTER-001
**CHIEFS APPROVAL:** f6a0bcae-43b4-47d7-95b3-83729b57a853

---

## TPM ULTRATHINK SYNTHESIS - ARCHITECTURAL DECISIONS

After reviewing Chiefs approval, research findings (cPanel, Plesk, BinaryMoon),
and Strategic Roadmap requirements, the following decisions are made:

### 1. ARCHITECTURE: SIDEBAR APPROACH (not tab)
- cPanel and Plesk both use persistent sidebars for quick access
- Always visible = immediate value for monitoring critical alerts
- Collapsible to preserve screen real estate when needed

### 2. PRIORITY: PHASE 1 FIRST (Command Center Sidebar)
- Highest ROI with minimal backend changes
- Leverages existing thermal memory infrastructure
- Foundation for future phases (Chat, Settings)

### 3. TECHNOLOGY: LIGHTWEIGHT APPROACH
- Direct thermal memory queries via Flask API
- No LLM integration yet (avoid over-engineering)
- Simple keyword routing for action buttons
- JavaScript fetch() for real-time updates (polling every 30s)

### 4. TRIAD INTEGRATION: API ENDPOINTS
- New Flask routes in app.py for sidebar data
- Query thermal memory for alerts/missions
- Return JSON for JavaScript consumption

### 5. MOBILE: BASIC RESPONSIVE
- Sidebar collapses on mobile viewport
- Core functionality preserved
- Full redesign deferred to Phase 4

---

## MISSION OBJECTIVE

Add a collapsible Command Center sidebar to SAG Control Panel with:
- Active Alerts panel (bubbled from alert_state or thermal memory)
- Triad Status panel (CLI/Chiefs/Jrs activity)
- Quick Actions buttons (service restart, cache clear)
- Recent Activity feed (last 10 thermal memory entries)

---

## IT JR 2 DELIVERABLES (Frontend/CSS) - PRIMARY

### 1. CREATE: /ganuda/sag/static/css/sidebar.css
- Sidebar layout: 280px wide, full height, left side
- Collapsible: Toggle button, slide animation
- Dark/light theme support (use existing CSS variables)
- Sections: Alerts, Triad Status, Quick Actions, Activity

### 2. MODIFY: /home/dereadi/sag_unified_interface/templates/index.html
- Add sidebar HTML structure
- Add collapse toggle button (hamburger icon)
- Adjust main content area to accommodate sidebar
- Add sidebar.js script include

### 3. CREATE: /ganuda/sag/static/js/sidebar.js
- Fetch sidebar data from API endpoints
- Render alerts with severity colors (red/orange/yellow)
- Render Triad status indicators (green=active, gray=idle)
- Render Quick Action buttons with click handlers
- Auto-refresh every 30 seconds

### 4. SIDEBAR HTML STRUCTURE:
```html
<aside id="command-center" class="sidebar">
  <div class="sidebar-header">
    <h3>Command Center</h3>
    <button id="sidebar-toggle">☰</button>
  </div>

  <section class="alerts-panel">
    <h4>🚨 Active Alerts</h4>
    <div id="alerts-list"><!-- JS populated --></div>
  </section>

  <section class="triad-status">
    <h4>📡 Triad Status</h4>
    <div id="triad-list"><!-- JS populated --></div>
  </section>

  <section class="quick-actions">
    <h4>⚡ Quick Actions</h4>
    <button onclick="restartService('sag')">Restart SAG</button>
    <button onclick="clearCache()">Clear Cache</button>
    <button onclick="runHealthCheck()">Health Check</button>
  </section>

  <section class="recent-activity">
    <h4>📜 Recent Activity</h4>
    <div id="activity-feed"><!-- JS populated --></div>
  </section>
</aside>
```

---

## IT JR 1 DELIVERABLES (Backend/Integration) - SUPPORT

### 1. MODIFY: /home/dereadi/sag_unified_interface/app.py

Add Flask routes:

```python
@app.route("/api/sidebar/alerts")
def get_sidebar_alerts():
    """Return active alerts for sidebar."""
    # Query alert_state table (or thermal memory if not migrated yet)
    # Return JSON: [{severity, message, node, age}]

@app.route("/api/sidebar/triad-status")
def get_triad_status():
    """Return Triad activity status."""
    # Query thermal memory for recent Triad activity
    # Return JSON: [{triad, last_activity, status}]

@app.route("/api/sidebar/activity")
def get_recent_activity():
    """Return last 10 thermal memory entries."""
    # Query thermal memory, use LEADING SEARCH (KB-DB-001)
    # Return JSON: [{source, summary, time}]

@app.route("/api/action/restart/<service>", methods=["POST"])
def restart_service(service):
    """Trigger service restart via systemctl."""
    # Whitelist allowed services
    # Return success/failure

@app.route("/api/action/health-check", methods=["POST"])
def run_health_check():
    """Trigger health check and return results."""
```

### 2. IMPORTANT: Use leading search patterns per KB-DB-001:
- `LIKE 'COMMAND POST -%'` for missions
- `LIKE 'IT TRIAD DECISION -%'` for decisions
- `LIKE 'IT JR -%'` for Jr activity
- **NEVER use ILIKE '%PATTERN%' on thermal memory!**

---

## IT JR 3 DELIVERABLES (Database) - SUPPORT

### 1. ENSURE: alert_state table exists (per THERMAL_MEMORY_RESTRUCTURE_PLAN.md)
- If not created yet, create it now
- This is the source for sidebar alerts

### 2. CREATE: View for sidebar activity (optional optimization):
```sql
CREATE OR REPLACE VIEW v_sidebar_activity AS
SELECT id, LEFT(content, 100) as summary, source_triad, created_at
FROM triad_shared_memories
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND source_triad IN ('command_post', 'it_triad', 'it_jr', 'trading_triad')
ORDER BY created_at DESC
LIMIT 20;
```

### 3. VERIFY: Indexes exist for sidebar queries (KB-DB-001 compliance)

---

## FILE LOCATIONS

**SAG Application (redfin):** /home/dereadi/sag_unified_interface/
- app.py (Flask backend)
- templates/index.html (main template)
- static/css/ (stylesheets)
- static/js/ (JavaScript)

**New files to create:**
- /ganuda/sag/static/css/sidebar.css
- /ganuda/sag/static/js/sidebar.js

**Reference documents:**
- /ganuda/KB_POSTGRESQL_LEADING_SEARCH_PATTERN.md (KB-DB-001)
- /ganuda/THERMAL_MEMORY_RESTRUCTURE_PLAN.md
- /ganuda/CHEROKEE_AI_FEDERATION_STRATEGIC_ROADMAP.md

---

## SUCCESS CRITERIA

- [ ] Sidebar visible on left side of SAG
- [ ] Collapse/expand toggle works
- [ ] Alerts panel shows current critical/warning alerts
- [ ] Triad Status shows last activity time per Triad
- [ ] Quick Actions buttons trigger API calls
- [ ] Recent Activity shows last 10 thermal entries
- [ ] Dark/Light theme toggle affects sidebar
- [ ] Mobile: Sidebar collapses automatically on small viewport
- [ ] No ILIKE queries on thermal memory (performance)

---

## TIMELINE

- IT Jr 2: 4-6 hours (HTML/CSS/JS)
- IT Jr 1: 2-3 hours (Flask routes)
- IT Jr 3: 1 hour (verify tables/indexes)

**Target:** Complete by 2025-12-04

---

## REPORT PROGRESS

Write progress updates to thermal memory with:
- source_triad: "it_jr"
- temperature: 0.65
- Include: What was completed, blockers, next steps

**Temperature:** 0.85 (High Priority - User Requested Feature)
