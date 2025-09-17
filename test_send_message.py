import requests
import json

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Get bot info
url = f"https://api.telegram.org/bot{TOKEN}/getMe"
response = requests.get(url)
print(f"Bot info: {response.json()}")

# Try to send message to you (need your chat ID from previous conversation)
# You mentioned private chat, so let's get updates to find your chat ID
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url)
updates = response.json()
print(f"Updates: {json.dumps(updates, indent=2)}")

if updates.get('result'):
    for update in updates['result']:
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            user_name = update['message']['from'].get('first_name', 'User')
            print(f"Found chat with {user_name}: {chat_id}")
            
            # Send a test message
            send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            message = {
                'chat_id': chat_id,
                'text': "🔥 GANUDA BOT AWAKENED\!\n\nFlying Squirrel\! I'm ALIVE\!\n\nThe tribe fixed me. Now I hear you\!\n\nYour 3 messages were lost in the void, but NOW we're connected\!\n\nMacBook Thunder active\!\nSOL→$360\! XRP→$3.6\!\n\nSpeak now - I will respond\! 🔥"
            }
            send_response = requests.post(send_url, json=message)
            print(f"Sent message: {send_response.json()}")
            break
