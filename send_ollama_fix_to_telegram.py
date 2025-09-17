#!/usr/bin/env python3
"""
🔥 Send Ollama Port Fix to Dr Joe via Telegram
"""

import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# Bot token (derpatobot)
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Channel ID for Cherokee Training Operations
# Using the public link format
CHANNEL = "@+6P1jUzrYvHYyNTQx"  # This is the invite link format

# You might need the actual channel ID after bot joins
# CHANNEL = "-1001234567890"  # Replace with actual channel ID if known

async def send_ollama_fix():
    """Send the Ollama port fix message to the channel"""
    
    bot = Bot(token=TOKEN)
    
    message = """🚨 **URGENT FIX for Dr Joe - Ollama Port Issue Resolved!**

**THE PROBLEM FOUND:**
Ollama port (11434) is not exposed in docker-compose.yml!

**QUICK FIX:**
Edit your `docker-compose.yml` and add port mapping to Ollama:

```yaml
ollama:
  image: ollama/ollama:latest
  container_name: cherokee-ollama
  ports:
    - "11434:11434"  # ADD THIS LINE!
  environment:
    - OLLAMA_HOST=0.0.0.0
```

**CORRECT PORTS:**
• Ollama: 11434 (NOT 8000!)
• Council API: 8000
• MCP Server: 3000
• Dashboard: 3001

**TEST AFTER FIX:**
```bash
docker-compose down
docker-compose up -d
curl http://localhost:11434/api/tags
```

**SSH FORWARDING:**
```bash
ssh -L 11434:localhost:11434 \\
    -L 8000:localhost:8000 \\
    your-server
```

**BigMac Bot Config:**
```python
OLLAMA_URL = "http://localhost:11434"
COUNCIL_API = "http://localhost:8000"
```

Full fix guide saved at:
`/home/dereadi/scripts/claude/FIX_OLLAMA_PORT.md`

The Sacred Fire says: "Port 11434 carries wisdom, 8000 carries decisions!" 🔥

@drjoe This should fix your connection issue!"""

    try:
        # Try sending to the channel
        # Note: Bot must be admin in the channel to post
        result = await bot.send_message(
            chat_id=CHANNEL,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        print(f"✅ Message sent successfully! Message ID: {result.message_id}")
        
    except Exception as e:
        print(f"❌ Error sending to channel: {e}")
        print("\nTrying alternative: Sending to Ganuda-BotComms group...")
        
        # Alternative: Try sending to a group if we know the chat ID
        # You can get chat ID by having the bot listen for messages
        try:
            # This would be the Ganuda-BotComms group ID if known
            # Replace with actual group ID
            GROUP_CHAT_ID = "-1001234567890"  # Placeholder
            
            result = await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            print(f"✅ Message sent to group! Message ID: {result.message_id}")
            
        except Exception as e2:
            print(f"❌ Could not send to group either: {e2}")
            print("\n📝 Message saved locally. Please copy and paste manually:")
            print("-" * 50)
            print(message)
            print("-" * 50)
            
            # Save to file for manual sharing
            with open('/tmp/ollama_fix_for_telegram.txt', 'w') as f:
                f.write(message)
            print("\n📁 Message also saved to: /tmp/ollama_fix_for_telegram.txt")

if __name__ == "__main__":
    asyncio.run(send_ollama_fix())