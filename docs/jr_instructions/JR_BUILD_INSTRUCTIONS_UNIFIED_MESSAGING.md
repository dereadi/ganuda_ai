# Jr Build Instructions: SAG Unified Messaging Hub
## Priority: MEDIUM - Post-Launch Enhancement

---

## Objective

Implement full send/receive capability for multiple messaging platforms through the SAG Unified Messages interface. Users should be able to:
1. Configure platform credentials in Settings
2. View all messages in a unified inbox
3. Send messages from SAG to any connected platform
4. Receive real-time message notifications

---

## Current State

- ✅ Messages UI with channel list (Telegram, Facebook, Instagram, WhatsApp, Slack, Discord, SMS)
- ✅ Settings page with platform configuration modals
- ✅ Basic API endpoints (`/api/messages/<channel>`, `/api/messages/<channel>/send`)
- ✅ Redis-backed message storage (`messaging.py`)
- ✅ Telegram bot running (but not integrated with SAG messages)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SAG Web Interface                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Messages UI │  │ Settings UI │  │ Notifications   │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
└─────────┼────────────────┼──────────────────┼───────────┘
          │                │                  │
          ▼                ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                    Flask API Layer                       │
│  /api/messages/*  /api/messages/*/config  WebSocket     │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                   messaging.py Module                    │
│  - Message storage (Redis)                              │
│  - Platform adapters                                    │
│  - Send/receive handlers                                │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────┬─────────┬─────────┬─────────┬─────────┬───────┐
│Telegram │Facebook │Instagram│WhatsApp │ Slack   │Discord│
│  Bot    │Graph API│Graph API│Cloud API│  Bot    │  Bot  │
└─────────┴─────────┴─────────┴─────────┴─────────┴───────┘
```

---

## Platform Integration Tasks

### 1. Telegram Integration (Easiest - Already Running)

**Status**: Bot exists, needs SAG integration

**Files to modify**:
- `/ganuda/telegram_bot/telegram_chief.py`
- `/home/dereadi/sag_unified_interface/messaging.py`

**Task 1.1: Store incoming messages**

Add to `telegram_chief.py` after receiving any message:

```python
import redis
import json

def store_message_for_sag(update):
    """Store message in Redis for SAG UI"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        message = {
            "id": update.message.message_id,
            "sender": update.message.from_user.first_name,
            "sender_id": update.message.from_user.id,
            "chat_id": update.message.chat_id,
            "text": update.message.text,
            "timestamp": update.message.date.isoformat(),
            "direction": "incoming"
        }
        r.lpush("sag:messages:telegram", json.dumps(message))
        r.ltrim("sag:messages:telegram", 0, 999)
        # Increment unread count
        r.incr("sag:unread:telegram")
    except Exception as e:
        logger.error(f"Failed to store message for SAG: {e}")
```

Call this in `handle_message()`:
```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_message_for_sag(update)  # Add this line
    # ... existing code
```

**Task 1.2: Send from SAG**

The `send_telegram_message()` function in `messaging.py` already works. Verify bot token is loaded.

**Task 1.3: Real-time updates**

Add WebSocket support to push new messages to UI:

```python
# In app.py, add Flask-SocketIO
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

# Redis subscriber for new messages
def message_listener():
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe('sag:new_message')
    for message in pubsub.listen():
        if message['type'] == 'message':
            socketio.emit('new_message', json.loads(message['data']))
```

---

### 2. Facebook Messenger Integration

**Prerequisites**:
- Facebook Developer Account
- Facebook Page
- Meta App with Messenger permissions

**API Documentation**: https://developers.facebook.com/docs/messenger-platform

**Required Credentials**:
- `page_access_token` - Long-lived Page Access Token
- `app_secret` - For webhook verification
- `verify_token` - Custom string for webhook setup

**Task 2.1: Create Facebook adapter**

```python
# messaging.py - add Facebook adapter

import requests

def send_facebook_message(recipient_id: str, text: str) -> dict:
    """Send message via Facebook Messenger"""
    config = get_platform_config('facebook')
    if not config or not config.get('page_access_token'):
        return {"error": "Facebook not configured"}
    
    url = "https://graph.facebook.com/v18.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": config['page_access_token']
    }
    
    response = requests.post(url, json=payload)
    return response.json()
```

**Task 2.2: Webhook for incoming messages**

```python
# app.py - add Facebook webhook

@app.route('/webhook/facebook', methods=['GET', 'POST'])
def facebook_webhook():
    if request.method == 'GET':
        # Verification
        verify_token = request.args.get('hub.verify_token')
        config = get_platform_config('facebook')
        if verify_token == config.get('verify_token'):
            return request.args.get('hub.challenge')
        return 'Invalid token', 403
    
    # Incoming message
    data = request.json
    for entry in data.get('entry', []):
        for event in entry.get('messaging', []):
            if 'message' in event:
                store_message('facebook', {
                    "sender": event['sender']['id'],
                    "text": event['message'].get('text', ''),
                    "timestamp": datetime.now().isoformat(),
                    "direction": "incoming"
                })
    return 'OK'
```

---

### 3. Instagram Direct Integration

**Prerequisites**:
- Instagram Business/Creator Account
- Connected Facebook Page
- Meta App with Instagram permissions

**API Documentation**: https://developers.facebook.com/docs/instagram-api/guides/messaging

**Note**: Instagram messaging uses the same Graph API as Facebook.

**Task 3.1: Create Instagram adapter**

```python
def send_instagram_message(recipient_id: str, text: str) -> dict:
    """Send message via Instagram Direct"""
    config = get_platform_config('instagram')
    if not config:
        return {"error": "Instagram not configured"}
    
    url = f"https://graph.facebook.com/v18.0/{config['ig_user_id']}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": config['access_token']
    }
    
    response = requests.post(url, json=payload)
    return response.json()
```

---

### 4. WhatsApp Business Integration

**Prerequisites**:
- WhatsApp Business Account
- Meta Business verification
- Phone number registered with WhatsApp Cloud API

**API Documentation**: https://developers.facebook.com/docs/whatsapp/cloud-api

**Required Credentials**:
- `phone_number_id` - WhatsApp phone number ID
- `access_token` - Permanent access token

**Task 4.1: Create WhatsApp adapter**

```python
def send_whatsapp_message(phone_number: str, text: str) -> dict:
    """Send message via WhatsApp Cloud API"""
    config = get_platform_config('whatsapp')
    if not config:
        return {"error": "WhatsApp not configured"}
    
    url = f"https://graph.facebook.com/v18.0/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

---

### 5. Slack Integration

**Prerequisites**:
- Slack Workspace
- Slack App with Bot Token

**API Documentation**: https://api.slack.com/methods

**Required Credentials**:
- `bot_token` - xoxb-... token
- `signing_secret` - For webhook verification

**Task 5.1: Create Slack adapter**

```python
def send_slack_message(channel: str, text: str) -> dict:
    """Send message via Slack"""
    config = get_platform_config('slack')
    if not config:
        return {"error": "Slack not configured"}
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {config['bot_token']}"}
    payload = {
        "channel": channel,
        "text": text
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

**Task 5.2: Event subscription webhook**

```python
@app.route('/webhook/slack', methods=['POST'])
def slack_webhook():
    data = request.json
    
    # URL verification
    if data.get('type') == 'url_verification':
        return data['challenge']
    
    # Message event
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        if event.get('type') == 'message' and not event.get('bot_id'):
            store_message('slack', {
                "sender": event.get('user'),
                "text": event.get('text'),
                "channel": event.get('channel'),
                "timestamp": datetime.now().isoformat(),
                "direction": "incoming"
            })
    
    return 'OK'
```

---

### 6. Discord Integration

**Prerequisites**:
- Discord Server
- Discord Bot Application

**API Documentation**: https://discord.com/developers/docs

**Required Credentials**:
- `bot_token` - Bot token from Discord Developer Portal
- `guild_id` - Server ID (optional)

**Task 6.1: Create Discord adapter**

```python
def send_discord_message(channel_id: str, text: str) -> dict:
    """Send message via Discord"""
    config = get_platform_config('discord')
    if not config:
        return {"error": "Discord not configured"}
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {config['bot_token']}"}
    payload = {"content": text}
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

**Task 6.2: Discord Gateway for receiving**

Discord requires a WebSocket connection for real-time messages. Consider using `discord.py` library:

```python
import discord

class SAGDiscordBot(discord.Client):
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        store_message('discord', {
            "sender": str(message.author),
            "text": message.content,
            "channel": str(message.channel.id),
            "timestamp": message.created_at.isoformat(),
            "direction": "incoming"
        })
```

---

### 7. SMS Integration (Twilio)

**Prerequisites**:
- Twilio Account
- Twilio Phone Number

**API Documentation**: https://www.twilio.com/docs/sms

**Required Credentials**:
- `account_sid` - Twilio Account SID
- `auth_token` - Twilio Auth Token
- `phone_number` - Your Twilio phone number

**Task 7.1: Create SMS adapter**

```python
from twilio.rest import Client

def send_sms_message(to_number: str, text: str) -> dict:
    """Send SMS via Twilio"""
    config = get_platform_config('sms')
    if not config:
        return {"error": "SMS not configured"}
    
    try:
        client = Client(config['account_sid'], config['auth_token'])
        message = client.messages.create(
            body=text,
            from_=config['phone_number'],
            to=to_number
        )
        return {"sid": message.sid, "status": message.status}
    except Exception as e:
        return {"error": str(e)}
```

**Task 7.2: Twilio webhook for incoming**

```python
@app.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    store_message('sms', {
        "sender": request.form.get('From'),
        "text": request.form.get('Body'),
        "timestamp": datetime.now().isoformat(),
        "direction": "incoming"
    })
    return '<Response></Response>', 200, {'Content-Type': 'text/xml'}
```

---

## UI Enhancements

### Task: Real-time message updates

Add to `control-room.js`:

```javascript
// WebSocket connection for real-time messages
var messageSocket = null;

function connectMessageSocket() {
    messageSocket = io.connect(window.location.origin);
    
    messageSocket.on('new_message', function(data) {
        // Update badge count
        var badge = document.getElementById('badge-' + data.channel);
        if (badge) {
            var count = parseInt(badge.textContent) + 1;
            badge.textContent = count;
            badge.style.display = '';
        }
        
        // If viewing this channel, append message
        var currentChannel = document.querySelector('.channel-item.active');
        if (currentChannel && currentChannel.dataset.channel === data.channel) {
            appendMessage(data);
        }
        
        // Desktop notification
        if (Notification.permission === 'granted') {
            new Notification('New message on ' + data.channel, {
                body: data.text.substring(0, 100)
            });
        }
    });
}

function appendMessage(msg) {
    var list = document.querySelector('.message-list');
    if (!list) return;
    
    var div = document.createElement('div');
    div.className = 'message-item';
    div.innerHTML = '<div class="message-sender">' + msg.sender + '</div>' +
                   '<div class="message-text">' + msg.text + '</div>' +
                   '<div class="message-time">' + msg.timestamp + '</div>';
    list.appendChild(div);
    list.scrollTop = list.scrollHeight;
}
```

---

## Security Considerations

1. **Token Storage**: Store API tokens encrypted in Redis or database, not plain text
2. **Webhook Verification**: Always verify webhook signatures
3. **Rate Limiting**: Implement rate limits on send endpoints
4. **Input Sanitization**: Sanitize all message content before display
5. **Access Control**: Require authentication for messaging APIs

---

## Testing Checklist

- [ ] Telegram: Send message from SAG, receive in Telegram
- [ ] Telegram: Send message from Telegram, see in SAG
- [ ] Facebook: Webhook verification succeeds
- [ ] Facebook: Send/receive messages
- [ ] Instagram: Send/receive messages
- [ ] WhatsApp: Send/receive messages
- [ ] Slack: Send/receive messages
- [ ] Discord: Send/receive messages
- [ ] SMS: Send/receive messages
- [ ] Settings: Configure each platform credentials
- [ ] Real-time: Messages appear without refresh
- [ ] Notifications: Desktop notifications work

---

## File Locations

| File | Purpose |
|------|---------|
| `/home/dereadi/sag_unified_interface/messaging.py` | Platform adapters and storage |
| `/home/dereadi/sag_unified_interface/app.py` | API endpoints and webhooks |
| `/home/dereadi/sag_unified_interface/static/js/control-room.js` | UI logic |
| `/ganuda/telegram_bot/telegram_chief.py` | Telegram bot integration |

---

## External Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Meta Graph API**: https://developers.facebook.com/docs/graph-api
- **WhatsApp Cloud API**: https://developers.facebook.com/docs/whatsapp/cloud-api
- **Slack API**: https://api.slack.com/
- **Discord API**: https://discord.com/developers/docs
- **Twilio API**: https://www.twilio.com/docs

---

## Success Criteria

1. ✅ User can configure platform credentials in Settings
2. ✅ Messages appear in unified inbox from all connected platforms
3. ✅ User can send messages to any platform from SAG
4. ✅ Real-time message delivery (< 5 second latency)
5. ✅ Desktop notifications for new messages
6. ✅ Message history persists across sessions

---

*For Seven Generations*
