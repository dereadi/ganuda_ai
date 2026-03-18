// Daily Briefing Window — markets, solar, weather at a glance

(function() {
    const app = {
        id: 'daily-briefing',
        title: 'Daily Briefing',
        tags: ['briefing', 'markets', 'solar', 'weather', 'dawn', 'mist'],

        open(savedPos) {
            if (WindowManager.exists(this.id)) {
                WindowManager.focus(this.id);
                return;
            }
            WindowManager.create({
                id: this.id,
                title: this.title,
                width: savedPos?.width || 620,
                height: savedPos?.height || 480,
                x: savedPos?.x || 'center',
                y: savedPos?.y || 'center',
                html: '<div class="wc-pad"><div class="wc-loading">Loading briefing...</div></div>',
                onclose: () => {}
            });
            this.load();
        },

        async load() {
            const body = WindowManager.getBody(this.id);
            if (!body) return;
            try {
                const data = await FlowCore.api('/api/briefing');
                const m = data.market || {};
                const s = data.solar || {};
                const w = data.weather || {};

                body.querySelector('.wc-pad').innerHTML = `
                    <h3 class="wc-heading">Dawn Mist — Daily Briefing</h3>

                    <div class="wc-stats" style="margin-top:12px">
                        ${this.marketStat(m.oil, 'Oil (WTI)', '$')}
                        ${this.marketStat(m.gold, 'Gold', '$')}
                        ${this.marketStat(m.vix, 'VIX')}
                        ${this.marketStat(m.dxy, 'DXY')}
                        ${this.kpStat(s.kp_index)}
                    </div>

                    ${s.storm_level || s.alerts?.length ? `<div class="wc-card" style="margin-top:12px">
                        <strong>Space Weather</strong>
                        <div class="wc-meta">Storm Level: ${s.storm_level || 'Unknown'} &middot; Kp ${s.kp_index || '--'}</div>
                        ${s.alerts?.length ? `<div style="color:var(--warn);margin-top:4px;font-size:12px">${s.alerts.length} active alert${s.alerts.length > 1 ? 's' : ''}</div>` : ''}
                    </div>` : ''}

                    ${this.weatherCards(w)}
                `;
            } catch (e) {
                body.querySelector('.wc-pad').innerHTML = `<div class="wc-error">Briefing unavailable: ${e.message}</div>`;
            }
        },

        marketStat(item, label, prefix) {
            if (!item) return '';
            const price = item.price ?? item;
            const change = item.change_pct;
            let changeHtml = '';
            if (change !== undefined) {
                const cls = change > 0 ? 'good' : change < 0 ? 'crit' : '';
                const sign = change > 0 ? '+' : '';
                changeHtml = ` <span class="${cls}" style="font-size:11px">${sign}${change.toFixed(1)}%</span>`;
            }
            return `<div class="wc-stat"><span class="wc-stat-num">${prefix || ''}${typeof price === 'number' ? price.toLocaleString() : price}${changeHtml}</span><span class="wc-stat-label">${label}</span></div>`;
        },

        weatherCard(w) {
            if (!w || w.error) return `<div class="wc-muted">${w?.location || 'Weather'}: ${w?.error || 'unavailable'}</div>`;
            return `<div class="wc-card" style="margin-top:12px">
                <strong>Weather — ${w.location}</strong>
                ${(w.periods || []).map(p => `
                    <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border)">
                        <span style="color:var(--text-secondary)">${p.name}</span>
                        <span><strong>${p.temp}°${p.unit || 'F'}</strong> &middot; ${p.forecast}</span>
                    </div>
                `).join('')}
            </div>`;
        },

        weatherCards(w) {
            if (!w) return '';
            if (w.locations) return w.locations.map(loc => this.weatherCard(loc)).join('');
            return this.weatherCard(w);
        },

        kpStat(kp) {
            if (kp === undefined || kp === null) return '';
            const cls = kp >= 5 ? 'crit' : kp >= 3 ? 'warn' : 'good';
            return `<div class="wc-stat"><span class="wc-stat-num ${cls}">${kp}</span><span class="wc-stat-label">Kp Index</span></div>`;
        },

        cleanup() {}
    };

    AppRegistry.register(app);
})();
