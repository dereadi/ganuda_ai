// Unified Messages Window — multi-platform messaging

(function() {
    const app = {
        id: 'messages',
        title: 'Messages',
        tags: ['messages', 'telegram', 'slack', 'discord', 'sms', 'chat', 'messaging'],

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
                width: savedPos?.width || 750,
                height: savedPos?.height || 500,
                x: savedPos?.x || 160,
                y: savedPos?.y || 60,
                html: this.render(),
                onclose: () => {}
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Unified Messages</h3>
                </div>
                <div class="wc-split">
                    <div class="wc-msg-channels" id="msg-channels"><div class="wc-loading">Loading...</div></div>
                    <div class="wc-msg-thread" id="msg-thread"><div class="wc-empty">Select a channel</div></div>
                </div>
            </div>`;
        },

        async init() {
            // Messages endpoint may not return channels directly — render platform list
            const channels = [
                { id: 'telegram', name: 'Telegram', icon: '✈' },
                { id: 'slack', name: 'Slack', icon: '💬' },
                { id: 'discord', name: 'Discord', icon: '🎮' },
                { id: 'sms', name: 'SMS', icon: '📱' }
            ];
            const el = this._el('msg-channels');
            if (el) {
                el.innerHTML = channels.map(ch =>
                    `<div class="wc-msg-channel" onclick="AppRegistry.get('messages').selectChannel('${ch.id}')">
                        <span>${ch.icon}</span> ${ch.name}
                    </div>`
                ).join('');
            }
        },

        async selectChannel(channelId) {
            const el = this._el('msg-thread');
            if (!el) return;
            el.innerHTML = `<div class="wc-empty">Messages for ${channelId} — coming in Phase 3</div>`;
        },

        cleanup() {}
    };

    AppRegistry.register(app);
})();
