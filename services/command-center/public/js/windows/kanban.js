// Kanban Board Window — ticket management

(function() {
    const app = {
        id: 'kanban',
        title: 'Kanban Board',
        tags: ['kanban', 'tickets', 'tasks', 'board', 'operations'],
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
                width: savedPos?.width || 1000,
                height: savedPos?.height || 600,
                x: savedPos?.x || 80,
                y: savedPos?.y || 40,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Kanban Board</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('kanban').refresh()">Refresh</button>
                </div>
                <div class="wc-kanban-board" id="kanban-board"><div class="wc-loading">Loading...</div></div>
            </div>`;
        },

        async init() {
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 30000);
        },

        async refresh() {
            const el = this._el('kanban-board');
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/kanban/tickets');
                const tickets = data.tickets || data || [];
                const columns = {
                    'pending': [], 'assigned': [], 'in_progress': [],
                    'blocked': [], 'completed': [], 'other': []
                };
                tickets.forEach(t => {
                    const s = (t.status || 'other').toLowerCase();
                    (columns[s] || columns.other).push(t);
                });

                el.innerHTML = ['pending', 'assigned', 'in_progress', 'blocked', 'completed'].map(col => {
                    const items = columns[col];
                    const colClass = col === 'blocked' ? 'crit' : col === 'completed' ? 'good'
                                   : col === 'in_progress' ? 'warn' : '';
                    return `<div class="wc-kanban-col">
                        <div class="wc-kanban-col-header ${colClass}">
                            ${col.replace('_', ' ').toUpperCase()} (${items.length})
                        </div>
                        <div class="wc-kanban-col-body">
                            ${items.map(t => `
                                <div class="wc-kanban-card">
                                    <div class="wc-kanban-card-title">${t.title || t.ticket_number || 'Untitled'}</div>
                                    <div class="wc-muted">${t.category || t.priority || ''}</div>
                                    ${t.description ? `<div class="wc-meta" style="margin-top:4px">${t.description.substring(0, 80)}${t.description.length > 80 ? '...' : ''}</div>` : ''}
                                </div>
                            `).join('') || '<div class="wc-empty" style="padding:8px">Empty</div>'}
                        </div>
                    </div>`;
                }).join('');
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
