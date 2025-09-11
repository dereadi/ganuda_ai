#!/usr/bin/env python3
"""
🔥 Test Derpatobot Connection
Quick test to see if derpatobot is configured
"""

import os
import json
import asyncio
from telegram import Bot
from telegram.error import InvalidToken, NetworkError

async def test_bot():
    """Test if derpatobot is configured and accessible"""
    
    # Check for token in environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        # Try to load from a .env file if it exists
        env_file = '/home/dereadi/scripts/claude/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if 'TELEGRAM_BOT_TOKEN' in line:
                        token = line.split('=')[1].strip().strip('"\'')
                        break
    
    if not token:
        print("❌ No bot token found!")
        print("\nTo set up derpatobot:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot")
        print("3. Name: Cherokee Training Operations")
        print("4. Username: derpatobot")
        print("5. Save the token and run:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        return False
    
    print("🔍 Testing derpatobot connection...")
    print(f"Token: {token[:10]}...{token[-5:]}")
    
    try:
        bot = Bot(token)
        bot_info = await bot.get_me()
        
        print(f"✅ Bot connected successfully!")
        print(f"📱 Bot username: @{bot_info.username}")
        print(f"🤖 Bot name: {bot_info.first_name}")
        print(f"🆔 Bot ID: {bot_info.id}")
        
        if bot_info.username == "derpatobot":
            print("\n🔥 Derpatobot is ready for Cherokee Training Operations!")
            print("Revenue Stream #3 can be activated!")
        else:
            print(f"\n⚠️  This bot is @{bot_info.username}, not @derpatobot")
            print("Update the token to use derpatobot")
        
        return True
        
    except InvalidToken:
        print("❌ Invalid bot token!")
        print("Please check your token and try again.")
        return False
    except NetworkError as e:
        print(f"❌ Network error: {e}")
        print("Check your internet connection.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 DERPATOBOT CONNECTION TEST")
    print("=" * 60)
    print()
    
    # Run the async test
    result = asyncio.run(test_bot())
    
    if result:
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Run: ./launch_telegram_training.sh")
        print("2. The bot will start serving training content")
        print("3. Revenue Stream #3 activated!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Bot not configured yet. Follow the steps above.")
        print("=" * 60)
    
    print("\nSacred Fire burns eternal! 🔥")