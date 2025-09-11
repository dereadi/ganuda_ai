#!/usr/bin/env python3
"""
Send Dr Joe's setup instructions to Ganuda-BotComms channel
"""
import requests
import json

BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Try common Telegram group/channel ID formats
# Groups usually start with -100
CHANNEL_ID = "-1002218391016"  # Common format for Telegram channels

def send_instructions():
    """Send Dr Joe's instructions to the channel"""
    
    message = """🔥 **DR JOE - BIGMAC COUNCIL SETUP INSTRUCTIONS**

Since your Ollama is running perfectly, here's how to connect to our Cherokee tribe:

**STEP 1: Create Your Telegram Bot**
1. Go to @BotFather in Telegram
2. Send `/newbot`
3. Name it: `BigMac Council Bot`
4. Username: `@BigMacCouncilBot` (or similar)
5. Save the token you receive

**STEP 2: Create Bridge Script**
Create `bigmac_bridge.py`:
```python
#!/usr/bin/env python3
import requests
import json
from telegram import Bot
import asyncio

BOT_TOKEN = "YOUR_TOKEN_HERE"
CHANNEL_ID = "-1002218391016"  # Ganuda-BotComms

async def send_to_cherokee(message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"🏔️ BigMac Council: {message}"
    )

async def query_ollama(prompt):
    response = requests.post(
        "http://localhost:8000/api/generate",
        json={"model": "llama3.1", "prompt": prompt}
    )
    return response.json()['response']
```

**STEP 3: Test Connection**
```bash
pip install python-telegram-bot requests
python3 bigmac_bridge.py
```

**STEP 4: Add Bot to Channel**
1. Add @BigMacCouncilBot to Ganuda-BotComms
2. Make it admin so it can read/write

**STEP 5: JSON Communication**
Your tribe can communicate via JSON:
```json
{
  "from": "BigMac",
  "to": "Cherokee",
  "message": "Council ready",
  "sag_request": "training"
}
```

**That's it!** Once your bot is in the channel, both tribes can collaborate!

The Cherokee Council is ready to share:
• SAG Resource AI code
• Trading algorithms
• Thermal memory design
• All our discoveries

Mitakuye Oyasin! 🦅"""
    
    # Try to send
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Instructions sent to Ganuda-BotComms!")
            return True
        else:
            print(f"Error: {response.text}")
            # Try without channel ID prefix
            CHANNEL_ID_ALT = "2218391016"
            payload['chat_id'] = CHANNEL_ID_ALT
            response2 = requests.post(url, json=payload)
            if response2.status_code == 200:
                print("✅ Instructions sent using alternative ID!")
                return True
            else:
                print(f"Alternative also failed: {response2.text}")
    except Exception as e:
        print(f"Failed to send: {e}")
    
    return False

if __name__ == "__main__":
    print("🔥 Sending Dr Joe's instructions to Ganuda-BotComms...")
    send_instructions()