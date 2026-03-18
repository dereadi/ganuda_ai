// Tribe Council Window — council vote history + tribal awareness

(function() {
    const app = {
        id: 'tribe-council',
        title: 'Tribe Council',
        tags: ['tribe', 'council', 'votes', 'governance', 'awareness'],
        _interval: null,
        _currentTab: 'votes',

        open(savedPos) {
            if (WindowManager.exists(this.id)) {
                WindowManager.focus(this.id);
                return;
            }
            WindowManager.create({
                id: this.id,
                title: this.title,
                width: savedPos?.width || 900,
                height: savedPos?.height || 600,
                x: savedPos?.x || 140,
                y: savedPos?.y || 55,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Tribe Council</h3>
                    <div class="wc-filters">
                        <button class="wc-filter-btn active" data-tab="votes">Council Votes</button>
                        <button class="wc-filter-btn" data-tab="awareness">Tribal Awareness</button>
                        <button class="wc-filter-btn" data-tab="briefing">Daily Briefing</button>
                    </div>
                    <button class="wc-btn" onclick="AppRegistry.get('tribe-council').refresh()">Refresh</button>
                </div>
                <div id="tribe-content"><div class="wc-loading">Loading...</div></div>
            </div>`;
        },

        async init() {
            const body = WindowManager.getBody(this.id);
            if (body) {
                body.querySelectorAll('.wc-filter-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        body.querySelectorAll('.wc-filter-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        this._currentTab = btn.dataset.tab;
                        this.refresh();
                    });
                });
            }
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 30000);
        },

        async refresh() {
            if (this._currentTab === 'votes') await this.renderVotes();
            else if (this._currentTab === 'awareness') await this.renderAwareness();
            else if (this._currentTab === 'briefing') await this.renderBriefing();
        },

        _el() {
            const body = WindowManager.getBody(this.id);
            return body ? body.querySelector('#tribe-content') : null;
        },

        async renderVotes() {
            const el = this._el();
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/tribe/council-votes');
                const votes = data.votes || data || [];
                el.innerHTML = votes.length ? votes.map(v => {
                    const conf = v.confidence ? `${(v.confidence * 100).toFixed(0)}%` : '';
                    const rec = (v.recommendation || v.result || '').toUpperCase();
                    const cls = rec.includes('APPROVE') ? 'good' : rec.includes('REJECT') ? 'crit' : 'warn';
                    return `<div class="wc-card" style="margin-bottom:8px">
                        <div class="wc-card-head">
                            <strong>${v.vote_hash || v.id || ''}</strong>
                            <span class="wc-badge-sm ${cls}">${rec} ${conf}</span>
                        </div>
                        <div class="wc-event-title">${v.question || v.topic || ''}</div>
                        <div class="wc-muted">${v.created_at || v.voted_at || ''}</div>
                        ${v.specialists ? `<div class="wc-meta" style="margin-top:8px">${
                            Object.entries(v.specialists).map(([s, vote]) =>
                                `<span class="wc-badge-sm" style="margin:2px">${s}: ${vote.vote || vote}</span>`
                            ).join(' ')
                        }</div>` : ''}
                    </div>`;
                }).join('') : '<div class="wc-empty">No recent votes</div>';
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderAwareness() {
            const el = this._el();
            if (!el) return;
            try {
                // Pull from endpoints that actually exist
                const [federation, votes] = await Promise.allSettled([
                    FlowCore.api('/api/federation/nodes'),
                    FlowCore.api('/api/tribe/council-votes')
                ]);

                const nodes = federation.status === 'fulfilled' ? (federation.value.nodes || federation.value || []) : [];
                const recentVotes = votes.status === 'fulfilled' ? (votes.value.votes || votes.value || []).slice(0, 3) : [];

                el.innerHTML = `
                    <h4 class="wc-heading">Federation Nodes</h4>
                    <div class="wc-grid">${nodes.length ? nodes.map(n => {
                        const st = (n.status || 'unknown').toLowerCase();
                        const cls = st === 'healthy' || st === 'online' ? 'good' : st === 'degraded' ? 'warn' : 'crit';
                        return `<div class="wc-card" style="border-left:3px solid var(--${cls})">
                            <strong>${n.name || n.node_id || n.hostname || '?'}</strong>
                            <div class="wc-meta"><span class="wc-badge-sm ${st}">${st}</span></div>
                            ${n.role ? `<div class="wc-muted">${n.role}</div>` : ''}
                            ${n.ip ? `<div class="wc-muted" style="font-size:10px">${n.ip}</div>` : ''}
                        </div>`;
                    }).join('') : '<div class="wc-empty">No node data</div>'}</div>

                    <h4 class="wc-heading" style="margin-top:16px">Recent Council Activity</h4>
                    <div class="wc-list">${recentVotes.length ? recentVotes.map(v => {
                        const rec = (v.recommendation || v.result || '').toUpperCase();
                        const cls = rec.includes('APPROVE') ? 'good' : rec.includes('REJECT') ? 'crit' : 'warn';
                        return `<div class="wc-event-row">
                            <div class="wc-event-content">
                                <div class="wc-event-title">${v.question || v.topic || ''}</div>
                                <div class="wc-event-meta">
                                    <span class="wc-badge-sm ${cls}">${rec}</span>
                                    &middot; ${v.created_at || v.voted_at || ''}
                                </div>
                            </div>
                        </div>`;
                    }).join('') : '<div class="wc-empty">No recent votes</div>'}</div>
                `;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        _marketStat(item, label) {
            if (!item || item.error) return '';
            const chg = item.change_pct || 0;
            const color = chg > 0 ? 'good' : chg < 0 ? 'crit' : '';
            const arrow = chg > 0 ? '▲' : chg < 0 ? '▼' : '';
            const prefix = label === 'VIX' || label === 'Kp' || label === 'DXY' ? '' : '$';
            return `<div class="wc-stat">
                <span class="wc-stat-num">${prefix}${item.price}</span>
                <span class="wc-stat-label">${label} <span class="${color}">${arrow}${Math.abs(chg)}%</span></span>
            </div>`;
        },

        _weatherBlock(w) {
            if (!w || w.error) return `<div class="wc-muted">${w?.location || 'Weather'}: ${w?.error || 'unavailable'}</div>`;
            return `<div class="wc-card" style="margin-bottom:8px">
                <strong>${w.location}</strong>
                <table style="width:100%;margin-top:6px;font-size:12px;color:var(--text-secondary)">
                    ${(w.periods || []).map(p => `<tr>
                        <td style="padding:2px 8px 2px 0;white-space:nowrap"><strong>${p.name}</strong></td>
                        <td style="padding:2px 8px">${p.temp}°${p.unit || 'F'}</td>
                        <td style="padding:2px 0">${p.forecast}</td>
                    </tr>`).join('')}
                </table>
            </div>`;
        },

        async renderBriefing() {
            const el = this._el();
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/briefing');
                const m = data.market || {};
                const s = data.solar || {};
                const kp = s.kp_index;
                el.innerHTML = `
                    <div class="wc-stats">
                        ${this._marketStat(m.oil, 'Oil (WTI)')}
                        ${this._marketStat(m.gold, 'Gold')}
                        ${this._marketStat(m.vix, 'VIX')}
                        ${this._marketStat(m.dxy, 'DXY')}
                        ${kp !== undefined ? `<div class="wc-stat"><span class="wc-stat-num ${kp >= 5 ? 'crit' : kp >= 3 ? 'warn' : 'good'}">${kp}</span><span class="wc-stat-label">Kp Index</span></div>` : ''}
                    </div>
                    <h4 class="wc-heading" style="margin-top:12px">Weather</h4>
                    ${data.weather?.locations
                        ? data.weather.locations.map(w => this._weatherBlock(w)).join('')
                        : this._weatherBlock(data.weather)}
                `;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
