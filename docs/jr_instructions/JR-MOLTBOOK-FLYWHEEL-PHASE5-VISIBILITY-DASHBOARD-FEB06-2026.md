# Jr Instruction: Moltbook Flywheel Visibility Dashboard

**Task ID:** MOLTBOOK-FLYWHEEL-P5
**Jr Type:** Full Stack Engineer Jr.
**Priority:** P1
**Category:** SAG UI Enhancement / Flywheel Integration
**Phase:** 5 of Research Jr + Moltbook Flywheel Integration

---

## Objective

Add a flywheel visibility widget to the SAG UI dashboard that provides real-time monitoring of the Moltbook content pipeline, including scan metrics, research dispatch status, council approvals, and budget tracking.

---

## Context

The Moltbook Flywheel automates content creation:
1. Research Jr scans for topics
2. Topics trigger research dispatches
3. Research results become draft responses
4. Council reviews and approves
5. Approved content posts to Moltbook

This dashboard widget provides visibility into the entire pipeline with budget controls to prevent runaway costs.

---

## Deliverables

### 1. API Endpoint

Create file: `/ganuda/sag/routes/flywheel_routes.py`

```python
from flask import Blueprint, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any

flywheel_bp = Blueprint('flywheel', __name__, url_prefix='/api/flywheel')

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

DAILY_BUDGET = 10.00  # $10/day budget limit

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@flywheel_bp.route('/status', methods=['GET'])
def get_flywheel_status() -> Dict[str, Any]:
    """
    Get current flywheel pipeline status and metrics.

    Returns comprehensive dashboard data including:
    - Scan count for today
    - Topics detected
    - Research dispatched
    - Responses drafted
    - Council approved
    - Posted count
    - Budget usage
    - Last post info
    - Pending items
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())

        # Scan count (flywheel_scans from thermal_memory)
        cur.execute("""
            SELECT COUNT(*) as count
            FROM thermal_memory_archive
            WHERE memory_type = 'flywheel_scan'
            AND created_at >= %s
        """, (today_start,))
        scans_today = cur.fetchone()['count']

        # Topics detected (from scans with topics)
        cur.execute("""
            SELECT COUNT(*) as count
            FROM thermal_memory_archive
            WHERE memory_type = 'flywheel_topic_detected'
            AND created_at >= %s
        """, (today_start,))
        topics_detected = cur.fetchone()['count']

        # Research dispatched
        cur.execute("""
            SELECT COUNT(*) as count
            FROM thermal_memory_archive
            WHERE memory_type = 'flywheel_research_dispatched'
            AND created_at >= %s
        """, (today_start,))
        research_dispatched = cur.fetchone()['count']

        # Research cost calculation
        cur.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN original_content ~ 'cost[:\s]+\$?([0-9.]+)'
                    THEN (regexp_match(original_content, 'cost[:\s]+\$?([0-9.]+)'))[1]::numeric
                    ELSE 0.0
                END
            ), 0.0) as total_cost
            FROM thermal_memory_archive
            WHERE memory_type = 'flywheel_research_cost'
            AND created_at >= %s
        """, (today_start,))
        research_cost = float(cur.fetchone()['total_cost'])

        # Responses drafted (moltbook_post_queue count)
        cur.execute("""
            SELECT COUNT(*) as count
            FROM moltbook_post_queue
            WHERE status = 'drafted'
            AND created_at >= %s
        """, (today_start,))
        responses_drafted = cur.fetchone()['count']

        # Council approved (from council_votes)
        cur.execute("""
            SELECT COUNT(DISTINCT post_id) as count
            FROM council_votes
            WHERE vote = 'approve'
            AND voted_at >= %s
        """, (today_start,))
        council_approved = cur.fetchone()['count']

        # Posted count
        cur.execute("""
            SELECT COUNT(*) as count
            FROM moltbook_post_queue
            WHERE status = 'posted'
            AND posted_at >= %s
        """, (today_start,))
        posted_count = cur.fetchone()['count']

        # Last post info
        cur.execute("""
            SELECT id, title, status, posted_at, platform
            FROM moltbook_post_queue
            WHERE status = 'posted'
            ORDER BY posted_at DESC
            LIMIT 1
        """)
        last_post_row = cur.fetchone()
        last_post = None
        if last_post_row:
            last_post = {
                'id': last_post_row['id'],
                'title': last_post_row['title'],
                'status': last_post_row['status'],
                'posted_at': last_post_row['posted_at'].isoformat() if last_post_row['posted_at'] else None,
                'platform': last_post_row['platform']
            }

        # Pending items (drafted, awaiting approval)
        cur.execute("""
            SELECT id, title, status, created_at
            FROM moltbook_post_queue
            WHERE status IN ('drafted', 'pending_approval', 'approved')
            ORDER BY created_at DESC
            LIMIT 10
        """)
        pending_items = []
        for row in cur.fetchall():
            pending_items.append({
                'id': row['id'],
                'title': row['title'],
                'status': row['status'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None
            })

        cur.close()
        conn.close()

        # Calculate budget percentage
        budget_percentage = (research_cost / DAILY_BUDGET) * 100
        budget_alert = budget_percentage >= 80

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'date': today.isoformat(),
            'metrics': {
                'scans_today': scans_today,
                'topics_detected': topics_detected,
                'research_dispatched': research_dispatched,
                'responses_drafted': responses_drafted,
                'council_approved': council_approved,
                'posted_count': posted_count
            },
            'budget': {
                'spent': research_cost,
                'limit': DAILY_BUDGET,
                'percentage': round(budget_percentage, 1),
                'alert': budget_alert,
                'remaining': round(DAILY_BUDGET - research_cost, 2)
            },
            'last_post': last_post,
            'pending_items': pending_items,
            'pipeline_health': 'healthy' if not budget_alert else 'budget_warning'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@flywheel_bp.route('/budget/alert', methods=['GET'])
def check_budget_alert() -> Dict[str, Any]:
    """
    Quick check for budget alert status.
    Returns simple alert boolean for fast polling.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        today_start = datetime.combine(datetime.now().date(), datetime.min.time())

        cur.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN original_content ~ 'cost[:\s]+\$?([0-9.]+)'
                    THEN (regexp_match(original_content, 'cost[:\s]+\$?([0-9.]+)'))[1]::numeric
                    ELSE 0.0
                END
            ), 0.0) as total_cost
            FROM thermal_memory_archive
            WHERE memory_type = 'flywheel_research_cost'
            AND created_at >= %s
        """, (today_start,))

        research_cost = float(cur.fetchone()['total_cost'])
        cur.close()
        conn.close()

        return jsonify({
            'alert': research_cost >= (DAILY_BUDGET * 0.8),
            'spent': research_cost,
            'limit': DAILY_BUDGET
        })

    except Exception as e:
        return jsonify({'alert': False, 'error': str(e)}), 500
```

---

### 2. Dashboard Template

Create file: `/ganuda/sag/templates/flywheel_dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moltbook Flywheel Dashboard</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent-green: #00d9a5;
            --accent-blue: #4f8cff;
            --accent-yellow: #ffc107;
            --accent-red: #ff4757;
            --accent-purple: #a855f7;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--bg-card);
        }

        .dashboard-header h1 {
            font-size: 24px;
            font-weight: 600;
        }

        .refresh-info {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .metric-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }

        .metric-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .metric-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-card.scans .metric-value { color: var(--accent-blue); }
        .metric-card.topics .metric-value { color: var(--accent-purple); }
        .metric-card.research .metric-value { color: var(--accent-yellow); }
        .metric-card.drafted .metric-value { color: var(--text-primary); }
        .metric-card.approved .metric-value { color: var(--accent-green); }
        .metric-card.posted .metric-value { color: var(--accent-green); }

        .budget-section {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .budget-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .budget-header h2 {
            font-size: 18px;
            font-weight: 600;
        }

        .budget-amount {
            font-size: 24px;
            font-weight: 700;
        }

        .budget-bar-container {
            background: var(--bg-card);
            border-radius: 8px;
            height: 24px;
            overflow: hidden;
            position: relative;
        }

        .budget-bar {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s ease, background 0.3s ease;
        }

        .budget-bar.safe { background: var(--accent-green); }
        .budget-bar.warning { background: var(--accent-yellow); }
        .budget-bar.danger { background: var(--accent-red); }

        .budget-percentage {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            font-weight: 600;
        }

        .budget-alert {
            background: var(--accent-red);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
            align-items: center;
            gap: 8px;
        }

        .budget-alert.visible {
            display: flex;
        }

        .budget-alert svg {
            width: 20px;
            height: 20px;
        }

        .panel-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 900px) {
            .panel-grid {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
        }

        .panel h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--bg-card);
        }

        .last-post {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 16px;
        }

        .last-post-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .last-post-meta {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.posted { background: var(--accent-green); color: #000; }
        .status-badge.drafted { background: var(--accent-blue); }
        .status-badge.pending_approval { background: var(--accent-yellow); color: #000; }
        .status-badge.approved { background: var(--accent-purple); }

        .pending-list {
            list-style: none;
        }

        .pending-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: var(--bg-card);
            border-radius: 8px;
            margin-bottom: 8px;
        }

        .pending-item:last-child {
            margin-bottom: 0;
        }

        .pending-item-title {
            font-size: 13px;
            flex: 1;
            margin-right: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .empty-state {
            text-align: center;
            padding: 32px;
            color: var(--text-secondary);
        }

        .pipeline-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .pipeline-status.healthy {
            background: rgba(0, 217, 165, 0.2);
            color: var(--accent-green);
        }

        .pipeline-status.budget_warning {
            background: rgba(255, 193, 7, 0.2);
            color: var(--accent-yellow);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .pipeline-status.healthy .status-dot { background: var(--accent-green); }
        .pipeline-status.budget_warning .status-dot { background: var(--accent-yellow); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }

        .error-message {
            background: rgba(255, 71, 87, 0.2);
            border: 1px solid var(--accent-red);
            color: var(--accent-red);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div>
            <h1>Moltbook Flywheel Dashboard</h1>
            <div class="refresh-info">Auto-refresh: <span id="countdown">60</span>s | Last update: <span id="lastUpdate">--</span></div>
        </div>
        <div id="pipelineStatus" class="pipeline-status healthy">
            <span class="status-dot"></span>
            <span id="statusText">Healthy</span>
        </div>
    </div>

    <div id="content">
        <div class="loading">Loading flywheel data...</div>
    </div>

    <script>
        const API_BASE = '/api/flywheel';
        let refreshInterval;
        let countdownInterval;
        let countdown = 60;

        async function fetchFlywheelStatus() {
            try {
                const response = await fetch(`${API_BASE}/status`);
                const data = await response.json();

                if (data.success) {
                    renderDashboard(data);
                } else {
                    showError(data.error || 'Failed to fetch data');
                }
            } catch (error) {
                showError(error.message);
            }
        }

        function renderDashboard(data) {
            const { metrics, budget, last_post, pending_items, pipeline_health, timestamp } = data;

            // Update last update time
            document.getElementById('lastUpdate').textContent = new Date(timestamp).toLocaleTimeString();

            // Update pipeline status
            const statusEl = document.getElementById('pipelineStatus');
            const statusTextEl = document.getElementById('statusText');
            statusEl.className = `pipeline-status ${pipeline_health}`;
            statusTextEl.textContent = pipeline_health === 'healthy' ? 'Healthy' : 'Budget Warning';

            // Render main content
            document.getElementById('content').innerHTML = `
                <div class="metrics-grid">
                    <div class="metric-card scans">
                        <div class="metric-value">${metrics.scans_today}</div>
                        <div class="metric-label">Scans Today</div>
                    </div>
                    <div class="metric-card topics">
                        <div class="metric-value">${metrics.topics_detected}</div>
                        <div class="metric-label">Topics Detected</div>
                    </div>
                    <div class="metric-card research">
                        <div class="metric-value">${metrics.research_dispatched}</div>
                        <div class="metric-label">Research Dispatched</div>
                    </div>
                    <div class="metric-card drafted">
                        <div class="metric-value">${metrics.responses_drafted}</div>
                        <div class="metric-label">Responses Drafted</div>
                    </div>
                    <div class="metric-card approved">
                        <div class="metric-value">${metrics.council_approved}</div>
                        <div class="metric-label">Council Approved</div>
                    </div>
                    <div class="metric-card posted">
                        <div class="metric-value">${metrics.posted_count}</div>
                        <div class="metric-label">Posted</div>
                    </div>
                </div>

                <div class="budget-section">
                    <div class="budget-header">
                        <h2>Daily Budget</h2>
                        <div class="budget-amount">$${budget.spent.toFixed(2)} / $${budget.limit.toFixed(2)}</div>
                    </div>
                    <div class="budget-bar-container">
                        <div class="budget-bar ${getBudgetClass(budget.percentage)}"
                             style="width: ${Math.min(budget.percentage, 100)}%"></div>
                        <span class="budget-percentage">${budget.percentage}%</span>
                    </div>
                    <div class="budget-alert ${budget.alert ? 'visible' : ''}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        <span>Budget threshold exceeded (80%). Research dispatch may be throttled.</span>
                    </div>
                </div>

                <div class="panel-grid">
                    <div class="panel">
                        <h3>Last Post</h3>
                        ${renderLastPost(last_post)}
                    </div>
                    <div class="panel">
                        <h3>Pending Items (${pending_items.length})</h3>
                        ${renderPendingItems(pending_items)}
                    </div>
                </div>
            `;
        }

        function getBudgetClass(percentage) {
            if (percentage >= 80) return 'danger';
            if (percentage >= 60) return 'warning';
            return 'safe';
        }

        function renderLastPost(post) {
            if (!post) {
                return '<div class="empty-state">No posts yet today</div>';
            }

            const postedAt = post.posted_at ? new Date(post.posted_at).toLocaleString() : 'Unknown';

            return `
                <div class="last-post">
                    <div class="last-post-title">${escapeHtml(post.title || 'Untitled')}</div>
                    <div class="last-post-meta">
                        <span class="status-badge ${post.status}">${post.status}</span>
                        <span>Platform: ${post.platform || 'Unknown'}</span>
                        <span>${postedAt}</span>
                    </div>
                </div>
            `;
        }

        function renderPendingItems(items) {
            if (!items || items.length === 0) {
                return '<div class="empty-state">No pending items</div>';
            }

            return `
                <ul class="pending-list">
                    ${items.map(item => `
                        <li class="pending-item">
                            <span class="pending-item-title">${escapeHtml(item.title || 'Untitled')}</span>
                            <span class="status-badge ${item.status}">${item.status.replace('_', ' ')}</span>
                        </li>
                    `).join('')}
                </ul>
            `;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showError(message) {
            document.getElementById('content').innerHTML = `
                <div class="error-message">
                    <strong>Error:</strong> ${escapeHtml(message)}
                </div>
            `;
        }

        function startRefreshCycle() {
            countdown = 60;

            countdownInterval = setInterval(() => {
                countdown--;
                document.getElementById('countdown').textContent = countdown;

                if (countdown <= 0) {
                    fetchFlywheelStatus();
                    countdown = 60;
                }
            }, 1000);
        }

        // Initialize
        fetchFlywheelStatus();
        startRefreshCycle();
    </script>
</body>
</html>
```

---

### 3. Register Blueprint in SAG App

Update the main SAG application file to register the new blueprint.

**File to modify:** Main SAG app.py (location may vary)

Add import:
```python
from routes.flywheel_routes import flywheel_bp
```

Register blueprint:
```python
app.register_blueprint(flywheel_bp)
```

---

### 4. Database Schema Requirements

Ensure the following tables exist in `zammad_production` database on bluefin (192.168.132.222):

**Table: moltbook_post_queue**
```sql
CREATE TABLE IF NOT EXISTS moltbook_post_queue (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    platform VARCHAR(100),
    status VARCHAR(50) DEFAULT 'drafted',
    research_id VARCHAR(100),
    topic_source VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    posted_at TIMESTAMP,
    error_message TEXT
);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_moltbook_status ON moltbook_post_queue(status);
CREATE INDEX IF NOT EXISTS idx_moltbook_created ON moltbook_post_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_moltbook_posted ON moltbook_post_queue(posted_at);
```

**Table: council_votes**
```sql
CREATE TABLE IF NOT EXISTS council_votes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES moltbook_post_queue(id),
    voter_id VARCHAR(100),
    vote VARCHAR(20),
    reasoning TEXT,
    voted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_council_post ON council_votes(post_id);
CREATE INDEX IF NOT EXISTS idx_council_voted ON council_votes(voted_at);
```

**Thermal Memory Types for Flywheel:**
- `flywheel_scan` - Each scan operation
- `flywheel_topic_detected` - Topics found during scan
- `flywheel_research_dispatched` - Research tasks sent
- `flywheel_research_cost` - Cost tracking (include "cost: $X.XX" in content)

---

## Steps

1. **Create flywheel_routes.py**
   - Add the API endpoint code to `/ganuda/sag/routes/flywheel_routes.py`
   - Ensure proper error handling and connection management

2. **Create dashboard template**
   - Add the HTML template to `/ganuda/sag/templates/flywheel_dashboard.html`
   - Verify CSS styling matches SAG UI theme

3. **Register the blueprint**
   - Locate main SAG app.py file
   - Add blueprint import and registration

4. **Create database tables**
   - Connect to bluefin: `psql -h 192.168.132.222 -U claude -d zammad_production`
   - Execute CREATE TABLE statements for `moltbook_post_queue` and `council_votes`
   - Verify indexes created

5. **Test the integration**
   - Access http://192.168.132.223:4000/api/flywheel/status
   - Verify JSON response structure
   - Access dashboard template via appropriate route
   - Confirm auto-refresh functionality (60s interval)

6. **Add dashboard route**
   - Add route to serve the dashboard HTML template
   - Either add to existing routes or flywheel_routes.py

---

## Verification

1. **API Endpoint Test:**
```bash
curl http://192.168.132.223:4000/api/flywheel/status | jq
```
Expected: JSON with metrics, budget, last_post, pending_items

2. **Budget Alert Test:**
```bash
curl http://192.168.132.223:4000/api/flywheel/budget/alert | jq
```
Expected: JSON with alert boolean, spent, limit

3. **Dashboard Visual Test:**
   - Navigate to dashboard URL
   - Verify all 6 metric cards display
   - Verify budget progress bar renders
   - Wait 60s to confirm auto-refresh countdown works
   - Check browser console for JavaScript errors

4. **Database Connection Test:**
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) FROM thermal_memory_archive WHERE memory_type LIKE 'flywheel_%';"
```

---

## Files Created

| File | Purpose |
|------|---------|
| `/ganuda/sag/routes/flywheel_routes.py` | API endpoints for flywheel status and budget alert |
| `/ganuda/sag/templates/flywheel_dashboard.html` | Frontend dashboard widget with auto-refresh |

---

## Files Modified

| File | Change |
|------|--------|
| Main SAG app.py | Register flywheel_bp blueprint |

---

## Do NOT

- Expose database credentials in frontend code
- Skip error handling on database queries
- Hardcode IP addresses in frontend JavaScript (use relative paths)
- Ignore connection cleanup (always close cursor and connection)
- Set refresh interval below 30 seconds (avoid hammering API)
- Deploy without testing budget alert threshold logic

---

## Dependencies

- Flask (already in SAG)
- psycopg2 (database driver)
- Existing thermal_memory_archive table
- SAG UI running on http://192.168.132.223:4000

---

## Related Phase Documents

- Phase 1: Topic Detection Daemon
- Phase 2: Research Dispatch Integration
- Phase 3: Council Review Pipeline
- Phase 4: Auto-Post Publisher
- **Phase 5: Visibility Dashboard (this document)**
- Phase 6: Budget Controls & Throttling

---

## Notes

- Budget resets daily at midnight (based on created_at filtering)
- All costs tracked via thermal_memory with `flywheel_research_cost` type
- Dashboard is read-only; no write operations from UI
- Consider adding WebSocket support in future for real-time updates

---

*Generated: 2026-02-06*
*TPM: Claude Opus 4.5*
