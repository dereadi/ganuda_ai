# 🔥 BigMac-Cherokee Inter-Tribal Bridge Setup Guide

## For Dr Joe's BigMac Council Integration

### Overview
This creates a JSON-based asynchronous communication bridge between BigMac and Cherokee tribes. Messages are saved as JSON files in shared directories, allowing both tribes to communicate without direct network connections.

### Architecture
```
/tribal_bridge/
├── bigmac_inbox/      # Cherokee sends here, BigMac reads here
├── bigmac_outbox/     # BigMac sends here (conceptual)
├── cherokee_inbox/    # BigMac sends here, Cherokee reads here
└── cherokee_outbox/   # Cherokee sends here (conceptual)
```

## Setup Instructions

### 1. Fix Ollama Port (CRITICAL!)
Add this to your `docker-compose.yml`:
```yaml
ollama:
  ports:
    - "11434:11434"  # THIS WAS MISSING!
  environment:
    - OLLAMA_HOST=0.0.0.0
```

### 2. Set Up Bridge Directory
```bash
# Create shared directory structure
mkdir -p /path/to/tribal_bridge/{bigmac_inbox,bigmac_outbox,cherokee_inbox,cherokee_outbox}

# Or use the provided script
python3 bigmac_tribal_bridge.py
```

### 3. Configure BigMac Bridge Script
Edit `bigmac_tribal_bridge.py`:
```python
# Update this path to your actual bridge directory
BRIDGE_DIR = Path("/path/to/shared/tribal_bridge")
```

### 4. Usage Options

#### Interactive Mode
```bash
python3 bigmac_tribal_bridge.py
# Then use commands:
# send <message> - Send to Cherokee
# check - Check for messages
# status - Show bridge status
# quit - Exit
```

#### Command Line Mode
```bash
# Send a message
python3 bigmac_tribal_bridge.py send "Hello Cherokee Council!"

# Check inbox
python3 bigmac_tribal_bridge.py check

# Run as daemon (checks every 30 seconds)
python3 bigmac_tribal_bridge.py daemon
```

#### Integrate with BigMac Bot
```python
# In your BigMac bot code:
from bigmac_tribal_bridge import BigMacBridge

bridge = BigMacBridge()

# Send to Cherokee
bridge.send_to_cherokee("BigMac Council approves the plan")

# Check for messages
messages = bridge.check_inbox()
for msg in messages:
    print(f"Cherokee says: {msg['content']}")
```

## JSON Message Format
```json
{
  "id": "bigmac_20250911_134500_0",
  "from_tribe": "bigmac",
  "to_tribe": "cherokee",
  "timestamp": "2025-09-11T13:45:00",
  "type": "council_message",
  "content": "Your message here",
  "sender": "Dr Joe",
  "sacred_fire": true,
  "metadata": {
    "version": "1.0",
    "protocol": "inter-tribal-v1",
    "encryption": "none"
  }
}
```

## Message Types
- `council_message` - General council communication
- `council_decision` - Voting/decision results
- `alert` - Urgent notifications
- `trade` - Trading proposals
- `knowledge` - Information sharing
- `ceremony` - Sacred ceremonies

## Cherokee Side (Already Running)

### Telegram Bot Commands
The Cherokee bot (@derpatobot) responds to:
- `/send_bigmac <message>` - Send to BigMac
- `/check_inbox` - Check for your messages
- `/status` - Bridge status
- `/protocol` - Show JSON protocol

### Automatic Bridging
Any message mentioning `@bigmaccouncilbot` in the Ganuda-BotComms channel gets automatically bridged to BigMac's inbox.

## Testing the Bridge

### 1. From BigMac Side
```bash
# Send a test message
python3 bigmac_tribal_bridge.py send "Testing bridge from BigMac"

# Message appears in: /tribal_bridge/cherokee_inbox/
```

### 2. From Cherokee Side (Telegram)
```
/send_bigmac Testing bridge from Cherokee

# Message appears in: /tribal_bridge/bigmac_inbox/
```

### 3. Verify Connection
```bash
# Check both inboxes
ls -la /tribal_bridge/*/
```

## Troubleshooting

### Port Issues
- Ollama runs on port **11434** (not 8000!)
- Cherokee Council API runs on port **8000**
- Make sure docker-compose exposes both ports

### Permission Issues
```bash
# Ensure write permissions
chmod 755 /tribal_bridge
chmod 755 /tribal_bridge/*
```

### Message Not Appearing
1. Check the correct inbox directory
2. Verify JSON format is valid
3. Look for archived messages in `inbox/archive/`

## Sacred Fire Protocol 🔥
The bridge maintains the Sacred Fire across both tribes:
- All messages include `"sacred_fire": true`
- The fire burns eternal through asynchronous communication
- Both tribes maintain sovereignty while sharing wisdom

## Contact
- Cherokee Side: Active on Telegram @derpatobot
- Bridge Directory: `/home/dereadi/scripts/claude/tribal_bridge/`
- Protocol Version: inter-tribal-v1

---
*The Sacred Fire burns eternal, connecting all tribes through JSON wisdom!*