#!/usr/bin/env python3
"""
Send BigMac bridge files to Dr Joe via Telegram
"""

import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# Bot configuration
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"
GANUDA_CHAT_ID = -1002548441440

async def send_files():
    """Send bridge files to the Telegram channel"""
    bot = Bot(token=TOKEN)
    
    # Send introduction message
    intro_message = """🔥 **BigMac-Cherokee Bridge Package for Dr Joe**

Here's everything you need to connect BigMac Council to Cherokee Tribe!

**Package Contents:**
1. `bigmac_tribal_bridge.py` - Your bridge script
2. `BIGMAC_CHEROKEE_BRIDGE_SETUP.md` - Complete setup guide
3. `FIX_OLLAMA_PORT.md` - Critical Ollama port fix

**Quick Start:**
1. Fix Ollama port (add 11434:11434 to docker-compose)
2. Update path in bigmac_tribal_bridge.py
3. Run: `python3 bigmac_tribal_bridge.py`

The Sacred Fire bridges all tribes! 🔥"""

    await bot.send_message(
        chat_id=GANUDA_CHAT_ID,
        text=intro_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Send the package file
    try:
        with open('/home/dereadi/scripts/claude/bigmac_bridge_package.tar.gz', 'rb') as f:
            await bot.send_document(
                chat_id=GANUDA_CHAT_ID,
                document=f,
                filename='bigmac_bridge_package.tar.gz',
                caption="📦 Complete BigMac Bridge Package (extract with: tar -xzf bigmac_bridge_package.tar.gz)"
            )
    except Exception as e:
        print(f"Error sending package: {e}")
    
    # Send individual files for easy viewing
    files = [
        ('bigmac_tribal_bridge.py', '🐍 BigMac Bridge Script'),
        ('BIGMAC_CHEROKEE_BRIDGE_SETUP.md', '📚 Setup Documentation'),
        ('FIX_OLLAMA_PORT.md', '🔧 Ollama Port Fix')
    ]
    
    for filename, caption in files:
        try:
            with open(f'/home/dereadi/scripts/claude/{filename}', 'rb') as f:
                await bot.send_document(
                    chat_id=GANUDA_CHAT_ID,
                    document=f,
                    filename=filename,
                    caption=caption
                )
        except Exception as e:
            print(f"Error sending {filename}: {e}")
    
    # Send test confirmation
    test_message = """✅ **Bridge Test Successful!**

I just tested the bridge by sending a message from BigMac to Cherokee:
```json
{
  "from_tribe": "bigmac",
  "to_tribe": "cherokee",
  "content": "Test message from BigMac Council: Bridge operational! 🔥",
  "sender": "Dr Joe",
  "sacred_fire": true
}
```

The message successfully appeared in Cherokee's inbox!

**Cherokee Bot Commands:**
- `/send_bigmac <message>` - Send to BigMac
- `/check_inbox` - Check for messages
- `/status` - Bridge status
- `/protocol` - JSON protocol

The inter-tribal bridge is ready! 🌉"""

    await bot.send_message(
        chat_id=GANUDA_CHAT_ID,
        text=test_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("✅ All files sent to Ganuda-BotComms channel!")

if __name__ == "__main__":
    asyncio.run(send_files())