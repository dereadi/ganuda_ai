// Federation Status Window — live node health grid

(function() {
    const app = {
        id: 'federation-status',
        title: 'Federation Status',
        tags: ['federation', 'nodes', 'health', 'systems'],
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
                width: savedPos?.width || 900,
                height: savedPos?.height || 550,
                x: savedPos?.x || 50,
                y: savedPos?.y || 30,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Cherokee AI Federation</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('federation-status').refresh()">Refresh</button>
                </div>
                <div class="wc-stats" id="fed-stats"></div>
                <div class="wc-grid" id="fed-grid"><div class="wc-loading">Loading nodes...</div></div>
            </div>`;
        },

        async init() {
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 10000);
        },

        async refresh() {
            try {
                const data = await FlowCore.api('/api/federation/summary');
                this.renderStats(data);
                this.renderNodes(data.nodes || []);
            } catch (e) {
                const grid = this._el('fed-grid');
                if (grid) grid.innerHTML = `<div class="wc-error">Failed to load: ${e.message}</div>`;
            }
        },

        renderStats(data) {
            const el = this._el('fed-stats');
            if (!el) return;
            const status = data.federation_status || 'unknown';
            const statusClass = status === 'healthy' ? 'good' : status === 'degraded' ? 'warn' : 'crit';
            el.innerHTML = `
                <div class="wc-stat"><span class="wc-stat-num">${data.total_nodes || 0}</span><span class="wc-stat-label">Total</span></div>
                <div class="wc-stat"><span class="wc-stat-num good">${data.healthy || 0}</span><span class="wc-stat-label">Healthy</span></div>
                <div class="wc-stat"><span class="wc-stat-num warn">${data.degraded || 0}</span><span class="wc-stat-label">Degraded</span></div>
                <div class="wc-stat"><span class="wc-stat-num crit">${data.down || 0}</span><span class="wc-stat-label">Down</span></div>
                <div class="wc-stat"><span class="wc-stat-num ${statusClass}">${status.toUpperCase()}</span><span class="wc-stat-label">Federation</span></div>
            `;
        },

        renderNodes(nodes) {
            const grid = this._el('fed-grid');
            if (!grid) return;
            if (!nodes.length) {
                grid.innerHTML = '<div class="wc-empty">No nodes reported</div>';
                return;
            }
            grid.innerHTML = nodes.map(node => {
                const s = node.status || 'unknown';
                const borderClass = s === 'healthy' ? 'border-good' : s === 'degraded' ? 'border-warn' : 'border-crit';
                const services = (node.services || []).map(svc => {
                    const sc = svc.status === 'healthy' ? 'good' : svc.status === 'degraded' ? 'warn' : 'crit';
                    const ms = svc.response_time_ms ? ` (${Math.round(svc.response_time_ms)}ms)` : '';
                    return `<div class="wc-svc"><span class="wc-dot ${sc}"></span> ${svc.name}:${svc.port}${ms}</div>`;
                }).join('');
                return `<div class="wc-card ${borderClass}">
                    <div class="wc-card-head">
                        <strong>${node.node_id}</strong>
                        <span class="wc-badge-sm ${s}">${s.toUpperCase()}</span>
                    </div>
                    <div class="wc-card-body">
                        <div class="wc-meta">${node.name || ''}</div>
                        <div class="wc-meta">${node.hostname || ''}</div>
                        <div class="wc-meta">${node.role || ''}</div>
                        <div class="wc-services">${services || '<span class="wc-muted">No services checked</span>'}</div>
                    </div>
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
