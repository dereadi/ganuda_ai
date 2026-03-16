# Jr Instruction: Tauri Desktop Shell — Stoneclad Desktop Presence

**Task**: Wrap Command Center frontend in Tauri shell for native desktop windows
**Priority**: P2 (after council vote)
**Story Points**: 8 (EPIC)
**Council Vote**: b289914a6b5f7fcf (pending deliberation)
**Date**: 2026-03-15

## Why

Partner: "I am just trying to get closer to the Cluster and get it closer to me."

The Command Center lives in a browser tab. Close the tab, the organism disappears. This is wrong. The organism should be as present as the desktop — system tray, global hotkeys, native windows that float over everything else.

## Architecture

```
┌──────────────────────────────────────────────┐
│  Tauri Shell (Rust)                          │
│  ├── System Tray Icon (Stoneclad)            │
│  ├── Global Hotkeys (Cmd+Shift+S → chat)     │
│  ├── Window Manager (native OS windows)      │
│  ├── Notification Bridge (OS notifications)  │
│  └── WebSocket IPC → gateway :8080 / SAG :4000│
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  Webview (existing frontend)           │  │
│  │  ├── flow-core.js                      │  │
│  │  ├── cherokee-theme.css                │  │
│  │  ├── window-manager.js                 │  │
│  │  └── js/windows/*.js (all existing)    │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
         │
         │ HTTP/WebSocket
         ▼
   SAG Backend (:4000)  ←→  Gateway (:8080)  ←→  PostgreSQL (bluefin)
```

## Build Targets

| Platform | Target | Node | Webview Engine |
|----------|--------|------|----------------|
| Linux x86_64 | `x86_64-unknown-linux-gnu` | redfin | WebKitGTK |
| macOS arm64 | `aarch64-apple-darwin` | sasass, bmasass | WebKit (native) |

## Phases

### Phase 1: Scaffold (3 SP)
1. `cargo install create-tauri-app` on redfin
2. Initialize Tauri project at `/ganuda/services/stoneclad-desktop/`
3. Point webview at existing Command Center frontend (`/ganuda/services/command-center/public/`)
4. Verify all existing windows render correctly in native webview
5. Build for Linux x86_64

### Phase 2: Native Integration (3 SP)
1. System tray icon with menu (Show/Hide, Quit)
2. Global hotkey: `Ctrl+Shift+S` (Linux) / `Cmd+Shift+S` (macOS) → toggle main window
3. Native notifications via `tauri-plugin-notification` — wire to Fire Guard alerts + council votes
4. Window state persistence (position, size, which windows are open)

### Phase 3: Multi-Window (2 SP)
1. Replace `WindowManager.create()` with `tauri::window::Window` creation via IPC
2. Each Command Center window becomes a real OS window
3. Pin-to-top support per window (council votes card pinned while coding)
4. Cross-window communication via Tauri events

### Phase 4: macOS Build
1. Cross-compile for `aarch64-apple-darwin` OR build natively on sasass
2. Deploy to sasass and bmasass
3. Code-sign with ad-hoc signature (no Apple Developer account needed for internal use)

## Prerequisites

**Linux (redfin)**:
```bash
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev libappindicator3-dev librsvg2-dev
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install create-tauri-app
```

**macOS (sasass/bmasass)**:
```bash
# Xcode CLI tools already installed
cargo install create-tauri-app
```

## Key Design Decisions

- **Presentation layer ONLY** — no data storage in the desktop shell. All data flows through SAG :4000 and gateway :8080. DC-16 compliant.
- **Existing frontend unchanged** — cherokee-theme.css, flow-core.js, all window JS files load as-is. Tauri just wraps them in a native webview.
- **Tauri v2** — use latest stable. Supports multi-window, system tray, notifications, global shortcuts out of the box.
- **No Electron** — DC-9. 3MB vs 150MB. No bundled Chromium. No Google dependency.
- **Kill switch** — if webview fails, fall back to browser at :4000. The web app never goes away.

## Acceptance Criteria

1. Stoneclad icon appears in system tray on redfin
2. Global hotkey summons/hides the main window
3. All existing Command Center windows render correctly
4. Fire Guard alert triggers native OS notification
5. Window positions persist across restarts
6. Binary size < 10MB

## Do NOT

- Bundle Node.js or Chromium
- Store any data in the desktop shell (DC-16)
- Remove or break the existing web-based Command Center (fallback)
- Require internet access to function (sovereign, on-prem)
- Use any framework other than Tauri (council decision pending)
