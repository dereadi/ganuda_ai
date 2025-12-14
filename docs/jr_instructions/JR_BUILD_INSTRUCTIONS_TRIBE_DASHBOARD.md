# JR BUILD INSTRUCTIONS: Tribe Dashboard for SAG UI

**Target**: SAG Unified Interface (http://192.168.132.223:4000/)
**Date**: December 13, 2025
**Priority**: P1 - Integration
**Purpose**: Consolidate all tribal data (Specialists, Council, Trails, Memory) into one view

## Overview

Add a new "Tribe" tab to SAG UI that provides a unified view of:
- 7-Specialist Council status and recent votes
- Trail health by category (stigmergic system)
- Thermal memory resonance
- Memory vs Trails comparison (arXiv:2512.10166 metrics)
- CMDB/Hardware inventory

This gives the TPM "the tribe in one place."

---

## PART 1: Backend API Endpoints

**Modify**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

### 1.1 Add Tribe Summary Endpoint

```python
# ============================================================================
# ROUTES - Tribe Dashboard
# ============================================================================

@app.route('/api/tribe/summary')
def tribe_summary():
    """Get unified tribe summary - specialists, trails, memory"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        # Get thermal memory stats
        cur.execute("""
            SELECT COUNT(*),
                   ROUND(AVG(temperature_score)::numeric, 2),
                   COUNT(*) FILTER (WHERE temperature_score >= 90),
                   COUNT(*) FILTER (WHERE sacred_pattern = true)
            FROM thermal_memory_archive
        """)
        mem_row = cur.fetchone()

        # Get trail stats
        cur.execute("""
            SELECT COUNT(*),
                   ROUND(AVG(pheromone_strength)::numeric, 2),
                   COUNT(*) FILTER (WHERE pheromone_strength >= 70)
            FROM breadcrumb_trails
            WHERE pheromone_strength > 0
        """)
        trail_row = cur.fetchone()

        # Get council vote stats
        cur.execute("""
            SELECT COUNT(*),
                   COUNT(*) FILTER (WHERE vote_outcome = 'PROCEED'),
                   COUNT(*) FILTER (WHERE vote_outcome = 'CAUTION'),
                   MAX(created_at)
            FROM council_votes
        """)
        vote_row = cur.fetchone()

        # Get deposit counts by specialist
        cur.execute("""
            SELECT deposited_by, COUNT(*) as deposits
            FROM pheromone_deposits
            GROUP BY deposited_by
            ORDER BY deposits DESC
        """)
        deposits = [{"specialist": r[0], "deposits": r[1]} for r in cur.fetchall()]

        conn.close()

        return jsonify({
            "thermal_memory": {
                "total": mem_row[0] or 0,
                "avg_temperature": float(mem_row[1] or 0),
                "hot_count": mem_row[2] or 0,
                "sacred_patterns": mem_row[3] or 0,
                "resonance_pct": round((mem_row[2] or 0) / max(mem_row[0] or 1, 1) * 100, 1)
            },
            "trails": {
                "total": trail_row[0] or 0,
                "avg_strength": float(trail_row[1] or 0),
                "hot_count": trail_row[2] or 0
            },
            "council": {
                "total_votes": vote_row[0] or 0,
                "proceed_count": vote_row[1] or 0,
                "caution_count": vote_row[2] or 0,
                "last_vote": vote_row[3].isoformat() if vote_row[3] else None
            },
            "deposits_by_specialist": deposits,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Tribe summary error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tribe/specialists')
def tribe_specialists():
    """Get specialist mapping and trail categories"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        # Get specialist-trail mapping with decay rates
        cur.execute("""
            SELECT stm.specialist, stm.default_category, stm.description,
                   tdr.decay_rate
            FROM specialist_trail_mapping stm
            LEFT JOIN trail_decay_rates tdr ON stm.default_category = tdr.category
            ORDER BY tdr.decay_rate DESC NULLS LAST
        """)

        specialists = []
        for row in cur.fetchall():
            specialists.append({
                "name": row[0],
                "category": row[1],
                "description": row[2],
                "decay_rate": float(row[3]) if row[3] else 0.95
            })

        conn.close()

        return jsonify({
            "specialists": specialists,
            "count": len(specialists)
        })

    except Exception as e:
        logger.error(f"Tribe specialists error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tribe/trail-health')
def tribe_trail_health():
    """Get trail health by category - from trail_health_summary view"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        cur.execute("SELECT * FROM trail_health_summary ORDER BY trail_count DESC")

        categories = []
        for row in cur.fetchall():
            categories.append({
                "category": row[0],
                "decay_rate": float(row[1]) if row[1] else 0.95,
                "specialist_owner": row[2],
                "trail_count": row[3],
                "avg_strength": float(row[4]) if row[4] else 0,
                "avg_consensus": float(row[5]) if row[5] else 1,
                "total_deposits": row[6],
                "last_activity": row[7].isoformat() if row[7] else None
            })

        conn.close()

        return jsonify({
            "categories": categories,
            "total_trails": sum(c["trail_count"] for c in categories)
        })

    except Exception as e:
        logger.error(f"Trail health error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tribe/council-votes')
def tribe_council_votes():
    """Get recent council votes"""
    import psycopg2

    limit = request.args.get('limit', 10, type=int)

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT vote_id, question, vote_outcome, confidence_score,
                   concern_flags, participating_specialists, created_at
            FROM council_votes
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        votes = []
        for row in cur.fetchall():
            votes.append({
                "vote_id": row[0],
                "question": row[1][:100] + "..." if len(row[1] or "") > 100 else row[1],
                "outcome": row[2],
                "confidence": float(row[3]) if row[3] else 0,
                "concerns": row[4],
                "specialists": row[5],
                "timestamp": row[6].isoformat() if row[6] else None
            })

        conn.close()

        return jsonify({
            "votes": votes,
            "count": len(votes)
        })

    except Exception as e:
        logger.error(f"Council votes error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tribe/memory-vs-trails')
def tribe_memory_vs_trails():
    """Get memory vs trails comparison - implements arXiv:2512.10166 metrics"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        cur.execute("SELECT * FROM memory_vs_trails")

        comparison = []
        for row in cur.fetchall():
            comparison.append({
                "system_type": row[0],
                "entry_count": row[1],
                "avg_strength": float(row[2]) if row[2] else 0,
                "hot_entries": row[3],
                "last_activity": row[4].isoformat() if row[4] else None
            })

        conn.close()

        # Calculate density (from paper: stigmergy dominates at >= 0.20)
        total_entries = sum(c["entry_count"] for c in comparison)
        node_count = 6  # Current federation size
        density = total_entries / (node_count * 1000) if node_count > 0 else 0

        return jsonify({
            "comparison": comparison,
            "density": round(density, 3),
            "density_threshold": 0.20,
            "dominant_system": "stigmergy" if density >= 0.20 else "memory",
            "paper_reference": "arXiv:2512.10166"
        })

    except Exception as e:
        logger.error(f"Memory vs trails error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tribe/cmdb')
def tribe_cmdb():
    """Get CMDB/hardware inventory"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT hostname, scan_timestamp, memory_total, gpu_count,
                   LEFT(os_info::text, 100) as os_info
            FROM hardware_inventory
            ORDER BY hostname
        """)

        nodes = []
        for row in cur.fetchall():
            nodes.append({
                "hostname": row[0],
                "last_scan": row[1].isoformat() if row[1] else None,
                "memory_gb": round((row[2] or 0) / (1024**3), 1),
                "gpu_count": row[3] or 0,
                "os_info": row[4]
            })

        conn.close()

        return jsonify({
            "nodes": nodes,
            "count": len(nodes)
        })

    except Exception as e:
        logger.error(f"CMDB error: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## PART 2: Frontend - Add Tribe Tab

**Modify**: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

### 2.1 Add Tab Button

Find the `<nav class="tab-nav">` section and add:

```html
<button class="tab-btn" data-tab="tribe">🏛️ Tribe</button>
```

### 2.2 Add Tribe Tab Content

Add this after the last `</div>` of a tab-content section:

```html
<!-- Tab: Tribe Dashboard -->
<div id="tribe-tab" class="tab-content">
    <h2 style="margin-bottom: 20px; color: var(--sacred-green);">🏛️ Tribe Dashboard</h2>
    <p style="color: var(--text-secondary); margin-bottom: 20px;">
        7-Specialist Council | Stigmergic Trails | Thermal Memory | FOR SEVEN GENERATIONS
    </p>

    <!-- Summary Cards -->
    <div id="tribe-summary" class="tribe-summary-grid">
        <div class="loading">Loading tribe summary...</div>
    </div>

    <!-- Two Column Layout -->
    <div class="tribe-columns">
        <!-- Left Column: Specialists & Trail Health -->
        <div class="tribe-column">
            <div class="tribe-section">
                <h3>🦎 Specialist-Trail Mapping</h3>
                <div id="tribe-specialists"><div class="loading">Loading...</div></div>
            </div>

            <div class="tribe-section">
                <h3>🐜 Trail Health by Category</h3>
                <div id="tribe-trail-health"><div class="loading">Loading...</div></div>
            </div>
        </div>

        <!-- Right Column: Council Votes & Memory -->
        <div class="tribe-column">
            <div class="tribe-section">
                <h3>🗳️ Recent Council Votes</h3>
                <div id="tribe-council-votes"><div class="loading">Loading...</div></div>
            </div>

            <div class="tribe-section">
                <h3>📊 Memory vs Trails (arXiv:2512.10166)</h3>
                <div id="tribe-memory-comparison"><div class="loading">Loading...</div></div>
            </div>
        </div>
    </div>

    <!-- CMDB Section -->
    <div class="tribe-section" style="margin-top: 20px;">
        <h3>🖥️ CMDB - Hardware Inventory</h3>
        <div id="tribe-cmdb"><div class="loading">Loading...</div></div>
    </div>
</div>
```

---

## PART 3: Frontend - JavaScript

**Add to**: `/ganuda/home/dereadi/sag_unified_interface/static/js/unified.js` (or inline in index.html)

```javascript
// ============================================================================
// TRIBE DASHBOARD
// ============================================================================

async function loadTribeSummary() {
    try {
        const response = await fetch('/api/tribe/summary');
        const data = await response.json();

        const container = document.getElementById('tribe-summary');
        container.innerHTML = `
            <div class="tribe-card thermal">
                <div class="tribe-card-icon">🔥</div>
                <div class="tribe-card-content">
                    <div class="tribe-card-title">Thermal Memory</div>
                    <div class="tribe-card-value">${data.thermal_memory.total.toLocaleString()}</div>
                    <div class="tribe-card-detail">
                        ${data.thermal_memory.resonance_pct}% hot |
                        ${data.thermal_memory.sacred_patterns} sacred
                    </div>
                </div>
            </div>

            <div class="tribe-card trails">
                <div class="tribe-card-icon">🐜</div>
                <div class="tribe-card-content">
                    <div class="tribe-card-title">Active Trails</div>
                    <div class="tribe-card-value">${data.trails.total}</div>
                    <div class="tribe-card-detail">
                        Avg strength: ${data.trails.avg_strength}
                    </div>
                </div>
            </div>

            <div class="tribe-card council">
                <div class="tribe-card-icon">🗳️</div>
                <div class="tribe-card-content">
                    <div class="tribe-card-title">Council Votes</div>
                    <div class="tribe-card-value">${data.council.total_votes}</div>
                    <div class="tribe-card-detail">
                        ${data.council.proceed_count} PROCEED |
                        ${data.council.caution_count} CAUTION
                    </div>
                </div>
            </div>

            <div class="tribe-card deposits">
                <div class="tribe-card-icon">👣</div>
                <div class="tribe-card-content">
                    <div class="tribe-card-title">Pheromone Deposits</div>
                    <div class="tribe-card-value">${data.deposits_by_specialist.reduce((a, b) => a + b.deposits, 0)}</div>
                    <div class="tribe-card-detail">
                        ${data.deposits_by_specialist.slice(0, 3).map(d => d.specialist).join(', ')}
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load tribe summary:', error);
        document.getElementById('tribe-summary').innerHTML =
            '<div class="error">Failed to load tribe summary</div>';
    }
}

async function loadTribeSpecialists() {
    try {
        const response = await fetch('/api/tribe/specialists');
        const data = await response.json();

        const container = document.getElementById('tribe-specialists');

        const specialistEmoji = {
            'crawdad': '🦞',
            'gecko': '🦎',
            'turtle': '🐢',
            'eagle_eye': '🦅',
            'spider': '🕷️',
            'peace_chief': '☮️',
            'raven': '🐦‍⬛',
            'tpm': '📋',
            'system': '⚙️',
            'observer': '👁️'
        };

        container.innerHTML = `
            <table class="tribe-table">
                <thead>
                    <tr>
                        <th>Specialist</th>
                        <th>Category</th>
                        <th>Decay Rate</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.specialists.map(s => `
                        <tr>
                            <td>${specialistEmoji[s.name] || '👤'} ${s.name}</td>
                            <td><span class="category-badge ${s.category}">${s.category}</span></td>
                            <td>${(s.decay_rate * 100).toFixed(1)}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Failed to load specialists:', error);
    }
}

async function loadTribeTrailHealth() {
    try {
        const response = await fetch('/api/tribe/trail-health');
        const data = await response.json();

        const container = document.getElementById('tribe-trail-health');

        if (data.categories.length === 0) {
            container.innerHTML = '<div class="empty-state">No active trails</div>';
            return;
        }

        container.innerHTML = `
            <table class="tribe-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Trails</th>
                        <th>Avg Strength</th>
                        <th>Consensus</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.categories.map(c => `
                        <tr>
                            <td><span class="category-badge ${c.category}">${c.category}</span></td>
                            <td>${c.trail_count}</td>
                            <td>
                                <div class="strength-bar" style="--strength: ${c.avg_strength}%">
                                    ${c.avg_strength.toFixed(1)}
                                </div>
                            </td>
                            <td>${c.avg_consensus.toFixed(2)}x</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="tribe-footer">Total: ${data.total_trails} trails</div>
        `;
    } catch (error) {
        console.error('Failed to load trail health:', error);
    }
}

async function loadTribeCouncilVotes() {
    try {
        const response = await fetch('/api/tribe/council-votes?limit=5');
        const data = await response.json();

        const container = document.getElementById('tribe-council-votes');

        if (data.votes.length === 0) {
            container.innerHTML = '<div class="empty-state">No council votes recorded</div>';
            return;
        }

        container.innerHTML = `
            <div class="vote-list">
                ${data.votes.map(v => `
                    <div class="vote-item ${v.outcome.toLowerCase()}">
                        <div class="vote-header">
                            <span class="vote-outcome">${v.outcome}</span>
                            <span class="vote-confidence">${(v.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div class="vote-question">${v.question}</div>
                        <div class="vote-meta">
                            ${v.concerns ? `<span class="concern-flag">⚠️ ${v.concerns}</span>` : ''}
                            <span class="vote-time">${new Date(v.timestamp).toLocaleDateString()}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Failed to load council votes:', error);
    }
}

async function loadTribeMemoryComparison() {
    try {
        const response = await fetch('/api/tribe/memory-vs-trails');
        const data = await response.json();

        const container = document.getElementById('tribe-memory-comparison');

        container.innerHTML = `
            <div class="comparison-chart">
                ${data.comparison.map(c => `
                    <div class="comparison-row">
                        <div class="comparison-label">${c.system_type}</div>
                        <div class="comparison-bar-container">
                            <div class="comparison-bar" style="width: ${Math.min(100, c.entry_count / 50)}%"></div>
                            <span class="comparison-value">${c.entry_count.toLocaleString()}</span>
                        </div>
                        <div class="comparison-meta">
                            Avg: ${c.avg_strength} | Hot: ${c.hot_entries}
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="density-indicator">
                <strong>Density:</strong> ${data.density}
                <span class="density-status ${data.density >= data.density_threshold ? 'high' : 'low'}">
                    ${data.dominant_system === 'stigmergy' ? '🐜 Stigmergy Dominant' : '🧠 Memory Dominant'}
                </span>
            </div>
            <div class="paper-ref">
                Research: <a href="https://arxiv.org/abs/2512.10166" target="_blank">${data.paper_reference}</a>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load memory comparison:', error);
    }
}

async function loadTribeCMDB() {
    try {
        const response = await fetch('/api/tribe/cmdb');
        const data = await response.json();

        const container = document.getElementById('tribe-cmdb');

        container.innerHTML = `
            <table class="tribe-table">
                <thead>
                    <tr>
                        <th>Hostname</th>
                        <th>Memory</th>
                        <th>GPUs</th>
                        <th>Last Scan</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.nodes.map(n => `
                        <tr>
                            <td><strong>${n.hostname}</strong></td>
                            <td>${n.memory_gb} GB</td>
                            <td>${n.gpu_count}</td>
                            <td>${n.last_scan ? new Date(n.last_scan).toLocaleDateString() : 'Never'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Failed to load CMDB:', error);
    }
}

// Load all tribe data when tab is activated
function loadTribeDashboard() {
    loadTribeSummary();
    loadTribeSpecialists();
    loadTribeTrailHealth();
    loadTribeCouncilVotes();
    loadTribeMemoryComparison();
    loadTribeCMDB();
}

// Hook into tab switching
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.dataset.tab === 'tribe') {
                loadTribeDashboard();
            }
        });
    });
});
```

---

## PART 4: CSS Styles

**Add to**: `/ganuda/home/dereadi/sag_unified_interface/static/css/unified.css`

```css
/* ============================================================================
   TRIBE DASHBOARD STYLES
   ============================================================================ */

.tribe-summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.tribe-card {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-left: 4px solid var(--sacred-green);
}

.tribe-card.thermal { border-left-color: #ff6b6b; }
.tribe-card.trails { border-left-color: #4ecdc4; }
.tribe-card.council { border-left-color: #45b7d1; }
.tribe-card.deposits { border-left-color: #96ceb4; }

.tribe-card-icon {
    font-size: 2em;
}

.tribe-card-title {
    font-size: 0.85em;
    color: var(--text-secondary);
}

.tribe-card-value {
    font-size: 1.8em;
    font-weight: bold;
    color: var(--text-primary);
}

.tribe-card-detail {
    font-size: 0.75em;
    color: var(--text-muted);
}

.tribe-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

@media (max-width: 1024px) {
    .tribe-columns {
        grid-template-columns: 1fr;
    }
}

.tribe-section {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.tribe-section h3 {
    margin: 0 0 12px 0;
    color: var(--sacred-green);
    font-size: 1.1em;
}

.tribe-table {
    width: 100%;
    border-collapse: collapse;
}

.tribe-table th,
.tribe-table td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.tribe-table th {
    background: var(--header-bg);
    font-weight: 600;
    font-size: 0.85em;
}

.category-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 500;
}

.category-badge.danger { background: #ff6b6b22; color: #ff6b6b; }
.category-badge.technical { background: #45b7d122; color: #45b7d1; }
.category-badge.wisdom { background: #9b59b622; color: #9b59b6; }
.category-badge.discovery { background: #f39c1222; color: #f39c12; }
.category-badge.integration { background: #4ecdc422; color: #4ecdc4; }
.category-badge.coordination { background: #96ceb422; color: #96ceb4; }
.category-badge.strategy { background: #3498db22; color: #3498db; }
.category-badge.general { background: #95a5a622; color: #95a5a6; }

.strength-bar {
    background: linear-gradient(90deg, var(--sacred-green) var(--strength), transparent var(--strength));
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
}

.vote-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.vote-item {
    padding: 12px;
    border-radius: 6px;
    background: var(--bg-secondary);
    border-left: 3px solid;
}

.vote-item.proceed { border-left-color: var(--sacred-green); }
.vote-item.caution { border-left-color: #f39c12; }
.vote-item.halt { border-left-color: #e74c3c; }

.vote-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.vote-outcome {
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.85em;
}

.vote-confidence {
    color: var(--text-muted);
    font-size: 0.85em;
}

.vote-question {
    font-size: 0.9em;
    margin-bottom: 8px;
}

.vote-meta {
    display: flex;
    gap: 12px;
    font-size: 0.75em;
    color: var(--text-muted);
}

.concern-flag {
    color: #f39c12;
}

.comparison-chart {
    margin-bottom: 16px;
}

.comparison-row {
    margin-bottom: 12px;
}

.comparison-label {
    font-weight: 500;
    margin-bottom: 4px;
}

.comparison-bar-container {
    display: flex;
    align-items: center;
    gap: 8px;
}

.comparison-bar {
    height: 24px;
    background: var(--sacred-green);
    border-radius: 4px;
    min-width: 10px;
}

.comparison-value {
    font-weight: bold;
}

.comparison-meta {
    font-size: 0.75em;
    color: var(--text-muted);
    margin-top: 4px;
}

.density-indicator {
    padding: 12px;
    background: var(--bg-secondary);
    border-radius: 6px;
    margin-bottom: 12px;
}

.density-status {
    padding: 4px 8px;
    border-radius: 4px;
    margin-left: 8px;
}

.density-status.high { background: #4ecdc422; color: #4ecdc4; }
.density-status.low { background: #ff6b6b22; color: #ff6b6b; }

.paper-ref {
    font-size: 0.8em;
    color: var(--text-muted);
}

.paper-ref a {
    color: var(--sacred-green);
}

.tribe-footer {
    text-align: right;
    font-size: 0.85em;
    color: var(--text-muted);
    margin-top: 8px;
}

.empty-state {
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
}
```

---

## Deployment Checklist

### On redfin (192.168.132.223):

```bash
# 1. Backup current app.py
cp /ganuda/home/dereadi/sag_unified_interface/app.py \
   /ganuda/home/dereadi/sag_unified_interface/app.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Add the new routes to app.py (after existing routes)
# Insert the Python code from PART 1 above

# 3. Add the Tribe tab HTML to templates/index.html
# Insert the HTML code from PART 2 above

# 4. Add the JavaScript functions
# Either add to static/js/unified.js or inline in index.html

# 5. Add the CSS styles to static/css/unified.css
# Append the CSS from PART 4 above

# 6. Restart SAG UI
pkill -f 'python.*app.py'
cd /ganuda/home/dereadi/sag_unified_interface
source venv/bin/activate
nohup python app.py &

# 7. Verify
curl http://localhost:4000/api/tribe/summary
```

---

## Success Criteria

| Component | Metric |
|-----------|--------|
| Summary Cards | Shows thermal memory, trails, council, deposits |
| Specialist Mapping | 10 specialists with categories/decay rates |
| Trail Health | Category breakdown with strength/consensus |
| Council Votes | Recent 5 votes with outcomes |
| Memory vs Trails | Comparison with density calculation |
| CMDB | Hardware inventory display |

---

## API Reference

| Endpoint | Description |
|----------|-------------|
| GET /api/tribe/summary | Overall tribe metrics |
| GET /api/tribe/specialists | Specialist-trail mapping |
| GET /api/tribe/trail-health | Trail health by category |
| GET /api/tribe/council-votes | Recent council votes |
| GET /api/tribe/memory-vs-trails | Memory vs trails comparison |
| GET /api/tribe/cmdb | Hardware inventory |

---

**FOR SEVEN GENERATIONS**
