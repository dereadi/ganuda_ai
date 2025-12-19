# Jr Build Instructions: Tribe Chrome Extension

## Priority: HIGH - Council Approved (Audit: 261e576729496114)

---

## Overview

Build a Chrome extension that gives the Tribe direct browser control, replacing the error-prone screen capture + AppleScript approach.

**Current Limitations:**
- Screen capture requires GUI Terminal trick for SSH
- AppleScript keystrokes are unreliable
- OCR/Vision can misread text
- Can't detect events (video ended, page loaded)
- Coordinate-based clicking is fragile

**Chrome Extension Benefits:**
- Direct DOM access (no OCR needed)
- CSS selector-based clicking (precise)
- Form filling without keystrokes
- Event listeners (video ended, form submitted)
- Works over SSH without GUI context
- Air-gap compatible (local WebSocket only)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Chrome Browser                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Tribe Extension (content.js)                   ││
│  │                                                             ││
│  │  • Reads DOM / extracts text                                ││
│  │  • Clicks elements by selector                              ││
│  │  • Fills form fields                                        ││
│  │  • Listens for events (video end, page load)                ││
│  │  • Captures screenshots when needed                         ││
│  └───────────────────────────┬─────────────────────────────────┘│
│                              │ messages                         │
│  ┌───────────────────────────▼─────────────────────────────────┐│
│  │              Background Service (background.js)              ││
│  │                                                             ││
│  │  • WebSocket connection to Tribe Controller                 ││
│  │  • Routes commands to content script                        ││
│  │  • Sends page state back to controller                      ││
│  └───────────────────────────┬─────────────────────────────────┘│
└──────────────────────────────┼──────────────────────────────────┘
                               │ WebSocket (ws://localhost:8765)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Tribe Controller (sasass or redfin)                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              WebSocket Server (Python)                       ││
│  │              Port 8765                                       ││
│  └───────────────────────────┬─────────────────────────────────┘│
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────────┐│
│  │              Command Processor                               ││
│  │                                                             ││
│  │  • Receives page state from extension                       ││
│  │  • Decides next action (click, type, scroll, wait)          ││
│  │  • Calls FARA when visual analysis needed                   ││
│  │  • Uses learning memory for decisions                       ││
│  │  • Sends commands back to extension                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              FARA (when needed for images)                   ││
│  │              Learning Memory (PostgreSQL)                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Chrome Extension Structure

### 1.1 Create Extension Directory

```
/Users/Shared/ganuda/tribe-extension/
├── manifest.json
├── background.js
├── content.js
├── popup.html
├── popup.js
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── styles.css
```

### 1.2 manifest.json

```json
{
  "manifest_version": 3,
  "name": "Tribe Browser Control",
  "version": "1.0.0",
  "description": "Cherokee AI Federation - Browser automation for the Tribe",

  "permissions": [
    "activeTab",
    "scripting",
    "tabs"
  ],

  "host_permissions": [
    "<all_urls>"
  ],

  "background": {
    "service_worker": "background.js"
  },

  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },

  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### 1.3 content.js (Injected into pages)

```javascript
// Tribe Browser Control - Content Script
// Runs in the context of web pages

(() => {
  console.log('[Tribe] Content script loaded');

  // ============================================================
  // DOM READING
  // ============================================================

  function getPageState() {
    return {
      url: window.location.href,
      title: document.title,
      text: document.body.innerText.substring(0, 5000),
      forms: getFormFields(),
      buttons: getButtons(),
      links: getLinks(),
      videos: getVideos(),
      images: getImageCount()
    };
  }

  function getFormFields() {
    const fields = [];
    document.querySelectorAll('input, textarea, select').forEach((el, i) => {
      fields.push({
        index: i,
        type: el.type || el.tagName.toLowerCase(),
        name: el.name || el.id || `field_${i}`,
        placeholder: el.placeholder || '',
        value: el.value || '',
        selector: getSelector(el)
      });
    });
    return fields;
  }

  function getButtons() {
    const buttons = [];
    document.querySelectorAll('button, input[type="submit"], [role="button"]').forEach((el, i) => {
      buttons.push({
        index: i,
        text: el.innerText || el.value || '',
        selector: getSelector(el)
      });
    });
    return buttons;
  }

  function getLinks() {
    const links = [];
    document.querySelectorAll('a[href]').forEach((el, i) => {
      if (i < 50) { // Limit to first 50
        links.push({
          index: i,
          text: el.innerText.substring(0, 100),
          href: el.href,
          selector: getSelector(el)
        });
      }
    });
    return links;
  }

  function getVideos() {
    const videos = [];
    document.querySelectorAll('video').forEach((el, i) => {
      videos.push({
        index: i,
        duration: el.duration || 0,
        currentTime: el.currentTime || 0,
        paused: el.paused,
        ended: el.ended,
        selector: getSelector(el)
      });
    });
    return videos;
  }

  function getImageCount() {
    return document.querySelectorAll('img').length;
  }

  function getSelector(el) {
    // Generate a CSS selector for the element
    if (el.id) return `#${el.id}`;
    if (el.className && typeof el.className === 'string') {
      const classes = el.className.trim().split(/\s+/).slice(0, 2).join('.');
      if (classes) return `${el.tagName.toLowerCase()}.${classes}`;
    }
    return el.tagName.toLowerCase();
  }

  // ============================================================
  // ACTIONS
  // ============================================================

  function clickElement(selector) {
    const el = document.querySelector(selector);
    if (el) {
      el.click();
      return { success: true, message: `Clicked ${selector}` };
    }
    return { success: false, message: `Element not found: ${selector}` };
  }

  function typeInElement(selector, text) {
    const el = document.querySelector(selector);
    if (el) {
      el.focus();
      el.value = text;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return { success: true, message: `Typed in ${selector}` };
    }
    return { success: false, message: `Element not found: ${selector}` };
  }

  function scrollTo(direction, amount = 300) {
    if (direction === 'down') window.scrollBy(0, amount);
    else if (direction === 'up') window.scrollBy(0, -amount);
    else if (direction === 'bottom') window.scrollTo(0, document.body.scrollHeight);
    else if (direction === 'top') window.scrollTo(0, 0);
    return { success: true, message: `Scrolled ${direction}` };
  }

  function scrollToElement(selector) {
    const el = document.querySelector(selector);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return { success: true, message: `Scrolled to ${selector}` };
    }
    return { success: false, message: `Element not found: ${selector}` };
  }

  function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve) => {
      const el = document.querySelector(selector);
      if (el) {
        resolve({ success: true, found: true });
        return;
      }

      const observer = new MutationObserver(() => {
        const el = document.querySelector(selector);
        if (el) {
          observer.disconnect();
          resolve({ success: true, found: true });
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });

      setTimeout(() => {
        observer.disconnect();
        resolve({ success: true, found: false, message: 'Timeout' });
      }, timeout);
    });
  }

  function getScreenshot() {
    // Note: This requires additional permissions and may not work in all contexts
    // For now, return null and fall back to FARA screen capture
    return null;
  }

  // ============================================================
  // VIDEO EVENT LISTENERS
  // ============================================================

  function setupVideoListeners() {
    document.querySelectorAll('video').forEach((video, i) => {
      if (!video.dataset.tribeListening) {
        video.dataset.tribeListening = 'true';

        video.addEventListener('ended', () => {
          chrome.runtime.sendMessage({
            type: 'VIDEO_ENDED',
            videoIndex: i,
            selector: getSelector(video)
          });
        });

        video.addEventListener('play', () => {
          chrome.runtime.sendMessage({
            type: 'VIDEO_PLAYING',
            videoIndex: i
          });
        });
      }
    });
  }

  // Run on load and periodically
  setupVideoListeners();
  setInterval(setupVideoListeners, 2000);

  // ============================================================
  // MESSAGE HANDLER
  // ============================================================

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Tribe] Received message:', message);

    switch (message.action) {
      case 'GET_PAGE_STATE':
        sendResponse(getPageState());
        break;

      case 'CLICK':
        sendResponse(clickElement(message.selector));
        break;

      case 'TYPE':
        sendResponse(typeInElement(message.selector, message.text));
        break;

      case 'SCROLL':
        sendResponse(scrollTo(message.direction, message.amount));
        break;

      case 'SCROLL_TO':
        sendResponse(scrollToElement(message.selector));
        break;

      case 'WAIT_FOR':
        waitForElement(message.selector, message.timeout).then(sendResponse);
        return true; // Async response

      case 'GET_TEXT':
        const el = document.querySelector(message.selector);
        sendResponse({ text: el ? el.innerText : null });
        break;

      default:
        sendResponse({ error: 'Unknown action' });
    }

    return true; // Keep channel open for async
  });

})();
```

### 1.4 background.js (Service Worker)

```javascript
// Tribe Browser Control - Background Service Worker
// Manages WebSocket connection to Tribe Controller

const CONTROLLER_URL = 'ws://localhost:8765';
let ws = null;
let reconnectInterval = null;

// ============================================================
// WEBSOCKET CONNECTION
// ============================================================

function connect() {
  console.log('[Tribe] Connecting to controller...');

  ws = new WebSocket(CONTROLLER_URL);

  ws.onopen = () => {
    console.log('[Tribe] Connected to controller');
    clearInterval(reconnectInterval);
    sendToController({ type: 'EXTENSION_CONNECTED' });
  };

  ws.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    console.log('[Tribe] Received from controller:', message);
    await handleControllerMessage(message);
  };

  ws.onclose = () => {
    console.log('[Tribe] Disconnected from controller');
    scheduleReconnect();
  };

  ws.onerror = (error) => {
    console.error('[Tribe] WebSocket error:', error);
  };
}

function scheduleReconnect() {
  if (!reconnectInterval) {
    reconnectInterval = setInterval(() => {
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        connect();
      }
    }, 5000);
  }
}

function sendToController(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

// ============================================================
// MESSAGE HANDLING
// ============================================================

async function handleControllerMessage(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab) {
    sendToController({ type: 'ERROR', message: 'No active tab' });
    return;
  }

  try {
    const response = await chrome.tabs.sendMessage(tab.id, message);
    sendToController({
      type: 'RESPONSE',
      action: message.action,
      result: response
    });
  } catch (error) {
    sendToController({
      type: 'ERROR',
      action: message.action,
      message: error.message
    });
  }
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Forward events to controller
  if (message.type === 'VIDEO_ENDED' || message.type === 'VIDEO_PLAYING') {
    sendToController(message);
  }
  sendResponse({ received: true });
  return true;
});

// ============================================================
// INITIALIZATION
// ============================================================

connect();

// Reconnect on startup
chrome.runtime.onStartup.addListener(() => {
  connect();
});

// Reconnect on install
chrome.runtime.onInstalled.addListener(() => {
  connect();
});
```

### 1.5 popup.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      width: 300px;
      padding: 15px;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 14px;
    }
    h2 {
      margin: 0 0 10px 0;
      color: #333;
    }
    .status {
      padding: 8px;
      border-radius: 4px;
      margin-bottom: 10px;
    }
    .connected { background: #d4edda; color: #155724; }
    .disconnected { background: #f8d7da; color: #721c24; }
    .info { margin: 5px 0; color: #666; }
    button {
      width: 100%;
      padding: 10px;
      margin: 5px 0;
      border: none;
      border-radius: 4px;
      background: #4a90d9;
      color: white;
      cursor: pointer;
    }
    button:hover { background: #357abd; }
  </style>
</head>
<body>
  <h2>🪶 Tribe Browser Control</h2>
  <div id="status" class="status disconnected">Checking connection...</div>
  <div class="info" id="url"></div>
  <button id="getState">Get Page State</button>
  <button id="reconnect">Reconnect</button>
  <pre id="output" style="font-size: 11px; max-height: 200px; overflow: auto;"></pre>
  <script src="popup.js"></script>
</body>
</html>
```

### 1.6 popup.js

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  document.getElementById('url').textContent = tab?.url?.substring(0, 40) + '...';

  document.getElementById('getState').addEventListener('click', async () => {
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'GET_PAGE_STATE' });
      document.getElementById('output').textContent = JSON.stringify(response, null, 2);
    } catch (e) {
      document.getElementById('output').textContent = 'Error: ' + e.message;
    }
  });

  document.getElementById('reconnect').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'RECONNECT' });
  });
});
```

---

## Phase 2: Tribe Controller (Python WebSocket Server)

### 2.1 Create Controller Script

Create `/Users/Shared/ganuda/scripts/tribe_controller.py`:

```python
#!/usr/bin/env python3
"""
Tribe Browser Controller
WebSocket server that receives page state and sends commands to Chrome extension

For Seven Generations.
"""

import asyncio
import json
import websockets
from datetime import datetime

# Connected clients
clients = set()

# Command queue
command_queue = asyncio.Queue()

# ============================================================
# WEBSOCKET SERVER
# ============================================================

async def handle_client(websocket, path):
    """Handle incoming WebSocket connections from Chrome extension"""
    clients.add(websocket)
    print(f"[{datetime.now()}] Extension connected. Total clients: {len(clients)}")

    try:
        async for message in websocket:
            data = json.loads(message)
            await process_message(data, websocket)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        print(f"[{datetime.now()}] Extension disconnected. Total clients: {len(clients)}")


async def process_message(data, websocket):
    """Process messages from extension"""
    msg_type = data.get('type')

    if msg_type == 'EXTENSION_CONNECTED':
        print("[Controller] Extension ready")
        # Request initial page state
        await send_command(websocket, {'action': 'GET_PAGE_STATE'})

    elif msg_type == 'RESPONSE':
        action = data.get('action')
        result = data.get('result')
        print(f"[Response] {action}: {json.dumps(result)[:200]}...")

        # Handle page state
        if action == 'GET_PAGE_STATE':
            await handle_page_state(result, websocket)

    elif msg_type == 'VIDEO_ENDED':
        print("[Event] Video ended!")
        # Auto-click continue button
        await send_command(websocket, {
            'action': 'CLICK',
            'selector': 'button, [class*="continue"], [class*="next"]'
        })

    elif msg_type == 'VIDEO_PLAYING':
        print("[Event] Video started playing")

    elif msg_type == 'ERROR':
        print(f"[Error] {data.get('message')}")


async def handle_page_state(state, websocket):
    """Analyze page state and decide next action"""
    url = state.get('url', '')
    title = state.get('title', '')
    buttons = state.get('buttons', [])
    forms = state.get('forms', [])
    videos = state.get('videos', [])

    print(f"\n[Page] {title}")
    print(f"[URL] {url}")
    print(f"[Buttons] {len(buttons)}, [Forms] {len(forms)}, [Videos] {len(videos)}")

    # Check for videos that need to play
    for video in videos:
        if not video.get('ended') and video.get('paused'):
            print("[Action] Found paused video, clicking to play")
            await send_command(websocket, {
                'action': 'CLICK',
                'selector': video.get('selector', 'video')
            })
            return

    # Check for Continue button
    for btn in buttons:
        text = btn.get('text', '').lower()
        if 'continue' in text or 'next' in text or 'submit' in text:
            print(f"[Action] Found button: {btn['text']}")
            # Don't auto-click, wait for command
            break


async def send_command(websocket, command):
    """Send command to extension"""
    await websocket.send(json.dumps(command))


# ============================================================
# COMMAND INTERFACE
# ============================================================

async def command_interface():
    """Simple command interface for manual control"""
    while True:
        try:
            cmd = await asyncio.get_event_loop().run_in_executor(None, input, "\n[Command] > ")
            cmd = cmd.strip().lower()

            if not clients:
                print("No extension connected")
                continue

            websocket = next(iter(clients))

            if cmd == 'state' or cmd == 's':
                await send_command(websocket, {'action': 'GET_PAGE_STATE'})

            elif cmd == 'continue' or cmd == 'c':
                await send_command(websocket, {
                    'action': 'CLICK',
                    'selector': 'button'
                })

            elif cmd.startswith('click '):
                selector = cmd[6:]
                await send_command(websocket, {'action': 'CLICK', 'selector': selector})

            elif cmd.startswith('type '):
                parts = cmd[5:].split(' ', 1)
                if len(parts) == 2:
                    selector, text = parts
                    await send_command(websocket, {
                        'action': 'TYPE',
                        'selector': selector,
                        'text': text
                    })

            elif cmd == 'scroll' or cmd == 'd':
                await send_command(websocket, {'action': 'SCROLL', 'direction': 'down'})

            elif cmd == 'up' or cmd == 'u':
                await send_command(websocket, {'action': 'SCROLL', 'direction': 'up'})

            elif cmd == 'help' or cmd == 'h':
                print("""
Commands:
  state (s)       - Get current page state
  continue (c)    - Click continue/next button
  click <sel>     - Click element by selector
  type <sel> <txt>- Type text in element
  scroll (d)      - Scroll down
  up (u)          - Scroll up
  help (h)        - Show this help
                """)

            else:
                print("Unknown command. Type 'help' for options.")

        except Exception as e:
            print(f"Error: {e}")


# ============================================================
# MAIN
# ============================================================

async def main():
    print("="*60)
    print("Tribe Browser Controller")
    print("="*60)
    print("Waiting for Chrome extension connection on ws://localhost:8765")
    print("Type 'help' for commands\n")

    server = await websockets.serve(handle_client, "localhost", 8765)

    # Run command interface alongside server
    await asyncio.gather(
        server.wait_closed(),
        command_interface()
    )


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Phase 3: Installation

### 3.1 Install Extension in Chrome

1. Open Chrome on sasass
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right toggle)
4. Click "Load unpacked"
5. Select `/Users/Shared/ganuda/tribe-extension/`
6. Extension should appear with Tribe icon

### 3.2 Start Controller

```bash
# On sasass
pip3 install websockets --user
python3 /Users/Shared/ganuda/scripts/tribe_controller.py
```

### 3.3 Test Connection

1. Controller shows "Extension connected"
2. Type `state` to get page state
3. Type `click button` to click first button

---

## Phase 4: Integration with FARA

### 4.1 When to Use FARA

The extension handles text and DOM interactions. Use FARA only when:
- Image analysis needed (quiz images, charts)
- Visual verification required
- Complex visual decisions

### 4.2 Hybrid Flow

```python
# In controller, when page has images:
if page_state['images'] > 0 and 'quiz' in page_state['url']:
    # Trigger FARA screen capture and analysis
    fara_result = await analyze_with_fara(question)
    # Use result to decide action
```

---

## Alternative: browser-automator Library

### Overview

The [browser-automator](https://github.com/SheikhAminul/browser-automator) library is a **Puppeteer alternative designed specifically for Chrome extensions**. It provides a cleaner API for DOM interaction.

**Benefits:**
- Puppeteer-like API (familiar syntax)
- Built for extension context
- Handles async operations properly
- Works within Chrome's extension sandbox

### Installation

Add to the extension:
```bash
npm init -y
npm install browser-automator
```

Or include directly via the bundled script.

### API Reference

```javascript
import { automator } from 'browser-automator';

// Launch browser instance
const browser = await automator.launch();

// Create new page (tab)
const page = await browser.newPage();

// Navigate
await page.goto('https://example.com');

// Wait for elements
await page.waitForSelector('button.submit');

// Click elements
await page.click('button.submit');
await page.click('#start-task'); // by ID
await page.click('[data-action="continue"]'); // by attribute

// Type into inputs
await page.input('input[name="email"]', 'user@example.com');

// Execute JavaScript in page context
const result = await page.evaluate(() => {
    return document.querySelector('.result').textContent;
});

// Take screenshot
const screenshot = await page.screenshot();

// Check element exists
const exists = await page.elementExists('.success-message');

// Trigger events
await page.triggerEvent('button', 'mouseover');

// Upload files
await page.uploadFiles('input[type="file"]', ['/path/to/file.jpg']);

// Wait for navigation
await page.waitForNavigation();

// Wait for arbitrary time
await page.waitFor(2000); // 2 seconds
```

### Integration with Tribe Controller

Modify `background.js` to use browser-automator:

```javascript
import { automator } from 'browser-automator';

let browser = null;

async function initAutomator() {
    browser = await automator.launch();
}

async function handleControllerMessage(message) {
    const page = await browser.newPage();

    switch (message.action) {
        case 'CLICK':
            await page.click(message.selector);
            return { success: true };

        case 'TYPE':
            await page.input(message.selector, message.text);
            return { success: true };

        case 'WAIT_FOR':
            await page.waitForSelector(message.selector);
            return { success: true, found: true };

        case 'EVALUATE':
            const result = await page.evaluate(message.script);
            return { success: true, result };

        case 'SCREENSHOT':
            const screenshot = await page.screenshot();
            return { success: true, data: screenshot };
    }
}
```

### When to Use

| Approach | Use Case |
|----------|----------|
| Custom content.js | Simple DOM reads, basic clicks |
| browser-automator | Complex workflows, multi-step automation |
| Hybrid | Use automator for actions, content.js for events |

---

## Security Considerations (Council Concerns)

### From Crawdad (Security):
- [ ] WebSocket uses localhost only (no external exposure)
- [ ] Pre-shared key authentication between extension and controller
- [ ] Extension has minimal permissions

### From Raven (Strategy):
- [ ] Plan for updates in air-gapped environment
- [ ] Controller redundancy (not single point of failure)
- [ ] Secure deployment process

### Implementation:
```javascript
// In background.js - add authentication
const AUTH_KEY = 'tribe-secret-key-here'; // Store securely

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'AUTH', key: AUTH_KEY }));
};
```

```python
# In controller - verify auth
async def process_message(data, websocket):
    if data.get('type') == 'AUTH':
        if data.get('key') != EXPECTED_KEY:
            await websocket.close()
            return
```

---

## Testing

### Test 1: Page State
```
[Command] > state
[Page] Aether Certification
[URL] https://...
[Buttons] 3, [Forms] 1, [Videos] 1
```

### Test 2: Click Button
```
[Command] > click button.continue
[Response] CLICK: {"success": true, "message": "Clicked button.continue"}
```

### Test 3: Video Event
```
[Event] Video ended!
[Action] Auto-clicking continue
```

### Test 4: Form Fill
```
[Command] > type input[name="email"] test@example.com
[Response] TYPE: {"success": true}
```

---

## Success Criteria

- [ ] Extension loads in Chrome without errors
- [ ] WebSocket connects to controller
- [ ] Page state retrieval works
- [ ] Click by selector works
- [ ] Form typing works
- [ ] Video end event detected
- [ ] Works over SSH (controller on remote machine)
- [ ] FARA integration for image analysis

---

*For Seven Generations.*
