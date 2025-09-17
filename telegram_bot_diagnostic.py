#!/usr/bin/env python3
"""
TELEGRAM BOT DIAGNOSTIC - Find and fix issues
"""

import requests
import json
import subprocess
import time

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def check_bot_info():
    """Check if bot is alive and get info"""
    print("🔍 Checking bot status...")
    
    url = f"{BASE_URL}/getMe"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot = data['result']
                print(f"✅ Bot is ALIVE!")
                print(f"   Username: @{bot['username']}")
                print(f"   Name: {bot['first_name']}")
                print(f"   Can join groups: {bot.get('can_join_groups', True)}")
                print(f"   Can read all messages: {bot.get('can_read_all_group_messages', False)}")
                return True
            else:
                print(f"❌ Bot error: {data}")
                return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def check_webhook():
    """Check if webhook is set (should be empty for polling)"""
    print("\n🔍 Checking webhook status...")
    
    url = f"{BASE_URL}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            webhook = data['result']
            if webhook.get('url'):
                print(f"⚠️ Webhook is SET to: {webhook['url']}")
                print("   This prevents polling! Removing...")
                remove_webhook()
            else:
                print("✅ No webhook set (good for polling)")
                return True
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return False

def remove_webhook():
    """Remove any existing webhook"""
    url = f"{BASE_URL}/deleteWebhook"
    try:
        response = requests.post(url, json={'drop_pending_updates': True})
        if response.status_code == 200:
            print("✅ Webhook removed!")
            return True
    except:
        print("❌ Failed to remove webhook")
        return False

def check_updates():
    """Check for pending updates"""
    print("\n🔍 Checking for messages...")
    
    url = f"{BASE_URL}/getUpdates"
    params = {'timeout': 5, 'limit': 10}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                updates = data['result']
                if updates:
                    print(f"📨 Found {len(updates)} pending messages!")
                    for update in updates[-3:]:  # Show last 3
                        if 'message' in update:
                            msg = update['message']
                            text = msg.get('text', 'No text')
                            user = msg.get('from', {}).get('first_name', 'Unknown')
                            chat = msg['chat']
                            chat_type = chat['type']
                            chat_title = chat.get('title', 'Private')
                            
                            print(f"\n   Message from {user} in {chat_type} chat '{chat_title}':")
                            print(f"   Text: {text[:100]}")
                else:
                    print("📭 No pending messages")
                return True
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return False

def test_send_message(chat_id=None):
    """Test sending a message"""
    print("\n🔍 Testing message sending...")
    
    if not chat_id:
        print("⚠️ No chat_id provided. Get one from /getUpdates first")
        return False
    
    url = f"{BASE_URL}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🔥 Cherokee Council Test Message!\n\nIf you see this, the bot is working!',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Test message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send: {result}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")
    
    return False

def check_running_processes():
    """Check for conflicting bot processes"""
    print("\n🔍 Checking for running bot processes...")
    
    try:
        result = subprocess.run(
            "ps aux | grep -E 'telegram|bot|ganuda' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            print(f"⚠️ Found {len(lines)} bot-related processes:")
            for line in lines:
                parts = line.split()
                if len(parts) > 10:
                    pid = parts[1]
                    cmd = ' '.join(parts[10:])[:80]
                    print(f"   PID {pid}: {cmd}")
        else:
            print("✅ No conflicting bot processes found")
    except:
        print("❌ Error checking processes")

def provide_fixes():
    """Provide specific fixes based on diagnostics"""
    print("\n" + "="*60)
    print("🔧 RECOMMENDED FIXES:")
    print("="*60)
    
    print("""
1. FIX PRIVACY MODE (Most Important):
   - Open Telegram
   - Message @BotFather
   - Send: /mybots
   - Select: ganudabot
   - Select: Bot Settings
   - Select: Group Privacy
   - Select: Turn off
   
2. RE-ADD BOT TO GROUP:
   - Remove @ganudabot from the group
   - Add @ganudabot back to the group
   - Make sure it says "Bot added to group"
   
3. TEST THE BOT:
   - In the group, type: @ganudabot hello
   - Or just type: /start
   - The bot should respond

4. KILL CONFLICTING PROCESSES:
   If you see multiple bot processes above, kill them:
   pkill -f telegram
   pkill -f ganuda
   
5. START FRESH BOT:
   python3 /home/dereadi/scripts/claude/telegram_llm_bridge.py
""")

def main():
    print("="*60)
    print("🔥 TELEGRAM BOT DIAGNOSTIC TOOL")
    print("="*60)
    
    # Run all checks
    bot_ok = check_bot_info()
    webhook_ok = check_webhook() if bot_ok else False
    updates_ok = check_updates() if bot_ok else False
    check_running_processes()
    
    # Provide recommendations
    provide_fixes()
    
    print("\n" + "="*60)
    if bot_ok and webhook_ok:
        print("✅ Bot is properly configured!")
        print("If it's still not responding in groups, fix privacy mode in BotFather")
    else:
        print("❌ Bot needs configuration fixes above")
    print("="*60)

if __name__ == "__main__":
    main()