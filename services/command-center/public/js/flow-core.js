// Flow Core — boot sequence, spotlight search, clock, WebSocket, keyboard shortcuts

const FlowCore = {
    SAG_API: window.location.origin,  // SAG backend on same origin
    socket: null,

    boot() {
        this.initClock();
        this.initSpotlight();
        this.initLaunchers();
        this.initKeyboard();
        this.initWebSocket();
        this.checkFederationHealth();

        // Restore saved window layout
        WindowManager.restoreLayout();

        console.log('%c Cherokee AI Command Center ', 'background: #8B4513; color: #FFD700; font-size: 16px; padding: 4px 8px;');
    },

    // Clock
    initClock() {
        const update = () => {
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            const date = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const el = document.getElementById('clock');
            if (el) el.textContent = `${date} ${time}`;
            const tb = document.getElementById('taskbar-time');
            if (tb) tb.textContent = time;
        };
        update();
        setInterval(update, 30000);
    },

    // Spotlight search
    initSpotlight() {
        const input = document.getElementById('spotlight-search');
        const results = document.getElementById('spotlight-results');
        if (!input || !results) return;

        input.addEventListener('input', () => {
            const q = input.value.trim();
            if (!q) {
                results.style.display = 'none';
                return;
            }
            const matches = AppRegistry.search(q);
            if (matches.length === 0) {
                results.innerHTML = '<div class="cc-spotlight-item muted">No matches</div>';
            } else {
                results.innerHTML = matches.map(app =>
                    `<div class="cc-spotlight-item" data-app="${app.id}">${app.title}</div>`
                ).join('');
            }
            results.style.display = 'block';
        });

        results.addEventListener('click', (e) => {
            const item = e.target.closest('[data-app]');
            if (item) {
                AppRegistry.open(item.dataset.app);
                input.value = '';
                results.style.display = 'none';
            }
        });

        input.addEventListener('blur', () => {
            setTimeout(() => { results.style.display = 'none'; }, 200);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                input.value = '';
                results.style.display = 'none';
                input.blur();
            }
            if (e.key === 'Enter') {
                const first = results.querySelector('[data-app]');
                if (first) {
                    AppRegistry.open(first.dataset.app);
                    input.value = '';
                    results.style.display = 'none';
                }
            }
        });
    },

    // Taskbar launcher buttons
    initLaunchers() {
        document.querySelectorAll('.cc-launcher[data-app]').forEach(btn => {
            btn.addEventListener('click', () => {
                AppRegistry.open(btn.dataset.app);
            });
        });
    },

    // Keyboard shortcuts
    initKeyboard() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Space — focus spotlight
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                const input = document.getElementById('spotlight-search');
                if (input) input.focus();
            }
        });
    },

    // WebSocket for real-time alerts
    initWebSocket() {
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not loaded — real-time alerts disabled');
            return;
        }
        try {
            this.socket = io(this.SAG_API, { transports: ['websocket', 'polling'] });
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.updateBadge('Connected', true);
            });
            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.updateBadge('Disconnected', false);
            });
            this.socket.on('redis_message', (data) => {
                AppRegistry.broadcast('redis_message', data);
            });
        } catch (e) {
            console.warn('WebSocket init failed:', e.message);
        }
    },

    // Federation health badge
    async checkFederationHealth() {
        try {
            const resp = await fetch(this.SAG_API + '/api/federation/summary');
            const data = await resp.json();
            const healthy = data.healthy || 0;
            const total = data.total_nodes || 0;
            this.updateBadge(`${healthy}/${total} Nodes`, data.federation_status === 'healthy');
        } catch (e) {
            this.updateBadge('Offline', false);
        }
        // Re-check every 30s
        setTimeout(() => this.checkFederationHealth(), 30000);
    },

    updateBadge(text, healthy) {
        const badge = document.getElementById('federation-badge-text');
        const dot = document.querySelector('.cc-badge-dot');
        if (badge) badge.textContent = text;
        if (dot) {
            dot.classList.toggle('healthy', healthy);
            dot.classList.toggle('unhealthy', !healthy);
        }
    },

    // Helper: fetch from SAG API
    async api(path, opts) {
        const resp = await fetch(this.SAG_API + path, opts);
        if (!resp.ok) throw new Error(`API ${resp.status}: ${path}`);
        return resp.json();
    }
};

// Boot on DOM ready
document.addEventListener('DOMContentLoaded', () => FlowCore.boot());
