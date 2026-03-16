# JR INSTRUCTION: Unified Command Center — FlowOS Shell + SAG Engine + Cherokee Features

**Task**: Merge three existing frontend applications (SAG Control Room, Cherokee AI Desktop, Pathfinder Apps) into one unified windowed command center. FlowOS/WinBox is the shell. SAG's 68 API endpoints are the engine. Cherokee Desktop contributes D3.js Canvas, Chiefs Theater, and the windowed paradigm. Each SAG view becomes a standalone WinBox window app — no iframes, no framework migration.
**Priority**: P1
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 11 (Phase 1: 3, Phase 2: 5, Phase 3: 3)
**Council Vote**: #36c3cd28b3a6376e (PROCEED, 0.843 confidence)
**Triad Consultation**: GPT-4o via Consultation Ring — aligned on windowed desktop + NOC/SOC patterns
**Supersedes**: Jr #1381 (Desktop Assistant Full Stack — based on nonexistent "Joe's MyBrain React/Tailwind")
**Depends On**: Gateway tool-call loop (DONE), Anti-sycophancy prompt (DONE)

## Why This Instruction Exists

We discovered three separately-built frontends that need to be one product:

| App | Location | Port | Endpoints | Views | Status |
|-----|----------|------|-----------|-------|--------|
| SAG Control Room | redfin `/ganuda/home/dereadi/sag_unified_interface/` | 4000 | 68 | 18 | Running, most mature |
| Cherokee AI Desktop | bmasass `/Users/Shared/ganuda/cherokee_desktop/` | 9001 | 10 | 7 | Running, prototype |
| Pathfinder Apps | BigMac `/Users/Shared/ganuda/pathfinder/qdad-apps/` | — | few | 2 | Standalone |

The SAG Control Room is the operational engine (cameras, email, IoT, secrets, kanban, messaging, tribal awareness, FARA vision, harness, 4 DB connections, external integrations with Gmail/Nest/Amcrest/Telegram). The Cherokee Desktop has the better UI paradigm (WinBox windowed multitasking, D3.js federation graph, Chiefs Theater). The Pathfinder apps have visual kanban drag-drop and SVG council circle.

Council and Triad agreed: **windowed desktop shell, SAG backend untouched, gateway API for all data, no framework migration, ship incrementally.**

Coyote's dissent (accepted): Don't iframe SAG views into WinBox — each view becomes a standalone WinBox app module calling SAG endpoints directly. The SAG monolith stays as a backend API; only the frontend restructures.

## Architecture

```
FlowOS Shell (served from redfin, Cherokee-themed)
  ├── WinBox Window: Federation Status    → GET /api/federation/summary
  ├── WinBox Window: Events Triage        → GET/POST /api/events/*
  ├── WinBox Window: Cameras              → GET /api/cameras/*
  ├── WinBox Window: Alert Feed           → WebSocket (Redis jr_alerts)
  ├── WinBox Window: Home Hub / IoT       → GET /api/home-hub/*, /api/iot/*
  ├── WinBox Window: Email Intelligence   → GET/POST /api/emails/*
  ├── WinBox Window: Messages             → GET/POST /api/messaging/*
  ├── WinBox Window: Kanban               → GET /api/kanban/*
  ├── WinBox Window: Console              → POST /api/console/*
  ├── WinBox Window: Secrets              → GET/PUT/POST /api/secrets/*
  ├── WinBox Window: Tribal Awareness     → GET /api/awareness/*
  ├── WinBox Window: Settings             → Config management
  ├── WinBox Window: Federation Canvas    → D3.js force-directed graph (from Cherokee Desktop)
  ├── WinBox Window: Chiefs Theater       → Animated deliberation replay (from Cherokee Desktop)
  ├── WinBox Window: Chat                 → POST /v1/chat/completions (gateway :8080, with sessions)
  ├── WinBox Window: Visual Kanban        → Drag-drop columns (from Pathfinder)
  └── Taskbar + Command Bar + Spotlight Search
           │
           ▼
    SAG Backend (:4000, untouched)  +  Gateway (:8080, for chat/council/tools)
```

Token flow for chat: FlowOS → gateway :8080 `/v1/chat/completions` with `session_id` → LLM → response. Chat sessions stored in `chat_sessions` / `chat_messages` tables (schema from the superseded #1381 instruction — those tables are still valid).

## Existing Source Files to Reuse

### From Cherokee AI Desktop (bmasass)
| File | What to Take |
|------|-------------|
| `public/index.html` | Cherokee-themed header, taskbar, desktop container layout |
| `public/js/cherokee-apps.js` (29KB) | WinBox window patterns — adapt for SAG endpoints |
| `public/js/federation-canvas.js` (10KB) | D3.js force-directed federation graph — port as-is |
| `public/js/chiefs-theater.js` (11KB) | Chiefs deliberation replay — wire to real council vote data |
| `public/js/winbox.bundle.min.js` | WinBox library — keep |
| `public/flow.js` | FlowOS runtime (boot, spotlight, hotkeys) — keep spotlight search |
| `public/wm.js` | WindowManager wrapper — keep |
| `cherokee_desktop_api.py` | Flask + Socket.IO WebSocket pattern — merge into SAG or run alongside |

### From SAG Control Room (redfin)
| File | What to Take |
|------|-------------|
| `app.py` (2954 lines) | ALL 68 API endpoints — backend stays untouched |
| `static/js/control-room.js` (2100 lines) | View rendering logic — refactor each view into a WinBox app module |
| `static/js/unified.js` (1800 lines) | Event management UI, toast notifications — port to WinBox context |
| `static/js/sidebar.js` | Alerts, triad status, activity feed, daily briefing — becomes sidebar or alert window |
| `static/js/theme-switcher.js` | Light/dark theme — keep |
| `static/css/*.css` | Styles — merge Cherokee theming with SAG functional styles |
| `action_integrations.py` | CVE patching, triad consultations, security scans — backend, untouched |
| `email_intelligence.py` | Gmail integration — backend, untouched |
| `federation_monitor.py` | Node health checks — backend, untouched |
| All other .py modules | Backend, untouched |

### From Pathfinder Apps (BigMac)
| File | What to Take |
|------|-------------|
| `visual-kanban/frontend/` | Drag-drop kanban with burndown chart — port as WinBox window |
| `sag-resource-ai/v3-visual/frontend/` | Council circle SVG, thermal zones — port as widget or window |

## Phase 1: Shell + Core Windows (3 SP)

**Goal**: FlowOS shell running on redfin, serving 5 core WinBox windows backed by SAG endpoints.

### Step 1: Set Up the Unified App Directory

On redfin, create `/ganuda/services/command-center/`:

```
command-center/
  public/
    index.html          ← Cherokee-themed FlowOS shell (from Cherokee Desktop, adapted)
    js/
      winbox.bundle.min.js   ← Copy from Cherokee Desktop
      winbox.bundle.min.css
      flow-core.js           ← Stripped FlowOS runtime (spotlight, hotkeys, boot)
      window-manager.js      ← WinBox wrapper (from wm.js)
      app-registry.js        ← Registry of all window apps
      windows/
        federation-status.js ← WinBox app: federation grid
        events-triage.js     ← WinBox app: event management
        cameras.js           ← WinBox app: camera live/gallery/events
        alert-feed.js        ← WinBox app: real-time WebSocket alerts
        home-iot.js           ← WinBox app: Home Hub + IoT devices
    css/
      cherokee-theme.css     ← Merged Cherokee brown/orange + SAG functional styles
      dark-theme.css         ← From SAG
      light-theme.css        ← From SAG
  server.py                  ← Thin Flask server: serves static files + proxies to SAG :4000
```

### Step 2: The Shell (index.html)

Take Cherokee Desktop's `index.html` as the base. Modify:

- **Header**: "Cherokee AI Command Center" (not "Desktop") with federation status badge
- **Taskbar**: Dynamic — shows open windows, click to focus/minimize
- **Command Bar**: Global search from SAG's command bar + FlowOS spotlight (Ctrl+Space)
- **Desktop Container**: Where WinBox windows render
- **No sidebar by default** — sidebar content becomes its own window or notification panel

### Step 3: Window App Pattern

Each window app is a standalone JS module that:

```javascript
// windows/federation-status.js
const FederationStatusApp = {
    id: 'federation-status',
    title: 'Federation Status',
    icon: '🏔️',
    defaultSize: { width: 900, height: 600 },
    defaultPosition: { x: 50, y: 50 },

    open() {
        if (WindowManager.exists(this.id)) {
            WindowManager.focus(this.id);
            return;
        }
        WindowManager.create({
            id: this.id,
            title: this.title,
            width: this.defaultSize.width,
            height: this.defaultSize.height,
            x: this.defaultPosition.x,
            y: this.defaultPosition.y,
            html: this.render(),
            onclose: () => this.cleanup()
        });
        this.init();
    },

    render() {
        return `<div class="window-content cherokee-dark">
            <div class="window-toolbar">
                <button onclick="FederationStatusApp.refresh()">Refresh</button>
            </div>
            <div id="federation-grid" class="card-grid">Loading...</div>
        </div>`;
    },

    async init() {
        await this.refresh();
        this._interval = setInterval(() => this.refresh(), 10000);
    },

    async refresh() {
        const resp = await fetch('http://localhost:4000/api/federation/summary');
        const data = await resp.json();
        // Render node cards (port SAG's control-room.js rendering logic)
        document.getElementById('federation-grid').innerHTML = this.renderNodes(data);
    },

    renderNodes(data) {
        // Port the node card rendering from SAG's control-room.js
        // ...
    },

    cleanup() {
        if (this._interval) clearInterval(this._interval);
    }
};

AppRegistry.register(FederationStatusApp);
```

### Step 4: WebSocket for Real-Time

Port the Socket.IO connection from Cherokee Desktop's `cherokee-apps.js`:

```javascript
// In flow-core.js
const socket = io('http://localhost:4000');  // Connect to SAG backend

socket.on('redis_message', (data) => {
    // Route to any open window that cares
    AppRegistry.broadcast('redis_message', data);
});
```

Each window app can subscribe:
```javascript
// In alert-feed.js
onMessage(channel, data) {
    if (channel === 'jr_alerts') {
        this.addAlert(data);
    }
}
```

### Step 5: Serve It

Option A (simple): Add a route to SAG's `app.py` that serves the command center:
```python
@app.route('/command-center')
@app.route('/command-center/<path:path>')
def command_center(path='index.html'):
    return send_from_directory('/ganuda/services/command-center/public', path)
```

Option B (separate): Thin Flask server on a new port (e.g., :4100) that serves static files and proxies API calls to SAG :4000.

**Recommend Option A** — no new service to manage. Access at `http://redfin:4000/command-center`.

### Phase 1 Acceptance Criteria

- [ ] FlowOS shell loads at `http://redfin:4000/command-center`
- [ ] Cherokee brown/orange theming with header + taskbar
- [ ] Federation Status window opens with live node data from SAG API
- [ ] Events Triage window opens with CRITICAL/IMPORTANT/FYI filtering
- [ ] Cameras window opens with live view, gallery, and events tabs
- [ ] Alert Feed window receives real-time WebSocket alerts
- [ ] Home/IoT window shows devices and Nest thermostat
- [ ] Spotlight search (Ctrl+Space) opens and filters available windows
- [ ] Multiple windows can be open, dragged, resized, and overlapped simultaneously
- [ ] Taskbar shows open windows and allows focus/minimize

## Phase 2: Full Migration + Cherokee Features (5 SP)

**Goal**: All 18 SAG views ported as WinBox windows. Cherokee-exclusive features (Canvas, Theater) integrated. Chat sessions wired to gateway.

### Additional Window Apps

Port each remaining SAG view as a standalone WinBox app module:

| Window | SAG Endpoints | Notes |
|--------|--------------|-------|
| Email Intelligence | `/api/emails/*` | Draft/send/discard, daemon control |
| Messages | `/api/messaging/*` | Multi-platform: Telegram, Slack, Discord, Facebook, Instagram, WhatsApp, SMS |
| Kanban | `/api/kanban/*` | Native WinBox rendering, NOT iframe to :3001 |
| Console | `/api/console/*` | Mission dispatch to triad |
| Secrets | `/api/secrets/*` | Reveal/edit/add with audit |
| Tribal Awareness | `/api/awareness/*` | Agent social graph, pulses, boss election |
| Settings | Config API | Theme, layout preferences, window positions |
| Monitoring | `/api/monitoring/*` | CPU/RAM/disk, service health, DB stats |
| Tribe Council | `/api/tribe/*` | Council votes display |
| Daily Briefing | `/api/briefing` | Market data, solar, weather |
| Nodes Detail | `/api/federation/nodes/*` | Per-node deep view |
| Services | from federation | Service-level view |

### Cherokee Features (Port from bmasass)

| Window | Source File | Wiring |
|--------|-----------|--------|
| Federation Canvas | `federation-canvas.js` (10KB) | Replace mock data with `/api/federation/nodes` |
| Chiefs Theater | `chiefs-theater.js` (11KB) | Replace simulated data with `/api/tribe/council-votes` for real deliberation replay |

### Chat Window (New)

```javascript
const ChatApp = {
    id: 'chat',
    title: 'Cherokee Chat',

    async sendMessage(text) {
        const resp = await fetch('http://redfin:8080/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({
                messages: [{ role: 'user', content: text }],
                session_id: this.sessionId,
                model: 'default'
            })
        });
        const data = await resp.json();
        this.appendMessage('assistant', data.choices[0].message.content);
    }
};
```

Requires the chat session DB tables from the superseded #1381 instruction:

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) DEFAULT 'New Chat',
    api_key_id VARCHAR(64),
    source_node VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    tool_name VARCHAR(128),
    tool_result JSONB,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_api_key ON chat_sessions(api_key_id, updated_at DESC);
```

Gateway session endpoints (add to `gateway.py`):
- `POST /v1/sessions` — create session
- `GET /v1/sessions` — list sessions
- `GET /v1/sessions/{id}/messages` — message history
- `DELETE /v1/sessions/{id}` — delete session
- Modify `/v1/chat/completions` to accept `session_id`, load/save context

### Window Layout Persistence

Save window positions/sizes to localStorage:

```javascript
WindowManager.saveLayout = () => {
    const layout = {};
    Object.entries(windows).forEach(([id, win]) => {
        layout[id] = { x: win.x, y: win.y, width: win.width, height: win.height, open: true };
    });
    localStorage.setItem('cherokee-layout', JSON.stringify(layout));
};

WindowManager.restoreLayout = () => {
    const layout = JSON.parse(localStorage.getItem('cherokee-layout') || '{}');
    Object.entries(layout).forEach(([id, pos]) => {
        if (pos.open) AppRegistry.get(id)?.open(pos);
    });
};
```

### Phase 2 Acceptance Criteria

- [ ] All 18 SAG views available as WinBox windows
- [ ] Federation Canvas shows live D3.js force-directed graph with real node data
- [ ] Chiefs Theater replays real council vote deliberations
- [ ] Chat window sends messages through gateway with session persistence
- [ ] Window layout persists across page reloads (localStorage)
- [ ] Spotlight search finds and opens any window by name
- [ ] Theme switcher (dark/light) works across all windows

## Phase 3: Polish + Pathfinder + Voice (3 SP)

### Visual Kanban Window

Port Pathfinder's drag-drop kanban:
- Columns: Backlog, To Do, In Progress, Review, Done
- Cards draggable between columns
- Burndown chart
- Backed by `/api/kanban/*` endpoints

### SAG Resource AI Widget

Port Pathfinder's council circle SVG and thermal zone visualization as a window or dashboard widget.

### NOC/SOC Patterns (from Triad advice)

1. **Persistent notification bar**: Any window can push a notification. Critical alerts float above all windows.
2. **Drill-down**: Click any summary metric to open a detail window. E.g., click "3 Critical" on home dashboard → Events window opens filtered to CRITICAL.
3. **Customizable default layout**: Pre-built layouts — "Operations" (Events + Cameras + Alerts), "Intel" (Email + Messages + Chat), "Engineering" (Console + Federation + Kanban).

### Voice Interface (Optional)

Browser-native, no server-side dependencies:
- Input: `window.SpeechRecognition` (Chrome/Edge)
- Output: `window.speechSynthesis` or Piper TTS on BigMac
- Trigger: Hold-to-talk button in Chat window
- Flow: Voice → text → ChatApp.sendMessage() → response → TTS

### Mobile/Tablet (Stretch)

On small screens, WinBox windows stack vertically (CSS media query). Taskbar becomes a hamburger menu. Touch-friendly window controls.

### Phase 3 Acceptance Criteria

- [ ] Visual Kanban window with drag-drop columns
- [ ] Drill-down from dashboard metrics to detail windows
- [ ] At least 3 pre-built layouts (Operations, Intel, Engineering)
- [ ] Voice input captures speech and sends as chat text
- [ ] Anti-sycophancy prompt active in all chat (inherited from gateway)
- [ ] Notification bar shows critical alerts above all windows

## DO NOT

- Rewrite SAG's backend — it has 68 working endpoints, 14 Python modules, 4 DB connections. Leave it alone.
- Adopt React/Vue/Svelte — framework migration is a 6-month rewrite for a single-operator system. Stay vanilla JS.
- Use iframes for SAG views — each view must be a native WinBox app calling APIs directly (Coyote's dissent, accepted)
- Break SAG while building this — SAG at :4000 stays running and accessible throughout. The command center is additive.
- Store API keys in frontend JavaScript — all auth goes through server-side proxy or gateway
- Build chat before the windowed shell works — Phase 1 first, chat is Phase 2
- Over-engineer mobile — this is primarily a desktop command center for one operator

## Files to Create

| File | Purpose |
|------|---------|
| `/ganuda/services/command-center/public/index.html` | FlowOS shell with Cherokee theming |
| `/ganuda/services/command-center/public/js/flow-core.js` | Boot, spotlight, hotkeys, WebSocket |
| `/ganuda/services/command-center/public/js/window-manager.js` | WinBox wrapper + layout persistence |
| `/ganuda/services/command-center/public/js/app-registry.js` | Window app registration + broadcast |
| `/ganuda/services/command-center/public/js/windows/*.js` | One file per WinBox window app (~16 files) |
| `/ganuda/services/command-center/public/js/federation-canvas.js` | Ported from Cherokee Desktop |
| `/ganuda/services/command-center/public/js/chiefs-theater.js` | Ported from Cherokee Desktop |
| `/ganuda/services/command-center/public/css/cherokee-theme.css` | Merged Cherokee + SAG styles |
| `/ganuda/services/command-center/public/css/dark-theme.css` | From SAG |
| `/ganuda/services/command-center/public/css/light-theme.css` | From SAG |

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/home/dereadi/sag_unified_interface/app.py` | Add `/command-center` route to serve static files |
| `/ganuda/services/llm_gateway/gateway.py` | Add session endpoints (Phase 2) |
| Bluefin DB | Create chat_sessions + chat_messages tables (Phase 2) |

## Verification

1. Open `http://redfin:4000/command-center` in browser
2. Open Federation Status + Cameras + Alert Feed simultaneously — all three windows visible, draggable, resizable
3. Receive a real-time alert via WebSocket while cameras window is open
4. Use spotlight (Ctrl+Space) to find and open Email Intelligence
5. Open Chat window, send a message, get response with anti-sycophancy active
6. Close browser, reopen — window layout restored from localStorage
7. Open Chiefs Theater, replay a real council vote deliberation
8. Click "3 Critical" on dashboard → Events window opens filtered to CRITICAL tier
