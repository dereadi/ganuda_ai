// Home & IoT Window — devices, Nest thermostat, security status

(function() {
    const app = {
        id: 'home-iot',
        title: 'Home & IoT',
        tags: ['home', 'iot', 'nest', 'thermostat', 'devices', 'hub'],
        _interval: null,
        _currentTab: 'dashboard',

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
                width: savedPos?.width || 850,
                height: savedPos?.height || 550,
                x: savedPos?.x || 200,
                y: savedPos?.y || 80,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Home & IoT</h3>
                    <div class="wc-filters">
                        <button class="wc-filter-btn active" data-tab="dashboard">Dashboard</button>
                        <button class="wc-filter-btn" data-tab="devices">Devices</button>
                        <button class="wc-filter-btn" data-tab="security">Security</button>
                        <button class="wc-filter-btn" data-tab="nest">Nest</button>
                    </div>
                    <button class="wc-btn" onclick="AppRegistry.get('home-iot').refresh()">Refresh</button>
                </div>
                <div id="home-content"><div class="wc-loading">Loading...</div></div>
            </div>`;
        },

        async init() {
            const body = WindowManager.getBody(this.id);
            if (body) {
                body.querySelectorAll('.wc-filter-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        body.querySelectorAll('.wc-filter-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        this._currentTab = btn.dataset.tab;
                        this.refresh();
                    });
                });
            }
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 30000);
        },

        async refresh() {
            if (this._currentTab === 'dashboard') await this.renderDashboard();
            else if (this._currentTab === 'devices') await this.renderDevices();
            else if (this._currentTab === 'security') await this.renderSecurity();
            else if (this._currentTab === 'nest') await this.renderNest();
        },

        async renderDashboard() {
            const el = this._el('home-content');
            if (!el) return;
            try {
                const stats = await FlowCore.api('/api/home/stats');
                el.innerHTML = `
                    <div class="wc-stats">
                        <div class="wc-stat"><span class="wc-stat-num good">${stats.systems_healthy || 0}</span><span class="wc-stat-label">Systems OK</span></div>
                        <div class="wc-stat"><span class="wc-stat-num crit">${stats.systems_down || 0}</span><span class="wc-stat-label">Down</span></div>
                        <div class="wc-stat"><span class="wc-stat-num">${stats.cpu_percent || '--'}%</span><span class="wc-stat-label">CPU</span></div>
                        <div class="wc-stat"><span class="wc-stat-num">${stats.ram_percent || '--'}%</span><span class="wc-stat-label">RAM</span></div>
                        <div class="wc-stat"><span class="wc-stat-num good">${stats.iot_online || 0}</span><span class="wc-stat-label">IoT Online</span></div>
                        <div class="wc-stat"><span class="wc-stat-num">${stats.iot_total || 0}</span><span class="wc-stat-label">IoT Total</span></div>
                        <div class="wc-stat"><span class="wc-stat-num warn">${stats.alerts_warning || 0}</span><span class="wc-stat-label">Warnings</span></div>
                        <div class="wc-stat"><span class="wc-stat-num crit">${stats.alerts_critical || 0}</span><span class="wc-stat-label">Critical</span></div>
                    </div>`;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderDevices() {
            const el = this._el('home-content');
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/home-hub/devices');
                const devices = data.devices || [];
                // Group by zone
                const zones = {};
                devices.forEach(d => {
                    const z = d.zone || 'Unknown';
                    if (!zones[z]) zones[z] = [];
                    zones[z].push(d);
                });
                el.innerHTML = Object.entries(zones).map(([zone, devs]) =>
                    `<div class="wc-zone">
                        <h4 class="wc-zone-title">${zone} (${devs.length})</h4>
                        <div class="wc-grid">${devs.map(d => {
                            const online = d.online ? 'good' : 'crit';
                            return `<div class="wc-card border-${online}" style="padding:10px">
                                <div class="wc-card-head">
                                    <span class="wc-dot ${online}"></span>
                                    <strong>${d.name || d.ip}</strong>
                                </div>
                                <div class="wc-meta">${d.vendor || ''} ${d.type || ''}</div>
                                <div class="wc-meta">${d.ip || ''} ${d.mac || ''}</div>
                                <div class="wc-muted">${d.last_seen ? 'Seen: ' + new Date(d.last_seen).toLocaleString() : ''}</div>
                            </div>`;
                        }).join('')}</div>
                    </div>`
                ).join('');
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderSecurity() {
            const el = this._el('home-content');
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/home-hub/security-status');
                const highRisk = data.high_risk || [];
                const stale = data.stale_devices || [];
                el.innerHTML = `
                    <h4 class="wc-heading" style="color:var(--crit)">High Risk Devices (${highRisk.length})</h4>
                    ${highRisk.length ? `<div class="wc-list">${highRisk.map(d =>
                        `<div class="wc-event-row">
                            <span class="wc-tier-badge crit">${d.severity || 'HIGH'}</span>
                            <div class="wc-event-content">
                                <div class="wc-event-title">${d.device} (${d.ip})</div>
                                <div class="wc-event-meta">${d.vendor || ''} &middot; ${d.warning || ''}</div>
                            </div>
                        </div>`
                    ).join('')}</div>` : '<div class="wc-empty">No high-risk devices</div>'}

                    <h4 class="wc-heading" style="margin-top:16px;color:var(--warn)">Stale Devices (${stale.length})</h4>
                    ${stale.length ? `<div class="wc-list">${stale.map(d =>
                        `<div class="wc-event-row">
                            <span class="wc-tier-badge warn">${d.severity || 'STALE'}</span>
                            <div class="wc-event-content">
                                <div class="wc-event-title">${d.device} (${d.ip})</div>
                                <div class="wc-event-meta">${d.warning || ''}</div>
                            </div>
                        </div>`
                    ).join('')}</div>` : '<div class="wc-empty">All devices recently seen</div>'}
                `;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderNest() {
            const el = this._el('home-content');
            if (!el) return;
            try {
                const thermo = await FlowCore.api('/api/home-hub/nest/thermostat');
                el.innerHTML = `
                    <div class="wc-nest-panel">
                        <h4 class="wc-heading">Nest Thermostat</h4>
                        <div class="wc-stats">
                            <div class="wc-stat"><span class="wc-stat-num">${thermo.ambient_temp || '--'}&deg;</span><span class="wc-stat-label">Current</span></div>
                            <div class="wc-stat"><span class="wc-stat-num">${thermo.target_temp || '--'}&deg;</span><span class="wc-stat-label">Target</span></div>
                            <div class="wc-stat"><span class="wc-stat-num">${thermo.humidity || '--'}%</span><span class="wc-stat-label">Humidity</span></div>
                            <div class="wc-stat"><span class="wc-stat-num">${thermo.mode || '--'}</span><span class="wc-stat-label">Mode</span></div>
                            <div class="wc-stat"><span class="wc-stat-num">${thermo.hvac_status || '--'}</span><span class="wc-stat-label">HVAC</span></div>
                        </div>
                        <div class="wc-nest-controls" style="margin-top:16px">
                            <label>Set Temperature:</label>
                            <input type="number" id="nest-temp" value="${thermo.target_temp || 72}" min="60" max="85" class="wc-input" style="width:80px">
                            <select id="nest-mode" class="wc-input">
                                <option value="HEAT" ${thermo.mode === 'HEAT' ? 'selected' : ''}>Heat</option>
                                <option value="COOL" ${thermo.mode === 'COOL' ? 'selected' : ''}>Cool</option>
                                <option value="HEATCOOL" ${thermo.mode === 'HEATCOOL' ? 'selected' : ''}>Auto</option>
                                <option value="OFF" ${thermo.mode === 'OFF' ? 'selected' : ''}>Off</option>
                            </select>
                            <button class="wc-btn" onclick="AppRegistry.get('home-iot').setNest()">Set</button>
                        </div>
                    </div>`;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Nest unavailable: ${e.message}</div>`;
            }
        },

        async setNest() {
            const temp = this._el('nest-temp')?.value;
            const mode = this._el('nest-mode')?.value;
            try {
                await FlowCore.api('/api/home-hub/nest/thermostat/set', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ temp: parseInt(temp), mode: mode })
                });
                this.renderNest();
            } catch (e) { console.error('Nest set failed:', e); }
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
