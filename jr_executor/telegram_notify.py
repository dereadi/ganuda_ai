#!/usr/bin/env python3
"""
Telegram notification helper for Jr
Allows Jr to send status updates to the owner
"""
import os
import requests

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
OWNER_CHAT_ID = 8025375307

def send_notification(message: str) -> bool:
    """Send a notification to the owner via Telegram"""
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys as _sys
        if '/ganuda/lib' not in _sys.path:
            _sys.path.insert(0, '/ganuda/lib')
        from slack_telegram_bridge import send_telegram as _slack_send
        if _slack_send(message):
            return True
    except Exception:
        pass  # fall through to Telegram
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": OWNER_CHAT_ID,
            "text": message
        }
        response = requests.post(url, data=data, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False

def notify_mission_start(mission_title: str):
    """Notify when Jr starts a mission"""
    msg = f"🚀 Jr Starting Mission\n\n{mission_title}"
    return send_notification(msg)

def notify_mission_complete(mission_title: str, success: bool, duration_ms: int):
    """Notify when Jr completes a mission"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    msg = f"{status}\n\nMission: {mission_title}\nDuration: {duration_ms}ms"
    return send_notification(msg)

def notify_error(error_msg: str):
    """Notify on critical errors"""
    msg = f"⚠️ Jr Error\n\n{error_msg}"
    return send_notification(msg)

if __name__ == "__main__":
    # Test
    send_notification("🤖 Jr Telegram notifications enabled!")
    print("Test notification sent")
