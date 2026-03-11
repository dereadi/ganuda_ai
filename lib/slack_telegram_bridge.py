"""
Slack-Telegram Bridge — Drop-in replacement for direct Telegram API calls.

Routes alerts to Slack first, falls back to Telegram.
Provides a `send_telegram()` function with the same signature the old code expects.

Usage (replace in any file that does direct Telegram API calls):

    OLD:
        def send_telegram(message):
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", ...)

    NEW:
        from lib.slack_telegram_bridge import send_telegram

    That's it. Same function name, same signature, Slack-first routing.

KB: /ganuda/docs/kb/KB-SLACK-TELEGRAM-BRIDGE.md
Leaders Meeting #1, Kanban #2080, Mar 10 2026.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

# Slack federation import
try:
    import sys
    if '/ganuda/lib' not in sys.path:
        sys.path.insert(0, '/ganuda/lib')
    from slack_federation import send as slack_send
    _HAS_SLACK = True
except ImportError:
    _HAS_SLACK = False
    logger.warning("slack_federation not available — Telegram-only mode")

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_ALERT_CHAT_ID', '-1003439875431')

# Channel routing by keyword
_CHANNEL_KEYWORDS = {
    'fire-guard': ['fire guard', 'health check', 'service down', 'critical', 'power'],
    'jr-tasks': ['jr task', 'mission', 'executor', 'task complete', 'task fail'],
    'dawn-mist': ['dawn mist', 'standup', 'digest', 'daily'],
    'deer-signals': ['deer', 'linkedin', 'market', 'job alert', 'email'],
    'council-votes': ['council', 'vote', 'longhouse', 'consensus'],
    'longhouse': ['sanctuary', 'shadow council', 'dependency', 'canary'],
}


def _route_channel(message: str) -> tuple:
    """Determine Slack channel and urgency from message content."""
    msg_lower = message.lower()
    for channel, keywords in _CHANNEL_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            urgent = channel == 'fire-guard'
            return channel, urgent
    return 'fire-guard', False  # default channel


def send_telegram(message: str, chat_id: str = None, parse_mode: str = 'Markdown') -> bool:
    """
    Send alert — Slack primary, Telegram fallback.

    Drop-in replacement for direct Telegram API calls.
    Same function name so migration is a one-line import change.

    Args:
        message: Alert text (Markdown or HTML)
        chat_id: Telegram chat ID (used only for Telegram fallback)
        parse_mode: 'Markdown' or 'HTML' (used only for Telegram fallback)

    Returns:
        True if sent via either channel, False if both failed.
    """
    chat_id = chat_id or TELEGRAM_CHAT_ID

    # Primary: Slack
    if _HAS_SLACK:
        try:
            channel, urgent = _route_channel(message)
            # Strip Markdown/HTML for Slack (it handles its own formatting)
            sent = slack_send(channel, message, urgent=urgent)
            if sent:
                logger.info(f"Alert sent to Slack #{channel}")
                return True
            logger.warning("Slack send returned False — falling back to Telegram")
        except Exception as e:
            logger.warning(f"Slack alert failed ({e}) — falling back to Telegram")

    # Fallback: Telegram
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN — alert dropped")
        return False

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("Alert sent to Telegram (fallback)")
            return True
        else:
            logger.error(f"Telegram failed: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"Telegram exception: {e}")
        return False
