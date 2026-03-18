// Chat Window — multi-turn conversation via gateway with session persistence

(function() {
    const GATEWAY_URL = 'http://192.168.132.223:8080';

    const app = {
        id: 'chat',
        title: 'Cherokee Chat',
        tags: ['chat', 'conversation', 'ai', 'gateway', 'llm'],
        _sessionId: null,
        _sessions: [],
        _messages: [],
        _sending: false,

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
                width: savedPos?.width || 700,
                height: savedPos?.height || 600,
                x: savedPos?.x || 'center',
                y: savedPos?.y || 'center',
                html: this.render(),
                onclose: () => {}
            });
            this.init();
        },

        render() {
            return `<div class="wc-chat-container">
                <div class="wc-chat-sidebar" id="chat-sidebar">
                    <button class="wc-btn" style="width:100%;margin-bottom:8px" onclick="AppRegistry.get('chat').newSession()">+ New Chat</button>
                    <div id="chat-session-list" class="wc-chat-sessions"></div>
                </div>
                <div class="wc-chat-main">
                    <div class="wc-chat-messages" id="chat-messages">
                        <div class="wc-empty">Start a conversation</div>
                    </div>
                    <div class="wc-chat-input-area">
                        <textarea id="chat-input" class="wc-chat-input" rows="2"
                                  placeholder="Ask Cherokee AI..."
                                  onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();AppRegistry.get('chat').send()}"></textarea>
                        <button class="wc-btn wc-chat-send" id="chat-send-btn" onclick="AppRegistry.get('chat').send()">Send</button>
                    </div>
                </div>
            </div>`;
        },

        async init() {
            await this.loadSessions();
            // Auto-create a session if none exist
            if (!this._sessions.length) {
                await this.newSession();
            } else {
                // Select most recent
                await this.selectSession(this._sessions[0].id);
            }
        },

        async loadSessions() {
            try {
                const resp = await fetch(GATEWAY_URL + '/v1/sessions');
                if (resp.ok) {
                    const data = await resp.json();
                    this._sessions = data.sessions || data || [];
                }
            } catch (e) {
                // Sessions endpoint may not exist yet — use localStorage fallback
                this._sessions = JSON.parse(localStorage.getItem('cc-chat-sessions') || '[]');
            }
            this.renderSessionList();
        },

        renderSessionList() {
            const el = this._el('chat-session-list');
            if (!el) return;
            el.innerHTML = this._sessions.map(s => {
                const active = s.id === this._sessionId ? ' active' : '';
                const name = s.name || 'Chat ' + (s.id || '').substring(0, 8);
                return `<div class="wc-chat-session-item${active}" onclick="AppRegistry.get('chat').selectSession('${s.id}')">
                    <span>${name}</span>
                    <button class="wc-chat-delete" onclick="event.stopPropagation();AppRegistry.get('chat').deleteSession('${s.id}')">&times;</button>
                </div>`;
            }).join('') || '<div class="wc-muted" style="padding:8px">No sessions</div>';
        },

        async newSession() {
            try {
                const resp = await fetch(GATEWAY_URL + '/v1/sessions', { method: 'POST' });
                if (resp.ok) {
                    const data = await resp.json();
                    this._sessionId = data.session_id || data.id;
                    await this.loadSessions();
                    this._messages = [];
                    this.renderMessages();
                    return;
                }
            } catch (e) { /* fallback below */ }

            // Fallback: local session
            const id = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36);
            const session = { id, name: 'New Chat', created_at: new Date().toISOString() };
            this._sessions.unshift(session);
            this._sessionId = id;
            this._messages = [];
            localStorage.setItem('cc-chat-sessions', JSON.stringify(this._sessions));
            this.renderSessionList();
            this.renderMessages();
        },

        async selectSession(id) {
            this._sessionId = id;
            this.renderSessionList();
            // Load message history
            try {
                const resp = await fetch(GATEWAY_URL + `/v1/sessions/${id}/messages`);
                if (resp.ok) {
                    const data = await resp.json();
                    this._messages = data.messages || data || [];
                    this.renderMessages();
                    return;
                }
            } catch (e) { /* fallback */ }
            // Fallback: local messages
            this._messages = JSON.parse(localStorage.getItem(`cc-chat-${id}`) || '[]');
            this.renderMessages();
        },

        async deleteSession(id) {
            if (!confirm('Delete this chat session?')) return;
            try {
                await fetch(GATEWAY_URL + `/v1/sessions/${id}`, { method: 'DELETE' });
            } catch (e) { /* local fallback */ }
            this._sessions = this._sessions.filter(s => s.id !== id);
            localStorage.setItem('cc-chat-sessions', JSON.stringify(this._sessions));
            localStorage.removeItem(`cc-chat-${id}`);
            if (this._sessionId === id) {
                this._sessionId = null;
                this._messages = [];
                this.renderMessages();
            }
            this.renderSessionList();
        },

        async send() {
            if (this._sending) return;
            const input = this._el('chat-input');
            if (!input || !input.value.trim()) return;
            const text = input.value.trim();
            input.value = '';

            // Add user message
            this._messages.push({ role: 'user', content: text });
            this.renderMessages();
            this.scrollToBottom();

            this._sending = true;
            const btn = this._el('chat-send-btn');
            if (btn) { btn.textContent = '...'; btn.disabled = true; }

            try {
                const body = {
                    messages: this._messages.map(m => ({ role: m.role, content: m.content })),
                    model: 'default'
                };
                if (this._sessionId) body.session_id = this._sessionId;

                const resp = await fetch(GATEWAY_URL + '/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (resp.ok) {
                    const data = await resp.json();
                    const reply = data.choices?.[0]?.message?.content || data.content || data.response || 'No response';
                    this._messages.push({ role: 'assistant', content: reply });
                } else {
                    const err = await resp.text();
                    this._messages.push({ role: 'assistant', content: `Error ${resp.status}: ${err}` });
                }
            } catch (e) {
                this._messages.push({ role: 'assistant', content: `Connection failed: ${e.message}` });
            }

            // Save locally as fallback
            if (this._sessionId) {
                localStorage.setItem(`cc-chat-${this._sessionId}`, JSON.stringify(this._messages));
            }

            this._sending = false;
            if (btn) { btn.textContent = 'Send'; btn.disabled = false; }
            this.renderMessages();
            this.scrollToBottom();
        },

        renderMessages() {
            const el = this._el('chat-messages');
            if (!el) return;
            if (!this._messages.length) {
                el.innerHTML = '<div class="wc-empty">Start a conversation</div>';
                return;
            }
            el.innerHTML = this._messages.map(m => {
                const cls = m.role === 'user' ? 'wc-chat-msg-user' : 'wc-chat-msg-assistant';
                const label = m.role === 'user' ? 'You' : 'Cherokee AI';
                return `<div class="${cls}">
                    <div class="wc-chat-msg-label">${label}</div>
                    <div class="wc-chat-msg-content">${this.formatContent(m.content)}</div>
                </div>`;
            }).join('');
        },

        formatContent(text) {
            // Basic markdown-ish rendering
            return text
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/```([\s\S]*?)```/g, '<pre class="wc-chat-code">$1</pre>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
        },

        scrollToBottom() {
            const el = this._el('chat-messages');
            if (el) el.scrollTop = el.scrollHeight;
        },

        cleanup() {}
    };

    AppRegistry.register(app);
})();
