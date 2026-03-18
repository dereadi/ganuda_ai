// Command Console Window — mission dispatch + triad responses

(function() {
    const app = {
        id: 'console',
        title: 'Command Console',
        tags: ['console', 'command', 'dispatch', 'mission', 'triad'],
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
                height: savedPos?.height || 550,
                x: savedPos?.x || 180,
                y: savedPos?.y || 70,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Command Console</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('console').refresh()">Refresh</button>
                </div>
                <div class="wc-console-input">
                    <textarea id="console-mission" class="wc-textarea" rows="3"
                              placeholder="Describe mission for the triad..."></textarea>
                    <button class="wc-btn" onclick="AppRegistry.get('console').dispatch()">Dispatch Mission</button>
                </div>
                <h4 class="wc-heading" style="margin-top:16px">Recent Missions</h4>
                <div id="console-missions" class="wc-list"><div class="wc-loading">Loading...</div></div>
                <h4 class="wc-heading" style="margin-top:16px">Triad Responses</h4>
                <div id="console-responses" class="wc-list"><div class="wc-empty">No responses yet</div></div>
            </div>`;
        },

        async init() {
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 20000);
        },

        async refresh() {
            await Promise.all([this.loadMissions(), this.loadResponses()]);
        },

        async loadMissions() {
            try {
                const data = await FlowCore.api('/api/console/missions');
                const el = this._el('console-missions');
                if (!el) return;
                const missions = data.missions || data || [];
                if (!missions.length) {
                    el.innerHTML = '<div class="wc-empty">No missions dispatched</div>';
                    return;
                }
                el.innerHTML = missions.map(m => `
                    <div class="wc-event-row">
                        <span class="wc-tier-badge info">MISSION</span>
                        <div class="wc-event-content">
                            <div class="wc-event-title">${m.description || m.content || ''}</div>
                            <div class="wc-event-meta">${m.dispatched_at || m.created_at || ''} &middot; ${m.status || ''}</div>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                const el = this._el('console-missions');
                if (el) el.innerHTML = `<div class="wc-error">${e.message}</div>`;
            }
        },

        async loadResponses() {
            try {
                const data = await FlowCore.api('/api/console/responses');
                const el = this._el('console-responses');
                if (!el) return;
                const responses = data.responses || data || [];
                if (!responses.length) {
                    el.innerHTML = '<div class="wc-empty">No responses</div>';
                    return;
                }
                el.innerHTML = responses.map(r => `
                    <div class="wc-event-row">
                        <span class="wc-tier-badge good">RESPONSE</span>
                        <div class="wc-event-content">
                            <div class="wc-event-title">${r.content || r.message || ''}</div>
                            <div class="wc-event-meta">${r.from || r.agent || ''} &middot; ${r.created_at || ''}</div>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                const el = this._el('console-responses');
                if (el) el.innerHTML = `<div class="wc-error">${e.message}</div>`;
            }
        },

        async dispatch() {
            const textarea = this._el('console-mission');
            if (!textarea || !textarea.value.trim()) return;
            try {
                await FlowCore.api('/api/console/dispatch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mission: textarea.value.trim() })
                });
                textarea.value = '';
                this.refresh();
            } catch (e) { alert('Dispatch failed: ' + e.message); }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
