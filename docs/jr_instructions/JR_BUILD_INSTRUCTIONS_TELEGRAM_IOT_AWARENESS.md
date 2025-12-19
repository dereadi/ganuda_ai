# Jr Build Instructions: Telegram Bot IoT Awareness & Self-Learning

**Priority**: MEDIUM
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Integration Jr / IT Triad Jr
**Date**: December 13, 2025

## Objective

Enhance the Telegram bot (`telegram_chief.py`) with:
1. **IoT Awareness** - Query and report on IoT device inventory
2. **Self-Learning** - Store interaction patterns in thermal memory
3. **Proactive Alerts** - Notify TPM of new/unauthorized devices

## Current State

The bot already has:
- `TribeInterface` class for Council queries
- `classify_request()` for routing
- Connection to LLM Gateway on redfin:8080
- Database access via gateway API

## Architecture Enhancement

```
┌─────────────────────────────────────────────────────────────────┐
│                    Telegram Bot (redfin)                         │
├─────────────────────────────────────────────────────────────────┤
│  classify_request()                                              │
│       │                                                          │
│       ├─ diagnostic → Eagle Eye (IT Jr)                          │
│       ├─ iot_query → NEW: IoT Handler ◄── Query iot_devices      │
│       ├─ action → Council Vote                                   │
│       └─ query → Council                                         │
├─────────────────────────────────────────────────────────────────┤
│  Self-Learning Module                                            │
│       │                                                          │
│       ├─ Log interactions → thermal_memory_archive               │
│       ├─ Learn patterns → Improve classify_request()             │
│       └─ Recall context → Query past interactions                │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Add IoT Query Methods to TribeInterface

Add to `/ganuda/telegram_bot/telegram_chief.py`:

```python
class TribeInterface:
    # ... existing methods ...

    def query_iot_devices(self, filter_type: str = None) -> dict:
        """Query IoT device inventory from database"""
        try:
            # Build query based on filter
            if filter_type == "active":
                query = "SELECT * FROM iot_devices WHERE status = 'active' ORDER BY last_seen DESC LIMIT 20"
            elif filter_type == "unauthorized":
                query = "SELECT * FROM iot_devices WHERE is_authorized IS NULL OR is_authorized = false ORDER BY first_seen DESC LIMIT 10"
            elif filter_type == "new":
                query = "SELECT * FROM iot_devices WHERE first_seen > now() - interval '24 hours' ORDER BY first_seen DESC"
            else:
                query = "SELECT ip_address, mac_address, vendor, device_class, status FROM iot_devices ORDER BY last_seen DESC LIMIT 15"

            response = requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_iot_summary(self) -> dict:
        """Get IoT device summary statistics"""
        try:
            query = """
                SELECT
                    status,
                    count(*) as count,
                    count(*) FILTER (WHERE is_authorized = true) as authorized,
                    count(*) FILTER (WHERE is_authorized IS NULL) as pending_auth
                FROM iot_devices
                GROUP BY status
            """
            response = requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def authorize_iot_device(self, mac_address: str, authorized: bool, notes: str = None) -> dict:
        """Authorize or block an IoT device"""
        try:
            query = f"""
                UPDATE iot_devices
                SET is_authorized = {authorized},
                    notes = COALESCE(notes || ' | ', '') || '{notes or "Updated via Telegram"}'
                WHERE mac_address = '{mac_address}'
                RETURNING ip_address, mac_address, vendor, is_authorized
            """
            response = requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
```

## Step 2: Update classify_request() for IoT

Modify the `classify_request()` function:

```python
def classify_request(message: str) -> dict:
    """Classify user request type"""
    message_lower = message.lower()

    # NEW: IoT-related queries
    iot_keywords = ['iot', 'device', 'devices', 'network scan', 'mac address',
                    'unauthorized', 'smart home', 'sonos', 'daikin', 'tuya',
                    'espressif', 'discovered', 'new devices']
    if any(k in message_lower for k in iot_keywords):
        return {"type": "iot_query", "tpm_wait": False, "route_to": "iot_handler"}

    # ... existing classification logic ...
```

## Step 3: Add IoT Command Handlers

Add new command handlers:

```python
async def iot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /iot command - show IoT device summary"""
    tribe = TribeInterface()
    summary = tribe.get_iot_summary()

    if "error" in summary:
        await update.message.reply_text(f"Error: {summary['error']}")
        return

    lines = ["📡 IoT Device Inventory\n"]

    total = 0
    for row in summary.get("rows", []):
        status = row.get("status", "unknown")
        count = row.get("count", 0)
        authorized = row.get("authorized", 0)
        pending = row.get("pending_auth", 0)
        total += count
        lines.append(f"  {status.upper()}: {count} ({authorized} auth, {pending} pending)")

    lines.append(f"\nTotal: {total} devices")
    lines.append("\nCommands:")
    lines.append("/iot_active - Show active devices")
    lines.append("/iot_new - Show new devices (24h)")
    lines.append("/iot_unauth - Show unauthorized devices")

    await update.message.reply_text("\n".join(lines))


async def iot_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /iot_active command"""
    tribe = TribeInterface()
    devices = tribe.query_iot_devices("active")

    if "error" in devices:
        await update.message.reply_text(f"Error: {devices['error']}")
        return

    lines = ["🟢 Active IoT Devices\n"]
    for dev in devices.get("rows", [])[:15]:
        ip = dev.get("ip_address", "?")
        vendor = dev.get("vendor", "Unknown")[:20]
        device_class = dev.get("device_class", "")
        auth = "✓" if dev.get("is_authorized") else "?"
        lines.append(f"  {auth} {ip} - {vendor} {device_class}")

    await update.message.reply_text("\n".join(lines))


async def iot_unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /iot_unauth command - show unauthorized devices"""
    tribe = TribeInterface()
    devices = tribe.query_iot_devices("unauthorized")

    if "error" in devices:
        await update.message.reply_text(f"Error: {devices['error']}")
        return

    rows = devices.get("rows", [])
    if not rows:
        await update.message.reply_text("✅ No unauthorized devices detected.")
        return

    lines = ["⚠️ Unauthorized/Pending Devices\n"]
    for dev in rows[:10]:
        ip = dev.get("ip_address", "?")
        mac = dev.get("mac_address", "?")
        vendor = dev.get("vendor", "Unknown")[:25]
        lines.append(f"  {ip} ({mac})")
        lines.append(f"    Vendor: {vendor}")

    lines.append("\nTo authorize: /iot_auth <mac_address>")
    lines.append("To block: /iot_block <mac_address>")

    await update.message.reply_text("\n".join(lines))


async def iot_authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /iot_auth command - authorize a device"""
    if not context.args:
        await update.message.reply_text("Usage: /iot_auth <mac_address> [notes]")
        return

    mac = context.args[0]
    notes = " ".join(context.args[1:]) if len(context.args) > 1 else "Authorized via Telegram"

    tribe = TribeInterface()
    result = tribe.authorize_iot_device(mac, True, notes)

    if "error" in result:
        await update.message.reply_text(f"Error: {result['error']}")
    else:
        await update.message.reply_text(f"✅ Device {mac} authorized.")
```

## Step 4: Self-Learning Module

Add thermal memory integration for self-learning:

```python
class SelfLearningModule:
    """Store and retrieve interaction patterns in thermal memory"""

    def __init__(self, tribe_interface):
        self.tribe = tribe_interface

    def log_interaction(self, user_id: int, message: str, classification: dict,
                        response_type: str, was_helpful: bool = None):
        """Log interaction to thermal memory for learning"""
        try:
            content = f"""Telegram Interaction Log
User ID: {user_id}
Message: {message}
Classification: {classification}
Response Type: {response_type}
Helpful: {was_helpful}
Timestamp: {datetime.now().isoformat()}"""

            query = f"""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
                VALUES (
                    'TELEGRAM-{user_id}-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    $${content}$$,
                    'FRESH',
                    75.0,
                    false
                )
            """
            requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.tribe.headers,
                json={"query": query},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

    def get_similar_interactions(self, message: str, limit: int = 5) -> list:
        """Find similar past interactions for context"""
        try:
            # Simple keyword matching - could be enhanced with embeddings
            keywords = message.lower().split()[:5]
            like_clauses = " OR ".join([f"original_content ILIKE '%{k}%'" for k in keywords])

            query = f"""
                SELECT original_content, temperature_score
                FROM thermal_memory_archive
                WHERE memory_hash LIKE 'TELEGRAM-%'
                AND ({like_clauses})
                ORDER BY temperature_score DESC
                LIMIT {limit}
            """
            response = requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.tribe.headers,
                json={"query": query},
                timeout=10
            )
            return response.json().get("rows", [])
        except:
            return []

    def learn_classification_pattern(self, message: str, correct_type: str):
        """Learn from corrections to improve future classification"""
        # Store pattern for future reference
        content = f"""Classification Learning
Pattern: {message}
Correct Type: {correct_type}
Learned: {datetime.now().isoformat()}

This pattern should be classified as '{correct_type}' in future."""

        try:
            query = f"""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
                VALUES (
                    'LEARN-CLASSIFY-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    $${content}$$,
                    'WARM',
                    90.0,
                    true
                )
            """
            requests.post(
                f"{GATEWAY_URL}/v1/sql/query",
                headers=self.tribe.headers,
                json={"query": query},
                timeout=10
            )
            return True
        except:
            return False
```

## Step 5: Proactive IoT Alerts

Add a background task to check for new devices:

```python
async def check_new_devices(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check for new IoT devices and alert TPM"""
    tribe = TribeInterface()

    try:
        query = """
            SELECT ip_address, mac_address, vendor, first_seen
            FROM iot_devices
            WHERE first_seen > now() - interval '1 hour'
            AND is_authorized IS NULL
        """
        response = requests.post(
            f"{GATEWAY_URL}/v1/sql/query",
            headers=tribe.headers,
            json={"query": query},
            timeout=30
        )

        devices = response.json().get("rows", [])
        if devices:
            lines = ["🆕 New IoT Devices Detected!\n"]
            for dev in devices:
                ip = dev.get("ip_address", "?")
                mac = dev.get("mac_address", "?")
                vendor = dev.get("vendor", "Unknown")
                lines.append(f"  {ip} - {vendor}")
                lines.append(f"    MAC: {mac}")

            lines.append("\nUse /iot_auth <mac> to authorize")

            # Send to TPM chat (configure this ID)
            TPM_CHAT_ID = os.environ.get("TPM_CHAT_ID")
            if TPM_CHAT_ID:
                await context.bot.send_message(
                    chat_id=TPM_CHAT_ID,
                    text="\n".join(lines)
                )
    except Exception as e:
        logger.error(f"New device check failed: {e}")


def main():
    """Start the bot"""
    # ... existing setup ...

    # Add IoT handlers
    app.add_handler(CommandHandler("iot", iot_status))
    app.add_handler(CommandHandler("iot_active", iot_active))
    app.add_handler(CommandHandler("iot_new", iot_new))
    app.add_handler(CommandHandler("iot_unauth", iot_unauthorized))
    app.add_handler(CommandHandler("iot_auth", iot_authorize))
    app.add_handler(CommandHandler("iot_block", iot_block))

    # Schedule background job for new device alerts
    job_queue = app.job_queue
    job_queue.run_repeating(check_new_devices, interval=3600, first=60)  # Every hour

    # ... rest of main ...
```

## Step 6: Register Commands

Update the help text and register with Telegram:

```python
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "Cherokee AI - Tribe Interface\n\n"
        "Commands:\n"
        "/status - Cluster health\n"
        "/pending - View pending approvals\n"
        "/approve <hash> - Approve a decision\n"
        "/veto <hash> <reason> - Veto a decision\n\n"
        "📡 IoT Commands:\n"
        "/iot - Device inventory summary\n"
        "/iot_active - Show active devices\n"
        "/iot_new - New devices (24h)\n"
        "/iot_unauth - Unauthorized devices\n"
        "/iot_auth <mac> - Authorize device\n"
        "/iot_block <mac> - Block device\n\n"
        "Ask anything - I learn from our interactions!"
    )
```

## Verification Checklist

- [ ] IoT query methods added to TribeInterface
- [ ] classify_request() updated with IoT keywords
- [ ] /iot, /iot_active, /iot_new, /iot_unauth commands added
- [ ] /iot_auth and /iot_block commands added
- [ ] SelfLearningModule class added
- [ ] Interactions logging to thermal_memory_archive
- [ ] Background job for new device alerts
- [ ] Help text updated
- [ ] TPM_CHAT_ID environment variable set
- [ ] Bot restarted and tested

## Environment Variables Needed

```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TPM_CHAT_ID="your-telegram-chat-id"  # For proactive alerts
```

## Testing

```bash
# In Telegram, test these commands:
/iot
/iot_active
/iot_unauth

# Test natural language IoT queries:
"What IoT devices are online?"
"Show me unauthorized devices"
"Any new devices discovered?"
```

---

FOR SEVEN GENERATIONS - Self-learning systems grow wiser with each interaction.
