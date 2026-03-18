// Email Intelligence Window — prioritized emails with draft/send/discard

(function() {
    const app = {
        id: 'email-intel',
        title: 'Email Intelligence',
        tags: ['email', 'gmail', 'intelligence', 'inbox', 'draft'],
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
                height: savedPos?.height || 600,
                x: savedPos?.x || 120,
                y: savedPos?.y || 50,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Email Intelligence</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('email-intel').refresh()">Refresh</button>
                </div>
                <div class="wc-split" id="email-split">
                    <div class="wc-email-list" id="email-list"><div class="wc-loading">Loading...</div></div>
                    <div class="wc-email-detail" id="email-detail">
                        <div class="wc-empty">Select an email</div>
                    </div>
                </div>
            </div>`;
        },

        async init() {
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 60000);
        },

        async refresh() {
            try {
                const data = await FlowCore.api('/api/emails?limit=30');
                this.renderList(data.emails || data || []);
            } catch (e) {
                const el = this._el('email-list');
                if (el) el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        renderList(emails) {
            const el = this._el('email-list');
            if (!el) return;
            if (!emails.length) {
                el.innerHTML = '<div class="wc-empty">No emails</div>';
                return;
            }
            el.innerHTML = emails.map(em => {
                const priority = em.priority || em.tier || 'normal';
                const cls = priority === 'high' || priority === 'CRITICAL' ? 'crit'
                          : priority === 'medium' || priority === 'IMPORTANT' ? 'warn' : 'info';
                return `<div class="wc-email-item" onclick="AppRegistry.get('email-intel').selectEmail(${em.id})">
                    <div class="wc-email-from">${em.sender || em.from_addr || 'Unknown'}</div>
                    <div class="wc-email-subject">${em.subject || 'No subject'}</div>
                    <div class="wc-email-meta">
                        <span class="wc-tier-badge ${cls}">${priority}</span>
                        <span class="wc-muted">${em.received_at || em.date || ''}</span>
                    </div>
                </div>`;
            }).join('');
        },

        async selectEmail(id) {
            const el = this._el('email-detail');
            if (!el) return;
            try {
                const em = await FlowCore.api(`/api/emails/${id}`);
                el.innerHTML = `
                    <div class="wc-email-header">
                        <strong>${em.subject || 'No subject'}</strong>
                        <div class="wc-muted">From: ${em.sender || em.from_addr || ''}</div>
                        <div class="wc-muted">Date: ${em.received_at || em.date || ''}</div>
                    </div>
                    <div class="wc-email-body">${em.body || em.content || ''}</div>
                    ${em.draft_response ? `
                        <div class="wc-email-draft">
                            <h4 class="wc-heading">Draft Response</h4>
                            <div class="wc-email-draft-text">${em.draft_response}</div>
                            <div class="wc-email-draft-actions">
                                <button class="wc-btn" onclick="AppRegistry.get('email-intel').sendDraft(${id})">Send</button>
                                <button class="wc-btn-sm" onclick="AppRegistry.get('email-intel').regenerateDraft(${id})">Regenerate</button>
                                <button class="wc-btn-sm warn" onclick="AppRegistry.get('email-intel').discardDraft(${id})">Discard</button>
                            </div>
                        </div>
                    ` : ''}
                `;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async sendDraft(id) {
            if (!confirm('Send this reply?')) return;
            try {
                await FlowCore.api(`/api/emails/${id}/send`, { method: 'POST' });
                this.refresh();
                this._el('email-detail').innerHTML = '<div class="wc-empty">Sent</div>';
            } catch (e) { alert('Send failed: ' + e.message); }
        },

        async regenerateDraft(id) {
            try {
                await FlowCore.api(`/api/emails/${id}/draft`, { method: 'POST' });
                this.selectEmail(id);
            } catch (e) { alert('Regenerate failed: ' + e.message); }
        },

        async discardDraft(id) {
            try {
                await FlowCore.api(`/api/emails/${id}/discard`, { method: 'POST' });
                this.selectEmail(id);
            } catch (e) { alert('Discard failed: ' + e.message); }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
