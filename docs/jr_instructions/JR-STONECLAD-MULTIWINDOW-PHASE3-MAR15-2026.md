# Jr Instruction: Stoneclad Multi-Window — WinBox to Native OS Windows

**Task ID**: To be assigned
**Priority**: P2
**Story Points**: 8
**Node**: redfin (Rust backend) + sasass (macOS build/test)
**Prerequisites**: Stoneclad Phase 1 binary verified working (Jr #1396 or manual)
**Council Vote**: Longhouse #b289914a6b5f7fcf (Tauri Desktop Shell — pending Phase 3 scope)

## Context

Partner's words: *"I am just trying to get closer to the Cluster and get it closer to me."*

Phase 1 Stoneclad wraps the Command Center in a single native window. All 14 WinBox windows live inside one webview — they can't escape the app frame. Phase 3 breaks that boundary: each WinBox becomes a real native OS window that can be dragged anywhere on the desktop, placed on different monitors, tiled with other apps, and managed independently through the OS window manager (Cmd+Tab, Mission Control, Spaces on macOS).

The Command Center stops being an app you look into and becomes windows that live *on* your desktop.

## Architecture

### Current Flow (Phase 1)
```
Stoneclad.app
  └── WebviewWindow("main")
        └── Command Center HTML/CSS/JS
              ├── WinBox("federation-status")  ← DOM elements, trapped in webview
              ├── WinBox("kanban")
              ├── WinBox("monitoring")
              └── ... 14 total
```

### Target Flow (Phase 3)
```
Stoneclad.app
  ├── WebviewWindow("main") — taskbar/launcher only (slim bar, no WinBox windows)
  ├── WebviewWindow("federation-status") — native OS window, loads /window/federation-status
  ├── WebviewWindow("kanban") — native OS window, loads /window/kanban
  ├── WebviewWindow("monitoring") — native OS window, loads /window/monitoring
  └── ... each WinBox → separate native window
```

### Key Tauri v2 APIs
```javascript
// JS side — create a native window
import { WebviewWindow } from '@tauri-apps/api/webviewWindow';

const win = new WebviewWindow('federation-status', {
    url: 'http://192.168.132.223:4000/command-center/window/federation-status',
    title: 'Federation Status — Stoneclad',
    width: 800,
    height: 500,
    x: 100,
    y: 200,
    decorations: true,       // native title bar
    transparent: false,
    resizable: true,
    center: false
});

win.once('tauri://created', () => { /* window ready */ });
win.once('tauri://error', (e) => { /* handle error */ });
```

```rust
// Rust side — allow multi-window creation
// In lib.rs, add window creation permissions
// In capabilities/default.json, add "core:window:allow-create"
```

## Implementation Steps

### Step 1: SAG Window Routes (Python — redfin)

Add individual window routes to the Command Center's SAG backend. Each route serves a standalone HTML page containing only that window's content (no taskbar, no WinBox wrapper, no other windows).

**File**: `/ganuda/services/command-center/server.py` (or equivalent SAG route file)

Add route pattern:
```
GET /command-center/window/<window-id>
```

Each route serves a minimal HTML page:
- Cherokee theme CSS (shared)
- The window's JS module (e.g., `federation-status.js`)
- A single root `<div>` the window renders into
- WebSocket connection to SAG for live updates
- NO WinBox library, NO window-manager.js, NO taskbar

Example for `/command-center/window/federation-status`:
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/command-center/css/cherokee-theme.css">
    <style>
        body { margin: 0; background: var(--bg-primary); color: var(--text-primary); }
        #window-root { padding: 16px; height: 100vh; overflow-y: auto; }
    </style>
</head>
<body>
    <div id="window-root"></div>
    <script src="/command-center/js/windows/federation-status.js"></script>
    <script>
        // Initialize window module, render into #window-root
        // Each window JS file needs a renderStandalone(container) export
    </script>
</body>
</html>
```

### Step 2: Window JS Refactor — Dual Render Mode

Each of the 14 window JS files needs to support two render modes:

1. **Embedded mode** (current): Renders inside WinBox DOM, uses `WindowManager.getBody(this.id)` for scoping
2. **Standalone mode** (new): Renders into a full-page `#window-root` div, is the entire page

**Pattern** — add to each window module:
```javascript
// At bottom of each window JS file
if (window.__STONECLAD_STANDALONE__) {
    // We're in a native Tauri window, render standalone
    const root = document.getElementById('window-root');
    MyWindow.renderStandalone(root);
    MyWindow.startPolling();  // if applicable
}
```

The `renderStandalone(container)` method generates the same HTML as the WinBox content but targets the provided container instead of `WindowManager.getBody()`.

**DO NOT break embedded mode.** The Command Center browser experience must continue working. Feature detection, not feature flags.

### Step 3: Tauri Multi-Window Bridge

**File**: `/ganuda/services/stoneclad-desktop/src-tauri/src/lib.rs`

Add Tauri command to create native windows:
```rust
use tauri::{AppHandle, WebviewWindowBuilder, WebviewUrl};

#[tauri::command]
fn open_native_window(
    app: AppHandle,
    id: String,
    title: String,
    url: String,
    width: f64,
    height: f64,
    x: Option<f64>,
    y: Option<f64>,
) -> Result<(), String> {
    let mut builder = WebviewWindowBuilder::new(
        &app,
        &id,
        WebviewUrl::External(url.parse().map_err(|e| format!("{}", e))?)
    )
    .title(&title)
    .inner_size(width, height)
    .resizable(true);

    if let (Some(x), Some(y)) = (x, y) {
        builder = builder.position(x, y);
    } else {
        builder = builder.center();
    }

    builder.build().map_err(|e| format!("{}", e))?;
    Ok(())
}
```

Register in the invoke handler:
```rust
.invoke_handler(tauri::generate_handler![stoneclad_version, open_native_window])
```

### Step 4: Capabilities Update

**File**: `/ganuda/services/stoneclad-desktop/src-tauri/capabilities/default.json`

Add permissions for multi-window and webview:
```json
{
    "identifier": "default",
    "description": "Capability for all windows",
    "windows": ["*"],
    "permissions": [
        "core:default",
        "core:window:allow-create",
        "core:window:allow-close",
        "core:window:allow-set-focus",
        "core:window:allow-set-size",
        "core:window:allow-set-position",
        "core:window:allow-set-title",
        "core:webview:allow-create-webview-window",
        "opener:default"
    ]
}
```

### Step 5: WindowManager Tauri Adapter

**File**: `/ganuda/services/command-center/public/js/window-manager.js`

Add Tauri-aware branch to `WindowManager.create()`:

```javascript
create(opts) {
    const id = opts.id;
    if (this._windows[id]) {
        this._windows[id].focus();
        return this._windows[id];
    }

    // If running inside Tauri, create native OS window instead of WinBox
    if (window.__TAURI_INTERNALS__) {
        return this._createTauriWindow(opts);
    }

    // Existing WinBox path (browser mode)
    // ... current code unchanged ...
},

async _createTauriWindow(opts) {
    const { invoke } = window.__TAURI_INTERNALS__;
    const id = opts.id;
    const baseUrl = 'http://192.168.132.223:4000/command-center/window/';

    try {
        await invoke('open_native_window', {
            id: id,
            title: (opts.title || id) + ' — Stoneclad',
            url: baseUrl + id,
            width: opts.width || 800,
            height: opts.height || 500,
            x: typeof opts.x === 'number' ? opts.x : null,
            y: typeof opts.y === 'number' ? opts.y : null
        });

        // Track as open window (no WinBox reference, just metadata)
        this._windows[id] = { tauri: true, id: id };
        this._addTaskbarItem(id, opts.title || id);
        this.saveLayout();
    } catch (e) {
        console.error('Failed to create Tauri window:', e);
        // Fallback to WinBox if Tauri window creation fails
        return this._createWinBox(opts);
    }
},
```

### Step 6: CSP Update for Multi-Window

**File**: `/ganuda/services/stoneclad-desktop/src-tauri/tauri.conf.json`

The CSP must apply to all windows. Current config already allows connections to `192.168.132.223:4000`. Verify that child windows inherit the same CSP. If not, add CSP to the window creation builder in Rust.

### Step 7: Layout Persistence (Multi-Window Aware)

`saveLayout()` and `restoreLayout()` in window-manager.js need to handle Tauri windows:

- **Save**: For Tauri windows, use the Tauri window position/size APIs to get actual OS-level coordinates
- **Restore**: On app launch, restore each window to its saved desktop position using `open_native_window` with saved x/y/width/height
- **Close tracking**: Listen for Tauri `close-requested` events to update the layout when the user closes a native window via the OS close button

## Window Inventory (14 windows to support)

| Window ID | File | Default Size |
|-----------|------|-------------|
| `federation-status` | federation-status.js | 800x500 |
| `kanban` | kanban.js | 900x600 |
| `monitoring` | monitoring.js | 800x500 |
| `tribe-council` | tribe-council.js | 800x500 |
| `daily-briefing` | daily-briefing.js | 700x500 |
| `alert-feed` | alert-feed.js | 600x400 |
| `cameras` | cameras.js | 800x500 |
| `chat` | chat.js | 600x500 |
| `console` | console.js | 800x500 |
| `email-intel` | email-intel.js | 700x500 |
| `events-triage` | events-triage.js | 700x500 |
| `home-iot` | home-iot.js | 600x400 |
| `messages` | messages.js | 600x500 |
| `secrets` | secrets.js | 600x400 |

## Testing

1. **Browser mode preserved**: Open `http://192.168.132.223:4000/command-center/` in Safari/Chrome. All 14 windows still work as WinBox inside the browser. No regressions.

2. **Standalone routes**: Open `http://192.168.132.223:4000/command-center/window/federation-status` directly in a browser. Should render full-page, no WinBox chrome, live data updating.

3. **Tauri multi-window**: Launch Stoneclad.app. Click a window in the launcher. Native macOS window appears. Drag it to a second monitor. Resize it. Verify live data flows via WebSocket.

4. **Cross-window independence**: Open 3+ native windows. Close one. Others continue running. No crashes, no state corruption.

5. **Layout persistence**: Open 3 windows, position them. Quit Stoneclad. Relaunch. Windows restore to saved positions.

6. **Mission Control**: Open multiple Stoneclad windows. Trigger macOS Mission Control (F3 or swipe up). Each Stoneclad window appears independently, not grouped under one app thumbnail.

## Constraints

- **DO NOT remove WinBox support.** Browser mode must keep working. The Tauri path is an enhancement, not a replacement.
- **Each window loads from SAG over HTTP.** No bundled frontend assets for individual windows. SAG is the single source of truth.
- **WebSocket connections per window.** Each standalone window establishes its own WebSocket to SAG. Verify SAG handles 14+ concurrent WebSocket connections.
- **macOS build target.** Test on sasass (Apple Silicon). Redfin Linux build is secondary since redfin is headless.
- **No Electron.** Tauri only. DC-9 compliant. 13MB binary, not 150MB.

## Definition of Done

- [ ] All 14 windows render as native OS windows when launched from Stoneclad
- [ ] Each window is independently draggable, resizable, closeable via OS controls
- [ ] Browser mode (no Tauri) continues working identically to today
- [ ] Layout saves/restores across app restarts
- [ ] WebSocket live updates work in each standalone window
- [ ] Builds and runs on macOS (sasass) — Apple Silicon
- [ ] No regressions in existing Command Center functionality
