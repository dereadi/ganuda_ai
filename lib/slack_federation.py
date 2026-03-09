"""
Cherokee AI Federation — Shared Slack Notification Library

Module-level functions for sending Slack messages via the Bot API
(chat.postMessage). Uses a single bot token (SLACK_BOT_TOKEN) with
per-message channel targeting.

Rate limit: 30 messages/minute (Slack Tier 1).
Silent hours: 10 PM – 6 AM CT (bypass with urgent=True).
Retry: 3 attempts, exponential backoff.
Graceful degradation: missing token logs a warning, returns False.
"""

import logging
import os
import time
from collections import deque
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger("ganuda.slack_federation")

# ---------------------------------------------------------------------------
# Channel map — hardcoded channel IDs for the ganuda.slack.com workspace
# ---------------------------------------------------------------------------
CHANNELS = {
    "fire-guard": "C0AK59LQYF8",
    "council-votes": "C0AL1KCLHFA",
    "jr-tasks": "C0AK59P5VRC",
    "dawn-mist": "C0AL1KEBCBA",
    "deer-signals": "C0AL1KEHQM6",
    "saturday-morning": "C0AKAV1Q9RS",
    "longhouse": "C0AKL90CAGH",
}

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
_SLACK_API_URL = "https://slack.com/api/chat.postMessage"
_MAX_MESSAGES_PER_MINUTE = 30
_MAX_RETRIES = 3
_SILENT_START_HOUR = 22  # 10 PM CT
_SILENT_END_HOUR = 6     # 6 AM CT
_TZ = ZoneInfo("America/Chicago")

# ---------------------------------------------------------------------------
# Module-level state (lazy-loaded)
# ---------------------------------------------------------------------------
_token: Optional[str] = None
_session: Optional[requests.Session] = None
_sent_timestamps: deque = deque(maxlen=_MAX_MESSAGES_PER_MINUTE * 2)


def _get_token() -> Optional[str]:
    """Lazily load the bot token on first use."""
    global _token
    if _token is None:
        _token = os.environ.get("SLACK_BOT_TOKEN", "")
    return _token or None


def _get_session() -> requests.Session:
    """Lazily create a requests session."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _resolve_channel(channel_name: str) -> Optional[str]:
    """Resolve a friendly channel name to a Slack channel ID."""
    # Accept raw channel IDs (start with C)
    if channel_name.startswith("C") and len(channel_name) > 8:
        return channel_name
    # Strip leading # if present
    name = channel_name.lstrip("#")
    channel_id = CHANNELS.get(name)
    if not channel_id:
        logger.error("Unknown channel: %s (known: %s)", name, ", ".join(CHANNELS))
    return channel_id


def _is_silent_hours() -> bool:
    """Check if current time falls within silent hours (10 PM – 6 AM CT)."""
    hour = datetime.now(_TZ).hour
    return hour >= _SILENT_START_HOUR or hour < _SILENT_END_HOUR


def _is_rate_limited() -> bool:
    """Check if we have hit the per-minute message ceiling."""
    now = time.time()
    one_minute_ago = now - 60
    recent = sum(1 for t in _sent_timestamps if t > one_minute_ago)
    return recent >= _MAX_MESSAGES_PER_MINUTE


def _post(payload: dict) -> bool:
    """Post a payload to chat.postMessage with retry + exponential backoff."""
    token = _get_token()
    if not token:
        logger.warning("SLACK_BOT_TOKEN not set — message not sent")
        return False

    session = _get_session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    for attempt in range(_MAX_RETRIES):
        try:
            resp = session.post(
                _SLACK_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                logger.warning("Slack 429, retry after %ds", retry_after)
                time.sleep(min(retry_after, 30))
                continue

            data = resp.json()
            if data.get("ok"):
                _sent_timestamps.append(time.time())
                return True

            error = data.get("error", "unknown")
            logger.warning(
                "Slack API error: %s (attempt %d/%d)",
                error, attempt + 1, _MAX_RETRIES,
            )

        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Slack request failed (attempt %d/%d): %s",
                attempt + 1, _MAX_RETRIES, exc,
            )

        # Exponential backoff before next attempt
        if attempt < _MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    logger.error("All %d Slack attempts failed", _MAX_RETRIES)
    return False


# ===================================================================
# Public API
# ===================================================================

def send(channel_name: str, text: str, urgent: bool = False) -> bool:
    """Send a plain text message to a named channel.

    Args:
        channel_name: Friendly name (e.g. "fire-guard") or raw channel ID.
        text: Message text (supports mrkdwn).
        urgent: If True, bypasses silent hours and rate limiting.

    Returns:
        True on success, False on failure.
    """
    channel_id = _resolve_channel(channel_name)
    if not channel_id:
        return False

    if not urgent and _is_silent_hours():
        logger.info("Silent hours — suppressing message to %s", channel_name)
        return False

    if not urgent and _is_rate_limited():
        logger.warning("Rate limited — dropping message to %s", channel_name)
        return False

    return _post({"channel": channel_id, "text": text})


def send_blocks(
    channel_name: str,
    blocks: list,
    text_fallback: str = "",
    urgent: bool = False,
) -> bool:
    """Send a Block Kit message to a named channel.

    Args:
        channel_name: Friendly name or raw channel ID.
        blocks: List of Slack Block Kit block dicts.
        text_fallback: Fallback text for notifications / accessibility.
        urgent: If True, bypasses silent hours and rate limiting.

    Returns:
        True on success, False on failure.
    """
    channel_id = _resolve_channel(channel_name)
    if not channel_id:
        return False

    if not urgent and _is_silent_hours():
        logger.info("Silent hours — suppressing block message to %s", channel_name)
        return False

    if not urgent and _is_rate_limited():
        logger.warning("Rate limited — dropping block message to %s", channel_name)
        return False

    payload = {
        "channel": channel_id,
        "blocks": blocks,
        "text": text_fallback or "Federation notification",
    }
    return _post(payload)


# -------------------------------------------------------------------
# Convenience functions
# -------------------------------------------------------------------

def notify_fire_guard(text: str, urgent: bool = False) -> bool:
    """Send a message to #fire-guard."""
    return send("fire-guard", text, urgent=urgent)


def notify_council_vote(
    vote_hash: str,
    question: str,
    decision: str,
    confidence: float,
    concerns: Optional[List[str]] = None,
) -> bool:
    """Post a formatted council vote result to #council-votes."""
    conf_pct = f"{confidence * 100:.1f}%"
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Council Vote: {decision.upper()}",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Hash:*\n`{vote_hash}`"},
                {"type": "mrkdwn", "text": f"*Confidence:*\n{conf_pct}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Question:*\n{question}",
            },
        },
    ]

    if concerns:
        concern_text = "\n".join(f"- {c}" for c in concerns)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Concerns:*\n{concern_text}",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Cherokee AI Federation | {datetime.now(_TZ).strftime('%Y-%m-%d %H:%M CT')}",
            },
        ],
    })

    return send_blocks(
        "council-votes",
        blocks,
        text_fallback=f"Council Vote {vote_hash}: {decision} ({conf_pct})",
    )


def notify_jr_task(
    task_id: str,
    title: str,
    status: str,
    details: str = "",
) -> bool:
    """Post a Jr task lifecycle event to #jr-tasks."""
    status_emoji = {
        "queued": ":inbox_tray:",
        "assigned": ":pencil2:",
        "in_progress": ":hammer_and_wrench:",
        "completed": ":white_check_mark:",
        "failed": ":x:",
        "retrying": ":arrows_counterclockwise:",
    }.get(status.lower(), ":memo:")

    text = f"{status_emoji} *{status.upper()}* — `{task_id}`\n*{title}*"
    if details:
        text += f"\n{details}"

    return send("jr-tasks", text)


def notify_deer_signal(
    source: str,
    summary: str,
    connections: Optional[List[str]] = None,
) -> bool:
    """Post a market intelligence signal to #deer-signals."""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":deer: *Deer Signal*\n*Source:* {source}\n\n{summary}",
            },
        },
    ]

    if connections:
        conn_text = "\n".join(f"- {c}" for c in connections)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Connections to Federation:*\n{conn_text}",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Deer (Outer Council) | {datetime.now(_TZ).strftime('%Y-%m-%d %H:%M CT')}",
            },
        ],
    })

    return send_blocks(
        "deer-signals",
        blocks,
        text_fallback=f"Deer Signal from {source}: {summary[:100]}",
    )


# ===================================================================
# CLI test
# ===================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ok = notify_fire_guard(
        "slack_federation.py test message — library loaded successfully.",
        urgent=True,
    )
    if ok:
        logger.info("Test message sent to #fire-guard")
    else:
        logger.error("Test message failed (check SLACK_BOT_TOKEN)")
