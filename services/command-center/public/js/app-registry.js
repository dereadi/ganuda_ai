// App Registry — central registration for all WinBox window apps
// Each app module calls AppRegistry.register() with its config

const AppRegistry = {
    _apps: {},

    register(app) {
        if (!app.id) throw new Error('App must have an id');
        this._apps[app.id] = app;
    },

    get(id) {
        return this._apps[id] || null;
    },

    getAll() {
        return Object.values(this._apps);
    },

    search(query) {
        const q = query.toLowerCase();
        return this.getAll().filter(app =>
            app.title.toLowerCase().includes(q) ||
            app.id.toLowerCase().includes(q) ||
            (app.tags || []).some(t => t.toLowerCase().includes(q))
        );
    },

    open(id) {
        const app = this.get(id);
        if (app && app.open) app.open();
    },

    // Broadcast a message to all open windows that have an onMessage handler
    broadcast(type, data) {
        this.getAll().forEach(app => {
            if (app.onMessage) app.onMessage(type, data);
        });
    }
};
