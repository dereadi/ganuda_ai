"""
Slack Notification Service for the Chief PA.

Supports Slack Incoming Webhooks (simplest integration) with
structured Block Kit messages. Handles rate limiting, silent hours,
retry with exponential backoff, and message categorization.

Rate limit: max 10 messages/hour (configurable, prevents notification fatigue).
Silent hours: 10 PM - 6 AM CT (configurable).
Retry: 3 attempts with exponential backoff on webhook failures.

Config-driven: webhook URL, channel, bot name all from YAML.
Webhook URL stored in config file (chmod 600), never in source code.
"""

import json
import logging
import os
import time
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger("chief_pa.slack")


class SlackNotifier:
    """Slack webhook-based notification service.

    Usage:
        notifier = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/...",
            channel="#chief-pa",
        )
        notifier.send_message("Hello, Chief!")
        notifier.send_briefing(sections={...})
    """

    # Default timezone for silent hours
    DEFAULT_TIMEZONE = "America/Chicago"

    def __init__(
        self,
        webhook_url: str = "",
        channel: str = "#chief-pa",
        bot_name: str = "Cherokee PA",
        bot_icon: str = ":eagle:",
        max_messages_per_hour: int = 10,
        silent_start_hour: int = 22,
        silent_end_hour: int = 6,
        timezone: str = "America/Chicago",
        max_retries: int = 3,
    ):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
        self.channel = channel
        self.bot_name = bot_name
        self.bot_icon = bot_icon
        self.max_messages_per_hour = max_messages_per_hour
        self.silent_start_hour = silent_start_hour
        self.silent_end_hour = silent_end_hour
        self.timezone = ZoneInfo(timezone)
        self.max_retries = max_retries

        # Rate limiting: track timestamps of sent messages
        self._sent_timestamps: deque = deque(maxlen=max_messages_per_hour * 2)
        # Queue for messages deferred during silent hours
        self._deferred_queue: List[Dict[str, Any]] = []

        self._session = requests.Session()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SlackNotifier":
        """Create a SlackNotifier from a config dict (loaded from YAML).

        Expected config keys under 'slack':
            webhook_url: str
            channel: str
            bot_name: str
            bot_icon: str
            max_messages_per_hour: int
            silent_start_hour: int
            silent_end_hour: int
            timezone: str
            max_retries: int
        """
        slack_cfg = config.get("slack", {})
        return cls(
            webhook_url=slack_cfg.get("webhook_url", ""),
            channel=slack_cfg.get("channel", "#chief-pa"),
            bot_name=slack_cfg.get("bot_name", "Cherokee PA"),
            bot_icon=slack_cfg.get("bot_icon", ":eagle:"),
            max_messages_per_hour=slack_cfg.get("max_messages_per_hour", 10),
            silent_start_hour=slack_cfg.get("silent_start_hour", 22),
            silent_end_hour=slack_cfg.get("silent_end_hour", 6),
            timezone=slack_cfg.get("timezone", "America/Chicago"),
            max_retries=slack_cfg.get("max_retries", 3),
        )

    def send_message(
        self,
        text: str,
        category: str = "general",
        urgent: bool = False,
    ) -> bool:
        """Send a simple text message to Slack.

        Args:
            text: The message text.
            category: Message category (general, calendar-urgent, briefing,
                     email-triage, cluster-alert).
            urgent: If True, bypasses silent hours and rate limiting.

        Returns:
            True if message was sent (or deferred), False on failure.
        """
        if not self.webhook_url:
            logger.error("No Slack webhook URL configured")
            return False

        # Check silent hours (unless urgent)
        if not urgent and self._is_silent_hours():
            logger.info(
                "Silent hours active, deferring message: %s",
                text[:80],
            )
            self._deferred_queue.append({
                "text": text,
                "category": category,
                "deferred_at": datetime.now(self.timezone).isoformat(),
            })
            return True  # Deferred successfully

        # Check rate limit (unless urgent)
        if not urgent and self._is_rate_limited():
            logger.warning(
                "Rate limited (%d/hour), dropping message: %s",
                self.max_messages_per_hour, text[:80],
            )
            return False

        payload = {
            "channel": self.channel,
            "username": self.bot_name,
            "icon_emoji": self.bot_icon,
            "text": "[" + category.upper() + "] " + text,
        }

        return self._post_webhook(payload)

    def send_blocks(
        self,
        blocks: List[Dict[str, Any]],
        text_fallback: str = "",
        category: str = "general",
        urgent: bool = False,
    ) -> bool:
        """Send a Block Kit formatted message to Slack.

        Args:
            blocks: List of Slack Block Kit block objects.
            text_fallback: Fallback text for notifications/accessibility.
            category: Message category.
            urgent: If True, bypasses silent hours and rate limiting.

        Returns:
            True if sent, False on failure.
        """
        if not self.webhook_url:
            logger.error("No Slack webhook URL configured")
            return False

        if not urgent and self._is_silent_hours():
            self._deferred_queue.append({
                "blocks": blocks,
                "text_fallback": text_fallback,
                "category": category,
                "deferred_at": datetime.now(self.timezone).isoformat(),
            })
            return True

        if not urgent and self._is_rate_limited():
            logger.warning("Rate limited, dropping block message")
            return False

        payload = {
            "channel": self.channel,
            "username": self.bot_name,
            "icon_emoji": self.bot_icon,
            "text": text_fallback or "[" + category.upper() + "]",
            "blocks": blocks,
        }

        return self._post_webhook(payload)

    def send_briefing(
        self,
        calendar_section: str = "",
        cluster_section: str = "",
        email_section: str = "",
        kanban_section: str = "",
        summary: str = "",
    ) -> bool:
        """Send a structured daily briefing message.

        Formats the briefing as a Block Kit message with distinct sections
        for each data source.

        Args:
            calendar_section: Today's calendar events (formatted text).
            cluster_section: Overnight cluster activity summary.
            email_section: Actionable email summary.
            kanban_section: Pending kanban items.
            summary: LLM-generated natural language summary.

        Returns:
            True if sent, False on failure.
        """
        now = datetime.now(self.timezone)
        date_str = now.strftime("%A, %B %d, %Y")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Good morning, Chief -- " + date_str,
                },
            },
        ]

        if summary:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*What's on your plate today:*\n" + summary,
                },
            })

        if calendar_section:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Calendar*\n" + calendar_section,
                },
            })

        if email_section:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Actionable Emails*\n" + email_section,
                },
            })

        if cluster_section:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Federation Activity (overnight)*\n" + cluster_section,
                },
            })

        if kanban_section:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Kanban*\n" + kanban_section,
                },
            })

        # Footer with timestamp
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Cherokee AI Federation | Briefing generated "
                            + now.strftime("%H:%M CT"),
                },
            ],
        })

        return self.send_blocks(
            blocks=blocks,
            text_fallback="Daily Briefing -- " + date_str,
            category="briefing",
            urgent=False,  # Briefings respect silent hours
        )

    def send_calendar_alert(
        self,
        event_title: str,
        event_time: str,
        event_location: str = "",
        minutes_until: int = 0,
    ) -> bool:
        """Send an urgent calendar alert (event starting soon).

        Args:
            event_title: The calendar event title.
            event_time: Formatted time string.
            event_location: Optional location.
            minutes_until: Minutes until the event starts.

        Returns:
            True if sent, False on failure.
        """
        # Events within 30 minutes are urgent (bypass silent hours)
        is_urgent = minutes_until <= 30

        text_parts = [
            "Upcoming: *" + event_title + "*",
            "Time: " + event_time,
        ]
        if event_location:
            text_parts.append("Location: " + event_location)
        if minutes_until > 0:
            text_parts.append("Starts in " + str(minutes_until) + " minutes")

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(text_parts),
                },
            },
        ]

        return self.send_blocks(
            blocks=blocks,
            text_fallback="Calendar: " + event_title + " at " + event_time,
            category="calendar-urgent" if is_urgent else "calendar",
            urgent=is_urgent,
        )

    def flush_deferred(self) -> int:
        """Send all deferred messages (called when silent hours end).

        Returns:
            Number of messages successfully sent.
        """
        if not self._deferred_queue:
            return 0

        if self._is_silent_hours():
            return 0

        sent_count = 0
        remaining = []

        for msg in self._deferred_queue:
            if "blocks" in msg:
                ok = self.send_blocks(
                    blocks=msg["blocks"],
                    text_fallback=msg.get("text_fallback", ""),
                    category=msg.get("category", "general"),
                    urgent=True,  # Already waited, send now
                )
            else:
                ok = self.send_message(
                    text=msg.get("text", ""),
                    category=msg.get("category", "general"),
                    urgent=True,
                )
            if ok:
                sent_count += 1
            else:
                remaining.append(msg)

        self._deferred_queue = remaining
        if sent_count > 0:
            logger.info("Flushed %d deferred messages", sent_count)
        return sent_count

    def _post_webhook(self, payload: Dict[str, Any]) -> bool:
        """Post payload to Slack webhook with retry logic.

        Retries with exponential backoff: 1s, 2s, 4s.
        """
        for attempt in range(self.max_retries):
            try:
                response = self._session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )

                if response.status_code == 200:
                    self._sent_timestamps.append(time.time())
                    return True

                if response.status_code == 429:
                    # Slack rate limit
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(
                        "Slack rate limited, retry after %ds", retry_after,
                    )
                    time.sleep(min(retry_after, 30))
                    continue

                logger.warning(
                    "Slack webhook returned %d: %s (attempt %d/%d)",
                    response.status_code,
                    response.text[:200],
                    attempt + 1,
                    self.max_retries,
                )

            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Slack webhook request failed (attempt %d/%d): %s",
                    attempt + 1, self.max_retries, e,
                )

            # Exponential backoff
            if attempt < self.max_retries - 1:
                backoff = 2 ** attempt
                time.sleep(backoff)

        logger.error("All %d Slack webhook attempts failed", self.max_retries)
        return False

    def _is_silent_hours(self) -> bool:
        """Check if current time is within silent hours."""
        now = datetime.now(self.timezone)
        hour = now.hour

        if self.silent_start_hour > self.silent_end_hour:
            # Wraps midnight: e.g., 22:00 - 06:00
            return hour >= self.silent_start_hour or hour < self.silent_end_hour
        else:
            # Same-day range
            return self.silent_start_hour <= hour < self.silent_end_hour

    def _is_rate_limited(self) -> bool:
        """Check if we have exceeded the per-hour message limit."""
        now = time.time()
        hour_ago = now - 3600
        # Count messages in the last hour
        recent = sum(1 for t in self._sent_timestamps if t > hour_ago)
        return recent >= self.max_messages_per_hour