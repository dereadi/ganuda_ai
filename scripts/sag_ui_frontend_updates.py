#!/usr/bin/env python3
"""
Update SAG UI frontend with enhanced Tribe tab and Alert filtering
Run on redfin
"""

import shutil
from datetime import datetime

JS_FILE = "/ganuda/home/dereadi/sag_unified_interface/static/js/control-room.js"

# New enhanced loadTribeView function
NEW_TRIBE_VIEW = '''function loadTribeView() {
    var container = document.getElementById("tribe-content");
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading tribe data...</div>';

    // Fetch multiple endpoints in parallel
    Promise.all([
        fetch("/api/tribe/summary").then(function(r) { return r.json(); }).catch(function() { return {}; }),
        fetch("/api/tribe/council-votes?limit=10").then(function(r) { return r.json(); }).catch(function() { return {votes: []}; })
    ]).then(function(results) {
        var summary = results[0];
        var votesData = results[1];

        var html = '<div class="tribe-dashboard">';

        // Summary Cards
        html += '<div class="tribe-stats">';
        html += '<div class="stat-card"><h4>Council Votes</h4><div class="stat-value">' + (summary.council ? summary.council.total_votes : 0) + '</div></div>';
        html += '<div class="stat-card"><h4>Thermal Memories</h4><div class="stat-value">' + (summary.thermal_memory ? summary.thermal_memory.total : 0) + '</div></div>';
        html += '<div class="stat-card"><h4>Avg Temperature</h4><div class="stat-value">' + (summary.thermal_memory ? summary.thermal_memory.avg_temperature.toFixed(1) : 0) + '&deg;</div></div>';
        html += '<div class="stat-card"><h4>Resonance</h4><div class="stat-value">' + (summary.thermal_memory ? summary.thermal_memory.resonance_pct.toFixed(0) : 0) + '%</div></div>';
        html += '</div>';

        // Recent Council Votes
        html += '<div class="tribe-section"><h3>Recent Council Votes</h3>';
        if (votesData.votes && votesData.votes.length > 0) {
            html += '<div class="council-votes">';
            votesData.votes.forEach(function(vote) {
                var confidenceClass = vote.confidence > 0.8 ? 'high' : vote.confidence > 0.6 ? 'medium' : 'low';
                var statusClass = vote.tpm_vote === 'approved' ? 'approved' : vote.tpm_vote === 'rejected' ? 'rejected' : 'pending';
                html += '<div class="vote-card">';
                html += '<div class="vote-header">';
                html += '<span class="vote-id">#' + vote.vote_id + '</span>';
                html += '<span class="vote-recommendation">' + (vote.recommendation || 'PENDING') + '</span>';
                html += '</div>';
                html += '<div class="vote-question">' + escapeHtml(vote.question || '').substring(0, 150) + '...</div>';
                html += '<div class="vote-meta">';
                html += '<span class="vote-confidence ' + confidenceClass + '">' + (vote.confidence * 100).toFixed(0) + '% confident</span>';
                html += '<span class="vote-status ' + statusClass + '">TPM: ' + (vote.tpm_vote || 'pending') + '</span>';
                if (vote.concern_count > 0) {
                    html += '<span class="vote-concerns">' + vote.concern_count + ' concern(s)</span>';
                }
                html += '</div>';
                html += '</div>';
            });
            html += '</div>';
        } else {
            html += '<p class="no-data">No recent council votes</p>';
        }
        html += '</div>';

        // 7-Specialist Council
        html += '<div class="tribe-section"><h3>7-Specialist Council</h3>';
        html += '<div class="specialist-grid">';
        var specialists = [
            {name: 'Crawdad', role: 'Security', icon: '&#129408;'},
            {name: 'Gecko', role: 'Performance', icon: '&#129422;'},
            {name: 'Turtle', role: '7GEN Wisdom', icon: '&#128034;'},
            {name: 'Eagle Eye', role: 'Monitoring', icon: '&#129413;'},
            {name: 'Spider', role: 'Integration', icon: '&#128375;'},
            {name: 'Peace Chief', role: 'Consensus', icon: '&#128330;'},
            {name: 'Raven', role: 'Strategy', icon: '&#129413;'}
        ];
        specialists.forEach(function(spec) {
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
}'''

# New enhanced loadAlertsView function
NEW_ALERTS_VIEW = '''function loadAlertsView() {
    var container = document.getElementById("alerts-list-full");
    if (!container) return;

    // Add filter controls if not present
    var filterDiv = document.getElementById("alerts-filters");
    if (!filterDiv) {
        var parentDiv = container.parentElement;
        var filterHtml = '<div id="alerts-filters" class="filter-controls">';
        filterHtml += '<label><input type="checkbox" id="filter-critical" checked> Critical</label>';
        filterHtml += '<label><input type="checkbox" id="filter-warning" checked> Warning</label>';
        filterHtml += '<label><input type="checkbox" id="filter-info"> Info/FYI</label>';
        filterHtml += '</div>';
        parentDiv.insertAdjacentHTML('afterbegin', filterHtml);

        // Add filter event listeners
        ['critical', 'warning', 'info'].forEach(function(type) {
            var el = document.getElementById('filter-' + type);
            if (el) el.addEventListener('change', loadAlertsView);
        });
    }

    // Get filter states
    var showCritical = document.getElementById('filter-critical') ? document.getElementById('filter-critical').checked : true;
    var showWarning = document.getElementById('filter-warning') ? document.getElementById('filter-warning').checked : true;
    var showInfo = document.getElementById('filter-info') ? document.getElementById('filter-info').checked : false;

    fetch("/api/alerts?limit=50")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var alerts = (data.alerts || []).filter(function(a) {
                var tier = (a.severity || 'INFO').toUpperCase();
                if (tier === 'CRITICAL' && !showCritical) return false;
                if (tier === 'WARNING' && !showWarning) return false;
                if ((tier === 'INFO' || tier === 'FYI' || tier === 'ACTION_REQUIRED') && !showInfo) return false;
                return true;
            });

            var html = '<div class="alerts-summary">';
            var critCount = (data.alerts || []).filter(function(a) { return (a.severity || '').toUpperCase() === 'CRITICAL'; }).length;
            var warnCount = (data.alerts || []).filter(function(a) { return (a.severity || '').toUpperCase() === 'WARNING'; }).length;
            var infoCount = (data.alerts || []).filter(function(a) { return ['INFO', 'FYI', 'ACTION_REQUIRED'].indexOf((a.severity || '').toUpperCase()) >= 0; }).length;

            html += '<span class="alert-count critical">' + critCount + ' Critical</span>';
            html += '<span class="alert-count warning">' + warnCount + ' Warning</span>';
            html += '<span class="alert-count info">' + infoCount + ' Info</span>';
            html += '</div>';

            html += '<div class="alerts-list">';
            alerts.forEach(function(alert) {
                var tierClass = (alert.severity || 'info').toLowerCase();
                html += '<div class="alert-item ' + tierClass + '">';
                html += '<span class="alert-tier">' + (alert.severity || 'INFO') + '</span>';
                html += '<span class="alert-title">' + escapeHtml(alert.title || alert.description || '') + '</span>';
                html += '<span class="alert-source">' + (alert.source || '') + '</span>';
                html += '</div>';
            });
            if (alerts.length === 0) {
                html += '<p class="no-data">No alerts matching filters</p>';
            }
            html += '</div>';

            container.innerHTML = html;
        })
        .catch(function(err) {
            container.innerHTML = '<p>Error loading alerts</p>';
        });
}'''


def main():
    # Backup
    backup_path = f"{JS_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(JS_FILE, backup_path)
    print(f"Backup created: {backup_path}")

    with open(JS_FILE, 'r') as f:
        content = f.read()

    # Find and replace loadTribeView function
    import re

    # Replace loadTribeView - find from function declaration to next function
    tribe_pattern = r'function loadTribeView\(\) \{[^}]+\{[^}]+\}[^}]+\}'
    if re.search(tribe_pattern, content):
        content = re.sub(tribe_pattern, NEW_TRIBE_VIEW, content, count=1)
        print("Replaced loadTribeView function")
    else:
        print("Could not find loadTribeView pattern, trying simpler replacement...")
        # Simpler approach - find the function and replace to the next function
        start = content.find('function loadTribeView()')
        if start >= 0:
            # Find the next function definition
            next_func = content.find('function load', start + 10)
            if next_func < 0:
                next_func = content.find('// Alerts View', start + 10)
            if next_func > start:
                content = content[:start] + NEW_TRIBE_VIEW + '\n\n' + content[next_func:]
                print("Replaced loadTribeView using position method")

    # Replace loadAlertsView - find from function declaration
    start = content.find('function loadAlertsView()')
    if start >= 0:
        # Find the next function definition
        next_func = content.find('function attach', start + 10)
        if next_func < 0:
            next_func = content.find('// Attach Configure', start + 10)
        if next_func > start:
            content = content[:start] + NEW_ALERTS_VIEW + '\n\n' + content[next_func:]
            print("Replaced loadAlertsView function")

    with open(JS_FILE, 'w') as f:
        f.write(content)

    print("Frontend updates complete!")

if __name__ == "__main__":
    main()
