// Window Manager — WinBox wrapper with taskbar integration and layout persistence

const WindowManager = {
    _windows: {},

    create(opts) {
        const id = opts.id;
        if (this._windows[id]) {
            this._windows[id].focus();
            return this._windows[id];
        }

        const win = new WinBox({
            title: opts.title || id,
            width: opts.width || 800,
            height: opts.height || 500,
            x: opts.x || 'center',
            y: opts.y || 'center',
            top: 56,      // below header
            bottom: 44,    // above taskbar
            html: opts.html || '',
            class: ['cc-window'],
            onclose: () => {
                delete this._windows[id];
                this._removeTaskbarItem(id);
                this.saveLayout();
                if (opts.onclose) opts.onclose();
                return false; // let WinBox handle DOM removal
            },
            onfocus: () => {
                this._highlightTaskbarItem(id, true);
            },
            onblur: () => {
                this._highlightTaskbarItem(id, false);
            },
            onminimize: () => {
                this._highlightTaskbarItem(id, false);
                return false;
            }
        });

        this._windows[id] = win;
        this._addTaskbarItem(id, opts.title || id);
        this.saveLayout();
        return win;
    },

    exists(id) {
        return !!this._windows[id];
    },

    focus(id) {
        if (this._windows[id]) this._windows[id].focus();
    },

    close(id) {
        if (this._windows[id]) this._windows[id].close();
    },

    getBody(id) {
        if (!this._windows[id]) return null;
        return this._windows[id].body;
    },

    // Taskbar integration
    _addTaskbarItem(id, title) {
        const bar = document.getElementById('taskbar-windows');
        if (!bar) return;
        const btn = document.createElement('button');
        btn.className = 'cc-taskbar-window active';
        btn.dataset.windowId = id;
        btn.textContent = title.length > 20 ? title.substring(0, 18) + '...' : title;
        btn.onclick = () => {
            const win = this._windows[id];
            if (!win) return;
            if (win.min) {
                win.minimize(false);
                win.focus();
            } else {
                win.minimize(true);
            }
        };
        bar.appendChild(btn);
    },

    _removeTaskbarItem(id) {
        const bar = document.getElementById('taskbar-windows');
        if (!bar) return;
        const btn = bar.querySelector(`[data-window-id="${id}"]`);
        if (btn) btn.remove();
    },

    _highlightTaskbarItem(id, active) {
        const bar = document.getElementById('taskbar-windows');
        if (!bar) return;
        const btn = bar.querySelector(`[data-window-id="${id}"]`);
        if (btn) btn.classList.toggle('active', active);
    },

    // Layout persistence
    saveLayout() {
        const layout = {};
        Object.entries(this._windows).forEach(([id, win]) => {
            layout[id] = {
                x: win.x, y: win.y,
                width: win.width, height: win.height,
                open: true
            };
        });
        try {
            localStorage.setItem('cc-layout', JSON.stringify(layout));
        } catch (e) { /* quota exceeded, ignore */ }
    },

    restoreLayout() {
        try {
            const layout = JSON.parse(localStorage.getItem('cc-layout') || '{}');
            Object.entries(layout).forEach(([id, pos]) => {
                if (pos.open) {
                    const app = AppRegistry.get(id);
                    if (app && app.open) app.open(pos);
                }
            });
        } catch (e) { /* corrupt data, ignore */ }
    }
};
