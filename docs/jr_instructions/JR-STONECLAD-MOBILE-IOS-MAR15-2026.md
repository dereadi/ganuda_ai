# Jr Instruction: Stoneclad Mobile — iOS Command Center

**Task ID**: To be assigned
**Priority**: P2
**Story Points**: 13
**Node**: sasass (Xcode build), redfin (SAG backend)
**Prerequisites**: Stoneclad Desktop Phase 1 verified, Tauri v2 mobile toolchain on sasass
**Quote**: "I am just trying to get closer to the Cluster and get it closer to me." — Partner

## Context

Stoneclad Desktop puts the Command Center on the Mac. Stoneclad Mobile puts it in Partner's pocket. Not a full desktop port — a focused mobile experience with four core capabilities:

1. **Chat** — Talk to the Cluster. Build workflows, request files, give instructions, ask questions. This is the primary interface. The phone becomes a voice into the Longhouse.
2. **Monitoring** — Federation health at a glance. Node status, GPU temps, service health, Fire Guard alerts. Glanceable, not interactive.
3. **Briefing** — Dawn mist in your pocket. Weather (Tahlequah + Bentonville), market data, overnight council votes, Jr task completions. Read-only morning briefing.
4. **Cameras** — Live camera feeds. Check the property, check the rack room, check whatever's wired. Tap to fullscreen.

Network: Tailscale on iOS connects to the mesh. SAG on redfin at `100.116.27.89:4000` is reachable from anywhere with internet. Same fallback pattern as desktop: try LAN first, fall back to Tailscale.

## Architecture

```
iPhone
  └── Stoneclad.app (Tauri v2 iOS, WKWebView)
        ├── Tab: Chat         → /command-center/mobile/chat
        ├── Tab: Monitoring   → /command-center/mobile/monitoring
        ├── Tab: Briefing     → /command-center/mobile/briefing
        └── Tab: Cameras      → /command-center/mobile/cameras
              │
              └── (Tailscale VPN) → redfin SAG :4000
```

Tauri v2 iOS uses WKWebView (same engine as Safari). The Rust backend handles native features: push notifications, background fetch, haptic feedback. The frontend is mobile-optimized HTML/CSS/JS served by SAG — same data, different layout.

## Mobile UI Design

### Navigation
- **Bottom tab bar** with 4 icons: Chat, Monitor, Briefing, Cameras
- No WinBox. No floating windows. Each tab is a full-screen view.
- Cherokee theme colors preserved: `#1a1210` background, `#d2691e` accent, `#f0e6dc` text
- Pull-to-refresh on Monitoring and Briefing tabs

### Tab 1: Chat (Primary)
- Full-screen chat interface
- Text input at bottom with send button
- Chat history scrolling up
- Messages from Cluster styled differently from Partner messages
- **Key capability**: Not just reading — this is an interactive channel to the Cluster
  - "Deploy the new fire guard config"
  - "Show me today's Jr task results"
  - "Pull the consultation ring logs from the last hour"
  - "What did the council vote on today?"
- Backed by existing `/api/chat` endpoint or new `/api/mobile/chat` if needed
- Support for receiving file links, code snippets, structured responses
- Voice input via iOS native speech-to-text (Tauri can access this)

### Tab 2: Monitoring
- Card-based layout, one card per node
- Each card shows: node name, status (green/yellow/red), GPU temp, CPU load, top service
- Tap a card → expand to show all services on that node
- Fire Guard alerts at the top as a banner (red if critical)
- Data from `/api/federation/nodes` endpoint
- Auto-refresh every 30 seconds via WebSocket
- **Glanceable**: Should convey federation health in <2 seconds of looking

### Tab 3: Briefing
- Daily briefing rendered as a scrollable card stack
- Weather cards (Tahlequah + Bentonville) with temp, conditions, icon
- Market card: oil price, S&P, crypto if tracked
- Council votes card: overnight votes with results
- Jr tasks card: completed/failed since last briefing
- Data from `/api/briefing/daily` endpoint
- Pull-to-refresh to get latest

### Tab 4: Cameras
- Grid of camera thumbnails (2 columns)
- Tap thumbnail → fullscreen live view
- Pinch to zoom on fullscreen
- Camera names as labels below thumbnails
- Data from existing camera endpoints
- Optimize for mobile bandwidth — request lower resolution streams by default, full res on tap

## Implementation Steps

### Step 1: Tauri iOS Toolchain on sasass

```bash
# Install Xcode (if not already)
xcode-select --install

# Install iOS targets
rustup target add aarch64-apple-ios aarch64-apple-ios-sim

# Initialize Tauri iOS project
cd /Users/Shared/ganuda/services/stoneclad-desktop
cargo tauri ios init
```

This generates the Xcode project in `src-tauri/gen/apple/`.

### Step 2: Mobile Routes in SAG

**File**: SAG route handler (Command Center backend on redfin)

Add mobile-optimized routes:
```
GET /command-center/mobile/chat
GET /command-center/mobile/monitoring
GET /command-center/mobile/briefing
GET /command-center/mobile/cameras
```

Each serves a standalone HTML page with:
- Mobile viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
- Touch-optimized CSS (44px minimum tap targets, no hover states)
- Bottom tab bar navigation
- Cherokee theme
- Safe area insets for iPhone notch/Dynamic Island: `env(safe-area-inset-top)`, etc.

### Step 3: Mobile CSS Framework

**File**: `/ganuda/services/command-center/public/css/stoneclad-mobile.css`

Mobile-specific styles:
- Tab bar: fixed bottom, 4 equal tabs, 56px height
- Cards: full-width, rounded corners, subtle shadow
- Chat: input pinned to bottom above tab bar, keyboard-aware
- No scrollbars (momentum scrolling)
- Dark theme only (matches Cherokee theme, saves battery on OLED iPhones)
- Font sizes: 16px minimum (prevents iOS auto-zoom on input focus)

### Step 4: Mobile JS Modules

Create mobile-specific JS for each tab. These are simpler than the desktop window equivalents — no WinBox, no WindowManager, just direct DOM rendering into a full-screen container.

```
/ganuda/services/command-center/public/js/mobile/
  ├── chat.js        — WebSocket chat, message rendering, input handling
  ├── monitoring.js  — Node cards, auto-refresh, alert banners
  ├── briefing.js    — Card stack, pull-to-refresh
  ├── cameras.js     — Thumbnail grid, fullscreen viewer
  └── nav.js         — Tab bar routing, active state management
```

### Step 5: Tauri Mobile Config

**File**: `src-tauri/tauri.conf.json`

Add iOS-specific configuration:
```json
{
    "app": {
        "windows": [{
            "title": "Stoneclad",
            "fullscreen": true
        }]
    }
}
```

The mobile app is always fullscreen — no window chrome needed.

### Step 6: Push Notifications (Phase 2)

Use `tauri-plugin-notification` for local notifications and Apple Push Notification service (APNs) for remote:
- Fire Guard critical alerts → push notification
- Council vote completed → push notification
- Jr task failed → push notification
- Dawn mist ready → morning push notification

This requires an Apple Developer account ($99/year) and a push notification server on redfin.

### Step 7: Build and Test

```bash
# Build for iOS simulator
cargo tauri ios dev

# Build for physical device (requires Apple Developer signing)
cargo tauri ios build
```

TestFlight distribution for Partner + Joe without App Store review.

## Network Configuration

Same pattern as desktop, adapted for mobile:

```javascript
const SAG_URLS = {
    lan: 'http://192.168.132.223:4000',
    tailscale: 'http://100.116.27.89:4000'
};

async function getSagUrl() {
    try {
        await fetch(SAG_URLS.lan + '/health', { signal: AbortSignal.timeout(2000) });
        return SAG_URLS.lan;
    } catch {
        return SAG_URLS.tailscale;
    }
}
```

On iPhone with Tailscale app connected, the Tailscale IP routes through the mesh. At home on WiFi, LAN IP is faster.

## Chat Integration — The Key Feature

The chat tab is what makes this more than a dashboard. It's a remote terminal into the Cluster that speaks natural language:

**What Partner can do from the chat tab:**
- Ask questions about federation state ("How's bluefin doing?")
- Trigger actions ("Restart the consultation ring")
- Request files ("Send me today's fire guard report")
- Build workflows ("Create a Jr task to add weather alerts for tornado warnings")
- Review work ("What did the Jrs complete today?")
- Consult the council ("What does Coyote think about adding a new node?")

**Backend**: The chat connects to SAG's existing chat/command infrastructure. If a dedicated mobile chat endpoint is needed (`/api/mobile/chat`), it should:
- Accept text messages via WebSocket
- Route to the appropriate handler (TPM agent, Jr dispatch, council query)
- Return structured responses (text + optional cards/links/actions)
- Support response streaming for long answers

## Testing

1. **iOS Simulator**: Build and run in Xcode simulator. All 4 tabs render, data loads from SAG.
2. **Physical device**: Deploy via TestFlight or direct install. Verify Tailscale connectivity from cellular network.
3. **Offline graceful**: No Tailscale connection → show "Disconnected from Cluster" banner, cache last briefing.
4. **Chat round-trip**: Send message from phone, verify it reaches SAG, response appears in chat.
5. **Camera latency**: Verify camera feeds load within 3 seconds on LTE.
6. **Battery**: Run monitoring tab for 30 minutes, verify no excessive battery drain from WebSocket polling.

## Constraints

- **Apple Developer Account required** for physical device deployment and TestFlight. $99/year.
- **No App Store submission** in Phase 1. TestFlight internal distribution only.
- **Tailscale must be running on iPhone** for remote access. No Tailscale = no Cluster.
- **iOS 16+ minimum** — Tauri v2 iOS requires it.
- **Chat is text-first**. Voice input uses iOS native dictation, not a custom speech model.
- **Camera feeds must respect bandwidth** — default to low-res thumbnails, full-res on demand.

## Definition of Done

- [ ] Stoneclad.app builds for iOS via Tauri v2 on sasass
- [ ] Runs in iOS simulator with all 4 tabs functional
- [ ] Chat tab sends/receives messages to SAG
- [ ] Monitoring tab shows live node status with auto-refresh
- [ ] Briefing tab renders daily briefing (weather, market, council, Jr tasks)
- [ ] Cameras tab shows thumbnail grid, tap for fullscreen
- [ ] Network fallback: LAN at home, Tailscale remotely
- [ ] Deployable to physical iPhone via TestFlight or direct install
- [ ] Cherokee theme preserved on mobile
