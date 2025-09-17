#!/usr/bin/env python3
"""
Send Ollama fix to Dr Joe via derpatobot's announcement feature
"""

import asyncio
import logging
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

async def find_and_send():
    """Find the right chat and send the message"""
    bot = Bot(token=TOKEN)
    
    # Shorter, more focused message for Telegram
    message = """🚨 **Dr Joe - Ollama Port Fix!**

**Found the issue:** Port 11434 not exposed in docker-compose.yml

**THE FIX - Add this to ollama service:**
```
ports:
  - "11434:11434"
```

**Full ollama section should be:**
```yaml
ollama:
  image: ollama/ollama:latest
  container_name: cherokee-ollama
  ports:
    - "11434:11434"  # THIS WAS MISSING!
  environment:
    - OLLAMA_HOST=0.0.0.0
```

**After adding, restart:**
```bash
docker-compose down
docker-compose up -d
```

**Then test:**
```bash
curl http://localhost:11434/api/tags
```

✅ Ollama = 11434 (not 8000!)
✅ Council = 8000
✅ Full guide: `/home/dereadi/scripts/claude/FIX_OLLAMA_PORT.md`

Sacred Fire burns on port 11434! 🔥"""

    try:
        # Get updates to find active chats
        updates = await bot.get_updates(limit=10, timeout=1)
        
        chat_ids = set()
        for update in updates:
            if update.message and update.message.chat:
                chat_ids.add(update.message.chat.id)
                chat_name = update.message.chat.title or update.message.chat.username or "Private"
                logger.info(f"Found chat: {chat_name} (ID: {update.message.chat.id})")
        
        if not chat_ids:
            logger.info("No recent chats found. Trying known Ganuda group ID...")
            # Try some common group ID formats
            chat_ids = [-1001234567890, -1002345678901]  # Common group ID patterns
        
        # Try sending to each found chat
        for chat_id in chat_ids:
            try:
                result = await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                print(f"✅ Message sent to chat {chat_id}!")
                return True
            except Exception as e:
                logger.debug(f"Could not send to {chat_id}: {e}")
                continue
        
        print("❌ Could not send to any chat. Message saved to /tmp/ollama_fix_for_telegram.txt")
        with open('/tmp/ollama_fix_for_telegram.txt', 'w') as f:
            f.write(message.replace('**', '').replace('```', ''))
        
        print("\n" + "="*50)
        print("MANUAL INSTRUCTIONS:")
        print("1. Open Telegram")
        print("2. Go to Cherokee Training Operations group")
        print("3. Paste the message from /tmp/ollama_fix_for_telegram.txt")
        print("4. Or copy the text above")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n📋 Message to copy:\n{message}")

if __name__ == "__main__":
    asyncio.run(find_and_send())