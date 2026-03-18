// Cameras Window — live view, gallery, and detection events

(function() {
    const app = {
        id: 'cameras',
        title: 'Tribal Vision - Cameras',
        tags: ['cameras', 'vision', 'security', 'crawdad', 'fara'],
        _interval: null,
        _currentTab: 'live',

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
                height: savedPos?.height || 650,
                x: savedPos?.x || 150,
                y: savedPos?.y || 40,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.init();
        },

        render() {
            return `<div class="wc-pad">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Tribal Vision</h3>
                    <div class="wc-filters">
                        <button class="wc-filter-btn active" data-tab="live">Live</button>
                        <button class="wc-filter-btn" data-tab="gallery">Gallery</button>
                        <button class="wc-filter-btn" data-tab="detections">Detections</button>
                    </div>
                    <button class="wc-btn" onclick="AppRegistry.get('cameras').refresh()">Refresh</button>
                </div>
                <div id="cam-stats" class="wc-stats"></div>
                <div id="cam-content"><div class="wc-loading">Loading cameras...</div></div>
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
            await this.loadStats();
            await this.refresh();
            this._interval = setInterval(() => this.refresh(), 15000);
        },

        async loadStats() {
            try {
                const stats = await FlowCore.api('/api/cameras/stats');
                const el = this._el('cam-stats');
                if (!el) return;
                el.innerHTML = `
                    <div class="wc-stat"><span class="wc-stat-num">${stats.total_frames || 0}</span><span class="wc-stat-label">Total Frames</span></div>
                    <div class="wc-stat"><span class="wc-stat-num">${stats.frames_today || 0}</span><span class="wc-stat-label">Today</span></div>
                    <div class="wc-stat"><span class="wc-stat-num">${(stats.disk_usage_mb || 0).toFixed(0)} MB</span><span class="wc-stat-label">Disk</span></div>
                `;
            } catch (e) { /* optional */ }
        },

        async refresh() {
            if (this._currentTab === 'live') await this.renderLive();
            else if (this._currentTab === 'gallery') await this.renderGallery();
            else if (this._currentTab === 'detections') await this.renderDetections();
        },

        async renderLive() {
            const el = this._el('cam-content');
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/cameras');
                const cameras = data.cameras || [];
                el.innerHTML = `<div class="wc-cam-grid">${cameras.map(cam => {
                    const statusDot = cam.status === 'active' ? 'good' : 'warn';
                    // Use stored frame if available, otherwise fall back to live snapshot endpoint
                    const imgSrc = cam.latest_frame
                        ? `${FlowCore.SAG_API}/api/cameras/frame/${cam.latest_frame}`
                        : `${FlowCore.SAG_API}/api/cameras/${cam.id}/snapshot?t=${Date.now()}`;
                    return `<div class="wc-cam-card">
                        <div class="wc-cam-header">
                            <span class="wc-dot ${statusDot}"></span>
                            <strong>${cam.name}</strong>
                        </div>
                        <img src="${imgSrc}" class="wc-cam-img" alt="${cam.name}"
                             onclick="AppRegistry.get('cameras').snapshot('${cam.id}')"
                             onerror="this.outerHTML='<div class=\\'wc-cam-placeholder\\'>No frame</div>'">
                        <div class="wc-cam-footer">
                            <span class="wc-muted">${cam.purpose || ''}</span>
                            <button class="wc-btn-sm" onclick="AppRegistry.get('cameras').snapshot('${cam.id}')">Snapshot</button>
                        </div>
                    </div>`;
                }).join('')}</div>`;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderGallery() {
            const el = this._el('cam-content');
            if (!el) return;
            try {
                const data = await FlowCore.api('/api/cameras/gallery?per_page=24');
                const frames = data.frames || [];
                el.innerHTML = `<div class="wc-gallery">${frames.map(f =>
                    `<div class="wc-gallery-thumb" onclick="AppRegistry.get('cameras').viewFrame('${f.filename}')">
                        <img src="${FlowCore.SAG_API}/api/cameras/frame/${f.filename}" loading="lazy" alt="${f.camera}">
                        <div class="wc-gallery-label">${f.camera} &middot; ${f.timestamp || ''}</div>
                    </div>`
                ).join('')}</div>
                <div class="wc-muted" style="margin-top:8px">Page ${data.page}/${data.total_pages} (${data.total} frames)</div>`;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async renderDetections() {
            const el = this._el('cam-content');
            if (!el) return;
            try {
                const [detections, alerts] = await Promise.all([
                    FlowCore.api('/api/cameras/detections'),
                    FlowCore.api('/api/cameras/alerts')
                ]);
                const allItems = [
                    ...(alerts.alerts || []).map(a => ({ ...a, type: 'alert' })),
                    ...(detections.detections || []).map(d => ({ ...d, type: 'detection' }))
                ];
                el.innerHTML = `<div class="wc-list">${allItems.map(item => {
                    const cls = item.type === 'alert' ? 'crit' : 'info';
                    return `<div class="wc-event-row">
                        <span class="wc-tier-badge ${cls}">${item.type === 'alert' ? 'ALERT' : 'DETECT'}</span>
                        <div class="wc-event-content">
                            <div class="wc-event-title">${item.message || ''}</div>
                            <div class="wc-event-meta">${item.timestamp || ''}</div>
                        </div>
                    </div>`;
                }).join('') || '<div class="wc-empty">No recent detections</div>'}</div>`;
            } catch (e) {
                el.innerHTML = `<div class="wc-error">Failed: ${e.message}</div>`;
            }
        },

        async snapshot(cameraId) {
            try {
                const img = document.createElement('img');
                img.src = `${FlowCore.SAG_API}/api/cameras/${cameraId}/snapshot?t=${Date.now()}`;
                img.style.cssText = 'max-width:100%;border-radius:4px';
                // Open in a new WinBox
                WindowManager.create({
                    id: `snapshot-${cameraId}-${Date.now()}`,
                    title: `Snapshot: ${cameraId}`,
                    width: 640, height: 480,
                    x: 'center', y: 'center',
                    html: `<div class="wc-pad" style="text-align:center"><img src="${img.src}" style="max-width:100%;border-radius:4px"></div>`
                });
            } catch (e) { console.error('Snapshot failed:', e); }
        },

        viewFrame(filename) {
            WindowManager.create({
                id: `frame-${Date.now()}`,
                title: filename,
                width: 800, height: 600,
                x: 'center', y: 'center',
                html: `<div class="wc-pad" style="text-align:center">
                    <img src="${FlowCore.SAG_API}/api/cameras/frame/${filename}" style="max-width:100%;max-height:100%;border-radius:4px">
                </div>`
            });
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
