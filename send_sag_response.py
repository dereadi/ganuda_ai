#!/usr/bin/env python3
"""
Send response to Dr Joe about SAG Resource AI training
"""

import asyncio
from telegram import Bot
from datetime import datetime, timedelta

# Bot token
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Cherokee Training Operations Group ID (from invite link)
# We'll need to get the actual chat ID from the bot's updates
# For now, we'll send to the channel if it exists

async def send_sag_response():
    bot = Bot(token=TOKEN)
    
    # Response message for Dr Joe
    message = """🔥 **SAG Resource AI Training Response** 🔥

Dr Joe - Received your request!

**Training Details:**
📚 Module: SAG Resource AI Implementation
⏰ Timeline: ASAP (Can start immediately)
👤 Participant: Dr Joe (Internal Testing)
💰 Price: Internal rate - Free for testing/validation

**Available Times Today:**
• 2:00 PM - 4:00 PM CDT
• 4:30 PM - 6:30 PM CDT
• 7:00 PM - 9:00 PM CDT

**Training Covers:**
1. SAG PRD Overview & Architecture
2. Resource Allocation AI Components
3. Integration with Productive.io API
4. Real-time dashboards & monitoring
5. Cherokee Constitutional AI governance model
6. Hands-on implementation walkthrough

**Next Steps:**
Please confirm your preferred time slot and I'll set up:
- Zoom/Meet link
- Shared workspace access
- Productive.io test environment
- Training materials & documentation

The Sacred Fire burns eternal for knowledge transfer! 🔥
Ready when you are, Dr Joe!

- Cherokee Constitutional AI Training Division"""

    # First, get updates to find the chat ID
    updates = await bot.get_updates()
    
    if updates:
        # Get the most recent chat ID
        chat_id = updates[-1].message.chat.id if updates[-1].message else None
        
        if chat_id:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            print(f"✅ Response sent to chat {chat_id}")
        else:
            print("❌ No chat ID found in recent updates")
    else:
        print("❌ No updates found. Dr Joe may need to message the bot first.")
    
    # Also try to send to known group chat if we have it
    # The invite link suggests a group exists
    print("\nTrying to identify group chat...")
    for update in updates:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            group_id = update.message.chat.id
            try:
                await bot.send_message(chat_id=group_id, text=message, parse_mode='Markdown')
                print(f"✅ Also sent to group {group_id}")
            except Exception as e:
                print(f"Could not send to group: {e}")

if __name__ == "__main__":
    asyncio.run(send_sag_response())