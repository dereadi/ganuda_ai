# Jr Build Instructions: FARA Browser Control via chrome-mcp

## Priority: HIGH - Council Approved (Audit: 0e559d2303f6c93e)

---

## Council Decision Summary

**Question**: Which approach for FARA visual AI to control browser (scroll, click, type)?

**Options Evaluated**:
- A) AppleScript - Simple but limited DOM access
- B) browser-use - Requires cloud API (❌ air-gap incompatible)
- C) chrome-mcp - Local DevTools Protocol (✅ APPROVED)

**Vote**: 7/7 specialists recommend **Option C (chrome-mcp)**

**Rationale**: Air-gapped environment goal requires local-only solution. chrome-mcp provides full browser control via Chrome DevTools Protocol without any external dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         sasass (Mac Studio)                      │
│                         192.168.132.241                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SCREEN CAPTURE (via GUI Terminal trick)                      │
│     └──▶ /tmp/fara_screen_capture.png                           │
│                                                                  │
│  2. FARA ANALYSIS (Qwen2.5-VL 7B on MPS)                        │
│     └──▶ "Fail - The expression does not match..."              │
│                                                                  │
│  3. CHROME-MCP EXECUTION                                         │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  Chrome Browser                                          │ │
│     │  --remote-debugging-port=9222                            │ │
│     │                                                          │ │
│     │  ◄────── CDP WebSocket ──────►  chrome-mcp server        │ │
│     │                                 (Bun/TypeScript)         │ │
│     │                                 localhost:3000           │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                  │
│  4. ACTIONS EXECUTED                                             │
│     • click(selector: "textarea.answer-input")                  │
│     • type(text: "Fail - The expression does not match...")     │
│     • click(selector: "button.submit")                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Install chrome-mcp on sasass

### 1.1 Install Bun (JavaScript runtime)

```bash
# On sasass
curl -fsSL https://bun.sh/install | bash

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Verify
bun --version
```

### 1.2 Clone and Install chrome-mcp

```bash
# Clone repository
cd /Users/Shared/ganuda/services
git clone https://github.com/lxe/chrome-mcp.git
cd chrome-mcp

# Install dependencies
bun install
```

### 1.3 Create Chrome Launch Script

Create `/Users/Shared/ganuda/scripts/start_chrome_debug.sh`:

```bash
#!/bin/bash
# Start Chrome with remote debugging enabled for chrome-mcp

CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT=9222

# Check if Chrome is already running with debug port
if lsof -i :$DEBUG_PORT > /dev/null 2>&1; then
    echo "Chrome already running on port $DEBUG_PORT"
    exit 0
fi

# Launch Chrome with debugging
"$CHROME_APP" --remote-debugging-port=$DEBUG_PORT &

echo "Chrome started with remote debugging on port $DEBUG_PORT"
```

```bash
chmod +x /Users/Shared/ganuda/scripts/start_chrome_debug.sh
```

### 1.4 Create chrome-mcp Service Script

Create `/Users/Shared/ganuda/scripts/start_chrome_mcp.sh`:

```bash
#!/bin/bash
# Start chrome-mcp server

cd /Users/Shared/ganuda/services/chrome-mcp
bun start
```

---

## Phase 2: Integration Script

### 2.1 FARA + chrome-mcp Integration

Create `/Users/Shared/ganuda/scripts/fara_browser.py`:

```python
#!/usr/bin/env python3
"""
FARA Browser Control - Visual AI + chrome-mcp integration
Captures screen, analyzes with FARA, executes browser actions via chrome-mcp
"""

import subprocess
import sys
import time
import os
import json
import requests
from PIL import Image
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

# Configuration
MODEL_PATH = "/Users/Shared/ganuda/models/fara-7b"
SCREENSHOT_PATH = "/tmp/fara_screen_capture.png"
CAPTURE_SCRIPT = "/tmp/fara_capture.sh"
CHROME_MCP_URL = "http://localhost:3000"

# ============================================================
# Screen Capture (GUI Terminal trick for SSH compatibility)
# ============================================================

def capture_screen_gui():
    """Capture screen using GUI Terminal to work over SSH"""
    with open(CAPTURE_SCRIPT, 'w') as f:
        f.write(f'#!/bin/bash\nscreencapture -x {SCREENSHOT_PATH}\n')
    os.chmod(CAPTURE_SCRIPT, 0o755)

    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)

    subprocess.run(['open', '-a', 'Terminal', CAPTURE_SCRIPT], check=True)

    for _ in range(10):
        time.sleep(0.5)
        if os.path.exists(SCREENSHOT_PATH):
            time.sleep(0.3)
            return True
    return False

# ============================================================
# chrome-mcp Browser Control
# ============================================================

def chrome_mcp_action(action: str, params: dict) -> dict:
    """Execute action via chrome-mcp server"""
    try:
        response = requests.post(
            f"{CHROME_MCP_URL}/action",
            json={"action": action, **params},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def browser_click(selector: str) -> dict:
    """Click an element by CSS selector"""
    return chrome_mcp_action("click", {"selector": selector})

def browser_click_element(selector: str) -> dict:
    """Click element using clickElement action"""
    return chrome_mcp_action("clickElement", {"selector": selector})

def browser_type(text: str) -> dict:
    """Type text (assumes element is focused)"""
    return chrome_mcp_action("type", {"text": text})

def browser_type_in_field(selector: str, text: str) -> dict:
    """Click field then type text"""
    click_result = browser_click(selector)
    if "error" in click_result:
        return click_result
    time.sleep(0.3)
    return browser_type(text)

def browser_navigate(url: str) -> dict:
    """Navigate to URL"""
    return chrome_mcp_action("navigate", {"url": url})

def browser_get_text(selector: str) -> dict:
    """Get text content of element"""
    return chrome_mcp_action("getText", {"selector": selector})

def browser_get_page_state() -> dict:
    """Get current page state"""
    return chrome_mcp_action("getPageState", {})

# ============================================================
# FARA Visual Analysis
# ============================================================

def load_fara_model():
    """Load FARA model (cached after first load)"""
    print("Loading FARA model...")
    processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="mps",
        trust_remote_code=True
    )
    return processor, model

def analyze_screen(processor, model, question: str, crop_bounds=None) -> str:
    """Analyze screenshot with FARA"""

    img = Image.open(SCREENSHOT_PATH)

    # Crop if specified
    if crop_bounds:
        img = img.crop(crop_bounds)
    else:
        # Default: crop to left 2000px for Chrome
        img = img.crop((0, 0, min(2000, img.width), img.height))

    # Resize for MPS memory
    MAX_DIM = 1600
    if max(img.size) > MAX_DIM:
        ratio = MAX_DIM / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    messages = [{
        'role': 'user',
        'content': [
            {'type': 'image', 'image': img},
            {'type': 'text', 'text': question}
        ]
    }]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[img], return_tensors='pt').to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=600)
    response = processor.decode(outputs[0], skip_special_tokens=True)

    if 'assistant' in response.lower():
        response = response.split('assistant')[-1].strip()

    import re
    response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL).strip()

    return response

# ============================================================
# High-Level Actions
# ============================================================

def answer_quiz(processor, model, input_selector: str = "textarea", submit_selector: str = None):
    """
    Complete workflow: capture screen, analyze quiz, type answer

    Args:
        input_selector: CSS selector for the answer text field
        submit_selector: CSS selector for submit button (optional)
    """

    # 1. Capture screen
    print("Capturing screen...")
    if not capture_screen_gui():
        return {"error": "Screen capture failed"}

    # 2. Analyze with FARA
    print("Analyzing quiz with FARA...")
    question = """Describe what you see in this browser window.
There is a table with images showing Target Image, Source Image, Prompt, and Output.
Read the Prompt text and carefully examine all images.
Compare the Output image to what the Prompt requested.
Look for:
- Expression mismatches (smiling vs serious)
- Head/body proportion issues
- Artifacts from original image bleeding through
- Identity characteristics preserved or lost

Based on your analysis, provide a verdict in this exact format:
"Pass - [detailed justification]" or "Fail - [detailed justification]"
"""

    answer = analyze_screen(processor, model, question)
    print(f"\nFARA Answer: {answer}\n")

    # 3. Click input field and type answer
    print(f"Clicking input field: {input_selector}")
    click_result = browser_click(input_selector)
    if "error" in click_result:
        print(f"Click failed: {click_result}")
        # Try alternative method
        click_result = browser_click_element(input_selector)

    time.sleep(0.3)

    print("Typing answer...")
    type_result = browser_type(answer)

    # 4. Optionally submit
    if submit_selector:
        print(f"Clicking submit: {submit_selector}")
        time.sleep(0.5)
        browser_click(submit_selector)

    return {
        "answer": answer,
        "click_result": click_result,
        "type_result": type_result
    }

# ============================================================
# Main Entry Point
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='FARA Browser Control')
    parser.add_argument('--action', choices=['analyze', 'answer', 'click', 'type', 'navigate'],
                        default='analyze', help='Action to perform')
    parser.add_argument('--question', type=str, help='Question to ask FARA')
    parser.add_argument('--selector', type=str, help='CSS selector for click/type')
    parser.add_argument('--text', type=str, help='Text to type')
    parser.add_argument('--url', type=str, help='URL to navigate to')
    parser.add_argument('--submit', type=str, help='Submit button selector')

    args = parser.parse_args()

    if args.action == 'analyze':
        # Just analyze screen
        print("Capturing screen...")
        if not capture_screen_gui():
            print("ERROR: Screen capture failed")
            sys.exit(1)

        processor, model = load_fara_model()
        question = args.question or "Describe what you see on this screen."
        result = analyze_screen(processor, model, question)
        print("\n" + "="*60)
        print("FARA Analysis:")
        print("="*60)
        print(result)

    elif args.action == 'answer':
        # Full quiz answering workflow
        processor, model = load_fara_model()
        selector = args.selector or "textarea"
        result = answer_quiz(processor, model, selector, args.submit)
        print("\n" + "="*60)
        print("Result:")
        print("="*60)
        print(json.dumps(result, indent=2))

    elif args.action == 'click':
        if not args.selector:
            print("ERROR: --selector required for click action")
            sys.exit(1)
        result = browser_click(args.selector)
        print(json.dumps(result, indent=2))

    elif args.action == 'type':
        if not args.text:
            print("ERROR: --text required for type action")
            sys.exit(1)
        result = browser_type(args.text)
        print(json.dumps(result, indent=2))

    elif args.action == 'navigate':
        if not args.url:
            print("ERROR: --url required for navigate action")
            sys.exit(1)
        result = browser_navigate(args.url)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

---

## Phase 3: Testing

### 3.1 Test chrome-mcp Connection

```bash
# Terminal 1: Start Chrome with debugging
/Users/Shared/ganuda/scripts/start_chrome_debug.sh

# Terminal 2: Start chrome-mcp server
cd /Users/Shared/ganuda/services/chrome-mcp
bun start

# Terminal 3: Test connection
curl http://localhost:3000/health
```

### 3.2 Test Browser Actions

```bash
# Navigate
curl -X POST http://localhost:3000/action \
  -H "Content-Type: application/json" \
  -d '{"action": "navigate", "url": "https://example.com"}'

# Get page info
curl -X POST http://localhost:3000/action \
  -H "Content-Type: application/json" \
  -d '{"action": "getPageInfo"}'

# Click element
curl -X POST http://localhost:3000/action \
  -H "Content-Type: application/json" \
  -d '{"action": "click", "selector": "a"}'
```

### 3.3 Test Full FARA + Browser Workflow

```bash
# Just analyze screen
python3 /Users/Shared/ganuda/scripts/fara_browser.py --action analyze

# Answer quiz (captures, analyzes, types answer)
python3 /Users/Shared/ganuda/scripts/fara_browser.py --action answer --selector "textarea"

# With submit button
python3 /Users/Shared/ganuda/scripts/fara_browser.py --action answer --selector "textarea" --submit "button.submit"
```

---

## Phase 4: LaunchAgent for Auto-Start (Optional)

### 4.1 chrome-mcp LaunchAgent

Create `~/Library/LaunchAgents/com.ganuda.chrome-mcp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ganuda.chrome-mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/dereadi/.bun/bin/bun</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda/services/chrome-mcp</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/chrome-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/chrome-mcp.error.log</string>
</dict>
</plist>
```

```bash
# Load the agent
launchctl load ~/Library/LaunchAgents/com.ganuda.chrome-mcp.plist

# Check status
launchctl list | grep chrome-mcp
```

---

## Troubleshooting

### Chrome not connecting
```bash
# Check if Chrome is running with debug port
lsof -i :9222

# If not, restart Chrome with debugging
pkill "Google Chrome"
/Users/Shared/ganuda/scripts/start_chrome_debug.sh
```

### chrome-mcp server not responding
```bash
# Check if server is running
curl http://localhost:3000/health

# Check logs
tail -f /tmp/chrome-mcp.log
tail -f /tmp/chrome-mcp.error.log

# Restart server
cd /Users/Shared/ganuda/services/chrome-mcp
bun start
```

### FARA memory issues
```bash
# Reduce image size in script
# Edit MAX_DIM from 1600 to 1280
```

### Screen capture shows wallpaper (SSH issue)
```bash
# Must use GUI Terminal trick - the script handles this automatically
# If running locally on sasass, direct screencapture works
```

---

## Success Criteria

- [ ] Bun installed on sasass
- [ ] chrome-mcp cloned and dependencies installed
- [ ] Chrome launches with --remote-debugging-port=9222
- [ ] chrome-mcp server starts and responds to health check
- [ ] Browser actions work (navigate, click, type)
- [ ] FARA + chrome-mcp integration script works
- [ ] Can answer Aether quiz automatically
- [ ] LaunchAgent configured for auto-start (optional)

---

## Security Notes

1. **Local only**: chrome-mcp binds to localhost:3000, not accessible externally
2. **Debug port**: Chrome debug port 9222 is localhost only
3. **Air-gap ready**: No external network calls required
4. **Credential safety**: Don't use for sites with sensitive logins while debugging enabled

---

## Future Enhancements

1. **Persistent FARA service**: Keep model loaded to reduce latency
2. **Action queue**: Queue multiple actions for complex workflows
3. **Error recovery**: Retry logic for failed actions
4. **Visual feedback**: Screenshot after each action to verify success
5. **Telegram integration**: `/browse` command to control browser remotely

---

*For Seven Generations*
