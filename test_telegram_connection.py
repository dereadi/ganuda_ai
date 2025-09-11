#!/usr/bin/env python3
"""
Test Telegram bot connection and check for updates
"""
import requests
import json

BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_bot_info():
    """Get bot information"""
    response = requests.get(f"{BASE_URL}/getMe")
    return response.json()

def get_updates():
    """Get recent updates/messages"""
    response = requests.get(f"{BASE_URL}/getUpdates")
    return response.json()

def get_webhook_info():
    """Check webhook status"""
    response = requests.get(f"{BASE_URL}/getWebhookInfo")
    return response.json()

print("🔥 Testing Telegram Bot Connection")
print("=" * 50)

# Get bot info
bot_info = get_bot_info()
if bot_info['ok']:
    print(f"✅ Bot Connected: @{bot_info['result']['username']}")
    print(f"   Bot Name: {bot_info['result']['first_name']}")
    print(f"   Bot ID: {bot_info['result']['id']}")
else:
    print("❌ Failed to connect to bot")

print("\n📨 Recent Updates:")
updates = get_updates()
if updates['ok']:
    if updates['result']:
        for update in updates['result'][-5:]:  # Last 5 updates
            if 'message' in update:
                msg = update['message']
                chat_type = msg['chat']['type']
                chat_title = msg['chat'].get('title', 'Private Chat')
                text = msg.get('text', 'No text')
                from_user = msg['from'].get('username', 'Unknown')
                print(f"   [{chat_type}] {chat_title}: @{from_user}: {text}")
            elif 'channel_post' in update:
                post = update['channel_post']
                chat_title = post['chat'].get('title', 'Channel')
                text = post.get('text', 'No text')
                print(f"   [channel] {chat_title}: {text}")
    else:
        print("   No recent messages")
else:
    print("   Failed to get updates")

print("\n🔗 Webhook Status:")
webhook = get_webhook_info()
if webhook['ok']:
    if webhook['result']['url']:
        print(f"   Webhook URL: {webhook['result']['url']}")
    else:
        print("   No webhook set (using polling)")

print("\n💡 If you just said hello:")
print("   - Check if you messaged in the right group/channel")
print("   - Bot may need admin rights to see group messages")
print("   - Try messaging @derpatobot directly")