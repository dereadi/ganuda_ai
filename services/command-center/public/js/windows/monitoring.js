// Monitoring Window — system metrics + service health

(function() {
    const app = {
        id: 'monitoring',
        title: 'Monitoring',
        tags: ['monitoring', 'metrics', 'cpu', 'ram', 'disk', 'health'],
        _interval: null,

        _el(id) {
            const body = WindowManager.getBody(this.id);
            return body ? body.querySelector('#' + id) : null;
        },

        open(savedPos) {
            if (WindowManager.exists(this.id)) {
                WindowManager.focus(this.id);
                return;
            }
            WindowManager.create({
                id: this.id,
                title: this.title,
                width: savedPos?.width || 800,
                height: savedPos?.height || 500,
                x: savedPos?.x || 100,
                y: savedPos?.y || 80,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">System Monitoring</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('monitoring').refresh()">Refresh</button>
                </div>
                <div id="mon-metrics" class="wc-stats"></div>
                <h4 class="wc-heading" style="margin-top:16px">Service Health</h4>
                <div id="mon-services" class="wc-list"><div class="wc-loading">Loading...</div></div>
            </div>`;
        },

        async init() {
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 15000);
        },

        async refresh() {
            await Promise.all([this.loadMetrics(), this.loadServices()]);
        },

        async loadMetrics() {
            try {
                const data = await FlowCore.api('/api/system/metrics');
                const el = this._el('mon-metrics');
                if (!el) return;
                el.innerHTML = `
                    <div class="wc-stat"><span class="wc-stat-num ${data.cpu_percent > 80 ? 'crit' : data.cpu_percent > 60 ? 'warn' : 'good'}">${data.cpu_percent || '--'}%</span><span class="wc-stat-label">CPU</span></div>
                    <div class="wc-stat"><span class="wc-stat-num ${data.ram_percent > 80 ? 'crit' : data.ram_percent > 60 ? 'warn' : 'good'}">${data.ram_percent || '--'}%</span><span class="wc-stat-label">RAM</span></div>
                    <div class="wc-stat"><span class="wc-stat-num">${data.ram_used_gb || '--'} GB</span><span class="wc-stat-label">RAM Used</span></div>
                    <div class="wc-stat"><span class="wc-stat-num">${data.ram_total_gb || '--'} GB</span><span class="wc-stat-label">RAM Total</span></div>
                    ${data.disk_percent ? `<div class="wc-stat"><span class="wc-stat-num ${data.disk_percent > 85 ? 'crit' : 'good'}">${data.disk_percent}%</span><span class="wc-stat-label">Disk</span></div>` : ''}
                `;
            } catch (e) { /* optional */ }
        },

        async loadServices() {
            try {
                const data = await FlowCore.api('/api/monitoring/overview');
                const el = this._el('mon-services');
                if (!el) return;
                const services = data.services || [];
                if (!services.length) {
                    el.innerHTML = `<div class="wc-stats">
                        ${data.thermal_count ? `<div class="wc-stat"><span class="wc-stat-num">${data.thermal_count}</span><span class="wc-stat-label">Thermals</span></div>` : ''}
                        ${data.council_votes ? `<div class="wc-stat"><span class="wc-stat-num">${data.council_votes}</span><span class="wc-stat-label">Council Votes</span></div>` : ''}
                    </div>`;
                    return;
                }
                el.innerHTML = services.map(s => {
                    const cls = s.status === 'healthy' ? 'good' : s.status === 'degraded' ? 'warn' : 'crit';
                    return `<div class="wc-event-row">
                        <span class="wc-dot ${cls}"></span>
                        <div class="wc-event-content">
                            <div class="wc-event-title">${s.name}</div>
                            <div class="wc-event-meta">${s.url || ''} &middot; ${s.response_time_ms ? s.response_time_ms + 'ms' : ''}</div>
                        </div>
                        <span class="wc-badge-sm ${cls}">${(s.status || '').toUpperCase()}</span>
                    </div>`;
                }).join('');
            } catch (e) {
                const el = this._el('mon-services');
                if (el) el.innerHTML = `<div class="wc-error">${e.message}</div>`;
            }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
