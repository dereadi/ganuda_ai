# JR INSTRUCTIONS: SAG UI Tab Improvements
## Priority: 3 (Medium)
## December 17, 2025

### OVERVIEW

Improve the SAG Control Room UI based on Tribe Council feedback. Focus on quick wins that enhance usability without major restructuring.

**Tribe Feedback Summary:**
- Redfin Elder: Node Health dashboard, Alert severity filtering
- Meta Jr: Cross-tab integration, Event-driven architecture
- TPM-Mac: Simplify navigation, Enhance search, Better Tribe integration

---

## TASK 1: Enhance Tribe Tab with Real Council Activity

The Tribe tab is underutilized. Show real council votes and resonance data.

**File:** `/home/dereadi/sag_unified_interface/static/js/control-room.js`

**Find `function loadTribeView()` and replace with:**

```javascript
function loadTribeView() {
    var container = document.getElementById("tribe-content");
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading tribe data...</div>';

    // Fetch multiple endpoints in parallel
    Promise.all([
        fetch("/api/tribe/summary").then(r => r.json()).catch(() => ({})),
        fetch("/api/tribe/council-votes").then(r => r.json()).catch(() => ({votes: []})),
        fetch("/api/tribe/specialists").then(r => r.json()).catch(() => ({specialists: []}))
    ]).then(function([summary, votes, specialists]) {
        var html = '<div class="tribe-dashboard">';

        // Summary Cards
        html += '<div class="tribe-stats">';
        html += '<div class="stat-card"><h3>Active Specialists</h3><div class="stat-value">' + (summary.active_specialists || 7) + '</div></div>';
        html += '<div class="stat-card"><h3>Votes Today</h3><div class="stat-value">' + (summary.votes_today || 0) + '</div></div>';
        html += '<div class="stat-card"><h3>Pending TPM Review</h3><div class="stat-value">' + (summary.pending_tpm || 0) + '</div></div>';
        html += '<div class="stat-card"><h3>Avg Confidence</h3><div class="stat-value">' + ((summary.avg_confidence || 0.75) * 100).toFixed(0) + '%</div></div>';
        html += '</div>';

        // Recent Council Votes
        html += '<div class="tribe-section"><h3>Recent Council Votes</h3>';
        if (votes.votes && votes.votes.length > 0) {
            html += '<div class="council-votes">';
            votes.votes.slice(0, 10).forEach(function(vote) {
                var confidenceClass = vote.confidence > 0.8 ? 'high' : vote.confidence > 0.6 ? 'medium' : 'low';
                html += '<div class="vote-card">';
                html += '<div class="vote-question">' + escapeHtml(vote.question || '').substring(0, 100) + '...</div>';
                html += '<div class="vote-meta">';
                html += '<span class="vote-confidence ' + confidenceClass + '">' + ((vote.confidence || 0) * 100).toFixed(0) + '% confident</span>';
                html += '<span class="vote-status ' + (vote.tpm_vote || 'pending') + '">' + (vote.tpm_vote || 'pending') + '</span>';
                html += '<span class="vote-time">' + formatTimeAgo(vote.timestamp) + '</span>';
                html += '</div></div>';
            });
            html += '</div>';
        } else {
            html += '<p class="no-data">No recent council votes</p>';
        }
        html += '</div>';

        // Specialist Status
        html += '<div class="tribe-section"><h3>7-Specialist Council</h3>';
        html += '<div class="specialist-grid">';
        var defaultSpecialists = [
            {name: 'Crawdad', role: 'Security', icon: '🦀'},
            {name: 'Gecko', role: 'Performance', icon: '🦎'},
            {name: 'Turtle', role: 'Stability', icon: '🐢'},
            {name: 'Hummingbird', role: 'UX', icon: '🐦'},
            {name: 'Owl', role: 'Strategy', icon: '🦉'},
            {name: 'Bear', role: 'Resources', icon: '🐻'},
            {name: 'Eagle', role: 'Vision', icon: '🦅'}
        ];
        defaultSpecialists.forEach(function(spec) {
            html += '<div class="specialist-card">';
            html += '<span class="specialist-icon">' + spec.icon + '</span>';
            html += '<span class="specialist-name">' + spec.name + '</span>';
            html += '<span class="specialist-role">' + spec.role + '</span>';
            html += '</div>';
        });
        html += '</div></div>';

        html += '</div>';
        container.innerHTML = html;
    });
}

function formatTimeAgo(timestamp) {
    if (!timestamp) return '';
    var date = new Date(timestamp);
    var now = new Date();
    var diff = Math.floor((now - date) / 1000);
    if (diff < 60) return diff + 's ago';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
}
```

---

## TASK 2: Add Alert Severity Filtering

**File:** `/home/dereadi/sag_unified_interface/static/js/control-room.js`

**Find `function loadAlertsView()` and add filtering UI:**

```javascript
function loadAlertsView() {
    var container = document.getElementById("alerts-list-full");
    if (!container) return;

    // Add filter controls if not present
    var filterDiv = document.getElementById("alerts-filters");
    if (!filterDiv) {
        var parentDiv = container.parentElement;
        var filterHtml = '<div id="alerts-filters" class="filter-controls">';
        filterHtml += '<label><input type="checkbox" id="filter-critical" checked> Critical</label>';
        filterHtml += '<label><input type="checkbox" id="filter-warning" checked> Warning</label>';
        filterHtml += '<label><input type="checkbox" id="filter-info" checked> Info</label>';
        filterHtml += '<label><input type="checkbox" id="filter-dismissed"> Show Dismissed</label>';
        filterHtml += '</div>';
        parentDiv.insertAdjacentHTML('afterbegin', filterHtml);

        // Add filter event listeners
        ['critical', 'warning', 'info', 'dismissed'].forEach(function(type) {
            document.getElementById('filter-' + type).addEventListener('change', loadAlertsView);
        });
    }

    // Get filter states
    var showCritical = document.getElementById('filter-critical').checked;
    var showWarning = document.getElementById('filter-warning').checked;
    var showInfo = document.getElementById('filter-info').checked;
    var showDismissed = document.getElementById('filter-dismissed').checked;

    fetch("/api/events?include_dismissed=" + showDismissed)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var events = (data.events || []).filter(function(e) {
                var tier = (e.tier || 'INFO').toUpperCase();
                if (tier === 'CRITICAL' && !showCritical) return false;
                if (tier === 'WARNING' && !showWarning) return false;
                if ((tier === 'INFO' || tier === 'FYI') && !showInfo) return false;
                return true;
            });

            var html = '<div class="alerts-summary">';
            var critCount = events.filter(e => (e.tier || '').toUpperCase() === 'CRITICAL').length;
            var warnCount = events.filter(e => (e.tier || '').toUpperCase() === 'WARNING').length;
            var infoCount = events.filter(e => ['INFO', 'FYI'].includes((e.tier || '').toUpperCase())).length;

            html += '<span class="alert-count critical">' + critCount + ' Critical</span>';
            html += '<span class="alert-count warning">' + warnCount + ' Warning</span>';
            html += '<span class="alert-count info">' + infoCount + ' Info</span>';
            html += '</div>';

            html += '<div class="alerts-list">';
            events.forEach(function(event) {
                var tierClass = (event.tier || 'info').toLowerCase();
                html += '<div class="alert-item ' + tierClass + '">';
                html += '<span class="alert-tier">' + (event.tier || 'INFO') + '</span>';
                html += '<span class="alert-title">' + escapeHtml(event.title || event.message || '') + '</span>';
                html += '<span class="alert-time">' + formatTimeAgo(event.created_at) + '</span>';
                html += '</div>';
            });
            html += '</div>';

            container.innerHTML = html;
        });
}
```

---

## TASK 3: Add Node Health At-a-Glance to Home

**File:** `/home/dereadi/sag_unified_interface/static/js/control-room.js`

**Add after the systems-grid section in home view:**

```javascript
// Add to the home view rendering, after systems grid
function renderNodeHealthSummary(nodes) {
    var html = '<div class="node-health-summary">';
    html += '<h3>Node Health</h3>';
    html += '<div class="health-grid">';

    nodes.forEach(function(node) {
        var healthClass = node.status === 'online' ? 'healthy' :
                         node.status === 'degraded' ? 'degraded' : 'offline';
        var cpuPercent = node.cpu_usage || 0;
        var ramPercent = node.memory_usage || 0;

        html += '<div class="health-node ' + healthClass + '">';
        html += '<div class="node-name">' + (node.name || node.hostname) + '</div>';
        html += '<div class="node-metrics">';
        html += '<div class="metric"><span class="label">CPU</span><div class="bar"><div class="fill" style="width:' + cpuPercent + '%"></div></div><span class="value">' + cpuPercent + '%</span></div>';
        html += '<div class="metric"><span class="label">RAM</span><div class="bar"><div class="fill" style="width:' + ramPercent + '%"></div></div><span class="value">' + ramPercent + '%</span></div>';
        html += '</div>';
        html += '</div>';
    });

    html += '</div></div>';
    return html;
}
```

---

## TASK 4: CSS Styles for New Components

**File:** `/home/dereadi/sag_unified_interface/static/css/unified.css`

**Add at the end:**

```css
/* Tribe Dashboard */
.tribe-dashboard {
    padding: 20px;
}

.tribe-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.tribe-stats .stat-card {
    background: var(--color-surface);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}

.tribe-stats .stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--color-accent);
}

.tribe-section {
    margin-bottom: 24px;
}

.tribe-section h3 {
    margin-bottom: 12px;
    color: var(--color-text);
}

.council-votes {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.vote-card {
    background: var(--color-surface);
    border-radius: 6px;
    padding: 12px;
    border-left: 3px solid var(--color-accent);
}

.vote-question {
    font-weight: 500;
    margin-bottom: 8px;
}

.vote-meta {
    display: flex;
    gap: 12px;
    font-size: 0.85rem;
    color: var(--color-text-muted);
}

.vote-confidence.high { color: #22c55e; }
.vote-confidence.medium { color: #eab308; }
.vote-confidence.low { color: #ef4444; }

.vote-status.approved { color: #22c55e; }
.vote-status.rejected { color: #ef4444; }
.vote-status.pending { color: #eab308; }

.specialist-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
}

.specialist-card {
    background: var(--color-surface);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.specialist-icon {
    font-size: 2rem;
    margin-bottom: 8px;
}

.specialist-name {
    font-weight: 600;
}

.specialist-role {
    font-size: 0.8rem;
    color: var(--color-text-muted);
}

/* Alert Filters */
.filter-controls {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    padding: 12px;
    background: var(--color-surface);
    border-radius: 6px;
}

.filter-controls label {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
}

.alerts-summary {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.alert-count {
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 500;
}

.alert-count.critical { background: #fee2e2; color: #dc2626; }
.alert-count.warning { background: #fef3c7; color: #d97706; }
.alert-count.info { background: #dbeafe; color: #2563eb; }

.alerts-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.alert-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: var(--color-surface);
    border-radius: 6px;
    border-left: 3px solid;
}

.alert-item.critical { border-color: #dc2626; }
.alert-item.warning { border-color: #d97706; }
.alert-item.info { border-color: #2563eb; }

.alert-tier {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
}

.alert-item.critical .alert-tier { background: #fee2e2; color: #dc2626; }
.alert-item.warning .alert-tier { background: #fef3c7; color: #d97706; }
.alert-item.info .alert-tier { background: #dbeafe; color: #2563eb; }

.alert-title {
    flex: 1;
}

.alert-time {
    color: var(--color-text-muted);
    font-size: 0.85rem;
}

/* Node Health Summary */
.node-health-summary {
    margin-top: 24px;
}

.health-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
}

.health-node {
    background: var(--color-surface);
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid;
}

.health-node.healthy { border-color: #22c55e; }
.health-node.degraded { border-color: #eab308; }
.health-node.offline { border-color: #ef4444; }

.health-node .node-name {
    font-weight: 600;
    margin-bottom: 12px;
}

.health-node .metric {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}

.health-node .metric .label {
    width: 40px;
    font-size: 0.8rem;
    color: var(--color-text-muted);
}

.health-node .metric .bar {
    flex: 1;
    height: 6px;
    background: var(--color-bg);
    border-radius: 3px;
    overflow: hidden;
}

.health-node .metric .bar .fill {
    height: 100%;
    background: var(--color-accent);
    transition: width 0.3s;
}

.health-node .metric .value {
    width: 40px;
    text-align: right;
    font-size: 0.85rem;
}

.no-data {
    color: var(--color-text-muted);
    font-style: italic;
}
```

---

## TASK 5: Add /api/tribe/council-votes Endpoint

**File:** `/home/dereadi/sag_unified_interface/app.py`

**Add this route (before the `if __name__` block):**

```python
@app.route('/api/tribe/council-votes')
def get_council_votes():
    """Get recent council votes from audit log"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                audit_hash,
                question,
                confidence,
                tpm_vote,
                created_at as timestamp
            FROM council_audit_log
            ORDER BY created_at DESC
            LIMIT 20
        """)
        votes = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"votes": votes})
    except Exception as e:
        return jsonify({"votes": [], "error": str(e)})
```

---

## SUCCESS CRITERIA

1. **Tribe tab** shows real council votes, specialist status, and summary stats
2. **Alerts tab** has Critical/Warning/Info filter checkboxes
3. **Home view** shows node health bars for CPU/RAM
4. **CSS** renders cleanly without breaking existing styles
5. **API endpoint** returns council votes from database

---

## TESTING

```bash
# Test tribe API
curl http://localhost:4000/api/tribe/council-votes

# Test alerts with filter
curl "http://localhost:4000/api/events?include_dismissed=true"

# Visual test - load each tab in browser
open http://192.168.132.223:4000/
```

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
