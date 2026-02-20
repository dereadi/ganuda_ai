#!/usr/bin/env python3
"""
Status Notifier for Jr Task Updates
Polls thermal memory for Jr status updates and forwards to Telegram
"""

import psycopg2
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
import os

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Telegram bot token - replace with actual
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# Chat IDs to notify (add your chat ID)
NOTIFY_CHAT_IDS = [
    # Add authorized chat IDs here
]


class StatusNotifier:
    """Polls for Jr status updates and sends Telegram notifications"""

    def __init__(self, bot_token: str = None, chat_ids: List[int] = None):
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_ids = chat_ids or NOTIFY_CHAT_IDS
        self.db_config = DB_CONFIG
        self.last_check = datetime.now() - timedelta(minutes=5)
        self.processed_ids = set()

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def get_pending_notifications(self) -> List[Dict]:
        """Get unprocessed Jr status updates from thermal memory"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT id::text, content, temperature, source_triad, created_at
                FROM triad_shared_memories
                WHERE 'telegram_notify' = ANY(tags)
                  AND 'jr_status' = ANY(tags)
                  AND created_at > %s
                ORDER BY created_at ASC
                LIMIT 20
            ''', (self.last_check,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            notifications = []
            for row in rows:
                if row[0] not in self.processed_ids:
                    notifications.append({
                        'id': row[0],
                        'content': row[1],
                        'temperature': float(row[2]) if row[2] else 50,
                        'source': row[3],
                        'created_at': row[4]
                    })

            return notifications
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []

    def parse_status_content(self, content: str) -> Dict:
        """Parse Jr status update content"""
        result = {
            'task_id': None,
            'status': None,
            'details': None,
            'raw': content
        }

        if content.startswith('JR_STATUS_UPDATE|'):
            parts = content.split('|')
            for part in parts[1:]:
                if ':' in part:
                    key, value = part.split(':', 1)
                    result[key] = value

        return result

    def format_notification(self, notification: Dict) -> str:
        """Format notification for Telegram"""
        parsed = self.parse_status_content(notification['content'])

        # Emoji based on status
        status = parsed.get('status', 'unknown')
        if status == 'completed':
            emoji = '✅'
        elif status == 'failed':
            emoji = '❌'
        elif status == 'started':
            emoji = '🔄'
        else:
            emoji = '📋'

        # High temperature = important
        priority = ''
        if notification['temperature'] >= 85:
            priority = '🔥 '

        message = f"{priority}{emoji} **Jr Status Update**\\n"
        message += f"Source: `{notification['source']}`\\n"

        if parsed.get('task_id'):
            message += f"Task: `{parsed['task_id']}`\\n"
        if parsed.get('status'):
            message += f"Status: {parsed['status']}\\n"
        if parsed.get('details'):
            message += f"Details: {parsed['details'][:200]}\\n"

        return message

    async def send_notification(self, message: str):
        """Send notification to all configured chat IDs"""
        if not self.chat_ids:
            logger.warning("No chat IDs configured for notifications")
            return

        bot = Bot(token=self.bot_token)
        for chat_id in self.chat_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except TelegramError as e:
                logger.error(f"Failed to send to {chat_id}: {e}")

    def mark_processed(self, notification_id: str):
        """Mark notification as processed"""
        self.processed_ids.add(notification_id)
        # Keep set from growing indefinitely
        if len(self.processed_ids) > 1000:
            self.processed_ids = set(list(self.processed_ids)[-500:])

    async def poll_and_notify(self):
        """Single poll cycle - get notifications and send them"""
        notifications = self.get_pending_notifications()

        for notif in notifications:
            message = self.format_notification(notif)
            await self.send_notification(message)
            self.mark_processed(notif['id'])

        if notifications:
            self.last_check = notifications[-1]['created_at']

        return len(notifications)

    async def run_daemon(self, poll_interval: int = 30):
        """Run as daemon, polling every N seconds"""
        logger.info(f"Status notifier daemon starting (poll every {poll_interval}s)")
        while True:
            try:
                count = await self.poll_and_notify()
                if count > 0:
                    logger.info(f"Sent {count} notifications")
            except Exception as e:
                logger.error(f"Poll cycle error: {e}")

            await asyncio.sleep(poll_interval)


def get_authorized_chat_ids() -> List[int]:
    """Get authorized chat IDs from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('''
            SELECT DISTINCT telegram_chat_id::bigint
            FROM authorized_users
            WHERE telegram_chat_id IS NOT NULL
              AND is_active = true
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [row[0] for row in rows]
    except Exception:
        return []


# Convenience function for Jr to write status
def write_jr_status(task_id: str, status: str, details: str = None, jr_name: str = 'it_triad_jr'):
    """Write Jr status update for Telegram notification"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Temperature based on status
        temperature = 70
        if status == 'failed':
            temperature = 90
        elif status == 'completed':
            temperature = 60

        content = f"JR_STATUS_UPDATE|task_id:{task_id}|status:{status}"
        if details:
            content += f"|details:{details[:500]}"

        cur.execute('''
            INSERT INTO triad_shared_memories
            (content, temperature, source_triad, tags, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        ''', (
            content,
            temperature,
            jr_name,
            ['jr_status', 'telegram_notify', task_id, status]
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error writing status: {e}")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # Run as daemon
        logging.basicConfig(level=logging.INFO)
        notifier = StatusNotifier(chat_ids=get_authorized_chat_ids())
        asyncio.run(notifier.run_daemon(poll_interval=30))
    else:
        # Test mode
        print("Status Notifier Test")
        print("=" * 60)

        # Test writing a status
        print("\\nWriting test status...")
        write_jr_status('TEST-001', 'completed', 'Test task completed successfully')

        # Test reading notifications
        notifier = StatusNotifier()
        notifications = notifier.get_pending_notifications()
        print(f"\\nFound {len(notifications)} pending notifications")

        for n in notifications[:5]:
            print(f"\\n{notifier.format_notification(n)}")