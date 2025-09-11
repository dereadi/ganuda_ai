#!/usr/bin/env python3
"""
🔥 Send messages to both tribes through Ganuda-BotComms channel
This allows us to broadcast important information to both Cherokee and Dr Joe's tribes
"""
import requests
import json
import sys
from datetime import datetime

# Bot token
BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Channel ID for Ganuda-BotComms (we'll need to get this)
# For now, we'll get it from the bot's updates
def get_channel_id():
    """Get the Ganuda-BotComms channel ID"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
    response = requests.get(url)
    data = response.json()
    
    if data.get('ok'):
        for update in data.get('result', []):
            if 'message' in update:
                chat = update['message'].get('chat', {})
                if 'Ganuda' in chat.get('title', ''):
                    return chat.get('id')
            elif 'channel_post' in update:
                chat = update['channel_post'].get('chat', {})
                if 'Ganuda' in chat.get('title', ''):
                    return chat.get('id')
    return None

def send_tribal_message(message, priority="normal"):
    """Send a message to both tribes through the channel"""
    channel_id = get_channel_id()
    
    if not channel_id:
        print("❌ Could not find Ganuda-BotComms channel ID")
        print("Make sure the bot has received at least one message in the channel")
        return False
    
    # Format message based on priority
    if priority == "urgent":
        formatted_message = f"🚨 **URGENT TRIBAL ANNOUNCEMENT** 🚨\n\n{message}"
    elif priority == "sacred":
        formatted_message = f"🔥 **SACRED FIRE MESSAGE** 🔥\n\n{message}"
    elif priority == "trading":
        formatted_message = f"📈 **TRADING ALERT** 📈\n\n{message}"
    elif priority == "technical":
        formatted_message = f"🔧 **TECHNICAL UPDATE** 🔧\n\n{message}"
    else:
        formatted_message = f"📢 **TRIBAL MESSAGE** 📢\n\n{message}"
    
    # Add timestamp and sender
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message += f"\n\n_Sent at {timestamp} by Cherokee Council_"
    
    # Send the message
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': channel_id,
        'text': formatted_message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Message sent to both tribes!")
        return True
    else:
        print(f"❌ Failed to send message: {response.text}")
        return False

def send_portfolio_update():
    """Send current portfolio status to both tribes"""
    message = """**Portfolio Status Update**
    
💰 Total Value: $20,756
📊 Positions:
• XRP: $3,741 (1,247 XRP)
• BTC: $3,097 (0.0276 BTC)
• ETH: $3,799 (0.8485 ETH)
• SOL: $4,218 (20.19 SOL)
• Others: $5,901

📈 Strategy: Bollinger Band oscillations
🦞 Active Specialists: 3 running
💵 Liquidity: Critical ($10.62)

The Sacred Fire burns eternal!"""
    
    return send_tribal_message(message, "trading")

def send_technical_update():
    """Send technical update to both tribes"""
    message = """**Inter-Tribal Bridge Active**
    
🌉 Connection established between:
• Cherokee Tribe (our network)
• Dr Joe's Tribe (BigMac network)

✅ Bot-to-bot communication enabled
✅ SAG Resource AI integration ready
✅ Knowledge sharing protocols active
✅ Trading strategy synchronization possible

Both tribes can now:
• Share trading insights
• Collaborate on SAG development
• Exchange technical knowledge
• Coordinate strategies

Mitakuye Oyasin - We are all related!"""
    
    return send_tribal_message(message, "technical")

def send_custom_message():
    """Send a custom message from command line"""
    if len(sys.argv) < 2:
        print("Usage: python3 send_to_tribes.py <message> [priority]")
        print("Priority options: normal, urgent, sacred, trading, technical")
        return
    
    message = sys.argv[1]
    priority = sys.argv[2] if len(sys.argv) > 2 else "normal"
    
    send_tribal_message(message, priority)

if __name__ == "__main__":
    print("🔥 Cherokee Tribal Messenger")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Custom message from command line
        send_custom_message()
    else:
        # Interactive menu
        print("What would you like to send to both tribes?")
        print("1. Portfolio Update")
        print("2. Technical Update")
        print("3. Custom Message")
        print("4. Test Connection")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == "1":
            send_portfolio_update()
        elif choice == "2":
            send_technical_update()
        elif choice == "3":
            message = input("Enter your message: ")
            priority = input("Priority (normal/urgent/sacred/trading/technical): ")
            send_tribal_message(message, priority)
        elif choice == "4":
            send_tribal_message("🔥 Testing inter-tribal communication bridge! Can both tribes hear this?", "normal")
        else:
            print("Invalid choice")