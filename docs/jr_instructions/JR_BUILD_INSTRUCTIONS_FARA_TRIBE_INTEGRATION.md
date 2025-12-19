# Jr Build Instructions: FARA Tribe Integration

## Priority: HIGH - TPM Requests Visual Q&A via Tribe

---

## Problem Statement

TPM wants to ask questions about what's displayed on sasass screen through natural language, using the existing Tribe infrastructure (Telegram bot, Council).

**Example interactions:**
- Telegram: "Look at my Chrome browser and answer the question displayed"
- Telegram: "What error is showing in Terminal?"
- Telegram: "Read the form on screen and tell me what fields are missing"

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TPM (Telegram)                              │
│              "Look at Chrome and answer the question"            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Telegram Bot (redfin)                          │
│                   /look command handler                          │
│                   Detects visual keywords                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM Gateway (redfin)                           │
│                   POST /v1/visual/analyze                        │
│                   Routes to sasass FARA                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SSH
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   sasass (Mac Studio)                            │
│                   FARA-7B Screen Analysis                        │
│                   Returns observation                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### 1. Gateway Endpoint for Visual Analysis

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
import subprocess
import asyncio

SASASS_HOST = "192.168.132.241"
SASASS_USER = "dereadi"
FARA_SCRIPT = "/Users/Shared/ganuda/scripts/fara_look.py"

@app.post("/v1/visual/analyze")
async def visual_analyze(request: dict, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Route visual analysis request to sasass FARA"""

    question = request.get("question", "What do you see on this screen?")

    # Escape question for shell
    safe_question = question.replace("'", "'\\''")

    # Execute FARA on sasass via SSH
    cmd = f"ssh {SASASS_USER}@{SASASS_HOST} \"python3 {FARA_SCRIPT} '{safe_question}'\""

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        output = stdout.decode()

        # Extract FARA response from output
        if "FARA Response:" in output:
            response = output.split("FARA Response:")[-1].strip()
            response = response.replace("=" * 60, "").strip()
        else:
            response = output

        return {
            "status": "success",
            "observation": response,
            "source": "sasass/fara-7b"
        }

    except asyncio.TimeoutError:
        return {"status": "error", "message": "FARA analysis timed out (120s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### 2. Telegram /look Command

Add to `/ganuda/telegram_bot/telegram_chief.py`:

```python
async def look_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Visual analysis of sasass screen: /look [question]"""

    question = " ".join(context.args) if context.args else "What do you see on this screen?"

    await update.message.reply_text(f"Looking at sasass screen...")

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/visual/analyze",
            headers={"X-API-Key": API_KEY},
            json={"question": question},
            timeout=130
        )

        if response.ok:
            data = response.json()
            if data.get("status") == "success":
                await update.message.reply_text(f"FARA: {data['observation']}")
            else:
                await update.message.reply_text(f"Error: {data.get('message')}")
        else:
            await update.message.reply_text(f"Gateway error: {response.status_code}")

    except requests.Timeout:
        await update.message.reply_text("FARA timed out - screen analysis takes ~30 seconds")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Register handler
application.add_handler(CommandHandler("look", look_command))
```

### 3. Natural Language Detection (No /look required)

Detect visual requests in regular messages:

```python
VISUAL_KEYWORDS = [
    "look at", "what's on screen", "screen shows", "chrome browser",
    "what do you see", "read the", "terminal shows", "error on screen",
    "what's displayed", "my screen", "look at my"
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language messages"""
    text = update.message.text.lower()

    # Check if this is a visual request
    is_visual = any(kw in text for kw in VISUAL_KEYWORDS)

    if is_visual:
        # Route to FARA
        await update.message.reply_text("Checking sasass screen...")
        response = requests.post(
            f"{GATEWAY_URL}/v1/visual/analyze",
            headers={"X-API-Key": API_KEY},
            json={"question": update.message.text},
            timeout=130
        )
        # ... handle response
    else:
        # Route to Council as normal
        # ... existing council logic
```

---

## Alternative: Direct SSH from Telegram Bot

If gateway changes are complex, telegram bot can SSH directly:

```python
import asyncio

async def look_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Visual analysis via direct SSH to sasass"""

    question = " ".join(context.args) if context.args else "What do you see?"
    safe_question = question.replace("'", "'\\''")

    await update.message.reply_text("Analyzing sasass screen (~30 sec)...")

    cmd = f"ssh dereadi@192.168.132.241 \"python3 /Users/Shared/ganuda/scripts/fara_look.py '{safe_question}'\""

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

    output = stdout.decode()
    if "FARA Response:" in output:
        response = output.split("FARA Response:")[-1].strip()
        response = response.replace("=" * 60, "").strip()
        await update.message.reply_text(f"FARA: {response}")
    else:
        await update.message.reply_text(f"FARA output: {output[-500:]}")
```

---

## SSH Key Setup (redfin → sasass)

Ensure redfin can SSH to sasass without password:

```bash
# On redfin, generate key if needed
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Copy to sasass
ssh-copy-id dereadi@192.168.132.241

# Test
ssh dereadi@192.168.132.241 "echo OK"
```

---

## Testing

### 1. Test Gateway Endpoint
```bash
curl -X POST http://192.168.132.223:8080/v1/visual/analyze \
  -H "X-API-Key: ck-..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What browser tabs are open?"}'
```

### 2. Test Telegram
```
/look What's on my Chrome browser?
/look Read the error message
/look What form is displayed?
```

### 3. Test Natural Language
```
"Hey, look at my screen and tell me what the question is"
"What's showing in Chrome right now?"
```

---

## Success Criteria

- [ ] Gateway `/v1/visual/analyze` endpoint working
- [ ] SSH from redfin to sasass working
- [ ] Telegram `/look` command responds with FARA analysis
- [ ] Natural language visual requests detected and routed
- [ ] Response time under 60 seconds (including model load)
- [ ] Errors handled gracefully with user feedback

---

## Future: Persistent FARA Service

To reduce latency from ~30s to ~5s:

1. Run FARA as persistent service on sasass (port 8081)
2. Keep model loaded in memory
3. Gateway calls HTTP instead of SSH

See: `JR_BUILD_INSTRUCTIONS_FARA_VISUAL_ASSISTANT.md` for service design.

---

*For Seven Generations*
