// Events Triage Window — CRITICAL/IMPORTANT/FYI event management

(function() {
    const app = {
        id: 'events-triage',
        title: 'Events Triage',
        tags: ['events', 'alerts', 'triage', 'critical', 'operations'],
        _interval: null,
        _currentTier: 'all',

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
                width: savedPos?.width || 950,
                height: savedPos?.height || 600,
                x: savedPos?.x || 100,
                y: savedPos?.y || 60,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Event Triage</h3>
                    <div class="wc-filters">
                        <button class="wc-filter-btn active" data-tier="all">All</button>
                        <button class="wc-filter-btn crit" data-tier="CRITICAL">Critical</button>
                        <button class="wc-filter-btn warn" data-tier="IMPORTANT">Important</button>
                        <button class="wc-filter-btn info" data-tier="FYI">FYI</button>
                    </div>
                    <button class="wc-btn" onclick="AppRegistry.get('events-triage').refresh()">Refresh</button>
                </div>
                <div class="wc-stats" id="evt-stats"></div>
                <div class="wc-list" id="evt-list"><div class="wc-loading">Loading events...</div></div>
            </div>`;
        },

        async init() {
            // Wire filter buttons
            const body = WindowManager.getBody(this.id);
            if (body) {
                body.querySelectorAll('.wc-filter-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        body.querySelectorAll('.wc-filter-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        this._currentTier = btn.dataset.tier;
                        this.refresh();
                    });
                });
            }
            await this.loadStats();
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 15000);
        },

        async loadStats() {
            try {
                const stats = await FlowCore.api('/api/events/stats');
                const el = this._el('evt-stats');
                if (!el) return;
                const byTier = stats.by_tier || {};
                el.innerHTML = `
                    <div class="wc-stat"><span class="wc-stat-num crit">${byTier.CRITICAL || 0}</span><span class="wc-stat-label">Critical</span></div>
                    <div class="wc-stat"><span class="wc-stat-num warn">${byTier.IMPORTANT || 0}</span><span class="wc-stat-label">Important</span></div>
                    <div class="wc-stat"><span class="wc-stat-num info">${byTier.FYI || 0}</span><span class="wc-stat-label">FYI</span></div>
                    <div class="wc-stat"><span class="wc-stat-num">${stats.total || 0}</span><span class="wc-stat-label">Total</span></div>
                `;
            } catch (e) { /* stats are optional */ }
        },

        async refresh() {
            try {
                const tier = this._currentTier === 'all' ? '' : `?tier=${this._currentTier}`;
                const data = await FlowCore.api(`/api/events${tier}`);
                this.renderEvents(data.events || []);
            } catch (e) {
                const list = this._el('evt-list');
                if (list) list.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        renderEvents(events) {
            const list = this._el('evt-list');
            if (!list) return;
            if (!events.length) {
                list.innerHTML = '<div class="wc-empty">No events matching filter</div>';
                return;
            }
            list.innerHTML = events.map(evt => {
                const tier = (evt.tier || 'FYI').toUpperCase();
                const tierClass = tier === 'CRITICAL' ? 'crit' : tier === 'IMPORTANT' ? 'warn' : 'info';
                const reviewed = evt.reviewed ? ' reviewed' : '';
                const time = evt.created_at ? new Date(evt.created_at).toLocaleString() : '';
                return `<div class="wc-event-row${reviewed}">
                    <span class="wc-tier-badge ${tierClass}">${tier}</span>
                    <div class="wc-event-content">
                        <div class="wc-event-title">${evt.ticket_number || ''} ${evt.title || 'Untitled'}</div>
                        <div class="wc-event-meta">${evt.category || ''} &middot; ${time}</div>
                    </div>
                    <div class="wc-event-actions">
                        ${!evt.reviewed ? `<button class="wc-btn-sm" onclick="AppRegistry.get('events-triage').reviewEvent(${evt.id})">Review</button>` : '<span class="wc-muted">Reviewed</span>'}
                        <button class="wc-btn-sm" onclick="AppRegistry.get('events-triage').createTicket(${evt.id})">Ticket</button>
                        <button class="wc-btn-sm warn" onclick="AppRegistry.get('events-triage').dismissEvent(${evt.id})">Dismiss</button>
                    </div>
                </div>`;
            }).join('');
        },

        async reviewEvent(id) {
            try {
                await FlowCore.api(`/api/events/${id}/review`, { method: 'POST' });
                this.refresh();
            } catch (e) { console.error('Review failed:', e); }
        },

        async createTicket(id) {
            try {
                const result = await FlowCore.api(`/api/events/${id}/create-ticket`, { method: 'POST' });
                alert(`Ticket #${result.ticket_id} created`);
            } catch (e) { console.error('Ticket creation failed:', e); }
        },

        async dismissEvent(id) {
            try {
                await FlowCore.api(`/api/events/${id}/dismiss`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: 'Dismissed from Command Center', dismissed_by: 'operator' })
                });
                this.refresh();
            } catch (e) { console.error('Dismiss failed:', e); }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
