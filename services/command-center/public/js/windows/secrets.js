// Secrets Management Window — reveal/edit/add with audit

(function() {
    const app = {
        id: 'secrets',
        title: 'Secrets Management',
        tags: ['secrets', 'credentials', 'keys', 'security', 'config'],
        _secrets: [],

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
                x: savedPos?.x || 200,
                y: savedPos?.y || 90,
                html: this.render(),
                onclose: () => {}
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Secrets</h3>
                    <select id="secrets-cat-filter" class="wc-input" onchange="AppRegistry.get('secrets').filterSecrets()">
                        <option value="all">All Categories</option>
                    </select>
                    <span class="wc-muted" id="secrets-info"></span>
                    <button class="wc-btn" onclick="AppRegistry.get('secrets').refresh()">Refresh</button>
                </div>
                <div id="secrets-table"><div class="wc-loading">Loading...</div></div>
            </div>`;
        },

        async init() {
            await this.refresh();
        },

        async refresh() {
            try {
                const data = await FlowCore.api('/api/secrets');
                this._secrets = data.secrets || [];
                const info = this._el('secrets-info');
                if (info) info.textContent = `${data.count || this._secrets.length} secrets in ${data.file || 'secrets.env'}`;

                // Populate category filter
                const cats = [...new Set(this._secrets.map(s => s.category))];
                const filter = this._el('secrets-cat-filter');
                if (filter) {
                    filter.innerHTML = '<option value="all">All Categories</option>' +
                        cats.map(c => `<option value="${c}">${c}</option>`).join('');
                }
                this.renderTable();
            } catch (e) {
                const el = this._el('secrets-table');
                if (el) el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        filterSecrets() {
            this.renderTable();
        },

        renderTable() {
            const el = this._el('secrets-table');
            if (!el) return;
            const filter = this._el('secrets-cat-filter')?.value || 'all';
            const filtered = filter === 'all' ? this._secrets : this._secrets.filter(s => s.category === filter);

            el.innerHTML = `<table class="wc-table">
                <thead><tr>
                    <th>Name</th><th>Category</th><th>Value</th><th>Actions</th>
                </tr></thead>
                <tbody>${filtered.map(s => `
                    <tr>
                        <td class="wc-mono">${s.name}</td>
                        <td><span class="wc-badge-sm">${s.category}</span></td>
                        <td class="wc-mono" id="sval-${s.name}">${s.masked}</td>
                        <td>
                            <button class="wc-btn-sm" onclick="AppRegistry.get('secrets').reveal('${s.name}')">Reveal</button>
                            <button class="wc-btn-sm" onclick="AppRegistry.get('secrets').edit('${s.name}')">Edit</button>
                        </td>
                    </tr>
                `).join('')}</tbody>
            </table>`;
        },

        async reveal(name) {
            try {
                const data = await FlowCore.api(`/api/secrets/${name}/reveal`);
                const body = WindowManager.getBody(this.id);
                const el = body?.querySelector('#sval-' + name);
                if (el) {
                    el.textContent = data.value;
                    el.style.color = 'var(--warn)';
                    setTimeout(() => {
                        const s = this._secrets.find(s => s.name === name);
                        if (el && s) { el.textContent = s.masked; el.style.color = ''; }
                    }, 5000);
                }
            } catch (e) { alert('Reveal failed: ' + e.message); }
        },

        edit(name) {
            const newVal = prompt(`New value for ${name}:`);
            if (newVal === null || !newVal.trim()) return;
            FlowCore.api(`/api/secrets/${name}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value: newVal.trim() })
            }).then(() => this.refresh())
              .catch(e => alert('Update failed: ' + e.message));
        },

        cleanup() {}
    };

    AppRegistry.register(app);
})();
