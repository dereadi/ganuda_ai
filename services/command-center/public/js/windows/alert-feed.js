// Alert Feed Window — real-time WebSocket alerts + REST fallback

(function() {
    const MAX_ALERTS = 100;

    const app = {
        id: 'alert-feed',
        title: 'Alert Feed',
        tags: ['alerts', 'feed', 'real-time', 'websocket', 'fire-guard'],
        _interval: null,
        _alerts: [],

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
                width: savedPos?.width || 500,
                height: savedPos?.height || 600,
                x: savedPos?.x || 'right',
                y: savedPos?.y || 30,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Live Alerts</h3>
                    <span class="wc-muted" id="alert-count">0 alerts</span>
                    <button class="wc-btn" onclick="AppRegistry.get('alert-feed').clearAlerts()">Clear</button>
                </div>
                <div class="wc-list" id="alert-list"><div class="wc-empty">Waiting for alerts...</div></div>
            </div>`;
        },

        async init() {
            // Load recent alerts from REST
            try {
                const data = await FlowCore.api('/api/alerts?limit=30');
                (data.alerts || []).reverse().forEach(a => this.addAlert(a));
            } catch (e) { /* no initial alerts, that's ok */ }

            // Also try sidebar alerts (thermal-based)
            try {
                const sidebar = await FlowCore.api('/api/sidebar/alerts');
                (sidebar.alerts || []).forEach(a => this.addAlert({
                    title: a.title,
                    severity: a.severity,
                    created_at: a.timestamp,
                    description: a.message
                }));
            } catch (e) { /* optional */ }

            // Poll for new alerts every 30s as fallback
            this._interval = setInterval(async () => {
                try {
                    const data = await FlowCore.api('/api/alerts?limit=5');
                    (data.alerts || []).forEach(a => {
                        if (!this._alerts.find(existing => existing.id === a.id)) {
                            this.addAlert(a);
                        }
                    });
                } catch (e) { /* silent */ }
            }, 30000);
        },

        // Called by AppRegistry.broadcast when WebSocket redis_message arrives
        onMessage(type, data) {
            if (type === 'redis_message' && data.channel === 'jr_alerts') {
                this.addAlert({
                    title: data.data || 'Alert',
                    severity: 'warning',
                    created_at: new Date().toISOString(),
                    source: 'websocket'
                });
            }
        },

        addAlert(alert) {
            this._alerts.unshift(alert);
            if (this._alerts.length > MAX_ALERTS) this._alerts.pop();
            this.renderAlerts();
        },

        clearAlerts() {
            this._alerts = [];
            this.renderAlerts();
        },

        renderAlerts() {
            const list = this._el('alert-list');
            const count = this._el('alert-count');
            if (!list) return;
            if (count) count.textContent = `${this._alerts.length} alerts`;

            if (!this._alerts.length) {
                list.innerHTML = '<div class="wc-empty">No alerts</div>';
                return;
            }

            list.innerHTML = this._alerts.map(a => {
                const sev = (a.severity || 'info').toLowerCase();
                const sevClass = sev === 'critical' ? 'crit' : sev === 'warning' ? 'warn' : 'info';
                const time = a.created_at ? new Date(a.created_at).toLocaleTimeString() : '';
                return `<div class="wc-alert-row ${sevClass}">
                    <div class="wc-alert-header">
                        <span class="wc-tier-badge ${sevClass}">${sev.toUpperCase()}</span>
                        <span class="wc-muted">${time}</span>
                    </div>
                    <div class="wc-alert-title">${a.title || ''}</div>
                    ${a.description ? `<div class="wc-alert-desc">${a.description}</div>` : ''}
                </div>`;
            }).join('');
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
